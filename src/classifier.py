"""Rule-based competition classifier with 2-layer filtering."""

import json
import re
from typing import Any
from src.config import KEYWORDS_FILE


class CompetitionClassifier:
    def __init__(self, keywords_file=KEYWORDS_FILE):
        with open(keywords_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.noise_patterns = [
            re.compile(p, re.IGNORECASE) for p in data.get("noise_patterns", [])
        ]
        self.majors = data.get("majors", {})

    def is_noise(self, text: str) -> bool:
        """Layer 1: Filter out jobs, webinars, scholarships."""
        return any(p.search(text) for p in self.noise_patterns)

    def classify(self, item: dict[str, Any]) -> dict[str, Any]:
        """Layer 2: Match weighted keywords across 15 majors.

        # ponytail: regex + keyword weighting covers 80% without LLM API cost. Upgrade to LLM when ambiguity > 20%.
        """
        combined_text = f"{item.get('title', '')} {item.get('description', '')}".lower()

        if self.is_noise(combined_text):
            return {
                "is_competition": False,
                "confidence": 0.0,
                "jurusan": "Non-Kompetisi / Noise",
                "scores": {},
                "status_color": "RED",
            }

        scores: dict[str, int] = {}
        for major_name, major_data in self.majors.items():
            total = 0
            for kw, weight in major_data.get("keywords", {}).items():
                if kw in combined_text:
                    total += weight
            if total >= 20:  # PRD threshold
                scores[major_name] = total

        if not scores:
            return {
                "is_competition": True,
                "confidence": 0.30,
                "jurusan": "Umum / Belum Terpetakan",
                "scores": {},
                "status_color": "RED",
            }

        sorted_majors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_major, top_score = sorted_majors[0]
        confidence = round(min(top_score / 60.0, 0.98), 2)

        matched_names = [m[0] for m in sorted_majors[:3]]
        jurusan_str = ", ".join(matched_names)

        color = "GREEN" if confidence >= 0.85 else ("YELLOW" if confidence >= 0.50 else "RED")

        return {
            "is_competition": True,
            "confidence": confidence,
            "jurusan": jurusan_str,
            "scores": dict(sorted_majors),
            "status_color": color,
        }
