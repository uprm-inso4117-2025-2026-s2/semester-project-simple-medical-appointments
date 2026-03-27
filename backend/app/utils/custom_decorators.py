from functools import wraps
import sqlite3


def get_user_roles(user_id: int, db: sqlite3.Connection) -> set[str]:
    """ Returns the roles of a user

    Args:
        user_id (int): user id
        db (sqlite3.Connection): database connection

    Returns:
        set[str]: set of roles
    """
    cursor = db.cursor()
    query = """
            SELECT roles.name FROM user_roles
            JOIN roles ON user_roles.role_id = roles.id
            WHERE user_roles.user_id = ?
            """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()

    role_names = {row[0] for row in rows}
    return role_names


def requires_role(required_roles: set[str], db: sqlite3.Connection):
    """Decorator to check if the user has the required roles

    Example usage:
    @requires_role({"admin"}, database_connection)
    @requires_role({"admin", "doctor", ...}, database_connection)

    This will check if the user has at least one of the required roles.

    Args:
        required_roles (set[str]): set of required roles
        db (sqlite3.Connection): database connection
    """
    def decorator(f):
        @wraps(f)
        def wrapper(user_id: int, *args, **kwargs):
            user_roles = get_user_roles(user_id, db)
            if not (user_roles & required_roles):
                return "Unauthorized", 401

            return f(user_id, *args, **kwargs)

        return wrapper

    return decorator
