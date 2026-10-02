"""Cross-source deduplication engine using title token similarity and deadline proximity."""

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import DATA_DIR
from src.models import CompetitionRecord

log = logging.getLogger("compScraper")

MASTER_STORE_FILE = DATA_DIR / "master_competitions.json"

STOPWORDS = {
    "lomba", "kompetisi", "competition", "fest", "festival", "nasional", "national",
    "international", "internasional", "tahun", "tingkat", "mahasiswa", "event", "fair",
    "2024", "2025", "2026", "2027", "ke", "dan", "di", "the", "of", "and", "se", "indonesia",
}


def normalize_title_tokens(title: str) -> set[str]:
    """Extracts distinctive normalized tokens from competition title."""
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower())
    tokens = set(clean.split())
    return {t for t in tokens if len(t) > 2 and t not in STOPWORDS}


def compute_fingerprint(title: str, deadline: str | None) -> str:
    """Computes a deterministic hash fingerprint from sorted tokens and deadline."""
    tokens = sorted(normalize_title_tokens(title))
    date_part = deadline or "nodate"
    payload = f"{'_'.join(tokens)}|{date_part}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest()[:16]


def calculate_jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Calculates Jaccard overlap coefficient between two token sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def are_deadlines_proximate(d1: str | None, d2: str | None, max_days: int = 4) -> bool:
    """Checks if two ISO deadline dates are within max_days of each other."""
    if not d1 or not d2:
        return True  # If one is unknown, rely entirely on title similarity

    try:
        dt1 = datetime.strptime(d1, "%Y-%m-%d")
        dt2 = datetime.strptime(d2, "%Y-%m-%d")
        return abs((dt1 - dt2).days) <= max_days
    except ValueError:
        return True


class Deduplicator:
    """Deduplication engine managing identity resolution across all scrape sources."""

    def __init__(self, store_file: Path = MASTER_STORE_FILE):
        self.store_file = store_file
        self.history: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict[str, Any]]:
        if self.store_file.exists():
            try:
                with open(self.store_file, encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        return []
                    data = json.loads(content)
                    return data if isinstance(data, list) else []
            except Exception as e:
                log.warning(f"Could not load master store: {e}. Starting fresh.")
        return []

    def save(self):
        try:
            with open(self.store_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Failed to save master store: {e}")

    def is_duplicate(self, candidate: CompetitionRecord) -> tuple[bool, str]:
        """Checks if candidate matches an existing record in history.

        Returns (True, reason) if duplicate, else (False, "").
        """
        cand_tokens = normalize_title_tokens(candidate.title)
        cand_fingerprint = compute_fingerprint(candidate.title, candidate.deadline)

        # 1. Exact ID match
        for item in self.history:
            if item.get("id") == candidate.id:
                return True, f"Exact ID match: {candidate.id}"

        # 2. Exact Fingerprint match
        for item in self.history:
            if item.get("fingerprint") == cand_fingerprint:
                return True, f"Fingerprint match with existing [{item.get('id')}]"

        # 3. Fuzzy Title Match + Deadline Proximity
        for item in self.history:
            item_tokens = normalize_title_tokens(item.get("title", ""))
            similarity = calculate_jaccard_similarity(cand_tokens, item_tokens)
            if similarity >= 0.70:
                if are_deadlines_proximate(candidate.deadline, item.get("deadline")):
                    return True, f"Fuzzy title match ({similarity:.2f}) with [{item.get('id')}]: '{item.get('title')}'"

        return False, ""

    def filter_and_register(self, records: list[CompetitionRecord]) -> list[CompetitionRecord]:
        """Filters out duplicates, attaches fingerprints, and registers novel records."""
        unique_records: list[CompetitionRecord] = []

        for record in records:
            record.fingerprint = compute_fingerprint(record.title, record.deadline)
            is_dup, reason = self.is_duplicate(record)
            if is_dup:
                log.info(f"Duplicate dropped [{record.id}]: {reason}")
                continue

            unique_records.append(record)
            self.history.append(record.model_dump())

        if unique_records:
            self.save()

        return unique_records
