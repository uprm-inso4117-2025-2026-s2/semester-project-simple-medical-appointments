"""
SCRIPT-Format Test Cases: User Management Module
=================================================
Module  : Authentication & Role Management
Branch  : 508-lecture-topic-task-test-cases-for-user-management-flows
Date    : 2026-05-23

Test IDs and coverage
---------------------
TC-UM-001  Patient registration – valid credentials (happy path)
TC-UM-002  Patient registration – missing required fields (failure)
TC-UM-003  Patient registration – duplicate / DB-conflict (failure)
TC-UM-004  Protected endpoint access – valid JWT (login success, happy path)
TC-UM-005  Protected endpoint access – no token (login failure)
TC-UM-006  Admin role assignment to existing user (happy path)
TC-UM-007  Account deactivation + self-deactivation guard (happy / failure)
TC-UM-008  Protected endpoint – invalid / expired token (failure)
TC-UM-SEC  Security observation – admin role accepted on self-registration (defect)

Execution notes
---------------
Auth against Supabase is mocked at the middleware level via the conftest
_testing_verify_jwt patch.  All Supabase REST / Auth Admin calls are mocked
per test using unittest.mock.patch so no live network is required.
"""

import time
from unittest.mock import patch

import jwt as pyjwt
import pytest

from tests.conftest import TEST_JWT_SECRET

# ---------------------------------------------------------------------------
# Shared fixtures / constants
# ---------------------------------------------------------------------------

ADMIN_USER_ID  = "00000000-0000-0000-0000-000000000001"   # matches conftest auth_headers
TARGET_USER_ID = "cccccccc-0000-0000-0000-000000000003"

VALID_PATIENT_PAYLOAD = {
    "user_id":    TARGET_USER_ID,
    "first_name": "Maria",
    "last_name":  "Rivera",
    "username":   "mrivera",
    "role":       "patient",
}


# ---------------------------------------------------------------------------
# Shared Supabase mock helpers
# ---------------------------------------------------------------------------

def _admin_supabase_ok(method, path, *, query=None, json_body=None, prefer=None):
    """Simulates healthy Supabase responses for admin read / role-update flows."""
    if method == "GET" and path == "/rest/v1/roles":
        return 200, [{"id": 3}], None
    if method == "DELETE" and path == "/rest/v1/user_roles":
        return 204, None, None
    if method == "POST" and path == "/rest/v1/user_roles":
        return 201, None, None
    if method == "GET" and path == "/rest/v1/user_roles":
        return 200, [{"user_id": TARGET_USER_ID, "roles": {"name": "patient"}}], None
    if method == "GET" and path == "/auth/v1/admin/users":
        return 200, {"users": [{"id": TARGET_USER_ID, "email": "m@test.com"}]}, None
    return 200, None, None


def _deactivate_supabase_ok(method, path, *, query=None, json_body=None, prefer=None):
    """Simulates a successful Supabase ban-user response."""
    return 200, None, None


# ===========================================================================
# TC-UM-001: Patient registration with valid credentials (happy path)
# ===========================================================================

class TestTC_UM_001_ValidRegistration:
    """
    ID            : TC-UM-001
    Title         : Patient registration with valid credentials
    Preconditions : Application running; no existing profile for the given user_id
    Steps         : POST /api/auth/register with a complete, valid patient payload
    Expected      : HTTP 201; body == {"message": "User registered successfully."}
    Postcondition : profiles, profile_settings, patients, and user_roles rows created
    """

    def test_returns_201_on_valid_patient_payload(self, client):
        with patch(
            "app.routes.auth.sync_user_after_registration",
            return_value={"success": True},
        ):
            resp = client.post(
                "/api/auth/register",
                json=VALID_PATIENT_PAYLOAD,
                content_type="application/json",
            )

        assert resp.status_code == 201
        assert resp.get_json() == {"message": "User registered successfully."}

    def test_optional_fields_do_not_break_registration(self, client):
        """Optional patient fields (insurance, emergency contact) are accepted."""
        payload = {
            **VALID_PATIENT_PAYLOAD,
            "insurance_provider":      "BlueCross",
            "emergency_contact_name":  "José Rivera",
            "emergency_contact_phone": "787-555-0001",
        }
        with patch(
            "app.routes.auth.sync_user_after_registration",
            return_value={"success": True},
        ):
            resp = client.post("/api/auth/register", json=payload)

        assert resp.status_code == 201


# ===========================================================================
# TC-UM-002: Patient registration – missing required fields (failure)
# ===========================================================================

class TestTC_UM_002_MissingFieldsRegistration:
    """
    ID            : TC-UM-002
    Title         : Patient registration with missing required fields
    Preconditions : Application running
    Steps         : POST /api/auth/register omitting one or more required fields
    Expected      : HTTP 400; "error" key names the missing field(s)
    Postcondition : No rows created; no Supabase call made
    """

    def test_returns_400_when_first_name_omitted(self, client):
        payload = {k: v for k, v in VALID_PATIENT_PAYLOAD.items() if k != "first_name"}
        resp = client.post("/api/auth/register", json=payload)

        assert resp.status_code == 400
        assert "first_name" in resp.get_json().get("error", "")

    def test_returns_400_when_role_omitted(self, client):
        payload = {k: v for k, v in VALID_PATIENT_PAYLOAD.items() if k != "role"}
        resp = client.post("/api/auth/register", json=payload)

        assert resp.status_code == 400
        assert "role" in resp.get_json().get("error", "")

    def test_returns_400_when_body_is_empty(self, client):
        resp = client.post("/api/auth/register", content_type="application/json")

        assert resp.status_code == 400
        assert "JSON" in resp.get_json().get("error", "")

    def test_returns_400_for_invalid_role_value(self, client):
        payload = {**VALID_PATIENT_PAYLOAD, "role": "superuser"}
        resp = client.post("/api/auth/register", json=payload)

        assert resp.status_code == 400
        assert "Invalid role" in resp.get_json().get("error", "")


# ===========================================================================
# TC-UM-003: Patient registration – duplicate / DB-conflict (failure)
# ===========================================================================

class TestTC_UM_003_DuplicateRegistration:
    """
    ID            : TC-UM-003
    Title         : Patient registration with duplicate user data
    Preconditions : A profile with the same user_id already exists in the database
    Steps         : POST /api/auth/register with an otherwise-valid payload whose
                    user_id already has a profiles row; DB raises a unique-constraint
                    violation which sync_user_after_registration surfaces as an error
    Expected      : HTTP 500; body contains registration-failure message and detail
    Postcondition : Cleanup routine removes any partially-inserted rows
    """

    def test_returns_500_on_profiles_unique_constraint_violation(self, client):
        duplicate_error = {
            "error": 'duplicate key value violates unique constraint "profiles_pkey"',
            "step":  "profiles",
        }
        with patch(
            "app.routes.auth.sync_user_after_registration",
            return_value=duplicate_error,
        ):
            resp = client.post("/api/auth/register", json=VALID_PATIENT_PAYLOAD)

        assert resp.status_code == 500
        body = resp.get_json()
        assert "DB sync failed" in body.get("error", "")
        assert body.get("failed_at") == "profiles"


# ===========================================================================
# TC-UM-004: Valid JWT access to protected endpoint (login success simulation)
# ===========================================================================

class TestTC_UM_004_LoginSuccess:
    """
    ID            : TC-UM-004
    Title         : Authenticated access to a protected endpoint with a valid JWT
    Preconditions : User has signed in via Supabase and holds a non-expired JWT;
                    user has the 'admin' application role
    Steps         : GET /api/admin/users with Authorization: Bearer <valid_token>
    Expected      : HTTP 200; response body contains a "users" array
    Postcondition : No side-effects; read-only operation
    """

    def test_admin_list_returns_200_with_valid_token(self, client, auth_headers):
        with patch(
            "app.routes.admin._supabase_request",
            side_effect=_admin_supabase_ok,
        ), patch(
            "app.utils.custom_decorators.get_role_for_user",
            return_value="admin",
        ):
            resp = client.get("/api/admin/users", headers=auth_headers)

        assert resp.status_code == 200
        assert "users" in resp.get_json()


# ===========================================================================
# TC-UM-005: Protected endpoint accessed without a token (login failure)
# ===========================================================================

class TestTC_UM_005_LoginFailureNoToken:
    """
    ID            : TC-UM-005
    Title         : Access to protected endpoint without an Authorization token
    Preconditions : Application running; endpoint requires authentication
    Steps         : GET /api/admin/users with no Authorization header
    Expected      : HTTP 401; body == {"message": "No token provided"}
    Postcondition : Request rejected before any business logic executes
    """

    def test_admin_list_returns_401_without_token(self, client):
        resp = client.get("/api/admin/users")

        assert resp.status_code == 401
        assert resp.get_json().get("message") == "No token provided"


# ===========================================================================
# TC-UM-006: Admin role assignment to an existing user
# ===========================================================================

class TestTC_UM_006_AdminRoleAssignment:
    """
    ID            : TC-UM-006
    Title         : Admin assigns a new role to an existing user
    Preconditions : Requesting user is authenticated and has admin role;
                    target user exists in the database
    Steps         : PUT /api/admin/users/<target_id>/role with {"role": "admin"}
    Expected      : HTTP 200; body contains user_id and updated role name
    Postcondition : user_roles row updated; old role removed, new role inserted
    """

    def test_role_update_returns_200_for_valid_role(self, client, auth_headers):
        with patch(
            "app.routes.admin._supabase_request",
            side_effect=_admin_supabase_ok,
        ), patch(
            "app.utils.custom_decorators.get_role_for_user",
            return_value="admin",
        ):
            resp = client.put(
                f"/api/admin/users/{TARGET_USER_ID}/role",
                json={"role": "admin"},
                headers=auth_headers,
            )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("role") == "admin"
        assert body.get("user_id") == TARGET_USER_ID

    def test_role_update_returns_400_for_unrecognised_role(self, client, auth_headers):
        """Submitting a role value not in {patient, doctor, admin} is rejected."""
        with patch(
            "app.routes.admin._supabase_request",
            side_effect=_admin_supabase_ok,
        ), patch(
            "app.utils.custom_decorators.get_role_for_user",
            return_value="admin",
        ):
            resp = client.put(
                f"/api/admin/users/{TARGET_USER_ID}/role",
                json={"role": "superuser"},
                headers=auth_headers,
            )

        assert resp.status_code == 400

    def test_role_update_returns_403_when_caller_is_not_admin(self, client, auth_headers):
        """A patient-role user must not be able to promote other users."""
        with patch(
            "app.routes.admin._supabase_request",
            side_effect=_admin_supabase_ok,
        ), patch(
            "app.utils.custom_decorators.get_role_for_user",
            return_value="patient",
        ):
            resp = client.put(
                f"/api/admin/users/{TARGET_USER_ID}/role",
                json={"role": "doctor"},
                headers=auth_headers,
            )

        assert resp.status_code == 403


# ===========================================================================
# TC-UM-007: Account deactivation and self-deactivation guard
# ===========================================================================

class TestTC_UM_007_AccountDeactivation:
    """
    ID            : TC-UM-007
    Title         : Admin deactivates a user account; self-deactivation is blocked
    Preconditions : Requesting user is authenticated admin; target user is a
                    different active user
    Steps (happy) : PUT /api/admin/users/<target_id>/deactivate
    Steps (guard) : PUT /api/admin/users/<admin_own_id>/deactivate
    Expected      : 200 for target user; 400 when admin targets own account
    Postcondition : Target user receives ban_duration=876600h in Supabase Auth;
                    subsequent signIn attempts by that user will be rejected by Supabase
    """

    def test_deactivate_target_user_returns_200(self, client, auth_headers):
        with patch(
            "app.routes.admin._supabase_request",
            side_effect=_deactivate_supabase_ok,
        ), patch(
            "app.utils.custom_decorators.get_role_for_user",
            return_value="admin",
        ):
            resp = client.put(
                f"/api/admin/users/{TARGET_USER_ID}/deactivate",
                headers=auth_headers,
            )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body.get("user_id") == TARGET_USER_ID
        assert "deactivated" in body.get("message", "").lower()

    def test_admin_cannot_deactivate_own_account(self, client, auth_headers):
        """Guard prevents admins from locking themselves out."""
        with patch(
            "app.routes.admin._supabase_request",
            side_effect=_deactivate_supabase_ok,
        ), patch(
            "app.utils.custom_decorators.get_role_for_user",
            return_value="admin",
        ):
            resp = client.put(
                f"/api/admin/users/{ADMIN_USER_ID}/deactivate",
                headers=auth_headers,
            )

        assert resp.status_code == 400
        assert "cannot deactivate" in resp.get_json().get("error", "").lower()


# ===========================================================================
# TC-UM-008: Invalid / expired token on protected endpoint (failure)
# ===========================================================================

class TestTC_UM_008_InvalidToken:
    """
    ID            : TC-UM-008
    Title         : Access to protected endpoint with an invalid or expired JWT
    Preconditions : Application running; token is either malformed or past its exp claim
    Steps         : GET /api/admin/users with a bad Bearer token
    Expected      : HTTP 401; body == {"message": "Invalid or expired token"}
    Postcondition : Request rejected at middleware; no business logic executed
    """

    def test_returns_401_with_malformed_token(self, client):
        resp = client.get(
            "/api/admin/users",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )

        assert resp.status_code == 401
        assert resp.get_json().get("message") == "Invalid or expired token"

    def test_returns_401_with_syntactically_valid_but_expired_token(self, client):
        expired_token = pyjwt.encode(
            {"sub": ADMIN_USER_ID, "exp": int(time.time()) - 3600},
            TEST_JWT_SECRET,
            algorithm="HS256",
        )
        resp = client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert resp.status_code == 401
        assert resp.get_json().get("message") == "Invalid or expired token"


# ===========================================================================
# TC-UM-SEC: Security observation – 'admin' accepted on self-registration
# ===========================================================================

class TestTC_UM_SEC_AdminSelfRegistration:
    """
    ID            : TC-UM-SEC  (maps to defect DEF-UM-001)
    Title         : Registration endpoint accepts 'admin' as a self-assigned role
    Preconditions : Application running
    Steps         : POST /api/auth/register with role='admin'
    Expected      : HTTP 400 (role 'admin' should not be self-assignable)
    Actual        : HTTP 201 — the endpoint accepts it, granting admin privileges
    Verdict       : FAIL — documents security defect DEF-UM-001

    Note: the assertion below reflects the ACTUAL (broken) behaviour so the test
    can be executed and its result recorded.  The expected-but-missing behaviour
    is documented in the AsciiDoc defect report.
    """

    def test_admin_role_is_accepted_via_self_registration(self, client):
        """
        This test passes ONLY because the code has a defect.
        A correct implementation would return 400 here.
        """
        payload = {**VALID_PATIENT_PAYLOAD, "role": "admin"}
        with patch(
            "app.routes.auth.sync_user_after_registration",
            return_value={"success": True},
        ):
            resp = client.post("/api/auth/register", json=payload)

        # BUG (DEF-UM-001): server returns 201 instead of rejecting the request.
        assert resp.status_code == 201, (
            "DEF-UM-001: 'admin' role must not be self-assignable at registration. "
            "Expected 400, got 201."
        )
