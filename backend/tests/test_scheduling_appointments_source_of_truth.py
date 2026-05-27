from datetime import date

import pytest

from app.repositories import availability
from app.repositories import slot_bookings
from app.routes import scheduling_appointments as scheduling_routes


DOCTOR = "dr-1"
DAY = date(2026, 3, 9)


@pytest.fixture
def fake_supabase(monkeypatch):
    fake_appointments = []
    fake_doctors = {
        DOCTOR: {"id": DOCTOR, "clinic_id": "fake-clinic-id"},
        "dr-2": {"id": "dr-2", "clinic_id": "clinic-2"},
    }

    def fake_supabase_request(method, path, *, query=None, json_body=None):
        query = query or {}

        if method == "GET" and path == "/rest/v1/doctors":
            if query.get("select") == "clinic_id":
                return 200, [{"clinic_id": "fake-clinic-id"}], None

        if method == "GET" and path == "/rest/v1/appointments":
            doctor_id = query.get("doctor_id", "").replace("eq.", "")
            appointment_datetime = query.get("appointment_datetime", "").replace("eq.", "")
            status_filter = query.get("status", "")

            results = [
                appt for appt in fake_appointments
                if appt["doctor_id"] == doctor_id
            ]

            if appointment_datetime:
                results = [
                    appt for appt in results
                    if appt["appointment_datetime"] == appointment_datetime
                ]

            if status_filter == "in.(pending,confirmed)":
                results = [
                    appt for appt in results
                    if appt.get("status") in ("pending", "confirmed")
                ]

            return 200, results, None

        if method == "POST" and path == "/rest/v1/appointments":
            new_appointment = dict(json_body)
            new_appointment["id"] = len(fake_appointments) + 1
            fake_appointments.append(new_appointment)
            return 201, [new_appointment], None

        return 404, None, f"Unhandled fake request: {method} {path}"

    class FakeResponse:
        def __init__(self, data):
            self.data = data

    class FakeTableQuery:
        def __init__(self, table_name):
            self.table_name = table_name
            self.filters = {}
            self.update_payload = None

        def select(self, *_args, **_kwargs):
            return self

        def eq(self, field, value):
            self.filters[field] = value
            return self

        def order(self, *_args, **_kwargs):
            return self

        def update(self, payload):
            self.update_payload = payload
            return self

        def execute(self):
            if self.table_name == "appointments":
                matches = [
                    appt for appt in fake_appointments
                    if all(appt.get(field) == value for field, value in self.filters.items())
                ]
                if self.update_payload is None:
                    return FakeResponse([dict(appt) for appt in matches])

                updated = []
                for appt in matches:
                    appt.update(self.update_payload)
                    updated.append(dict(appt))
                return FakeResponse(updated)

            if self.table_name == "doctors":
                doctor_id = self.filters.get("id")
                doctor = fake_doctors.get(doctor_id)
                return FakeResponse([dict(doctor)] if doctor else [])

            return FakeResponse([])

    class FakeSupabaseClient:
        def table(self, table_name):
            return FakeTableQuery(table_name)

    monkeypatch.setattr(availability, "_supabase_request", fake_supabase_request)
    monkeypatch.setattr(slot_bookings, "_supabase_request", fake_supabase_request)
    monkeypatch.setattr(
        scheduling_routes,
        "_get_supabase_client",
        lambda: FakeSupabaseClient(),
    )

    return fake_appointments


def test_create_scheduling_appointment_uses_shared_booking_logic(
    client,
    auth_headers,
    fake_supabase,
):
    response = client.post(
        "/api/scheduling/appointments/",
        json={
            "patient_id": "patient-1",
            "doctor_id": DOCTOR,
            "appointment_datetime": f"{DAY.isoformat()}T09:00:00",
            "status": "pending",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["booking_type"] == "MAIN"
    assert payload["data"]["appointment"]["status"] == "pending"
    assert payload["data"]["assigned_datetime"] == f"{DAY.isoformat()}T09:00:00"
    assert len(fake_supabase) == 1


def test_scheduling_create_endpoint_and_available_slots_share_capacity_rules(
    client,
    auth_headers,
    fake_supabase,
):
    booking_payload = {
        "doctor_id": DOCTOR,
        "appointment_datetime": f"{DAY.isoformat()}T09:00:00",
    }

    for patient_id in ("patient-1", "patient-2"):
        response = client.post(
            "/api/scheduling/appointments/",
            json={**booking_payload, "patient_id": patient_id},
            headers=auth_headers,
        )
        assert response.status_code == 201

    slots_response = client.get(
        f"/api/doctors/{DOCTOR}/available-slots",
        query_string={"date": DAY.isoformat()},
        headers=auth_headers,
    )

    assert slots_response.status_code == 200
    assert "09:00" not in slots_response.get_json()["slots"]

    full_slot_response = client.post(
        "/api/scheduling/appointments/",
        json={**booking_payload, "patient_id": "patient-3"},
        headers=auth_headers,
    )

    assert full_slot_response.status_code == 409
    payload = full_slot_response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "Unable to book appointment."
    assert len(fake_supabase) == 2


def test_update_scheduling_appointment_rejects_reschedule_into_full_slot(
    client,
    auth_headers,
    fake_supabase,
):
    fake_supabase.extend(
        [
            {
                "id": "appt-1",
                "patient_id": "patient-1",
                "doctor_id": DOCTOR,
                "clinic_id": "fake-clinic-id",
                "appointment_datetime": f"{DAY.isoformat()}T09:30:00",
                "status": "confirmed",
                "appointment_type": "MAIN",
                "notes": None,
            },
            {
                "id": "appt-2",
                "patient_id": "patient-2",
                "doctor_id": DOCTOR,
                "clinic_id": "fake-clinic-id",
                "appointment_datetime": f"{DAY.isoformat()}T09:00:00",
                "status": "confirmed",
                "appointment_type": "MAIN",
                "notes": None,
            },
            {
                "id": "appt-3",
                "patient_id": "patient-3",
                "doctor_id": DOCTOR,
                "clinic_id": "fake-clinic-id",
                "appointment_datetime": f"{DAY.isoformat()}T09:00:00",
                "status": "pending",
                "appointment_type": "MAIN",
                "notes": None,
            },
        ]
    )

    response = client.put(
        "/api/scheduling/appointments/appt-1",
        json={"appointment_datetime": f"{DAY.isoformat()}T09:00:00"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    payload = response.get_json()
    assert payload["success"] is False
    assert payload["error"] == "This time slot is full"
    assert fake_supabase[0]["appointment_datetime"] == f"{DAY.isoformat()}T09:30:00"


def test_update_scheduling_appointment_rejects_seconds_in_datetime(
    client,
    auth_headers,
    fake_supabase,
):
    fake_supabase.append(
        {
            "id": "appt-1",
            "patient_id": "patient-1",
            "doctor_id": DOCTOR,
            "clinic_id": "fake-clinic-id",
            "appointment_datetime": f"{DAY.isoformat()}T09:30:00",
            "status": "confirmed",
            "appointment_type": "MAIN",
            "notes": None,
        }
    )

    response = client.put(
        "/api/scheduling/appointments/appt-1",
        json={"appointment_datetime": f"{DAY.isoformat()}T10:00:30"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "appointment_datetime" in payload["message"]
