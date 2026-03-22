from flask import Blueprint, jsonify, request
from app.config import get_db_connection

# Blueprint for authentication-related routes.
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register_user():
    """Sync a newly Supabase-registered user to the local database.

    This endpoint is the DB-sync step of the registration flow (issue #193).
    It is called by the frontend immediately after a successful
    supabase.auth.signUp(), passing the Supabase-assigned UID and email so
    we can maintain a local users table that the rest of the app can join
    against for role checks, profiles, etc.

    Expected JSON body:
        supabase_uid (str): UUID assigned by Supabase Auth.
        email        (str): The user's email address.

    Returns:
        201 — user record created; body: { message, email }
        400 — missing / invalid request body
        409 — user already exists in the local DB
        500 — unexpected database error
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Request body must be JSON'}), 400

    supabase_uid = data.get('supabase_uid', '').strip()
    email = data.get('email', '').strip()

    if not supabase_uid or not email:
        return jsonify({'error': 'supabase_uid and email are required'}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute(
            'SELECT id FROM users WHERE supabase_uid = ?', (supabase_uid,)
        ).fetchone()
        if existing:
            return jsonify({'error': 'User already registered'}), 409

        conn.execute(
            'INSERT INTO users (supabase_uid, email, role) VALUES (?, ?, ?)',
            (supabase_uid, email, 'patient'),
        )
        conn.commit()
    except Exception as exc:
        return jsonify({'error': f'Database error: {exc}'}), 500
    finally:
        conn.close()

    return jsonify({'message': 'User registered successfully', 'email': email}), 201
