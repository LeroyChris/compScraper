"""Google Sheets sync integration for Competition Hub Tab Audit with local persistence."""

import csv
import json
import logging
from pathlib import Path

from src.config import (
    DATA_DIR,
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    LATEST_CSV_FILE,
    LATEST_OUTPUT_FILE,
    SHEET_AUDIT_TAB,
    SPREADSHEET_ID,
)
from src.models import CompetitionRecord, sanitize_text

log = logging.getLogger("compScraper")

LATEST_DIGEST_FILE = DATA_DIR / "latest_digest.txt"

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
    """Manages publishing enriched competition records to Google Sheets and local storage."""

    def __init__(self):
        self.client = None
        self.sheet = None
        self._init_client()

    def _init_client(self):
        """Init gspread client with service account credentials if provided."""
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
            log.warning(f"Google Sheets init skipped ({e}). Falling back to local storage.")

    def _merge_and_save_json(self, records: list[CompetitionRecord]):
        existing_map: dict[str, dict] = {}
        if LATEST_OUTPUT_FILE.exists():
            try:
                with open(LATEST_OUTPUT_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if "id" in item:
                                existing_map[str(item["id"])] = item
            except Exception as e:
                log.warning(f"Could not load existing JSON for merge: {e}")

        for rec in records:
            existing_map[rec.id] = rec.model_dump()

        merged_list = list(existing_map.values())
        try:
            with open(LATEST_OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(merged_list, f, indent=2, ensure_ascii=False)
            log.info(f"Saved {len(merged_list)} items to {LATEST_OUTPUT_FILE.name}")
        except Exception as e:
            log.error(f"Failed to save JSON: {e}")

    def _merge_and_save_csv(self, formatted_rows: list[list]):
        row_map: dict[str, list] = {}
        if LATEST_CSV_FILE.exists():
            try:
                with open(LATEST_CSV_FILE, newline="", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    for r in reader:
                        if r:
                            row_map[str(r[0])] = r
            except Exception as e:
                log.warning(f"Could not load existing CSV for merge: {e}")

        for r in formatted_rows:
            row_map[str(r[0])] = r

        sorted_rows = sorted(row_map.values(), key=lambda x: str(x[0]), reverse=True)
        try:
            with open(LATEST_CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(AUDIT_HEADERS)
                writer.writerows(sorted_rows)
            log.info(f"Saved {len(sorted_rows)} items to {LATEST_CSV_FILE.name}")
        except Exception as e:
            log.error(f"Failed to save CSV: {e}")

    def _export_digest(self, records: list[CompetitionRecord]):
        """Exports a clean text digest for instant copy-pasting to messaging channels."""
        if not records:
            return

        digests = [rec.generate_digest() for rec in records]
        content = "\n\n" + ("=" * 45) + "\n\n".join(digests) + "\n"
        try:
            with open(LATEST_DIGEST_FILE, "w", encoding="utf-8") as f:
                f.write(content.strip())
            log.info(f"Exported text digest to {LATEST_DIGEST_FILE.name}")
        except Exception as e:
            log.error(f"Failed to export digest: {e}")

    def sync_to_audit_tab(self, records: list[CompetitionRecord]) -> int:
        """Push enriched records to Tab Audit and persist merged local CSV/JSON/Digest."""
        if not records:
            log.info("No records to sync.")
            return 0

        formatted_rows = []
        for rec in records:
            desc = rec.description.replace("\n", " ").strip()
            short_desc = (desc[:150] + "...") if len(desc) > 150 else desc

            formatted_rows.append([
                rec.id,
                rec.title,
                rec.organizer,
                rec.location,
                rec.target,
                rec.fee,
                rec.deadline or "TBD",
                rec.jurusan,
                rec.confidence,
                rec.status_review.value if hasattr(rec.status_review, "value") else str(rec.status_review),
                rec.registration_url,
                rec.guidebook_url,
                rec.source_url,
                sanitize_text(short_desc),
                rec.scraped_at,
            ])

        # 1. Update and merge local persistent files
        self._merge_and_save_json(records)
        self._merge_and_save_csv(formatted_rows)
        self._export_digest(records)

        # 2. Sync to Google Sheets if configured
        if not self.sheet:
            log.info(f"Google Sheets not configured. Stored locally in {LATEST_CSV_FILE.name}")
            return len(records)

        try:
            worksheet = self._get_or_create_worksheet(SHEET_AUDIT_TAB)
            existing_ids = set(worksheet.col_values(1)[1:]) if worksheet.row_count > 1 else set()

            rows_to_append = [row for row in formatted_rows if row[0] not in existing_ids]

            if rows_to_append:
                worksheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
                log.info(f"Appended {len(rows_to_append)} rows to Google Sheet '{SHEET_AUDIT_TAB}'")
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
