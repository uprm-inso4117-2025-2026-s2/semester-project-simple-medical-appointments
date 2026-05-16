"""
Exploratory Testing: Session Log -- Authentication & Role Permission Boundaries
Author: Carlos Pepin Delgado
Lecture applied: Exploratory Testing

SESSION CHARTER
---------------
Mission:  Probe the boundary between role assignment at registration and the
          requires_role permission gates to surface behaviors that scripted
          tests do not reach.
Scope:    POST /api/auth/register (role field validation), requires_role
          decorator (None role path), requires_auth (missing token path).
Time box: One focused session targeting three risk areas.

The lecture defines session-based testing as time-boxed, charter-driven
exploration where the tester documents actions, observations, and findings
in a session log. Unlike scripted tests, session-based testing is not
following steps -- it is reasoning about what could go wrong and probing
those boundaries deliberately.

RISK AREAS AND SESSION LOG
--------------------------
RISK-A: No-role user hitting a protected route
  Rationale: get_role_for_user returns None for users with no DB row.
             None is not in any required_roles set, so the 403 branch
             should fire. If broken, every role-gated route is reachable
             without a valid role assignment.
  Finding:   Confirmed correct. requires_role returns 403 when the role
             is None. The check is implicit -- None not in {"admin"} is
             True -- so the guard fires without an explicit None check.

RISK-B: Self-registration with role="admin" via direct API call
  Rationale: VALID_ROLES in auth.py included "admin" before this session.
             Any unauthenticated caller could POST /api/auth/register with
             role="admin" and receive admin privileges without approval from
             an existing admin. The registration endpoint has no auth gate.
  Finding:   DEFECT FOUND. POST with role="admin" returned 201.
             This is a privilege escalation path -- severity: Critical.
  Fix:       "admin" removed from VALID_ROLES. Admins are assigned by
             existing admins via PUT /api/admin/users/:id/role, not by
             self-registration. After fix, POST with role="admin" returns 400.

RISK-C: Request to protected route with no Authorization header
  Rationale: The JWT middleware (requires_auth) must reject unauthenticated
             requests before requires_role is ever evaluated. If 401 is not
             returned here, the permission layer has no stable foundation.
  Finding:   Confirmed correct. extract_token() returns None for a missing
             Authorization header; requires_auth returns 401 immediately.

DEFECT REPORT
-------------
ID:           DEFECT-128-01
Summary:      Unauthenticated caller can self-assign admin role via registration
Preconditions: POST /api/auth/register is reachable without authentication.
               "admin" was present in VALID_ROLES in app/routes/auth.py.
Steps:         POST /api/auth/register with role="admin" and all required fields.
Expected:      HTTP 400 -- admin role cannot be self-assigned at registration.
Actual:        HTTP 201 -- admin role was accepted and would be stored in DB.
Severity:      Critical -- any unauthenticated user can escalate to admin.
Status:        Fixed. "admin" removed from VALID_ROLES in app/routes/auth.py.

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
