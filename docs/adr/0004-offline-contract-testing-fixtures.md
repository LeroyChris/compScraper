# 4. Offline Contract Testing with Static Fixtures

Date: 2026-10-03

## Status

Accepted

## Context

Allowing open-source contributions of new competition scrapers creates a testing challenge. If unit tests in CI make live HTTP calls to target university portals:
1. CI builds fail intermittently due to target server downtime, rate-limiting, or dynamic UI changes.
2. Contributor PRs spam production websites during testing runs.
3. Tests cannot run offline or deterministically.

We considered:
1. Live network tests against production URLs.
2. Mocking via responses/requests-mock inline.
3. Static HTML/JSON fixtures stored under `tests/fixtures/<source_name>/` validated against canonical Pydantic models.

## Decision

Every scraper provider must include recorded static HTML/JSON fixtures in `tests/fixtures/<source_id>/` and a contract test verifying that parsing those fixtures emits valid `CompetitionRecord` instances. Live HTTP requests are strictly prohibited in the CI test suite.

## Consequences

### Positive
- Fully reproducible, lightning-fast offline CI tests.
- Contributor PRs can be safely merged with 100% confidence in schema compliance.
- No risk of IP bans or load generation against external campus websites during CI.

### Negative
- Fixtures must be updated manually if a target website undergoes a structural redesign.
