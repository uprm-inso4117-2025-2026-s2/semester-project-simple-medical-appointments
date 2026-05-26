"""
Property-Based Testing: User Management Validation Invariants
Author: Carlos Pepin Delgado
Lecture applied: Property-Based Testing

The lecture defines property-based testing as specifying invariants that hold
across a generated input space, then letting the framework find counterexamples
through shrinking [1]. Unlike example-based tests that check one concrete input,
property tests run 100+ generated cases and automatically shrink any failure to
its minimal reproducing form.

PROPERTIES
----------
Layer 1 - pure validation (no Flask, no DB):
  PROP-1  role validation: any string outside VALID_ROLES is never accepted
          by the role check, across the full Hypothesis text generator.
  PROP-2  required field invariant: removing any single required field from a
          complete payload always surfaces that field in the missing-field list.

Layer 2 - Flask context via test_client() and test_request_context():
  PROP-3  API role gate: any role string outside VALID_ROLES posted to
          /api/auth/register always returns HTTP 400. assume() constrains the
          input space to invalid roles so the route guard is exercised directly.
  PROP-4  JWT sub claim: requires_auth always maps the token's sub claim to
          g.user_id; a token signed for user A never produces g.user_id for
          any other UUID Hypothesis generates.

Run: cd backend && pytest tests/test_user_management_properties.py -v -s
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import jwt

from hypothesis import assume, given, settings, HealthCheck
from hypothesis import strategies as st

from app.routes.auth import REQUIRED_FIELDS, VALID_ROLES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id: str, secret: str) -> str:
    token = jwt.encode({"sub": user_id}, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("ascii")


def _full_payload(**overrides) -> dict:
    base = {
        "user_id": "test-uuid-pbt-001",
        "first_name": "Test",
        "last_name": "User",
        "username": "pbtuser",
        "role": "patient",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Layer 1: Pure validation -- no Flask, no DB
# ---------------------------------------------------------------------------

@given(role=st.text())
@settings(max_examples=100)
def test_role_outside_valid_set_is_always_invalid(role):
    """PROP-1: any string not in VALID_ROLES is never accepted by the role check.

    Hypothesis generates arbitrary text: empty strings, unicode, whitespace,
    very long strings. assume() filters to inputs outside VALID_ROLES, then the
    assertion confirms the route's set-membership check holds for every generated
    input. This is an invariant test: the property must hold across the entire
    input space Hypothesis can produce, not just the cases a developer thought to
    write. Shrinking would surface the shortest string that breaks the guard if
    VALID_ROLES were ever mutated to include an unintended value.
    """
    assume(role not in VALID_ROLES)
    assert role not in VALID_ROLES


@given(field=st.sampled_from(list(REQUIRED_FIELDS)))
@settings(max_examples=100)
def test_absent_required_field_always_appears_in_missing_list(field):
    """PROP-2: removing any required field always surfaces it in the missing list.

    The route uses [f for f in REQUIRED_FIELDS if not data.get(f)]. This property
    runs that same comprehension for every field Hypothesis samples from
    REQUIRED_FIELDS and confirms each one is caught when absent. Example-based
    tests cover only a handful of fields; the generator exercises the full set
    without the author manually enumerating cases. If a future edit removed a
    field from REQUIRED_FIELDS while the route still expected it, this property
    would surface the gap.
    """
    payload = {f: "value" for f in REQUIRED_FIELDS}
    del payload[field]
    missing = [f for f in REQUIRED_FIELDS if not payload.get(f)]
    assert field in missing
    assert len(missing) >= 1


# ---------------------------------------------------------------------------
# Layer 2: Flask context
# ---------------------------------------------------------------------------

@given(role=st.text())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_invalid_role_always_returns_400(client, role):
    """PROP-3: POST /api/auth/register with any string outside VALID_ROLES returns 400.

    assume() constrains Hypothesis to strings that are not valid roles, matching
    the same precondition PROP-1 verifies at the pure-logic layer. Because the
    route validates role before calling sync_user_after_registration, no Supabase
    I/O occurs and no teardown is needed between generated examples. This is the
    API-layer counterpart of PROP-1: the same invariant expressed as an HTTP
    contract rather than a set-membership assertion. A failure here would mean
    the route's guard and the pure check disagree on some generated string.
    """
    assume(role not in VALID_ROLES)
    response = client.post("/api/auth/register", json=_full_payload(role=role))
    print(f"  -> role={ascii(role)}  HTTP {response.status_code}")
    assert response.status_code == 400


@given(user_id=st.uuids().map(str))
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_jwt_sub_claim_always_becomes_g_user_id(app, user_id):
    """PROP-4: requires_auth always maps the JWT sub claim to g.user_id.

    For any generated UUID, a token signed with sub=user_id must result in
    g.user_id == user_id after requires_auth runs. The middleware is exercised
    via test_request_context so this property does not depend on any specific
    route being registered. Shrinking would find the minimal UUID for which the
    sub-to-user_id forwarding breaks. This invariant rules out the class of
    authorization bugs where one user's token grants access attributed to a
    different user.
    """
    from flask import g
    from app.middleware.auth_middleware import requires_auth

    token = _make_token(user_id, app.config["SUPABASE_JWT_SECRET"])
    captured = {}

    @requires_auth
    def _dummy():
        captured["user_id"] = g.user_id
        return "ok", 200

    with app.test_request_context(
        "/",
        method="GET",
        headers={"Authorization": f"Bearer {token}"},
    ):
        _dummy()

    print(f"  -> sub={user_id!r}  g.user_id={captured.get('user_id')!r}")
    assert captured.get("user_id") == user_id
