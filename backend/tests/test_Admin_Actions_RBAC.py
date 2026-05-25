from unittest.mock import patch

# These tests validate the admin user management endpoints which indirectly test
# role-based access control enforced by the requires_role decorator and
# the _supabase_request helper used by all admin routes.
# We are testing the full admin management flow logic, including:
# - Listing all users (GET /api/admin/users)
# - Updating a user's role (PUT /api/admin/users/<id>/role)
# - Deactivating a user account (PUT /api/admin/users/<id>/deactivate)
# - Deleting a user from auth and DB (DELETE /api/admin/users/<id>)
#
# The goal is to ensure:
# - Admin can perform all user management actions successfully
# - Each action calls Supabase with the correct payload and order
# - Non-admin roles (doctor, patient) receive 403 on all admin endpoints
# - Unauthenticated requests are rejected with 401/403
# - Edge cases (self-deactivation, self-deletion, invalid inputs) return correct codes
#
# External dependencies (Supabase REST + Auth Admin API) are mocked using
# unittest.mock.patch to isolate route logic and avoid real network calls.
# The requires_role decorator's DB lookup (get_role_for_user) is also mocked
# so tests are not coupled to a live user_roles table.
#
# For testing go to backend directory in terminal: cd backend
# Run the test file with: python3.13 -m pytest tests/test_Admin_Actions_RBAC.py -v

import jwt
import pytest

TEST_JWT_SECRET = "test-jwt-secret-for-pytest-only-32bytes!!"

ADMIN_ID   = "aaaaaaaa-0000-0000-0000-000000000001"
DOCTOR_ID  = "bbbbbbbb-0000-0000-0000-000000000002"
PATIENT_ID = "cccccccc-0000-0000-0000-000000000003"
TARGET_ID  = "dddddddd-0000-0000-0000-000000000004"

SUPABASE_REQUEST = "app.routes.admin._supabase_request"
GET_ROLE         = "app.utils.custom_decorators.get_role_for_user"


def _mint(app, sub: str) -> str:
    token = jwt.encode(
        {"sub": sub},
        app.config["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )
    return token if isinstance(token, str) else token.decode("ascii")


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token(app):
    return _mint(app, ADMIN_ID)

@pytest.fixture
def doctor_token(app):
    return _mint(app, DOCTOR_ID)

@pytest.fixture
def patient_token(app):
    return _mint(app, PATIENT_ID)

@pytest.fixture
def admin_headers(admin_token):
    return _h(admin_token)

@pytest.fixture
def doctor_headers(doctor_token):
    return _h(doctor_token)

@pytest.fixture
def patient_headers(patient_token):
    return _h(patient_token)


_USER_ROW = {
    "id": TARGET_ID,
    "email": "target@example.com",
    "created_at": "2024-01-01T00:00:00Z",
    "last_sign_in_at": None,
    "banned_until": None,
}

_ROLE_ROWS = [
    {"user_id": TARGET_ID, "roles": {"name": "patient"}},
    {"user_id": ADMIN_ID,  "roles": {"name": "admin"}},
]

_AUTH_USERS_PAGE = {"users": [_USER_ROW]}


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/admin/users
# ─────────────────────────────────────────────────────────────────────────────

class TestListUsers:

    def _supabase_calls(self):
        return [
            (200, _ROLE_ROWS,       None),
            (200, _AUTH_USERS_PAGE, None),
        ]

    #<------------------- SUCCESS ─────────────────────────────────────────-->
    def test_admin_receives_user_list(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.get("/api/admin/users", headers=admin_headers)

        assert resp.status_code == 200
        body = resp.get_json()
        assert "users" in body
        assert isinstance(body["users"], list)
        assert "total" in body

    #<------------------- RESPONSE SHAPE ──────────────────────────────────-->
    def test_response_shape(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.get("/api/admin/users", headers=admin_headers)

        user = resp.get_json()["users"][0]
        for field in ("user_id", "email", "role", "status"):
            assert field in user, f"Missing field '{field}' in user object"

    #<------------------- ACTIVE STATUS ───────────────────────────────────-->
    def test_active_user_has_active_status(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.get("/api/admin/users", headers=admin_headers)

        users = resp.get_json()["users"]
        target = next((u for u in users if u["user_id"] == TARGET_ID), None)
        assert target is not None
        assert target["status"] == "active"

    #<------------------- DOCTOR FORBIDDEN ────────────────────────────────-->
    def test_doctor_is_forbidden(self, client, doctor_headers):
        with patch(GET_ROLE, return_value="doctor"):
            resp = client.get("/api/admin/users", headers=doctor_headers)
        assert resp.status_code == 403

    #<------------------- PATIENT FORBIDDEN ───────────────────────────────-->
    def test_patient_is_forbidden(self, client, patient_headers):
        with patch(GET_ROLE, return_value="patient"):
            resp = client.get("/api/admin/users", headers=patient_headers)
        assert resp.status_code == 403

    #<------------------- UNAUTHENTICATED ─────────────────────────────────-->
    def test_unauthenticated_is_rejected(self, client):
        resp = client.get("/api/admin/users")
        assert resp.status_code in (401, 403)

    #<------------------- INVALID ROLE FILTER ─────────────────────────────-->
    def test_invalid_role_filter_returns_400(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.get("/api/admin/users?role=superuser", headers=admin_headers)
        assert resp.status_code == 400

    #<------------------- INVALID STATUS FILTER ───────────────────────────-->
    def test_invalid_status_filter_returns_400(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.get("/api/admin/users?status=banned", headers=admin_headers)
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/admin/users/<user_id>/role
# ─────────────────────────────────────────────────────────────────────────────

class TestChangeRole:
    URL = f"/api/admin/users/{TARGET_ID}/role"

    def _supabase_calls(self):
        return [
            (200, [{"id": "role-uuid-doctor"}], None),
            (204, None, None),
            (201, None, None),
        ]

    #<------------------- SUCCESS ─────────────────────────────────────────-->
    def test_admin_can_change_role(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.put(self.URL, json={"role": "doctor"}, headers=admin_headers)

        assert resp.status_code == 200

    #<------------------- RESPONSE CONTAINS NEW ROLE ──────────────────────-->
    def test_response_contains_new_role(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.put(self.URL, json={"role": "doctor"}, headers=admin_headers)

        body = resp.get_json()
        assert body["role"] == "doctor"
        assert body["user_id"] == TARGET_ID

    #<------------------- MISSING ROLE FIELD ──────────────────────────────-->
    def test_missing_role_field_returns_400(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"):
            resp = client.put(self.URL, json={}, headers=admin_headers)
        assert resp.status_code == 400

    #<------------------- INVALID ROLE VALUE ──────────────────────────────-->
    def test_invalid_role_value_returns_400(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"):
            resp = client.put(self.URL, json={"role": "superuser"}, headers=admin_headers)
        assert resp.status_code == 400

    #<------------------- DOCTOR FORBIDDEN ────────────────────────────────-->
    def test_doctor_cannot_change_role(self, client, doctor_headers):
        with patch(GET_ROLE, return_value="doctor"):
            resp = client.put(self.URL, json={"role": "admin"}, headers=doctor_headers)
        assert resp.status_code == 403

    #<------------------- PATIENT FORBIDDEN ───────────────────────────────-->
    def test_patient_cannot_change_role(self, client, patient_headers):
        with patch(GET_ROLE, return_value="patient"):
            resp = client.put(self.URL, json={"role": "admin"}, headers=patient_headers)
        assert resp.status_code == 403

    #<------------------- DB SYNC FAILURE ─────────────────────────────────-->
    def test_supabase_failure_returns_500(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=[
                 (200, [{"id": "role-uuid-doctor"}], None),
                 (500, None, "DB error"),
             ]):
            resp = client.put(self.URL, json={"role": "doctor"}, headers=admin_headers)
        assert resp.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/admin/users/<user_id>/deactivate
# ─────────────────────────────────────────────────────────────────────────────

class TestDeactivateUser:
    URL = f"/api/admin/users/{TARGET_ID}/deactivate"

    #<------------------- SUCCESS ─────────────────────────────────────────-->
    def test_admin_can_deactivate(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, return_value=(200, {}, None)):
            resp = client.put(self.URL, headers=admin_headers)

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["user_id"] == TARGET_ID
        assert "deactivated" in body["message"].lower()

    #<------------------- BAN DURATION PAYLOAD ────────────────────────────-->
    def test_supabase_called_with_ban_duration(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, return_value=(200, {}, None)) as mock_sb:
            client.put(self.URL, headers=admin_headers)

        ban_call = next(
            (c for c in mock_sb.call_args_list
             if "ban_duration" in (c.kwargs.get("json_body") or {})),
            None,
        )
        assert ban_call is not None, "ban_duration was never sent to Supabase"
        assert ban_call.kwargs["json_body"]["ban_duration"] == "876600h"

    #<------------------- SELF DEACTIVATION BLOCKED ───────────────────────-->
    def test_admin_cannot_deactivate_self(self, client, app):
        self_token = _mint(app, ADMIN_ID)
        self_url   = f"/api/admin/users/{ADMIN_ID}/deactivate"

        with patch(GET_ROLE, return_value="admin"):
            resp = client.put(self_url, headers=_h(self_token))
        assert resp.status_code == 400

    #<------------------- DOCTOR FORBIDDEN ────────────────────────────────-->
    def test_doctor_cannot_deactivate(self, client, doctor_headers):
        with patch(GET_ROLE, return_value="doctor"):
            resp = client.put(self.URL, headers=doctor_headers)
        assert resp.status_code == 403

    #<------------------- PATIENT FORBIDDEN ───────────────────────────────-->
    def test_patient_cannot_deactivate(self, client, patient_headers):
        with patch(GET_ROLE, return_value="patient"):
            resp = client.put(self.URL, headers=patient_headers)
        assert resp.status_code == 403

    #<------------------- DB SYNC FAILURE ─────────────────────────────────-->
    def test_supabase_failure_returns_500(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, return_value=(500, None, "upstream error")):
            resp = client.put(self.URL, headers=admin_headers)
        assert resp.status_code == 500


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /api/admin/users/<user_id>
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteUser:
    URL = f"/api/admin/users/{TARGET_ID}"

    def _supabase_calls(self):
        ok = (204, None, None)
        return [(200, [], None)] + [ok] * 9 + [(204, None, None)]

    #<------------------- SUCCESS ─────────────────────────────────────────-->
    def test_admin_can_delete_user(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()):
            resp = client.delete(self.URL, headers=admin_headers)

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["user_id"] == TARGET_ID
        assert "deleted" in body["message"].lower()

    #<------------------- AUTH DELETED LAST ───────────────────────────────-->
    def test_auth_user_deleted_last(self, client, admin_headers):
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=self._supabase_calls()) as mock_sb:
            client.delete(self.URL, headers=admin_headers)

        last_call = mock_sb.call_args_list[-1]
        path = last_call.args[1] if len(last_call.args) > 1 else ""
        assert f"/auth/v1/admin/users/{TARGET_ID}" in path

    #<------------------- DOCTOR ROWS DELETED WHEN PROVIDER ───────────────-->
    def test_doctor_linked_rows_deleted_when_provider(self, client, admin_headers):
        ok = (204, None, None)
        side_effects = (
            [(200, [{"user_id": TARGET_ID}], None)]
            + [ok] * 4
            + [ok] * 2
            + [ok] * 4
            + [ok] * 3
            + [(204, None, None)]
        )
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=side_effects) as mock_sb:
            resp = client.delete(self.URL, headers=admin_headers)

        assert resp.status_code == 200
        assert mock_sb.call_count > 11

    #<------------------- SELF DELETION BLOCKED ───────────────────────────-->
    def test_admin_cannot_delete_self(self, client, app):
        self_token = _mint(app, ADMIN_ID)
        self_url   = f"/api/admin/users/{ADMIN_ID}"

        with patch(GET_ROLE, return_value="admin"):
            resp = client.delete(self_url, headers=_h(self_token))
        assert resp.status_code == 400

    #<------------------- DOCTOR FORBIDDEN ────────────────────────────────-->
    def test_doctor_cannot_delete(self, client, doctor_headers):
        with patch(GET_ROLE, return_value="doctor"):
            resp = client.delete(self.URL, headers=doctor_headers)
        assert resp.status_code == 403

    #<------------------- PATIENT FORBIDDEN ───────────────────────────────-->
    def test_patient_cannot_delete(self, client, patient_headers):
        with patch(GET_ROLE, return_value="patient"):
            resp = client.delete(self.URL, headers=patient_headers)
        assert resp.status_code == 403

    #<------------------- AUTH DELETION FAILURE ───────────────────────────-->
    def test_auth_deletion_failure_returns_500(self, client, admin_headers):
        ok = (204, None, None)
        side_effects = (
            [(200, [], None)]
            + [ok] * 9
            + [(500, None, "auth error")]
        )
        with patch(GET_ROLE, return_value="admin"), \
             patch(SUPABASE_REQUEST, side_effect=side_effects):
            resp = client.delete(self.URL, headers=admin_headers)
        assert resp.status_code == 500