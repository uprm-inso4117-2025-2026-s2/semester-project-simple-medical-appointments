"""
Scheduling team appointment management API.

Endpoints:
- POST /api/scheduling/appointments/
- GET /api/scheduling/appointments/doctor/<doctor_id>
- GET /api/scheduling/appointments/patient/<patient_id>
- PUT /api/scheduling/appointments/<appointment_id>
- PATCH /api/scheduling/appointments/<appointment_id>/cancel
"""

from flask import Blueprint, request, jsonify, current_app
from supabase import create_client, Client
from app.middleware.auth_middleware import requires_auth

scheduling_appointments_bp = Blueprint("scheduling_appointments", __name__)

VALID_STATUSES = {"pending", "confirmed", "cancelled", "completed"}


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


@scheduling_appointments_bp.route("/", methods=["POST"])
@requires_auth
def create_appointment():
    validation_result = _validate_json_request()
    if not isinstance(validation_result, dict):
        return validation_result

    data = validation_result

    required_fields = ["patient_id", "doctor_id", "clinic_id", "appointment_datetime"]
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

    status = data.get("status", "pending")
    if status not in VALID_STATUSES:
        return jsonify({
            "success": False,
            "message": f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        }), 400

    appointment_data = {
        "patient_id": data["patient_id"].strip() if isinstance(data["patient_id"], str) else data["patient_id"],
        "doctor_id": data["doctor_id"].strip() if isinstance(data["doctor_id"], str) else data["doctor_id"],
        "clinic_id": data["clinic_id"].strip() if isinstance(data["clinic_id"], str) else data["clinic_id"],
        "appointment_datetime": data["appointment_datetime"].strip()
        if isinstance(data["appointment_datetime"], str) else data["appointment_datetime"],
        "status": status,
    }

    try:
        supabase = _get_supabase_client()
        response = supabase.table("appointments").insert(appointment_data).execute()

        return jsonify({
            "success": True,
            "message": "Appointment created successfully",
            "data": response.data
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


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
    update_data = {}

    if "doctor_id" in data:
        update_data["doctor_id"] = data["doctor_id"].strip() if isinstance(data["doctor_id"], str) else data["doctor_id"]

    if "clinic_id" in data:
        update_data["clinic_id"] = data["clinic_id"].strip() if isinstance(data["clinic_id"], str) else data["clinic_id"]

    if "appointment_datetime" in data:
        update_data["appointment_datetime"] = (
            data["appointment_datetime"].strip()
            if isinstance(data["appointment_datetime"], str)
            else data["appointment_datetime"]
        )

    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            return jsonify({
                "success": False,
                "message": f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            }), 400
        update_data["status"] = data["status"]

    if not update_data:
        return jsonify({
            "success": False,
            "message": "No valid fields were provided for update"
        }), 400

    try:
        supabase = _get_supabase_client()
        response = (
            supabase.table("appointments")
            .update(update_data)
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