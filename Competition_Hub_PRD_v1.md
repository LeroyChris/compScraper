# COMPETITION HUB v1.0

## Otomatisasi Pipa Data Informasi Kompetisi Multi-Fakultas

**SGA Cakrawala University | Divisi ICD Subdivisi Lomba**

---

## Metadata Dokumen

| Item | Nilai |
|------|-------|
| Versi Dokumen | v1.0 (Minimal Viable Product) |
| Tanggal | 19 September 2026 |
| Scope | Minggu I - Implementasi |
| Target Launch | Akhir minggu ini |
| Biaya Operasional | Rp 0 (Free Tier) |

---

## 1. RINGKASAN EKSEKUTIF

**Competition Hub** adalah sistem otomatisasi penjaring informasi lomba yang dirancang untuk mengeliminasi beban pencarian manual tim Subdivisi Lomba SGA Cakrawala University. Sistem akan beroperasi 24/7 di latar belakang, menyisir sumber data terpercaya, mengklasifikasi lomba secara otomatis ke 15 jurusan, dan menyajikan hasil audit internal dalam waktu **5 menit seminggu**.

### Key Metrics v1

| Metrik | Target v1 | Dampak |
|--------|-----------|--------|
| Waktu Pencarian Manual | ~3 jam/minggu/orang | → 5-10 menit/minggu/orang |
| Sumber Data Otomatis | 3-5 sumber stabil | Crawling 24/7 tanpa henti |
| Jumlah Lomba/Minggu | 15-25 item | Semua 15 jurusan tercakup |
| Tingkat Presisi | >80% | Human-in-the-loop audit |
| Cost of Infrastructure | Rp 0 | Gratis (Free Tier) |

### Dari: Manual Crawling → Ke: Automated Curation

Perubahan fundamental adalah shift dari model "setiap orang cari 2 lomba per minggu" menjadi "sistem otomatis menemukan, sistem filter mengklasifikasi, tim hanya perlu audit 5 menit". Ini mengubah tugas kognitif dari labour-intensive pencarian menjadi quality-control yang ringan.

---

## 2. LATAR BELAKANG & MASALAH

### 2.1 Konteks Organisasi

SGA Cakrawala University dengan 15 jurusan aktif memiliki misi mendukung prestasi akademis dan non-akademis mahasiswa. Salah satu pilar utamanya adalah **Divisi ICD Subdivisi Lomba** yang bertanggung jawab menyebarkan informasi peluang kompetisi kepada mahasiswa.

### 2.2 Tiga Masalah Utama (Bottleneck)

#### **Masalah 1: Saturasi & Kelelahan Tim**

Setiap anggota Subdivisi Lomba dituntut mencari minimal **2 lomba per minggu secara manual** (scrolling media sosial, browsing Google, menelusuri website). Ini memakan ~3 jam per minggu per orang, sangat melelahkan, dan rawan human error:
- Lomba terlewat karena deadline keburu
- Informasi salah atau link mati
- Copy-paste manual → typo, duplikasi

#### **Masalah 2: Ketimpangan Sebaran Informasi**

Dengan 15 jurusan yang sangat berbeda (dari Tech, Engineering, Bisnis, hingga Hukum dan Seni), pencarian manual **bias ke sektor tertentu**:
- Terlalu banyak lomba IT atau bisnis
- Lomba untuk rumpun Hukum, Teknik Lingkungan, Psikologi sering terlewat
- Mahasiswa dari jurusan tertentu merasa "diabaikan"

#### **Masalah 3: Skalabilitas Data Lambat**

Master Data Lomba sudah tersedia dan terstruktur baik, tetapi proses pengisian menggunakan **copy-paste manual**:
- Tidak ada feedback loop otomatis dari sumber eksternal
- Volume data berkembang lambat
- Kebergantungan pada keaktifan individual anggota

### 2.3 Implikasi Jangka Panjang

Jika masalah ini dibiarkan:
- Kualitas informasi akan menurun
- Kepercayaan mahasiswa terhadap Subdivisi Lomba melemah
- Setiap pergantian kepengurusan dihadapkan pada tugas yang sama tanpa peningkatan efisiensi
- Asset digital organisasi tidak terwariskan dengan baik

---

## 3. VISI SOLUSI & ARSITEKTUR

### 3.1 Visi Utama: Shift dari Pencarian ke Kurasi

**Alih-alih tim mencari data, sistem yang mencari data. Tim bertugas mengaudit dan memvalidasi.**

Target: waktu kerja turun dari **3 jam/minggu menjadi 5-10 menit/minggu** per orang.

### 3.2 Alur Kerja Sistem (High-Level)

```
[INTERNET / SUMBER LUAR]
    ↓
[MESIN PENJARING OTOMATIS] (Crawling 3-5 sumber web)
    ↓
[SISTEM FILTER JURUSAN] (Kategorisasi otomatis + LLM untuk kasus ambigu)
    ↓
[TAB AUDIT INTERNAL] (Antrean yang sudah terfilter)
    ↓
[TOMBOL APPROVE TEAM] (5 menit review)
    ↓
[SHEET MASTER DATA LOMBA] (Otomatis masuk, langsung ke siswa)
```

### 3.3 Komponen Utama Sistem

#### **Crawler/Scraper**
Google Apps Script atau Python script (GitHub Actions) yang otomatis menyisir 3-5 sumber web (portal kampus, situs agregator lomba, Google Alerts) setiap hari.

#### **Klasifikasi Otomatis**
Tiga lapis filter:
1. **Regex/keyword** untuk hapus noise
2. **Kamus keyword terbobot** per jurusan
3. **LLM untuk item ambigu**

Output: JSON terstruktur dengan jurusan relevan + confidence score.

#### **Tab Audit Internal**
Google Sheet khusus dengan kolom pre-filled (judul, link, jurusan terdeteksi, confidence, deadline). Berwarna: hijau (high confidence), kuning (perlu review), merah (rejected).

#### **Tombol Approve**
Google Apps Script menu yang memungkinkan tim:
- Approve row tertentu
- Reject
- Edit manual

Satu klik → data langsung pindah ke Master Data Lomba.

---

## 4. SCOPE v1: FITUR & PRIORITAS

### 4.1 Yang Termasuk v1 (MVP)

✅ Crawling otomatis dari 3-5 sumber stabil (portal kampus, agregator, Google Alerts)
✅ Klasifikasi dua-lapis (regex keyword + kamus terbobot per 15 jurusan)
✅ Tab Audit dengan UI sederhana (bisa di-klik untuk approve/reject)
✅ Otomatis sync hasil approved ke Master Data Lomba
✅ Deduplikasi dasar (hash URL)
✅ Scheduler harian (waktu eksekusi menyesuaikan dengan free tier limits)

### 4.2 Yang TIDAK Termasuk v1 (Backlog v2+)

❌ Scraping Instagram atau sosial media (risiko ToS, prioritas rendah untuk v1)
❌ Intake via Telegram bot (akan ditambah setelah core system stabil)
❌ Fuzzy matching canggih untuk deduplikasi (implementasi dasar sudah cukup)
❌ Integrasi dengan sistem LMS atau notification otomatis ke mahasiswa
❌ Dashboard analytics dan reporting (akan ditambah setelah 2-3 minggu data terkumpul)
❌ Multi-language support

### 4.3 Prioritas Fitur

| Level | Fitur | Timeline |
|-------|-------|----------|
| **P0 (Critical)** | Crawling stabil + Tab Audit + Approve button | Hari 1-3 |
| **P1 (High)** | Klasifikasi 2-lapis + deduplikasi | Hari 4-5 |
| **P2 (Medium)** | Manual edit di Tab Audit + normalisasi deadline | Hari 5-6 |
| **P3 (Nice-to-have)** | Auto-expiry + metrik tracking | Hari 7 atau v1.1 |

---

## 5. STRATEGI TEKNIS (PILIHAN YANG DIPUTUSKAN)

### 5.1 Sumber Data: Web/Dokumen Only (NO Instagram Scraping)

#### Keputusan
✅ v1 fokus **100% pada web crawling** dari sumber stabil. Instagram scraping **ditolak** untuk v1.

#### Alasan

1. **Scraping IG melanggar ToS**
   - Risiko suspend akun organisasi sangat tinggi
   - Tidak ada API resmi untuk crawl akun pihak ketiga

2. **Graph API IG terbatas**
   - Hanya bisa akses akun bisnis milik sendiri
   - Tidak bisa akses akun penyelenggara lomba

3. **Anti-bot layer IG berubah cepat**
   - Scraper bisa mati dalam 2-6 minggu
   - Maintenance cost tinggi untuk tim yang awam koding

#### Sumber Data Prioritas v1

| Sumber | Deskripsi |
|--------|-----------|
| **Portal Kampus (.ac.id)** | Situs resmi universitas + pengumuman acara akademik |
| **Google Programmable Search Engine** | JSON API dengan query keyword per jurusan + date filter |
| **Agregator Lomba Nasional** | Situs yang punya struktur HTML konsisten (e.g., kompetisio.com) |
| **Google Alerts Feed** | Keyword-based alerts yang diarahkan ke email khusus, dibaca sistem |

#### Rencana untuk Instagram (v2+)

**Intake terbantu manusia:**
- Buat Telegram bot atau Google Form sederhana
- Anggota/mahasiswa yang melihat lomba di IG tinggal forward link + screenshot
- Sistem yang parse dan klasifikasi, bukan yang cari
- Ini mengubah tugas dari "cari" menjadi "forward", jauh lebih murah energi

### 5.2 Arsitektur & Stack: Google Apps Script + GitHub Actions

#### Pilihan Utama: Google Apps Script

**Keuntungan:**
- ✅ Gratis selamanya (termasuk trigger time-driven dan UrlFetchApp)
- ✅ Akses native ke Google Sheets tanpa OAuth setup rumit
- ✅ Tidak perlu infrastruktur eksternal, tidak perlu server
- ✅ Non-teknis bisa edit script langsung di Extensions → Apps Script
- ✅ Tombol approve, custom menu, bisa dikode di file yang sama dengan data
- ✅ Skalabilitas cukup untuk puluhan item per minggu

**Limitasi & Mitigasi:**

| Limitasi | Mitigasi |
|----------|----------|
| **Kuota runtime** (~6 jam/hari per project) | Crawling dijadwalkan batch kecil bertahap |
| **Timeout per eksekusi** (Max 6 menit per run) | URL fetch dibatasi, dibagi ke trigger terpisah |
| **Rate limiting** | Request ke sumber eksternal diberi delay; respect robots.txt |

#### Hybrid Option (Jika crawling berat)

**GitHub Actions (Python scraper) untuk crawling + Apps Script untuk audit UI dan sync ke Master:**

- GitHub Actions punya free tier ~2000 menit/bulan
- Cukup untuk job 10 menit per hari
- ⚠️ **Perhatian:** Scheduled workflow otomatis dinonaktifkan jika repo 60 hari tanpa aktivitas (disable saat archive semester)

### 5.3 Klasifikasi Otomatis: Tiga Lapis, Deterministik Dulu

Melempar semua teks berantakan ke LLM mahal dan lambat. Pakai pipeline bertingkat untuk akurasi tinggi dan efisiensi biaya.

#### Lapis 1: Filter Kasar (Regex/Keyword)

Hapus noise: lowongan kerja, webinar berbayar, event expired.

**Cutting:** 60-80% trash items dihilang dengan cost Rp 0.

**Contoh regex patterns:**
```regex
/(job|lowongan|hiring|aplikasi|beasiswa)/i  → Hapus (bukan lomba)
/(seminar|webinar|workshop|training|kursus)/i  → Hapus (bukan lomba)
/(deadline|registrasi|pendaftaran).*(lalu|lewat|hangus|expired|selesai)/i  → Hapus (expired)
```

#### Lapis 2: Kamus Keyword Terbobot per Jurusan

Susun spreadsheet: setiap jurusan punya daftar keyword dengan skor bobot.

**Cara Kerja Scoring:**
- Untuk setiap item lomba, hitung total skor per jurusan
- Contoh: item berjudul "Kompetisi Datathon Nasional 2026"
  - Skor rumpun Tech: "datathon"(40) + "kompetisi"(generic, 0) = **40 pts**
  - Rumpun lain: <20 pts
  - Output: "Sains Data" dengan skor 40, confidence 75%
- Ambang minimum: **20 pts** untuk include di list jurusan relevan

**Output:** JSON dengan jurusan relevan + confidence score

#### Lapis 3: LLM untuk Item Ambigu

Hanya item yang skor rendah atau menyebar merata yang masuk ke LLM.

**Cutting:** Cukup 10-20% volume total.

**Prompt template:**
```
Analisis teks lomba berikut dan tentukan jurusan relevan dari 15 jurusan ini:
[list 15 jurusan]

Teks: {title dan description}

Respond ONLY dalam JSON format:
{
  "is_competition": true/false,
  "jurusan_relevan": ["Jurusan A", "Jurusan B"],
  "confidence": 0.85,
  "deadline": "2026-10-15",
  "biaya": "gratis|bayar|tidak jelas",
  "reason": "singkat menjelaskan alasan"
}
```

#### Output Klasifikasi

Setiap item di Tab Audit diberi label warna:
- 🟢 **Hijau** (confidence >85%) → Bisa auto-approve
- 🟡 **Kuning** (confidence 50-85%) → Perlu manual review
- 🔴 **Merah** (confidence <50%) → Rejected atau TBD

Auditor fokus ke kuning dulu, baru merah kalau ada waktu.

---

## 6. DESIGN & USER FLOW

### 6.1 Struktur Sheet: Tab Audit vs Master

#### Tab Audit (Internal Processing Queue)

| Kolom | Tipe | Disi Oleh | Fungsi |
|-------|------|-----------|--------|
| ID | Auto | System | Unique identifier, buat deduplikasi |
| Judul Lomba | Text | System | Parsed dari sumber, bisa diedit |
| Link Resmi | URL | System | URL sumber utama, untuk verifikasi |
| Sumber | Text | System | Nama situs crawled (e.g., "portal.ui.ac.id") |
| Jurusan (Auto) | Text | System | Hasil klasifikasi otomatis |
| Confidence | Number | System | Skor 0-100, determine warna |
| Deadline | Date | System | Parsed atau manual kalau gagal |
| Biaya | Text | System | "Gratis", "Bayar", "TBD" |
| Status | Dropdown | Manual | Approve / Reject / Hold |
| Catatan Auditor | Text | Manual | Perlu diedit karena...? |
| Tanggal Audit | Date | System | Timestamp saat approved |
| Approved By | Text | System | Nama auditor yang approve |

#### Tab Master Data Lomba (Public Feed)

Sudah ada, struktur tetap sama. Setelah item approved di Tab Audit, row baru otomatis ditambahkan ke tab ini.

**Untuk auto-sync:** Gunakan Apps Script yang membaca Tab Audit status='Approve' dan melakukan INSERT ke Master.

### 6.2 User Flow: Audit & Approve (5 menit/minggu)

#### Step 1: Sistem Crawl (Background)
Setiap hari pagi, sistem crawl 3-5 sumber, parse, klasifikasi, tambah ke Tab Audit.

#### Step 2: Auditor Buka Tab Audit
Tim Subdivisi Lomba setiap hari Jumat (atau sesuai jadwal) buka Sheet, lihat Tab Audit.

#### Step 3: Scan Warna & Read Kuning Dulu
- Cepat scan: baris hijau (confidence >85%) accept en-masse dengan checkbox
- Baris kuning (50-85%) dibaca satu-satu
- Baris merah diabaikan kecuali ada insight khusus

#### Step 4: Edit Manual Kalau Perlu
- Judul berantakan? Edit inline di sheet
- Deadline salah parse? Correct it
- Terus klik approve

#### Step 5: Klik 'Approve Checked Rows' (Custom Button)
Apps Script button di menu:
- Ambil semua row status='Approve'
- Deduplikasi
- Insert ke Master
- Hapus dari Tab Audit (atau archive)

#### Step 6: Selesai
Master sudah updated, siap dilihat mahasiswa.

**Target durasi:** 5-10 menit per minggu (hanya untuk kuning rows). Hijau rows bisa auto-approve dalam batch.

---

## 7. SUCCESS METRICS

Sistem sukses jika mencapai metrik-metrik di bawah. Tracking dilakukan setiap minggu.

### Uptime Sistem
**Target:** 95% crawl job berhasil (tidak error)
- Tracked: log eksekusi Apps Script/GitHub Actions

### Volume Lomba/Minggu
**Target:** 15-25 item valid masuk Master per minggu di v1
- Index: unique items (setelah deduplikasi) yang approved

### Sebaran per Jurusan
**Target:** Minimal 10 dari 15 jurusan punya lomba setidaknya 1x per 2 minggu
- Tracked: histogram jurusan di Master data

### Precision (Tidak ada item sampah)
**Target:** >80% item di Master tidak ada keluhan mahasiswa tentang link mati atau info salah
- Measured: feedback form simpel atau support ticket count

### Audit Speed
**Target:** Waktu aktual audit kurang dari 10 menit per minggu
- Tracked: timestamp audit vs jumlah row reviewed

### Cost
**Target:** Biaya operasional tetap Rp 0 (hanya free tier)
- Backup: Jika butuh LLM API, kurang dari Rp 10k/minggu

---

## 8. RISK & MITIGATION

### 🚨 Source Blocking / IP Blacklist

**Potensi:** Jika crawl terlalu agresif, sumber bisa block IP.

**Mitigation:**
- Jeda antar request 2-5 detik
- Respect robots.txt
- Pakai User-Agent jujur dengan nama organisasi + kontak
- Mulai dengan 1 request/jam per sumber, naikkan kalau stabil

### 🚨 Penurunan Precision LLM

**Potensi:** Teks lomba berantakan, LLM bingung jurusan mana.

**Mitigation:**
- 70% rely pada kamus keyword
- LLM hanya untuk 30% ambigu
- Catat false positive, update kamus berdasarkan error pattern

### 🚨 Deadline Parse Gagal

**Potensi:** Parsing otomatis deadline "Batas akhir bulan ini" ke date format sulit.

**Mitigation:**
- Jika parse fail dengan confidence <70%, tandai manual (string 'TBD' atau 'CHECK')
- Auditor baca caption, fill manual
- Better slow-but-right daripada deadline salah

### 🚨 Deduplikasi Tidak Sempurna

**Potensi:** Satu lomba ada di 3 sumber, tapi link berbeda (vanity URL) → tercatat 3x di Master.

**Mitigation:**
- Minimal: hash URL terburuknya
- Better: fuzzy match judul dengan token overlap >70%
- Built-in v1.1 kalau ada issue

### 🚨 Repository Hilang (GitHub)

**Potensi:** Kalau pakai GitHub Actions dan repo dihapus, scraper mati.

**Mitigation:**
- Docs jelas dimana script disimpan
- Backup copy di Divisi
- Better: pakai Apps Script sebagai primary (aman di akun Google Sheets)

### 🚨 Burnout Tim Audit

**Potensi:** Seminggu lewat, antrean tab audit penuh 100 row.

**Mitigation:**
- Auto-delete atau archive row yang sudah masuk Master >1 minggu
- Confidence score tinggi langsung auto-approve
- Kurangi manual beban

---

## 9. TIMELINE & MILESTONE

**Target:** v1 fully functional (basic crawl + audit + approve) dalam **7 hari (minggu ini)**.

| Day | Milestone | Deliverable | Owner |
|-----|-----------|-------------|-------|
| 1-2 | Setup & Design | Sheet template + Script skeleton + Source list | Tech Lead |
| 3 | Crawling v1 (1 sumber) | Script fetch dari 1 sumber, parse basic | Developer |
| 4 | Klasifikasi Lapis 1-2 | Regex filter + Kamus keyword 15 jurusan | Tech + Domain |
| 5 | Tab Audit UI + Button | Tab Audit lengkap + Custom menu approve/reject | Developer |
| 6 | Sync ke Master + Testing | Auto-sync + end-to-end test, crawl 2-3 sumber | QA |
| 7 | Polish & Docs | Error handling, limit tuning, runbook, launch | Tech + Team |

### Day 7 Acceptance Criteria

✅ Minimal 1 sumber crawl berhasil 2x per hari tanpa error
✅ Tab Audit punya >10 item dengan classification + color coding
✅ Approve button fungsi: row masuk Master, dihapus dari Audit
✅ Manual: 3 orang bisa audit 10 row dalam 5 menit
✅ Dokumentasi lengkap untuk handoff ke kepengurusan depan

### Post-v1 (Roadmap v1.1+)

- **Week 2-3:** Tambah sumber #4-5, LLM integration, fuzzy deduplikasi
- **Week 4:** Telegram intake bot, auto-expiry logic, dashboard analytics
- **Month 2:** Instagram intake (manual forwarding), advanced filtering, integration dengan sistem notifikasi mahasiswa

---

## 10. APPENDIX: KAMUS KEYWORD & SKEMA TAB AUDIT

### A. Kamus Keyword Terbobot per Jurusan (Contoh)

Berikut contoh untuk 4 rumpun jurusan (dari 15 total). Full list akan diperluas di sprint pertama berdasarkan feedback auditor.

#### RUMPUN TECH & AI
```
"data science" = 50 pts
"machine learning" / "AI" = 50 pts
"datathon" / "hackathon" = 40 pts
"analytics" = 30 pts
"kaggle" = 30 pts
"big data" = 35 pts
"deep learning" = 40 pts
```

#### RUMPUN ENGINEERING
```
"civil engineering" = 50 pts
"bridge design" = 40 pts
"infrastructure" = 35 pts
"sustainability" = 25 pts
"teknik sipil" = 50 pts
"structural design" = 45 pts
"environmental engineering" = 45 pts
```

#### RUMPUN BISNIS & FINANSIAL
```
"business case" / "case competition" = 50 pts
"financial modeling" = 45 pts
"entrepreneurship" / "startup" = 40 pts
"business plan" = 40 pts
"pitch competition" = 35 pts
"investment" = 30 pts
"consulting case" = 40 pts
```

#### RUMPUN HUKUM
```
"moot court" / "legal" = 50 pts
"contract drafting" = 45 pts
"constitutional law" = 40 pts
"legislative drafting" = 35 pts
"law competition" = 35 pts
"arbitration" = 40 pts
"legal opinion" = 35 pts
```

### B. Contoh JSON Output Klasifikasi (Structured)

```json
{
  "id": "comp_20260919_001",
  "title": "Kompetisi Case Bisnis Nasional 2026",
  "source_url": "https://bca-challenge.id/case-2026",
  "source_name": "bca-challenge.id",
  "is_competition": true,
  "classification_method": "keyword_layer_2",
  "confidence": 0.88,
  "jurusan_relevan": [
    {
      "name": "Manajemen Bisnis",
      "score": 45
    },
    {
      "name": "Akuntansi",
      "score": 30
    }
  ],
  "deadline_parsed": "2026-11-30",
  "cost": "gratis",
  "description_excerpt": "Kompetisi case bisnis tingkat nasional untuk mahasiswa S1 dan S2...",
  "flag_for_review": false,
  "reason": "High confidence match dengan keyword 'case competition' dan 'business'"
}
```

### C. Checklist Pre-Launch (Day 7)

- [ ] Sheet template siap dengan 3 tab: Audit, Master, Settings
- [ ] Apps Script / Scraper sudah berjalan di 1-2 sumber, test <24 jam
- [ ] Classifier layer 1-2 beroperasi, manual test 20 item
- [ ] Tab Audit punya custom button 'Approve Checked' dan 'Reject'
- [ ] Sync ke Master tested: 5 item approve → 5 item tambah ke Master
- [ ] Deduplikasi basic (hash URL) berfungsi
- [ ] Dokumentasi: Cara menambah sumber, cara edit kamus, troubleshooting
- [ ] Runbook: Step-by-step audit untuk tim non-teknis
- [ ] Backup: Copy script, copy kamus ke doc terpisah
- [ ] Owner assigned: Siapa yang maintain di minggu 2+?
- [ ] Test dengan tim: Simulasi audit 5 menit, feedback final

---

## Catatan Akhir

Dokumen ini adalah Product Requirements Document (PRD) untuk v1.0 Competition Hub. Revisi berdasarkan feedback dari forum tech dan leadership diharapkan.

**Approval final dari Head of Division sebelum eksekusi dimulai.**

---

**Last Updated:** 19 September 2026

**Document Type:** Product Requirements Document (PRD)

**Intended Audience:** Tech Team, Leadership, Subdivisi Lomba Team
