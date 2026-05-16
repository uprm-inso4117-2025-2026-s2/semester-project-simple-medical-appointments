"""
Exploratory Testing: Session -- Authentication & Role Permission Boundaries
Author: Carlos Pepin Delgado
Lecture applied: Exploratory Testing

SESSION CHARTER
---------------
Mission:  Probe the boundary between role assignment at registration and the
          requires_role permission gates to surface behaviors the scripted
          baseline does not reach.
Scope:    POST /api/auth/register (role field), requires_role (None role path),
          requires_auth (missing token path).
Time box: One focused session targeting three risk areas.

RISK AREAS
----------
RISK-A: No-role user hitting a protected route -- get_role_for_user returns
        None; None not in required_roles should fire 403.
RISK-B: Self-registration with role="admin" -- registration endpoint has no
        auth gate; "admin" was in VALID_ROLES before this session.
        Defect found and fixed: "admin" removed from VALID_ROLES in auth.py.
RISK-C: Missing Authorization header -- requires_auth must return 401 before
        requires_role is ever evaluated.

Run: cd backend && pytest tests/exploratory/test_exploratory_session.py -v -s
"""
import pytest
import jwt
from unittest.mock import patch


NO_ROLE_USER_ID = "eeeeeeee-0000-0000-0000-000000000005"


def _make_token(user_id, secret):
    token = jwt.encode({"sub": user_id}, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("ascii")


def test_risk_a_no_role_user_blocked_403(client, app):
    """RISK-A: requires_role returns 403 when get_role_for_user returns None."""
    token = _make_token(NO_ROLE_USER_ID, app.config["SUPABASE_JWT_SECRET"])
    headers = {"Authorization": f"Bearer {token}"}
    with patch("app.utils.custom_decorators.get_role_for_user", return_value=None):
        response = client.get("/api/admin/users", headers=headers)
    print(f"  ->GET /api/admin/users (no-role user)  HTTP {response.status_code}")
    assert response.status_code == 403


def test_risk_b_admin_self_registration_rejected_400(client):
    """RISK-B: After fix, POST /api/auth/register with role=admin returns 400."""
    payload = {
        "user_id": "attacker-uuid-001",
        "first_name": "Bad",
        "last_name": "Actor",
        "username": "badactor",
        "role": "admin",
    }
    response = client.post("/api/auth/register", json=payload)
    print(f"  ->POST /api/auth/register (role=admin)  HTTP {response.status_code}")
    assert response.status_code == 400


def test_risk_c_no_auth_header_returns_401(client):
    """RISK-C: Missing Authorization header returns 401 before role check fires."""
    response = client.get("/api/admin/users")
    print(f"  ->GET /api/admin/users (no auth header)  HTTP {response.status_code}")
    assert response.status_code == 401
