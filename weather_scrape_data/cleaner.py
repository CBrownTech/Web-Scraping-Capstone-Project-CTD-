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


def clean_weather_data(
    raw_records: list[dict[str, str]],
    scraped_at: datetime | None = None,
) -> pd.DataFrame:
    """Transform raw scrape records into a cleaned, analysis-ready DataFrame."""
    if scraped_at is None:
        scraped_at = datetime.now(timezone.utc)

    cleaned_rows: list[dict[str, object]] = []

    for record in raw_records:
        city, is_capital = parse_city_name(record.get("city_raw", ""))
        day_of_week, clock_time, local_time = parse_local_time(
            record.get("local_time_raw", "")
        )
        temp_f, temp_c = parse_temperature(record.get("temperature_raw", ""))
        weather_url = record.get("weather_url", "")

        cleaned_rows.append(
            {
                "city": city,
                "is_capital": is_capital,
                "country": parse_country_from_url(weather_url),
                "local_time": local_time,
                "day_of_week": day_of_week,
                "time": clock_time,
                "weather_condition": normalize_weather_condition(
                    record.get("weather_condition_raw", "")
                ),
                "temperature_f": temp_f,
                "temperature_c": temp_c,
                "weather_url": weather_url,
                "scraped_at": scraped_at.isoformat(),
            }
        )

    df = pd.DataFrame(cleaned_rows)
    df = df.drop_duplicates(subset=["city", "country", "weather_url"])
    df = df.dropna(subset=["city", "temperature_f"])
    df = df.sort_values(["country", "city"]).reset_index(drop=True)
    return df
