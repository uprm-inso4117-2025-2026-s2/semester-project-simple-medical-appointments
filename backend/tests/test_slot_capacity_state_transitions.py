"""
State-transition tests for per-slot booking capacity (Lecture: Test Preparation).

States: AVAILABLE (0 bookings) -> PARTIAL -> FULL -> (release) -> PARTIAL/AVAILABLE.
"""

from datetime import date, time

import pytest

from app.repositories.slot_bookings import decrement_booking, get_booking_count
from app.services.slot_capacity import slot_time_strings_for_doctor_day, try_reserve_slot

DOCTOR = "dr-1"
DAY = date(2026, 3, 9)
SLOT = time(9, 0)


def _reserve():
    return try_reserve_slot(DOCTOR, DAY, SLOT)


class TestSlotCapacityStateTransitions:
    def test_available_to_partial_to_full(self):
        assert get_booking_count(DOCTOR, _slot_start()) == 0
        assert _reserve() is None
        assert get_booking_count(DOCTOR, _slot_start()) == 1

        assert _reserve() is None
        assert get_booking_count(DOCTOR, _slot_start()) == 2

        body, status = _reserve()
        assert status == 409
        assert "full" in body["error"].lower()

    def test_full_slot_hidden_from_available_slots_list(self):
        for _ in range(2):
            assert _reserve() is None

        slots = slot_time_strings_for_doctor_day(DOCTOR, DAY)
        assert "09:00" not in slots
        assert "09:30" in slots

    def test_full_to_partial_allows_one_more_booking(self):
        for _ in range(2):
            assert _reserve() is None
        decrement_booking(DOCTOR, _slot_start())

        assert get_booking_count(DOCTOR, _slot_start()) == 1
        assert _reserve() is None
        assert get_booking_count(DOCTOR, _slot_start()) == 2

        body, status = _reserve()
        assert status == 409

    def test_partial_to_available_after_cancellation(self):
        assert _reserve() is None
        decrement_booking(DOCTOR, _slot_start())
        assert get_booking_count(DOCTOR, _slot_start()) == 0
        assert "09:00" in slot_time_strings_for_doctor_day(DOCTOR, DAY)

    def test_invalid_slot_time_stays_rejected_from_any_state(self):
        body, status = try_reserve_slot(DOCTOR, DAY, time(12, 0))
        assert status == 400
        assert get_booking_count(DOCTOR, _slot_start()) == 0


def _slot_start():
    from datetime import datetime

    return datetime.combine(DAY, SLOT)
