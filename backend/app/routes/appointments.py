"""Appointment routes — form submission and related endpoints."""

from flask import Blueprint, jsonify, request

appointments_bp = Blueprint('appointments', __name__)


def _validate_form_submission(data):
    """Validate the appointment form payload. Returns (is_valid, errors)."""
    errors = []
    required_fields = ['name', 'surname', 'symptoms_and_or_allergies', 'medications']

    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            label = field.replace('_', ' ').title()
            errors.append(f"{label} is required")

    return len(errors) == 0, errors


@appointments_bp.route('/submit', methods=['POST'])
def submit_appointment_form():
    """
    Submit the appointment form.

    Expects JSON body with:
    - name (str, required)
    - surname (str, required)
    - symptoms_and_or_allergies (str, required)
    - medications (str, required)

    Returns:
    - 201: Success
    - 400: Validation error (missing or empty fields)
    - 415: Invalid content type (not JSON)
    """
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Content-Type must be application/json',
        }), 415

    data = request.get_json() or {}
    is_valid, errors = _validate_form_submission(data)

    if not is_valid:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': errors,
        }), 400

    # Extract and optionally sanitize data (add DB persistence here later)
    payload = {
        'name': data['name'].strip(),
        'surname': data['surname'].strip(),
        'symptoms_and_or_allergies': data['symptoms_and_or_allergies'].strip(),
        'medications': data['medications'].strip(),
    }

    # TODO: Persist to database when models are ready
    # For now, return success to confirm the backend accepted the data
    return jsonify({
        'success': True,
        'message': 'Appointment form submitted successfully',
        'data': payload,
    }), 201
