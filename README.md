# Web Scraping Capstone Project (Code The Dream)

Capstone project for scraping global weather data from [Weather Around The World](https://www.timeanddate.com/weather/), storing it in SQLite, and building an interactive Streamlit dashboard.

## Project Plan

| Program | Purpose | Status |
|---------|---------|--------|
| `scrape_weather.py` | Scrape, clean, and save raw + cleaned CSV | Week 1 |
| `load_weather_db.py` | Import CSV files into SQLite tables | Week 2 |
| Program 3 | Query the database from the command line | Upcoming |
| Program 4 | Streamlit dashboard with interactive visualizations | Upcoming |

## Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Week 1: Scrape and clean data

```bash
cd weather_scrape_data
python scrape_weather.py
```

This will:

1. Open Chrome with Selenium and load the weather page
2. Extract city, local time, weather condition, and temperature for each city
3. Save raw scrape data to `data/weather_raw.csv`
4. Clean and transform the data with pandas (with before/after output)
5. Save cleaned data to `data/weather.csv`

Optional flags:

```bash
python scrape_weather.py --raw-output data/weather_raw.csv --output data/weather.csv
python scrape_weather.py --headless
```

**Note:** If the page shows a Cloudflare challenge, run without `--headless`. A visible Chrome window usually passes the check automatically.

## Week 2: Load CSV files into SQLite

```bash
cd weather_scrape_data
python load_weather_db.py
```

This will:

1. Read `data/weather_raw.csv` into the `weather_raw` table
2. Read `data/weather.csv` into the `weather_clean` table
3. Build `country_temperature_summary` using SQL `GROUP BY` aggregation

Optional flags:

```bash
python load_weather_db.py --raw-csv data/weather_raw.csv --clean-csv data/weather.csv --db data/weather.db
```

## Database Tables

| Table | Source CSV | Description |
|-------|------------|-------------|
| `weather_raw` | `weather_raw.csv` | Unprocessed scrape fields |
| `weather_clean` | `weather.csv` | Cleaned and transformed weather records |
| `country_temperature_summary` | SQL aggregation | Average temperature and city count by country |

## Rubric Coverage (Task 6)

| Requirement | Where it is handled |
|-------------|---------------------|
| Load raw data into a Pandas DataFrame | `cleaner.py` → `raw_records_to_dataframe()` |
| Clean missing, duplicate, malformed entries | `cleaner.py` → `clean_weather_data()` |
| Transformations, groupings, filters | `cleaner.py` (pandas groupby/filter) + `database.py` (SQL summary) |
| Show before/after cleaning stages | `cleaner.py` → `summarize_dataframe()` printed during scrape |
| Save clean data into SQLite | `load_weather_db.py` imports each CSV into its own table |

## Output Columns (cleaned CSV / weather_clean table)

| Column | Description |
|--------|-------------|
| `city` | City name (asterisk removed) |
| `is_capital` | Whether the city is marked as a capital on the site |
| `country` | Country parsed from the city's weather URL |
| `local_time` | Full local date/time string from the page |
| `day_of_week` | Parsed day abbreviation |
| `time` | Parsed local clock time |
| `weather_condition` | Condition text from the weather icon |
| `temperature_f` | Temperature in Fahrenheit |
| `temperature_c` | Temperature converted to Celsius |
| `weather_url` | Link to the city's weather page |
| `scraped_at` | UTC timestamp when the scrape ran |

## Project Structure

```
weather_scrape_data/
  scrape_weather.py    # Week 1 entry point
  load_weather_db.py   # Week 2 entry point
  scraper.py           # Selenium scraping logic
  cleaner.py           # Data cleaning and transformation
  database.py          # SQLite schema and CSV import helpers
  data/
    weather_raw.csv    # Raw scrape output (gitignored)
    weather.csv        # Cleaned output (gitignored)
    weather.db         # SQLite database (gitignored)
requirements.txt
README.md
```
