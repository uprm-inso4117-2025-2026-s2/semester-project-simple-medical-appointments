from flask import Blueprint, request, jsonify
from app.services.registration import sync_user_after_registration

auth_bp = Blueprint('auth', __name__)

VALID_ROLES = {'patient', 'doctor', 'admin'}

REQUIRED_FIELDS = ['user_id', 'first_name', 'last_name', 'username', 'role']


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register

    Called by the frontend immediately after supabase.auth.signUp() succeeds.
    Syncs the new auth user into the application DB:
      - Creates profiles row
      - Creates profile_settings row with defaults
      - Creates patients or providers row depending on role
      - Assigns role in user_roles

    Request body (JSON):
    {
      "user_id":        "uuid",           -- from Supabase signUp response
      "first_name":     "string",
      "last_name":      "string",
      "username":       "string",
      "role":           "patient" | "doctor",
      "display_name":   "string",         -- optional, defaults to first + last
      "phone_number":   "string",         -- optional
      "date_of_birth":  "YYYY-MM-DD",     -- optional
      "gender":         "string",         -- optional

      -- If role == "patient" (all optional):
      "insurance_provider":        "string",
      "insurance_member_id":       "string",
      "emergency_contact_name":    "string",
      "emergency_contact_phone":   "string",

      -- If role == "doctor" (all optional):
      "profession_title":  "string",
      "specialty":         "string",
      "license_number":    "string",
      "license_state":     "string",
      "bio":               "string"
    }

    Responses:
      201 — sync successful
      400 — missing or invalid fields
      500 — DB sync failed (auth user was created, DB write failed)
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Request body must be JSON.'}), 400

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

    if data['role'] not in VALID_ROLES:
        return jsonify({'error': f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"}), 400

    result = sync_user_after_registration(data['user_id'], data)

    if 'error' in result:
        return jsonify({
            'error': 'Registration succeeded in Supabase Auth but DB sync failed. '
                     'Please contact support.',
            'detail': result['error'],
            'failed_at': result.get('step'),
        }), 500

    return jsonify({'message': 'User registered successfully.'}), 201