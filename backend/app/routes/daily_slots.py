from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, datetime as dt

from app.repositories.availability import (
    get_availability_for_doctor_date,
)

slots_bp = Blueprint("slots", __name__, url_prefix="/api/slots")


def is_inside_blocked_period(slot_start, slot_end, blocked_periods):
    """
    Returns True if a slot overlaps a blocked period.
    """

    for blocked in blocked_periods:
        blocked_start = blocked.start
        blocked_end = blocked.end

        if slot_start < blocked_end and slot_end > blocked_start:
            return True

    return False


def generate_slots(availability):
    slots = []

    working_start = availability.working_hours.start
    working_end = availability.working_hours.end

    current = dt.combine(availability.date, working_start)
    end_datetime = dt.combine(availability.date, working_end)

    slot_duration = availability.slot_minutes

    while current < end_datetime:
        slot_end = current + timedelta(minutes=slot_duration)

        # Prevent slots that exceed working hours
        if slot_end > end_datetime:
            break

        current_time = current.time()
        slot_end_time = slot_end.time()

        if not is_inside_blocked_period(
            current_time,
            slot_end_time,
            availability.blocked_periods,
        ):
            slots.append(
                {
                    "start_time": current.strftime("%H:%M"),
                    "end_time": slot_end.strftime("%H:%M"),
                    "available": True,
                }
            )

        current += timedelta(minutes=slot_duration)

    return slots


@slots_bp.route("/", methods=["GET"])
def get_slots():
    doctor_id = request.args.get("doctor_id")
    date_str = request.args.get("date")

    if not doctor_id or not date_str:
        return jsonify(
            {"error": "doctor_id and date are required"}
        ), 400

    try:
        target_date = datetime.strptime(
            date_str,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return jsonify(
            {"error": "Invalid date format. Use YYYY-MM-DD"}
        ), 400

    try:
        availability = get_availability_for_doctor_date(
            doctor_id,
            target_date,
        )

        slots = generate_slots(availability)

        return jsonify(
            {
                "doctor_id": doctor_id,
                "date": date_str,
                "slot_duration_minutes": availability.slot_minutes,
                "slots": slots,
            }
        ), 200

    except Exception as exc:
        return jsonify(
            {
                "error": "Failed to generate slots",
                "details": str(exc),
            }
        ), 500