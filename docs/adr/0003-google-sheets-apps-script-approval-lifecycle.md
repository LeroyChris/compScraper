# 3. Google Sheets In-Sheet Review and Approval via Apps Script

Date: 2026-10-03

## Status

Accepted

## Context

The core objective of the Competition Hub PRD is reducing manual searching while empowering non-technical student reviewers to curate events in under 5 minutes per week. While the Python pipeline ingests and writes candidate events to `Tab Audit`, reviewers need a frictionless mechanism in the Google Sheets web interface to approve or reject events and transfer approved rows to `Master Data Lomba`.

We evaluated:
1. Two-way sync where Python polls Google Sheets for approval marks.
2. CLI-based approval tool requiring student auditors to run terminal commands.
3. Native Google Apps Script menu inside Google Sheets that performs row migration and archiving on click.

## Decision

We provide a versioned Google Apps Script (`scripts/Code.gs`) alongside the repository. It binds a custom menu `🏆 Competition Hub` into the spreadsheet with actions:
- `Approve Baris Terpilih` (Transfers selected rows from `Tab Audit` to `Master Data Lomba` and marks/archives them).
- `Batch Approve Semua Hijau (AUTO_APPROVE)`.
- `Tandai Reject`.

## Consequences

### Positive
- Zero installation or technical barriers for non-technical student reviewers.
- Real-time row movement without waiting for a scheduled Python background sync.
- Code is version-controlled in the repository and easily updated.

### Negative
- Requires a one-time copy-paste into `Extensions → Apps Script` when setting up a new Google Sheet instance.
