# 📖 Kamus Data (Data Dictionary) — Aceh Resilience Monitor (ARM)
**Proyek:** Platform Intelijen Harga Pangan Strategis Aceh  
**Format Sumber:** dataup JSON (Scraped dari PIHPS)  
**Tingkat Granularitas:** Harian × Komoditas × Daerah × Sumber Harga  

---

## 📌 Pendahuluan

Dokumen ini mendefinisikan seluruh struktur data, tipe data, rentang nilai, dan arti variabel yang digunakan dalam ekosistem **Aceh Resilience Monitor (ARM)**. Kamus data ini dirancang untuk memastikan keselarasan interpretasi antara data hasil scraping (`dataup/`), data pemrosesan ETL (`scripts/etl.py`), model forecasting (`scripts/forecast.py`), hingga payload visualisasi dasbor (`dashboard/dashboard_data.json`).

Ekosistem ARM menggunakan model data **multi-dimensi penuh**. Ini berarti data tidak dipadatkan secara kasar saat masuk, melainkan dipertahankan dimensi asalnya sehingga sistem dapat menganalisis variabilitas harga tidak hanya berdasarkan waktu, tetapi juga berdasarkan **Daerah** (Banda Aceh, Lhokseumawe, Meulaboh) dan **Sumber Harga** (Pasar Tradisional, Pasar Modern, Pedagang Besar, Produsen).

---

## 🗃️ 1. Skema Data Mentah (Raw Scraped JSON)
Data mentah hasil scraping disimpan di dalam folder `dataup/*.json` per tahun (contoh: `2025.json`). Setiap file berisi array JSON yang merepresentasikan data harian hasil ekstraksi PIHPS.

| Nama Atribut | Tipe Data | Contoh Nilai | Deskripsi | Aturan & Transformasi |
| :--- | :---: | :--- | :--- | :--- |
| `tanggal` | string | `"2025-05-24"` | Tanggal pencatatan harga dalam format `YYYY-MM-DD`. | Dikonversi ke tipe `datetime` di ETL. |
| `level` | integer | `2` | Tingkatan hierarki komoditas. `1` untuk kategori utama, `2` untuk sub-komoditas. | Hanya data dengan `level` = `2` yang diproses. |
| `name` | string | `"Cabai Merah Keriting "` | Nama sub-komoditas pangan hasil scraping. | Trailing space dibersihkan dengan `.str.strip()` di ETL. |
| `harga` | string \| null | `"45,500"` atau `null` | Nilai harga dalam Rupiah dengan koma pemisah ribuan. | Koma dihapus, `null` atau `"-"` dikonversi ke NaN, lalu difilter keluar. |
| `daerah` | string | `"Banda Aceh"` | Nama kota/kabupaten pencatatan harga. | Terdiri dari 3 daerah utama di Aceh. |
| `sumber` | string | `"Pasar Tradisional"` | Saluran distribusi penjualan pangan. | Terdiri dari 4 jenis sumber utama. |

---

## ⚙️ 2. Skema Data Hasil ETL (`load_all_data()`)
Setelah melewati fungsi `load_all_data()` di `scripts/etl.py`, data dibersihkan, disaring berdasarkan komoditas terdaftar (21 komoditas), diubah tipe datanya, dan diperkaya dengan dimensi kalender.

DataFrame hasil akhir memiliki kolom-kolom berikut:

| Nama Kolom | Tipe Data Pandas | Contoh Nilai | Deskripsi | Nilai Kosong (NaN) |
| :--- | :---: | :--- | :--- | :--- |
| `date` | datetime64[ns] | `2025-05-24` | Tanggal pencatatan harga pangan. | Tidak diperbolehkan (Dihapus). |
| `commodity` | object (string) | `"Cabai Merah Keriting"` | Nama resmi sub-komoditas (sudah di-*strip*). | Tidak diperbolehkan (Dihapus). |
| `price` | float64 | `45500.0` | Nilai harga absolut dalam Rupiah (Rp). | Tidak diperbolehkan (Dihapus). |
| `year` | int64 | `2025` | Tahun pencatatan harga (diambil dari `date`). | Otomatis terisi. |
| `month` | int64 | `5` | Bulan pencatatan harga (1 = Jan, 12 = Des). | Otomatis terisi. |
| `category` | object (string) | `"Cabai Merah"` | Kategori induk komoditas (dari `CATEGORY_MAP`). | Otomatis terisi lewat pemetaan kamus. |
| `daerah` | object (string) | `"Banda Aceh"` | Nama daerah pemantauan (Banda Aceh, Lhokseumawe, Meulaboh). | Dipertahankan untuk analisis spasial. |
| `sumber` | object (string) | `"Pasar Tradisional"` | Sumber harga pangan. | Dipertahankan untuk analisis rantai pasok. |

---

## 📈 3. Skema Fitur Tambahan (Feature Engineering - `add_features()`)
Untuk kebutuhan pemodelan *Machine Learning* dan analisis tingkat lanjut, fungsi `add_features()` menambahkan 8 fitur kalkulasi baru ke dalam DataFrame ETL:

### A. Fitur Harga Lag (Lagged Price Features)
Fitur lag berguna bagi model time-series untuk mempelajari korelasi pergerakan harga hari ini dengan masa lalu.
*   `price_lag_1d` (float64): Harga komoditas pada 1 hari sebelumnya ($\text{Price}_{t-1}$).
*   `price_lag_7d` (float64): Harga komoditas pada 1 minggu sebelumnya ($\text{Price}_{t-7}$).
*   `price_lag_30d` (float64): Harga komoditas pada 30 hari sebelumnya ($\text{Price}_{t-30}$).

### B. Fitur Statistik Bergerak (Rolling Window Statistics)
Membantu meredam *noise* (fluktuasi harian yang terlalu liar) guna menangkap tren jangka menengah.
*   `rolling_mean_7d` (float64): Rata-rata pergerakan harga selama 7 hari terakhir (MA7).
*   `rolling_std_7d` (float64): Standar deviasi harga selama 7 hari terakhir. Digunakan untuk melihat lonjakan volatilitas jangka pendek.

### C. Fitur Momentum
*   `price_momentum_7d` (float64): Persentase perubahan harga hari ini dibandingkan dengan 7 hari lalu ($\frac{\text{Price}_t - \text{Price}_{t-7}}{\text{Price}_{t-7}} \times 100$). Nilai positif menunjukkan tren inflasi, nilai negatif menunjukkan deflasi.

### D. Fitur Kalender & Seasonalitas
*   `day_of_week` (int64): Hari dalam seminggu dalam representasi angka. Rentang nilai: `0` (Senin) s/d `6` (Minggu).
*   `is_holiday_season` (int64): Bendera biner (`1` atau `0`) untuk menandai periode musiman hari raya besar keagamaan. Ditentukan bernilai `1` pada:
    *   Bulan November, Desember, dan Januari (Natal dan Tahun Baru).
    *   Bulan pergerakan Ramadan & Idul Fitri spesifik tiap tahun (contoh 2025: Februari dan Maret).

### E. Fitur Extra Regressor Prophet (Deterministic Events)
Untuk melatih model forecasting Prophet tingkat lanjut di RAM, fungsi `add_holiday_features()` menyuntikkan 4 regressor deterministik yang nilainya dapat dihitung untuk masa depan:
*   `is_meugang_season` (int64): Menandai tradisi Meugang di Aceh (H-2 s/d H-0 sebelum awal Ramadan, Idul Fitri, dan Idul Adha).
*   `is_ramadan_prep` (int64): Masa persiapan 7 hari sebelum awal Ramadan.
*   `is_nataru` (int64): Periode Natal & Tahun Baru (20 Desember s/d 2 Januari).
*   `is_wet_season` (int64): Musim hujan BMKG Sumatera (Oktober s/d April).

---

## 📊 4. Payload Output Dasbor (`dashboard_data.json`)
Pipeline orchestrator `prepare_dashboard_data.py` menghasilkan satu file payload terintegrasi (`dashboard_data.json`) berukuran ~1.2 MB yang diunggah ke public Blob Storage container (`$web`) untuk dikonsumsi langsung oleh frontend Static Web App.

### Struktur Key Utama Payload:

| Nama Key | Tipe Data | Deskripsi |
| :--- | :---: | :--- |
| `kpi` | object | Ringkasan indikator kinerja utama tingkat provinsi (detail di bawah). |
| `commodityCards` | array | Data status teranyar per komoditas untuk komponen grid kartu dasbor (detail di bawah). |
| `timeseries` | object | Histori harga mingguan tingkat provinsi per komoditas untuk grafik tren utama. |
| `timeseriesRecentDaily` | object | Histori harga harian tingkat provinsi per komoditas selama 90 hari terakhir. |
| `anomalies` | array | Daftar transaksi anomali harga pangan historis hasil deteksi Z-score (>2σ). |
| `alertFeed` | array | Gabungan alert prediksi lonjakan harga (Prophet) dan anomali historis. |
| `yoyData` | array | Perbandingan persentase harga Year-over-Year (YoY) antar tahun. |
| `seasonality` | object | Z-score bulanan untuk analisis pola seasonal komoditas. |
| `volatility` | object | Nilai Coefficient of Variation (CV) tahunan per komoditas. |
| `correlation` | object | Matriks korelasi harga antar komoditas (koefisien korelasi Pearson). |
| `categoryMonthly` | object | Tren rata-rata harga bulanan per kategori induk komoditas (misal: Beras, Cabai). |
| `forecasts` | object | Hasil proyeksi harga agregat provinsi 90 hari ke depan hasil model Prophet. |
| `categories` | array | Daftar unik kategori induk pangan yang terurut. |
| `categoryIcons` | object | Pemetaan ikon emoji per kategori pangan. |
| `categoryColors` | object | Pemetaan kode warna hex per kategori pangan untuk grafik. |
| `aiInsight` | string | Narasi ringkasan eksekutif hasil analisis berbasis data (Executive Summary). |
| `regional` | object | Tren harga harian serta metrik regional tingkat kabupaten/kota (Banda Aceh, Lhokseumawe, Meulaboh). |
| `priceBySource` | object | Margin harga pangan berdasarkan saluran distribusi / sumber harga (Tradisional vs Modern vs Produsen vs Grosir). |
| `regionalForecasts` | object | Proyeksi harga pangan 90 hari ke depan per daerah hasil model Prophet regional. |
| `regions` | array | Daftar wilayah pemantauan: `["Banda Aceh", "Lhokseumawe", "Meulaboh"]`. |
| `priceSources` | array | Daftar saluran distribusi: `["Pasar Tradisional", "Pasar Modern", "Pedagang Besar", "Produsen"]`. |

### A. Detail Objek `kpi`:
*   `totalCommodities` (integer): Jumlah komoditas pangan aktif (21).
*   `criticalAlerts` (integer): Jumlah komoditas dengan status anomali 'critical' (Z-score > 3σ atau perubahan tahunan > 20%).
*   `warningAlerts` (integer): Jumlah komoditas dengan status anomali 'warning' (Z-score > 2σ atau perubahan tahunan > 10%).
*   `avgPriceChange` (float): Rata-rata perubahan harga total (%) seluruh komoditas.
*   `dataStartDate` (string): Tanggal awal data historis (`YYYY-MM-DD`).
*   `dataEndDate` (string): Tanggal akhir data terproses (`YYYY-MM-DD`).
*   `totalDataPoints` (integer): Total baris titik data mentah yang digunakan.
*   `recentAnomalies` (integer): Jumlah anomali harga dalam 90 hari terakhir.
*   `totalRegions` (integer): Jumlah daerah pemantauan (3).
*   `totalSources` (integer): Jumlah saluran distribusi harga (4).

### B. Detail Objek di `commodityCards`:
Setiap elemen dalam array `commodityCards` memiliki struktur sebagai berikut:
*   `commodity` (string): Nama lengkap komoditas (misal: `"Beras Kualitas Bawah I"`).
*   `shortName` (string): Singkatan nama untuk visualisasi (misal: `"Beras Bawah I"`).
*   `category` (string): Kategori induk komoditas (misal: `"Beras"`).
*   `icon` (string): Emoji representatif.
*   `latestPrice` (float): Harga terbaru absolut (Rp).
*   `monthChange` (float): Persentase perubahan harga bulan ini dibanding rata-rata 30 hari sebelumnya.
*   `totalChange` (float): Persentase perubahan harga kumulatif multi-tahun.
*   `cvLatest` (float): Koefisien variasi harga tahun berjalan (%).
*   `cv2025` (float): Koefisien variasi harga khusus tahun 2025 (untuk kompatibilitas frontend).
*   `status` (string): Klasifikasi status anomali (`normal`, `warning`, `critical`).
*   `recentAnomalies` (integer): Jumlah anomali yang dialami komoditas tersebut dalam 90 hari terakhir.

---

## 📝 5. Tabel Referensi & Standar Klasifikasi

### A. Klasifikasi 21 Sub-Komoditas Terdaftar (`CATEGORY_MAP` & `SHORT_NAMES`)

| No | Nama Sub-Komoditas (Database/JSON) | Kategori Induk | Singkatan Dasbor (`shortName`) |
|---|---|---|---|
| 1 | Beras Kualitas Bawah I | Beras | Beras Bawah I |
| 2 | Beras Kualitas Bawah II | Beras | Beras Bawah II |
| 3 | Beras Kualitas Medium I | Beras | Beras Medium I |
| 4 | Beras Kualitas Medium II | Beras | Beras Medium II |
| 5 | Beras Kualitas Super I | Beras | Beras Super I |
| 6 | Beras Kualitas Super II | Beras | Beras Super II |
| 7 | Bawang Merah Ukuran Sedang | Bawang Merah | Bawang Merah |
| 8 | Bawang Putih Ukuran Sedang | Bawang Putih | Bawang Putih |
| 9 | Cabai Merah Keriting | Cabai Merah | Cabai Keriting |
| 10 | Cabai Rawit Hijau | Cabai Rawit | Cabai Rawit Hijau |
| 11 | Daging Sapi Kualitas 1 | Daging Sapi | Daging Sapi 1 |
| 12 | Daging Ayam Ras Segar | Daging Ayam | Daging Ayam |
| 13 | Telur Ayam Ras Segar | Telur Ayam | Telur Ayam |
| 14 | Gula Pasir Lokal | Gula Pasir | Gula Lokal |
| 15 | Gula Pasir Kualitas Premium | Gula Pasir | Gula Premium |
| 16 | Minyak Goreng Curah | Minyak Goreng | M. Goreng Curah |
| 17 | Minyak Goreng Kemasan Bermerk 1 | Minyak Goreng | M. Goreng Merk 1 |
| 18 | Minyak Goreng Kemasan Bermerk 2 | Minyak Goreng | M. Goreng Merk 2 |
| 19 | Cabai Merah Besar *(NEW)* | Cabai Merah | Cabai Besar |
| 20 | Cabai Rawit Merah *(NEW)* | Cabai Rawit | Cabai Rawit Merah |
| 21 | Daging Sapi Kualitas 2 *(NEW)* | Daging Sapi | Daging Sapi 2 |

### B. Pemetaan Wilayah Pemantauan (`REGIONS`)
*   **ID 1:** `Banda Aceh` (Pusat Pemerintahan & Konsumsi Utama)
*   **ID 2:** `Lhokseumawe` (Hub Ekonomi Wilayah Pantai Timur)
*   **ID 3:** `Meulaboh` (Hub Logistik Wilayah Pantai Barat Selatan)

### C. Pemetaan Saluran Distribusi (`PRICE_SOURCES`)
*   **ID 1:** `Pasar Tradisional` (Indikator ritel langsung masyarakat kelas menengah-bawah)
*   **ID 2:** `Pasar Modern` (Indikator pasar ritel terstruktur/swalayan)
*   **ID 3:** `Pedagang Besar` (Indikator harga grosir tingkat distributor utama)
*   **ID 4:** `Produsen` (Indikator harga dasar tingkat petani/peternak/nelayan)
