# Competition Hub Scraper (`compScraper`)

> Pipeline otomatis penjaring informasi kompetisi mahasiswa multi-jurusan untuk Subdivisi Lomba SGA Cakrawala University.

Sistem ini melakukan web scraping dari agregator kompetisi terpercaya, menyaring noise (lowongan kerja, webinar, beasiswa), mengklasifikasikan bidang kompetisi ke 15 jurusan berbasis kamus keyword terbobot, lalu mengekspor hasil ke **Tab Audit** Google Sheets untuk di-review oleh tim dalam 5 menit per minggu.

---

## Arsitektur Pipeline

```
[Sumber Web: infolomba.id]
       │
       ▼
[Scraper Engine (AJAX + Pagination + Exponential Backoff)]
       │
       ▼
[Classifier 2-Lapis]
  ├── Lapis 1: Filter Kasar (Regex: noise / loker / webinar / expired)
  └── Lapis 2: Kamus Terbobot 15 Jurusan (data/keywords.json)
       │
       ▼
[Sheets Sync Module]
  ├── Google Sheets API (Tab Audit)
  └── Fallback: data/latest_scraped_output.json
```

---

## Fitur Utama

- **Paginasi Cerdas**: Scraping dinamis dari SSR (Page 0) hingga POST AJAX `/load-event-2` (Page 1+) sampai batas yang ditentukan.
- **Deduplikasi State**: Melacak status per event ID di `data/processed_events.json` agar tidak terjadi duplikasi scraping.
- **Filter 15 Jurusan**: Scoring otomatis untuk Teknik Informatika, Sistem Informasi, Sains Data, Teknik Sipil, Teknik Mesin, Teknik Elektro, Teknik Lingkungan, Manajemen Bisnis, Akuntansi, Ilmu Hukum, Psikologi, DKV, Ilmu Komunikasi, Farmasi/Kedokteran, dan Sastra/Bahasa.
- **Zero-Crash Fallback**: Berjalan lancar secara lokal tanpa Google Service Account (otomatis menulis output ke JSON lokal).
- **Automasi GitHub Actions**: Workflow cron harian yang otomatis mengikis, mengklasifikasi, dan commit state kembali ke repo.

---

## Struktur Folder

```
compScraper/
├── .github/workflows/
│   └── scrape.yml              # Scheduled GitHub Actions runner
├── data/
│   ├── keywords.json           # Kamus bobot keyword 15 jurusan & regex noise
│   ├── processed_events.json   # State tracking deduplikasi
│   ├── failed_queue.json       # Antrean item gagal untuk retry & debugging
│   ├── latest_scraped_output.csv  # Output CSV tabel lengkap (human readable)
│   └── latest_scraped_output.json # Output JSON lengkap (machine readable)
├── docs/
│   ├── AUDIT_GUIDE.md          # Penjelasan Confidence, Status Review, & SOP 5 Menit
│   └── infolomba_notes.md      # Catatan arsitektur & reverse engineering infolomba
├── logs/
│   ├── scraper.log             # Log aktivitas umum (DEBUG level)
│   └── error.log               # Log kegagalan & stack trace (WARNING/ERROR level)
├── src/
│   ├── __init__.py
│   ├── classifier.py           # Layer 1 & 2 rule-based classification
│   ├── config.py               # Konfigurasi, paths, & setup logging
│   ├── scraper.py              # Infolomba pagination, extraction, & retry engine
│   └── sheets_sync.py          # Sinkronisasi ke Google Sheets & persistent merge
├── tests/
│   └── test_classifier.py      # Assert-based test suite
├── .env.example                # Template variabel lingkungan
├── .gitignore
├── CONTRIBUTING.md             # Panduan kontribusi open source
├── main.py                     # Entry point CLI
├── README.md                   # Dokumentasi utama
├── requirements.txt            # Dependensi Python
├── Competition_Hub_PRD_v1.md   # Product Requirements Document
└── Competition_Hub_PRD_v1.pdf
```

---

## Log & Penanganan Eror (Error Handling)

Sistem dirancang tahan banting dengan pencatatan eror berlapis:
1. **`logs/error.log`**: Menyimpan semua kejadian fatal, timeout, rate limit HTTP 429, atau kegagalan parsing DOM lengkap dengan *timestamp* dan *stack trace*.
2. **`data/failed_queue.json`**: Menyimpan daftar ID lomba yang gagal diambil beserta URL dan alasannya. Item di antrean ini tidak ditandai selesai sehingga dapat di-retry otomatis pada run berikutnya.
3. **`logs/scraper.log`**: Menyimpan histori operasional lengkap untuk monitoring performa scraping.

Untuk detail cara tim menggunakan kolom **Confidence** dan **Status Review** dalam proses kurasi, silakan baca [AUDIT_GUIDE.md](docs/AUDIT_GUIDE.md).

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

*(Catatan: Jika tidak dikonfigurasi, pipeline tetap berjalan dan menyimpan data ke `data/latest_scraped_output.json`).*

---

## Penggunaan (CLI)

### Menjalankan pipeline lengkap:
```bash
python main.py
```

### Membatasi jumlah item baru yang diambil:
```bash
python main.py --limit 10
```

### Menjalankan dry-run (hanya scrape & klasifikasi tanpa update Sheet):
```bash
python main.py --dry-run
```

### Menjalankan tes:
```bash
python tests/test_classifier.py
```

---

## Lisensi & Kontribusi

Silakan baca [CONTRIBUTING.md](CONTRIBUTING.md) untuk panduan menambah sumber scraper baru atau memperbarui kamus jurusan.
