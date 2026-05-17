from __future__ import annotations

from datetime import time
from typing import Iterable, List, Tuple


TimePair = Tuple[time, time]


def parse_time_value(value: str) -> time:
    """Parse a time string like HH:MM or HH:MM:SS."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Time values must be non-empty strings")

    raw = value.strip()
    try:
        return time.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid time format: {value}. Use HH:MM or HH:MM:SS") from exc


def ensure_non_overlapping_ranges(ranges: Iterable[TimePair]) -> List[TimePair]:
    """Validate and return sorted, non-overlapping half-open ranges [start, end)."""
    ordered = sorted(list(ranges), key=lambda pair: pair[0])

    if not ordered:
        return []

    for start, end in ordered:
        if start >= end:
            raise ValueError("Each time range must have start_time earlier than end_time")

    for idx in range(len(ordered) - 1):
        current_start, current_end = ordered[idx]
        next_start, _ = ordered[idx + 1]
        if next_start < current_end:
            raise ValueError(
                "Overlapping time ranges are not allowed for the same day"
            )

    return ordered


def normalize_ranges_payload(payload: dict) -> List[TimePair]:
    """Normalize supported request payload shapes into validated time ranges.

    Accepted payload formats:
      1) {"ranges": [{"start_time": "09:00", "end_time": "12:00"}, ...]}
      2) {
            "start_time": "09:00",
            "end_time": "17:00",
            "lunch_break_start": "12:00",  # optional
            "lunch_break_end": "13:00"     # optional
         }
    """
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")

    if isinstance(payload.get("ranges"), list):
        pairs: List[TimePair] = []
        for item in payload["ranges"]:
            if not isinstance(item, dict):
                raise ValueError("Each range must be an object")
            start = parse_time_value(item.get("start_time", ""))
            end = parse_time_value(item.get("end_time", ""))
            pairs.append((start, end))
        return ensure_non_overlapping_ranges(pairs)

    start_raw = payload.get("start_time")
    end_raw = payload.get("end_time")
    if start_raw is None or end_raw is None:
        raise ValueError(
            "Provide either ranges[] or start_time/end_time fields"
        )

    day_start = parse_time_value(start_raw)
    day_end = parse_time_value(end_raw)

    lunch_start_raw = payload.get("lunch_break_start")
    lunch_end_raw = payload.get("lunch_break_end")

    if (lunch_start_raw is None) != (lunch_end_raw is None):
        raise ValueError("Both lunch_break_start and lunch_break_end must be provided together")

    if lunch_start_raw is None and lunch_end_raw is None:
        return ensure_non_overlapping_ranges([(day_start, day_end)])

    lunch_start = parse_time_value(lunch_start_raw)
    lunch_end = parse_time_value(lunch_end_raw)

    if day_start >= day_end:
        raise ValueError("start_time must be earlier than end_time")
    if lunch_start >= lunch_end:
        raise ValueError("lunch_break_start must be earlier than lunch_break_end")
    if lunch_start <= day_start or lunch_end >= day_end:
        raise ValueError("Lunch break must be strictly inside working hours")

    ranges: List[TimePair] = [(day_start, lunch_start), (lunch_end, day_end)]
    return ensure_non_overlapping_ranges(ranges)


def serialize_ranges(ranges: Iterable[TimePair]) -> List[dict]:
    """Serialize ranges to JSON-friendly HH:MM:SS strings."""
    return [
        {
            "start_time": start.strftime("%H:%M:%S"),
            "end_time": end.strftime("%H:%M:%S"),
        }
        for start, end in ranges
    ]
