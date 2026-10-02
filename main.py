"""Main orchestrator for Competition Hub multi-source pipeline."""

import argparse

from src.classifier import CompetitionClassifier
from src.config import MAX_ITEMS_PER_RUN, setup_logger
from src.deduplicator import Deduplicator
from src.models import CompetitionRecord
from src.sheets_sync import SheetsSync
from src.sources import ACTIVE_SOURCES

log = setup_logger("compScraper")


def run_pipeline(limit: int = MAX_ITEMS_PER_RUN, dry_run: bool = False, source_filter: str | None = None):
    log.info("=== Competition Hub Pipeline Starting ===")
    log.info(f"Active registered providers: {[s.source_id for s in ACTIVE_SOURCES]}")

    # Step 1: Ingest raw candidates across active scraper providers
    raw_records: list[CompetitionRecord] = []
    items_per_source = max(1, limit // len(ACTIVE_SOURCES)) if ACTIVE_SOURCES else limit

    for scraper_cls in ACTIVE_SOURCES:
        if source_filter and scraper_cls.source_id != source_filter:
            continue

        try:
            scraper = scraper_cls()
            log.info(f"Running scraper provider: {scraper.source_name} ({scraper.source_id})")
            items = scraper.scrape(max_items=items_per_source)
            raw_records.extend(items)
        except Exception as e:
            log.error(f"Scraper [{scraper_cls.source_id}] encountered an error: {e}", exc_info=True)

    if not raw_records:
        log.info("No records collected across all providers this run.")
        return

    log.info(f"Total raw records gathered: {len(raw_records)}")

    # Step 2: Cross-Source Deduplication
    deduplicator = Deduplicator()
    unique_candidates = deduplicator.filter_and_register(raw_records)
    log.info(f"Remaining novel records after cross-source deduplication: {len(unique_candidates)}")

    if not unique_candidates:
        log.info("All gathered records were duplicates of existing competitions.")
        return

    # Step 3: Classification (Layer 1: Noise Filter, Layer 2: 15 Majors Keyword Scoring)
    classifier = CompetitionClassifier()
    enriched_records: list[CompetitionRecord] = []

    for item in unique_candidates:
        enriched = classifier.enrich_record(item)
        if not enriched:
            log.info(f"Filtered noise [{item.id}]: {item.title}")
            continue

        enriched_records.append(enriched)
        log.info(
            f"Classified [{enriched.id}]: {enriched.jurusan} (Conf: {enriched.confidence:.2f}, Status: {enriched.status_review.value})"
        )

    log.info(f"Total valid competitions ready for audit: {len(enriched_records)}")

    # Step 4: Sync to Sheets, Local CSV, JSON & Digest
    if dry_run:
        log.info("Dry-run mode active. Skipping Sheets sync and local export.")
        return

    syncer = SheetsSync()
    synced_count = syncer.sync_to_audit_tab(enriched_records)
    log.info(f"Synced {synced_count} records to Tab Audit and local storage.")
    log.info("=== Pipeline Completed Successfully ===")


def main():
    parser = argparse.ArgumentParser(description="Competition Hub Multi-Source Scraper & Classifier")
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_ITEMS_PER_RUN,
        help="Max new events to scrape and process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and classify without syncing or writing outputs",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Run only a specific source_id (e.g. infolomba)",
    )
    args = parser.parse_args()
    run_pipeline(limit=args.limit, dry_run=args.dry_run, source_filter=args.source)


if __name__ == "__main__":
    main()
