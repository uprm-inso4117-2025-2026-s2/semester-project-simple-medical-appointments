"""
Lightweight CI load-smoke test for the backend health endpoint.

Usage:
    locust -f backend/tests/load/locust_smoke.py --host=http://127.0.0.1:5000 \
           --headless -u 10 -r 10 --run-time 20s
"""
from locust import HttpUser, task, between


class HealthUser(HttpUser):
    wait_time = between(0.1, 0.5)
    weight = 1

    @task
    def health(self):
        self.client.get("/api/health", name="/api/health")

