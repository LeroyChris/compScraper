"""Unit tests for cross-source deduplication logic."""

import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.deduplicator import (
    Deduplicator,
    are_deadlines_proximate,
    calculate_jaccard_similarity,
    normalize_title_tokens,
)
from src.models import CompetitionRecord


def test_token_normalization():
    t1 = "Lomba Business Plan Competition Nasional 2026"
    tokens1 = normalize_title_tokens(t1)
    assert "business" in tokens1
    assert "plan" in tokens1
    # Stopwords should be removed
    assert "lomba" not in tokens1
    assert "competition" not in tokens1
    assert "2026" not in tokens1


def test_jaccard_similarity():
    s1 = {"business", "plan", "startup"}
    s2 = {"business", "plan", "innovation"}
    sim = calculate_jaccard_similarity(s1, s2)
    # intersection: 2 (business, plan), union: 4 (business, plan, startup, innovation) -> 2/4 = 0.5
    assert abs(sim - 0.5) < 0.01


def test_deadline_proximity():
    assert are_deadlines_proximate("2026-10-15", "2026-10-17") is True
    assert are_deadlines_proximate("2026-10-15", "2026-10-25") is False
    assert are_deadlines_proximate("2026-10-15", None) is True


def test_deduplicator_with_records():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        store_path = Path(tmp.name)
        dedup = Deduplicator(store_file=store_path)

        rec1 = CompetitionRecord(
            id="infolomba_101",
            source_id="infolomba",
            title="National Hackathon Gemastik 2026",
            deadline="2026-11-01",
        )
        rec2 = CompetitionRecord(
            id="puspresnas_202",
            source_id="puspresnas",
            title="Kompetisi Gemastik Hackathon Nasional 2026",  # Same event from another source
            deadline="2026-11-02",
        )
        rec3 = CompetitionRecord(
            id="infolomba_102",
            source_id="infolomba",
            title="Lomba Debat Hukum Nasional 2026",  # Distinct event
            deadline="2026-11-01",
        )

        filtered = dedup.filter_and_register([rec1, rec2, rec3])
        # rec2 should be identified as duplicate of rec1
        assert len(filtered) == 2
        assert filtered[0].id == "infolomba_101"
        assert filtered[1].id == "infolomba_102"


if __name__ == "__main__":
    test_token_normalization()
    test_jaccard_similarity()
    test_deadline_proximity()
    test_deduplicator_with_records()
    print("✓ All deduplication tests passed.")
