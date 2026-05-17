"""
Decision-table tests for doctor slot availability (Lecture: Test Planning).

Each row in SCHEDULING_DECISION_TABLE maps conditions to an expected outcome.
"""

from datetime import date, time

import pytest

from app.repositories.availability import get_availability_for_doctor_date
from app.services.scheduling import DailyAvailability, TimeRange, generate_available_slots

DOCTOR = "dr-1"
WEEKDAY = date(2026, 3, 9)  # Monday
SUNDAY = date(2026, 3, 8)

WEEKDAY_SLOT_COUNT = 14
WEEKDAY_FIRST = "09:00"
WEEKDAY_LAST = "16:30"


SCHEDULING_DECISION_TABLE = [
    {
        "id": "DT-API-01",
        "date_param": None,
        "expected_status": 400,
        "expect_date_error": True,
    },
    {
        "id": "DT-API-02",
        "date_param": "not-a-date",
        "expected_status": 400,
        "expect_date_error": True,
    },
    {
        "id": "DT-API-03",
        "date_param": WEEKDAY.isoformat(),
        "expected_status": 200,
        "min_slots": WEEKDAY_SLOT_COUNT,
        "must_include": [WEEKDAY_FIRST, WEEKDAY_LAST],
        "must_exclude": ["12:00", "12:30"],
    },
    {
        "id": "DT-API-04",
        "date_param": SUNDAY.isoformat(),
        "expected_status": 200,
        "exact_slots": [],
    },
]


class TestAvailableSlotsDecisionTable:
    @pytest.mark.parametrize("row", SCHEDULING_DECISION_TABLE, ids=lambda r: r["id"])
    def test_api_row(self, client, row):
        query = {}
        if row["date_param"] is not None:
            query["date"] = row["date_param"]

        response = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string=query,
        )
        assert response.status_code == row["expected_status"]

        if row["expected_status"] != 200:
            if row.get("expect_date_error"):
                assert "date" in response.get_json().get("error", "").lower()
            return

        slots = response.get_json()["slots"]
        if "exact_slots" in row:
            assert slots == row["exact_slots"]
        if "min_slots" in row:
            assert len(slots) >= row["min_slots"]
        for slot in row.get("must_include", []):
            assert slot in slots
        for slot in row.get("must_exclude", []):
            assert slot not in slots


SERVICE_DECISION_TABLE = [
    {
        "id": "DT-SVC-01",
        "label": "closed_day",
        "availability": lambda: get_availability_for_doctor_date(DOCTOR, SUNDAY),
        "expect_count": 0,
    },
    {
        "id": "DT-SVC-02",
        "label": "weekday_with_lunch_break",
        "availability": lambda: get_availability_for_doctor_date(DOCTOR, WEEKDAY),
        "expect_count": WEEKDAY_SLOT_COUNT,
        "forbid_times": [time(12, 0), time(12, 30)],
    },
    {
        "id": "DT-SVC-03",
        "label": "weekday_without_lunch_break",
        "availability": lambda: DailyAvailability(
            date=WEEKDAY,
            working_hours=TimeRange(time(9, 0), time(17, 0)),
            blocked_periods=[],
            slot_minutes=30,
            max_appointments_per_slot=2,
        ),
        "expect_count": 16,
        "require_times": [time(12, 0)],
    },
]


class TestSlotGenerationDecisionTable:
    @pytest.mark.parametrize("row", SERVICE_DECISION_TABLE, ids=lambda r: r["id"])
    def test_service_row(self, row):
        availability = row["availability"]()
        slots = generate_available_slots(availability)
        assert len(slots) == row["expect_count"]
        slot_times = {s.time() for s in slots}
        for forbidden in row.get("forbid_times", []):
            assert forbidden not in slot_times
        for required in row.get("require_times", []):
            assert required in slot_times
