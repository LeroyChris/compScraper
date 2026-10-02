# Panduan Kontribusi (Contributing Guide)

Terima kasih atas minat Anda berkontribusi pada **Competition Hub Scraper (`compScraper`)**! 

Proyek ini dibangun dengan arsitektur modular **Provider Plugin** agar siapapun dapat dengan mudah menambahkan sumber perayap (scraper) baru untuk portal universitas, agregator kompetisi, atau situs kementerian, serta memperkaya sistem klasifikasi jurusan.

---

## 3 Area Utama Kontribusi

1. **Menambahkan Sumber Scraper Baru** (misal: Puspresnas, Diktiristek, portal lomba UI/ITB/UGM).
2. **Memperkaya Kamus Keyword & Akronim Jurusan** (`data/keywords.json`).
3. **Meningkatkan Filter Noise & Logika Deduplikasi**.

---

## 1. Menambahkan Sumber Scraper Baru (Plugin Pattern)

Setiap scraper sumber baru diisolasi sebagai modul mandiri di folder `src/sources/`.

### Langkah-langkah Pembuatan Scraper:

1. **Buat file provider baru**: `src/sources/<nama_sumber>.py`.
2. **Inherit dari `BaseScraper`**:
   ```python
   from src.models import CompetitionRecord, sanitize_text
   from src.sources.base import BaseScraper

   class MyCampusScraper(BaseScraper):
       source_id = "mycampus"
       source_name = "Portal Lomba Kampus"
       base_url = "https://lomba.kampus.ac.id"

       def scrape(self, max_items: int = 25) -> list[CompetitionRecord]:
           records = []
           # Implementasi fetch & parse
           # Kembalikan daftar instance CompetitionRecord
           return records
   ```
3. **Patuhi Skema Kanonikal (`CompetitionRecord`)**:
   Output wajib menghasilkan objek `CompetitionRecord` yang valid (`src/models.py`). Field otomatis dinormalisasi (emoji dihapus, spasi dibersihkan).
4. **Daftarkan di `src/sources/__init__.py`**:
   Tambahkan class scraper Anda ke list `ACTIVE_SOURCES`:
   ```python
   from src.sources.mycampus import MyCampusScraper

   ACTIVE_SOURCES: list[type[BaseScraper]] = [
       InfolombaScraper,
       MyCampusScraper,
   ]
   ```
5. **Wajib Menyertakan Offline Contract Fixture**:
   - Simpan sample file HTML/JSON statis di `tests/fixtures/<nama_sumber>/`.
   - Buat unit test di `tests/` yang memverifikasi bahwa parser Anda berhasil memetakan fixture statis tersebut menjadi `CompetitionRecord` tanpa melakukan network call ke internet saat CI GitHub Actions berjalan.

---

## 2. Memperbarui Kamus Jurusan & Akronim

Kamus berada di `data/keywords.json`.
- Sistem menggunakan pencocokan **Word Boundary (`\b`)** otomatis, sehingga aman menambahkan akronim pendek (seperti `BPC`, `BCC`, `CP`, `CTF`, `UI/UX`, `BIM`).
- Pastikan kata kunci ditulis dalam huruf kecil (`lowercase`).
- Rentang bobot rekomendasi:
  - `50`: Sangat spesifik untuk bidang tersebut (misal: "moot court", "hackathon", "bpc").
  - `40 - 45`: Relevan kuat (misal: "startup pitch", "tax olympiad").
  - `30 - 35`: Istilah pendukung/lintas bidang.

---

## 3. Alur Pengembangan & Pengujian Lokal

1. **Clone & Buat Branch**:
   ```bash
   git checkout -b feat/tambah-scraper-puspresnas
   ```
2. **Setup Lingkungan Virtual & Install Dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Jalankan Linter & Format Checker**:
   ```bash
   ruff check .
   ```
4. **Jalankan Test Suite**:
   ```bash
   pytest tests/
   ```
5. **Test Scraper Secara Terisolasi**:
   ```bash
   python main.py --source infolomba --limit 2 --dry-run
   ```

---

## 4. Checklist Pengajuan Pull Request (PR)

- [ ] Kode baru lolos `ruff check .` tanpa error.
- [ ] Seluruh unit test lolos `pytest tests/`.
- [ ] PR menyertakan fixture HTML statis di `tests/fixtures/` untuk scraper baru.
- [ ] Scraper baru meng-inherit `BaseScraper` dan didaftarkan di `ACTIVE_SOURCES`.
- [ ] Menggunakan pesan commit yang deskriptif (misal: `feat(sources): add puspresnas competition provider`).
