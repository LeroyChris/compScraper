"""Google Sheets sync integration for Competition Hub Tab Audit."""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    LATEST_CSV_FILE,
    LATEST_OUTPUT_FILE,
    SHEET_AUDIT_TAB,
    SPREADSHEET_ID,
)
from src.scraper import clean_text_for_display

log = logging.getLogger("compScraper")

# Comprehensive Headers for Tab Audit & CSV Export
AUDIT_HEADERS = [
    "ID",
    "Judul Lomba",
    "Penyelenggara",
    "Lokasi",
    "Sasaran",
    "Biaya",
    "Deadline",
    "Jurusan (Auto)",
    "Confidence",
    "Status Review",
    "Link Pendaftaran",
    "Link Panduan",
    "URL Sumber",
    "Deskripsi Singkat",
    "Tanggal Scrape",
]


class SheetsSync:
    def __init__(self):
        self.client = None
        self.sheet = None
        self._init_client()

    def _init_client(self):
        """Init gspread client with service account file or JSON string."""
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            if GOOGLE_SERVICE_ACCOUNT_JSON:
                creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                self.client = gspread.authorize(creds)
            elif Path(GOOGLE_SERVICE_ACCOUNT_FILE).exists():
                creds = Credentials.from_service_account_file(
                    GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes
                )
                self.client = gspread.authorize(creds)

            if self.client and SPREADSHEET_ID:
                self.sheet = self.client.open_by_key(SPREADSHEET_ID)
                log.info(f"Connected to Google Spreadsheet: {self.sheet.title}")
        except Exception as e:
            log.warning(f"Google Sheets init skipped ({e}). Falling back to local CSV/JSON.")

    def _merge_and_save_json(self, new_records: list[dict[str, Any]]):
        """Merges new items with existing JSON storage without dropping historical entries."""
        existing_map: dict[str, dict[str, Any]] = {}
        if LATEST_OUTPUT_FILE.exists():
            try:
                with open(LATEST_OUTPUT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if "event_id" in item:
                                existing_map[str(item["event_id"])] = item
            except Exception as e:
                log.warning(f"Could not load existing JSON for merge: {e}")

        # Update or append new items
        for item in new_records:
            eid = str(item.get("event_id", ""))
            if eid:
                existing_map[eid] = item

        # Save merged list
        merged_list = list(existing_map.values())
        try:
            with open(LATEST_OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(merged_list, f, indent=2, ensure_ascii=False)
            log.info(f"💾 Preserved & saved {len(merged_list)} items to {LATEST_OUTPUT_FILE.name}")
        except Exception as e:
            log.error(f"Failed to save JSON output: {e}", exc_info=True)

    def _merge_and_save_csv(self, formatted_rows: list[list[Any]]):
        """Merges formatted rows into CSV without deleting historical rows (UTF-8-SIG for Excel)."""
        row_map: dict[str, list[Any]] = {}

        if LATEST_CSV_FILE.exists():
            try:
                with open(LATEST_CSV_FILE, "r", newline="", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    for r in reader:
                        if r:
                            row_map[str(r[0])] = r
            except Exception as e:
                log.warning(f"Could not load existing CSV for merge: {e}")

        for r in formatted_rows:
            row_map[str(r[0])] = r

        # Write merged rows sorted by ID descending
        sorted_rows = sorted(row_map.values(), key=lambda x: str(x[0]), reverse=True)
        try:
            with open(LATEST_CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(AUDIT_HEADERS)
                writer.writerows(sorted_rows)
            log.info(f"📊 Preserved & saved {len(sorted_rows)} items to {LATEST_CSV_FILE.name}")
        except Exception as e:
            log.error(f"Failed to save CSV output: {e}", exc_info=True)

    def sync_to_audit_tab(self, records: list[dict[str, Any]]) -> int:
        """Push enriched records to Tab Audit and persist merged local CSV/JSON."""
        if not records:
            log.info("No records to sync.")
            return 0

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        formatted_rows = []
        for item in records:
            # Actionable status mapping for audit team
            conf = float(item.get("confidence", 0.0))
            if conf >= 0.85:
                status_label = "AUTO_APPROVE"
            elif conf >= 0.50:
                status_label = "PERLU_REVIEW"
            else:
                status_label = "MANUAL_CHECK"

            # Clean short description excerpt for CSV readability & strip emojis
            desc = item.get("description", "").replace("\n", " ").strip()
            short_desc = (desc[:150] + "...") if len(desc) > 150 else desc

            formatted_rows.append([
                str(item.get("event_id", "")),
                clean_text_for_display(item.get("title", "")),
                clean_text_for_display(item.get("organizer", "")),
                clean_text_for_display(item.get("location", "")),
                clean_text_for_display(item.get("target", "")),
                clean_text_for_display(item.get("fee", "")),
                item.get("deadline", "TBD"),
                item.get("jurusan", "Umum"),
                conf,
                status_label,
                item.get("registration_url") or "",
                item.get("guidebook_url") or "",
                item.get("source_url") or f"https://infolomba.id/{item.get('event_id', '')}",
                clean_text_for_display(short_desc),
                now_str,
            ])

        # 1. Update and merge local persistent files
        self._merge_and_save_json(records)
        self._merge_and_save_csv(formatted_rows)

        # 2. Sync to Google Sheets if configured
        if not self.sheet:
            log.info(
                f"Google Sheets not configured. Preserved locally in {LATEST_CSV_FILE.name} & {LATEST_OUTPUT_FILE.name}."
            )
            return len(records)

        try:
            worksheet = self._get_or_create_worksheet(SHEET_AUDIT_TAB)
            existing_ids = set(worksheet.col_values(1)[1:]) if worksheet.row_count > 1 else set()

            rows_to_append = [
                row for row in formatted_rows if row[0] not in existing_ids
            ]

            if rows_to_append:
                worksheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
                log.info(f"Appended {len(rows_to_append)} rows to Google Sheet '{SHEET_AUDIT_TAB}'.")
            else:
                log.info("All items already exist in Tab Audit Google Sheet.")

            return len(rows_to_append)

        except Exception as e:
            log.error(f"Failed to sync with Google Sheet: {e}", exc_info=True)
            return 0

    def _get_or_create_worksheet(self, title: str):
        try:
            return self.sheet.worksheet(title)
        except Exception:
            ws = self.sheet.add_worksheet(title=title, rows=100, cols=len(AUDIT_HEADERS))
            ws.append_row(AUDIT_HEADERS)
            return ws
