# 📋 Strategi Menang: Analisis Rubrik Assessment vs Kondisi ARM

> **Deadline:** 5 Juni 2026 (sisa **~3 minggu**)
> **Situasi:** Top 20, harus masuk Top 10

---

## 🎯 Rubrik Assessment — 4 Pilar Penilaian

| # | Pilar | Bobot | Deskripsi |
|---|---|:---:|---|
| 1 | **Metodologi dan Eksplorasi Data** | **25%** | Kualitas EDA, data cleaning, dan feature engineering |
| 2 | **Performa Model dan Kualitas Kode** | **25%** | Ketepatan metrik evaluasi (Akurasi, F1-Score, RMSE, dll.) dari model ML/Deep Learning |
| 3 | **Pemanfaatan AI & Microsoft Azure** | **30%** | Ketepatan, efektivitas, dan relevansi penggunaan AI serta layanan Microsoft Azure dalam solusi |
| 4 | **Insight dan Solusi Strategis** | **20%** | Kemampuan menerjemahkan hasil model menjadi actionable insights yang dapat ditindaklanjuti |

---

## 🔍 Analisis Per Pilar: Kondisi ARM Saat Ini vs Yang Diharapkan

---

### Pilar 1: Metodologi dan Eksplorasi Data (25%)

#### Estimasi Skor Saat Ini: 🟢 **20/25** (80%)

**✅ Yang Sudah Kuat:**

| Aspek | Evidence | File |
|---|---|---|
| EDA berkualitas | 13 plot komprehensif (boxplot, violin, time series, heatmap, correlation, seasonality, daily returns, stacked area) | `scripts/save_plots.py` |
| Interpretasi EDA | Setiap plot punya interpretasi mendalam, temuan utama, dan implikasi bisnis | `docs/eda_interpretation.md` |
| Data cleaning | Handle: format tanggal non-standar, angka romawi, string rupiah, missing values | `scripts/prepare_dashboard_data.py` |
| Data profiling | Statistik deskriptif 3 tahun, CV%, YoY analysis terdokumentasi | `data_analysis.md` |

**⚠️ Gap yang Harus Ditutup:**

| Gap | Dampak | Solusi |
|---|---|---|
| **Feature Engineering hampir tidak ada** | Rubrik menyebut ini EKSPLISIT. Saat ini ARM hanya pakai raw price → Prophet. Tidak ada engineered features. | Tambahkan features: lagged prices, rolling statistics, day-of-week encoding, holiday flags, seasonal decomposition |
| **Hipotesis EDA tidak formal** | Tidak ada dokumen yang menyatakan hipotesis sebelum EDA | Tambahkan section "Hipotesis Penelitian" di `docs/eda_interpretation.md` |
| **Tidak ada outlier treatment strategy** | Outlier terdeteksi tapi tidak ada dokumen strategi penanganannya (keep vs cap vs remove) | Dokumentasikan keputusan outlier handling |

#### 🎯 Action Plan — Pilar 1

**Task 1.1: Feature Engineering (HIGH PRIORITY)**
```
Estimasi: 3-4 jam
Assignee: Ilhaam atau Aulia

Buat features baru di prepare_dashboard_data.py:
1. lag_1d, lag_7d, lag_30d (harga kemarin, minggu lalu, bulan lalu)
2. rolling_mean_7d, rolling_mean_30d (sudah ada MA30, tambah MA7)
3. rolling_std_7d (volatilitas jangka pendek)
4. price_momentum (perubahan harga 7 hari terakhir)
5. day_of_week encoding (Senin=0, Jumat=4)
6. month encoding (untuk seasonality)
7. is_ramadan flag (binary, menggunakan tanggal Ramadan)
8. is_year_end flag (Nov-Dec = 1)

Catatan: Features ini bukan untuk dipakai Prophet (yang sudah handle 
seasonality sendiri), tapi untuk MENUNJUKKAN kepada juri bahwa kalian
TAHU feature engineering. Dokumentasikan prosesnya.
```

**Task 1.2: Formalisasi Hipotesis EDA (QUICK WIN)**
```
Estimasi: 30 menit
Assignee: Arief

Tambahkan section di docs/eda_interpretation.md:

## Hipotesis Penelitian
H1: Komoditas hortikultura (cabai, bawang) memiliki volatilitas 
    signifikan lebih tinggi dibanding komoditas stabil (beras, minyak)
H2: Terdapat pola musiman yang berkorelasi dengan hari raya keagamaan
H3: Harga komoditas dalam kategori yang sama bergerak secara sinergis
H4: Komoditas dengan CV > 15% memiliki MAPE prediksi yang lebih tinggi

Kemudian di setiap plot interpretasi, tautkan kembali ke hipotesis:
"Plot ini memvalidasi H1 — CV cabai merah (35%) vs beras (4.7%)"
```

---

### Pilar 2: Performa Model dan Kualitas Kode (25%)

#### Estimasi Skor Saat Ini: 🟡 **14/25** (56%)

> [!WARNING]
> **Ini pilar terlemah kamu saat ini.** Rubrik secara EKSPLISIT menyebut:
> - "Model ML/**Deep Learning**" ← ARM tidak punya Deep Learning
> - "**Kualitas Kode**" ← kode belum modular, belum ada test, belum ada logging
> - "**F1-Score**" disebut sebagai contoh metrik ← ARM tidak punya classification task

**✅ Yang Sudah Ada:**

| Aspek | Evidence |
|---|---|
| Metrik evaluasi forecasting | MAE, RMSE, MAPE per 18 komoditas |
| Backtesting methodology | Train/Test split holdout 90 hari |
| Evaluasi per kategori | Komoditas dikategorikan: Sangat Akurat / Cukup / Sulit Diprediksi |
| Analisis kegagalan | Dijelaskan kenapa cabai/bawang sulit diprediksi |

**🔴 Gap KRITIS:**

| Gap | Dampak | Severity |
|---|---|:---:|
| **Tidak ada Deep Learning** | Rubrik menyebut "ML/Deep Learning" secara eksplisit. Prophet saja mungkin dianggap kurang. | 🔴 Tinggi |
| **Kualitas kode buruk** | Tidak modular, duplikasi, tidak ada test, tidak ada logging | 🔴 Tinggi |
| **Tidak ada baseline comparison** | Tidak bisa menunjukkan bahwa Prophet lebih baik dari metode sederhana | 🟡 Medium |
| **Tidak ada cross-validation** | Hanya 1x train-test split. Tidak ada time-series CV (expanding window) | 🟡 Medium |

#### 🎯 Action Plan — Pilar 2

**Task 2.1: Tambah Deep Learning Model — LSTM (HIGHEST PRIORITY)**
```
Estimasi: 6-8 jam
Assignee: Aulia

Buat scripts/lstm_forecast.py:
1. Buat LSTM sederhana untuk 3-5 komoditas paling volatil 
   (Cabai Merah, Cabai Rawit, Bawang Merah)
2. Bandingkan MAPE LSTM vs Prophet
3. Tujuannya BUKAN mengganti Prophet — tapi menunjukkan bahwa 
   kalian SUDAH COBA dan membandingkan
4. Jika LSTM lebih baik → bonus! 
   Jika Prophet lebih baik → "Kami memilih Prophet karena terbukti 
   lebih akurat untuk data kami + lebih interpretable"

Library: PyTorch atau TensorFlow/Keras
Architecture: Simple LSTM → Dense → output

Ini WAJIB karena rubrik menyebut "Deep Learning" secara eksplisit.
```

**Task 2.2: Baseline Comparison (MEDIUM PRIORITY)**
```
Estimasi: 2 jam
Assignee: Aulia

Tambahkan di evaluate_prophet.ipynb atau buat script baru:

Baseline models:
1. Naive Forecast (prediksi = harga hari terakhir)
2. Simple Moving Average 30 hari
3. Exponential Moving Average

Hitung MAPE untuk setiap baseline.
Buat tabel comparison:
| Model | Avg MAPE | Best For |
|-------|----------|----------|
| Naive | ~15% | - |
| SMA30 | ~12% | - |
| EMA | ~11% | - |
| Prophet | 7.74% | Overall ✅ |
| LSTM | ~X% | Volatile commodities |

Ini menunjukkan "systematic improvement" yang diminta kurikulum.
```

**Task 2.3: Refactor Kualitas Kode (HIGH PRIORITY)**
```
Estimasi: 3-4 jam
Assignee: Ilhaam atau Arief

1. Buat scripts/config.py (single source of truth)
   - CATEGORY_MAP, SHORT_NAMES, CATEGORY_ICONS, DATA_DIR, dll.

2. Buat scripts/etl.py
   - Pindahkan load_and_clean() ke sini
   - Fungsi: load_all_data(), clean_data(), add_features()

3. Buat scripts/anomaly.py
   - Pindahkan Z-Score logic
   - Fungsi: detect_anomalies(), classify_severity()

4. Buat scripts/forecast.py
   - Pindahkan Prophet logic
   - Fungsi: train_prophet(), predict_future(), detect_future_spikes()

5. Update prepare_dashboard_data.py jadi ORCHESTRATOR:
   from config import *
   from etl import load_all_data, clean_data
   from anomaly import detect_anomalies
   from forecast import train_prophet, predict_future

6. Ganti semua print() → logging
7. Tambahkan type hints
8. Tambahkan docstrings
```

**Task 2.4: Unit Tests (MEDIUM PRIORITY)**
```
Estimasi: 2-3 jam
Assignee: Arief (tugas yang bisa dikerjakan tanpa deep ML knowledge)

Buat tests/test_etl.py:
- test_load_and_clean_returns_correct_shape()
- test_load_and_clean_handles_missing_values()
- test_category_map_covers_all_commodities()

Buat tests/test_anomaly.py:
- test_zscore_normal_data_no_anomaly()
- test_zscore_spike_detected()
- test_severity_classification()

Buat tests/test_forecast.py:
- test_prophet_output_has_correct_columns()
- test_future_spike_detection()
```

---

### Pilar 3: Pemanfaatan AI & Microsoft Azure (30%) — BOBOT TERBESAR

#### Estimasi Skor Saat Ini: 🟡 **16/30** (53%)

> [!CAUTION]
> **Ini pilar dengan bobot TERBESAR (30%) dan skor kamu paling rendah.** Ini harus jadi fokus utama perbaikan.

**✅ Yang Sudah Ada:**

| Azure Service | Implementasi | Evidence |
|---|---|---|
| Azure Blob Storage | Data Lake endpoint untuk JSON | `app.js` line 66 |
| Azure Static Web Apps | Deployment dashboard | `staticwebapp.config.json` |
| Azure OpenAI (optional) | Executive summary generation | `prepare_dashboard_data.py` L476-520 |

**🔴 Gap KRITIS:**

| Gap | Kenapa Ini Masalah |
|---|---|
| **Tidak ada Azure Machine Learning** | Rubrik bilang "layanan Microsoft Azure" — Azure ML adalah layanan ML flagship Microsoft |
| **Tidak ada MLflow** | Kurikulum secara eksplisit menyebutkan MLflow untuk experiment tracking |
| **Tidak ada Azure Functions** | Pipeline masih manual (run Python script). Seharusnya otomatis. |
| **AI usage dangkal** | Prophet + optional OpenAI ≠ "efektif menggunakan AI". Perlu show depth. |

#### 🎯 Action Plan — Pilar 3

**Task 3.1: Azure Machine Learning + MLflow (HIGHEST PRIORITY)**
```
Estimasi: 6-8 jam
Assignee: Aulia

Langkah:
1. Buat Azure ML Workspace (free tier available)
2. Setup MLflow tracking di workspace
3. Log semua experiment Prophet ke MLflow:
   - Parameters: yearly_seasonality, weekly_seasonality, dll.
   - Metrics: MAE, RMSE, MAPE per komoditas
   - Artifacts: model files, forecast plots
4. Log juga experiment LSTM ke MLflow
5. Buat comparison table dari MLflow UI
6. Screenshot MLflow dashboard → masukkan ke presentasi

Ini LANGSUNG address gap terbesar (30% bobot).
```

**Task 3.2: Azure Functions untuk Pipeline Automation (MEDIUM PRIORITY)**
```
Estimasi: 4-5 jam
Assignee: Aulia atau Ilhaam

Buat Azure Function (Timer Trigger) yang:
1. Dibuat scheduler (misal: daily)
2. Run Prophet pipeline
3. Upload hasil ke Azure Blob Storage
4. Dashboard otomatis ter-update

Ini mengubah ARM dari "dashboard statis" → "pipeline otomatis"
dan menjustifikasi klaim "monitoring aktif".
```

**Task 3.3: Perkuat Azure OpenAI Integration (QUICK WIN)**
```
Estimasi: 2-3 jam
Assignee: Aulia

Saat ini Azure OpenAI hanya untuk executive summary (1 call).
Perkuat:
1. Gunakan Azure OpenAI untuk INTERPRETASI otomatis per komoditas
   - Input: data anomali + forecast per komoditas
   - Output: rekomendasi kebijakan spesifik per komoditas
2. Tambahkan ke dashboard sebagai "AI Analysis" tab/section
3. Ini menunjukkan penggunaan AI yang BERMAKNA, bukan sekadar 
   text generation

Atau minimal: pastikan Azure OpenAI berfungsi (bukan fallback)
saat demo ke juri.
```

**Task 3.4: Dokumentasikan Azure Architecture (QUICK WIN)**
```
Estimasi: 1 jam
Assignee: Arief

Buat docs/azure_architecture.md:
1. Diagram arsitektur Azure (Azure Blob → Azure ML → Azure Functions → 
   Azure Static Web Apps)
2. Justifikasi pemilihan setiap service
3. Cost estimation (free tier vs production)
4. Comparison: kenapa Azure vs AWS/GCP untuk use case ini
5. Security considerations (CORS policy, access keys)
```

---

### Pilar 4: Insight dan Solusi Strategis (20%)

#### Estimasi Skor Saat Ini: 🟢 **16/20** (80%)

**✅ Yang Sudah KUAT:**

| Aspek | Evidence |
|---|---|
| Actionable insights | EWS Cards: "Segera lakukan operasi pasar / inspeksi rantai pasok" |
| Rekomendasi per status | Critical → operasi pasar, Warning → monitor + siapkan rencana |
| Executive summary | Data-driven narrative untuk Gubernur |
| Konteks lokal | Spesifik untuk Aceh, komoditas lokal, kebijakan daerah |

**⚠️ Gap untuk Skor Sempurna:**

| Gap | Solusi |
|---|---|
| **Rekomendasi terlalu generic** | Buat rekomendasi SPESIFIK per komoditas (contoh: untuk cabai → "Koordinasi dengan petani di Takengon untuk antisipasi panen berikutnya") |
| **Tidak ada cost-benefit analysis** | Tambahkan estimasi: "Jika pemerintah bertindak saat status WASPADA, estimasi penghematan Rp X miliar per tahun" |
| **Belum ada validasi stakeholder** | Kontak minimal 1 ahli ekonomi / pegawai Dinas Perdagangan untuk validasi |
| **Tidak ada decision tree untuk stakeholder** | Buat flowchart: "Jika status X → lakukan Y → eskalasi ke Z" |

#### 🎯 Action Plan — Pilar 4

**Task 4.1: Buat Decision Framework (MEDIUM)**
```
Estimasi: 2 jam
Assignee: Tim bersama

Buat docs/decision_framework.md:
Flowchart untuk TPID / Satgas Pangan:

Status KRITIS → Tindakan dalam 24 jam:
  1. Operasi pasar di pasar tradisional terbesar
  2. Aktivasi cadangan pangan strategis daerah  
  3. Koordinasi dengan BULOG provinsi
  4. Rilis informasi harga ke media

Status WASPADA → Tindakan dalam 7 hari:
  1. Monitor harga harian intensif
  2. Siapkan rencana intervensi
  3. Koordinasi dengan distributor
  
Status AMAN → Routine:
  1. Monitor mingguan
  2. Update proyeksi bulanan
```

**Task 4.2: Tambahkan Impact Estimation (QUICK WIN)**
```
Estimasi: 1-2 jam
Assignee: Arief

Riset sederhana:
- Berapa kerugian ekonomi akibat lonjakan harga pangan di Aceh?
- Berapa subsidi yang dikeluarkan pemerintah untuk operasi pasar?
- Jika ARM bisa mendeteksi 7 hari lebih awal → berapa saving?

Masukkan angka-angka ini ke presentasi dan README.
"ARM berpotensi menghemat Rp X miliar per tahun melalui 
early intervention pada komoditas kritis."
```

---

## 📅 Timeline 3 Minggu (14 Mei - 5 Juni 2026)

### Minggu 1 (14-20 Mei): Foundation & Critical Fixes

| Hari | Aulia | Ilhaam | Arief |
|---|---|---|---|
| **Rabu 14** | Setup Azure ML workspace + MLflow | Mulai refactor: `config.py` + `etl.py` | Formalisasi hipotesis EDA |
| **Kamis 15** | MLflow: log Prophet experiments | Refactor: `anomaly.py` + `forecast.py` | Dokumentasi Azure architecture |
| **Jumat 16** | MLflow: selesaikan logging | Update `prepare_dashboard_data.py` (orchestrator) | Mulai unit tests |
| **Sabtu 17** | Mulai LSTM model (Cabai, Bawang) | Ganti print() → logging + type hints | Unit tests lanjut |
| **Minggu 18** | LSTM training + evaluation | Review + test refactored code | Unit tests selesai |
| **Senin 19** | LSTM vs Prophet comparison | Feature engineering | Decision framework doc |
| **Selasa 20** | ✅ **Checkpoint**: LSTM + MLflow selesai | ✅ **Checkpoint**: Refactor selesai | ✅ **Checkpoint**: Tests + docs selesai |

### Minggu 2 (21-27 Mei): Azure Integration & Enhancement

| Hari | Aulia | Ilhaam | Arief |
|---|---|---|---|
| **Rabu 21** | Azure Functions setup | Dashboard: tampilkan LSTM vs Prophet | Impact estimation research |
| **Kamis 22** | Azure Functions: pipeline automation | Dashboard: AI Analysis section baru | Baseline comparison (Naive, SMA, EMA) |
| **Jumat 23** | Azure OpenAI: interpretasi per komoditas | Dashboard: responsive polish | Update README + evaluation docs |
| **Sabtu 24** | Integration testing | Integration testing | Integration testing |
| **Minggu 25** | Bug fixes | Bug fixes | Mulai slide presentasi |
| **Senin 26** | Code review keseluruhan | Code review keseluruhan | Slide presentasi draft |
| **Selasa 27** | ✅ **Checkpoint**: Azure pipeline end-to-end | ✅ **Checkpoint**: Dashboard final | ✅ **Checkpoint**: Docs + slides draft |

### Minggu 3 (28 Mei - 5 Juni): Polish & Submit

| Hari | Seluruh Tim |
|---|---|
| **Rabu 28** | Final testing: jalankan seluruh pipeline dari 0 |
| **Kamis 29** | Polish README, evaluation docs, all documentation |
| **Jumat 30** | Latihan presentasi #1 — record & review |
| **Sabtu 31** | Fix berdasarkan review presentasi |
| **Minggu 1 Jun** | Latihan presentasi #2 |
| **Senin 2** | Final code review, merge semua branch |
| **Selasa 3** | Final documentation check |
| **Rabu 4** | **Buffer day** — fix last-minute issues |
| **Kamis 5** | 🚀 **SUBMIT** |

---

## 📊 Proyeksi Skor: Sebelum vs Sesudah Perbaikan

| Pilar | Bobot | Skor Saat Ini | Target Setelah Fix | Delta |
|---|:---:|:---:|:---:|:---:|
| Metodologi & EDA | 25% | 20/25 (80%) | **23/25 (92%)** | +3 |
| Performa Model & Kode | 25% | 14/25 (56%) | **21/25 (84%)** | +7 |
| AI & Azure | 30% | 16/30 (53%) | **25/30 (83%)** | +9 |
| Insight & Solusi | 20% | 16/20 (80%) | **18/20 (90%)** | +2 |
| **TOTAL** | **100%** | **66/100** | **87/100** | **+21** |

> [!IMPORTANT]
> **Kenaikan terbesar datang dari Pilar 3 (Azure, +9 poin) dan Pilar 2 (Model+Kode, +7 poin).** Ini harus jadi prioritas utama.

---

## 🎯 Prioritas Berdasarkan ROI (Return on Investment)

### 🔴 HARUS DILAKUKAN (Deal-breaker jika tidak ada)

| # | Task | Impact | Effort | ROI |
|---|---|---|---|:---:|
| 1 | **LSTM model** (minimal 3 komoditas) | Pilar 2: +5 | 6-8 jam | ⭐⭐⭐⭐⭐ |
| 2 | **Azure ML + MLflow** | Pilar 3: +6 | 6-8 jam | ⭐⭐⭐⭐⭐ |
| 3 | **Refactor kode** (modular) | Pilar 2: +3 | 3-4 jam | ⭐⭐⭐⭐ |
| 4 | **Feature engineering** | Pilar 1: +2 | 3-4 jam | ⭐⭐⭐⭐ |

### 🟡 SEBAIKNYA DILAKUKAN (Differentiator kuat)

| # | Task | Impact | Effort | ROI |
|---|---|---|---|:---:|
| 5 | Azure Functions (automation) | Pilar 3: +3 | 4-5 jam | ⭐⭐⭐ |
| 6 | Baseline comparison | Pilar 2: +2 | 2 jam | ⭐⭐⭐⭐ |
| 7 | Unit tests | Pilar 2: +1 | 2-3 jam | ⭐⭐⭐ |
| 8 | Logging (print→logging) | Pilar 2: +1 | 1 jam | ⭐⭐⭐⭐ |

### 🟢 NICE TO HAVE (Bonus points)

| # | Task | Impact | Effort | ROI |
|---|---|---|---|:---:|
| 9 | Azure OpenAI per komoditas | Pilar 3: +1 | 2-3 jam | ⭐⭐ |
| 10 | Validasi stakeholder | Pilar 4: +2 | Variabel | ⭐⭐⭐ |
| 11 | Impact estimation | Pilar 4: +1 | 1-2 jam | ⭐⭐⭐ |
| 12 | Decision framework doc | Pilar 4: +1 | 2 jam | ⭐⭐ |

---

## ⚡ Quick Wins — Bisa Dikerjakan HARI INI

1. ✍️ Formalisasi hipotesis EDA (30 menit)
2. 📝 Ganti semua print() → logging (1 jam, bisa pakai AI)
3. 📦 Buat `config.py` + pindahkan duplikasi (1 jam)
4. 🗑️ Hapus klaim "real-time" di project brief (5 menit)
5. 📋 Buat skeleton `tests/` folder + 2-3 test sederhana (1 jam)

Total quick wins: **~3.5 jam** → immediate improvement di 3 pilar sekaligus.
