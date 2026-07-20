# Dashboard Keuangan Masjid Al Ikhlas

Dashboard interaktif (Streamlit) untuk laporan keuangan DKM Al Ikhlas, dibuat dari file
`Laporan Keuangan Al Ikhlas bulan Juni 2026.xlsx` (ledger transaksi Jan 2019 – Jun 2026).

## Isi folder

- `dashboard.py` — aplikasi Streamlit utama
- `data_loader.py` — pembaca & pembersih data dari Excel (parsing tanggal Indonesia, kategorisasi transaksi, agregasi bulanan, tambah transaksi, export XLSX)
- `auth.py` — password gate untuk halaman Input Kotak Amal
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
- **10 transaksi terbesar** (pemasukan & pengeluaran).
- **Tambah Transaksi** (sidebar, halaman Dashboard) — input pemasukan/pengeluaran manual apa saja, langsung tercatat ke ledger untuk sesi berjalan.
- **Input Kotak Amal** (halaman terpisah, dilindungi password) — form hitung pecahan uang (Rp100.000 s/d Rp500) seperti rekap kotak amal manual; total otomatis dihitung dan dicatat sebagai transaksi pemasukan dengan keterangan "Pemasukan Kotak Amal" pada tanggal yang dipilih.
  - Password default: `amalalikhlas26` (lihat `auth.py` untuk cara mengganti, disarankan lewat environment variable `KOTAK_AMAL_PASSWORD`).
- **Export ke Excel (.xlsx)** — unduh ledger terfilter atau seluruh ledger (termasuk transaksi baru yang sudah diinput) sebagai file Excel yang rapi. CSV tetap tersedia juga.
- **Ganti file** — bisa upload file `.xlsx` laporan bulan lain langsung dari sidebar, tanpa perlu edit kode.

## Catatan penting soal data yang diinput

Transaksi yang ditambahkan lewat form (baik "Tambah Transaksi" maupun "Input Kotak Amal") disimpan di memori sesi Streamlit — akan hilang kalau aplikasi di-restart. Untuk menyimpannya secara permanen, unduh ledger sebagai XLSX lalu ganti/gabungkan dengan file sumber di `data/laporan_keuangan.xlsx`.

## Catatan kategorisasi

Kategori transaksi (Gaji, TPA, Listrik & Perawatan, Infaq Ustadz/Khotib, Kotak Amal, Renovasi & Aset, dll)
ditentukan otomatis dari kata kunci di kolom "Keterangan" (lihat `CATEGORY_RULES` di `data_loader.py`).
Kalau ada transaksi yang masuk kategori "Lainnya" dan ingin dikelompokkan lebih spesifik, tambahkan
pattern baru di `CATEGORY_RULES`.
