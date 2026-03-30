"""
Appointment form submission API (skeleton).
POST /api/appointments/submit — accepts form data; persistence to Supabase is TODO.
"""
from flask import Blueprint, request, jsonify
from app.middleware.auth_middleware import requires_auth

appointments_bp = Blueprint('appointments', __name__)

REQUIRED_FIELDS = ('name', 'surname', 'symptoms_and_or_allergies', 'medications')


@appointments_bp.route('/submit', methods=['POST'])
@requires_auth
def submit_appointment():
    """
    Submit appointment form data.

    Request: JSON body with required fields (all non-empty after trim):
      - name, surname, symptoms_and_or_allergies, medications

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

    # TODO: persist to Supabase once tables/entities are set up
    return jsonify({
        'success': True,
        'message': 'Appointment form submitted successfully.',
        'data': normalized,
    }), 201
