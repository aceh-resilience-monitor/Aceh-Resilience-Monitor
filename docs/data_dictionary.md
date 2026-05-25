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

---

## 📊 4. Payload Output Dasbor (`dashboard_data.json`)
Pipeline orchestrator `prepare_dashboard_data.py` menghasilkan satu file payload terintegrasi (`dashboard_data.json`) berukuran ~2.3 MB yang dikonsumsi langsung oleh frontend Static Web App. File JSON ini memiliki 21 bagian utama yang disusun sebagai berikut:

### Bagian Kunci & Skema Objek:
1.  **`kpi`** (object): Metrik ringkasan eksekutif provinsi.
    *   `totalRecords`: Total titik data terproses (contoh: `210,955`).
    *   `activeCommodities`: Jumlah komoditas aktif (`21`).
    *   `criticalAlertsCount`: Jumlah anomali berstatus Kritis saat ini.
    *   `warningAlertsCount`: Jumlah anomali berstatus Waspada saat ini.
2.  **`commodityCards`** (array of objects): Data ringkasan terkini untuk grid kartu utama dasbor. Berisi harga terbaru, rata-rata MA30, nilai CV%, status anomali (`Aman`, `Waspada`, atau `Kritis`), dan trend arah harga.
3.  **`timeseries`** (object): Data historis mingguan agregat tingkat provinsi per komoditas untuk grafik tren utama.
4.  **`regional`** (object): Data tren harga terperinci tingkat daerah (Banda Aceh, Lhokseumawe, Meulaboh). Memungkinkan visualisasi perbandingan disparitas harga antar daerah (Tier 2 Dashboard).
5.  **`priceBySource`** (object): Distribusi harga pangan terbaru berdasarkan 4 saluran distribusi (sumber) per komoditas. Berguna untuk memantau disparitas rantai pasok (Tier 3 Dashboard).
6.  **`regionalForecasts`** (object): Hasil prediksi model Meta Prophet 90 hari ke depan yang dihitung **secara spesifik per daerah**.
7.  **`forecasts`** (object): Proyeksi harga tingkat provinsi hasil rata-rata agregasi.
8.  **`anomalies`** (array of objects): Daftar seluruh transaksi anomali harga pangan historis yang mendeteksi lonjakan di luar $2\sigma$.

---

## 📝 5. Tabel Referensi & Standar Klasifikasi

### A. Klasifikasi 21 Sub-Komoditas Terdaftar (`CATEGORY_MAP`)

| No | Nama Sub-Komoditas | Kategori Induk | Singkatan Dasbor |
|---|---|---|---|
| 1 | Beras Kualitas Bawah I | Beras | Beras Bawah 1 |
| 2 | Beras Kualitas Bawah II | Beras | Beras Bawah 2 |
| 3 | Beras Kualitas Medium I | Beras | Beras Medium 1 |
| 4 | Beras Kualitas Medium II | Beras | Beras Medium 2 |
| 5 | Beras Kualitas Super I | Beras | Beras Super 1 |
| 6 | Beras Kualitas Super II | Beras | Beras Super 2 |
| 7 | Bawang Merah Ukuran Sedang | Bawang Merah | Bawang Merah |
| 8 | Bawang Putih Ukuran Sedang | Bawang Putih | Bawang Putih |
| 9 | Cabai Merah Keriting | Cabai Merah | Cabai Keriting |
| 10 | Cabai Rawit Hijau | Cabai Rawit | Cabai Rawit Hijau |
| 11 | Daging Sapi Kualitas 1 | Daging Sapi | Daging Sapi 1 |
| 12 | Daging Ayam Ras Segar | Daging Ayam | Daging Ayam |
| 13 | Telur Ayam Ras Segar | Telur Ayam | Telur Ayam |
| 14 | Gula Pasir Lokal | Gula Pasir | Gula Lokal |
| 15 | Gula Pasir Kualitas Premium | Gula Pasir | Gula Premium |
| 16 | Minyak Goreng Curah | Minyak Goreng | Minyak Curah |
| 17 | Minyak Goreng Kemasan Bermerk 1 | Minyak Goreng | Minyak Merk 1 |
| 18 | Minyak Goreng Kemasan Bermerk 2 | Minyak Goreng | Minyak Merk 2 |
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
