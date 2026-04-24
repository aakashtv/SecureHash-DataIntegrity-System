import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "db.sqlite3"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def rotate_key(key_id):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE keys
            SET usage_count = 0,
                status = 'active'
            WHERE id = ?
            """,
            (key_id,),
        )
        connection.commit()


def restrict_key(key_id):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE keys
            SET status = 'restricted'
            WHERE id = ?
            """,
            (key_id,),
        )
        connection.commit()


def revoke_key(key_id):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE keys
            SET status = 'revoked'
            WHERE id = ?
            """,
            (key_id,),
        )
        connection.commit()


def execute_action(key_id, action):
    if action == "rotate":
        rotate_key(key_id)
    elif action == "restrict":
        restrict_key(key_id)
    elif action == "revoke":
        revoke_key(key_id)


def get_key_status(key_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT status
            FROM keys
            WHERE id = ?
            """,
            (key_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"Key with id {key_id} was not found.")

    return row["status"]
