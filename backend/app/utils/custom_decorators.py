from functools import wraps
from flask import g, jsonify
from app.repositories.user_roles import get_role_for_user


def requires_role(required_roles: set[str]):
    """Decorator that restricts a route to users with one of the required roles.

    Must be applied after @requires_auth, which sets g.user_id.
    Fetches the user's role from Supabase and returns 403 if it is not in
    the required set.

    Example usage:
        @requires_auth
        @requires_role({"admin"})
        def admin_only_view(): ...

        @requires_auth
        @requires_role({"admin", "doctor"})
        def admin_or_doctor_view(): ...

    Args:
        required_roles (set[str]): Set of role names that are allowed access.

    Returns 401 if g.user_id is not set (requires_auth not applied).
    Returns 403 if the user's role is not in required_roles.
    Sets g.user_role to the resolved role string on success.
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = getattr(g, "user_id", None)
            if not user_id:
                return jsonify({"message": "Not authenticated"}), 401

            role = get_role_for_user(user_id)
            if role not in required_roles:
                return jsonify({"message": "Forbidden"}), 403

            g.user_role = role
            return f(*args, **kwargs)

        return wrapper

    return decorator
