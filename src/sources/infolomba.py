"""Infolomba.id scrape provider implementation."""

import json
import logging
import re
import urllib.parse
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from src.config import (
    BASE_URL,
    DETAIL_URL,
    FAILED_QUEUE_FILE,
    FILTERED_LIST_URL,
    MAX_PAGES,
    PAGE_SIZE,
    PAGINATION_URL,
    STATE_FILE,
)
from src.models import CompetitionRecord, sanitize_text
from src.sources.base import BaseScraper

log = logging.getLogger("compScraper")

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

REG_LINK_KEYWORDS = (
    "daftar", "registrasi", "register", "registration",
    "formulir", "form", "gform", "linktr.ee", "bit.ly",
)
GUIDE_LINK_KEYWORDS = (
    "panduan", "guide", "juklak", "juknis",
    "rulebook", "booklet", "pedoman", "syarat",
)


def parse_indonesian_date(date_str: str) -> datetime | None:
    """Extract closing date from Indonesian date strings, with smart year fallback."""
    if not date_str:
        return None
    date_str = date_str.lower().strip()
    if "-" in date_str:
        date_str = date_str.split("-")[-1].strip()

    # Pattern with explicit year
    match_with_year = re.search(r"(\d{1,2})\s+([a-z]+)\s+(\d{4})", date_str)
    if match_with_year:
        day, month_str, year = match_with_year.groups()
        month_val = ID_MONTHS.get(month_str[:3])
        if month_val:
            try:
                return datetime(int(year), int(month_val), int(day))
            except ValueError:
                return None

    # Pattern without explicit year (assume current or next year)
    match_no_year = re.search(r"(\d{1,2})\s+([a-z]+)", date_str)
    if match_no_year:
        day, month_str = match_no_year.groups()
        month_val = ID_MONTHS.get(month_str[:3])
        if month_val:
            now = datetime.now()
            year = now.year if month_val >= now.month - 1 else now.year + 1
            try:
                return datetime(year, int(month_val), int(day))
            except ValueError:
                return None

    return None


class InfolombaStateManager:
    """State manager for tracking processed items from infolomba."""

    def __init__(self, state_file=STATE_FILE):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict[str, Any]:
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding="utf-8") as f:
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
        entry = self.state.get(str(event_id))
        return bool(entry and entry.get("status") in ("SUCCESS", "EXPIRED"))

    def mark(self, event_id: str, status: str, meta: dict | None = None):
        self.state[str(event_id)] = {
            "status": status,
            "updated_at": datetime.now().isoformat(),
            **(meta or {}),
        }
        self.save()


class InfolombaScraper(BaseScraper):
    """Scraper provider for infolomba.id."""

    source_id = "infolomba"
    source_name = "Infolomba.id"
    base_url = BASE_URL

    def __init__(self, session=None, state_file=STATE_FILE):
        super().__init__(session=session)
        self.state = InfolombaStateManager(state_file=state_file)

    def parse_event_cards(self, html: str) -> list[dict[str, Any]]:
        """Parses event card snippets from list page HTML."""
        soup = BeautifulSoup(html, "html.parser")
        events = []
        for card in soup.select(".event-container"):
            match = re.search(
                r"loadDetailsEvent\((\d+),\s*[`'\"]([^`'\"]+)[`'\"]",
                str(card),
            )
            if not match:
                continue

            event_id, seo_slug = match.groups()
            date_el = card.select_one(".tanggal")
            date_text = sanitize_text(date_el.get_text(strip=True) if date_el else "")
            deadline = parse_indonesian_date(date_text)

            events.append({
                "event_id": str(event_id),
                "seo_slug": seo_slug,
                "raw_date": date_text,
                "deadline": deadline,
            })
        return events

    def parse_detail_html(
        self,
        html: str,
        event_id: str,
        seo_slug: str = "",
        deadline: datetime | None = None,
    ) -> CompetitionRecord:
        """Parses the raw HTML returned by /load-details into a canonical CompetitionRecord."""
        soup = BeautifulSoup(html, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True).lower()
            if href.startswith("http") and "infolomba.id" not in href:
                links.append({"text": text, "url": href})

        clean_slug = urllib.parse.quote(seo_slug.strip("/")) if seo_slug else ""
        source_url = f"{BASE_URL}/{clean_slug}-{event_id}" if clean_slug else f"{BASE_URL}/{event_id}"

        reg_link = next(
            (item["url"] for item in links if any(k in item["text"] or k in item["url"].lower() for k in REG_LINK_KEYWORDS)),
            "",
        )
        guide_link = next(
            (item["url"] for item in links if any(k in item["text"] or k in item["url"].lower() for k in GUIDE_LINK_KEYWORDS)),
            "",
        )
        first_ext_link = links[0]["url"] if links else source_url

        title_el = soup.select_one(".event-title") or soup.find("h3")
        org_el = soup.select_one(".penyelenggara span:last-child") or soup.select_one(".penyelenggara")
        loc_el = soup.select_one(".lokasi")
        fee_el = soup.select_one(".biaya")
        target_el = soup.select_one(".target")
        desc_el = soup.select_one(".description-body") or soup.find("p")

        deadline_str = deadline.strftime("%Y-%m-%d") if deadline else None

        return CompetitionRecord(
            id=f"{self.source_id}_{event_id}",
            source_id=self.source_id,
            source_url=source_url,
            title=sanitize_text(title_el.get_text(strip=True) if title_el else f"Event {event_id}"),
            organizer=sanitize_text(org_el.get_text(strip=True) if org_el else ""),
            location=sanitize_text(loc_el.get_text(strip=True) if loc_el else "Online"),
            target=sanitize_text(target_el.get_text(strip=True) if target_el else "Mahasiswa"),
            fee=sanitize_text(fee_el.get_text(strip=True) if fee_el else "TBD"),
            deadline=deadline_str,
            registration_url=reg_link or first_ext_link,
            guidebook_url=guide_link,
            description=sanitize_text(desc_el.get_text(separator=" ", strip=True) if desc_el else ""),
        )

    def fetch_page_events(self, page_index: int) -> list[dict[str, Any]]:
        """Fetch list page 0 via SSR, page >= 1 via AJAX POST."""
        if page_index == 0:
            resp = self.request_with_retry("GET", FILTERED_LIST_URL)
            return self.parse_event_cards(resp.text)

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
        resp = self.request_with_retry("POST", PAGINATION_URL, data=payload, headers=headers)
        data = resp.json()
        return self.parse_event_cards(data.get("html", ""))

    def fetch_event_detail(
        self,
        event_id: str,
        seo_slug: str = "",
        deadline: datetime | None = None,
    ) -> CompetitionRecord:
        """Fetches dynamic modal HTML from /load-details and returns CompetitionRecord."""
        self.sleep_polite()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": FILTERED_LIST_URL,
        }
        resp = self.request_with_retry("POST", DETAIL_URL, data={"event_id": event_id}, headers=headers)
        html = resp.json().get("html", "")
        return self.parse_detail_html(html, event_id, seo_slug, deadline)

    def record_failure(self, event_id: str, slug: str, error_msg: str):
        queue: list[dict[str, Any]] = []
        if FAILED_QUEUE_FILE.exists():
            try:
                with open(FAILED_QUEUE_FILE, encoding="utf-8") as f:
                    queue = json.load(f)
            except Exception:
                queue = []

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

    def scrape(self, max_items: int = 25) -> list[CompetitionRecord]:
        """Runs the scraping loop for infolomba."""
        log.info(f"[{self.source_id}] Starting scrape run (target max: {max_items})...")
        records: list[CompetitionRecord] = []

        for page in range(MAX_PAGES):
            if len(records) >= max_items:
                break

            log.info(f"[{self.source_id}] Scanning list page {page + 1}...")
            try:
                page_events = self.fetch_page_events(page)
            except Exception as e:
                log.error(f"[{self.source_id}] Failed page {page + 1}: {e}", exc_info=True)
                break

            if not page_events:
                break

            new_in_page = 0
            for ev in page_events:
                if len(records) >= max_items:
                    break

                eid = ev["event_id"]
                if self.state.is_processed(eid):
                    continue

                new_in_page += 1
                deadline = ev["deadline"]
                if deadline and deadline < datetime.now():
                    self.state.mark(eid, "EXPIRED", {"deadline": deadline.isoformat()})
                    continue

                try:
                    record = self.fetch_event_detail(eid, seo_slug=ev.get("seo_slug", ""), deadline=deadline)
                    records.append(record)
                    self.state.mark(eid, "SUCCESS")
                    log.info(f"[{self.source_id}] Extracted: {record.title}")
                except Exception as e:
                    log.error(f"[{self.source_id}] Detail failed for event {eid}: {e}", exc_info=True)
                    self.state.mark(eid, "FAILED", {"error": str(e)})
                    self.record_failure(eid, ev.get("seo_slug", ""), str(e))

            if new_in_page == 0:
                log.info(f"[{self.source_id}] All items on page {page + 1} already processed.")

        log.info(f"[{self.source_id}] Run complete. Extracted {len(records)} records.")
        return records
