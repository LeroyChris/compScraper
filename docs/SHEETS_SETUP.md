# Panduan Pemasangan Menu Otomatis Google Sheets

Panduan ini ditujukan bagi tim Subdivisi Lomba untuk memasang menu **`🏆 Competition Hub`** di Google Sheets agar proses kurasi dan pemindahan lomba ke **Master Data Lomba** dapat dilakukan dengan 1-klik.

---

## Langkah 1: Buka Google Apps Script di Spreadsheet
1. Buka Google Spreadsheet yang digunakan untuk Competition Hub.
2. Di bilah menu atas, klik **Extensions** (Ekstensi) $\rightarrow$ **Apps Script**.
3. Tab editor skrip baru akan terbuka.

## Langkah 2: Salin Kode Skrip
1. Buka file `scripts/Code.gs` dari repositori ini.
2. Salin seluruh isi file tersebut.
3. Hapus kode bawaan di editor Apps Script (`function myFunction() {...}`), lalu tempelkan kode dari `scripts/Code.gs`.
4. Klik tombol **Save** (ikon disket) atau tekan `Ctrl + S`.
5. Beri nama proyek skrip, misalnya: `CompetitionHubAutomation`.

## Langkah 3: Izinkan Hak Akses (Otorisasi Sekali Saja)
1. Muat ulang (*refresh*) halaman Google Spreadsheet Anda di browser.
2. Tunggu 5-10 detik. Di sebelah kanan menu *Bantuan* (*Help*), akan muncul menu baru bernama:
   **`🏆 Competition Hub`**
3. Klik menu **`🏆 Competition Hub`** $\rightarrow$ pilih salah satu aksi (misal: *Batch Approve Semua Hijau*).
4. Google akan memunculkan dialog **Authorization Required** (Perlu Otorisasi):
   - Klik **Continue**.
   - Pilih akun Google Anda.
   - Klik **Advanced** (Lanjutan) di bagian bawah.
   - Klik **Go to CompetitionHubAutomation (unsafe)**.
   - Klik **Allow**.
   *(Catatan: Peringatan ini standar untuk skrip kustom buatan sendiri).*

---

## Cara Penggunaan Sehari-Hari

1. **Batch Approve**:
   - Klik **`🏆 Competition Hub`** $\rightarrow$ **`⚡ Batch Approve Semua Hijau (AUTO_APPROVE)`**.
   - Semua baris yang memiliki tingkat keyakinan tinggi langsung dipindahkan ke tab `Master Data Lomba` secara instan!
2. **Review Baris Tertentu**:
   - Blok baris yang berstatus `PERLU_REVIEW` yang telah Anda setujui.
   - Klik **`🏆 Competition Hub`** $\rightarrow$ **`✅ Approve Baris Terpilih`**.
   - Baris tersebut akan langsung dipindahkan ke `Master Data Lomba`.
3. **Reject Lomba Tidak Relevan**:
   - Blok baris lomba yang ingin dibuang.
   - Klik **`🏆 Competition Hub`** $\rightarrow$ **`❌ Reject Baris Terpilih`**.
   - Baris dipindahkan ke tab `Arsip Reject`.
