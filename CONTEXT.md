# Domain Glossary: Competition Hub (`compScraper`)

## Competition (Kompetisi)
A single verifiable academic or non-academic contest, challenge, or olympiad targeted at university students.

## Canonical Competition Record (Catatan Kompetisi Kanonikal)
The unified, strictly-validated data structure representing a competition regardless of which origin source it was gathered from.

## Scraper Provider (Penyedia Perayap)
An isolated source connector responsible for collecting raw event data from a specific external website or API and mapping it into raw competition candidates.

## Provider Registry (Daftar Sumber Terdaftar)
The explicit registry defining all active, vetted scrape providers eligible for execution in the aggregation pipeline.

## Ingress Validation (Validasi Masuk)
The automated boundary check that rejects or normalizes malformed event data before it reaches the classification or storage pipelines.

## Event Fingerprint (Sidik Jari Acara)
A deterministic signature derived from normalized title tokens and deadline date, used to detect duplicate submissions across multiple distinct scrape providers.

## Cross-Source Deduplication (Deduplikasi Lintas Sumber)
The identity resolution process that determines whether two competition records from distinct sources refer to the same real-world event using title similarity and deadline proximity.

## Offline Contract Fixture (Berkas Uji Tiruan Mandiri)
A recorded sample of static HTML/JSON responses used to verify a scraper's output against the canonical schema without making live network calls.

## Word Boundary Matching (Pencocokan Batas Kata)
A regex-based keyword search pattern enforcing whole-word matching (`\b`) to prevent substring collisions in short acronyms and tokens.

## Noise Filter (Penyaring Derau)
The first-layer gate that filters out non-competition items (such as job vacancies, commercial seminars, webinars, and scholarships).

## Field Scoring (Penilaian Rumpun Jurusan)
The weighted heuristic system that maps a competition's title and description against target university majors.

## Confidence Score & Triage Status (Status Penelaahan)
A quantitative measure of classification certainty that determines the required human review effort (`AUTO_APPROVE`, `PERLU_REVIEW`, or `MANUAL_CHECK`).

## Review Lifecycle (Siklus Penelaahan)
The sequential states an event traverses: `INGESTED` → `TRIAGED` (in Tab Audit) → `APPROVED` (transferred to Master Data) or `REJECTED`.

## Audit Tab (Tab Penelaahan)
The staging area where incoming classified competitions await team inspection before publication.

## Master Data (Data Induk)
The verified, single-source-of-truth registry of active competitions published to university students.

## Ready Digest (Ringkasan Siar)
A concise, structured textual summary per event for rapid sharing into campus messaging channels.
