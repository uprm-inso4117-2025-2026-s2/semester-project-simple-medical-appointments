"""Slots with capacity: hide full times and reserve seats per slot start."""

from __future__ import annotations

from datetime import date, datetime, time

from app.repositories.availability import get_availability_for_doctor_date
from app.repositories.slot_bookings import get_booking_count, increment_booking
from app.services.scheduling import generate_available_slots


def slot_time_strings_for_doctor_day(doctor_id: str, day: date) -> list[str]:
    return [dt.strftime("%H:%M") for dt in _slot_starts_with_room(doctor_id, day)]


def try_reserve_slot(
    doctor_id: str,
    day: date,
    start_time: time,
) -> tuple[dict, int] | None:
    rules = get_availability_for_doctor_date(doctor_id, day)
    slot_start = datetime.combine(day, start_time)
    if slot_start not in set(generate_available_slots(rules)):
        return (
            {"error": "Requested time is not an available slot for this doctor/date"},
            400,
        )
    cap = rules.max_appointments_per_slot
    if get_booking_count(doctor_id, slot_start) >= cap:
        return (
            {
                "error": "This time slot is full",
                "max_appointments_per_slot": cap,
            },
            409,
        )
    increment_booking(doctor_id, slot_start)
    return None


def _slot_starts_with_room(doctor_id: str, day: date) -> list[datetime]:
    rules = get_availability_for_doctor_date(doctor_id, day)
    cap = rules.max_appointments_per_slot
    return [
        s
        for s in generate_available_slots(rules)
        if get_booking_count(doctor_id, s) < cap
    ]
