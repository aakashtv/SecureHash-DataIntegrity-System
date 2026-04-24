import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "db.sqlite3"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'active',
                usage_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.commit()


def create_key(key_name, algorithm):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO keys (key_name, algorithm)
            VALUES (?, ?)
            """,
            (key_name.strip(), algorithm.strip()),
        )
        connection.commit()


def get_all_keys():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                key_name,
                algorithm,
                created_at,
                status,
                usage_count,
                last_location,
                last_operation,
                anomaly_flag
            FROM keys
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
    return rows
