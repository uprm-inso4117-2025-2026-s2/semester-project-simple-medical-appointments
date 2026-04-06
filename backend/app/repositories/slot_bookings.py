"""Per-slot booking counts (stub) plus helpers to list/reserve slots with capacity rules."""

from __future__ import annotations

from datetime import date, datetime, time
from threading import Lock

from .availability import get_availability_for_doctor_date
from ..services.scheduling import generate_available_slots

_lock = Lock()
# (doctor_id, date_iso, "HH:MM") -> count
_counts: dict[tuple[str, str, str], int] = {}


def _key(doctor_id: str, slot_start: datetime) -> tuple[str, str, str]:
    return (doctor_id, slot_start.date().isoformat(), slot_start.strftime("%H:%M"))


def get_booking_count(doctor_id: str, slot_start: datetime) -> int:
    with _lock:
        return _counts.get(_key(doctor_id, slot_start), 0)


def increment_booking(doctor_id: str, slot_start: datetime) -> int:
    """Increment bookings for this slot; return the new total."""
    with _lock:
        k = _key(doctor_id, slot_start)
        _counts[k] = _counts.get(k, 0) + 1
        return _counts[k]


def slot_time_strings_for_doctor_day(doctor_id: str, day: date) -> list[str]:
    """HH:MM strings for the UI — calendar rules minus slots already at capacity."""
    return [dt.strftime("%H:%M") for dt in _slot_starts_with_room(doctor_id, day)]


def try_reserve_slot(
    doctor_id: str,
    day: date,
    start_time: time,
) -> tuple[dict, int] | None:
    """Record one booking in a slot, or return (error JSON, HTTP status)."""
    rules = get_availability_for_doctor_date(doctor_id, day)
    slot_start = datetime.combine(day, start_time)
    allowed_starts = set(generate_available_slots(rules))
    if slot_start not in allowed_starts:
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
