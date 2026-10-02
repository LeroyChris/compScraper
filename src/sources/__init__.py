"""Explicit provider registry for competition scrapers."""

from src.sources.base import BaseScraper
from src.sources.infolomba import InfolombaScraper

# Explicit registry: add newly vetted scraper providers here
ACTIVE_SOURCES: list[type[BaseScraper]] = [
    InfolombaScraper,
]

__all__ = ["ACTIVE_SOURCES", "BaseScraper", "InfolombaScraper"]
