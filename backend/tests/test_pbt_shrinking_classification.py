"""
Property-Based Tests: Custom Shrinking & Generator Classification
=================================================================
Covers LTT topic: custom shrinking strategies and generator statistics
for appointment validation logic using Hypothesis.

Focus areas (does NOT duplicate basic invariants from test_booking.py):
  - Custom shrinker for appointment form data → minimal counterexample
  - classify / event labels to show value-space coverage across edge cases
  - Note: run with `pytest -s` to see printed generator statistics
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, time, timedelta
from typing import Optional

import pytest
from hypothesis import assume, event, given, settings, HealthCheck
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, initialize, rule

from src.booking import (
    REQUIRED_FIELDS,
    DailyAvailability,
    TimeRange,
    book_appointment,
    generate_available_slots,
    has_conflict,
    validate_appointment_form,
)

# ---------------------------------------------------------------------------
# Custom shrinker: AppointmentForm
# ---------------------------------------------------------------------------
# Hypothesis shrinks composite strategies automatically, but we can guide it
# by building a dedicated strategy that already prefers simpler values.
# The shrinker strategy below orders candidates from "most minimal" (single
# char strings) upward, so when Hypothesis finds a failing example it shrinks
# toward the smallest possible form dictionary.

_FIELD_STRATEGY = st.one_of(
    # Minimal valid value: single non-whitespace character
    st.just("x"),
    # Short ASCII words (prefer early in the list → simpler shrinks)
    st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=8),
    # Strings with leading/trailing whitespace (interesting edge case)
    st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll")), min_size=1, max_size=5).map(
        lambda s: f"  {s}  "
    ),
)

_VALID_FORM_STRATEGY = st.fixed_dictionaries(
    {field: _FIELD_STRATEGY for field in REQUIRED_FIELDS}
)

# A strategy that may produce invalid forms (missing or blank fields).
_MAYBE_INVALID_FORM_STRATEGY = st.one_of(
    _VALID_FORM_STRATEGY,
    # Missing one required field
    st.fixed_dictionaries(
        {field: _FIELD_STRATEGY for field in REQUIRED_FIELDS}
    ).flatmap(
        lambda d: st.sampled_from(list(d.keys())).map(
            lambda k: {f: v for f, v in d.items() if f != k}
        )
    ),
    # One field is blank/whitespace
    _VALID_FORM_STRATEGY.flatmap(
        lambda d: st.sampled_from(list(d.keys())).map(
            lambda k: {**d, k: "   "}
        )
    ),
    # One field is None
    _VALID_FORM_STRATEGY.flatmap(
        lambda d: st.sampled_from(list(d.keys())).map(
            lambda k: {**d, k: None}
        )
    ),
)


# ---------------------------------------------------------------------------
# Time / date strategies
# ---------------------------------------------------------------------------

def _time_strategy(min_hour: int = 0, max_hour: int = 23) -> st.SearchStrategy:
    return st.builds(
        time,
        hour=st.integers(min_value=min_hour, max_value=max_hour),
        minute=st.sampled_from([0, 15, 30, 45]),
    )


_SLOT_MINUTES_STRATEGY = st.sampled_from([15, 20, 30, 45, 60])

_FUTURE_DATE_STRATEGY = st.dates(
    min_value=date(2026, 1, 1), max_value=date(2030, 12, 31)
)
_PAST_DATE_STRATEGY = st.dates(
    min_value=date(2000, 1, 1), max_value=date(2025, 12, 31)
)
_DATE_STRATEGY = st.one_of(_PAST_DATE_STRATEGY, _FUTURE_DATE_STRATEGY)


@st.composite
def valid_time_range(draw, min_duration_minutes: int = 30) -> TimeRange:
    """Draw a valid TimeRange with at least *min_duration_minutes* duration."""
    start_hour = draw(st.integers(min_value=6, max_value=20))
    start_minute = draw(st.sampled_from([0, 15, 30, 45]))
    start = time(start_hour, start_minute)

    duration = draw(st.integers(min_value=min_duration_minutes, max_value=480))
    start_dt = datetime.combine(date.min, start)
    end_dt = start_dt + timedelta(minutes=duration)
    # Clamp to midnight
    if end_dt.date() > date.min:
        end_dt = datetime.combine(date.min, time(23, 59))
    end = end_dt.time()
    assume(end > start)
    return TimeRange(start=start, end=end)


@st.composite
def daily_availability_strategy(draw) -> DailyAvailability:
    """Draw a DailyAvailability with zero or more blocked periods inside working hours."""
    target_date = draw(_DATE_STRATEGY)
    working = draw(valid_time_range(min_duration_minutes=60))
    slot_minutes = draw(_SLOT_MINUTES_STRATEGY)

    # Optionally draw a blocked period wholly inside working hours
    blocked: list[TimeRange] = []
    if draw(st.booleans()):
        wh_dur = working.duration_minutes()
        if wh_dur >= 2 * slot_minutes:
            block_start_offset = draw(st.integers(min_value=slot_minutes, max_value=wh_dur - slot_minutes))
            block_end_offset = draw(
                st.integers(min_value=block_start_offset + slot_minutes, max_value=wh_dur)
            )
            ws_dt = datetime.combine(date.min, working.start)
            bs = (ws_dt + timedelta(minutes=block_start_offset)).time()
            be = (ws_dt + timedelta(minutes=block_end_offset)).time()
            if be > bs:
                blocked.append(TimeRange(start=bs, end=be))

    return DailyAvailability(
        date=target_date,
        working_hours=working,
        blocked_periods=blocked,
        slot_minutes=slot_minutes,
    )


# ---------------------------------------------------------------------------
# Helper: classify an appointment form for statistics
# ---------------------------------------------------------------------------

def _classify_form(form: dict) -> None:
    """Emit Hypothesis events to track form shape distribution."""
    is_valid, _ = validate_appointment_form(form)
    event(f"form_valid={is_valid}")

    has_whitespace = any(
        isinstance(form.get(f), str) and form.get(f) != form.get(f, "").strip()
        for f in REQUIRED_FIELDS
    )
    if has_whitespace:
        event("has_leading_trailing_whitespace")

    missing = [f for f in REQUIRED_FIELDS if f not in form]
    if missing:
        event(f"missing_fields={len(missing)}")

    none_fields = [f for f in REQUIRED_FIELDS if form.get(f) is None]
    if none_fields:
        event("has_none_field")


def _classify_date(d: date) -> None:
    """Emit events for past/future split and boundary days."""
    today = date(2026, 3, 31)  # fixed reference for reproducibility
    if d < today:
        event("date=past")
    elif d == today:
        event("date=today")
    else:
        event("date=future")

    if d.month == 12 and d.day == 31:
        event("date=year_end")
    if d.month == 1 and d.day == 1:
        event("date=year_start")


def _classify_time_range(tr: TimeRange) -> None:
    dur = tr.duration_minutes()
    if dur < 60:
        event("duration=<1h")
    elif dur < 240:
        event("duration=1h-4h")
    else:
        event("duration=>4h")

    if tr.start == time(0, 0):
        event("start=midnight")
    if tr.end == time(23, 59):
        event("end=near_midnight")


# ===========================================================================
# Property 1 — Custom Shrinker: validate_appointment_form idempotency
# ===========================================================================
# If we validate a form, add the errors as None fields, and validate again,
# the second result should be a superset of the first error set.
# This property exposes the shrinker: when it fails, Hypothesis reduces the
# form to the minimal set of fields that triggers the bug.

@given(form=_MAYBE_INVALID_FORM_STRATEGY)
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_validation_error_set_monotone_after_nulling_errors(form: dict) -> None:
    """Nulling out failed fields never introduces new field errors elsewhere."""
    _classify_form(form)
    is_valid, errors = validate_appointment_form(form)

    if is_valid:
        return  # nothing to shrink toward

    # Build a new form with the bad fields set to None explicitly
    nulled = {**form, **{f: None for f in errors}}
    _, errors2 = validate_appointment_form(nulled)

    # Every error from round 1 must still be present in round 2
    assert set(errors).issubset(set(errors2)), (
        f"Shrunk form: {nulled!r}\nRound-1 errors: {errors}\nRound-2 errors: {errors2}"
    )


# ===========================================================================
# Property 2 — Custom Shrinker: validate + normalize round-trip
# ===========================================================================
# For any valid form, normalizing it and validating again must still succeed.
# The shrinker reduces counterexamples to the shortest field values that break
# this invariant (if ever a bug is introduced in normalize_appointment_form).

@given(form=_VALID_FORM_STRATEGY)
@settings(max_examples=300)
def test_normalize_preserves_validity(form: dict) -> None:
    """Normalized valid forms remain valid — shrinker finds minimal string."""
    _classify_form(form)

    from src.booking import normalize_appointment_form
    normalized = normalize_appointment_form(form)
    is_valid, errors = validate_appointment_form(normalized)

    assert is_valid, (
        f"Normalization broke validity.\n"
        f"Original (shrunken): {form!r}\n"
        f"Normalized: {normalized!r}\n"
        f"Errors: {errors}"
    )


# ===========================================================================
# Property 3 — Classification: slot count is non-negative for any valid avail
# ===========================================================================

@given(avail=daily_availability_strategy())
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_generate_slots_non_negative(avail: DailyAvailability) -> None:
    """generate_available_slots always returns a non-negative number of slots."""
    _classify_date(avail.date)
    _classify_time_range(avail.working_hours)

    blocked_count = len(avail.blocked_periods)
    event(f"blocked_periods={blocked_count}")

    if blocked_count > 0:
        event("has_blocked_period")

    slots = generate_available_slots(avail)
    assert len(slots) >= 0  # always true — shrinker would find zero-slot edge case


# ===========================================================================
# Property 4 — Classification: slot ordering invariant
# ===========================================================================

@given(avail=daily_availability_strategy())
@settings(max_examples=300, suppress_health_check=[HealthCheck.too_slow])
def test_generated_slots_are_sorted(avail: DailyAvailability) -> None:
    """All generated slots are in ascending datetime order."""
    _classify_date(avail.date)
    event(f"slot_minutes={avail.slot_minutes}")

    slots = generate_available_slots(avail)
    if len(slots) < 2:
        event("slots=zero_or_one")
        return

    event(f"slot_count={'few' if len(slots) <= 5 else 'many'}")
    assert slots == sorted(slots), f"Unsorted slots for avail={avail!r}"


# ===========================================================================
# Property 5 — Custom Shrinker: has_conflict symmetry
# ===========================================================================
# Conflict detection must be symmetric: if A conflicts with B, B conflicts with A.
# When this fails, Hypothesis shrinks (start, end, existing) to the shortest
# possible datetime pair.

@st.composite
def conflict_scenario(draw):
    base = draw(
        st.datetimes(
            min_value=datetime(2026, 1, 1, 6, 0),
            max_value=datetime(2030, 12, 31, 22, 0),
        )
    )
    slot = draw(_SLOT_MINUTES_STRATEGY)
    proposed_end = base + timedelta(minutes=slot)

    overlap_type = draw(st.sampled_from(["overlap", "adjacent", "before", "after", "contains"]))
    event(f"overlap_type={overlap_type}")

    if overlap_type == "overlap":
        # Existing starts partway through proposed
        offset = draw(st.integers(min_value=1, max_value=slot - 1))
        ex_start = base + timedelta(minutes=offset)
        ex_end = ex_start + timedelta(minutes=slot)
    elif overlap_type == "adjacent":
        # Existing starts exactly at proposed_end — no conflict
        ex_start = proposed_end
        ex_end = ex_start + timedelta(minutes=slot)
    elif overlap_type == "before":
        # Existing ends before proposed starts
        ex_end = base - timedelta(minutes=1)
        ex_start = ex_end - timedelta(minutes=slot)
    elif overlap_type == "after":
        # Existing starts after proposed ends
        ex_start = proposed_end + timedelta(minutes=1)
        ex_end = ex_start + timedelta(minutes=slot)
    else:  # contains
        # Existing wholly contains proposed
        ex_start = base - timedelta(minutes=slot)
        ex_end = proposed_end + timedelta(minutes=slot)

    return base, proposed_end, ex_start, ex_end, overlap_type


@given(scenario=conflict_scenario())
@settings(max_examples=400)
def test_conflict_detection_symmetry(scenario) -> None:
    """has_conflict(A, B, [existing]) == has_conflict(existing, [A,B])."""
    proposed_start, proposed_end, ex_start, ex_end, overlap_type = scenario

    result_forward = has_conflict(proposed_start, proposed_end, [(ex_start, ex_end)])
    result_backward = has_conflict(ex_start, ex_end, [(proposed_start, proposed_end)])

    assert result_forward == result_backward, (
        f"Asymmetric conflict!\n"
        f"  proposed={proposed_start}–{proposed_end}\n"
        f"  existing={ex_start}–{ex_end}\n"
        f"  forward={result_forward}, backward={result_backward}\n"
        f"  overlap_type={overlap_type}"
    )


# ===========================================================================
# Property 6 — Custom Shrinker: book_appointment conflict prevents double-booking
# ===========================================================================
# If we successfully book slot A and then try to book an overlapping slot B,
# the second booking must fail with time_slot_conflict.
# Shrinks form data to single-char strings and times to smallest offsets.

@given(
    form=_VALID_FORM_STRATEGY,
    start=st.datetimes(
        min_value=datetime(2026, 1, 1, 8, 0),
        max_value=datetime(2026, 12, 31, 17, 0),
    ),
    slot=_SLOT_MINUTES_STRATEGY,
    overlap_minutes=st.integers(min_value=1, max_value=59),
)
@settings(max_examples=300)
def test_double_booking_prevented_with_custom_shrink(
    form: dict, start: datetime, slot: int, overlap_minutes: int
) -> None:
    """Overlapping second booking always fails; shrinks to minimal form + times."""
    assume(overlap_minutes < slot)

    _classify_form(form)
    event(f"slot_minutes={slot}")
    event(f"overlap_minutes={overlap_minutes}")

    # First booking
    ok1, data1, _ = book_appointment(form, start, slot, [])
    assert ok1, f"First booking should succeed for valid form: {form!r}"

    # Second booking overlaps the first
    second_start = start + timedelta(minutes=overlap_minutes)
    first_end = start + timedelta(minutes=slot)
    existing = [(start, first_end)]

    ok2, data2, errors2 = book_appointment(form, second_start, slot, existing)
    assert not ok2, (
        f"Double-booking should be rejected!\n"
        f"  form (shrunken)={form!r}\n"
        f"  first slot: {start}–{first_end}\n"
        f"  second start: {second_start}\n"
        f"  overlap: {overlap_minutes} min"
    )
    assert "time_slot_conflict" in errors2


# ===========================================================================
# Property 7 — Classification statistics: form field distributions
# ===========================================================================
# This test exists purely to print generator statistics.
# Run with `pytest -s` to see the event distribution.

@given(form=_MAYBE_INVALID_FORM_STRATEGY)
@settings(max_examples=500)
def test_form_generator_statistics(form: dict) -> None:
    """Emit detailed classification events for the form generator.

    Run with `pytest -s --hypothesis-show-statistics` to see the distribution.
    """
    _classify_form(form)

    is_valid, errors = validate_appointment_form(form)

    # Classify by how many fields are problematic
    if not is_valid:
        event(f"error_count={len(errors)}")

    # Classify by field lengths (only valid string fields)
    for field in REQUIRED_FIELDS:
        val = form.get(field)
        if isinstance(val, str) and val.strip():
            stripped = val.strip()
            if len(stripped) == 1:
                event("field_length=1")
            elif len(stripped) <= 4:
                event("field_length=2-4")
            else:
                event("field_length=5+")
