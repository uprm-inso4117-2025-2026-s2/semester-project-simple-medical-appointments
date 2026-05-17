"""In-memory per-slot booking counts (stub until Supabase scheduling schema exists)."""

from __future__ import annotations

from datetime import datetime
from threading import Lock

_lock = Lock()
_counts: dict[tuple[str, str, str], int] = {}


def _key(doctor_id: str, slot_start: datetime) -> tuple[str, str, str]:
    return (doctor_id, slot_start.date().isoformat(), slot_start.strftime("%H:%M"))


def get_booking_count(doctor_id: str, slot_start: datetime) -> int:
    with _lock:
        return _counts.get(_key(doctor_id, slot_start), 0)


def increment_booking(doctor_id: str, slot_start: datetime) -> int:
    with _lock:
        k = _key(doctor_id, slot_start)
        _counts[k] = _counts.get(k, 0) + 1
        return _counts[k]


def decrement_booking(doctor_id: str, slot_start: datetime) -> int:
    """Release one seat (e.g. appointment cancelled). Returns the new count."""
    with _lock:
        k = _key(doctor_id, slot_start)
        current = _counts.get(k, 0)
        if current <= 0:
            return 0
        _counts[k] = current - 1
        if _counts[k] == 0:
            del _counts[k]
        return _counts.get(k, 0)


def reset_booking_counts() -> None:
    """Clear all counts — used between tests."""
    with _lock:
        _counts.clear()
