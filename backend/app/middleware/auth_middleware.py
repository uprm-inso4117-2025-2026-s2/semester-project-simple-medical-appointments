import os
import jwt
from flask import request, g
from functools import wraps

SUPABASE_JWT_SECRET = os.getenv(
    "SUPABASE_JWT_SECRET", "dev-supabase-jwt-secret-change-in-production"
)


def extract_token() -> str | None:
    """Extracts JWT token from Authorization header

    Returns:
        str | None: JWT token
    """

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    return auth_header.split(" ")[1]


def verify_jwt(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def requires_auth(f):
    """Decorator to check if the user is authenticated

    Example usage:
    @requires_auth

    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = extract_token()
        if not token:
            return "Unauthorized", 401

        payload = verify_jwt(token)
        if not payload:
            return "Unauthorized", 401

        # Expected to be UUID of the user
        g.user_id = payload.get("sub")
        # Expected to be a supabase user
        g.user = payload

        return f(*args, **kwargs)

    return wrapper
