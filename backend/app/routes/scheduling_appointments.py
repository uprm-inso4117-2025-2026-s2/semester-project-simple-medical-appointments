"""
Scheduling team appointment management API.

Endpoints:
- POST /api/scheduling/appointments/
- GET /api/scheduling/appointments/doctor/<doctor_id>
- GET /api/scheduling/appointments/patient/<patient_id>
- PUT /api/scheduling/appointments/<appointment_id>
- PATCH /api/scheduling/appointments/<appointment_id>/cancel
"""

from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from supabase import create_client, Client
from app.middleware.auth_middleware import requires_auth
from app.repositories.slot_bookings import book_admin_appointment, try_reserve_slot

scheduling_appointments_bp = Blueprint("scheduling_appointments", __name__)

VALID_STATUSES = {"pending", "confirmed", "cancelled", "completed"}
CREATABLE_STATUSES = {"pending", "confirmed"}


def _get_supabase_client() -> Client:
    url = current_app.config.get("SUPABASE_URL")
    key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
        )

    return create_client(url, key)


def _validate_json_request():
    if not request.is_json:
        return jsonify({
            "success": False,
            "message": "Request body must be JSON (Content-Type: application/json)"
        }), 415

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid or empty JSON body"
        }), 415

    return data


def _parse_appointment_datetime(raw_value):
    if raw_value is None or (isinstance(raw_value, str) and not raw_value.strip()):
        return None

    if not isinstance(raw_value, str):
        raise ValueError("appointment_datetime must be a string")

    normalized = raw_value.strip().replace("Z", "+00:00")
    appointment_dt = datetime.fromisoformat(normalized)
    if appointment_dt.second != 0 or appointment_dt.microsecond != 0:
        raise ValueError("appointment_datetime must not include seconds or microseconds")
    if appointment_dt.tzinfo is not None:
        appointment_dt = appointment_dt.replace(tzinfo=None)

    return appointment_dt


def _get_appointment_by_id(supabase: Client, appointment_id):
    response = (
        supabase.table("appointments")
        .select("*")
        .eq("id", appointment_id)
        .execute()
    )
    if not response.data:
        return None
    return response.data[0]


def _get_doctor_clinic_id(supabase: Client, doctor_id):
    response = (
        supabase.table("doctors")
        .select("clinic_id")
        .eq("id", doctor_id)
        .execute()
    )
    if not response.data:
        return None
    return response.data[0].get("clinic_id")


@scheduling_appointments_bp.route("/", methods=["POST"])
@requires_auth
def create_appointment():
    validation_result = _validate_json_request()
    if not isinstance(validation_result, dict):
        return validation_result

    data = validation_result

    required_fields = ["patient_id", "doctor_id", "appointment_datetime"]
    missing_fields = [
        field for field in required_fields
        if data.get(field) is None or (
            isinstance(data.get(field), str) and not data.get(field).strip()
        )
    ]

    if missing_fields:
        return jsonify({
            "success": False,
            "message": "Missing required fields",
            "errors": missing_fields
        }), 400

    status = str(data.get("status", "pending")).strip().lower()
    if status not in CREATABLE_STATUSES:
        return jsonify({
            "success": False,
            "message": (
                "Invalid status for appointment creation. "
                f"Must be one of: {', '.join(sorted(CREATABLE_STATUSES))}"
            )
        }), 400

    try:
        appointment_dt = _parse_appointment_datetime(data["appointment_datetime"])
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid appointment_datetime; use ISO-8601 format"
        }), 400

    patient_id = (
        data["patient_id"].strip()
        if isinstance(data["patient_id"], str)
        else data["patient_id"]
    )
    doctor_id = (
        data["doctor_id"].strip()
        if isinstance(data["doctor_id"], str)
        else data["doctor_id"]
    )

    result, err = book_admin_appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appointment_dt.date(),
        appointment_time=appointment_dt.time(),
        status=status,
        notes=data.get("notes"),
        accept_waitlist=bool(data.get("accept_waitlist", False)),
        allow_override=bool(data.get("allow_override", False)),
    )

    if err is not None:
        body, status_code = err
        return jsonify({"success": False, **body}), status_code

    return jsonify({
        "success": True,
        "message": "Appointment created successfully",
        "data": result,
    }), 201


@scheduling_appointments_bp.route("/doctor/<doctor_id>", methods=["GET"])
@requires_auth
def get_appointments_by_doctor(doctor_id):
    try:
        supabase = _get_supabase_client()
        response = (
            supabase.table("appointments")
            .select("*")
            .eq("doctor_id", doctor_id)
            .order("appointment_datetime")
            .execute()
        )

        return jsonify({
            "success": True,
            "data": response.data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@scheduling_appointments_bp.route("/patient/<patient_id>", methods=["GET"])
@requires_auth
def get_appointments_by_patient(patient_id):
    try:
        supabase = _get_supabase_client()
        response = (
            supabase.table("appointments")
            .select("*")
            .eq("patient_id", patient_id)
            .order("appointment_datetime")
            .execute()
        )

        return jsonify({
            "success": True,
            "data": response.data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@scheduling_appointments_bp.route("/<appointment_id>", methods=["PUT"])
@requires_auth
def update_appointment(appointment_id):
    validation_result = _validate_json_request()
    if not isinstance(validation_result, dict):
        return validation_result
    data = validation_result

    try:
        supabase = _get_supabase_client()
        existing_appointment = _get_appointment_by_id(supabase, appointment_id)
        if not existing_appointment:
            return jsonify({
                "success": False,
                "message": "Appointment not found"
            }), 404

        current_doctor_id = existing_appointment.get("doctor_id")
        current_datetime_raw = existing_appointment.get("appointment_datetime")
        current_datetime = _parse_appointment_datetime(current_datetime_raw)

        target_doctor_id = current_doctor_id
        if "doctor_id" in data:
            target_doctor_id = (
                data["doctor_id"].strip()
                if isinstance(data["doctor_id"], str)
                else data["doctor_id"]
            )
            if not target_doctor_id:
                return jsonify({
                    "success": False,
                    "message": "doctor_id cannot be empty"
                }), 400

        target_datetime = current_datetime
        if "appointment_datetime" in data:
            try:
                target_datetime = _parse_appointment_datetime(data["appointment_datetime"])
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Invalid appointment_datetime; use ISO-8601 format without seconds"
                }), 400
            if target_datetime is None:
                return jsonify({
                    "success": False,
                    "message": "appointment_datetime cannot be empty"
                }), 400

        update_data = {}
        if "status" in data:
            status = str(data["status"]).strip().lower()
            if status not in VALID_STATUSES:
                return jsonify({
                    "success": False,
                    "message": f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
                }), 400
            update_data["status"] = status

        scheduling_changed = (
            target_doctor_id != current_doctor_id
            or target_datetime != current_datetime
        )

        if scheduling_changed:
            err = try_reserve_slot(
                target_doctor_id,
                target_datetime.date(),
                target_datetime.time(),
            )
            if err is not None:
                body, status_code = err
                return jsonify({"success": False, **body}), status_code

            clinic_id = _get_doctor_clinic_id(supabase, target_doctor_id)
            if not clinic_id:
                return jsonify({
                    "success": False,
                    "message": "Could not determine clinic for selected doctor."
                }), 400

            update_data["doctor_id"] = target_doctor_id
            update_data["appointment_datetime"] = target_datetime.isoformat()
            update_data["clinic_id"] = clinic_id
        else:
            if "doctor_id" in data:
                update_data["doctor_id"] = target_doctor_id
            if "appointment_datetime" in data:
                update_data["appointment_datetime"] = target_datetime.isoformat()
            if "clinic_id" in data:
                update_data["clinic_id"] = (
                    data["clinic_id"].strip()
                    if isinstance(data["clinic_id"], str)
                    else data["clinic_id"]
                )

        if not update_data:
            return jsonify({
                "success": False,
                "message": "No valid fields were provided for update"
            }), 400

        response = (
            supabase.table("appointments")
            .update(update_data)
            .eq("id", appointment_id)
            .execute()
        )

        return jsonify({
            "success": True,
            "message": "Appointment updated successfully",
            "data": response.data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@scheduling_appointments_bp.route("/<appointment_id>/cancel", methods=["PATCH"])
@requires_auth
def cancel_appointment(appointment_id):
    try:
        supabase = _get_supabase_client()
        response = (
            supabase.table("appointments")
            .update({"status": "cancelled"})
            .eq("id", appointment_id)
            .execute()
        )

        if not response.data:
            return jsonify({
                "success": False,
                "message": "Appointment not found"
            }), 404

        return jsonify({
            "success": True,
            "message": "Appointment cancelled successfully",
            "data": response.data
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500