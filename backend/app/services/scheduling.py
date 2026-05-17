from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List


@dataclass(frozen=True)
class TimeRange:
    """Represents a half-open time interval [start, end)."""

    start: time
    end: time

    def duration_minutes(self) -> int:
        return int(
            (datetime.combine(date.min, self.end) - datetime.combine(date.min, self.start))
            .total_seconds()
            / 60
        )

    def split(self, slot_minutes: int) -> List[time]:
        """Split this range into start times for fixed-size slots.

        The last partial slot (shorter than slot_minutes) is discarded.
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
        """Return remaining sub-ranges after removing all blocked intervals.

        All ranges are assumed to be on the same day and in local clinic time.
        """
        # Start with the full range as the only available segment.
        remaining: List[TimeRange] = [self]

        for block in blocked:
            updated: List[TimeRange] = []
            for segment in remaining:
                updated.extend(_subtract_segment(segment, block))
            remaining = updated

        return remaining


def _subtract_segment(segment: TimeRange, block: TimeRange) -> List[TimeRange]:
    """Subtract a single blocked interval from a segment."""
    seg_start = datetime.combine(date.min, segment.start)
    seg_end = datetime.combine(date.min, segment.end)
    blk_start = datetime.combine(date.min, block.start)
    blk_end = datetime.combine(date.min, block.end)

    # No overlap.
    if blk_end <= seg_start or blk_start >= seg_end:
        return [segment]

    pieces: List[TimeRange] = []

    # Left piece, if any.
    if blk_start > seg_start:
        pieces.append(
            TimeRange(
                start=seg_start.time(),
                end=min(blk_start, seg_end).time(),
            )
        )

    # Right piece, if any.
    if blk_end < seg_end:
        pieces.append(
            TimeRange(
                start=max(blk_end, seg_start).time(),
                end=seg_end.time(),
            )
        )

    return pieces


@dataclass(frozen=True)
class DailyAvailability:
    """Normalized availability information for a single doctor on one day."""

    date: date
    working_hours: TimeRange
    blocked_periods: List[TimeRange]
    slot_minutes: int
    max_appointments_per_slot: int = 1


def generate_available_slots(availability: DailyAvailability) -> List[datetime]:
    """Generate concrete start datetimes for all valid slots on a given day.

    This function is intentionally pure and does not talk to the database.
    The calling code is responsible for:
    - Retrieving availability rules (working days/hours, breaks, holidays).
    - Converting them into a DailyAvailability instance.
    - Filtering out slots that conflict with existing appointments.
    """
    if availability.slot_minutes <= 0:
        raise ValueError("slot_minutes must be positive")

    base_range = availability.working_hours
    # Remove blocked periods (e.g. lunch, meetings, clinic closures).
    unblocked_segments = base_range.subtract(availability.blocked_periods)

    slots: List[datetime] = []
    for segment in unblocked_segments:
        for t in segment.split(availability.slot_minutes):
            slots.append(datetime.combine(availability.date, t))

    # Sort to be safe, in case segments were not ordered.
    slots.sort()
    return slots

