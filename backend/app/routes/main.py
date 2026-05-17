from datetime import date
from flask import Blueprint, jsonify, request

from app.services.slot_capacity import slot_time_strings_for_doctor_day

# A Blueprint groups related routes together.
# 'main' is the name used internally by Flask to identify this blueprint.
# To add more route files: create a new file (e.g. appointments.py), define a blueprint,
# then import and register it in routes/__init__.py.
main_bp = Blueprint('main', __name__)


@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint — confirms the API is running.
    Useful for deployment checks and debugging connectivity.
    Access at: GET /api/health
    """
    return jsonify({'status': 'ok'})


@main_bp.route('/doctors/<doctor_id>/available-slots', methods=['GET'])
def get_doctor_available_slots(doctor_id: str):
    """Return available appointment time slots for a doctor on a given date.

    Query params:
        date: YYYY-MM-DD (required)

    Returns JSON: {"slots": ["09:00", "09:30", ...]} — slots inside working hours,
    respecting breaks and appointment duration. Empty list with 200 OK if none.
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
