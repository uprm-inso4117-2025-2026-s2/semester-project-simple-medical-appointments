"""
Behavior Driven Development: Admin User Management Flows
Author: Carlos Pepin Delgado

BDD step definitions and fixtures -- Admin User Management acceptance tests.
Lecture applied: Behavior Driven Development

BDD PROCESS
-----------
The lecture defines BDD as generating automated acceptance tests from user
stories -- not just tests, but a shared understanding of requirements --
organized around three stages and the triad.

Discovery   -- The lecture defines this stage as discovering acceptance
               criteria from user stories with the entire team contributing.
               From the admin user story ("as a clinic admin I need to manage
               user accounts so access control stays accurate"), the triad
               surfaced the criteria: customer -- list users, assign roles,
               deactivate; developer -- JWT authentication and requires_role
               enforcement; test -- the boundary cases the other two
               perspectives miss: non-admin blocked (403), self-deactivation
               denied (400), invalid role rejected (400), banned user
               visible as inactive.

Formulation -- Criteria evolved into specific, unambiguous Gherkin scenarios
               -- the lecture's exact language for this stage. Two .feature
               files separate operation scenarios (admin_operations.feature,
               6 scenarios) from access control boundary scenarios
               (access_control.feature, 3 scenarios). Given/When/Then keeps
               each scenario readable without code -- specification-by-example.

Automation  -- Step definitions call live Flask routes via app.test_client()
               so evidenced behavior remains runnable -- the lecture's
               automation goal. Only Supabase I/O is stubbed; JWT
               verification, requires_role, and route logic all execute.

GAP FOUND AND FIXED
-------------------
admin_bp was absent from app/routes/__init__.py on this branch.
Every /api/admin/* route returned 404. The access control scenarios specified
HTTP 403 for non-admin users -- 404 != 403, so automation exposed a missing
blueprint registration, not a logic defect.
Without executable Gherkin, this gap would require manually probing each route.
Fix: app.register_blueprint(admin_bp, url_prefix='/api/admin')

SCENARIO FINDINGS
-----------------
1. list users         -- active/inactive derived from banned_until at query
                         time; not a stored boolean.
2. role assignment    -- three-step Supabase flow: resolve role_id, delete old
                         row, insert new row with granted_by=g.user_id.
3. invalid role       -- 400 fires before any Supabase call; validation is
                         purely in-process (no network round-trip).
4. deactivation       -- ban_duration="876600h" (~100 yr) is the mechanism via
                         Auth Admin API; no DB flag is written.
5. inactive status    -- a user with banned_until in the future appears as
                         status="inactive" in the list response.
6. self-deactivation  -- 400 returned by a route-level guard before Supabase
                         is called; not enforced by middleware.
7-9. access control   -- requires_role returns 403 for all three admin routes
                         when role=patient. The registration gap (fixed above)
                         was the only defect; role-check logic was correct.

Run: cd backend && pytest tests/bdd/ -v -s
"""
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from pytest_bdd import given, when, then, parsers

ADMIN_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
PATIENT_USER_ID = "cccccccc-0000-0000-0000-000000000003"
TARGET_USER_ID = "target-user-001"

# A timestamp far enough in the future that the user is always banned during tests.
_FUTURE_BAN = (datetime.now(timezone.utc) + timedelta(days=36500)).isoformat()


@pytest.fixture
def context():
    """Mutable dict for sharing state across Given/When/Then steps."""
    return {}


def _make_token(user_id, secret):
    token = jwt.encode({"sub": user_id}, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("ascii")


def _mock_supabase(method, path, *, query=None, json_body=None, prefer=None):
    """Simulates Supabase REST and Auth Admin responses for admin route tests.

    Returns an active (non-banned) user for auth/v1/admin/users by default.
    """
    if method == "GET" and path == "/rest/v1/user_roles":
        return 200, [{"user_id": TARGET_USER_ID, "roles": {"name": "patient"}}], None
    if method == "GET" and path == "/auth/v1/admin/users":
        return 200, {"users": [{"id": TARGET_USER_ID, "email": "patient@test.com", "banned_until": None}]}, None
    if method == "GET" and path == "/rest/v1/roles":
        return 200, [{"id": "role-uuid-001"}], None
    if method == "DELETE" and path == "/rest/v1/user_roles":
        return 204, None, None
    if method == "POST" and path == "/rest/v1/user_roles":
        return 201, None, None
    if method == "PUT" and "/auth/v1/admin/users/" in path:
        return 200, {"id": TARGET_USER_ID}, None
    return 200, None, None


def _mock_supabase_banned(method, path, *, query=None, json_body=None, prefer=None):
    """Variant that returns the target user with a future banned_until date.

    Used to verify the banned_until -> status="inactive" derivation in list_users.
    """
    if method == "GET" and path == "/auth/v1/admin/users":
        return 200, {"users": [{"id": TARGET_USER_ID, "email": "patient@test.com", "banned_until": _FUTURE_BAN}]}, None
    return _mock_supabase(method, path, query=query, json_body=json_body, prefer=prefer)


# ---------------------------------------------------------------------------
# Output hooks -- visible scenario trace when running with -s
# ---------------------------------------------------------------------------

def pytest_bdd_before_scenario(request, feature, scenario):
    print(f"\n{'-' * 60}")
    print(f"  SCENARIO  {scenario.name}")


def pytest_bdd_after_scenario(request, feature, scenario):
    print(f"{'-' * 60}")


# ---------------------------------------------------------------------------
# Given steps  [Discovery: encode acceptance criteria per the triad]
# ---------------------------------------------------------------------------

@given("I am authenticated as an admin")
def authenticated_as_admin(context, app):
    token = _make_token(ADMIN_USER_ID, app.config["SUPABASE_JWT_SECRET"])
    context["headers"] = {"Authorization": f"Bearer {token}"}
    context["user_role"] = "admin"


@given("I am authenticated as a patient")
def authenticated_as_patient(context, app):
    token = _make_token(PATIENT_USER_ID, app.config["SUPABASE_JWT_SECRET"])
    context["headers"] = {"Authorization": f"Bearer {token}"}
    context["user_role"] = "patient"


# ---------------------------------------------------------------------------
# When steps  [Automation: exercise live Flask routes via test_client]
# ---------------------------------------------------------------------------

@when("I request the list of all users")
def request_list_users(context, client):
    role = context["user_role"]
    with patch("app.routes.admin._supabase_request", side_effect=_mock_supabase), \
         patch("app.utils.custom_decorators.get_role_for_user", return_value=role):
        context["response"] = client.get("/api/admin/users", headers=context["headers"])
    r = context["response"]
    print(f"  ->GET /api/admin/users  HTTP {r.status_code}")


@when("I request the list of users including a banned user")
def request_list_users_banned(context, client):
    with patch("app.routes.admin._supabase_request", side_effect=_mock_supabase_banned), \
         patch("app.utils.custom_decorators.get_role_for_user", return_value="admin"):
        context["response"] = client.get("/api/admin/users", headers=context["headers"])
    r = context["response"]
    print(f"  ->GET /api/admin/users (banned_until={_FUTURE_BAN[:10]})  HTTP {r.status_code}")


@when(parsers.parse('I assign the "{role}" role to user "{user_id}"'))
def assign_role_to_user(role, user_id, context, client):
    caller_role = context["user_role"]
    with patch("app.routes.admin._supabase_request", side_effect=_mock_supabase), \
         patch("app.utils.custom_decorators.get_role_for_user", return_value=caller_role):
        context["response"] = client.put(
            f"/api/admin/users/{user_id}/role",
            json={"role": role},
            headers=context["headers"],
        )
    r = context["response"]
    print(f"  ->PUT /api/admin/users/{user_id}/role  body={{role: {role!r}}}  HTTP {r.status_code}")


@when(parsers.parse('I deactivate user "{user_id}"'))
def deactivate_user(user_id, context, client):
    caller_role = context["user_role"]
    with patch("app.routes.admin._supabase_request", side_effect=_mock_supabase), \
         patch("app.utils.custom_decorators.get_role_for_user", return_value=caller_role):
        context["response"] = client.put(
            f"/api/admin/users/{user_id}/deactivate",
            headers=context["headers"],
        )
    r = context["response"]
    print(f"  ->PUT /api/admin/users/{user_id}/deactivate  HTTP {r.status_code}")


@when("I deactivate my own account")
def deactivate_own_account(context, client):
    # Route guard fires (user_id == g.user_id) before any Supabase call.
    with patch("app.routes.admin._supabase_request", side_effect=_mock_supabase), \
         patch("app.utils.custom_decorators.get_role_for_user", return_value="admin"):
        context["response"] = client.put(
            f"/api/admin/users/{ADMIN_USER_ID}/deactivate",
            headers=context["headers"],
        )
    r = context["response"]
    print(f"  ->PUT /api/admin/users/{ADMIN_USER_ID}/deactivate (self)  HTTP {r.status_code}")


# ---------------------------------------------------------------------------
# Then steps  [Formulation: assert the specified behavior holds]
# ---------------------------------------------------------------------------

@then(parsers.parse("the response status is {status:d}"))
def check_response_status(status, context):
    r = context["response"]
    assert r.status_code == status, (
        f"Expected HTTP {status}, got {r.status_code}. Body: {r.get_json()}"
    )
    print(f"  [OK]HTTP {status}")


@then('the response body contains a "users" array')
def check_users_array(context):
    data = context["response"].get_json()
    assert "users" in data and isinstance(data["users"], list)
    n = len(data["users"])
    print(f"  [OK]users array | {n} entr{'y' if n == 1 else 'ies'}")


@then('each user entry has "user_id", "email", "role", and "status" fields')
def check_user_fields(context):
    users = context["response"].get_json()["users"]
    required = ("user_id", "email", "role", "status")
    for user in users:
        for field in required:
            assert field in user, f"Missing '{field}' in: {user}"
    print(f"  [OK]all entries contain: {', '.join(required)}")


@then(parsers.parse('the response body confirms role was updated to "{role}"'))
def check_role_updated(role, context):
    data = context["response"].get_json()
    assert data.get("role") == role, f"Expected role={role!r}, got: {data}"
    print(f"  [OK]role updated to {role!r}")


@then("the response body contains an error about invalid role")
def check_invalid_role_error(context):
    data = context["response"].get_json()
    assert "error" in data
    assert "role" in data["error"].lower() or "invalid" in data["error"].lower()
    print(f"  [OK]error returned: {data['error']!r}")


@then("the response body confirms the user was deactivated")
def check_user_deactivated(context):
    data = context["response"].get_json()
    assert "message" in data and "deactivated" in data["message"].lower()
    print(f"  [OK]{data['message']!r}")


@then(parsers.parse('the response includes a user with status "{status}"'))
def check_user_has_status(status, context):
    users = context["response"].get_json()["users"]
    found = [u for u in users if u.get("status") == status]
    assert found, f"No user with status={status!r} in {[u.get('status') for u in users]}"
    print(f"  [OK]user status={status!r} (derived from banned_until field)")
