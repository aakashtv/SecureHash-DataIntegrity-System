import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "db.sqlite3"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _parse_created_at(created_at):
    if not created_at:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(created_at, fmt)
        except ValueError:
            continue

    return None


def _table_exists(connection, table_name):
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _compute_geo_variance(connection, key_id, last_location):
    if _table_exists(connection, "telemetry_events"):
        distinct_count = connection.execute(
            """
            SELECT COUNT(DISTINCT location) AS location_count
            FROM telemetry_events
            WHERE key_id = ?
            """,
            (key_id,),
        ).fetchone()["location_count"]

        if distinct_count > 1:
            return 2
        if distinct_count == 1:
            return 1

    return 1 if last_location else 0


def extract_features(key_id):
    with get_connection() as connection:
        key_row = connection.execute(
            """
            SELECT id, usage_count, last_location, anomaly_flag, algorithm, created_at
            FROM keys
            WHERE id = ?
            """,
            (key_id,),
        ).fetchone()

        if key_row is None:
            raise ValueError(f"Key with id {key_id} was not found.")

        created_at = _parse_created_at(key_row["created_at"])
        key_age = 0
        if created_at is not None:
            key_age = (datetime.now() - created_at).days

        features = {
            "key_id": key_row["id"],
            "usage_rate": key_row["usage_count"],
            "geo_variance": _compute_geo_variance(
                connection, key_row["id"], key_row["last_location"]
            ),
            "key_age": key_age,
            "anomaly_flag": int(bool(key_row["anomaly_flag"])),
            "algo_strength": 0 if key_row["algorithm"] == "RSA-1024" else 1,
        }

    return features
