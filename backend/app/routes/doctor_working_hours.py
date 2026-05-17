import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, jsonify, request

from app.middleware.auth_middleware import requires_auth
from app.services.working_hours import (
    normalize_ranges_payload,
    serialize_ranges,
)
from app.utils.custom_decorators import requires_role

working_hours_bp = Blueprint("working_hours", __name__)


def _supabase_request(method, path, *, query=None, json_body=None, prefer=None):
    """Issue a request to Supabase REST API using service role credentials."""
    base_url = (current_app.config.get("SUPABASE_URL") or "").rstrip("/")
    service_key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")

    if not base_url or not service_key:
        return None, None, "Supabase is not configured."

    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer

    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    req = Request(url=url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.status, None, None
            try:
                return resp.status, json.loads(raw), None
            except json.JSONDecodeError:
                return resp.status, raw, None
    except HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw or None
        return exc.code, parsed, None
    except (URLError, Exception) as exc:
        return None, None, f"Supabase request failed: {exc}"


@working_hours_bp.route("/doctors/<doctor_id>/working-hours", methods=["GET"])
@requires_auth
@requires_role({"admin"})
def list_doctor_working_hours(doctor_id):
    day_of_week = request.args.get("day_of_week", type=int)
    if day_of_week is not None and not 0 <= day_of_week <= 6:
        return jsonify({"error": "day_of_week must be between 0 and 6"}), 400

    query = {
        "doctor_id": f"eq.{doctor_id}",
        "select": "id,doctor_id,day_of_week,start_time,end_time,is_active,created_at",
        "order": "day_of_week.asc,start_time.asc",
    }
    if day_of_week is not None:
        query["day_of_week"] = f"eq.{day_of_week}"

    status, data, err = _supabase_request("GET", "/rest/v1/availability_rules", query=query)
    if err or status != 200:
        return jsonify({"error": "Failed to fetch doctor working hours."}), 500

    grouped = {}
    for row in data or []:
        day = row.get("day_of_week")
        if day not in grouped:
            grouped[day] = {
                "day_of_week": day,
                "is_active": False,
                "ranges": [],
            }

        grouped[day]["is_active"] = grouped[day]["is_active"] or bool(row.get("is_active", False))
        grouped[day]["ranges"].append(
            {
                "id": row.get("id"),
                "start_time": row.get("start_time"),
                "end_time": row.get("end_time"),
            }
        )

    schedules = [grouped[key] for key in sorted(grouped.keys())]
    return jsonify({"doctor_id": doctor_id, "schedules": schedules}), 200


@working_hours_bp.route("/doctors/<doctor_id>/working-hours/<int:day_of_week>", methods=["PUT"])
@requires_auth
@requires_role({"admin"})
def replace_doctor_working_hours_for_day(doctor_id, day_of_week):
    if not 0 <= day_of_week <= 6:
        return jsonify({"error": "day_of_week must be between 0 and 6"}), 400

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be JSON"}), 400

    is_active = bool(data.get("is_active", True))

    delete_status, _, delete_err = _supabase_request(
        "DELETE",
        "/rest/v1/availability_rules",
        query={"doctor_id": f"eq.{doctor_id}", "day_of_week": f"eq.{day_of_week}"},
        prefer="return=minimal",
    )
    if delete_err or delete_status not in (200, 204):
        return jsonify({"error": "Failed to update working hours."}), 500

    if not is_active:
        return jsonify(
            {
                "doctor_id": doctor_id,
                "day_of_week": day_of_week,
                "is_active": False,
                "ranges": [],
            }
        ), 200

    try:
        ranges = normalize_ranges_payload(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if not ranges:
        return jsonify({"error": "At least one time range is required when is_active is true"}), 400

    rows = [
        {
            "doctor_id": doctor_id,
            "day_of_week": day_of_week,
            "start_time": start.strftime("%H:%M:%S"),
            "end_time": end.strftime("%H:%M:%S"),
            "is_active": True,
        }
        for start, end in ranges
    ]

    insert_status, _, insert_err = _supabase_request(
        "POST",
        "/rest/v1/availability_rules",
        json_body=rows,
        prefer="return=representation",
    )
    if insert_err or insert_status not in (200, 201):
        return jsonify({"error": "Failed to save working hours."}), 500

    return jsonify(
        {
            "doctor_id": doctor_id,
            "day_of_week": day_of_week,
            "is_active": True,
            "ranges": serialize_ranges(ranges),
        }
    ), 200


@working_hours_bp.route("/doctors/<doctor_id>/working-hours/<int:day_of_week>", methods=["DELETE"])
@requires_auth
@requires_role({"admin"})
def delete_doctor_working_hours_for_day(doctor_id, day_of_week):
    if not 0 <= day_of_week <= 6:
        return jsonify({"error": "day_of_week must be between 0 and 6"}), 400

    status, _, err = _supabase_request(
        "DELETE",
        "/rest/v1/availability_rules",
        query={"doctor_id": f"eq.{doctor_id}", "day_of_week": f"eq.{day_of_week}"},
        prefer="return=minimal",
    )
    if err or status not in (200, 204):
        return jsonify({"error": "Failed to delete working hours."}), 500

    return jsonify({"message": "Working hours deleted.", "doctor_id": doctor_id, "day_of_week": day_of_week}), 200
