import jwt
import pytest

from app import create_app

TEST_JWT_SECRET = "test-jwt-secret-for-pytest-only-32bytes!!"


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
