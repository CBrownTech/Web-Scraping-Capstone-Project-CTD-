"""Program 2: Load raw and cleaned weather CSV files into a SQLite database."""

import argparse
from pathlib import Path

from database import (
    DEFAULT_DB_PATH,
    build_country_summary_table,
    clear_tables,
    count_rows,
    get_connection,
    load_csv_into_table,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_RAW_CSV = DATA_DIR / "weather_raw.csv"
DEFAULT_CLEAN_CSV = DATA_DIR / "weather.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import each weather CSV file into a separate SQLite table "
            "and build a grouped summary table."
        )
    )
    parser.add_argument(
        "--raw-csv",
        type=Path,
        default=DEFAULT_RAW_CSV,
        help=f"Path to the raw CSV file (default: {DEFAULT_RAW_CSV})",
    )
    parser.add_argument(
        "--clean-csv",
        type=Path,
        default=DEFAULT_CLEAN_CSV,
        help=f"Path to the cleaned CSV file (default: {DEFAULT_CLEAN_CSV})",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to the SQLite database file (default: {DEFAULT_DB_PATH})",
    )
    return parser.parse_args()


def load_all_csv_files(raw_csv: Path, clean_csv: Path, db_path: Path) -> dict[str, int]:
    """Import raw and cleaned CSV files into separate tables."""
    for csv_path in (raw_csv, clean_csv):
        if not csv_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {csv_path}. Run scrape_weather.py first."
            )

    connection = get_connection(db_path)
    try:
        clear_tables(connection)

        raw_rows = load_csv_into_table(connection, raw_csv, "weather_raw")
        clean_rows = load_csv_into_table(connection, clean_csv, "weather_clean")
        summary_rows = build_country_summary_table(connection)

        return {
            "weather_raw": raw_rows,
            "weather_clean": clean_rows,
            "country_temperature_summary": summary_rows,
        }
    finally:
        connection.close()


def main() -> None:
    args = parse_args()

    print("Importing CSV files into SQLite...")
    print(f"  Raw CSV:    {args.raw_csv}")
    print(f"  Clean CSV:  {args.clean_csv}")
    print(f"  Database:   {args.db}")

    counts = load_all_csv_files(args.raw_csv, args.clean_csv, args.db)

    connection = get_connection(args.db)
    try:
        print("\n--- DATABASE LOAD SUMMARY ---")
        for table_name, inserted in counts.items():
            total = count_rows(connection, table_name)
            print(f"{table_name}: inserted {inserted}, total rows {total}")

        print("\n--- SQL GROUPING PREVIEW: top 5 countries by avg temp ---")
        rows = connection.execute(
            """
            SELECT country, avg_temp_f, city_count
            FROM country_temperature_summary
            ORDER BY avg_temp_f DESC
            LIMIT 5
            """
        ).fetchall()
        for row in rows:
            print(f"  {row['country']}: {row['avg_temp_f']} F ({row['city_count']} cities)")
    finally:
        connection.close()

    print(f"\nSaved database to {args.db}")


if __name__ == "__main__":
    main()
