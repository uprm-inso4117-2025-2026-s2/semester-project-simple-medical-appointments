import json
import pytest
from unittest.mock import patch
 
TEST_USER_ID  = "00000000-0000-0000-0000-000000000001"  # must match conftest JWT sub
OTHER_USER_ID = "bbbbbbbb-0000-0000-0000-000000000002"
BEARER        = "Bearer test-token"
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _profile_row(user_id=TEST_USER_ID, phone_number=None):
    return {
        "user_id":      user_id,
        "first_name":   "Jane",
        "last_name":    "Smith",
        "display_name": "Dr. Jane Smith",
        "username":     "drjanesmith",
        "avatar_url":   None,
        "phone_number": phone_number,
        "date_of_birth": None,
        "gender":       None,
        "created_at":   "2025-01-01T00:00:00Z",
    }
 
 
def _provider_row(specialty="General Practice", bio=None):
    return {
        "specialty":        specialty,
        "bio":              bio,
        "profession_title": "MD",
        "license_number":   None,
        "license_state":    None,
    }
 
 
def _settings_row(user_id=TEST_USER_ID):
    return {
        "user_id":                       user_id,
        "preferred_contact_method":      "email",
        "preferred_language":            "en",
        "notify_appointment_reminders":  True,
        "notify_appointment_updates":    True,
        "notify_messages":               True,
        "accessibility_mode":            "default",
    }
 
 
def _mock_supabase_request_factory(
    profile_row,
    provider_row=None,
    settings_row=None,
    patch_status=204,
):
    """Return a side_effect function that simulates Supabase REST responses.
 
    Handles the full call sequence for update_profile when doctor fields
    (specialty, bio) are present:
      auth → roles → PATCH profiles → GET providers (exists check)
      → PATCH providers → _fetch_profile_payload (5 GET calls)
    """
    def _mock(method, path, *, query=None, json_body=None, user_token=None, prefer=None):
        # ── auth ──────────────────────────────────────────────────────────
        if path == "/auth/v1/user":
            return 200, {"id": TEST_USER_ID}, None
 
        if path == "/rest/v1/user_roles":
            return 200, [{"roles": {"name": "doctor"}}], None
 
        # ── profile table ─────────────────────────────────────────────────
        if path == "/rest/v1/profiles" and method == "GET":
            return 200, [profile_row], None
 
        if path == "/rest/v1/profiles" and method == "PATCH":
            return patch_status, None, None
 
        # ── providers table ───────────────────────────────────────────────
        if path == "/rest/v1/providers" and method == "GET":
            # existence check during provider update uses select=user_id
            if provider_row is not None:
                return 200, [provider_row], None
            return 200, [], None
 
        if path == "/rest/v1/providers" and method == "PATCH":
            return patch_status, None, None
 
        # ── supporting tables (fetch-profile reads) ───────────────────────
        if path == "/rest/v1/provider_settings" and method == "GET":
            return 200, [], None
 
        if path == "/rest/v1/patients" and method == "GET":
            return 200, [], None
 
        if path == "/rest/v1/profile_settings" and method == "GET":
            return 200, [settings_row] if settings_row else [], None
 
        if path == "/rest/v1/profile_settings" and method == "PATCH":
            return patch_status, None, None
 
        return 200, None, None
 
    return _mock
 
 
# ---------------------------------------------------------------------------
# PUT /api/profile/<user_id> — doctor fields
# ---------------------------------------------------------------------------
 
class TestDoctorProfileUpdate:
    """Valid doctor update: phone_number, specialty, bio → 200."""
 
    def test_doctor_update_returns_200(self, client, auth_headers):
        """A well-formed doctor update request succeeds."""
        mock_req = _mock_supabase_request_factory(
            _profile_row(phone_number="+1-787-555-0100"),
            _provider_row(specialty="Cardiology", bio="Expert cardiologist."),
            _settings_row(),
        )
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({
                    "phone_number": "+1-787-555-0100",
                    "specialty":    "Cardiology",
                    "bio":          "Expert cardiologist.",
                }),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 200
 
    def test_doctor_update_phone_number_persists_in_db(self, client, auth_headers):
        """Response reflects the updated phone_number from the re-fetched profile."""
        mock_req = _mock_supabase_request_factory(
            _profile_row(phone_number="+1-787-555-0100"),
            _provider_row(),
            _settings_row(),
        )
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"phone_number": "+1-787-555-0100"}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 200
        data = response.get_json()
        assert data["phone_number"] == "+1-787-555-0100"
 
    def test_doctor_update_specialty_persists_in_db(self, client, auth_headers):
        """Response reflects the updated specialty from the re-fetched provider row."""
        mock_req = _mock_supabase_request_factory(
            _profile_row(),
            _provider_row(specialty="Cardiology"),
            _settings_row(),
        )
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"specialty": "Cardiology"}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 200
        data = response.get_json()
        assert data["specialty"] == "Cardiology"
 
    def test_doctor_update_bio_persists_in_db(self, client, auth_headers):
        """Response reflects the updated bio from the re-fetched provider row."""
        bio_text = "Board-certified cardiologist with 15 years of experience."
        mock_req = _mock_supabase_request_factory(
            _profile_row(),
            _provider_row(bio=bio_text),
            _settings_row(),
        )
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"bio": bio_text}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 200
        data = response.get_json()
        assert data["bio"] == bio_text
 
    def test_doctor_update_null_specialty_clears_field(self, client, auth_headers):
        """Sending null for specialty is valid and clears the field."""
        mock_req = _mock_supabase_request_factory(
            _profile_row(),
            _provider_row(specialty=None),
            _settings_row(),
        )
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"specialty": None}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 200
        data = response.get_json()
        assert data["specialty"] is None
 
 
# ---------------------------------------------------------------------------
# PUT /api/profile/<user_id> — cross-user 403
# ---------------------------------------------------------------------------
 
class TestDoctorProfileUpdateForbidden:
    """Non-admin user attempting to update a different user's profile → 403."""
 
    def test_update_forbidden_for_different_user(self, client, auth_headers):
        """A user authenticated as OTHER_USER_ID cannot update TEST_USER_ID's profile."""
        def _mock(method, path, *, query=None, json_body=None, user_token=None, prefer=None):
            if path == "/auth/v1/user":
                return 200, {"id": OTHER_USER_ID}, None
            if path == "/rest/v1/user_roles":
                return 200, [{"roles": {"name": "doctor"}}], None
            return 200, None, None
 
        with patch("app.routes.profile._supabase_request", side_effect=_mock):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"specialty": "Neurology"}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 403
 
    def test_update_forbidden_error_message(self, client, auth_headers):
        """403 response includes a descriptive error message."""
        def _mock(method, path, *, query=None, json_body=None, user_token=None, prefer=None):
            if path == "/auth/v1/user":
                return 200, {"id": OTHER_USER_ID}, None
            if path == "/rest/v1/user_roles":
                return 200, [], None
            return 200, None, None
 
        with patch("app.routes.profile._supabase_request", side_effect=_mock):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"specialty": "Neurology"}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        data = response.get_json()
        assert "error" in data
        assert "forbidden" in data["error"].lower() or "only update your own" in data["error"].lower()
 
 
# ---------------------------------------------------------------------------
# PUT /api/profile/<user_id> — invalid doctor update requests → 400
# ---------------------------------------------------------------------------
 
class TestDoctorProfileUpdateInvalidRequests:
    """Malformed or out-of-range doctor field values → 400."""
 
    def test_update_rejects_unknown_fields(self, client, auth_headers):
        """Fields outside ALLOWED_UPDATE_FIELDS return 400 with the field name listed."""
        mock_req = _mock_supabase_request_factory(_profile_row())
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"license_number": "XYZ-999"}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 400
        assert "Unknown fields" in response.get_json().get("error", "")
 
    def test_update_rejects_specialty_too_long(self, client, auth_headers):
        """specialty exceeding 100 characters returns 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"specialty": "X" * 101}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 400
        error = response.get_json().get("error", "")
        assert "specialty" in error.lower()
        assert "100" in error
 
    def test_update_rejects_bio_too_long(self, client, auth_headers):
        """bio exceeding 1000 characters returns 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"bio": "B" * 1001}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 400
        error = response.get_json().get("error", "")
        assert "bio" in error.lower()
        assert "1000" in error
 
    def test_update_rejects_phone_number_too_long(self, client, auth_headers):
        """phone_number exceeding 30 characters returns 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"phone_number": "1" * 31}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 400
        error = response.get_json().get("error", "")
        assert "phone_number" in error.lower()
        assert "30" in error
 
    def test_update_rejects_specialty_wrong_type(self, client, auth_headers):
        """specialty must be a string or null — integers return 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({"specialty": 42}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 400
        assert "specialty" in response.get_json().get("error", "").lower()
 
    def test_update_rejects_empty_body(self, client, auth_headers):
        """An empty JSON object with no fields returns 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data=json.dumps({}),
                content_type="application/json",
                headers=auth_headers,
            )
 
        assert response.status_code == 400
 
    def test_update_requires_json_content_type(self, client, auth_headers):
        """Request without Content-Type: application/json returns 415."""
        mock_req = _mock_supabase_request_factory(_profile_row())
 
        with patch("app.routes.profile._supabase_request", side_effect=mock_req):
            response = client.put(
                f"/api/profile/{TEST_USER_ID}",
                data="specialty=Cardiology",
                headers={"Authorization": auth_headers["Authorization"]},
            )
 
        assert response.status_code == 415
 
    def test_update_requires_auth(self, client):
        """Request without Authorization header returns 401."""
        response = client.put(
            f"/api/profile/{TEST_USER_ID}",
            data=json.dumps({"specialty": "Cardiology"}),
            content_type="application/json",
        )
 
        assert response.status_code == 401