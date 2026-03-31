"""Tests for src/booking.py — Patient Experience booking logic."""
import pytest
from datetime import date, datetime, time, timedelta

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.booking import (
    REQUIRED_FIELDS,
    DailyAvailability,
    TimeRange,
    _subtract_segment,
    book_appointment,
    filter_conflicting_slots,
    generate_available_slots,
    has_conflict,
    normalize_appointment_form,
    validate_appointment_form,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_FORM = {
    "name": "Maria",
    "surname": "Garcia",
    "symptoms_and_or_allergies": "headache",
    "medications": "ibuprofen",
}


def _availability(
    slot_minutes=30,
    work_start=time(9, 0),
    work_end=time(17, 0),
    blocked=None,
    target_date=date(2025, 6, 2),  # Monday
):
    return DailyAvailability(
        date=target_date,
        working_hours=TimeRange(start=work_start, end=work_end),
        blocked_periods=blocked or [],
        slot_minutes=slot_minutes,
    )


# ---------------------------------------------------------------------------
# validate_appointment_form
# ---------------------------------------------------------------------------

class TestValidateAppointmentForm:
    def test_valid_form_returns_true_no_errors(self):
        ok, errors = validate_appointment_form(VALID_FORM)
        assert ok is True
        assert errors == []

    def test_missing_field_returns_false(self):
        data = {k: v for k, v in VALID_FORM.items() if k != "name"}
        ok, errors = validate_appointment_form(data)
        assert ok is False
        assert "name" in errors

    def test_blank_string_field_returns_false(self):
        data = {**VALID_FORM, "surname": "   "}
        ok, errors = validate_appointment_form(data)
        assert ok is False
        assert "surname" in errors

    def test_none_field_returns_false(self):
        data = {**VALID_FORM, "medications": None}
        ok, errors = validate_appointment_form(data)
        assert ok is False
        assert "medications" in errors

    def test_all_fields_missing_returns_all_errors(self):
        ok, errors = validate_appointment_form({})
        assert ok is False
        assert set(errors) == set(REQUIRED_FIELDS)

    def test_non_dict_input_returns_false_all_errors(self):
        ok, errors = validate_appointment_form("bad input")
        assert ok is False
        assert len(errors) == len(REQUIRED_FIELDS)

    def test_extra_fields_are_ignored(self):
        data = {**VALID_FORM, "extra": "ignored"}
        ok, errors = validate_appointment_form(data)
        assert ok is True
        assert errors == []

    def test_empty_string_field_returns_false(self):
        data = {**VALID_FORM, "name": ""}
        ok, errors = validate_appointment_form(data)
        assert ok is False
        assert "name" in errors


# ---------------------------------------------------------------------------
# normalize_appointment_form
# ---------------------------------------------------------------------------

class TestNormalizeAppointmentForm:
    def test_strips_whitespace(self):
        data = {**VALID_FORM, "name": "  Ana  "}
        result = normalize_appointment_form(data)
        assert result["name"] == "Ana"

    def test_non_string_values_unchanged(self):
        data = {**VALID_FORM, "medications": 42}
        result = normalize_appointment_form(data)
        assert result["medications"] == 42

    def test_only_required_fields_in_output(self):
        data = {**VALID_FORM, "extra": "ignored"}
        result = normalize_appointment_form(data)
        assert "extra" not in result
        assert set(result.keys()) == set(REQUIRED_FIELDS)


# ---------------------------------------------------------------------------
# TimeRange.duration_minutes
# ---------------------------------------------------------------------------

class TestTimeRangeDurationMinutes:
    def test_one_hour(self):
        tr = TimeRange(start=time(9, 0), end=time(10, 0))
        assert tr.duration_minutes() == 60

    def test_thirty_minutes(self):
        tr = TimeRange(start=time(12, 0), end=time(12, 30))
        assert tr.duration_minutes() == 30

    def test_zero_duration(self):
        tr = TimeRange(start=time(9, 0), end=time(9, 0))
        assert tr.duration_minutes() == 0

    def test_full_working_day(self):
        tr = TimeRange(start=time(9, 0), end=time(17, 0))
        assert tr.duration_minutes() == 480


# ---------------------------------------------------------------------------
# TimeRange.overlaps
# ---------------------------------------------------------------------------

class TestTimeRangeOverlaps:
    def test_overlapping_ranges(self):
        a = TimeRange(start=time(9, 0), end=time(10, 0))
        b = TimeRange(start=time(9, 30), end=time(10, 30))
        assert a.overlaps(b) is True
        assert b.overlaps(a) is True

    def test_adjacent_ranges_do_not_overlap(self):
        a = TimeRange(start=time(9, 0), end=time(10, 0))
        b = TimeRange(start=time(10, 0), end=time(11, 0))
        assert a.overlaps(b) is False
        assert b.overlaps(a) is False

    def test_non_overlapping_ranges(self):
        a = TimeRange(start=time(9, 0), end=time(10, 0))
        b = TimeRange(start=time(11, 0), end=time(12, 0))
        assert a.overlaps(b) is False

    def test_contained_range_overlaps(self):
        outer = TimeRange(start=time(9, 0), end=time(17, 0))
        inner = TimeRange(start=time(12, 0), end=time(13, 0))
        assert outer.overlaps(inner) is True


# ---------------------------------------------------------------------------
# TimeRange.split
# ---------------------------------------------------------------------------

class TestTimeRangeSplit:
    def test_even_split(self):
        tr = TimeRange(start=time(9, 0), end=time(11, 0))
        slots = tr.split(30)
        assert slots == [time(9, 0), time(9, 30), time(10, 0), time(10, 30)]

    def test_partial_slot_discarded(self):
        tr = TimeRange(start=time(9, 0), end=time(9, 45))
        slots = tr.split(30)
        assert slots == [time(9, 0)]

    def test_zero_duration_range_returns_no_slots(self):
        tr = TimeRange(start=time(9, 0), end=time(9, 0))
        assert tr.split(30) == []

    def test_invalid_slot_minutes_raises(self):
        tr = TimeRange(start=time(9, 0), end=time(10, 0))
        with pytest.raises(ValueError):
            tr.split(0)
        with pytest.raises(ValueError):
            tr.split(-10)

    def test_slot_larger_than_range(self):
        tr = TimeRange(start=time(9, 0), end=time(9, 20))
        assert tr.split(30) == []


# ---------------------------------------------------------------------------
# _subtract_segment / TimeRange.subtract
# ---------------------------------------------------------------------------

class TestSubtractSegment:
    def test_no_overlap_returns_original(self):
        seg = TimeRange(start=time(9, 0), end=time(12, 0))
        block = TimeRange(start=time(13, 0), end=time(14, 0))
        assert _subtract_segment(seg, block) == [seg]

    def test_block_covers_segment_entirely(self):
        seg = TimeRange(start=time(9, 0), end=time(10, 0))
        block = TimeRange(start=time(8, 0), end=time(11, 0))
        assert _subtract_segment(seg, block) == []

    def test_block_removes_middle(self):
        seg = TimeRange(start=time(9, 0), end=time(17, 0))
        block = TimeRange(start=time(12, 0), end=time(13, 0))
        result = _subtract_segment(seg, block)
        assert result == [
            TimeRange(start=time(9, 0), end=time(12, 0)),
            TimeRange(start=time(13, 0), end=time(17, 0)),
        ]

    def test_block_clips_start(self):
        seg = TimeRange(start=time(9, 0), end=time(12, 0))
        block = TimeRange(start=time(8, 0), end=time(10, 0))
        result = _subtract_segment(seg, block)
        assert result == [TimeRange(start=time(10, 0), end=time(12, 0))]

    def test_block_clips_end(self):
        seg = TimeRange(start=time(9, 0), end=time(12, 0))
        block = TimeRange(start=time(11, 0), end=time(13, 0))
        result = _subtract_segment(seg, block)
        assert result == [TimeRange(start=time(9, 0), end=time(11, 0))]


class TestTimeRangeSubtract:
    def test_subtract_single_block(self):
        tr = TimeRange(start=time(9, 0), end=time(17, 0))
        blocked = [TimeRange(start=time(12, 0), end=time(13, 0))]
        result = tr.subtract(blocked)
        assert result == [
            TimeRange(start=time(9, 0), end=time(12, 0)),
            TimeRange(start=time(13, 0), end=time(17, 0)),
        ]

    def test_subtract_multiple_blocks(self):
        tr = TimeRange(start=time(9, 0), end=time(17, 0))
        blocked = [
            TimeRange(start=time(10, 0), end=time(10, 30)),
            TimeRange(start=time(12, 0), end=time(13, 0)),
        ]
        result = tr.subtract(blocked)
        assert len(result) == 3

    def test_subtract_empty_list_returns_self(self):
        tr = TimeRange(start=time(9, 0), end=time(17, 0))
        result = tr.subtract([])
        assert result == [tr]


# ---------------------------------------------------------------------------
# generate_available_slots
# ---------------------------------------------------------------------------

class TestGenerateAvailableSlots:
    def test_standard_day_returns_correct_count(self):
        # 9–17 with lunch 12–13 = 7 hours = 14 slots of 30 min
        avail = _availability(blocked=[TimeRange(start=time(12, 0), end=time(13, 0))])
        slots = generate_available_slots(avail)
        assert len(slots) == 14

    def test_slots_are_sorted(self):
        avail = _availability()
        slots = generate_available_slots(avail)
        assert slots == sorted(slots)

    def test_zero_duration_working_hours_returns_no_slots(self):
        avail = _availability(work_start=time(9, 0), work_end=time(9, 0))
        assert generate_available_slots(avail) == []

    def test_negative_slot_minutes_raises(self):
        avail = _availability(slot_minutes=-1)
        with pytest.raises(ValueError):
            generate_available_slots(avail)

    def test_all_slots_on_correct_date(self):
        target = date(2025, 6, 2)
        avail = _availability(target_date=target)
        slots = generate_available_slots(avail)
        assert all(s.date() == target for s in slots)

    def test_no_blocked_periods_full_day(self):
        # 9–17 no lunch = 8 hours = 16 slots
        avail = _availability(blocked=[])
        slots = generate_available_slots(avail)
        assert len(slots) == 16

    def test_slot_minutes_60(self):
        avail = _availability(slot_minutes=60, blocked=[])
        slots = generate_available_slots(avail)
        assert len(slots) == 8


# ---------------------------------------------------------------------------
# has_conflict
# ---------------------------------------------------------------------------

class TestHasConflict:
    BASE = datetime(2025, 6, 2, 10, 0)

    def test_no_existing_appointments_no_conflict(self):
        assert has_conflict(self.BASE, self.BASE + timedelta(minutes=30), []) is False

    def test_direct_overlap_is_conflict(self):
        existing = [(self.BASE, self.BASE + timedelta(minutes=30))]
        assert has_conflict(self.BASE, self.BASE + timedelta(minutes=30), existing) is True

    def test_adjacent_slots_no_conflict(self):
        slot_end = self.BASE + timedelta(minutes=30)
        existing = [(slot_end, slot_end + timedelta(minutes=30))]
        assert has_conflict(self.BASE, slot_end, existing) is False

    def test_partial_overlap_is_conflict(self):
        existing = [(self.BASE + timedelta(minutes=15), self.BASE + timedelta(minutes=45))]
        assert has_conflict(self.BASE, self.BASE + timedelta(minutes=30), existing) is True

    def test_proposed_inside_existing_is_conflict(self):
        existing = [(self.BASE - timedelta(minutes=15), self.BASE + timedelta(minutes=45))]
        assert has_conflict(self.BASE, self.BASE + timedelta(minutes=30), existing) is True

    def test_existing_inside_proposed_is_conflict(self):
        existing = [(self.BASE + timedelta(minutes=5), self.BASE + timedelta(minutes=10))]
        assert has_conflict(self.BASE, self.BASE + timedelta(minutes=30), existing) is True

    def test_proposed_before_all_existing_no_conflict(self):
        existing = [(self.BASE + timedelta(hours=2), self.BASE + timedelta(hours=3))]
        assert has_conflict(self.BASE, self.BASE + timedelta(minutes=30), existing) is False


# ---------------------------------------------------------------------------
# filter_conflicting_slots
# ---------------------------------------------------------------------------

class TestFilterConflictingSlots:
    BASE_DATE = date(2025, 6, 2)

    def test_removes_conflicting_slot(self):
        slot = datetime(2025, 6, 2, 9, 0)
        existing = [(slot, slot + timedelta(minutes=30))]
        result = filter_conflicting_slots([slot], 30, existing)
        assert result == []

    def test_keeps_non_conflicting_slots(self):
        slot1 = datetime(2025, 6, 2, 9, 0)
        slot2 = datetime(2025, 6, 2, 9, 30)
        existing = [(slot1, slot1 + timedelta(minutes=30))]
        result = filter_conflicting_slots([slot1, slot2], 30, existing)
        assert result == [slot2]

    def test_empty_existing_keeps_all(self):
        slots = [datetime(2025, 6, 2, h, 0) for h in range(9, 12)]
        assert filter_conflicting_slots(slots, 30, []) == slots


# ---------------------------------------------------------------------------
# book_appointment
# ---------------------------------------------------------------------------

class TestBookAppointment:
    START = datetime(2025, 6, 2, 10, 0)

    def test_valid_booking_succeeds(self):
        ok, data, errors = book_appointment(VALID_FORM, self.START, 30, [])
        assert ok is True
        assert errors == []
        assert data is not None
        assert data["name"] == "Maria"
        assert "start" in data
        assert "end" in data

    def test_invalid_form_returns_false(self):
        bad_form = {k: v for k, v in VALID_FORM.items() if k != "name"}
        ok, data, errors = book_appointment(bad_form, self.START, 30, [])
        assert ok is False
        assert "name" in errors
        assert data is None

    def test_conflict_returns_false(self):
        existing = [(self.START, self.START + timedelta(minutes=30))]
        ok, data, errors = book_appointment(VALID_FORM, self.START, 30, existing)
        assert ok is False
        assert "time_slot_conflict" in errors
        assert data is None

    def test_normalized_form_data_in_result(self):
        form = {**VALID_FORM, "name": "  Ana  "}
        ok, data, errors = book_appointment(form, self.START, 30, [])
        assert ok is True
        assert data["name"] == "Ana"

    def test_end_time_computed_from_slot_minutes(self):
        ok, data, errors = book_appointment(VALID_FORM, self.START, 45, [])
        assert ok is True
        expected_end = (self.START + timedelta(minutes=45)).isoformat()
        assert data["end"] == expected_end


# ---------------------------------------------------------------------------
# Mutant-killing tests (added after initial mutation run)
# ---------------------------------------------------------------------------

class TestTimeRangeFrozen:
    """Mutants 17 & 51: frozen=True vs frozen=False on dataclasses."""

    def test_time_range_is_hashable(self):
        # frozen=True dataclasses are hashable; frozen=False are not
        tr = TimeRange(start=time(9, 0), end=time(10, 0))
        s = {tr}  # raises TypeError if not hashable
        assert tr in s

    def test_daily_availability_is_immutable(self):
        avail = DailyAvailability(
            date=date(2025, 6, 2),
            working_hours=TimeRange(start=time(9, 0), end=time(17, 0)),
            blocked_periods=[],
            slot_minutes=30,
        )
        with pytest.raises((AttributeError, TypeError)):
            avail.slot_minutes = 60  # type: ignore[misc]

    def test_time_range_is_immutable(self):
        tr = TimeRange(start=time(9, 0), end=time(10, 0))
        with pytest.raises((AttributeError, TypeError)):
            tr.start = time(8, 0)  # type: ignore[misc]


class TestSplitBoundaryAndMessage:
    """Mutants 28 & 29: slot_minutes boundary and error message in split."""

    def test_slot_minutes_1_is_valid(self):
        # Mutant 28 changes <= 0 to <= 1, which would wrongly reject slot_minutes=1
        tr = TimeRange(start=time(9, 0), end=time(9, 5))
        slots = tr.split(1)
        assert len(slots) == 5

    def test_invalid_slot_minutes_error_message(self):
        # Mutant 29 corrupts the error message string.
        # Use anchored pattern so the corrupted "XXslot_minutes...XX" does NOT match.
        tr = TimeRange(start=time(9, 0), end=time(10, 0))
        with pytest.raises(ValueError, match=r"^slot_minutes must be positive$"):
            tr.split(0)


class TestSubtractSegmentBoundaries:
    """Mutants 45-47, 49, 50: boundary conditions in _subtract_segment."""

    def test_block_end_equals_seg_start_no_overlap(self):
        # Mutant 45: blk_end <= seg_start should NOT overlap; changing to < would treat adjacent as overlap
        seg = TimeRange(start=time(10, 0), end=time(12, 0))
        block = TimeRange(start=time(9, 0), end=time(10, 0))  # end == seg.start
        result = _subtract_segment(seg, block)
        assert result == [seg]

    def test_block_start_equals_seg_end_no_overlap(self):
        # Mutant 46: blk_start >= seg_end should NOT overlap; changing to > would treat adjacent as overlap
        seg = TimeRange(start=time(9, 0), end=time(10, 0))
        block = TimeRange(start=time(10, 0), end=time(11, 0))  # start == seg.end
        result = _subtract_segment(seg, block)
        assert result == [seg]

    def test_block_starts_before_seg_starts_within_seg(self):
        # Mutant 47: `or` changed to `and` would break non-overlap detection when only one condition true
        seg = TimeRange(start=time(10, 0), end=time(12, 0))
        block = TimeRange(start=time(8, 0), end=time(11, 0))
        result = _subtract_segment(seg, block)
        # Should leave only the right piece
        assert result == [TimeRange(start=time(11, 0), end=time(12, 0))]

    def test_block_starts_at_segment_start_no_left_piece(self):
        # Mutant 49: `> seg_start` changed to `>= seg_start` would add a zero-length left piece
        seg = TimeRange(start=time(9, 0), end=time(12, 0))
        block = TimeRange(start=time(9, 0), end=time(10, 0))  # block.start == seg.start
        result = _subtract_segment(seg, block)
        # Only a right piece; no zero-length left piece
        assert result == [TimeRange(start=time(10, 0), end=time(12, 0))]

    def test_block_ends_at_segment_end_no_right_piece(self):
        # Mutant 50: `< seg_end` changed to `<= seg_end` would add a zero-length right piece
        seg = TimeRange(start=time(9, 0), end=time(12, 0))
        block = TimeRange(start=time(11, 0), end=time(12, 0))  # block.end == seg.end
        result = _subtract_segment(seg, block)
        # Only a left piece; no zero-length right piece
        assert result == [TimeRange(start=time(9, 0), end=time(11, 0))]


class TestGenerateSlotsBoundaryAndMessage:
    """Mutants 53-55: slot_minutes boundary and error message in generate_available_slots."""

    def test_slot_minutes_zero_raises(self):
        # Mutant 53: <= 0 changed to < 0 would let slot_minutes=0 through.
        # Use fully-blocked working hours so that if the early guard is skipped,
        # unblocked_segments is [] and split() is never called → function returns []
        # instead of raising ValueError, making the mutant detectable.
        avail = DailyAvailability(
            date=date(2025, 6, 2),
            working_hours=TimeRange(start=time(9, 0), end=time(17, 0)),
            blocked_periods=[TimeRange(start=time(9, 0), end=time(17, 0))],  # fully blocked
            slot_minutes=0,
        )
        with pytest.raises(ValueError):
            generate_available_slots(avail)

    def test_slot_minutes_1_is_valid_for_generate(self):
        # Mutant 54: <= 0 changed to <= 1 would wrongly reject slot_minutes=1
        avail = _availability(slot_minutes=1, work_start=time(9, 0), work_end=time(9, 5), blocked=[])
        slots = generate_available_slots(avail)
        assert len(slots) == 5

    def test_generate_slots_error_message(self):
        # Mutant 55: corrupted error message string.
        # Use anchored pattern so "XXslot_minutes...XX" does NOT match.
        avail = _availability(slot_minutes=-5)
        with pytest.raises(ValueError, match=r"^slot_minutes must be positive$"):
            generate_available_slots(avail)


class TestBookAppointmentStartValue:
    """Mutant 75: normalized["start"] set to None instead of proposed_start.isoformat()."""

    START = datetime(2025, 6, 2, 10, 0)

    def test_start_value_matches_proposed_start(self):
        ok, data, errors = book_appointment(VALID_FORM, self.START, 30, [])
        assert ok is True
        assert data["start"] == self.START.isoformat()

    def test_start_is_not_none(self):
        ok, data, errors = book_appointment(VALID_FORM, self.START, 30, [])
        assert ok is True
        assert data["start"] is not None
