#!/usr/bin/env python3
"""
debug_auth_session.py
=====================
Debugging Session: User Management — Authentication & Role-Check Flow

Instruments 5 key execution points in the auth middleware and role-check flow:
  BP1       extract_token()          — pull raw token from Authorization header
  BP2       verify_jwt()             — decode and validate JWT signature / expiry
  BP3       read_claims()            — extract the 'sub' claim  →  g.user_id
  BP4       get_role_for_user()      — resolve application role from DB
  BP5       requires_role() gate     — final allow / deny decision

Conditional breakpoints:
  BP2-COND  fires when the token is structurally malformed (dot-count != 2)
  BP5-COND  fires when the resolved role is NOT in the required set

Watchpoint:
  Tracks  token  →  jwt_payload  →  user_id  →  resolved_role
  across all five steps so state evolution is visible end-to-end.

Run from the backend/ directory:
    python tests/debug_auth_session.py
"""

import os
import sys
import time

import jwt as pyjwt

# ---------------------------------------------------------------------------
# Path setup — must come before any app imports
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.environ.setdefault("SUPABASE_URL", "http://test-supabase")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("SECRET_KEY", "debug-session-secret-key")
os.environ.setdefault("FLASK_DEBUG", "0")

from tests.conftest import TEST_JWT_SECRET

# ---------------------------------------------------------------------------
# Debugger infrastructure
# ---------------------------------------------------------------------------

_breakpoints_hit: list[dict] = []
_watchpoint_log:  dict[str, list[dict]] = {}


def _bp(label: str, state: dict, condition_desc: str | None = None) -> None:
    """Record and print a breakpoint hit."""
    _breakpoints_hit.append({"label": label, "state": state, "condition": condition_desc})

    print(f"\n{'─' * 68}")
    tag = "CONDITIONAL BREAKPOINT" if condition_desc else "BREAKPOINT"
    print(f"  [{tag}]  {label}")
    if condition_desc:
        print(f"  Condition : {condition_desc}  ← triggered")
    print("  State :")
    for k, v in state.items():
        raw = repr(v)
        print(f"    {k:<32} = {raw[:80]}{'…' if len(raw) > 80 else ''}")
    print(f"{'─' * 68}")


def _watch(var: str, value, step: str) -> None:
    """Append a watchpoint observation for var at the named step."""
    _watchpoint_log.setdefault(var, []).append({"step": step, "value": repr(value)})
    truncated = repr(value)
    if len(truncated) > 70:
        truncated = truncated[:70] + "…"
    print(f"    [WATCH]  {var:<18} @ {step:<36} → {truncated}")


# ---------------------------------------------------------------------------
# Test tokens  (same secret used by conftest.py)
# ---------------------------------------------------------------------------
ADMIN_ID   = "00000000-0000-0000-0000-000000000001"
PATIENT_ID = "aaaaaaaa-0000-0000-0000-000000000002"


def _token(user_id: str, offset: int = 3600) -> str:
    return pyjwt.encode(
        {"sub": user_id, "exp": int(time.time()) + offset, "role": "authenticated"},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )


VALID_ADMIN_TOKEN   = _token(ADMIN_ID)
VALID_PATIENT_TOKEN = _token(PATIENT_ID)
EXPIRED_TOKEN       = _token(ADMIN_ID, offset=-3600)
MALFORMED_TOKEN     = "thisisnotavalidjwttoken"

# ---------------------------------------------------------------------------
# Instrumented auth-flow functions
# ---------------------------------------------------------------------------

def step_extract_token(auth_header: str | None) -> str | None:
    """BP1 — mirrors extract_token() in app/middleware/auth_middleware.py."""
    has_header = auth_header is not None
    has_bearer = bool(auth_header and auth_header.startswith("Bearer "))
    token      = auth_header.split(" ")[1] if has_bearer else None

    _bp(
        "BP1 · extract_token()",
        {
            "auth_header":          auth_header,
            "header_present":       has_header,
            "starts_with_Bearer":   has_bearer,
            "token_extracted":      token,
            "token_is_None":        token is None,
        },
    )
    _watch("token", token, "BP1 · extract_token")
    return token


def step_verify_jwt(token: str | None) -> dict | None:
    """BP2 — mirrors verify_jwt() in app/middleware/auth_middleware.py.
    Uses HS256 + TEST_JWT_SECRET instead of the production ES256/JWKS path.
    """
    payload    = None
    error_type = None

    # ── Conditional breakpoint: structurally malformed token ─────────────────
    if token is not None:
        dot_count = token.count(".")
        if dot_count != 2:
            _bp(
                "BP2-COND · verify_jwt() — malformed token detected",
                {
                    "token":          token,
                    "dot_count":      dot_count,
                    "expected_parts": 3,
                    "outcome":        "DecodeError will be raised",
                },
                condition_desc="token.count('.') != 2",
            )

        try:
            payload = pyjwt.decode(
                token,
                TEST_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except pyjwt.ExpiredSignatureError:
            error_type = "ExpiredSignatureError"
        except Exception as exc:
            error_type = type(exc).__name__

    _bp(
        "BP2 · verify_jwt() — result",
        {
            "token_present": token is not None,
            "payload":       payload,
            "error_type":    error_type,
            "auth_passes":   payload is not None,
        },
    )
    _watch("jwt_payload", payload, "BP2 · verify_jwt")
    return payload


def step_read_claims(payload: dict | None) -> str | None:
    """BP3 — mirrors the claim-reading block inside the requires_auth wrapper."""
    user_id  = payload.get("sub")  if payload else None
    exp      = payload.get("exp")  if payload else None
    role_jwt = payload.get("role") if payload else None

    _bp(
        "BP3 · requires_auth — read 'sub' claim → g.user_id",
        {
            "payload":        payload,
            "sub_claim":      user_id,
            "exp_claim":      exp,
            "role_jwt_claim": role_jwt,
            "g.user_id_set":  user_id is not None,
        },
    )
    _watch("jwt_payload", payload, "BP3 · read_claims")
    _watch("user_id",     user_id, "BP3 · sub extraction")
    return user_id


def step_get_role(user_id: str | None, role_map: dict) -> str | None:
    """BP4 — mirrors get_role_for_user() in app/repositories/user_roles.py.
    role_map substitutes the live Supabase REST call.
    """
    role = role_map.get(user_id) if user_id else None

    _watch("user_id", user_id, "BP4 · get_role_for_user")
    _bp(
        "BP4 · get_role_for_user() — DB lookup result",
        {
            "user_id":    user_id,
            "role":       role,
            "role_found": role is not None,
        },
    )
    _watch("resolved_role", role, "BP4 · role resolved")
    return role


def step_requires_role(role: str | None, required: set) -> bool:
    """BP5 — mirrors the gate inside requires_role() in app/utils/custom_decorators.py."""
    allowed = role in required

    # ── Conditional breakpoint: access will be denied ─────────────────────────
    if not allowed:
        _bp(
            "BP5-COND · requires_role() — access denied",
            {
                "resolved_role":  role,
                "required_roles": required,
                "access_granted": False,
                "http_response":  "403 Forbidden",
            },
            condition_desc="role not in required_roles",
        )

    _bp(
        "BP5 · requires_role() — final decision",
        {
            "resolved_role":  role,
            "required_roles": required,
            "access_granted": allowed,
            "http_response":  "200 → handler executes" if allowed else "403 Forbidden",
        },
    )
    _watch("resolved_role", role, "BP5 · authorization gate")
    return allowed


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

def run_scenario(
    name: str,
    auth_header: str | None,
    role_map: dict,
    required: frozenset = frozenset({"admin"}),
) -> str:
    print(f"\n{'═' * 68}")
    print(f"  SCENARIO {name}")
    print(f"{'═' * 68}")

    token = step_extract_token(auth_header)
    if token is None:
        result = "HTTP 401 — No token provided"
        print(f"\n  ↳ HALTED at BP1 — {result}")
        return result

    payload = step_verify_jwt(token)
    if payload is None:
        result = "HTTP 401 — Invalid or expired token"
        print(f"\n  ↳ HALTED at BP2 — {result}")
        return result

    user_id = step_read_claims(payload)
    role    = step_get_role(user_id, role_map)
    allowed = step_requires_role(role, required)

    result = "HTTP 200 — handler executes" if allowed else "HTTP 403 — Forbidden"
    print(f"\n  ↳ FINAL RESULT: {result}")
    return result


# ---------------------------------------------------------------------------
# Main session
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "█" * 68)
    print("  DEBUGGING SESSION")
    print("  Module  : User Management — Authentication & Role-Check Flow")
    print("  Author  : Viviana Ramos")
    print("  Date    : 2026-05-23")
    print("  Targets : extract_token · verify_jwt · read_claims ·")
    print("            get_role_for_user · requires_role")
    print("█" * 68)

    _role_map = {
        ADMIN_ID:   "admin",
        PATIENT_ID: "patient",
    }

    results: dict[str, str] = {}

    results["A"] = run_scenario(
        "A — Valid admin token on admin-only endpoint (happy path)",
        auth_header=f"Bearer {VALID_ADMIN_TOKEN}",
        role_map=_role_map,
    )

    results["B"] = run_scenario(
        "B — No Authorization header (missing token)",
        auth_header=None,
        role_map=_role_map,
    )

    results["C"] = run_scenario(
        "C — Malformed token  [triggers BP2-COND]",
        auth_header=f"Bearer {MALFORMED_TOKEN}",
        role_map=_role_map,
    )

    results["D"] = run_scenario(
        "D — Expired token (ExpiredSignatureError path)",
        auth_header=f"Bearer {EXPIRED_TOKEN}",
        role_map=_role_map,
    )

    results["E"] = run_scenario(
        "E — Valid patient token on admin-only endpoint  [triggers BP5-COND]",
        auth_header=f"Bearer {VALID_PATIENT_TOKEN}",
        role_map=_role_map,
    )

    # ── Watchpoint history ────────────────────────────────────────────────────
    print(f"\n{'═' * 68}")
    print("  WATCHPOINT HISTORY — state evolution across all execution steps")
    print(f"{'═' * 68}")
    for var, history in _watchpoint_log.items():
        print(f"\n  ▸ {var}")
        for entry in history:
            val = entry["value"]
            if len(val) > 60:
                val = val[:60] + "…"
            print(f"      [{entry['step']:<42}]  {val}")

    # ── Session summary ───────────────────────────────────────────────────────
    print(f"\n{'═' * 68}")
    print("  SESSION SUMMARY")
    print(f"{'═' * 68}")
    cond_hits = sum(1 for b in _breakpoints_hit if b["condition"] is not None)
    print(f"  Total breakpoints hit       : {len(_breakpoints_hit)}")
    print(f"  Conditional breakpoints hit : {cond_hits}")
    print(f"  Scenarios executed          : {len(results)}")
    print()
    for k, v in results.items():
        print(f"  Scenario {k}  →  {v}")
    print()
