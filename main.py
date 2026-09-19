"""Main entry point for Competition Hub scraping and classification pipeline."""

import argparse
import logging
import sys

from src.classifier import CompetitionClassifier
from src.config import MAX_ITEMS_PER_RUN
from src.scraper import InfolombaScraper
from src.sheets_sync import SheetsSync

log = logging.getLogger("compScraper")


def run_pipeline(limit: int = MAX_ITEMS_PER_RUN, dry_run: bool = False):
    log.info("=== Competition Hub Pipeline Starting ===")

    # Step 1: Scrape
    scraper = InfolombaScraper()
    raw_events = scraper.scrape(max_items=limit)
    if not raw_events:
        log.info("No new events collected this run.")
        return

    # Step 2: Classify (Layer 1: Noise Filter, Layer 2: 15 Majors Keyword Scoring)
    classifier = CompetitionClassifier()
    enriched_records = []

    for item in raw_events:
        cls_result = classifier.classify(item)
        if not cls_result["is_competition"]:
            log.info(f"Skipping noise [{item['event_id']}]: {item['title']}")
            continue

        item.update(cls_result)
        enriched_records.append(item)
        log.info(
            f"Classified [{item['event_id']}]: {item['jurusan']} (Confidence: {item['confidence']}, Status: {item['status_color']})"
        )

    log.info(f"Total valid competitions ready for audit: {len(enriched_records)}")

    # Step 3: Sync to Sheets / Local JSON
    if dry_run:
        log.info("Dry-run flag set. Skipping Google Sheets sync.")
        return

    syncer = SheetsSync()
    synced_count = syncer.sync_to_audit_tab(enriched_records)
    log.info(f"Synced {synced_count} records to Tab Audit.")
    log.info("=== Pipeline Completed Successfully ===")


def main():
    parser = argparse.ArgumentParser(description="Competition Hub Scraper & Classifier")
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_ITEMS_PER_RUN,
        help="Max new events to scrape and process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and classify without syncing to Google Sheets",
    )
    args = parser.parse_args()
    run_pipeline(limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
