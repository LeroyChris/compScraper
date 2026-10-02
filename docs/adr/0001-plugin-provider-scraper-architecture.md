# 1. Plugin-Based Provider Architecture for Multi-Source Scrapers

Date: 2026-10-03

## Status

Accepted

## Context

The initial implementation coupled crawling logic directly to `infolomba.id` in a single monolithic file. To serve as the primary competition aggregation engine for university teams and allow open-source contributions from other students, the system must accommodate diverse sources (university event portals, government bodies like Puspresnas, and external aggregators) that use different technologies (SSR, AJAX, GraphQL, pagination schemes).

We evaluated three approaches:
1. Declarative scraping (YAML/JSON config-driven)
2. Monolithic unified scraper
3. Abstract BaseScraper provider pattern with isolated source modules and automatic discovery

## Decision

We adopt the Abstract BaseScraper provider pattern (`src/sources/<source_name>.py`). Each source implements a standardized interface (`scrape() -> list[RawCompetitionCandidate]`, `source_id`, rate limit attributes). A provider registry dynamically loads and coordinates all registered scrapers.

## Consequences

### Positive
- Contributors can implement custom scrapers for complex web architectures without modifying core pipeline code.
- Each provider can be tested in total isolation using canned HTML/JSON fixtures without network calls.
- Failure in one provider does not crash the entire crawl pipeline.

### Negative
- Higher initial abstraction overhead compared to a single script.
- Contributors must write Python code rather than simple configuration files.
