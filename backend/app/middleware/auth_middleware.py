import jwt
from flask import jsonify, request, g, current_app
from functools import wraps


def extract_token() -> str | None:
    """Extracts JWT token from the Authorization header.

    Returns:
        str | None: Raw token string, or None if header is missing/malformed.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ")[1]


def verify_jwt(token: str) -> dict | None:
    """Verifies a Supabase-issued JWT using the project JWT secret.

    Reads SUPABASE_JWT_SECRET from the Flask app config (set in config.py).
    Returns the decoded payload dict on success, or None if the token is
    expired, invalid, or the secret is not configured.

    Args:
        token (str): Raw JWT string from the Authorization header.

    Returns:
        dict | None: Decoded JWT payload, or None on any verification failure.
    """
    secret = current_app.config.get("SUPABASE_JWT_SECRET")
    if not secret:
        return None

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def requires_auth(f):
    """Decorator that enforces JWT authentication on a route.

    Extracts and verifies the Bearer token from the Authorization header.
    On success, sets:
        g.user_id  — the Supabase user UUID (JWT 'sub' claim)
        g.user     — the full decoded JWT payload dict

    Returns 401 if the token is missing, expired, or invalid.

    Usage:
        @requires_auth
        def my_view(): ...
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = extract_token()
        if not token:
            return jsonify({"message": "No token provided"}), 401

        payload = verify_jwt(token)
        if not payload:
            return jsonify({"message": "Invalid or expired token"}), 401

        g.user_id = payload.get("sub")  # Supabase user UUID
        g.user = payload                # full JWT payload

        return f(*args, **kwargs)

    return wrapper
