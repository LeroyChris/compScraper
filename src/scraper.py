"""Compatibility wrapper redirecting to modular providers in src.sources."""

from src.models import sanitize_text as clean_text_for_display
from src.sources.infolomba import (
    InfolombaScraper,
    parse_indonesian_date,
)
from src.sources.infolomba import (
    InfolombaStateManager as StateManager,
)

__all__ = [
    "clean_text_for_display",
    "parse_indonesian_date",
    "StateManager",
    "InfolombaScraper",
]
