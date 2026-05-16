"""
Exploratory Testing: Scripted Baseline -- Authentication & Role Permission Boundaries
Author: Carlos Pepin Delgado
Lecture applied: Exploratory Testing

The lecture defines a scripted baseline as the set of test cases that establish
what is already known and verified BEFORE an exploratory session begins. Each
case is written in SCRIPT format -- preconditions, input, expected result --
so the session can focus on what scripted tests cannot cover: the unknown
and unexpected behaviors at boundary conditions.

SCRIPT CASES
------------
Three cases cover the known-correct behaviors of the registration endpoint
and the role permission gate:

  CASE 1 -- valid registration: all required fields + role=patient accepted (201)
  CASE 2 -- missing required field: endpoint rejects before any DB call (400)
  CASE 3 -- patient token on admin route: requires_role blocks before data access (403)

The middleware stack under test in Case 3 -- requires_auth sets g.user_id,
then requires_role resolves the role and gates the route -- is exercised fully.
Supabase I/O is stubbed in Cases 1 and 3; Case 2 needs no stub because
validation is purely in-process.

Run: cd backend && pytest tests/exploratory/test_scripted_baseline.py -v -s
"""
import pytest
import jwt
from unittest.mock import patch


PATIENT_USER_ID = "cccccccc-0000-0000-0000-000000000003"


def _make_token(user_id, secret):
    token = jwt.encode({"sub": user_id}, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("ascii")


def test_valid_registration_returns_201(client):
    """
    SCRIPT CASE 1: Valid registration payload with role=patient

    PRECONDITIONS: Registration endpoint is reachable. DB sync is available
                   (mocked to isolate route-level logic from Supabase I/O).
    INPUT:         POST /api/auth/register with all required fields,
                   role="patient".
    EXPECTED:      HTTP 201, message confirming registration success.
    """
    payload = {
        "user_id": "new-user-uuid-001",
        "first_name": "Jane",
        "last_name": "Doe",
        "username": "janedoe",
        "role": "patient",
    }
    with patch("app.routes.auth.sync_user_after_registration", return_value={"success": True}):
        response = client.post("/api/auth/register", json=payload)
    print(f"  ->POST /api/auth/register (valid patient)  HTTP {response.status_code}")
    assert response.status_code == 201


def test_missing_required_field_returns_400(client):
    """
    SCRIPT CASE 2: Registration with missing required field

    PRECONDITIONS: Registration endpoint is reachable. No prior session.
    INPUT:         POST /api/auth/register with user_id omitted.
    EXPECTED:      HTTP 400, error body identifying the missing field.
                   No Supabase call is made -- validation fires in-process.
    """
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "username": "janedoe",
        "role": "patient",
    }
    response = client.post("/api/auth/register", json=payload)
    data = response.get_json()
    print(f"  ->POST /api/auth/register (missing user_id)  HTTP {response.status_code} | {data}")
    assert response.status_code == 400
    assert "user_id" in data.get("error", "").lower() or "missing" in data.get("error", "").lower()


def test_patient_blocked_from_admin_route_returns_403(client, app):
    """
    SCRIPT CASE 3: Patient JWT calling admin-only endpoint

    PRECONDITIONS: A valid patient-role JWT exists. GET /api/admin/users
                   requires the admin role via requires_role({"admin"}).
    INPUT:         GET /api/admin/users with patient Bearer token.
    EXPECTED:      HTTP 403. No user data returned.
    """
    token = _make_token(PATIENT_USER_ID, app.config["SUPABASE_JWT_SECRET"])
    headers = {"Authorization": f"Bearer {token}"}
    with patch("app.utils.custom_decorators.get_role_for_user", return_value="patient"):
        response = client.get("/api/admin/users", headers=headers)
    print(f"  ->GET /api/admin/users (patient token)  HTTP {response.status_code}")
    assert response.status_code == 403
