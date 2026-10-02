# Competition Hub (`compScraper`)

> Pipeline agregasi otomatis dan kurasi informasi kompetisi mahasiswa multi-jurusan untuk Subdivisi Lomba SGA Cakrawala University.

Sistem ini dirancang untuk memangkas waktu pencarian lomba manual dari **~3 jam/minggu/orang menjadi < 5 menit/minggu**. Sistem mengumpulkan info lomba dari berbagai sumber (multi-provider), menyaring noise, mengklasifikasikan bidang ke 15 jurusan secara otomatis, melakukan deduplikasi lintas sumber, dan menyajikan hasilnya di **Tab Audit Google Sheets** serta file **Ready Digest** lokal siap kirim ke grup kampus.

---

## Arsitektur Pipeline

```
[Sumber Web: infolomba.id, portal kampus, puspresnas, dll]
       │
       ▼
[Provider Plugin Scrapers (src/sources/)]
       │
       ▼ (Ingress Validation via Pydantic v2)
[Deduplication Engine (src/deduplicator.py)]
  ├── Title Token Normalization (Jaccard Similarity)
  └── Deadline Proximity Matching (data/master_competitions.json)
       │
       ▼
[Classifier 2-Lapis (src/classifier.py)]
  ├── Lapis 1: Filter Kasar (Regex: noise / loker / webinar / expired)
  └── Lapis 2: Kamus Terbobot 15 Jurusan (data/keywords.json dengan Word Boundary \b)
       │
       ▼
[Sheets & Digest Sync (src/sheets_sync.py)]
  ├── Google Sheets API (Tab Audit)
  ├── Macro Approval 1-Klik (scripts/Code.gs)
  ├── Fallback Lokal: CSV (Excel UTF-8-SIG) & JSON
  └── Ringkasan Teks Siap Kirim (data/latest_digest.txt)
```

---

## Fitur Utama

- **Arsitektur Provider Plugin**: Setiap sumber lomba dibuat modular di `src/sources/` turunan dari `BaseScraper`. Menambah sumber baru cukup membuat 1 file baru tanpa mengubah kode inti.
- **Validasi Skema Kanonikal (Pydantic v2)**: Menjamin data selalu bersih (emoji dibersihkan, font unik di-normalisasi, URL diverifikasi, deadline ISO).
- **Deduplikasi Cerdas Lintas Sumber**: Mencegah lomba yang sama dari 2 situs berbeda muncul berulang kali di lembar kerja menggunakan *Event Fingerprint* dan *Jaccard Token Similarity*.
- **Klasifikasi Triage 15 Jurusan**: Scoring otomatis dengan regex *word boundary* (`\b`) untuk akurasi tinggi pada akronim (BPC, BCC, CP, CTF, BIM, UI/UX). Menghasilkan status triage:
  - 🟢 `AUTO_APPROVE` (Confidence $\ge 85\%$)
  - 🟡 `PERLU_REVIEW` (Confidence $50\% - 84\%$)
  - 🔴 `MANUAL_CHECK` (Confidence $< 50\%$)
- **Menu Approval 1-Klik di Google Sheets (`scripts/Code.gs`)**: Tim auditor cukup membuka Google Sheets dan mengklik tombol *"Batch Approve Semua Hijau"* untuk memindahkan lomba yang sudah valid ke *Master Data Lomba*.
- **Ready Digest Exporter**: Ringkasan teks format bersih siap kirim di `data/latest_digest.txt` untuk disalin ke grup koordinasi tanpa perlu merapikan format manual.
- **Zero-Crash Fallback**: Berjalan lancar secara lokal tanpa Google Service Account (otomatis menulis output ke CSV dan JSON lokal).
- **Automasi GitHub Actions**: Workflow cron harian pukul 08:00 WIB yang mengumpulkan info lomba, menguji validitas, dan menyimpan state terbaru.

---

## Struktur Folder

```
compScraper/
├── .github/workflows/
│   └── scrape.yml              # Scheduled GitHub Actions runner (linter + test + scrape)
├── data/
│   ├── keywords.json           # Kamus bobot keyword 15 jurusan & regex noise
│   ├── processed_events.json   # State tracking deduplikasi per scraper
│   ├── master_competitions.json # Database kanonikal untuk deduplikasi lintas-sumber
│   ├── failed_queue.json       # Antrean item gagal untuk retry otomatis
│   ├── latest_scraped_output.csv  # Output CSV tabel lengkap (UTF-8-SIG / Excel ready)
│   ├── latest_scraped_output.json # Output JSON lengkap (machine readable)
│   └── latest_digest.txt       # Ringkasan teks bersih siap copas ke chat/medsos
├── docs/
│   ├── adr/                    # Architecture Decision Records (ADR 0001 - 0004)
│   ├── AUDIT_GUIDE.md          # Penjelasan Confidence, Status Review, & SOP 5 Menit
│   ├── SHEETS_SETUP.md         # Panduan pasang menu otomatis 1-klik di Google Sheets
│   └── infolomba_notes.md      # Catatan arsitektur & reverse engineering infolomba
├── scripts/
│   └── Code.gs                 # Google Apps Script macro untuk Google Sheets
├── src/
│   ├── __init__.py
│   ├── classifier.py           # Layer 1 & 2 rule-based classification (\b regex)
│   ├── config.py               # Konfigurasi, paths, & structured logger
│   ├── deduplicator.py         # Cross-source deduplication & fingerprint engine
│   ├── models.py               # Canonical Pydantic v2 data models & text sanitizer
│   ├── scraper.py              # Backward compatibility wrapper
│   ├── sheets_sync.py          # Google Sheets publisher & local persistent merge
│   └── sources/                # Plugin provider directory
│       ├── __init__.py         # Explicit active provider registry
│       ├── base.py             # Abstract BaseScraper contract
│       └── infolomba.py        # Infolomba provider implementation
├── tests/
│   ├── fixtures/               # Offline canned fixtures untuk CI PR validation
│   │   └── infolomba/
│   │       ├── list_page.html
│   │       └── detail_modal.html
│   ├── test_classifier.py      # Uji klasifikasi jurusan & noise filter
│   ├── test_deduplicator.py    # Uji deduplikasi token & deadline proximity
│   └── test_scraper_contract.py # Contract test offline tanpa live HTTP request
├── pyproject.toml              # Definisi dependensi & konfigurasi ruff/pytest
├── CONTRIBUTING.md             # Panduan kontributor untuk menambah scraper baru
├── CONTEXT.md                  # Domain model glossary resmi
├── main.py                     # Entry point CLI orchestrator
└── README.md
```

---

## Panduan Memulai

### 1. Prasyarat
- Python >= 3.10
- Git

### 2. Instalasi
```bash
git clone https://github.com/your-org/compScraper.git
cd compScraper

python3 -m venv .venv
source .venv/bin/activate  # Di Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Konfigurasi Lingkungan (Opsional untuk Google Sheets)
Salin template konfigurasi:
```bash
cp .env.example .env
```
Isi variabel berikut jika ingin langsung sync ke Google Sheet:
- `SPREADSHEET_ID`: ID Google Sheets target.
- `GOOGLE_SERVICE_ACCOUNT_FILE`: Path ke file JSON kredensial Google Service Account.

*(Catatan: Jika tidak dikonfigurasi, pipeline tetap berjalan mulus dan menyimpan data ke `data/latest_scraped_output.csv`, `latest_scraped_output.json`, dan `latest_digest.txt`).*

---

## Penggunaan (CLI)

### Menjalankan pipeline lengkap (seluruh scraper aktif):
```bash
python main.py
```

### Menjalankan hanya untuk sumber tertentu:
```bash
python main.py --source infolomba --limit 10
```

### Menjalankan dry-run (hanya scraping & klasifikasi tanpa menulis data):
```bash
python main.py --dry-run
```

### Menjalankan linter dan test suite:
```bash
ruff check .
pytest tests/
```

---

## Dokumentasi Pendukung
- [Panduan SOP Audit 5 Menit](docs/AUDIT_GUIDE.md)
- [Panduan Pemasangan Menu Google Sheets](docs/SHEETS_SETUP.md)
- [Panduan Menambah Scraper Baru](CONTRIBUTING.md)
- [Architecture Decision Records (ADR)](docs/adr/)
- [Domain Glossary](CONTEXT.md)
