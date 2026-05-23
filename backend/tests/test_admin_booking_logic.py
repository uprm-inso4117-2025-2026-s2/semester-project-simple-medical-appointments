from datetime import date, time

import pytest

from app import create_app
from app.repositories import availability
from app.repositories import slot_bookings


@pytest.fixture
def app_context():
    app = create_app()
    with app.app_context():
        yield


@pytest.fixture
def fake_supabase(monkeypatch):
    fake_appointments = []

    def fake_supabase_request(method, path, *, query=None, json_body=None):
        query = query or {}

        # Fake availability rules: doctor works Monday 9 AM - 5 PM.
        if method == "GET" and path == "/rest/v1/availability_rules":
            return 200, [
                {
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                }
            ], None

        # Fake doctor lookups.
        if method == "GET" and path == "/rest/v1/doctors":
            if query.get("select") == "clinic_id":
                return 200, [{"clinic_id": "fake-clinic-id"}], None

            if query.get("select") == "user_id":
                return 200, [{"user_id": "fake-user-id"}], None

        # Fake provider settings.
        if method == "GET" and path == "/rest/v1/provider_settings":
            return 200, [{"default_appointment_duration": 30}], None

        # Fake appointment query/counting.
        if method == "GET" and path == "/rest/v1/appointments":
            doctor_id = query.get("doctor_id", "").replace("eq.", "")
            appointment_datetime = query.get("appointment_datetime", "").replace("eq.", "")
            appointment_type_filter = query.get("appointment_type", "")

            results = [
                appt for appt in fake_appointments
                if appt["doctor_id"] == doctor_id
            ]

            if appointment_datetime:
                results = [
                    appt for appt in results
                    if appt["appointment_datetime"] == appointment_datetime
                ]

            if appointment_type_filter == "eq.WAITLIST":
                results = [
                    appt for appt in results
                    if appt["appointment_type"] == "WAITLIST"
                ]

            return 200, results, None

        # Fake appointment insert.
        if method == "POST" and path == "/rest/v1/appointments":
            new_appointment = dict(json_body)
            new_appointment["id"] = len(fake_appointments) + 1
            fake_appointments.append(new_appointment)
            return 201, [new_appointment], None

        return 404, None, f"Unhandled fake request: {method} {path}"

    # Patch both modules because slot_bookings imports _supabase_request directly.
    monkeypatch.setattr(availability, "_supabase_request", fake_supabase_request)
    monkeypatch.setattr(slot_bookings, "_supabase_request", fake_supabase_request)

    return fake_appointments


def test_first_booking_goes_to_main(app_context, fake_supabase):
    result, err = slot_bookings.book_admin_appointment(
        patient_id="fake-patient-id",
        doctor_id="fake-doctor-id",
        appointment_date=date(2026, 5, 25),
        appointment_time=time(9, 0),
        accept_waitlist=True,
        allow_override=False,
        notes="Test main booking",
    )

    assert err is None
    assert result["booking_type"] == "MAIN"
    assert result["appointment"]["appointment_type"] == "MAIN"
    assert result["appointment"]["appointment_datetime"] == "2026-05-25T09:00:00"
    assert len(fake_supabase) == 1


def test_third_booking_goes_to_waitlist_next_available_slot(app_context, fake_supabase):
    # First two bookings fill the requested 09:00 slot.
    for _ in range(2):
        result, err = slot_bookings.book_admin_appointment(
            patient_id="fake-patient-id",
            doctor_id="fake-doctor-id",
            appointment_date=date(2026, 5, 25),
            appointment_time=time(9, 0),
            accept_waitlist=True,
            allow_override=False,
        )
        assert err is None
        assert result["booking_type"] == "MAIN"

    # Third booking should be moved to next available slot as WAITLIST.
    result, err = slot_bookings.book_admin_appointment(
        patient_id="fake-patient-id",
        doctor_id="fake-doctor-id",
        appointment_date=date(2026, 5, 25),
        appointment_time=time(9, 0),
        accept_waitlist=True,
        allow_override=False,
        notes="Test waitlist booking",
    )

    assert err is None
    assert result["booking_type"] == "WAITLIST"
    assert result["appointment"]["appointment_type"] == "WAITLIST"
    assert result["requested_datetime"] == "2026-05-25T09:00:00"
    assert result["assigned_datetime"] == "2026-05-25T09:30:00"
    assert len(fake_supabase) == 3


def test_full_slot_without_waitlist_or_override_is_rejected(app_context, fake_supabase):
    # Fill 09:00.
    for _ in range(2):
        result, err = slot_bookings.book_admin_appointment(
            patient_id="fake-patient-id",
            doctor_id="fake-doctor-id",
            appointment_date=date(2026, 5, 25),
            appointment_time=time(9, 0),
            accept_waitlist=False,
            allow_override=False,
        )
        assert err is None

    result, err = slot_bookings.book_admin_appointment(
        patient_id="fake-patient-id",
        doctor_id="fake-doctor-id",
        appointment_date=date(2026, 5, 25),
        appointment_time=time(9, 0),
        accept_waitlist=False,
        allow_override=False,
    )

    assert result is None
    assert err is not None

    body, status = err
    assert status == 409
    assert body["error"] == "Unable to book appointment."


def test_full_slot_with_override_books_override(app_context, fake_supabase):
    # Fill 09:00.
    for _ in range(2):
        result, err = slot_bookings.book_admin_appointment(
            patient_id="fake-patient-id",
            doctor_id="fake-doctor-id",
            appointment_date=date(2026, 5, 25),
            appointment_time=time(9, 0),
            accept_waitlist=False,
            allow_override=False,
        )
        assert err is None

    result, err = slot_bookings.book_admin_appointment(
        patient_id="fake-patient-id",
        doctor_id="fake-doctor-id",
        appointment_date=date(2026, 5, 25),
        appointment_time=time(9, 0),
        accept_waitlist=False,
        allow_override=True,
        notes="Admin approved override",
    )

    assert err is None
    assert result["booking_type"] == "OVERRIDE"
    assert result["appointment"]["appointment_type"] == "OVERRIDE"
    assert result["assigned_datetime"] == "2026-05-25T09:00:00"


def test_invalid_slot_is_rejected(app_context, fake_supabase):
    result, err = slot_bookings.book_admin_appointment(
        patient_id="fake-patient-id",
        doctor_id="fake-doctor-id",
        appointment_date=date(2026, 5, 25),
        appointment_time=time(8, 0),  # Before generated working hours.
        accept_waitlist=True,
        allow_override=False,
    )

    assert result is None
    assert err is not None

    body, status = err
    assert status == 400
    assert "not an available generated slot" in body["error"]


def test_daily_waitlist_capacity_is_enforced(app_context, fake_supabase):
    # Fill 09:00.
    for _ in range(2):
        result, err = slot_bookings.book_admin_appointment(
            patient_id="fake-patient-id",
            doctor_id="fake-doctor-id",
            appointment_date=date(2026, 5, 25),
            appointment_time=time(9, 0),
            accept_waitlist=True,
            allow_override=False,
        )
        assert err is None

    # Create 3 waitlist bookings, which matches DEFAULT_WAITLIST_CAPACITY_PER_DAY.
    for _ in range(3):
        result, err = slot_bookings.book_admin_appointment(
            patient_id="fake-patient-id",
            doctor_id="fake-doctor-id",
            appointment_date=date(2026, 5, 25),
            appointment_time=time(9, 0),
            accept_waitlist=True,
            allow_override=False,
        )
        assert err is None
        assert result["booking_type"] == "WAITLIST"

    # Next waitlist attempt should be rejected because daily waitlist cap is reached.
    result, err = slot_bookings.book_admin_appointment(
        patient_id="fake-patient-id",
        doctor_id="fake-doctor-id",
        appointment_date=date(2026, 5, 25),
        appointment_time=time(9, 0),
        accept_waitlist=True,
        allow_override=False,
    )

    assert result is None
    assert err is not None

    body, status = err
    assert status == 409
    assert body["details"]["error"] == "Daily waitlist capacity has been reached."