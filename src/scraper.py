"""Scraper engine for infolomba.id with pagination and fault tolerance."""

import json
import logging
import random
import re
import sys
import time
import unicodedata
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from src.config import (
    APP_LOG_FILE,
    BASE_URL,
    DEFAULT_HEADERS,
    DETAIL_URL,
    ERROR_LOG_FILE,
    FAILED_QUEUE_FILE,
    FILTERED_LIST_URL,
    MAX_DELAY,
    MAX_ITEMS_PER_RUN,
    MAX_PAGES,
    MAX_RETRIES,
    MIN_DELAY,
    PAGE_SIZE,
    PAGINATION_URL,
    STATE_FILE,
    TIMEOUT,
    setup_logger,
)

log = setup_logger("compScraper")

ID_MONTHS = {
    "jan": 1, "januari": 1,
    "feb": 2, "februari": 2,
    "mar": 3, "maret": 3,
    "apr": 4, "april": 4,
    "mei": 5,
    "jun": 6, "juni": 6,
    "jul": 7, "juli": 7,
    "agu": 8, "agustus": 8,
    "sep": 9, "september": 9,
    "okt": 10, "oktober": 10,
    "nov": 11, "november": 11,
    "des": 12, "desember": 12,
}

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def clean_text_for_display(text: str) -> str:
    """Normalizes stylized unicode fonts and removes emojis for clean spreadsheet display."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = EMOJI_PATTERN.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_indonesian_date(date_str: str) -> datetime | None:
    """Extract closing date from strings like '1 Agu - 20 Sep 2026'."""
    date_str = date_str.lower().strip()
    if "-" in date_str:
        date_str = date_str.split("-")[-1].strip()

    match = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", date_str)
    if not match:
        return None

    day, month_str, year = match.groups()
    month_val = ID_MONTHS.get(month_str[:3])
    if not month_val:
        return None

    try:
        return datetime(int(year), int(month_val), int(day))
    except ValueError:
        return None


def extract_clean_text(el) -> str:
    if not el:
        return ""
    text = el.get_text(separator=" ", strip=True)
    return clean_text_for_display(text)


class StateManager:
    """Tracks processed items to avoid duplicate scraping."""

    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict[str, Any]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.warning(f"Failed to read state: {e}. Starting fresh.")
        return {}

    def save(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save state: {e}")

    def is_processed(self, event_id: str) -> bool:
        # Only SUCCESS and EXPIRED count as processed. FAILED can be retried.
        entry = self.state.get(str(event_id))
        return bool(entry and entry.get("status") in ("SUCCESS", "EXPIRED"))

    def mark(self, event_id: str, status: str, meta: dict | None = None):
        self.state[str(event_id)] = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
            **(meta or {}),
        }
        self.save()


class InfolombaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.state = StateManager()

    def _sleep(self):
        time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.request(method, url, timeout=TIMEOUT, **kwargs)
                if resp.status_code in (429, 500, 502, 503, 504):
                    log.warning(f"HTTP {resp.status_code} on {url}. Retry {attempt}/{MAX_RETRIES}")
                else:
                    resp.raise_for_status()
                    return resp
            except requests.RequestException as e:
                log.warning(f"Request error on {url}: {e}. Retry {attempt}/{MAX_RETRIES}")

            if attempt < MAX_RETRIES:
                time.sleep((2**attempt) + random.uniform(0.5, 1.5))
        raise RuntimeError(f"Failed {method} {url} after {MAX_RETRIES} attempts")

    def _parse_event_cards(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        events = []
        for card in soup.select(".event-container"):
            # Handles backtick, single quote, and double quote in onclick
            match = re.search(
                r"loadDetailsEvent\((\d+),\s*[`'\"]([^`'\"]+)[`'\"]",
                str(card),
            )
            if not match:
                continue

            event_id, seo_slug = match.groups()
            date_text = extract_clean_text(card.select_one(".tanggal"))
            deadline = parse_indonesian_date(date_text)

            events.append({
                "event_id": event_id,
                "seo_slug": seo_slug,
                "raw_date": date_text,
                "deadline": deadline,
            })
        return events

    def fetch_page_events(self, page_index: int) -> list[dict[str, Any]]:
        """Fetch page 0 from SSR list, page >= 1 from AJAX /load-event-2."""
        if page_index == 0:
            resp = self._request("GET", FILTERED_LIST_URL)
            return self._parse_event_cards(resp.text)

        offset = page_index * PAGE_SIZE
        payload = {
            "start": offset,
            "sort": "Default",
            "title": "",
            "peserta": "5",
            "lokasi": "Semua Lokasi",
            "kategori": "Semua Kategori",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": FILTERED_LIST_URL,
        }
        resp = self._request("POST", PAGINATION_URL, data=payload, headers=headers)
        data = resp.json()
        html = data.get("html", "")
        return self._parse_event_cards(html)

    def fetch_event_detail(self, event_id: str, seo_slug: str = "") -> dict[str, Any]:
        self._sleep()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": FILTERED_LIST_URL,
        }
        resp = self._request("POST", DETAIL_URL, data={"event_id": event_id}, headers=headers)
        html = resp.json().get("html", "")
        soup = BeautifulSoup(html, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True).lower()
            if href.startswith("http") and "infolomba.id" not in href:
                links.append({"text": text, "url": href})

        clean_slug = urllib.parse.quote(seo_slug.strip("/")) if seo_slug else ""
        source_url = f"{BASE_URL}/{clean_slug}-{event_id}" if clean_slug else f"{BASE_URL}/{event_id}"

        reg_link = next((item["url"] for item in links if "daftar" in item["text"]), "")
        guide_link = next((item["url"] for item in links if "panduan" in item["text"] or "guide" in item["text"]), "")
        first_ext_link = links[0]["url"] if links else source_url

        return {
            "event_id": str(event_id),
            "title": extract_clean_text(soup.select_one(".event-title") or soup.find("h3")),
            "organizer": extract_clean_text(soup.select_one(".penyelenggara span:last-child") or soup.select_one(".penyelenggara")),
            "location": extract_clean_text(soup.select_one(".lokasi")),
            "fee": extract_clean_text(soup.select_one(".biaya")),
            "target": extract_clean_text(soup.select_one(".target")),
            "description": extract_clean_text(soup.select_one(".description-body") or soup.find("p")),
            "links": links,
            "registration_url": reg_link or first_ext_link,
            "guidebook_url": guide_link,
            "source_url": source_url,
            "source_name": "infolomba.id",
        }

    def record_failure(self, event_id: str, slug: str, error_msg: str):
        """Append error record to failed_queue.json for recovery and debugging."""
        queue: list[dict[str, Any]] = []
        if FAILED_QUEUE_FILE.exists():
            try:
                with open(FAILED_QUEUE_FILE, "r", encoding="utf-8") as f:
                    queue = json.load(f)
            except Exception:
                queue = []

        # Update existing or append new
        queue = [item for item in queue if str(item.get("event_id")) != str(event_id)]
        queue.append({
            "event_id": str(event_id),
            "url": f"{BASE_URL}/{event_id}",
            "slug": slug,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
        })

        try:
            with open(FAILED_QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Failed to write to {FAILED_QUEUE_FILE.name}: {e}")

    def retry_failed_queue(self) -> list[dict[str, Any]]:
        """Auto-retries previously failed items before scraping new ones."""
        if not FAILED_QUEUE_FILE.exists():
            return []

        try:
            with open(FAILED_QUEUE_FILE, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except Exception as e:
            log.warning(f"Could not read {FAILED_QUEUE_FILE.name}: {e}")
            return []

        if not queue:
            return []

        log.info(f"🔄 Retrying {len(queue)} items from failed queue...")
        recovered: list[dict[str, Any]] = []
        remaining: list[dict[str, Any]] = []

        for item in queue:
            eid = str(item.get("event_id", ""))
            slug = item.get("slug", "")
            try:
                detail = self.fetch_event_detail(eid, seo_slug=slug)
                detail["deadline_date"] = None
                detail["deadline"] = "TBD"
                detail["seo_slug"] = slug
                recovered.append(detail)
                self.state.mark(eid, "SUCCESS")
                log.info(f"✅ Successfully recovered failed event [{eid}]: {detail['title']}")
            except Exception as e:
                log.warning(f"Retry still failed for [{eid}]: {e}")
                remaining.append(item)

        try:
            with open(FAILED_QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(remaining, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Failed to update {FAILED_QUEUE_FILE.name}: {e}")

        return recovered

    def scrape(self, max_items: int = MAX_ITEMS_PER_RUN) -> list[dict[str, Any]]:
        """Crawl across pages until max_items reached or no new items found."""
        log.info(f"Starting scraper run (Target: up to {max_items} new items)...")
        results: list[dict[str, Any]] = []

        # Auto-retry failed items first
        recovered = self.retry_failed_queue()
        results.extend(recovered)

        for page in range(MAX_PAGES):
            if len(results) >= max_items:
                break

            log.info(f"Scanning list page {page + 1}...")
            try:
                page_events = self.fetch_page_events(page)
            except Exception as e:
                log.error(f"Failed to fetch page {page + 1}: {e}", exc_info=True)
                break

            if not page_events:
                log.info("No more events returned by server.")
                break

            new_in_page = 0
            for ev in page_events:
                if len(results) >= max_items:
                    break

                eid = ev["event_id"]
                if self.state.is_processed(eid):
                    continue

                new_in_page += 1
                deadline = ev["deadline"]
                if deadline and deadline < datetime.now():
                    log.debug(f"Event {eid} expired on {deadline.date()}. Skipping.")
                    self.state.mark(eid, "EXPIRED", {"deadline": deadline.isoformat()})
                    continue

                try:
                    detail = self.fetch_event_detail(eid, seo_slug=ev.get("seo_slug", ""))
                    detail["deadline_date"] = deadline.isoformat() if deadline else None
                    detail["deadline"] = deadline.strftime("%Y-%m-%d") if deadline else "TBD"
                    detail["seo_slug"] = ev["seo_slug"]
                    results.append(detail)
                    self.state.mark(eid, "SUCCESS")
                    log.info(f"Extracted [{eid}]: {detail['title']}")
                except Exception as e:
                    log.error(f"Failed detail for Event {eid}: {e}", exc_info=True)
                    self.state.mark(eid, "FAILED", {"error": str(e)})
                    self.record_failure(eid, ev.get("seo_slug", ""), str(e))

            if new_in_page == 0:
                log.info(f"All events on page {page + 1} already processed.")

        log.info(f"Scraper completed. Extracted {len(results)} items.")
        return results
