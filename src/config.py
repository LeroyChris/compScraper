"""Configuration settings for compScraper."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# File Paths
STATE_FILE = DATA_DIR / "processed_events.json"
KEYWORDS_FILE = DATA_DIR / "keywords.json"
LATEST_OUTPUT_FILE = DATA_DIR / "latest_scraped_output.json"
LATEST_CSV_FILE = DATA_DIR / "latest_scraped_output.csv"
FAILED_QUEUE_FILE = DATA_DIR / "failed_queue.json"

APP_LOG_FILE = LOGS_DIR / "scraper.log"
ERROR_LOG_FILE = LOGS_DIR / "error.log"

# Web Scraping Configuration
BASE_URL = "https://infolomba.id"
FILTERED_LIST_URL = (
    f"{BASE_URL}/events"
    "?sort=Default&title=&peserta=5"
    "&lokasi=Semua+Lokasi&kategori=Semua+Kategori"
)
PAGINATION_URL = f"{BASE_URL}/load-event-2"
DETAIL_URL = f"{BASE_URL}/load-details"

MAX_ITEMS_PER_RUN = int(os.getenv("MAX_ITEMS_PER_RUN", "25"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))
PAGE_SIZE = 10  # infolomba default offset increment
TIMEOUT = int(os.getenv("TIMEOUT", "15"))
MIN_DELAY = float(os.getenv("MIN_DELAY_SECONDS", "2.0"))
MAX_DELAY = float(os.getenv("MAX_DELAY_SECONDS", "4.0"))
MAX_RETRIES = 3

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 (CompetitionHubBot/1.0; SGA Cakrawala University)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SHEET_AUDIT_TAB = os.getenv("SHEET_AUDIT_TAB", "Tab Audit")
SHEET_MASTER_TAB = os.getenv("SHEET_MASTER_TAB", "Master Data Lomba")
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")


def setup_logger(name: str = "compScraper") -> logging.Logger:
    """Configures structured logging to console, logs/scraper.log, and logs/error.log."""
    import logging

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # 1. Console Handler (INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    # 2. General Scraper Log (DEBUG+)
    fh = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"))
    logger.addHandler(fh)

    # 3. Dedicated Error Log (WARNING+)
    eh = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
    eh.setLevel(logging.WARNING)
    eh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"))
    logger.addHandler(eh)

    return logger
