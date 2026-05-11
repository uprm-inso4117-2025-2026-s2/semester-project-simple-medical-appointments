from datetime import time

import pytest

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.working_hours import ensure_non_overlapping_ranges, normalize_ranges_payload


def test_normalize_ranges_payload_supports_lunch_break_shape():
    payload = {
        "start_time": "09:00",
        "end_time": "17:00",
        "lunch_break_start": "12:00",
        "lunch_break_end": "13:00",
    }

    ranges = normalize_ranges_payload(payload)

    assert ranges == [
        (time(9, 0), time(12, 0)),
        (time(13, 0), time(17, 0)),
    ]


def test_normalize_ranges_payload_rejects_overlap_in_ranges_array():
    payload = {
        "ranges": [
            {"start_time": "09:00", "end_time": "12:30"},
            {"start_time": "12:00", "end_time": "14:00"},
        ]
    }

    with pytest.raises(ValueError, match="Overlapping time ranges"):
        normalize_ranges_payload(payload)


def test_normalize_ranges_payload_rejects_invalid_lunch_bounds():
    payload = {
        "start_time": "09:00",
        "end_time": "17:00",
        "lunch_break_start": "08:30",
        "lunch_break_end": "09:30",
    }

    with pytest.raises(ValueError, match="Lunch break must be strictly inside"):
        normalize_ranges_payload(payload)


def test_ensure_non_overlapping_ranges_allows_adjacent_ranges():
    result = ensure_non_overlapping_ranges(
        [
            (time(13, 0), time(17, 0)),
            (time(9, 0), time(13, 0)),
        ]
    )

    assert result == [
        (time(9, 0), time(13, 0)),
        (time(13, 0), time(17, 0)),
    ]
