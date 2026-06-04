"""Program 1: Scrape Weather Around The World, clean the data, and save to CSV."""

import argparse
from pathlib import Path

from cleaner import clean_weather_data
from scraper import scrape_weather

# CSV files live in weather_scrape_data/data/
DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_OUTPUT = DATA_DIR / "weather.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scrape weather data from timeanddate.com, clean it, "
            "and save the results to a CSV file."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path for the cleaned CSV file (default: {DEFAULT_OUTPUT})",
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

    print("Cleaning and transforming data...")
    cleaned_df = clean_weather_data(raw_records)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    cleaned_df.to_csv(args.output, index=False)

    print(f"Saved {len(cleaned_df)} cleaned records to {args.output}")
    print("\nSample rows:")
    print(cleaned_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
