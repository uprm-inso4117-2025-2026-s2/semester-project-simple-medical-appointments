"""
Load test for Simple Medical Appointments API.

Usage:
    locust -f backend/tests/load/locustfile.py --host=http://localhost:5000
    locust -f backend/tests/load/locustfile.py --host=http://localhost:5000 \
           --headless -u 100 -r 10 --run-time 10m

Scenarios:
    PatientUser  (70%) — search providers, view slots, submit booking
    ProviderUser (20%) — view their daily schedule
    AdminUser    (10%) — view all appointments, publish slots

These weights reflect realistic usage: most concurrent users are patients
searching and booking; a smaller proportion are providers checking schedules;
a small minority are admin users modifying availability.
"""
import random
from locust import HttpUser, task, between

# Representative test data (matches seed data in the development database)
PROVIDER_IDS = ["prov_001", "prov_002", "prov_003"]
SPECIALTIES  = ["cardiology", "general_practice", "endocrinology"]
INSURANCE_PLANS = ["triple_s", "humana", "medicare_advantage"]


class PatientUser(HttpUser):
    """Simulates a patient searching for and booking an appointment."""

    wait_time = between(1, 5)
    weight = 7  # 70% of simulated users

    @task(3)
    def search_providers(self):
        """Most common action: search for an available provider."""
        self.client.get(
            "/api/providers",
            params={
                "specialty": random.choice(SPECIALTIES),
                "insurance":  random.choice(INSURANCE_PLANS),
            },
            name="/api/providers?specialty=&insurance=",
        )

    @task(2)
    def view_available_slots(self):
        """After finding a provider, patient browses available times."""
        provider_id = random.choice(PROVIDER_IDS)
        self.client.get(
            "/api/timeslots",
            params={"provider_id": provider_id},
            name="/api/timeslots?provider_id=",
        )

    @task(1)
    def submit_booking(self):
        """Patient submits an appointment request."""
        self.client.post(
            "/api/appointments/submit",
            json={
                "name":                       "Load",
                "surname":                    "TestUser",
                "symptoms_and_or_allergies":  "hypertension",
                "medications":                "lisinopril 10mg",
            },
            name="/api/appointments/submit",
        )


class ProviderUser(HttpUser):
    """Simulates a healthcare provider reviewing their schedule."""

    wait_time = between(5, 15)
    weight = 2  # 20% of simulated users

    @task
    def view_daily_schedule(self):
        provider_id = random.choice(PROVIDER_IDS)
        self.client.get(
            "/api/appointments",
            params={"provider_id": provider_id, "date": "2026-04-10"},
            name="/api/appointments?provider_id=&date=",
        )


class AdminUser(HttpUser):
    """Simulates a clinic admin managing availability and appointments."""

    wait_time = between(10, 30)
    weight = 1  # 10% of simulated users

    @task(3)
    def view_all_appointments(self):
        self.client.get("/api/appointments", name="/api/appointments (admin view)")

    @task(1)
    def publish_slot(self):
        self.client.post(
            "/api/slots",
            json={
                "provider_id":       random.choice(PROVIDER_IDS),
                "start_time":        "2026-04-15T09:00:00",
                "end_time":          "2026-04-15T09:30:00",
                "consultation_type": "revisita",
            },
            name="/api/slots (publish)",
        )
