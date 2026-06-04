# Web Scraping Capstone Project (Code The Dream)

Capstone project for scraping global weather data from [Weather Around The World](https://www.timeanddate.com/weather/), storing it in SQLite, and building an interactive Streamlit dashboard.

## Project Plan

| Program | Purpose | Status |
|---------|---------|--------|
| `scrape_weather.py` | Scrape, clean, and save data to CSV | Week 1 |
| Program 2 | Load cleaned data into SQLite | Upcoming |
| Program 3 | Query the database from the command line | Upcoming |
| Program 4 | Streamlit dashboard with interactive visualizations | Upcoming |

## Week 1 Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the scraper

From the project root:

```bash
cd weather_scrape_data
python scrape_weather.py
```

This will:

1. Open Chrome with Selenium and load the weather page
2. Extract city, local time, weather condition, and temperature for each city
3. Clean and structure the data with pandas
4. Save the result to `weather_scrape_data/data/weather.csv`

Optional flags:

```bash
python scrape_weather.py --output data/weather.csv
python scrape_weather.py --headless
```

**Note:** If the page shows a Cloudflare challenge, run without `--headless`. A visible Chrome window usually passes the check automatically.

## Output Columns

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
  scrape_weather.py   # Week 1 entry point
  scraper.py          # Selenium scraping logic
  cleaner.py          # Data cleaning and transformation
  data/
    weather.csv       # Generated output (gitignored)
requirements.txt
README.md
```
