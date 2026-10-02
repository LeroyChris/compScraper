"""Abstract base class for all competition scrape providers."""

import logging
import random
import time
from abc import ABC, abstractmethod

import requests

from src.config import DEFAULT_HEADERS, MAX_DELAY, MAX_RETRIES, MIN_DELAY, TIMEOUT
from src.models import CompetitionRecord

log = logging.getLogger("compScraper")


class BaseScraper(ABC):
    """Abstract interface for all competition scrape providers.

    All custom scrapers (e.g. infolomba, puspresnas, campus portals) must inherit from this class.
    """

    source_id: str = "base"
    source_name: str = "Base Scraper"
    base_url: str = ""

    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def sleep_polite(self):
        """Random polite delay to avoid aggressive scraping."""
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    def request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """HTTP request with exponential backoff retry on transient errors."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.request(method, url, timeout=TIMEOUT, **kwargs)
                if resp.status_code in (429, 500, 502, 503, 504):
                    log.warning(f"[{self.source_id}] HTTP {resp.status_code} on {url}. Retry {attempt}/{MAX_RETRIES}")
                else:
                    resp.raise_for_status()
                    return resp
            except requests.RequestException as e:
                log.warning(f"[{self.source_id}] Request error on {url}: {e}. Retry {attempt}/{MAX_RETRIES}")

            if attempt < MAX_RETRIES:
                time.sleep((2**attempt) + random.uniform(0.5, 1.5))

        raise RuntimeError(f"[{self.source_id}] Failed {method} {url} after {MAX_RETRIES} attempts")

    @abstractmethod
    def scrape(self, max_items: int = 25) -> list[CompetitionRecord]:
        """Collects raw competitions and returns canonical CompetitionRecord instances.

        Must be implemented by each provider.
        """
        pass
