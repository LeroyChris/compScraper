# Panduan Audit Lomba & Penjelasan Kolom

Dokumen ini menjelaskan fungsi kolom **`Confidence`** dan **`Status Review`** pada Tab Audit Google Sheets / file `latest_scraped_output.csv`, serta bagaimana tim Subdivisi Lomba memanfaatkannya untuk memangkas waktu kerja dari **3 jam/minggu menjadi < 5 menit/minggu**.

---

## 1. Mengapa Kolom Ini Sangat Penting?

Sesuai **Competition Hub PRD v1.0 (Bagian 2.2)**, bottleneck terbesar organisasi adalah:
- **Saturasi & Kelelahan Tim**: Membaca puluhan deskripsi lomba secara manual memakan waktu ~3 jam/minggu/orang dan rentan human error.
- **Ketimpangan Jurusan**: Tanpa klasifikasi terstruktur, info lomba cenderung bias ke jurusan tertentu (IT/Bisnis) dan mengabaikan rumpun lain (Hukum, Psikologi, Teknik Sipil, dll).

Jika sheet hanya berisi teks mentah tanpa label prioritas, tim auditor harus membaca ulang seluruh deskripsi lomba satu demi satu. 

**Dengan kolom `Confidence` dan `Status Review`, sistem menerapkan prinsip *Triage* (pemilahan cepat berbasis skor kognitif).**

---

## 2. Definisi & Ambang Batas (Threshold Matrix)

### A. Kolom `Confidence` (0.00 - 1.00)
Menunjukkan probabilitas kepastian kecocokan kompetisi terhadap 15 jurusan berdasarkan kamus keyword terbobot (`data/keywords.json`).

- Setiap kemunculan kata kunci memiliki bobot (20 - 50 poin).
- Skor dinormalisasi terhadap ambang batas kepastian tertinggi.
- Rumus dasar:
  $$\text{Confidence} = \min\left(\frac{\text{Skor Keyword Teratas}}{60}, 0.98\right)$$

---

### B. Kolom `Status Review` (Tindakan Auditor)

Sistem secara otomatis membagi baris audit menjadi 3 status:

| Status Review | Range Confidence | Warna Visual | Arti & Rekomendasi Tindakan | Estimasi Waktu |
| :--- | :---: | :---: | :--- | :---: |
| **`AUTO_APPROVE`** | $\ge 0.85$ | 🟢 Hijau | **Sangat Yakin.** Kata kunci spesifik kuat (misal: *hackathon*, *moot court*, *tax olympiad*). Auditor cukup centang massal (*batch approve*) tanpa membaca teks panjang. | ~30 detik |
| **`PERLU_REVIEW`** | $0.50 - 0.84$ | 🟡 Kuning | **Cukup Yakin tapi Lintas Disiplin.** Lomba memiliki kata kunci relevan namun mungkin melibatkan multi-jurusan (misal: *Business Plan IT* melibatkan Manajemen & Sistem Informasi). Auditor luangkan 10-20 detik untuk memeriksa jurusan yang terdeteksi. | ~2-3 menit |
| **`MANUAL_CHECK`** | $< 0.50$ | 🔴 Merah | **Ambigu / Umum.** Teks deskripsi pendek atau minim keyword teknis (misal: *Lomba Esai Nasional*). Auditor membaca sekilas untuk menentukan jurusan manual, atau biarkan di-reject jika tidak relevan. | ~1-2 menit |

---

## 3. SOP Audit 5 Menit per Minggu

Tim auditor Subdivisi Lomba menjalankan workflow berikut setiap pekan:

1. **Buka Tab Audit** di Google Sheets atau buka file `data/latest_scraped_output.csv`.
2. **Filter Berdasarkan Status**:
   - Filter `AUTO_APPROVE` (Hijau) $\rightarrow$ Klik **Approve All**. Data langsung mengalir ke Master Data Lomba.
   - Filter `PERLU_REVIEW` (Kuning) $\rightarrow$ Baca judul & kolom *Jurusan (Auto)*. Koreksi jika ada jurusan yang kurang sesuai, lalu set status ke **Approve**.
   - Filter `MANUAL_CHECK` (Merah) $\rightarrow$ Abaikan, kecuali ada kuota jurusan yang belum terpenuhi minggu tersebut.
3. **Selesai**: 15–25 lomba baru sudah terkurasi dan terbit ke mahasiswa dalam waktu kurang dari 5 menit.
