"""
Property-Based Tests: filter_conflicting_slots contract
========================================================
Verifies that every slot returned by filter_conflicting_slots does NOT
conflict with the existing appointments that were passed in.

Run with:
    pytest backend/tests/test_pbt_filter_conflicting_slots.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from src.booking import filter_conflicting_slots, has_conflict

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_SLOT_MINUTES = st.sampled_from([15, 20, 30, 45, 60])

_SLOT_DATETIME = st.datetimes(
    min_value=datetime(2026, 1, 1, 6, 0),
    max_value=datetime(2030, 12, 31, 22, 0),
)

@st.composite
def existing_appointments(draw, slot_minutes: int):
    """Generate a list of non-overlapping (start, end) appointment pairs."""
    starts = draw(st.lists(_SLOT_DATETIME, min_size=0, max_size=10))
    delta = timedelta(minutes=slot_minutes)
    return [(s, s + delta) for s in starts]


# ---------------------------------------------------------------------------
# Property: every returned slot is conflict-free
# ---------------------------------------------------------------------------

@given(
    slots=st.lists(_SLOT_DATETIME, min_size=0, max_size=20),
    slot_minutes=_SLOT_MINUTES,
)
@settings(max_examples=200)
def test_returned_slots_have_no_conflict(slots, slot_minutes):
    """Every slot returned by filter_conflicting_slots must not conflict
    with the existing appointments that were passed in."""
    delta = timedelta(minutes=slot_minutes)
    existing = [(s, s + delta) for s in slots[:5]]  # use first 5 as existing

    result = filter_conflicting_slots(slots, slot_minutes, existing)

    for slot in result:
        assert not has_conflict(slot, slot + delta, existing), (
            f"Slot {slot} was returned but conflicts with existing={existing}"
        )


# ---------------------------------------------------------------------------
# Property: empty existing appointments passes all slots through
# ---------------------------------------------------------------------------

@given(
    slots=st.lists(_SLOT_DATETIME, min_size=0, max_size=20),
    slot_minutes=_SLOT_MINUTES,
)
@settings(max_examples=200)
def test_empty_existing_returns_all_slots(slots, slot_minutes):
    """With no existing appointments every slot passes through unchanged."""
    result = filter_conflicting_slots(slots, slot_minutes, [])
    assert result == slots


# ---------------------------------------------------------------------------
# Property: output is always a subset of input
# ---------------------------------------------------------------------------

@given(
    slots=st.lists(_SLOT_DATETIME, min_size=0, max_size=20),
    slot_minutes=_SLOT_MINUTES,
    existing=st.lists(
        st.tuples(_SLOT_DATETIME, _SLOT_DATETIME).filter(lambda p: p[0] < p[1]),
        min_size=0,
        max_size=5,
    ),
)
@settings(max_examples=200)
def test_output_is_subset_of_input(slots, slot_minutes, existing):
    """filter_conflicting_slots never adds slots — output is always a subset of input."""
    result = filter_conflicting_slots(slots, slot_minutes, existing)
    assert all(s in slots for s in result)
