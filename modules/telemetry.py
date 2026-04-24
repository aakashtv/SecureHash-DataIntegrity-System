import random
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "db.sqlite3"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_telemetry_columns():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        existing_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(keys)").fetchall()
        }

        column_definitions = {
            "last_location": "TEXT",
            "last_operation": "TEXT",
            "anomaly_flag": "BOOLEAN NOT NULL DEFAULT 0",
        }

        for column_name, column_type in column_definitions.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE keys ADD COLUMN {column_name} {column_type}"
                )

        connection.commit()


def simulate_normal_usage(key_id):
    ensure_telemetry_columns()
    usage_increment = random.randint(1, 5)

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE keys
            SET usage_count = usage_count + ?,
                last_location = ?,
                last_operation = ?,
                anomaly_flag = ?
            WHERE id = ?
            """,
            (usage_increment, "India", "encrypt", 0, key_id),
        )
        connection.commit()


def simulate_attack(key_id):
    ensure_telemetry_columns()
    usage_increment = random.randint(10, 30)
    location = random.choice(["India", "USA", "Russia"])
    operation = random.choice(["encrypt", "decrypt", "export"])

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE keys
            SET usage_count = usage_count + ?,
                last_location = ?,
                last_operation = ?,
                anomaly_flag = ?
            WHERE id = ?
            """,
            (usage_increment, location, operation, 1, key_id),
        )
        connection.commit()
