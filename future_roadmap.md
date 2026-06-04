# 🗺️ Future Roadmap: Pengembangan & Optimasi Sistem ARM (Aceh Resilience Monitor)

Dokumen ini mendokumentasikan peta jalan (*future roadmap*) untuk pengembangan lanjutan dan optimasi arsitektur **Aceh Resilience Monitor (ARM)**. Peta jalan ini dirancang untuk menjaga kualitas data, meningkatkan akurasi model peramalan, serta menjamin skalabilitas pipa data cloud jangka panjang.

---

## 📋 Ringkasan Peta Jalan

Peta jalan pengembangan ARM dibagi ke dalam **3 Pilar Utama**:
1.  **Pilar 1: Rekayasa Kualitas & Integrasi Data (Data Engineering)**
2.  **Pilar 2: Optimasi Model & Machine Learning (MLOps & Analytics)**
3.  **Pilar 3: Skalabilitas Cloud & Efisiensi Infrastruktur (DevOps & Serverless)**

---

## 🗂️ Detail Pengembangan per Pilar

### 1. Pilar 1: Rekayasa Kualitas & Integrasi Data (Data Engineering)

Fokus utama pilar ini adalah untuk memastikan ketersediaan data harian selalu bersih, bebas dari kesalahan rilis, dan tahan terhadap gangguan server pihak ketiga.

*   **1.1. Penanganan Batas Pergantian Tahun (*Year-End Boundary Lookback*)**
    *   *Deskripsi*: Modifikasi scraper agar mendeteksi tahun dari setiap data tanggal yang berhasil di-scrape secara dinamis.
    *   *Tujuan*: Menjamin data *lookback* di akhir tahun (misalnya tanggal 30-31 Desember) yang di-scrape pada awal Januari tetap masuk ke berkas tahun yang benar (misalnya `2026.json` bukan `2027.json`).
*   **1.2. Deteksi Gap Otomatis (*Self-Healing Backfill*)**
    *   *Deskripsi*: Membuat subsistem pemindai data harian yang mendeteksi hari-hari kosong dalam 30 hari terakhir. Jika ditemukan hari kosong (akibat server BI mati lama), sistem otomatis membuat antrean penarikan data (*backfill queue*) saat server BI kembali *online*.
    *   *Tujuan*: Menutup celah data (*data gaps*) secara otomatis tanpa intervensi manual dari administrator.
*   **1.3. Penyelarasan Nama Komoditas Dinamis (*Fuzzy String Matching*)**
    *   *Deskripsi*: Menggunakan algoritma jarak Levenshtein (`difflib` di Python) untuk memetakan nama komoditas dari API BI ke standar ARM secara adaptif.
    *   *Tujuan*: Mencegah kegagalan ETL ketika admin BI Hargapangan mengubah nama komoditas secara tiba-tiba (seperti penambahan spasi atau tanda kurung satuan).

---

### 2. Pilar 2: Optimasi Model & Machine Learning (MLOps & Analytics)

Fokus utama pilar ini adalah menjaga stabilitas performa model peramalan Meta Prophet dari gangguan *noise* data ekstrem.

*   **2.1. Pelatihan Jendela Bergerak (*Sliding Window Training - 730 Days*)**
    *   *Deskripsi*: Membatasi sejarah data latih Prophet secara konstan hanya untuk data **2 tahun terakhir (730 hari)**.
    *   *Tujuan*: Menghindari *Concept Drift* (data lama tahun 2021-2022 sudah tidak relevan dengan perilaku pasar tahun 2026) dan memotong waktu eksekusi pelatihan.
*   **2.2. Penyaringan Outlier Ekstrem (*Data Winsorization / Clipping*)**
    *   *Deskripsi*: Menerapkan pemotongan harga otomatis pada data latih jika terdeteksi lonjakan anomali sesaat ($> 3\sigma$).
    *   *Tujuan*: Menjaga agar garis tren peramalan Prophet tidak rusak akibat fluktuasi jangka pendek yang ekstrem.
*   **2.3. Imputasi Data Kosong ML (*Forward Fill Constraint*)**
    *   *Deskripsi*: Mengisi kekosongan data jangka pendek (akhir pekan/hari libur) secara dinamis menggunakan harga terakhir yang dilaporkan (maksimum 7 hari berturut-turut) sebelum dimasukkan ke model pelatihan.
    *   *Tujuan*: Menjaga deret waktu tetap kontinu agar model Prophet tidak bias atau mengalami kegagalan fitting.
*   **2.4. Proteksi Batas Harga Logis (*Forecast Sanity Constraint*)**
    *   *Deskripsi*: Menerapkan pemotongan otomatis (*clipping*) pada batas bawah harga prediksi agar tidak pernah menyentuh nilai negatif (di bawah Rp 0).
    *   *Tujuan*: Mencegah visualisasi grafik dasbor menampilkan harga di bawah Rp 0 jika terjadi tren penurunan yang terlalu tajam.

---

### 3. Pilar 3: Skalabilitas Cloud & Efisiensi Infrastruktur (DevOps & Serverless)

Fokus utama pilar ini adalah mengoptimalkan infrastruktur serverless Azure Functions agar lebih hemat biaya dan memiliki performa tinggi.

*   **3.1. Pelatihan Model Paralel (*Multiprocessing*)**
    *   *Deskripsi*: Melakukan *paralelisasi* proses pelatihan 84 model Prophet menggunakan modul `multiprocessing` di Python Azure Functions.
    *   *Tujuan*: Memanfaatkan multi-core CPU pada Azure secara maksimal dan memangkas durasi eksekusi fungsi dari menit menjadi hanya belasan detik.
*   **3.2. Pemantauan Drift Model Terpusat (*Model & Data Drift Monitoring*)**
    *   *Deskripsi*: Mengintegrasikan metrik evaluasi harian (MAE, RMSE, MAPE) yang dicatat via MLflow ke dashboard Azure Machine Learning Studio secara visual.
    *   *Tujuan*: Memudahkan tim teknis mendeteksi secara dini apabila performa prediksi model di wilayah tertentu mulai menurun tajam (*model degradation*).
