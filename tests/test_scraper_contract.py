"""Offline contract tests for InfolombaScraper using static HTML fixtures."""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import CompetitionRecord
from src.sources.infolomba import InfolombaScraper

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "infolomba"


def test_infolomba_list_parsing_fixture():
    list_html_path = FIXTURES_DIR / "list_page.html"
    assert list_html_path.exists(), "List fixture must exist"

    with open(list_html_path, encoding="utf-8") as f:
        html = f.read()

    scraper = InfolombaScraper()
    cards = scraper.parse_event_cards(html)

    assert len(cards) == 2, f"Expected 2 cards parsed from fixture, got {len(cards)}"

    card1 = cards[0]
    assert card1["event_id"] == "2128"
    assert card1["seo_slug"] == "business-plan-competition-insys-fest-2026"
    assert card1["deadline"] == datetime(2026, 9, 20)

    card2 = cards[1]
    assert card2["event_id"] == "2140"
    assert card2["deadline"] == datetime(2026, 10, 25)


def test_infolomba_detail_parsing_fixture():
    detail_html_path = FIXTURES_DIR / "detail_modal.html"
    assert detail_html_path.exists(), "Detail fixture must exist"

    with open(detail_html_path, encoding="utf-8") as f:
        html = f.read()

    scraper = InfolombaScraper()
    record = scraper.parse_detail_html(
        html=html,
        event_id="2128",
        seo_slug="business-plan-competition-insys-fest-2026",
        deadline=datetime(2026, 9, 20),
    )

    # Ingress validation & Canonical schema assertions
    assert isinstance(record, CompetitionRecord)
    assert record.id == "infolomba_2128"
    assert record.source_id == "infolomba"
    # Verify emojis were stripped and text normalized
    assert "🚀" not in record.title
    assert "BUSINESS PLAN COMPETITION" in record.title
    assert record.organizer == "Hima Sistem Informasi UMK"
    assert record.deadline == "2026-09-20"
    assert record.registration_url == "https://bit.ly/RegistrasiBPCINSYS"
    assert record.guidebook_url == "https://bit.ly/GuidebookBPCINSYS"
    assert "proposal bisnis" in record.description


if __name__ == "__main__":
    test_infolomba_list_parsing_fixture()
    test_infolomba_detail_parsing_fixture()
    print("✓ All scraper contract tests passed.")
