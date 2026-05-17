import pytest

from app import create_app
from app.repositories.slot_bookings import reset_booking_counts


@pytest.fixture
def app():
    return create_app(testing=True)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clear_slot_bookings():
    reset_booking_counts()
    yield
    reset_booking_counts()
