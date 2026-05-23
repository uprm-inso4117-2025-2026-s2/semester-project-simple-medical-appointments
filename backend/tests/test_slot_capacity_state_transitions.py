"""
State-transition tests for per-slot booking capacity (Lecture: Test Preparation).

States: AVAILABLE (0 bookings) -> PARTIAL -> FULL -> (release) -> PARTIAL/AVAILABLE.
"""

from datetime import date, datetime, time

import pytest

from app import create_app
from app.repositories import availability
from app.repositories import slot_bookings
from app.repositories.slot_bookings import (
    slot_time_strings_for_doctor_day,
    try_reserve_slot,
)

DOCTOR = "dr-1"
DAY = date(2026, 3, 9)
SLOT = time(9, 0)


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

        if method == "GET" and path == "/rest/v1/availability_rules":
            return 200, [
                {
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                }
            ], None

        if method == "GET" and path == "/rest/v1/doctors":
            if query.get("select") == "clinic_id":
                return 200, [{"clinic_id": "fake-clinic-id"}], None

            if query.get("select") == "user_id":
                return 200, [{"user_id": "fake-user-id"}], None

        if method == "GET" and path == "/rest/v1/provider_settings":
            return 200, [{"default_appointment_duration": 30}], None

        if method == "GET" and path == "/rest/v1/appointments":
            doctor_id = query.get("doctor_id", "").replace("eq.", "")
            appointment_datetime = query.get("appointment_datetime", "").replace("eq.", "")
            appointment_type_filter = query.get("appointment_type", "")
            status_filter = query.get("status", "")

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

            if status_filter == "in.(pending,confirmed)":
                    results = [
                        appt for appt in results
                        if appt.get("status") in ("pending", "confirmed")
                    ]

            return 200, results, None

        if method == "POST" and path == "/rest/v1/appointments":
            new_appointment = dict(json_body)
            new_appointment["id"] = len(fake_appointments) + 1
            fake_appointments.append(new_appointment)
            return 201, [new_appointment], None

        return 404, None, f"Unhandled fake request: {method} {path}"

    monkeypatch.setattr(availability, "_supabase_request", fake_supabase_request)
    monkeypatch.setattr(slot_bookings, "_supabase_request", fake_supabase_request)

    return fake_appointments


def _slot_datetime():
    return datetime.combine(DAY, SLOT).isoformat()


def _reserve():
    return try_reserve_slot(DOCTOR, DAY, SLOT)


def _insert_fake_main_booking(fake_appointments):
    fake_appointments.append(
        {
            "id": len(fake_appointments) + 1,
            "patient_id": f"patient-{len(fake_appointments) + 1}",
            "doctor_id": DOCTOR,
            "clinic_id": "fake-clinic-id",
            "appointment_datetime": _slot_datetime(),
            "status": "confirmed",
            "appointment_type": "MAIN",
            "notes": None,
        }
    )


def _count_bookings_for_slot(fake_appointments):
    return len(
        [
            appt for appt in fake_appointments
            if appt["doctor_id"] == DOCTOR
            and appt["appointment_datetime"] == _slot_datetime()
            and appt["status"] in ("pending", "confirmed")
        ]
    )

def _cancel_one_booking(fake_appointments):
    for appt in fake_appointments:
        if (
            appt["doctor_id"] == DOCTOR
            and appt["appointment_datetime"] == _slot_datetime()
            and appt["status"] in ("pending", "confirmed")
        ):
            appt["status"] = "cancelled"
            return
class TestSlotCapacityStateTransitions:
    def test_available_to_partial_to_full(self, app_context, fake_supabase):
        assert _count_bookings_for_slot(fake_supabase) == 0
        assert _reserve() is None

        _insert_fake_main_booking(fake_supabase)
        assert _count_bookings_for_slot(fake_supabase) == 1
        assert _reserve() is None

        _insert_fake_main_booking(fake_supabase)
        assert _count_bookings_for_slot(fake_supabase) == 2

        body, status = _reserve()
        assert status == 409
        assert "full" in body["error"].lower()

    def test_full_slot_hidden_from_available_slots_list(self, app_context, fake_supabase):
        _insert_fake_main_booking(fake_supabase)
        _insert_fake_main_booking(fake_supabase)

        slots = slot_time_strings_for_doctor_day(DOCTOR, DAY)

        assert "09:00" not in slots
        assert "09:30" in slots

    def test_full_to_partial_allows_one_more_booking(self, app_context, fake_supabase):
        _insert_fake_main_booking(fake_supabase)
        _insert_fake_main_booking(fake_supabase)

        body, status = _reserve()
        assert status == 409

        _cancel_one_booking(fake_supabase)
        assert _count_bookings_for_slot(fake_supabase) == 1

        assert _reserve() is None

        _insert_fake_main_booking(fake_supabase)
        assert _count_bookings_for_slot(fake_supabase) == 2

        body, status = _reserve()
        assert status == 409


    def test_partial_to_available_after_cancellation(self, app_context, fake_supabase):
        _insert_fake_main_booking(fake_supabase)

        assert "09:00" in slot_time_strings_for_doctor_day(DOCTOR, DAY)

        _cancel_one_booking(fake_supabase)

        assert _count_bookings_for_slot(fake_supabase) == 0
        assert "09:00" in slot_time_strings_for_doctor_day(DOCTOR, DAY)

    def test_invalid_slot_time_stays_rejected_from_any_state(self, app_context, fake_supabase):
        body, status = try_reserve_slot(DOCTOR, DAY, time(8, 0))

        assert status == 400
        assert _count_bookings_for_slot(fake_supabase) == 0
