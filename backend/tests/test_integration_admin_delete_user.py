import pytest
from unittest.mock import patch

ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"
TARGET_USER_ID = "bbbbbbbb-0000-0000-0000-000000000002"


def _mock_supabase_delete_success(method, path, *, query=None, json_body=None, user_token=None, prefer=None):
    if method == "GET" and path == "/rest/v1/doctors":
        return 200, [], None
    if method == "DELETE" and path.startswith("/rest/v1/"):
        return 204, None, None
    if method == "DELETE" and path == f"/auth/v1/admin/users/{TARGET_USER_ID}":
        return 204, None, None
    return 200, None, None


def _mock_supabase_delete_server_failure(method, path, *, query=None, json_body=None, user_token=None, prefer=None):
    if method == "GET" and path == "/rest/v1/doctors":
        return 200, [], None
    if method == "DELETE" and path == "/rest/v1/profiles":
        return 500, None, None
    if method == "DELETE" and path.startswith("/rest/v1/"):
        return 204, None, None
    if method == "DELETE" and path == f"/auth/v1/admin/users/{TARGET_USER_ID}":
        return 204, None, None
    return 200, None, None


class TestAdminDeleteUser:

    def test_admin_can_delete_another_user(self, client, auth_headers):
        with patch('app.routes.admin._supabase_request', side_effect=_mock_supabase_delete_success), \
             patch('app.utils.custom_decorators.get_role_for_user', return_value='admin'):
            response = client.delete(
                f'/api/admin/users/{TARGET_USER_ID}',
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert response.get_json() == {
            'message': 'User deleted successfully.',
            'user_id': TARGET_USER_ID,
        }

    def test_admin_cannot_delete_their_own_account(self, client, auth_headers):
        with patch('app.routes.admin._supabase_request', side_effect=_mock_supabase_delete_success), \
             patch('app.utils.custom_decorators.get_role_for_user', return_value='admin'):
            response = client.delete(
                f'/api/admin/users/{ADMIN_USER_ID}',
                headers=auth_headers,
            )

        assert response.status_code == 400
        assert response.get_json().get('error') == 'Admins cannot delete their own account.'

    def test_non_admin_cannot_access_delete_route(self, client, auth_headers):
        with patch('app.routes.admin._supabase_request', side_effect=_mock_supabase_delete_success), \
             patch('app.utils.custom_decorators.get_role_for_user', return_value='patient'):
            response = client.delete(
                f'/api/admin/users/{TARGET_USER_ID}',
                headers=auth_headers,
            )

        assert response.status_code == 403

    def test_delete_route_returns_500_on_supabase_failure(self, client, auth_headers):
        with patch('app.routes.admin._supabase_request', side_effect=_mock_supabase_delete_server_failure), \
             patch('app.utils.custom_decorators.get_role_for_user', return_value='admin'):
            response = client.delete(
                f'/api/admin/users/{TARGET_USER_ID}',
                headers=auth_headers,
            )

        assert response.status_code == 500
        assert response.get_json().get('error') == 'Failed to delete from profiles.'
