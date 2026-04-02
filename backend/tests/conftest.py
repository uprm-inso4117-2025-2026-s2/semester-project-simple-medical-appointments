import jwt
import pytest

from app import create_app
from app.middleware import auth_middleware

TEST_JWT_SECRET = "test-jwt-secret-for-pytest-only-32bytes!!"

_production_verify_jwt = auth_middleware.verify_jwt


def _testing_verify_jwt(token: str):
    """Use HS256 + SUPABASE_JWT_SECRET in tests; otherwise keep production JWKS path."""
    from flask import current_app

    if not current_app.config.get("TESTING"):
        return _production_verify_jwt(token)

    secret = current_app.config.get("SUPABASE_JWT_SECRET")
    if secret:
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError:
            pass

    return _production_verify_jwt(token)


@pytest.fixture(autouse=True)
def _patch_jwt_verification_for_tests(monkeypatch, app):
    if app.config.get("TESTING") and app.config.get("SUPABASE_JWT_SECRET"):
        monkeypatch.setattr(auth_middleware, "verify_jwt", _testing_verify_jwt)
    yield


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SUPABASE_JWT_SECRET": TEST_JWT_SECRET,
        }
    )
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001"},
        app.config["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )
    if isinstance(token, bytes):
        token = token.decode("ascii")
    return {"Authorization": f"Bearer {token}"}
