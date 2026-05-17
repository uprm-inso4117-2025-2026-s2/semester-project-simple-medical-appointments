"""Pytest fixtures."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import jwt
import pytest
from datetime import date, time

from app import create_app
from app.middleware import auth_middleware
from app.repositories import availability as availability_repo
from app.repositories.slot_bookings import reset_booking_counts
from app.services.scheduling import DailyAvailability, TimeRange

TEST_JWT_SECRET = "test-jwt-secret-for-pytest-only-32bytes!!"

_production_verify_jwt = auth_middleware.verify_jwt


def _testing_verify_jwt(token: str):
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


def _stub_availability_for_doctor_date(doctor_id: str, target_date: date) -> DailyAvailability:
    """Deterministic Mon–Sat 9–17 with lunch break; Sunday closed (LTT tests)."""
    _ = doctor_id
    max_appointments_per_slot = 2
    if target_date.weekday() == 6:
        working_hours = TimeRange(start=time(9, 0), end=time(9, 0))
        blocked_periods = []
    else:
        working_hours = TimeRange(start=time(9, 0), end=time(17, 0))
        blocked_periods = [TimeRange(start=time(12, 0), end=time(13, 0))]
    return DailyAvailability(
        date=target_date,
        working_hours=working_hours,
        blocked_periods=blocked_periods,
        slot_minutes=30,
        max_appointments_per_slot=max_appointments_per_slot,
    )


@pytest.fixture(autouse=True)
def _patch_jwt_verification_for_tests(monkeypatch, app):
    if app.config.get("TESTING") and app.config.get("SUPABASE_JWT_SECRET"):
        monkeypatch.setattr(auth_middleware, "verify_jwt", _testing_verify_jwt)
    yield


@pytest.fixture(autouse=True)
def _stub_availability_in_tests(monkeypatch):
    monkeypatch.setattr(
        availability_repo,
        "get_availability_for_doctor_date",
        _stub_availability_for_doctor_date,
    )
    monkeypatch.setattr(
        "app.services.slot_capacity.get_availability_for_doctor_date",
        _stub_availability_for_doctor_date,
    )
    yield


@pytest.fixture
def app():
    app = create_app(testing=True)
    app.config.update(
        {
            "SUPABASE_JWT_SECRET": TEST_JWT_SECRET,
            "SUPABASE_URL": os.getenv("SUPABASE_URL", "http://test-supabase"),
            "SUPABASE_SERVICE_ROLE_KEY": os.getenv(
                "SUPABASE_SERVICE_ROLE_KEY", "test-key"
            ),
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


@pytest.fixture(autouse=True)
def _clear_slot_bookings():
    reset_booking_counts()
    yield
    reset_booking_counts()
