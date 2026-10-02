"""Test suite for classifier, word boundary matching, and triage statuses."""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.classifier import CompetitionClassifier
from src.models import CompetitionRecord, TriageStatus, sanitize_text
from src.sources.infolomba import parse_indonesian_date


def test_clean_text_for_display():
    raw1 = "🚀 BUSINESS PLAN COMPETITION — INSYS FEST 2026"
    assert sanitize_text(raw1) == "BUSINESS PLAN COMPETITION — INSYS FEST 2026"

    raw2 = "⚖️ 𝐎𝐏𝐄𝐍 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐓𝐈𝐎𝐍 *SULTAN AGUNG LAW FAIR NASIONAL 2026* ⚖️"
    cleaned2 = sanitize_text(raw2)
    assert "⚖" not in cleaned2
    assert "OPEN REGISTRATION *SULTAN AGUNG LAW FAIR NASIONAL 2026*" == cleaned2


def test_date_parser():
    d1 = parse_indonesian_date("1 Agu - 20 Sep 2026")
    assert d1 == datetime(2026, 9, 20), f"Expected 2026-09-20, got {d1}"

    d2 = parse_indonesian_date("15 Oktober 2026")
    assert d2 == datetime(2026, 10, 15), f"Expected 2026-10-15, got {d2}"

    # Test date without explicit year (smart fallback)
    d3 = parse_indonesian_date("20 Desember")
    assert d3 is not None
    assert d3.month == 12
    assert d3.day == 20

    d4 = parse_indonesian_date("Batas Akhir Besok")
    assert d4 is None


def test_noise_filter():
    classifier = CompetitionClassifier()

    noise_sample = {
        "title": "Lowongan Kerja Software Engineer PT Maju Jaya",
        "description": "We are hiring fresh graduate backend developer",
    }
    res = classifier.classify(noise_sample)
    assert not res["is_competition"], "Noise item should be rejected"
    assert res["status_review"] == TriageStatus.MANUAL_CHECK


def test_majors_classification():
    classifier = CompetitionClassifier()

    # 1. Tech Hackathon
    tech_rec = CompetitionRecord(
        id="test_1",
        source_id="test",
        title="National Hackathon & Competitive Programming 2026",
        description="Lomba web development dan coding competition tingkat nasional untuk mahasiswa.",
    )
    enriched_tech = classifier.enrich_record(tech_rec)
    assert enriched_tech is not None
    assert "Teknik Informatika" in enriched_tech.jurusan
    assert enriched_tech.confidence >= 0.85
    assert enriched_tech.status_review == TriageStatus.AUTO_APPROVE

    # 2. Business Plan (with acronym BCC/BPC)
    biz_rec = CompetitionRecord(
        id="test_2",
        source_id="test",
        title="National BPC & Business Case Competition 2026",
        description="Kompetisi proposal bisnis dan startup pitch deck mahasiswa.",
    )
    enriched_biz = classifier.enrich_record(biz_rec)
    assert enriched_biz is not None
    assert "Manajemen Bisnis" in enriched_biz.jurusan
    assert enriched_biz.confidence >= 0.85
    assert enriched_biz.status_review == TriageStatus.AUTO_APPROVE

    # 3. Law Moot Court
    law_rec = CompetitionRecord(
        id="test_3",
        source_id="test",
        title="National Moot Court Competition & Contract Drafting",
        description="Kompetisi peradilan semu dan legal opinion fakultas hukum.",
    )
    enriched_law = classifier.enrich_record(law_rec)
    assert enriched_law is not None
    assert "Ilmu Hukum" in enriched_law.jurusan
    assert enriched_law.status_review in (TriageStatus.AUTO_APPROVE, TriageStatus.PERLU_REVIEW)

    # 4. Word boundary check: "lain" shouldn't trigger "ai"
    ai_test_rec = CompetitionRecord(
        id="test_4",
        source_id="test",
        title="Lomba Melukis Lain daripada yang Lain",
        description="Kompetisi menggambar pemandangan santai",
    )
    enriched_ai = classifier.enrich_record(ai_test_rec)
    assert enriched_ai is not None
    assert "Sains Data" not in enriched_ai.jurusan


if __name__ == "__main__":
    test_clean_text_for_display()
    test_date_parser()
    test_noise_filter()
    test_majors_classification()
    print("✓ All classifier and triage tests passed.")
