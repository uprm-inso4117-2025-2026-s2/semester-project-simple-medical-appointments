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
