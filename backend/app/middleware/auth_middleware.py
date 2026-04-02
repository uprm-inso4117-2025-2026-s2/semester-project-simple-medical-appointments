import jwt
from jwt import PyJWKClient
from flask import jsonify, request, g, current_app
from functools import wraps

# Cached JWKS client — created once per process so the public keys are
# fetched from Supabase only when needed and then cached automatically.
_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        supabase_url = (current_app.config.get("SUPABASE_URL") or "").rstrip("/")
        jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def extract_token() -> str | None:
    """Extracts JWT token from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ")[1]


def verify_jwt(token: str) -> dict | None:
    """Verifies a Supabase-issued JWT using the project's JWKS endpoint.

    Supabase signs tokens with ES256 (asymmetric ECDSA). The public key is
    fetched automatically from /auth/v1/.well-known/jwks.json and cached.

    Returns the decoded payload dict on success, or None on any failure.
    """
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        print("[AUTH] token expired")
        return None
    except Exception as e:
        print(f"[AUTH] error: {type(e).__name__}: {e}")
        return None


def requires_auth(f):
    """Decorator that enforces JWT authentication on a route.

    On success, sets:
        g.user_id  — the Supabase user UUID (JWT 'sub' claim)
        g.user     — the full decoded JWT payload dict

    Returns 401 if the token is missing, expired, or invalid.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = extract_token()
        if not token:
            return jsonify({"message": "No token provided"}), 401

        payload = verify_jwt(token)
        if not payload:
            return jsonify({"message": "Invalid or expired token"}), 401

        g.user_id = payload.get("sub")
        g.user = payload

        return f(*args, **kwargs)

    return wrapper
