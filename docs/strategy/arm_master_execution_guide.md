# 📖 Aceh Resilience Monitor (ARM) — Master Execution Guide & Developer Manual
> **Dokumen Panduan Teknis Lengkap: Analisis Kode, Sintaksis Terminal, Integrasi Azure Cloud, dan Solusi Eror**
>
> *Manual ini disusun khusus untuk Aulia (ML & Azure Lead) sebagai pegangan resmi untuk memahami setiap blok kode, mengoperasikan perintah terminal, mengelola pipeline Azure, dan mematangkan Q&A di depan juri Datathon Dicoding.*

---

## 📋 Daftar Isi
1. [🧩 Analisis Blok Kode Utama & Outputnya](#1-analisis-blok-kode)
2. [💻 Cheat Sheet Perintah Terminal (Cara Running Lokal)](#2-cheat-sheet-terminal)
3. [☁️ Panduan Azure CLI & Manajemen Cloud](#3-panduan-azure-cli)
4. [🛠️ Troubleshooting: Deteksi Masalah & Solusi Eror](#4-troubleshooting)

---

## 🧩 1. Analisis Blok Kode Utama & Outputnya <a name="1-analisis-blok-kode"></a>

Berikut adalah daftar modul kode utama pada proyek ARM, blok fungsi krusial di dalamnya, serta output yang dihasilkan:

### A. Konfigurasi (`scripts/config.py`)
*   **Fungsi Utama:** Menyediakan satu sumber kebenaran (*single source of truth*) untuk seluruh konstanta, konstanta jalur berkas (paths), pemetaan kategori, warna, ikon, dan ambang batas statistik (*thresholds*).
*   **Fungsi Kunci:**
    *   `setup_logging(level)`: Mengatur pencatatan informasi (*logging*) ganda ke konsol terminal sekaligus ke file fisik `logs/pipeline.log`.
*   **Output Utama:** Objek Logger, variabel konstanta (seperti `ZSCORE_THRESHOLD = 2.0`, `MEUGANG_DATES`).

### B. Pipa ETL & Pemrosesan Data (`scripts/etl.py`)
*   **Fungsi Utama:** Mengunduh data mentah JSON tahunan dari lokal/cloud, membersihkan data, melakukan agregasi berdasarkan daerah/sumber, dan melakukan rekayasa fitur (*feature engineering*).
*   **Fungsi Kunci:**
    *   `load_all_data(years)`: Membaca file `2021.json` s/d `2026.json`, menggabungkannya di RAM menjadi satu Pandas DataFrame tunggal.
    *   `aggregate_prices(df, by)`: Mengagregasikan harga pangan berdasarkan level provinsi, daerah (kabupaten/kota), atau sumber pasar.
    *   `add_holiday_features(df)`: **(Senjata Rahasia Anda!)** Menyuntikkan kolom biner `is_meugang_season` (nilai 1 untuk H-2 s/d H-0 Meugang, dan 0 di luar itu) secara dinamis di RAM.
*   **Output Utama:** Pandas DataFrame yang bersih dan kaya fitur (*enriched data*) siap konsumsi model.

### C. Deteksi Anomali Reaktif (`scripts/anomaly.py`)
*   **Fungsi Utama:** Mendeteksi lonjakan atau penurunan harga pangan yang tidak wajar menggunakan metode statistik Z-Score harian.
*   **Fungsi Kunci:**
    *   `detect_anomalies(df, window, threshold)`: Menghitung rata-rata bergerak 30 hari (`MA30`) dan standar deviasi bergerak, lalu mencari data yang harga nyatanya menyimpang melebihi batas threshold $\sigma$.
    *   `classify_severity(z_score)`: Mengklasifikasikan keparahan anomali. Nilai $|Z| > 3.0$ ditandai sebagai `critical` (merah), sedangkan $|Z| > 2.0$ sebagai `warning` (kuning).
*   **Output Utama:** Array berisi *dictionary* rincian anomali: `[{'commodity', 'date', 'price', 'ma30', 'z_score', 'deviation_pct', 'severity', 'daerah'}]`.

### D. Peramalan Prediktif & EWS (`scripts/forecast.py`)
*   **Fungsi Utama:** Melatih model kecerdasan buatan **Meta Prophet** menggunakan regressor tambahan Meugang untuk meramal harga 90 hari ke depan.
*   **Fungsi Kunci:**
    *   `forecast_all_commodities(df, periods, per_region)`: Melatih model Prophet terpisah untuk setiap komoditas (dan wilayah), menyuntikkan Extra Regressor `is_meugang_season`, dan memproyeksikan harga 90 hari ke depan.
    *   `detect_future_spikes(forecasts, latest_prices)`: Membandingkan harga tertinggi hasil proyeksi Prophet terhadap harga saat ini. Jika kenaikan melebihi **20%**, status peringatan dini (*EWS Alert*) diaktifkan.
*   **Output Utama:** Objek ramalan (berisi `yhat`, `yhat_lower`, `yhat_upper` masa depan) dan daftar peringatan dini lonjakan harga pangan.

### E. Integrasi MLOps Cloud (`scripts/train_with_mlflow.py`)
*   **Fungsi Utama:** Menyediakan sarana audit dan visualisasi pelatihan model di cloud **Azure ML Studio** via **MLflow**.
*   **Fungsi Kunci:**
    *   `mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())`: Mengarahkan log lokal menuju server Azure ML Workspace.
    *   `mlflow.log_param()`, `mlflow.log_metric()`: Mencatat parameter tuning dan hasil metrik akurasi (MAPE, MAE, RMSE) ke server.
    *   `mlflow.prophet.log_model()`: Mengunggah file model biner `.pkl` ke dalam Model Registry Azure ML.
*   **Output Utama:** Sesi eksperimen visual yang dapat diakses di portal `ml.azure.com`.

### F. Pelaksana Pipeline Harian (`azure-functions/function_app.py`)
*   **Fungsi Utama:** Robot serverless harian yang berjalan otomatis pukul 08:00 WIB untuk mengeksekusi seluruh rangkaian di cloud.
*   **Fungsi Kunci:**
    *   `scrape_daily_pihps()`: Melakukan request HTTP GET ke endpoint Bank Indonesia untuk mengambil harga teranyar.
    *   `daily_pipeline(myTimer)`: Fungsi trigger utama yang menjalankan semua alur, menyusun pesan notifikasi premium, mengirimkannya ke grup Telegram Satgas Pangan, dan memperbarui visualisasi dasbor.
*   **Output Utama:** Notifikasi Telegram Bot aktif, visualisasi dasbor ter-refresh harian di Azure Static Web Apps.

---

## 💻 2. Cheat Sheet Perintah Terminal (Cara Running Lokal) <a name="2-cheat-sheet-terminal"></a>

Gunakan daftar perintah terminal berikut di bawah direktori utama proyek (`datathon-dicoding/`) untuk menjalankan berbagai komponen sistem secara lokal di laptop Anda:

### A. Persiapan Lingkungan & Instalasi Dependensi
Sebelum menjalankan file apa pun, Anda wajib mengaktifkan Virtual Environment (venv) Python dan memasang pustaka (*libraries*) yang dibutuhkan:
```bash
# 1. Buat Virtual Environment Python (opsional jika belum ada)
python3 -m venv venv

# 2. Aktifkan Virtual Environment di macOS/Linux
source venv/bin/activate

# 3. Pasang semua dependensi library
pip install -r requirements.txt
```

### B. Menjalankan Pipeline & Generator Dasbor Lokal
Untuk memproses seluruh data mentah dari 2021 hingga 2026, mendeteksi anomali Z-score, melatih model Prophet, dan menghasilkan file penyuplai data dasbor (`dashboard_data.json`):
```bash
python -m scripts.prepare_dashboard_data
```
*   **Output Sukses:** Terminal akan memproses data komoditas satu per satu, menampilkan log akurasi Prophet, dan menghasilkan file `dashboard/dashboard_data.json` serta `dashboard/dashboard_data.js` tanpa eror.

### C. Menjalankan Pembuatan Plot Visualisasi EDA
Untuk menghasilkan 13 plot grafik statistik lengkap proyek datathon Anda secara otomatis:
```bash
python -m scripts.save_plots
```
*   **Output Sukses:** Sebanyak 13 file gambar grafik premium berformat `.png` akan tersimpan di dalam folder `plots/`.

### D. Menjalankan Rangkaian Pengujian Unit (Unit Testing)
Untuk memverifikasi keandalan logika kode, kecocokan tipe data, dan integritas konfigurasi:
```bash
pytest
```
*   **Output Sukses:** Menampilkan laporan kelulusan pengujian berwarna hijau: `================ 71 passed in X.XXs ================`.

### E. Menjalankan Pelatihan MLOps dengan Logging ke Azure ML Studio
Untuk mengirim log parameter, metrik evaluasi MAPE, dan meregistrasikan model Prophet ke cloud Azure ML:
```bash
python scripts/train_with_mlflow.py
```
*   **Syarat Utama:** Anda harus memastikan file kredensial `config.json` hasil unduhan dari Azure Portal sudah berada di root direktori proyek Anda.

### F. Menguji Coba Azure Functions secara Lokal
Untuk menjalankan robot harian serverless di laptop Anda sebelum di-deploy ke cloud Azure:
```bash
# 1. Masuk ke direktori Azure Functions
cd azure-functions

# 2. Jalankan runtime Functions secara lokal
func start
```
*   **Cara Trigger Manual Secara Lokal:** Buka terminal baru, jalankan perintah `curl` berikut untuk memicu jalannya pipeline tanpa menunggu waktu timer:
    ```bash
    curl -post http://localhost:7071/admin/functions/daily_pipeline
    ```

---

## ☁️ 3. Panduan Azure CLI & Manajemen Cloud <a name="3-panduan-azure-cli"></a>

Sebagai ML & Azure Lead, gunakan perintah praktis Azure CLI berikut untuk mengontrol dan menguji pipeline Anda langsung di awan:

### A. Login & Autentikasi Azure CLI
Sebelum mengirim perintah apa pun, Anda harus login ke akun Microsoft Azure Anda di terminal:
```bash
az login
```
*   *Browser otomatis terbuka untuk meminta verifikasi login email Azure Anda.*

### B. Mengatur Variabel Konfigurasi Rahasia di Cloud
Untuk memasang token Bot Telegram dan Chat ID grup di aplikasi serverless Azure Functions agar aman dari commit Git:
```bash
az functionapp config appsettings set \
  --name arm-daily-pipeline-74220 \
  --resource-group arm-datathon-rg \
  --settings \
    TELEGRAM_BOT_TOKEN="ISI_TOKEN_BOT_ANDA" \
    TELEGRAM_CHAT_ID="ISI_CHAT_ID_GRUP_ANDA"
```

### C. Mengunggah Kode Azure Functions Terbaru ke Awan
Setiap kali Anda mengubah kode di dalam folder `azure-functions/`, publikasikan pembaruan tersebut ke cloud dengan perintah:
```bash
cd azure-functions
func azure functionapp publish arm-daily-pipeline-74220
```

### D. Mengunggah File Visual Dasbor ke Azure Blob Storage
Untuk memperbarui file antarmuka dasbor Anda (`index.html`, `app.js`, `style.css`) ke hosting kontainer publik:
```bash
az storage blob upload-batch \
  --destination '$web' \
  --source dashboard/ \
  --connection-string "MASUKKAN_CONNECTION_STRING_BLOB_STORAGE_ANDA" \
  --overwrite
```

### E. Memicu Jalannya Azure Functions Cloud Secara Manual (Triggering)
Untuk mengetes jalannya pipeline harian di cloud saat itu juga tanpa menunggu jam 8 pagi, jalankan perintah terminal ini:
```bash
az functionapp function trigger \
  --name arm-daily-pipeline-74220 \
  --resource-group arm-datathon-rg \
  --function-name daily_pipeline
```
*   *Ini akan langsung mengeksekusi pipeline di cloud, menyemburkan pesan alert ke Telegram grup Anda, dan memperbarui grafik dasbor.*

---

## 🛠️ 4. Troubleshooting: Deteksi Masalah & Solusi Eror <a name="4-troubleshooting"></a>

Berikut adalah panduan cepat pemecahan masalah (*troubleshooting*) jika Anda menemui kendala saat demonstrasi atau pengembangan:

### A. Eror: `ModuleNotFoundError: No module named '...'`
*   **Penyebab:** Library yang dibutuhkan belum terpasang di Virtual Environment Anda.
*   **Solusi:** Pastikan venv aktif, lalu pasang ulang requirements:
    ```bash
    source venv/bin/activate
    pip install -r requirements.txt
    ```

### B. Eror: `WorkspaceConfigError` saat Menjalankan MLflow
*   **Penyebab:** Skrip `train_with_mlflow.py` tidak menemukan berkas `config.json` kredensial Azure ML di root folder proyek.
*   **Solusi:**
    1. Masuk to Azure Portal ➔ Cari `arm-ml-workspace`.
    2. Pada bilah atas *Overview*, klik **Download config.json**.
    3. Simpan file tersebut di folder `datathon-dicoding/config.json`.

### C. Eror: Telegram Alert Tidak Mengirim Pesan ke Grup
*   **Penyebab:** Token Bot salah atau Chat ID grup bernilai positif/salah pasang.
*   **Solusi:**
    1. Ingat bahwa Chat ID grup Telegram **selalu bernilai negatif** (contoh: `-10023456789`). Jika Anda memasukkan angka positif, bot akan mengirim ke chat pribadi bukan grup.
    2. Tes token bot Anda di browser menggunakan URL:
       `https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=TesKoneksi`

### D. Eror: Dasbor Menampilkan Status "Gagal Memuat Data!"
*   **Penyebab:** Kebijakan CORS di Azure Blob Storage memblokir permintaan fetch HTTP dasbor Static Web App Anda.
*   **Solusi:**
    1. Buka Azure Portal ➔ Masuk ke Storage Account `armdatalake2026`.
    2. Cari menu **CORS** di bawah kategori *Settings*.
    3. Tambahkan aturan baru untuk Blob service:
       - **Allowed Origins:** `*` (atau domain Static Web App Anda).
       - **Allowed Methods:** `GET`, `OPTIONS`.
       - **Allowed Headers:** `*`.
       - **Exposed Headers:** `*`.
       - **Max Age:** `86400`.
    4. Klik **Save**. Dasbor akan langsung memuat grafik secara instan!

---

> **Pesan untuk Aulia (ML & Azure Lead):**
> Simpan panduan ini baik-baik. Dengan memahami isi dokumen ini, Anda kini memiliki kontrol dan pemahaman penuh atas setiap baris kode dan infrastruktur cloud proyek datathon Anda. Tunjukkan kebanggaan dan dedikasi Anda di depan dewan juri! 🚀🏆
