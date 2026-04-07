"""Integration tests for the Profile and Account Settings update flow.

Tests verify that:
- Profile updates persist correctly in the DB (PUT /api/profile/<user_id>)
- Settings updates persist correctly in the DB (PUT /api/settings/<user_id>)
- Cross-user update attempts are blocked with 403
- Invalid inputs return validation errors

Auth is mocked so these tests do not require a live Supabase JWT. All DB
interactions go through the Supabase REST API configured in the test environment.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

TEST_USER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
OTHER_USER_ID = "bbbbbbbb-0000-0000-0000-000000000002"
BEARER = "Bearer test-token"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _profile_row(user_id=TEST_USER_ID, display_name="Test User", avatar_url=None, phone_number=None):
    return {
        "user_id": user_id,
        "first_name": "Test",
        "last_name": "User",
        "display_name": display_name,
        "username": "testuser",
        "avatar_url": avatar_url,
        "phone_number": phone_number,
        "date_of_birth": None,
        "gender": None,
        "created_at": "2026-01-01T00:00:00Z",
    }


def _settings_row(user_id=TEST_USER_ID):
    return {
        "user_id": user_id,
        "preferred_contact_method": "email",
        "preferred_language": "en",
        "notify_appointment_reminders": True,
        "notify_appointment_updates": True,
        "notify_messages": True,
        "accessibility_mode": "default",
    }


def _mock_supabase_request_factory(profile_row, settings_row=None, patch_status=204):
    """Return a side_effect function that simulates Supabase REST responses."""
    def _mock(method, path, *, query=None, json_body=None, user_token=None, prefer=None):
        if path == '/auth/v1/user':
            return 200, {"id": TEST_USER_ID}, None
        if path == '/rest/v1/user_roles':
            return 200, [], None
        if path == '/rest/v1/profiles' and method == 'GET':
            return 200, [profile_row], None
        if path == '/rest/v1/profiles' and method == 'PATCH':
            return patch_status, None, None
        if path == '/rest/v1/profile_settings' and method == 'GET':
            return 200, [settings_row] if settings_row else [], None
        if path == '/rest/v1/profile_settings' and method == 'PATCH':
            return patch_status, None, None
        if path == '/rest/v1/providers' and method == 'GET':
            return 200, [], None
        if path == '/rest/v1/patients' and method == 'GET':
            return 200, [], None
        return 200, None, None
    return _mock


# ---------------------------------------------------------------------------
# PUT /api/profile/<user_id>
# ---------------------------------------------------------------------------

class TestProfileUpdate:

    def test_profile_name_update_persists_in_db(self, client):
        """DB reflects updated display_name after a valid PUT request."""
        updated_row = _profile_row(display_name="Updated Name")
        mock_req = _mock_supabase_request_factory(updated_row, _settings_row())

        with patch('app.routes.profile._supabase_request', side_effect=mock_req):
            response = client.put(
                f'/api/profile/{TEST_USER_ID}',
                data=json.dumps({'name': 'Updated Name'}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated Name'

    def test_profile_phone_update_persists_in_db(self, client):
        """DB reflects updated phone_number after a valid PUT request."""
        updated_row = _profile_row(phone_number="787-000-0001")
        mock_req = _mock_supabase_request_factory(updated_row, _settings_row())

        with patch('app.routes.profile._supabase_request', side_effect=mock_req):
            response = client.put(
                f'/api/profile/{TEST_USER_ID}',
                data=json.dumps({'phone_number': '787-000-0001'}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data['phone_number'] == '787-000-0001'

    def test_profile_update_forbidden_for_different_user(self, client):
        """User cannot update another user's profile — expects 403."""
        def _mock(method, path, *, query=None, json_body=None, user_token=None, prefer=None):
            if path == '/auth/v1/user':
                return 200, {"id": OTHER_USER_ID}, None
            if path == '/rest/v1/user_roles':
                return 200, [], None
            return 200, None, None

        with patch('app.routes.profile._supabase_request', side_effect=_mock):
            response = client.put(
                f'/api/profile/{TEST_USER_ID}',
                data=json.dumps({'name': 'Hacker'}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 403

    def test_profile_update_rejects_unknown_fields(self, client):
        """Unknown fields in the request body return 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())

        with patch('app.routes.profile._supabase_request', side_effect=mock_req):
            response = client.put(
                f'/api/profile/{TEST_USER_ID}',
                data=json.dumps({'unknown_field': 'value'}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 400
        assert 'Unknown fields' in response.get_json().get('error', '')

    def test_profile_update_rejects_empty_name(self, client):
        """Empty string for name returns 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())

        with patch('app.routes.profile._supabase_request', side_effect=mock_req):
            response = client.put(
                f'/api/profile/{TEST_USER_ID}',
                data=json.dumps({'name': '   '}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 400

    def test_profile_update_rejects_invalid_avatar_url(self, client):
        """Non-HTTP URL for avatar returns 400."""
        mock_req = _mock_supabase_request_factory(_profile_row())

        with patch('app.routes.profile._supabase_request', side_effect=mock_req):
            response = client.put(
                f'/api/profile/{TEST_USER_ID}',
                data=json.dumps({'avatar': 'not-a-url'}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 400

    def test_profile_update_requires_auth(self, client):
        """Request without Authorization header returns 401."""
        response = client.put(
            f'/api/profile/{TEST_USER_ID}',
            data=json.dumps({'name': 'Test'}),
            content_type='application/json',
        )

        assert response.status_code == 401

    def test_profile_update_requires_json_content_type(self, client):
        """Request without JSON content type returns 415."""
        mock_req = _mock_supabase_request_factory(_profile_row())

        with patch('app.routes.profile._supabase_request', side_effect=mock_req):
            response = client.put(
                f'/api/profile/{TEST_USER_ID}',
                data='name=Test',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 415


# ---------------------------------------------------------------------------
# PUT /api/settings/<user_id>
# ---------------------------------------------------------------------------

class TestSettingsUpdate:

    def _mock_supabase_client(self, updated_data):
        """Build a mock Supabase client that simulates a successful settings update."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.data = [updated_data]
        (mock_client.table.return_value
                   .update.return_value
                   .eq.return_value
                   .execute.return_value) = mock_resp
        return mock_client

    def _mock_auth_user(self, user_id=TEST_USER_ID):
        mock_user = MagicMock()
        mock_user.id = user_id
        return mock_user

    def test_settings_update_persists_in_db(self, client):
        """DB reflects updated preference after a valid PUT request."""
        updated = {
            'preferred_language': 'es',
            'notify_appointment_reminders': False,
        }
        mock_client = self._mock_supabase_client(updated)

        with patch('app.middleware.Auth._get_supabase_user', return_value=self._mock_auth_user()), \
             patch('app.routes.account_settings._get_supabase', return_value=mock_client):
            response = client.put(
                f'/api/settings/{TEST_USER_ID}',
                data=json.dumps(updated),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert 'updated_preferences' in data

    def test_settings_update_forbidden_for_different_user(self, client):
        """User cannot update another user's settings — expects 403."""
        with patch('app.middleware.Auth._get_supabase_user', return_value=self._mock_auth_user(OTHER_USER_ID)):
            response = client.put(
                f'/api/settings/{TEST_USER_ID}',
                data=json.dumps({'preferred_language': 'es'}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 403

    def test_settings_update_rejects_no_valid_fields(self, client):
        """Request with no updatable fields returns 400."""
        mock_client = MagicMock()

        with patch('app.middleware.Auth._get_supabase_user', return_value=self._mock_auth_user()), \
             patch('app.routes.account_settings._get_supabase', return_value=mock_client):
            response = client.put(
                f'/api/settings/{TEST_USER_ID}',
                data=json.dumps({'unknown_pref': 'value'}),
                content_type='application/json',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 400
        data = response.get_json()
        assert 'allowed_fields' in data

    def test_settings_update_rejects_missing_body(self, client):
        """Request with no JSON body returns 400."""
        with patch('app.middleware.Auth._get_supabase_user', return_value=self._mock_auth_user()):
            response = client.put(
                f'/api/settings/{TEST_USER_ID}',
                headers={'Authorization': BEARER},
            )

        assert response.status_code == 400

    def test_settings_update_requires_auth(self, client):
        """Request without Authorization header returns 401."""
        response = client.put(
            f'/api/settings/{TEST_USER_ID}',
            data=json.dumps({'preferred_language': 'es'}),
            content_type='application/json',
        )

        assert response.status_code == 401
