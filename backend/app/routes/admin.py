"""
Admin user management endpoints.
All routes require an authenticated admin user.

Endpoints:
    GET    /api/admin/users                      -- list all users (paginated, filterable)
    PUT    /api/admin/users/<user_id>/role        -- update a user's role
    PUT    /api/admin/users/<user_id>/deactivate  -- ban a user account
    DELETE /api/admin/users/<user_id>             -- delete user from auth and DB
"""
import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import Blueprint, current_app, g, jsonify, request

from app.middleware.auth_middleware import requires_auth
from app.utils.custom_decorators import requires_role

admin_bp = Blueprint("admin", __name__)

VALID_ROLES = {"patient", "doctor", "admin"}


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _supabase_request(method, path, *, query=None, json_body=None, prefer=None):
    """Issue a request to the Supabase REST or Auth Admin API.

    Uses the service role key so it bypasses RLS.

    Args:
        method (str): HTTP method ('GET', 'POST', 'PUT', 'PATCH', 'DELETE').
        path (str): Path relative to SUPABASE_URL (e.g. '/rest/v1/users').
        query (dict | None): Query-string parameters.
        json_body (dict | None): Request body; sets Content-Type automatically.
        prefer (str | None): Value for the Supabase 'Prefer' header.

    Returns:
        tuple[int | None, object | None, str | None]:
            (http_status, parsed_response, transport_error_message)
    """
    base_url = (current_app.config.get("SUPABASE_URL") or "").rstrip("/")
    service_key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")

    if not base_url or not service_key:
        return None, None, "Supabase is not configured."

    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer

    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    req = Request(url=url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.status, None, None
            try:
                return resp.status, json.loads(raw), None
            except json.JSONDecodeError:
                return resp.status, raw, None
    except HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = raw or None
        return exc.code, parsed, None
    except (URLError, Exception) as exc:
        return None, None, f"Supabase request failed: {exc}"


# ---------------------------------------------------------------------------
# GET /api/admin/users
# ---------------------------------------------------------------------------

@admin_bp.route("/users", methods=["GET"])
@requires_auth
@requires_role({"admin"})
def list_users():
    """Return a paginated list of all users with their role and status.

    Query params:
        page     (int, default 1)   -- page number
        per_page (int, default 20, max 100)
        role     (str, optional)    -- filter by role: patient | doctor | admin
        status   (str, optional)    -- filter by status: active | inactive

    Returns 200 with:
        {
          "users": [...],
          "page": 1,
          "per_page": 20,
          "total": N
        }
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    role_filter = request.args.get("role")
    status_filter = request.args.get("status")

    if role_filter and role_filter not in VALID_ROLES:
        return jsonify({"error": f'Invalid role filter. Must be one of: {", ".join(sorted(VALID_ROLES))}'}), 400
    if status_filter and status_filter not in ("active", "inactive"):
        return jsonify({"error": 'Invalid status filter. Must be "active" or "inactive".'}), 400

    # Build user_id -> role_name map from user_roles + roles
    role_status, role_data, err = _supabase_request(
        "GET",
        "/rest/v1/user_roles",
        query={"select": "user_id,roles(name)"},
    )
    if err or role_status != 200:
        return jsonify({"error": "Failed to fetch user roles."}), 500

    role_map: dict[str, str] = {}
    for row in (role_data or []):
        uid = row.get("user_id")
        role_name = (row.get("roles") or {}).get("name")
        if uid and role_name:
            # Admin takes precedence if a user somehow has multiple roles.
            if uid not in role_map or role_name == "admin":
                role_map[uid] = role_name

    # Fetch users from Supabase Auth Admin API (paginated)
    auth_status, auth_data, err = _supabase_request(
        "GET",
        "/auth/v1/admin/users",
        query={"page": page, "per_page": per_page},
    )
    if err or auth_status != 200:
        return jsonify({"error": "Failed to fetch users from auth."}), 500

    raw_users = auth_data.get("users", []) if isinstance(auth_data, dict) else (auth_data or [])

    now = datetime.now(timezone.utc)
    result = []

    for user in raw_users:
        uid = user.get("id")
        role = role_map.get(uid)

        # Derive status from banned_until field set by deactivate endpoint.
        banned_until_str = user.get("banned_until")
        is_banned = False
        if banned_until_str:
            try:
                banned_dt = datetime.fromisoformat(banned_until_str.replace("Z", "+00:00"))
                is_banned = banned_dt > now
            except (ValueError, TypeError):
                pass
        status = "inactive" if is_banned else "active"

        if role_filter and role != role_filter:
            continue
        if status_filter and status != status_filter:
            continue

        result.append({
            "user_id": uid,
            "email": user.get("email"),
            "role": role,
            "status": status,
            "created_at": user.get("created_at"),
            "last_sign_in_at": user.get("last_sign_in_at"),
        })

    return jsonify({
        "users": result,
        "page": page,
        "per_page": per_page,
        "total": len(result),
    }), 200


# ---------------------------------------------------------------------------
# PUT /api/admin/users/<user_id>/role
# ---------------------------------------------------------------------------

@admin_bp.route("/users/<user_id>/role", methods=["PUT"])
@requires_auth
@requires_role({"admin"})
def update_user_role(user_id):
    """Update a user's application role.

    Request body (JSON):
        { "role": "patient" | "doctor" | "admin" }

    Replaces the user's existing role entirely.
    Records the acting admin as granted_by.

    Returns 200 with { user_id, role, message }.
    """
    data = request.get_json(silent=True)
    if not data or "role" not in data:
        return jsonify({"error": 'Request body must include "role".'}), 400

    new_role = data["role"]
    if new_role not in VALID_ROLES:
        return jsonify({"error": f'Invalid role. Must be one of: {", ".join(sorted(VALID_ROLES))}'}), 400

    # Resolve role name to role_id from the roles table.
    role_status, role_data, err = _supabase_request(
        "GET",
        "/rest/v1/roles",
        query={"name": f"eq.{new_role}", "select": "id"},
    )
    if err or role_status != 200 or not role_data:
        return jsonify({"error": f'Role "{new_role}" not found in the roles table.'}), 400

    role_id = role_data[0]["id"]

    # Remove all existing roles for this user, then insert the new one.
    # The composite PK (user_id, role_id) allows multiple roles per user,
    # but the system treats each user as having a single active role.
    del_status, _, err = _supabase_request(
        "DELETE",
        "/rest/v1/user_roles",
        query={"user_id": f"eq.{user_id}"},
        prefer="return=minimal",
    )
    if err or del_status not in (200, 204):
        return jsonify({"error": "Failed to remove existing role."}), 500

    ins_status, _, err = _supabase_request(
        "POST",
        "/rest/v1/user_roles",
        json_body={"user_id": user_id, "role_id": role_id, "granted_by": g.user_id},
        prefer="return=minimal",
    )
    if err or ins_status not in (200, 201):
        return jsonify({"error": "Failed to assign new role."}), 500

    return jsonify({"message": f'Role updated to "{new_role}".', "user_id": user_id, "role": new_role}), 200


# ---------------------------------------------------------------------------
# PUT /api/admin/users/<user_id>/deactivate
# ---------------------------------------------------------------------------

@admin_bp.route("/users/<user_id>/deactivate", methods=["PUT"])
@requires_auth
@requires_role({"admin"})
def deactivate_user(user_id):
    """Ban a user account so they cannot log in.

    Uses Supabase's ban_duration mechanism. A duration of '876600h' (~100 years)
    is used as an indefinite ban. The user remains in the database and their
    data is preserved; only authentication is blocked.

    Admins cannot deactivate their own account.

    Returns 200 with { user_id, message }.
    """
    if user_id == g.user_id:
        return jsonify({"error": "Admins cannot deactivate their own account."}), 400

    status, _, err = _supabase_request(
        "PUT",
        f"/auth/v1/admin/users/{user_id}",
        json_body={"ban_duration": "876600h"},
    )
    if err or status not in (200, 204):
        return jsonify({"error": "Failed to deactivate user."}), 500

    return jsonify({"message": "User deactivated successfully.", "user_id": user_id}), 200


# ---------------------------------------------------------------------------
# DELETE /api/admin/users/<user_id>
# ---------------------------------------------------------------------------

@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@requires_auth
@requires_role({"admin"})
def delete_user(user_id):
    """Permanently delete a user from both the application DB and Supabase Auth.

    Deletes records in dependency order to satisfy FK constraints:
      1. Doctor-linked rows (appointments, time_slots, availability_rules, waitlist)
         detected via providers.user_id; doctor_id in those tables equals user_id
      2. Patient-linked rows (appointments, waitlist by patient_id)
      3. Settings tables (patient_settings, provider_settings, profile_settings)
      4. Role table (user_roles)
      5. Profile-linked tables (patients, providers, profiles)
      6. Auth user (Supabase Auth Admin API)

    Admins cannot delete their own account.

    Returns 200 with { user_id, message }.
    """
    if user_id == g.user_id:
        return jsonify({"error": "Admins cannot delete their own account."}), 400

    def _delete(table, col, value):
        """Run a DELETE and return (ok, error_response, status)."""
        s, _, e = _supabase_request(
            "DELETE",
            f"/rest/v1/{table}",
            query={col: f"eq.{value}"},
            prefer="return=minimal",
        )
        if e or s not in (200, 204, 404):
            return False, jsonify({"error": f"Failed to delete from {table}."}), 500
        return True, None, None

    # Step 1: Doctor-linked rows (providers table stores doctor accounts; doctor_id
    # in related tables equals the provider's user_id in the current schema)
    prov_status, prov_data, _ = _supabase_request(
        "GET",
        "/rest/v1/providers",
        query={"user_id": f"eq.{user_id}", "select": "user_id"},
    )
    if prov_status == 200 and isinstance(prov_data, list) and prov_data:
        for table, col in [
            ("appointments", "doctor_id"),
            ("time_slots", "doctor_id"),
            ("availability_rules", "doctor_id"),
            ("waitlist", "doctor_id"),
        ]:
            ok, err_resp, err_status = _delete(table, col, user_id)
            if not ok:
                return err_resp, err_status

    # Step 2: Patient-linked rows (patient_id == auth user UUID)
    for table, col in [
        ("appointments", "patient_id"),
        ("waitlist", "patient_id"),
    ]:
        ok, err_resp, err_status = _delete(table, col, user_id)
        if not ok:
            return err_resp, err_status

    # Step 3: Settings and role tables
    for table, col in [
        ("patient_settings", "user_id"),
        ("provider_settings", "user_id"),
        ("user_roles", "user_id"),
        ("profile_settings", "user_id"),
    ]:
        ok, err_resp, err_status = _delete(table, col, user_id)
        if not ok:
            return err_resp, err_status

    # Step 4: Profile-linked tables (patients, providers reference profiles.user_id)
    for table, col in [
        ("patients", "user_id"),
        ("providers", "user_id"),
        ("profiles", "user_id"),
    ]:
        ok, err_resp, err_status = _delete(table, col, user_id)
        if not ok:
            return err_resp, err_status

    # Step 5: Delete the auth user
    auth_status, _, err = _supabase_request(
        "DELETE",
        f"/auth/v1/admin/users/{user_id}",
    )
    if err or auth_status not in (200, 204):
        return jsonify({"error": "Failed to delete user from auth."}), 500

    return jsonify({"message": "User deleted successfully.", "user_id": user_id}), 200
