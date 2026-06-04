"""Clean and transform raw weather scrape data into a structured DataFrame."""

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd

TEMPERATURE_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)")
LOCAL_TIME_PATTERN = re.compile(
    r"^(?P<day_of_week>[A-Za-z]{3})\s+(?P<time>\d{1,2}:\d{2}\s*[ap]m)$",
    re.IGNORECASE,
)


def slug_to_title(slug: str) -> str:
    """Convert a URL slug such as 'new-delhi' to 'New Delhi'."""
    return slug.replace("-", " ").title()


def parse_country_from_url(url: str) -> str:
    """Extract the country slug from a timeanddate weather URL."""
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "weather":
        return slug_to_title(parts[1])
    return ""


def parse_city_name(city_raw: str) -> tuple[str, bool]:
    """Return cleaned city name and whether it is marked as a capital."""
    is_capital = city_raw.endswith("*")
    city = city_raw.rstrip("*").strip()
    return city, is_capital


def parse_temperature(temp_raw: str) -> tuple[float | None, float | None]:
    """Parse Fahrenheit text and compute Celsius."""
    match = TEMPERATURE_PATTERN.search(temp_raw.replace("\ufffd", ""))
    if not match:
        return None, None

    temp_f = float(match.group(1))
    temp_c = round((temp_f - 32) * 5 / 9, 1)
    return temp_f, temp_c


def parse_local_time(local_time_raw: str) -> tuple[str, str, str]:
    """Split local time text into day of week and clock time."""
    normalized = " ".join(local_time_raw.split())
    match = LOCAL_TIME_PATTERN.match(normalized)
    if not match:
        return "", normalized, normalized

    day_of_week = match.group("day_of_week").title()
    clock_time = match.group("time").lower()
    return day_of_week, clock_time, normalized


def normalize_weather_condition(condition_raw: str) -> str:
    """Standardize weather condition text from image alt attributes."""
    condition = condition_raw.strip()
    if condition.endswith("."):
        condition = condition[:-1]
    return condition


def raw_records_to_dataframe(raw_records: list[dict[str, str]]) -> pd.DataFrame:
    """Load scraped records into a Pandas DataFrame."""
    return pd.DataFrame(raw_records)


def summarize_dataframe(df: pd.DataFrame, label: str) -> None:
    """Print shape, missing values, and a sample for a cleaning stage."""
    print(f"\n--- {label} ---")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    if df.empty:
        print("(empty)")
        return

    missing = df.isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        print("Missing values per column:")
        print(missing.to_string())
    else:
        print("Missing values: none")

    print("\nSample:")
    print(df.head(3).to_string(index=False))


def _transform_records(raw_df: pd.DataFrame, scraped_at: datetime) -> pd.DataFrame:
    """Apply parsing and column transformations to raw scrape fields."""
    cleaned_rows: list[dict[str, object]] = []

    for record in raw_df.to_dict(orient="records"):
        city, is_capital = parse_city_name(str(record.get("city_raw", "")))
        day_of_week, clock_time, local_time = parse_local_time(
            str(record.get("local_time_raw", ""))
        )
        temp_f, temp_c = parse_temperature(str(record.get("temperature_raw", "")))
        weather_url = str(record.get("weather_url", ""))

        cleaned_rows.append(
            {
                "city": city,
                "is_capital": is_capital,
                "country": parse_country_from_url(weather_url),
                "local_time": local_time,
                "day_of_week": day_of_week,
                "time": clock_time,
                "weather_condition": normalize_weather_condition(
                    str(record.get("weather_condition_raw", ""))
                ),
                "temperature_f": temp_f,
                "temperature_c": temp_c,
                "weather_url": weather_url,
                "scraped_at": scraped_at.isoformat(),
            }
        )

    return pd.DataFrame(cleaned_rows)


def clean_weather_data(
    raw_records: list[dict[str, str]] | pd.DataFrame,
    scraped_at: datetime | None = None,
    *,
    verbose: bool = True,
) -> pd.DataFrame:
    """Transform raw scrape records into a cleaned, analysis-ready DataFrame."""
    if scraped_at is None:
        scraped_at = datetime.now(timezone.utc)

    raw_df = (
        raw_records
        if isinstance(raw_records, pd.DataFrame)
        else raw_records_to_dataframe(raw_records)
    )

    if verbose:
        summarize_dataframe(raw_df, "BEFORE CLEANING (raw scrape)")

    transformed_df = _transform_records(raw_df, scraped_at)
    rows_after_transform = len(transformed_df)

    duplicate_mask = transformed_df.duplicated(
        subset=["city", "country", "weather_url"], keep="first"
    )
    duplicates_removed = int(duplicate_mask.sum())

    missing_required_mask = (
        transformed_df["city"].isna()
        | (transformed_df["city"].astype(str).str.strip() == "")
        | transformed_df["temperature_f"].isna()
    )
    rows_dropped_missing = int(missing_required_mask.sum())

    cleaned_df = transformed_df.drop_duplicates(
        subset=["city", "country", "weather_url"]
    )
    cleaned_df = cleaned_df.dropna(subset=["city", "temperature_f"])
    cleaned_df = cleaned_df[
        cleaned_df["city"].astype(str).str.strip() != ""
    ]
    cleaned_df = cleaned_df.sort_values(["country", "city"]).reset_index(drop=True)

    if verbose:
        summarize_dataframe(cleaned_df, "AFTER CLEANING")
        print("\n--- CLEANING SUMMARY ---")
        print(f"Raw rows scraped:        {len(raw_df)}")
        print(f"Rows after transform:    {rows_after_transform}")
        print(f"Duplicate rows removed:  {duplicates_removed}")
        print(f"Rows dropped (missing):  {rows_dropped_missing}")
        print(f"Final rows kept:         {len(cleaned_df)}")

        print("\n--- GROUPING: average temperature (F) by country ---")
        country_summary = (
            cleaned_df.groupby("country", dropna=False)["temperature_f"]
            .agg(avg_temp_f="mean", city_count="count")
            .round(1)
            .sort_values("avg_temp_f", ascending=False)
        )
        print(country_summary.head(10).to_string())

        print("\n--- FILTER: capital cities only (first 5) ---")
        capitals = cleaned_df[cleaned_df["is_capital"]].head(5)
        print(
            capitals[
                ["city", "country", "temperature_f", "weather_condition"]
            ].to_string(index=False)
        )

    return cleaned_df
