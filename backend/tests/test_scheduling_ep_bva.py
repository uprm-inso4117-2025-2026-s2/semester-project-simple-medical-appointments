"""
Equivalence partitioning and boundary tests for GET /api/doctors/<id>/available-slots.

When the API gains JWT, booking capacity, or scheduling on POST /appointments/submit,
extend this module with matching equivalence and boundary cases.
"""

from datetime import date

import pytest

DOCTOR = "dr-1"
WEEKDAY = date(2026, 3, 9)
SUNDAY = date(2026, 3, 8)


class TestAvailableSlotsEquivalence:
    def test_missing_date_parameter_returns_400(self, client):
        r = client.get(f"/api/doctors/{DOCTOR}/available-slots")
        assert r.status_code == 400
        assert "date" in r.get_json().get("error", "").lower()

    @pytest.mark.parametrize(
        "bad_date",
        ["03-09-2026", "2026/03/09", "not-a-date", ""],
        ids=["mdy", "slashes", "garbage", "empty"],
    )
    def test_invalid_date_format_returns_400(self, client, bad_date):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": bad_date},
        )
        assert r.status_code == 400

    def test_valid_weekday_returns_slots_json(self, client):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": WEEKDAY.isoformat()},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert "slots" in data
        assert isinstance(data["slots"], list)
        assert len(data["slots"]) > 0

    def test_sunday_closed_returns_empty_slots(self, client):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": SUNDAY.isoformat()},
        )
        assert r.status_code == 200
        assert r.get_json()["slots"] == []


class TestAvailableSlotsBoundaries:
    EXPECTED_WEEKDAY_SLOTS = [
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
        "11:30",
        "13:00",
        "13:30",
        "14:00",
        "14:30",
        "15:00",
        "15:30",
        "16:00",
        "16:30",
    ]

    def test_weekday_slot_list_matches_boundaries(self, client):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": WEEKDAY.isoformat()},
        )
        assert r.get_json()["slots"] == self.EXPECTED_WEEKDAY_SLOTS

    def test_first_morning_slot(self, client):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": WEEKDAY.isoformat()},
        )
        assert r.get_json()["slots"][0] == "09:00"

    def test_last_slot_before_lunch(self, client):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": WEEKDAY.isoformat()},
        )
        slots = r.get_json()["slots"]
        assert "11:30" in slots and "12:00" not in slots

    def test_first_slot_after_lunch(self, client):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": WEEKDAY.isoformat()},
        )
        slots = r.get_json()["slots"]
        i = slots.index("11:30")
        assert slots[i + 1] == "13:00"

    def test_last_slot_of_day(self, client):
        r = client.get(
            f"/api/doctors/{DOCTOR}/available-slots",
            query_string={"date": WEEKDAY.isoformat()},
        )
        assert r.get_json()["slots"][-1] == "16:30"
