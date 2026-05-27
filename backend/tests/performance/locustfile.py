"""
Locust load-test scenarios — User Management authentication flow.

User journey (per virtual user)
---------------------------------
1. on_start  — craft a Bearer token signed with SUPABASE_JWT_SECRET.
               This simulates the result of a successful client-side Supabase
               login without executing a real auth network call from Locust.
2. health    — GET /api/health   (no auth, baseline measure of Flask overhead)
3. slots     — GET /api/doctors/:id/available-slots  (JWT-protected; exercises
               the full auth middleware + real Supabase DB round-trip)

Running
-------
Start the test server first (from backend/):
    venv/Scripts/python tests/performance/test_server.py

Then run Locust (from backend/):
    venv/Scripts/locust -f tests/performance/locustfile.py \\
        --host http://localhost:5001 \\
        --headless -u 10 -r 2 --run-time 60s \\
        --html tests/performance/reports/load_10.html

Adjust -u / -r for each load level (10 / 50 / 100 users).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import jwt
from dotenv import load_dotenv
from locust import HttpUser, between, task

# ---------------------------------------------------------------------------
# Load the real SUPABASE_JWT_SECRET from backend/.env so tokens are signed
# with the same secret the patched test_server.py uses for verification.
# ---------------------------------------------------------------------------
_BACKEND = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BACKEND / ".env")

PERF_JWT_SECRET: str = os.environ["SUPABASE_JWT_SECRET"]

# A UUID used as the virtual user's identity in the JWT sub claim.
# The available-slots endpoint does not authorise by user_id, so any valid
# UUID works — we are measuring throughput and latency, not data access.
TEST_USER_ID: str = "00000000-0000-0000-0000-000000000099"

# A doctor UUID passed in the URL.  If this doctor has no rows in
# availability_rules, Supabase returns an empty result set quickly; the
# network round-trip to Supabase still happens and contributes to latency.
TEST_DOCTOR_ID: str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

# Date used in the available-slots query.
TEST_DATE: str = "2026-05-22"


# ---------------------------------------------------------------------------
# Token factory
# ---------------------------------------------------------------------------

def _make_token(user_id: str) -> str:
    """Return a signed HS256 JWT accepted by the patched test server.

    The payload mirrors a minimal Supabase access token.  The ``sub`` claim
    carries the user UUID; ``exp`` is set to one hour from now so the token
    stays valid for the entire load-test run.
    """
    now = int(time.time())
    payload = {
        "sub": user_id,
        "role": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, PERF_JWT_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# Locust user
# ---------------------------------------------------------------------------

class MedicalAppUser(HttpUser):
    """Simulates a single authenticated user of the medical appointments app.

    Task weights reflect realistic usage: authenticated actions (slots lookup)
    are 4× more frequent than unauthenticated ones (health probe).
    """

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Called once when this virtual user spawns.

        Generates a Bearer token — the load-test equivalent of the client-side
        Supabase sign-in step.  All subsequent requests reuse this token for
        the lifetime of the virtual user.
        """
        self.token = _make_token(TEST_USER_ID)
        self.auth_headers = {"Authorization": f"Bearer {self.token}"}

    # ── Tasks ─────────────────────────────────────────────────────────────────

    @task(1)
    def health_check(self) -> None:
        """GET /api/health — unauthenticated baseline.

        Measures raw Flask routing + JSON serialisation overhead with no
        middleware in the critical path.  Comparing this to the protected
        endpoint isolates the cost of JWT verification.
        """
        self.client.get("/api/health", name="GET /api/health (no auth)")

    @task(4)
    def get_available_slots(self) -> None:
        """GET /api/doctors/:id/available-slots — JWT-protected endpoint.

        Full authentication flow under test:
          1. Extract Bearer token from the Authorization header
          2. Verify JWT signature (HS256 via patch, ES256/JWKS in production)
          3. Query Supabase REST API for availability rules (real DB call)
          4. Compute available time slots and serialise JSON response

        Weighted 4x relative to health_check to reflect realistic traffic
        patterns where authenticated data access dominates.
        """
        self.client.get(
            f"/api/doctors/{TEST_DOCTOR_ID}/available-slots",
            headers=self.auth_headers,
            params={"date": TEST_DATE},
            name="GET /api/doctors/:id/available-slots (auth + DB)",
        )
