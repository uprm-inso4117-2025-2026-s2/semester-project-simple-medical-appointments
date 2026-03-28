"""
Appointment form submission API (skeleton).
POST /api/appointments/submit — accepts form data; persistence to Supabase is TODO.
"""
from datetime import date, time

from flask import Blueprint, request, jsonify

from app.repositories.slot_bookings import try_reserve_slot

appointments_bp = Blueprint('appointments', __name__)

REQUIRED_FIELDS = ('name', 'surname', 'symptoms_and_or_allergies', 'medications')
SCHEDULING_FIELDS = ('doctor_id', 'appointment_date', 'appointment_time')


def _is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _scheduling_any_field_present(data: dict) -> bool:
    return any(_is_present(data.get(f)) for f in SCHEDULING_FIELDS)


def _scheduling_all_fields_present(data: dict) -> bool:
    return all(_is_present(data.get(f)) for f in SCHEDULING_FIELDS)


@appointments_bp.route('/submit', methods=['POST'])
def submit_appointment():
    """
    Submit appointment form data.

    Request: JSON body with required fields (all non-empty after trim):
      - name, surname, symptoms_and_or_allergies, medications

    Optional scheduling (all three required if any is sent):
      - doctor_id, appointment_date (YYYY-MM-DD), appointment_time (HH:MM)
      When provided, the slot must be valid for that doctor/date and not exceed
      max_appointments_per_slot (409 if full).

    Responses:
      - 201: success, returns { success, message, data } with normalized payload
      - 400: validation errors, returns { error, errors } with list of failed fields
      - 415: non-JSON or wrong Content-Type

    Note: This is a skeleton; database persistence will be added when Supabase is wired.
    """
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON (Content-Type: application/json)'}), 415

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Invalid or empty JSON body'}), 415

    errors = []
    normalized = {}
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(field)
        else:
            normalized[field] = value.strip() if isinstance(value, str) else value

    if errors:
        return jsonify({'error': 'Validation failed', 'errors': errors}), 400

    if _scheduling_any_field_present(data):
        if not _scheduling_all_fields_present(data):
            return jsonify(
                {
                    'error': 'Scheduling fields must all be provided together',
                    'fields': list(SCHEDULING_FIELDS),
                }
            ), 400

        doctor_id = str(data['doctor_id']).strip()
        date_str = str(data['appointment_date']).strip()
        time_str = str(data['appointment_time']).strip()
        try:
            appt_date = date.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': 'Invalid appointment_date; use YYYY-MM-DD'}), 400
        try:
            appt_time = time.fromisoformat(time_str)
        except ValueError:
            return jsonify({'error': 'Invalid appointment_time; use HH:MM (24h)'}), 400

        err = try_reserve_slot(doctor_id, appt_date, appt_time)
        if err is not None:
            body, status = err
            return jsonify(body), status

        normalized['doctor_id'] = doctor_id
        normalized['appointment_date'] = date_str
        normalized['appointment_time'] = time_str

    # TODO: persist to Supabase once tables/entities are set up
    return jsonify({
        'success': True,
        'message': 'Appointment form submitted successfully.',
        'data': normalized,
    }), 201
