"""Selenium scraper for the Weather Around The World page on timeanddate.com."""

import time
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

WEATHER_URL = "https://www.timeanddate.com/weather/"
PAGE_LOAD_TIMEOUT_SECONDS = 30
CLOUDFLARE_WAIT_SECONDS = 15


def create_driver(headless: bool = False) -> webdriver.Chrome:
    """Create a Chrome WebDriver configured for timeanddate.com."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    return driver


def _wait_for_weather_table(driver: webdriver.Chrome) -> None:
    """Wait until Cloudflare clears and the weather table is present."""
    deadline = time.time() + CLOUDFLARE_WAIT_SECONDS
    while time.time() < deadline:
        if "moment" not in driver.title.lower():
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table tr td"))
                )
                return
            except Exception:
                pass
        time.sleep(1)

    raise TimeoutError(
        "Timed out waiting for the weather table. "
        "Try running without --headless if Cloudflare is blocking the browser."
    )


def _parse_city_block(cells: list[Any], start_index: int) -> dict[str, str] | None:
    """Extract one city record from a 4-cell block inside a table row."""
    try:
        city_cell = cells[start_index]
        time_cell = cells[start_index + 1]
        weather_cell = cells[start_index + 2]
        temp_cell = cells[start_index + 3]
    except IndexError:
        return None

    city_text = city_cell.text.strip()
    if not city_text:
        return None

    weather_url = ""
    links = city_cell.find_elements(By.TAG_NAME, "a")
    if links:
        weather_url = links[0].get_attribute("href") or ""

    weather_condition = ""
    images = weather_cell.find_elements(By.TAG_NAME, "img")
    if images:
        weather_condition = (
            images[0].get_attribute("alt")
            or images[0].get_attribute("title")
            or ""
        ).strip()

    return {
        "city_raw": city_text,
        "local_time_raw": time_cell.text.strip(),
        "weather_condition_raw": weather_condition,
        "temperature_raw": temp_cell.text.strip(),
        "weather_url": weather_url,
    }


def scrape_weather_table(driver: webdriver.Chrome) -> list[dict[str, str]]:
    """Parse all city records from the main weather table."""
    table = driver.find_element(By.TAG_NAME, "table")
    rows = table.find_elements(By.TAG_NAME, "tr")[1:]

    records: list[dict[str, str]] = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        for block_start in range(0, len(cells), 4):
            record = _parse_city_block(cells, block_start)
            if record:
                records.append(record)

    if not records:
        raise ValueError("No weather records were found on the page.")

    return records


def scrape_weather(headless: bool = False) -> list[dict[str, str]]:
    """Scrape current weather data for all cities shown on the main page."""
    driver = create_driver(headless=headless)
    try:
        driver.get(WEATHER_URL)
        _wait_for_weather_table(driver)
        return scrape_weather_table(driver)
    finally:
        driver.quit()
