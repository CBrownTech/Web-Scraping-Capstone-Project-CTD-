"""Program 1: Scrape Weather Around The World, clean the data, and save to CSV."""

import argparse
from pathlib import Path

from cleaner import clean_weather_data, raw_records_to_dataframe
from scraper import scrape_weather

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_RAW_OUTPUT = DATA_DIR / "weather_raw.csv"
DEFAULT_CLEAN_OUTPUT = DATA_DIR / "weather.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scrape weather data from timeanddate.com, clean it, "
            "and save raw and cleaned CSV files."
        )
    )
    parser.add_argument(
        "--raw-output",
        type=Path,
        default=DEFAULT_RAW_OUTPUT,
        help=f"Path for the raw CSV file (default: {DEFAULT_RAW_OUTPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_CLEAN_OUTPUT,
        help=f"Path for the cleaned CSV file (default: {DEFAULT_CLEAN_OUTPUT})",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode (may be blocked by Cloudflare).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("Scraping weather data from timeanddate.com...")
    raw_records = scrape_weather(headless=args.headless)
    print(f"Retrieved {len(raw_records)} raw city records.")

    raw_df = raw_records_to_dataframe(raw_records)
    args.raw_output.parent.mkdir(parents=True, exist_ok=True)
    raw_df.to_csv(args.raw_output, index=False)
    print(f"Saved raw data to {args.raw_output}")

    print("\nCleaning and transforming data...")
    cleaned_df = clean_weather_data(raw_df, verbose=True)
    cleaned_df.to_csv(args.output, index=False)
    print(f"\nSaved cleaned data to {args.output}")


if __name__ == "__main__":
    main()
