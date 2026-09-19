# Panduan Kontribusi (Contributing Guide)

Terima kasih atas minat Anda berkontribusi pada **Competition Hub Scraper (`compScraper`)**! 

Proyek ini dibuat untuk mendukung mahasiswa menemukan peluang kompetisi yang relevan dan merata di seluruh jurusan.

---

## Cara Berkontribusi

Ada 3 area utama di mana Anda bisa berkontribusi:
1. **Memperbarui / Memperkaya Kamus Keyword Jurusan** (`data/keywords.json`).
2. **Menambahkan Sumber Scraper Baru** (misal: agregator lomba lain, portal kampus `.ac.id`).
3. **Meningkatkan Akurasi Klasifikasi & Filter Noise**.

---

## 1. Menambah / Memperbarui Keyword Jurusan

Kamus jurusan berada di file `data/keywords.json`. 

Format entri:
```json
"Nama Jurusan": {
  "keywords": {
    "istilah kompetisi": 50,
    "istilah sekunder": 40
  }
}
```
- Bobot 50: Sangat spesifik untuk jurusan tersebut (misal: "moot court" untuk Ilmu Hukum).
- Bobot 35-45: Cukup relevan (misal: "ui/ux" untuk Sistem Informasi).
- Pastikan kata kunci ditulis dalam huruf kecil (`lowercase`).

---

## 2. Menambahkan Scraper Sumber Baru

Jika Anda ingin menambahkan sumber web baru:
1. Analisis apakah situs menggunakan SSR (HTML biasa) atau CSR/AJAX API.
2. Buat file baru di `src/scrapers/<nama_sumber>.py` (atau tambahkan class baru).
3. Pastikan output detail sesuai dengan format umum:
   - `event_id`: ID unik sumber
   - `title`: Judul lomba
   - `description`: Deskripsi lengkap
   - `registration_url`: Link pendaftaran atau guidebook
   - `source_url`: URL halaman sumber
   - `source_name`: Nama domain sumber (misal: "kompetisi.id")
   - `deadline`: Format `YYYY-MM-DD` atau `"TBD"`
   - `fee`: Biaya pendaftaran ("Gratis", atau nominal)
4. Patuhi prinsip **Gentle Scraping**:
   - Selalu beri jeda acak 2–4 detik antar request (`time.sleep`).
   - Sertakan `User-Agent` yang jelas.
   - Hormati respons rate limiting (HTTP 429).

---

## 3. Alur Pengembangan (Git Workflow)

1. **Fork & Branch**:
   ```bash
   git checkout -b feat/tambah-sumber-baru
   ```
2. **Setup Lingkungan**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Uji Kode Anda**:
   Pastikan seluruh test lokal lulus sebelum submit PR:
   ```bash
   python tests/test_classifier.py
   ```
4. **Kirim Pull Request (PR)**:
   - Buat judul PR yang deskriptif (misal: `feat(classifier): perbaiki bobot keyword dkv`).
   - Jelaskan perubahan dan lampirkan hasil pengujian singkat.
