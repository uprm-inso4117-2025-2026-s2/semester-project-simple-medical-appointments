from datetime import date

from flask import Blueprint, jsonify, request

from app.middleware.auth_middleware import requires_auth
from app.services.slot_capacity import slot_time_strings_for_doctor_day

main_bp = Blueprint('main', __name__)


@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint — confirms the API is running."""
    return jsonify({'status': 'ok'})


@main_bp.route('/doctors/<doctor_id>/available-slots', methods=['GET'])
@requires_auth
def get_doctor_available_slots(doctor_id: str):
    """Return available appointment time slots for a doctor on a given date.

    Query params:
        date: YYYY-MM-DD (required)

    Returns JSON: {"slots": ["09:00", "09:30", ...]} — slots inside working hours,
    respecting breaks, duration, and per-slot capacity.
    """
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Missing required query parameter: date (YYYY-MM-DD)'}), 400
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    slots = slot_time_strings_for_doctor_day(doctor_id, target_date)
    return jsonify({'slots': slots})
