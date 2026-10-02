# 2. Strict Canonical Schema with Pydantic v2

Date: 2026-10-03

## Status

Accepted

## Context

With multiple external scrape providers feeding data into the pipeline, inconsistent data types, missing required fields (e.g. empty titles, broken URLs, malformed deadlines), and heterogeneous structures will degrade classification quality and corrupt downstream Google Sheets / CSV outputs.

We considered:
1. Python standard library dataclasses with manual `__post_init__` checks.
2. Pydantic v2 data models with built-in validation, URL sanitization, and serialization.
3. Unvalidated raw dictionaries with defensive `.get()` lookups.

## Decision

We adopt `pydantic` (v2) to define the canonical model `CompetitionRecord`. All scrapers must emit data conforming to this schema at ingress. Invalid records are quarantined into the error/failed queue rather than poisoning the master dataset.

## Consequences

### Positive
- Strict guarantees that downstream consumers (classifier, deduplicator, Google Sheets syncer) receive well-typed data.
- Built-in type coercion and validation error messages that guide open-source contributors when writing new scrapers.
- Automated JSON Schema export for API and documentation generation.

### Negative
- Adds `pydantic` as an external dependency in `requirements.txt`.
