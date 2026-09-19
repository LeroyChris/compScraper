"""Self-check test suite for classifier and date parser."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from src.classifier import CompetitionClassifier
from src.scraper import clean_text_for_display, parse_indonesian_date


def test_clean_text_for_display():
    raw1 = "🚀 BUSINESS PLAN COMPETITION — INSYS FEST 2026"
    assert clean_text_for_display(raw1) == "BUSINESS PLAN COMPETITION — INSYS FEST 2026"

    raw2 = "⚖️ 𝐎𝐏𝐄𝐍 𝐑𝐄𝐆𝐈𝐒𝐓𝐑𝐀𝐓𝐈𝐎𝐍 *SULTAN AGUNG LAW FAIR NASIONAL 2026* ⚖️"
    cleaned2 = clean_text_for_display(raw2)
    assert "⚖" not in cleaned2
    assert "OPEN REGISTRATION *SULTAN AGUNG LAW FAIR NASIONAL 2026*" == cleaned2

    raw3 = "🌊⚓ARE YOU READY?⚓🌊"
    assert clean_text_for_display(raw3) == "ARE YOU READY?"


def test_date_parser():
    d1 = parse_indonesian_date("1 Agu - 20 Sep 2026")
    assert d1 == datetime(2026, 9, 20), f"Expected 2026-09-20, got {d1}"

    d2 = parse_indonesian_date("15 Oktober 2026")
    assert d2 == datetime(2026, 10, 15), f"Expected 2026-10-15, got {d2}"

    d3 = parse_indonesian_date("Batas Akhir Besok")
    assert d3 is None, f"Expected None for invalid string, got {d3}"


def test_noise_filter():
    classifier = CompetitionClassifier()

    noise_sample = {
        "title": "Lowongan Kerja Software Engineer PT Maju Mundur",
        "description": "We are hiring fresh graduate backend developer",
    }
    res = classifier.classify(noise_sample)
    assert not res["is_competition"], "Noise item should be rejected"
    assert res["status_color"] == "RED"


def test_majors_classification():
    classifier = CompetitionClassifier()

    # 1. Tech Hackathon
    tech_sample = {
        "title": "National Hackathon & Competitive Programming 2026",
        "description": "Lomba web development dan coding competition tingkat nasional untuk mahasiswa.",
    }
    res_tech = classifier.classify(tech_sample)
    assert res_tech["is_competition"]
    assert "Teknik Informatika" in res_tech["jurusan"]
    assert res_tech["confidence"] >= 0.85
    assert res_tech["status_color"] == "GREEN"

    # 2. Business Plan
    biz_sample = {
        "title": "Business Plan Competition INSYS FEST 2026",
        "description": "Kompetisi business plan, startup pitch dan proposal kewirausahaan mahasiswa.",
    }
    res_biz = classifier.classify(biz_sample)
    assert res_biz["is_competition"]
    assert "Manajemen Bisnis" in res_biz["jurusan"]
    assert res_biz["confidence"] >= 0.85

    # 3. Law Moot Court
    law_sample = {
        "title": "National Moot Court Competition & Contract Drafting",
        "description": "Kompetisi peradilan semu dan legal opinion fakultas hukum.",
    }
    res_law = classifier.classify(law_sample)
    assert res_law["is_competition"]
    assert "Ilmu Hukum" in res_law["jurusan"]


if __name__ == "__main__":
    test_date_parser()
    test_noise_filter()
    test_majors_classification()
    test_clean_text_for_display()
    print("✓ All self-checks passed successfully.")
