"""
Core booking logic for the Simple Medical Appointments system.

This module handles:
- Appointment form validation
- Time slot generation and availability computation
- Conflict detection (double-booking prevention)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List, Optional

REQUIRED_FIELDS = ("name", "surname", "symptoms_and_or_allergies", "medications")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_appointment_form(data: dict) -> tuple[bool, list[str]]:
    """Validate appointment form data.

    Returns (is_valid, list_of_failed_fields).
    A field fails if it is missing, None, or blank after stripping whitespace.
    """
    if not isinstance(data, dict):
        return False, list(REQUIRED_FIELDS)

    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(field)

    return len(errors) == 0, errors


def normalize_appointment_form(data: dict) -> dict:
    """Return a copy of *data* with all string values stripped of leading/trailing whitespace."""
    return {
        field: data[field].strip() if isinstance(data[field], str) else data[field]
        for field in REQUIRED_FIELDS
        if field in data
    }


# ---------------------------------------------------------------------------
# Time range helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimeRange:
    """Half-open time interval [start, end)."""

    start: time
    end: time

    def duration_minutes(self) -> int:
        """Return the length of this interval in whole minutes."""
        start_dt = datetime.combine(date.min, self.start)
        end_dt = datetime.combine(date.min, self.end)
        return int((end_dt - start_dt).total_seconds() / 60)

    def overlaps(self, other: "TimeRange") -> bool:
        """Return True if this range overlaps with *other*."""
        return self.start < other.end and other.start < self.end

    def split(self, slot_minutes: int) -> List[time]:
        """Return a list of slot start times of *slot_minutes* each.

        Partial trailing slots (shorter than *slot_minutes*) are discarded.
        """
        if slot_minutes <= 0:
            raise ValueError("slot_minutes must be positive")

        slots: List[time] = []
        current = datetime.combine(date.min, self.start)
        end_dt = datetime.combine(date.min, self.end)
        delta = timedelta(minutes=slot_minutes)

        while current + delta <= end_dt:
            slots.append(current.time())
            current += delta

        return slots

    def subtract(self, blocked: List["TimeRange"]) -> List["TimeRange"]:
        """Return the sub-ranges remaining after removing all *blocked* intervals."""
        remaining: List[TimeRange] = [self]

        for block in blocked:
            updated: List[TimeRange] = []
            for segment in remaining:
                updated.extend(_subtract_segment(segment, block))
            remaining = updated

        return remaining


def _subtract_segment(segment: TimeRange, block: TimeRange) -> List[TimeRange]:
    """Remove *block* from *segment* and return the leftover pieces."""
    seg_start = datetime.combine(date.min, segment.start)
    seg_end = datetime.combine(date.min, segment.end)
    blk_start = datetime.combine(date.min, block.start)
    blk_end = datetime.combine(date.min, block.end)

    # No overlap — keep segment as-is.
    if blk_end <= seg_start or blk_start >= seg_end:
        return [segment]

    pieces: List[TimeRange] = []

    if blk_start > seg_start:
        pieces.append(TimeRange(start=seg_start.time(), end=min(blk_start, seg_end).time()))

    if blk_end < seg_end:
        pieces.append(TimeRange(start=max(blk_end, seg_start).time(), end=seg_end.time()))

    return pieces


# ---------------------------------------------------------------------------
# Slot generation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DailyAvailability:
    """Aggregated availability data for one doctor on one calendar day."""

    date: date
    working_hours: TimeRange
    blocked_periods: List[TimeRange]
    slot_minutes: int


def generate_available_slots(availability: DailyAvailability) -> List[datetime]:
    """Return sorted datetimes for every bookable slot in *availability*.

    The function is intentionally pure (no I/O). The caller is responsible for
    - Loading availability rules from the database.
    - Filtering out slots already taken by existing appointments.
    """
    if availability.slot_minutes <= 0:
        raise ValueError("slot_minutes must be positive")

    unblocked = availability.working_hours.subtract(availability.blocked_periods)

    slots: List[datetime] = []
    for segment in unblocked:
        for t in segment.split(availability.slot_minutes):
            slots.append(datetime.combine(availability.date, t))

    slots.sort()
    return slots


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def has_conflict(
    proposed_start: datetime,
    proposed_end: datetime,
    existing_appointments: List[tuple[datetime, datetime]],
) -> bool:
    """Return True if *proposed_start..proposed_end* overlaps any existing appointment.

    *existing_appointments* is a list of (start, end) pairs for appointments
    already on the books.  Overlap is defined as half-open intervals:
    [proposed_start, proposed_end) vs [existing_start, existing_end).
    """
    for existing_start, existing_end in existing_appointments:
        if proposed_start < existing_end and existing_start < proposed_end:
            return True
    return False


def filter_conflicting_slots(
    slots: List[datetime],
    slot_minutes: int,
    existing_appointments: List[tuple[datetime, datetime]],
) -> List[datetime]:
    """Remove from *slots* any slot that conflicts with *existing_appointments*."""
    delta = timedelta(minutes=slot_minutes)
    return [
        s for s in slots
        if not has_conflict(s, s + delta, existing_appointments)
    ]


# ---------------------------------------------------------------------------
# Booking entry point (pure, no I/O)
# ---------------------------------------------------------------------------

def book_appointment(
    form_data: dict,
    proposed_start: datetime,
    slot_minutes: int,
    existing_appointments: List[tuple[datetime, datetime]],
) -> tuple[bool, Optional[dict], list[str]]:
    """Attempt to book an appointment.

    Returns (success, normalized_data_or_None, list_of_errors).

    Steps:
    1. Validate the form data.
    2. Check for scheduling conflicts.
    """
    is_valid, field_errors = validate_appointment_form(form_data)
    if not is_valid:
        return False, None, field_errors

    proposed_end = proposed_start + timedelta(minutes=slot_minutes)
    if has_conflict(proposed_start, proposed_end, existing_appointments):
        return False, None, ["time_slot_conflict"]

    normalized = normalize_appointment_form(form_data)
    normalized["start"] = proposed_start.isoformat()
    normalized["end"] = proposed_end.isoformat()
    return True, normalized, []
