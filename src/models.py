"""Canonical competition domain models and ingress validation."""

import re
import unicodedata
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

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


def sanitize_text(text: str | None) -> str:
    """Normalize styled unicode text, strip emojis, collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = EMOJI_PATTERN.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


class TriageStatus(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    PERLU_REVIEW = "PERLU_REVIEW"
    MANUAL_CHECK = "MANUAL_CHECK"


class CompetitionRecord(BaseModel):
    """Canonical data model for a competition ingested from any source."""

    id: str = Field(description="Unique globally namespaced ID, e.g. 'infolomba_2128'")
    source_id: str = Field(description="Source identifier, e.g. 'infolomba'")
    source_url: str = Field(default="")
    title: str = Field(description="Competition title")
    organizer: str = Field(default="")
    location: str = Field(default="Online")
    target: str = Field(default="Mahasiswa")
    fee: str = Field(default="TBD")
    deadline: str | None = Field(default=None, description="ISO date YYYY-MM-DD or None")
    registration_url: str = Field(default="")
    guidebook_url: str = Field(default="")
    description: str = Field(default="")

    # Enriched fields (added by classifier/pipeline)
    jurusan: str = Field(default="Umum / Belum Terpetakan")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status_review: TriageStatus = Field(default=TriageStatus.MANUAL_CHECK)
    scores: dict[str, int] = Field(default_factory=dict)
    scraped_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    fingerprint: str | None = Field(default=None, description="Token-based similarity hash")

    @field_validator("title", "organizer", "location", "target", "fee", "description", mode="before")
    @classmethod
    def clean_text_fields(cls, v: Any) -> str:
        return sanitize_text(str(v) if v is not None else "")

    @field_validator("deadline", mode="before")
    @classmethod
    def validate_deadline_format(cls, v: Any) -> str | None:
        if not v or v in ("TBD", "None", ""):
            return None
        # Must be valid date or date string
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d")
        return str(v).strip()

    def generate_digest(self) -> str:
        """Generates clean structured summary suitable for campus messaging."""
        lines = [
            f"📌 {self.title}",
            f"🏢 Penyelenggara: {self.organizer or 'TBD'}",
            f"📍 Lokasi: {self.location or 'Online'}",
            f"🎯 Sasaran: {self.target or 'Mahasiswa'}",
            f"⏳ Deadline: {self.deadline or 'TBD'}",
            f"💰 Biaya: {self.fee or 'TBD'}",
            f"🎓 Bidang: {self.jurusan}",
        ]
        if self.registration_url:
            lines.append(f"🔗 Pendaftaran: {self.registration_url}")
        if self.guidebook_url:
            lines.append(f"📖 Panduan: {self.guidebook_url}")
        if self.source_url:
            lines.append(f"🌐 Sumber: {self.source_url}")
        return "\n".join(lines)
