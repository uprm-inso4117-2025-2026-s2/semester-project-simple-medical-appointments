"""
Flask test server for performance / load testing.

Why this exists
---------------
The production ``auth_middleware.verify_jwt`` fetches the Supabase JWKS
endpoint and verifies tokens with ES256 (asymmetric).  Locust needs to forge
tokens locally, so this script patches that function to accept HS256 tokens
signed with the project's own SUPABASE_JWT_SECRET — the same symmetric secret
Supabase uses internally and that is stored in backend/.env.

All Supabase database calls (availability rules, doctors, provider_settings)
go to the REAL Supabase project, so measured response times include actual
network latency and query execution time.

Usage (from the backend/ directory)
-------------------------------------
    venv/Scripts/python tests/performance/test_server.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Load the real backend/.env BEFORE any app imports so Config sees the values.
# ---------------------------------------------------------------------------
_BACKEND = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_BACKEND / ".env")

# Force off debug mode and reloader for stable load-test measurements.
os.environ["FLASK_DEBUG"] = "0"

# The symmetric secret stored in the Supabase project settings (JWT Secret).
# We use it to sign HS256 tokens that Flask will accept after the patch below.
PERF_JWT_SECRET: str = os.environ["SUPABASE_JWT_SECRET"]

# ---------------------------------------------------------------------------
# Patch JWT verification BEFORE importing the app.
# Replaces the JWKS-based ES256 verifier with a local HS256 check using the
# real project secret, so no live Supabase auth call is needed per request.
# ---------------------------------------------------------------------------
import jwt as _pyjwt  # noqa: E402
from app.middleware import auth_middleware as _auth_mw  # noqa: E402


def _hs256_verify(token: str) -> dict | None:
    """Accept HS256 tokens signed with the real SUPABASE_JWT_SECRET."""
    try:
        return _pyjwt.decode(
            token,
            PERF_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except _pyjwt.PyJWTError:
        return None


_auth_mw.verify_jwt = _hs256_verify

# ---------------------------------------------------------------------------
# Create and run the app (uses real Supabase URL + service role key from .env).
# ---------------------------------------------------------------------------
from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PERF_SERVER_PORT", "5001"))
    print(f"[perf-server] Listening on  http://localhost:{port}")
    print(f"[perf-server] Supabase URL : {os.environ.get('SUPABASE_URL')}")
    print("[perf-server] JWT mode     : HS256 (patched — real SUPABASE_JWT_SECRET)")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
