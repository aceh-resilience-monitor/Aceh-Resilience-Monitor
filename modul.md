# 📋 Prompt Modul Siap Pakai (Copy-Paste untuk AI Agent)

Panduan ini berisi draf prompt terstruktur menggunakan **Framework C.R.E.A.T.E** dan **Template Section 3.1** dari `ai_agent_masterguide.md`. Kamu tinggal menyalin (*copy-paste*) prompt di bawah ini ke AI Agent untuk membangun kodenya secara bertahap.

---

## 🌶️ Modul 1: Feature Engineering & Prophet Extra Regressor

**Salin teks di bawah ini:**

```markdown
## Konteks (Context)
Saya sedang mengembangkan proyek Datathon "Aceh Resilience Monitor (ARM)" untuk mengantisipasi inflasi pangan. Saat ini saya menggunakan model Prophet untuk memprediksi harga pangan secara harian, tetapi modelnya masih univariat (hanya berbasis tanggal dan harga historis). Saya ingin menambahkan fitur kearifan lokal "Meugang" (tradisi memotong hewan dan konsumsi pangan tinggi menjelang hari raya di Aceh) untuk mendongkrak akurasi model.

## Peran yang Diminta (Role)
Bertindaklah sebagai Senior ML & Data Engineer yang pakar dalam pemodelan deret waktu (time series forecasting).

## Modul yang Dikerjakan (Exact Task)
Modul 1: Implementasi Feature Engineering kearifan lokal "Meugang/Hari Raya" dan integrasi sebagai Extra Regressor di model Prophet.

## File yang Relevan (Input)
- `scripts/config.py` (Berisi konstanta pendukung)
- `scripts/etl.py` (Modul data loading)
- `scripts/forecast.py` (Modul pemodelan Prophet)
- `tests/test_etl.py` (Unit tests untuk ETL)

## Kriteria Sukses (Acceptance Criteria)
1. Di `scripts/etl.py` (atau `config.py`): Buat konstanta `MEUGANG_DATES` berisi tabel tanggal tradisi Meugang (Ramadan, Fitri, Adha) di Aceh untuk tahun 2021 s/d 2026.
2. Di `scripts/etl.py`: Buat fungsi `add_holiday_features(df)` yang menerima Pandas DataFrame, mengubah kolom date menjadi datetime, menginisialisasi kolom `is_meugang_season` dengan 0, lalu merubahnya menjadi 1 untuk baris data yang berada pada H-2 s/d H-0 menjelang hari H Meugang.
3. Di `scripts/forecast.py` pada fungsi `train_prophet()`: Daftarkan `is_meugang_season` sebagai extra regressor menggunakan `model.add_regressor('is_meugang_season')` jika kolom tersebut ada di dalam dataset.
4. Di `scripts/forecast.py` pada fungsi `predict_future()`: Pastikan sebelum melakukan `model.predict()`, tabel tanggal masa depan (90 hari ke depan) dilewatkan dulu ke fungsi `add_holiday_features()` agar model mengetahui kapan persisnya hari Meugang berikutnya akan terjadi di masa depan.
5. Unit tests: Seluruh pytest di folder `tests/` harus tetap berjalan sukses tanpa eror.

## Batasan (Constraint)
- Tetap pertahankan struktur modular yang sudah ada. Jangan merusak fungsi data loading yang membaca dataup JSON.
- Waktu eksekusi penambahan fitur di memori harus di bawah 10 milidetik.

## Langkah Pertama:
Tolong tinjau file `scripts/etl.py` dan `scripts/forecast.py` saat ini, lalu berikan kode perubahan untuk modul ETL & feature engineering terlebih dahulu.
```

---

## 🧠 Modul 2: MLOps dengan Azure ML & MLflow

**Salin teks di bawah ini:**

```markdown
## Konteks (Context)
Saya sedang membangun backend MLOps untuk proyek Aceh Resilience Monitor (ARM). Saya ingin melatih 84 model Prophet (21 komoditas × 4 daerah) dan melacak seluruh eksperimen ini (parameter, metrik MAPE/MAE/RMSE, dan model artifact) di cloud secara formal menggunakan Azure ML Studio dan MLflow.

## Peran yang Diminta (Role)
Bertindaklah sebagai Senior MLOps Engineer yang pakar dalam MLflow tracking dan Azure Machine Learning integration.

## Modul yang Dikerjakan (Exact Task)
Modul 2: Pembuatan script `scripts/train_with_mlflow.py` untuk mengotomatiskan training 84 model Prophet dan mencatat seluruh eksperimen di Azure ML Workspace via MLflow.

## File yang Relevan (Input)
- `scripts/config.py` (Membaca konstanta SHORT_NAMES, CATEGORY_MAP, dll)
- `scripts/etl.py` (Memuat `load_all_data` dan `aggregate_prices`)
- `scripts/forecast.py` (Fungsi training dan forecasting Prophet)
- File `config.json` (Berisi kredensial Azure ML Workspace yang diunduh dari portal)

## Kriteria Sukses (Acceptance Criteria)
1. Hubungkan script ke Azure ML Workspace menggunakan `Workspace.from_config(path="config.json")`.
2. Set MLflow tracking URI menggunakan URI workspace Azure ML, dan buat nama eksperimen `"arm-prophet-forecasting"`.
3. Lakukan loop untuk melatih model Prophet bagi 21 komoditas di tingkat provinsi (aggregated) dan 3 wilayah (Banda Aceh, Lhokseumawe, Meulaboh) dengan total 84 runs.
4. Di setiap run, gunakan `mlflow.start_run` dan log informasi berikut:
   - Parameter: `commodity`, `yearly_seasonality = True`, `seasonality_mode = 'multiplicative'`.
   - Metrik (di-evaluasi pada holdout test set 90 hari): `MAPE`, `MAE`, `RMSE` (hitung secara matematis).
   - Artifact: Simpan model Prophet terlatih menggunakan `mlflow.prophet.log_model(model, "prophet_model")`.
5. Script harus memiliki logging terstruktur yang rapi dan penanganan eror jika koneksi ke cloud terputus.

## Batasan (Constraint)
- Jangan commit `config.json` atau file `.pkl` lokal ke git (pastikan dikecualikan di `.gitignore`).
- Proses training harus berjalan lancar secara serial untuk ke-84 model.

## Langkah Pertama:
Tolong buatkan script utuh `scripts/train_with_mlflow.py` berdasarkan spesifikasi di atas agar saya bisa langsung menjalankannya dan memantau hasilnya di Azure ML Studio!
```

---

## ⚡ Modul 3: Daily Serverless Automation & Telegram Alerts (Azure Functions)

**Salin teks di bawah ini:**

```markdown
## Konteks (Context)
Saya sedang melakukan otomasi produksi harian untuk proyek Aceh Resilience Monitor (ARM). Saya ingin mengganti proses pembaruan data manual di komputer saya dengan **Azure Functions (Timer Trigger)** harian di cloud, yang akan men-scrape harga pangan terbaru, memperbarui Data Lake di Azure Blob Storage, mendeteksi anomali (Z-score + Prophet EWS), mengunggah dashboard JSON baru, dan mengirimkan peringatan taktis otomatis ke Telegram Bot Satgas Pangan.

## Peran yang Diminta (Role)
Bertindaklah sebagai Senior Cloud Solution Architect & Backend Developer dengan spesialisasi serverless Azure Functions dan Python.

## Modul yang Dikerjakan (Exact Task)
Modul 3: Pembuatan proyek serverless di folder `azure-functions/` menggunakan model pemrograman Python V2 dari Azure Functions Core Tools.

## File yang Relevan (Input)
- Modul pipeline lokal kita: `scripts/config.py`, `scripts/etl.py`, `scripts/anomaly.py`, `scripts/forecast.py`, `scripts/prepare_dashboard_data.py`.
- Kredensial Environment Variables: `AZURE_STORAGE_CONNECTION`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

## Kriteria Sukses (Acceptance Criteria)
1. Buat struktur folder `azure-functions/` lengkap dengan:
   - `host.json` (Konfigurasi runtime)
   - `requirements.txt` (Daftar pustaka: `azure-functions`, `azure-storage-blob`, `prophet`, `pandas`, `requests`)
   - `function_app.py` (Script serverless utama)
2. Di dalam `function_app.py`, buat sebuah fungsi Timer Trigger bernama `daily_pipeline` yang berjalan setiap hari pukul 08:00 WIB (01:00 UTC) dengan cron: `"0 0 1 * * *"`.
3. Alur kerja fungsi wajib:
   - **Scrape**: Ambil harga pangan hari ini dari API PIHPS BI.
   - **Blob Data Lake Update**: Unduh file `2026.json` dari Azure Blob Storage, tambahkan data harga hari ini, lalu unggah kembali.
   - **RAM Processing**: Gabungkan data 2021-2026 dari Blob di memori RAM, lalu jalankan modul `add_holiday_features()`, `train_prophet()`, `detect_anomalies()`, dan `detect_future_spikes()`.
   - **Dashboard Update**: Buat file ringkas `dashboard_data.json` dan unggah ke kontainer publik di Blob Storage agar dashboard live ter-refresh.
   - **Telegram Push**: Jika terdeteksi anomali kritis (Z-Score > 2σ) atau prediksi lonjakan Prophet EWS (>15%), kirimkan notifikasi Markdown yang rapi beserta rekomendasi aksi taktis ke grup Telegram Satgas Pangan.
4. Sediakan fitur *error handling* (jika scraping gagal, catat log di Azure Monitor dan gunakan harga kemarin sebagai fallback).

## Batasan (Constraint)
- Gunakan model pemrograman Azure Functions Python V2 (`azure.functions` SDK).
- Optimalkan penggunaan RAM di Functions agar tidak melebihi batas konsumsi dasar.

## Langkah Pertama:
Tolong buatkan draf struktur proyek `azure-functions` beserta kode lengkap untuk `requirements.txt` dan `function_app.py` yang siap dideploy dan diuji secara lokal!
```
