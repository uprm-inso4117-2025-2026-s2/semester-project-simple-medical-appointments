from functools import wraps
from flask import request, jsonify, current_app
from supabase import create_client
 
 
def _get_supabase_user(token: str):
    url = current_app.config['SUPABASE_URL']
    key = current_app.config['SUPABASE_SERVICE_ROLE_KEY']
    supabase = create_client(url, key)
    try:
        response = supabase.auth.get_user(token)
        return response.user
    except Exception:
        return None
 
 
def require_auth(f):
    """Decorator that validates a Supabase JWT and injects current_user_id."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or malformed Authorization header. Expected: Bearer <token>'}), 401
 
        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return jsonify({'error': 'Bearer token is empty.'}), 401
 
        user = _get_supabase_user(token)
        if user is None:
            return jsonify({'error': 'Invalid or expired token.'}), 401
 
        return f(current_user_id=user.id, *args, **kwargs)
    return decorated
 