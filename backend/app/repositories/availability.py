"""Retrieve doctor availability rules, working hours, and slot duration from Supabase."""

import json
from datetime import date, time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app

from ..services.scheduling import DailyAvailability, TimeRange
from ..services.working_hours import ensure_non_overlapping_ranges, parse_time_value


def _supabase_request(method, path, *, query=None):
    base_url = (current_app.config.get("SUPABASE_URL") or "").rstrip("/")
    service_key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")

    if not base_url or not service_key:
        return None, None, "Supabase is not configured."

    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }

    req = Request(url=url, headers=headers, method=method)

    try:
        with urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.status, None, None
            try:
                return resp.status, json.loads(raw), None
            except json.JSONDecodeError:
                return resp.status, raw, None
    except HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw or None
        return exc.code, parsed, None
    except (URLError, Exception) as exc:
        return None, None, f"Supabase request failed: {exc}"


def _fetch_day_rules(doctor_id: str, day_of_week: int):
    status, data, err = _supabase_request(
        "GET",
        "/rest/v1/availability_rules",
        query={
            "doctor_id": f"eq.{doctor_id}",
            "day_of_week": f"eq.{day_of_week}",
            "is_active": "eq.true",
            "select": "start_time,end_time",
            "order": "start_time.asc",
        },
    )
    if err or status != 200:
        return []

    pairs = []
    for row in data or []:
        start_raw = row.get("start_time")
        end_raw = row.get("end_time")
        if start_raw is None or end_raw is None:
            continue
        pairs.append((parse_time_value(start_raw), parse_time_value(end_raw)))

    return ensure_non_overlapping_ranges(pairs)


def _resolve_slot_minutes(doctor_id: str) -> int:
    # Default slot duration used when provider settings are missing.
    default_minutes = 30

    doc_status, doc_data, doc_err = _supabase_request(
        "GET",
        "/rest/v1/doctors",
        query={"id": f"eq.{doctor_id}", "select": "user_id"},
    )
    if doc_err or doc_status != 200 or not doc_data:
        return default_minutes

    user_id = doc_data[0].get("user_id") if isinstance(doc_data, list) else None
    if not user_id:
        return default_minutes

    settings_status, settings_data, settings_err = _supabase_request(
        "GET",
        "/rest/v1/provider_settings",
        query={"user_id": f"eq.{user_id}", "select": "default_appointment_duration"},
    )
    if settings_err or settings_status != 200 or not settings_data:
        return default_minutes

    value = settings_data[0].get("default_appointment_duration") if isinstance(settings_data, list) else None
    if isinstance(value, int) and value > 0:
        return value
    return default_minutes


def get_availability_for_doctor_date(doctor_id: str, target_date: date) -> DailyAvailability:
    day_of_week = target_date.weekday()

    ranges = _fetch_day_rules(doctor_id, day_of_week)

    # No working hours for this day
    if not ranges:
        working_hours = TimeRange(
            start=time(9, 0),
            end=time(9, 0),
        )

        return DailyAvailability(
            date=target_date,
            working_hours=working_hours,
            blocked_periods=[],
            slot_minutes=_resolve_slot_minutes(doctor_id),
        )

    # First start -> last end
    working_hours = TimeRange(
        start=ranges[0][0],
        end=ranges[-1][1],
    )

    blocked_periods = []

    # Gaps between ranges become blocked periods (lunch)
    for idx in range(len(ranges) - 1):
        current_end = ranges[idx][1]
        next_start = ranges[idx + 1][0]

        if current_end < next_start:
            blocked_periods.append(
                TimeRange(
                    start=current_end,
                    end=next_start,
                )
            )

    slot_minutes = _resolve_slot_minutes(doctor_id)

    return DailyAvailability(
        date=target_date,
        working_hours=working_hours,
        blocked_periods=blocked_periods,
        slot_minutes=slot_minutes,
    )
