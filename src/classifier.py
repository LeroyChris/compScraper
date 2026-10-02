"""Rule-based competition classifier with 2-layer filtering and regex word boundary matching."""

import json
import logging
import re
from typing import Any

from src.config import KEYWORDS_FILE
from src.models import CompetitionRecord, TriageStatus

log = logging.getLogger("compScraper")


class CompetitionClassifier:
    def __init__(self, keywords_file=KEYWORDS_FILE):
        with open(keywords_file, encoding="utf-8") as f:
            data = json.load(f)

        self.noise_patterns = [
            re.compile(p, re.IGNORECASE) for p in data.get("noise_patterns", [])
        ]

        # Compile word boundary patterns for majors to avoid substring false positives
        self.majors: dict[str, list[tuple[re.Pattern, int]]] = {}
        for major_name, major_data in data.get("majors", {}).items():
            compiled_kws = []
            for kw, weight in major_data.get("keywords", {}).items():
                # Word boundary regex pattern
                pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                compiled_kws.append((pattern, weight))
            self.majors[major_name] = compiled_kws

    def is_noise(self, text: str) -> bool:
        """Layer 1: Filter out jobs, webinars, scholarships."""
        return any(p.search(text) for p in self.noise_patterns)

    def classify(self, item: CompetitionRecord | dict[str, Any]) -> dict[str, Any]:
        """Layer 2: Match weighted keywords across 15 majors using word boundaries.

        Returns classification dict with confidence and TriageStatus.
        """
        if isinstance(item, CompetitionRecord):
            title = item.title
            desc = item.description
        else:
            title = item.get("title", "")
            desc = item.get("description", "")

        combined_text = f"{title} {desc}".lower()

        if self.is_noise(combined_text):
            return {
                "is_competition": False,
                "confidence": 0.0,
                "jurusan": "Non-Kompetisi / Noise",
                "scores": {},
                "status_color": "RED",
                "status_review": TriageStatus.MANUAL_CHECK,
            }

        scores: dict[str, int] = {}
        for major_name, patterns in self.majors.items():
            total = 0
            for pattern, weight in patterns:
                if pattern.search(combined_text):
                    total += weight
            if total >= 20:  # Threshold per PRD
                scores[major_name] = total

        if not scores:
            return {
                "is_competition": True,
                "confidence": 0.30,
                "jurusan": "Umum / Belum Terpetakan",
                "scores": {},
                "status_color": "RED",
                "status_review": TriageStatus.MANUAL_CHECK,
            }

        sorted_majors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_major, top_score = sorted_majors[0]
        confidence = round(min(top_score / 60.0, 0.98), 2)

        matched_names = [m[0] for m in sorted_majors[:3]]
        jurusan_str = ", ".join(matched_names)

        if confidence >= 0.85:
            color = "GREEN"
            triage = TriageStatus.AUTO_APPROVE
        elif confidence >= 0.50:
            color = "YELLOW"
            triage = TriageStatus.PERLU_REVIEW
        else:
            color = "RED"
            triage = TriageStatus.MANUAL_CHECK

        return {
            "is_competition": True,
            "confidence": confidence,
            "jurusan": jurusan_str,
            "scores": dict(sorted_majors),
            "status_color": color,
            "status_review": triage,
        }

    def enrich_record(self, record: CompetitionRecord) -> CompetitionRecord | None:
        """Enriches a CompetitionRecord in-place. Returns None if item is noise."""
        result = self.classify(record)
        if not result["is_competition"]:
            return None

        record.jurusan = result["jurusan"]
        record.confidence = result["confidence"]
        record.status_review = result["status_review"]
        record.scores = result["scores"]
        return record
