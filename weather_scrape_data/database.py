"""SQLite database helpers for weather snapshot data."""

import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DB_PATH = DATA_DIR / "weather.db"

CREATE_WEATHER_RAW_TABLE = """
CREATE TABLE IF NOT EXISTS weather_raw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_raw TEXT,
    local_time_raw TEXT,
    weather_condition_raw TEXT,
    temperature_raw TEXT,
    weather_url TEXT
)
"""

CREATE_WEATHER_CLEAN_TABLE = """
CREATE TABLE IF NOT EXISTS weather_clean (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL,
    is_capital INTEGER NOT NULL,
    country TEXT NOT NULL,
    local_time TEXT,
    day_of_week TEXT,
    time TEXT,
    weather_condition TEXT,
    temperature_f REAL,
    temperature_c REAL,
    weather_url TEXT,
    scraped_at TEXT NOT NULL
)
"""

CREATE_COUNTRY_SUMMARY_TABLE = """
CREATE TABLE IF NOT EXISTS country_temperature_summary (
    country TEXT PRIMARY KEY,
    avg_temp_f REAL NOT NULL,
    city_count INTEGER NOT NULL
)
"""


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a SQLite connection and ensure the schema exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    initialize_schema(connection)
    return connection


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create required tables if they do not already exist."""
    for statement in (
        CREATE_WEATHER_RAW_TABLE,
        CREATE_WEATHER_CLEAN_TABLE,
        CREATE_COUNTRY_SUMMARY_TABLE,
    ):
        connection.execute(statement)
    connection.commit()


def clear_tables(connection: sqlite3.Connection) -> None:
    """Remove existing rows before reloading CSV data."""
    connection.executescript(
        """
        DELETE FROM weather_raw;
        DELETE FROM weather_clean;
        DELETE FROM country_temperature_summary;
        """
    )
    connection.commit()


def load_csv_into_table(
    connection: sqlite3.Connection,
    csv_path: Path,
    table_name: str,
) -> int:
    """Import a CSV file into a SQLite table using pandas."""
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"No rows found in CSV file: {csv_path}")

    df.to_sql(table_name, connection, if_exists="append", index=False)
    return len(df)


def build_country_summary_table(connection: sqlite3.Connection) -> int:
    """Create grouped temperature summary using SQL aggregation."""
    connection.execute(
        """
        INSERT INTO country_temperature_summary (country, avg_temp_f, city_count)
        SELECT
            country,
            ROUND(AVG(temperature_f), 1) AS avg_temp_f,
            COUNT(*) AS city_count
        FROM weather_clean
        GROUP BY country
        ORDER BY avg_temp_f DESC
        """
    )
    connection.commit()
    cursor = connection.execute("SELECT COUNT(*) FROM country_temperature_summary")
    return int(cursor.fetchone()[0])


def count_rows(connection: sqlite3.Connection, table_name: str) -> int:
    """Return the number of rows in a table."""
    cursor = connection.execute(f"SELECT COUNT(*) FROM {table_name}")
    return int(cursor.fetchone()[0])
