"""
Unit tests for backend/app/services/scheduling.py.

Run with:  pytest backend/tests/unit/test_scheduling.py -v
Mutation testing:  mutmut run --paths-to-mutate app/services/scheduling.py \
                               --tests-dir tests/unit
"""
import pytest
from datetime import date, time, datetime
from app.services.scheduling import TimeRange, DailyAvailability, generate_available_slots


# ─── TimeRange.duration_minutes ───────────────────────────────────────────────

class TestTimeRangeDuration:
    def test_one_hour_range(self):
        r = TimeRange(start=time(9, 0), end=time(10, 0))
        assert r.duration_minutes() == 60

    def test_zero_duration(self):
        r = TimeRange(start=time(9, 0), end=time(9, 0))
        assert r.duration_minutes() == 0

    def test_partial_hour(self):
        r = TimeRange(start=time(9, 0), end=time(9, 30))
        assert r.duration_minutes() == 30

    def test_full_day(self):
        r = TimeRange(start=time(0, 0), end=time(23, 59))
        assert r.duration_minutes() == 23 * 60 + 59


# ─── TimeRange.split ──────────────────────────────────────────────────────────

class TestTimeRangeSplit:
    def test_exact_fit_two_slots(self):
        # 9:00–10:00, 30-min slots → [09:00, 09:30]
        r = TimeRange(start=time(9, 0), end=time(10, 0))
        assert r.split(30) == [time(9, 0), time(9, 30)]

    def test_partial_slot_discarded(self):
        # 9:00–9:45, 30-min slots → [09:00]; 9:30–9:45 partial slot dropped
        r = TimeRange(start=time(9, 0), end=time(9, 45))
        assert r.split(30) == [time(9, 0)]

    def test_no_slots_when_range_shorter_than_slot(self):
        r = TimeRange(start=time(9, 0), end=time(9, 20))
        assert r.split(30) == []

    def test_zero_slot_minutes_raises(self):
        r = TimeRange(start=time(9, 0), end=time(10, 0))
        with pytest.raises(ValueError):
            r.split(0)

    def test_negative_slot_minutes_raises(self):
        r = TimeRange(start=time(9, 0), end=time(10, 0))
        with pytest.raises(ValueError):
            r.split(-15)

    def test_single_slot_exactly_fills_range(self):
        r = TimeRange(start=time(9, 0), end=time(9, 30))
        assert r.split(30) == [time(9, 0)]

    def test_boundary_slot_included(self):
        # Slot that ends exactly at range end must be included (not excluded)
        r = TimeRange(start=time(9, 0), end=time(10, 0))
        # 60-minute slot from 9:00 ends exactly at 10:00 — must be included
        assert r.split(60) == [time(9, 0)]

    def test_empty_range_produces_no_slots(self):
        r = TimeRange(start=time(12, 0), end=time(12, 0))
        assert r.split(30) == []


# ─── TimeRange.subtract ───────────────────────────────────────────────────────

class TestTimeRangeSubtract:
    def test_subtract_middle_lunch(self):
        # 9:00–17:00 minus 12:00–13:00 → [9:00–12:00, 13:00–17:00]
        base  = TimeRange(start=time(9, 0),  end=time(17, 0))
        lunch = TimeRange(start=time(12, 0), end=time(13, 0))
        result = base.subtract([lunch])
        assert result == [
            TimeRange(start=time(9,  0), end=time(12, 0)),
            TimeRange(start=time(13, 0), end=time(17, 0)),
        ]

    def test_subtract_no_overlap(self):
        base  = TimeRange(start=time(9, 0),  end=time(12, 0))
        after = TimeRange(start=time(13, 0), end=time(14, 0))
        result = base.subtract([after])
        assert result == [base]

    def test_subtract_full_overlap(self):
        base  = TimeRange(start=time(9,  0), end=time(10, 0))
        block = TimeRange(start=time(9,  0), end=time(10, 0))
        assert base.subtract([block]) == []

    def test_adjacent_block_no_overlap(self):
        # Block that ends exactly where segment starts is NOT overlapping
        base  = TimeRange(start=time(10, 0), end=time(12, 0))
        block = TimeRange(start=time(9,  0), end=time(10, 0))
        result = base.subtract([block])
        assert result == [base]

    def test_block_at_end_of_segment(self):
        # Block overlaps the end of the segment
        base  = TimeRange(start=time(9,  0), end=time(12, 0))
        block = TimeRange(start=time(11, 0), end=time(13, 0))
        result = base.subtract([block])
        assert result == [TimeRange(start=time(9, 0), end=time(11, 0))]

    def test_multiple_blocks(self):
        # 9:00–17:00 minus [10:00–10:30, 12:00–13:00]
        base   = TimeRange(start=time(9,  0), end=time(17, 0))
        blocks = [
            TimeRange(start=time(10, 0), end=time(10, 30)),
            TimeRange(start=time(12, 0), end=time(13, 0)),
        ]
        result = base.subtract(blocks)
        assert len(result) == 3
        assert result[0] == TimeRange(time(9,  0), time(10, 0))
        assert result[1] == TimeRange(time(10, 30), time(12, 0))
        assert result[2] == TimeRange(time(13, 0), time(17, 0))


# ─── generate_available_slots ─────────────────────────────────────────────────

class TestGenerateAvailableSlots:
    def test_weekday_no_blocks(self):
        avail = DailyAvailability(
            date=date(2026, 4, 7),
            working_hours=TimeRange(time(9, 0), time(11, 0)),
            blocked_periods=[],
            slot_minutes=30,
        )
        slots = generate_available_slots(avail)
        assert slots == [
            datetime(2026, 4, 7, 9,  0),
            datetime(2026, 4, 7, 9, 30),
            datetime(2026, 4, 7, 10, 0),
            datetime(2026, 4, 7, 10, 30),
        ]

    def test_blocked_lunch_reduces_slots(self):
        avail = DailyAvailability(
            date=date(2026, 4, 7),
            working_hours=TimeRange(time(9, 0), time(14, 0)),
            blocked_periods=[TimeRange(time(12, 0), time(13, 0))],
            slot_minutes=60,
        )
        slots = generate_available_slots(avail)
        # 9–10, 10–11, 11–12, 13–14  (not 12–13 which is blocked)
        assert len(slots) == 4
        assert datetime(2026, 4, 7, 12, 0) not in slots
        assert datetime(2026, 4, 7, 13, 0) in slots

    def test_empty_working_hours_no_slots(self):
        avail = DailyAvailability(
            date=date(2026, 4, 7),
            working_hours=TimeRange(time(9, 0), time(9, 0)),
            blocked_periods=[],
            slot_minutes=30,
        )
        assert generate_available_slots(avail) == []

    def test_zero_slot_minutes_raises(self):
        avail = DailyAvailability(
            date=date(2026, 4, 7),
            working_hours=TimeRange(time(9, 0), time(17, 0)),
            blocked_periods=[],
            slot_minutes=0,
        )
        with pytest.raises(ValueError):
            generate_available_slots(avail)

    def test_slots_are_sorted(self):
        # Even with multiple unblocked segments, output must be sorted
        avail = DailyAvailability(
            date=date(2026, 4, 7),
            working_hours=TimeRange(time(9, 0), time(14, 0)),
            blocked_periods=[TimeRange(time(11, 0), time(12, 0))],
            slot_minutes=60,
        )
        slots = generate_available_slots(avail)
        assert slots == sorted(slots)
