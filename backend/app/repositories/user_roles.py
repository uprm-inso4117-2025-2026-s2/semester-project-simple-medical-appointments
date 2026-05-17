"""
user_roles repository -- fetch a user's application role from Supabase.

Uses the service role key (bypasses RLS) so the backend can always resolve
the role regardless of the calling user's permissions.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from flask import current_app


def get_role_for_user(user_id: str) -> str | None:
    """Return the application role name for a given Supabase user UUID.

    Queries the public.user_roles table joined to public.roles.
    If a user has the 'admin' role it is always returned preferentially;
    otherwise the first role found is returned.

    Args:
        user_id (str): Supabase auth UUID (the JWT 'sub' claim).

    Returns:
        str | None: Role name ('admin', 'doctor', 'patient'), or None if the
        user has no role or Supabase is unreachable/misconfigured.
    """
    base_url = (current_app.config.get("SUPABASE_URL") or "").rstrip("/")
    service_key = current_app.config.get("SUPABASE_SERVICE_ROLE_KEY")

    if not base_url or not service_key:
        return None

    query = urlencode({"user_id": f"eq.{user_id}", "select": "roles(name)"})
    url = f"{base_url}/rest/v1/user_roles?{query}"

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
    }

    req = Request(url=url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        return None

    if not isinstance(data, list) or not data:
        return None

    role_names = [
        (row.get("roles") or {}).get("name")
        for row in data
        if isinstance(row, dict)
    ]
    role_names = [name for name in role_names if name]

    if not role_names:
        return None

    # Admin takes precedence when a user somehow has multiple roles.
    return "admin" if "admin" in role_names else role_names[0]
