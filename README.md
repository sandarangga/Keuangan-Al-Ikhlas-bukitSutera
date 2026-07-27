# Dashboard Keuangan Masjid Al Ikhlas

Dashboard interaktif (Streamlit) untuk laporan keuangan DKM Al Ikhlas, dibuat dari file
`Laporan Keuangan Al Ikhlas bulan Juni 2026.xlsx` (ledger transaksi Jan 2019 – Jun 2026).

## Isi folder

- `dashboard.py` — aplikasi Streamlit utama
- `data_loader.py` — pembaca & pembersih data dari Excel (parsing tanggal Indonesia, kategorisasi transaksi, agregasi bulanan, tambah transaksi, export XLSX)
- `auth.py` — password gate admin (dipakai bersama untuk: ganti file laporan, tambah transaksi, input kotak amal)
- `persistence.py` — simpan ledger secara permanen (commit ke GitHub saat online, atau tulis langsung ke file saat dijalankan lokal)
- `data/laporan_keuangan.xlsx` — salinan file sumber
- `requirements.txt` — daftar dependensi Python

## Cara menjalankan

1. Install dependensi (sekali saja):
   ```
   pip install -r requirements.txt
   ```
2. Jalankan dashboard:
   ```
   streamlit run dashboard.py
   ```
3. Browser akan terbuka otomatis di `http://localhost:8501`.

## Fitur

- **KPI ringkas**: saldo terkini, total pemasukan/pengeluaran & arus kas bersih pada periode terpilih, jumlah transaksi.
- **Tren saldo kas** dari waktu ke waktu.
- **Pemasukan vs pengeluaran per bulan** (bar chart) + garis arus kas bersih.
- **Breakdown kategori** — pie chart sumber pemasukan (Kotak Amal, Infaq QRIS, Dana RW, dll) dan kategori pengeluaran (Gaji Marbot, TPA, Listrik, Renovasi, dll).
- **10 transaksi terbesar** (pemasukan & pengeluaran) — tampil persis di bawah ringkasan KPI.
- **Login Admin** (sidebar) — satu password admin yang membuka tiga fitur berikut. Password default: `amalalikhlas26` (lihat `auth.py` untuk cara mengganti; lokal lewat environment variable `KOTAK_AMAL_PASSWORD`, di Streamlit Cloud lewat Settings → Secrets).
  - **Ganti file laporan** (upload `.xlsx` lain)
  - **Tambah Transaksi** — input pemasukan/pengeluaran manual apa saja, langsung tercatat ke ledger untuk sesi berjalan
  - **Input Kotak Amal** (halaman terpisah) — form hitung pecahan uang (Rp100.000 s/d Rp500) seperti rekap kotak amal manual; total otomatis dihitung dan dicatat sebagai transaksi pemasukan dengan keterangan "Pemasukan Kotak Amal" pada tanggal yang dipilih.

  Pengunjung tanpa login tetap bisa melihat seluruh dashboard (grafik, tabel, filter, export) — hanya tiga fitur di atas yang dikunci.
- **Export ke Excel (.xlsx)** — unduh ledger terfilter atau seluruh ledger (termasuk transaksi baru yang sudah diinput) sebagai file Excel yang rapi. CSV tetap tersedia juga.
- **Ganti file** — bisa upload file `.xlsx` laporan bulan lain langsung dari sidebar, tanpa perlu edit kode.

## Menyimpan transaksi secara permanen

Transaksi yang ditambahkan lewat form ("Tambah Transaksi" atau "Input Kotak Amal") awalnya cuma tersimpan di memori sesi Streamlit — hilang kalau di-refresh/logout/app restart. Supaya permanen, admin yang sudah login akan melihat tombol **"💾 Simpan Permanen"** di sidebar.

- **Kalau dijalankan lokal** (`streamlit run dashboard.py` di komputer sendiri): tombol ini langsung menimpa file `data/laporan_keuangan.xlsx` di disk.
- **Kalau di-deploy di Streamlit Community Cloud**: filesystem di sana bersifat sementara (hilang tiap redeploy), jadi tombol ini otomatis commit file yang sudah diperbarui langsung ke repo GitHub lewat GitHub API. Untuk ini, dua Secrets berikut wajib diisi di **Settings → Secrets** app kamu di share.streamlit.io:

  ```
  GITHUB_TOKEN = "ghp_xxx..."
  GITHUB_REPO = "sandarangga/Keuangan-Al-Ikhlas-bukitSutera"
  ```

  (`GITHUB_TOKEN` boleh pakai token classic yang sudah kamu buat sebelumnya, asal masih berlaku dan punya scope `repo`.)

  Setelah "Simpan Permanen" berhasil commit ke GitHub, Streamlit Cloud akan otomatis redeploy dalam 1-2 menit untuk memuat data terbaru — persis seperti kalau kamu `git push` manual.

File yang tersimpan lewat fitur ini memakai format sedikit berbeda dari file laporan bulanan asli (ada sheet bernama "Ledger", header di baris pertama, ada kolom KATEGORI) — `data_loader.py` sudah bisa membaca kedua format itu secara otomatis, jadi tidak masalah.

## Catatan kategorisasi

Kategori transaksi (Gaji, TPA, Listrik & Perawatan, Infaq Ustadz/Khotib, Kotak Amal, Renovasi & Aset, dll)
ditentukan otomatis dari kata kunci di kolom "Keterangan" (lihat `CATEGORY_RULES` di `data_loader.py`).
Kalau ada transaksi yang masuk kategori "Lainnya" dan ingin dikelompokkan lebih spesifik, tambahkan
pattern baru di `CATEGORY_RULES`.
