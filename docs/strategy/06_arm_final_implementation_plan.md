# 🎯 ARM Final Implementation Plan v2

> **Versi final. Satu dokumen. Semua yang harus dikerjakan.**
> 
> Deadline: **5 Juni 2026** | Sisa: **3 minggu** | Tim: **Aulia, Ilhaam, Arief**
> Target: **95/100** (Juara)

---

## 📋 Master Gap List (22 Item)

### Dari Audit Report (Kepatuhan Kurikulum)
| ID | Gap | Pilar | Priority |
|---|---|---|---|
| G1 | Kode tidak modular (SRP violation) | P2 (25%) | 🔴 |
| G2 | Duplikasi kode di 2 file | P2 (25%) | 🔴 |
| G3 | Tidak ada logging (hanya print) | P2 (25%) | 🔴 |
| G4 | Tidak ada unit test | P2 (25%) | 🔴 |

### Dari Roasting Report (Kelemahan Kompetisi)
| ID | Gap | Pilar | Priority |
|---|---|---|---|
| G5 | Threshold EWS arbitrer, tanpa justifikasi | P4 (20%) | 🟡 |
| G6 | Klaim "real-time" menyesatkan | Semua | 🟡 |
| G7 | Rekomendasi terlalu generic | P4 (20%) | 🟡 |
| G8 | Kontribusi Arief tipis | Presentasi | 🟡 |

### Dari Battle Plan (Strategi Menang)
| ID | Gap | Pilar | Priority |
|---|---|---|---|
| G9 | Tidak ada feature engineering | P1 (25%) | 🟡 |
| G10 | Hipotesis EDA tidak formal | P1 (25%) | 🟡 |
| G11 | Tidak ada baseline comparison | P2 (25%) | 🟡 |
| G12 | Tidak ada Azure ML / MLflow | P3 (30%) | 🔴 |
| G13 | Tidak ada Azure Functions | P3 (30%) | 🔴 |
| G14 | Azure hanya untuk hosting | P3 (30%) | 🔴 |
| G15 | Tidak ada Telegram notification | P4 (20%) | 🟡 |

### BARU — Dari Diskusi Terakhir (Gap Menuju 95+)
| ID | Gap | Pilar | Priority |
|---|---|---|---|
| G16 | Tidak ada notebook reprodusibilitas | P1+P2 | 🔴 |
| G17 | Tidak ada slide presentasi | Presentasi | 🔴 |
| G18 | Tidak ada error analysis / failure mode | P2 (25%) | 🟡 |
| G19 | Tidak ada pembahasan skalabilitas | P4 (20%) | 🟡 |
| G20 | Tidak ada etika & limitasi | P4 (20%) | 🟡 |
| G21 | Tidak ada data dictionary | P1 (25%) | 🟢 |
| G22 | Tidak ada drill Q&A juri | Presentasi | 🔴 |

---

## 🗓️ Overview 3 Minggu

```
MINGGU 1 (14-20 Mei): FOUNDATION
  → Refactor kode + tests + feature engineering + EDA + baseline

MINGGU 2 (21-27 Mei): AZURE & REAL-TIME
  → Azure ML + MLflow + Azure Functions + Telegram + notebook

MINGGU 3 (28 Mei - 5 Jun): PRESENTASI & SUBMIT
  → Slides + demo + drill Q&A + docs + submit
```

---

## 📅 MINGGU 1: Foundation & Code Quality (14-20 Mei)

### Hari 1-2 (Rabu-Kamis): Refactor Kode → G1, G2, G3

**👤 Ilhaam**

| Task | Detail |
|---|---|
| Buat `scripts/config.py` | Pindahkan CATEGORY_MAP, SHORT_NAMES, CATEGORY_ICONS, paths. **Satu source of truth.** |
| Buat `scripts/etl.py` | Pindahkan `load_and_clean()` (1 copy saja). Tambah `load_all_data()`. Tambah docstrings + type hints. |
| Buat `scripts/anomaly.py` | Pindahkan Z-Score logic. Buat `detect_anomalies(df, window, threshold)` dan `classify_severity(z)`. |
| Update `prepare_dashboard_data.py` | Jadikan orchestrator: import dari config, etl, anomaly. ~150 baris max. |
| Update `save_plots.py` | Ganti semua duplikasi → import dari config, etl. |
| Ganti semua `print()` → `logging` | `logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')` |

**✅ Selesai jika:** `python scripts/prepare_dashboard_data.py` tetap jalan normal.

**👤 Arief — Paralel**

| Task | Detail |
|---|---|
| Buat `docs/data_dictionary.md` → G21 | Dokumentasikan setiap kolom: nama, tipe, contoh, sumber. Contoh: `price` (float, Rp/kg, PIHPS). |
| Formalisasi hipotesis EDA → G10 | Tambah section "Hipotesis Penelitian" di awal `docs/eda_interpretation.md`. 4 hipotesis + link ke plot yang memvalidasi. |

**👤 Aulia — Paralel**

| Task | Detail |
|---|---|
| Baseline comparison → G11 | Hitung MAPE untuk: Naive Forecast, SMA-30, EMA-30. Bandingkan dengan Prophet. Tulis di `evaluation_prophet.md`. |
| Perbaiki klaim real-time → G6 | Edit `project_brief_final.md`: ganti "real-time" → "daily automated update". Edit `index.html` L42: "Monitoring Aktif" → "Update Harian Otomatis". |

---

### Hari 3-4 (Jumat-Sabtu): Tests + Features + Justifikasi → G4, G5, G9

**👤 Arief — Unit Tests → G4, G8**

Buat 3 file test (ini juga memperkuat kontribusi Arief → G8):

`tests/test_etl.py`:
```
- test_load_and_clean_returns_correct_columns()
- test_load_and_clean_drops_missing_prices()
- test_category_map_covers_all_18_commodities()
- test_add_features_creates_lag_columns()
```

`tests/test_anomaly.py`:
```
- test_stable_data_no_anomaly()
- test_spike_detected_as_critical()
- test_classify_severity_thresholds()
- test_zscore_matches_manual_calculation()
```

`tests/test_config.py`:
```
- test_all_constants_defined()
- test_short_names_match_category_map()
```

**👤 Ilhaam — Feature Engineering → G9**

Tambah di `scripts/etl.py` → fungsi `add_features(df)`:
```
1. price_lag_1d, price_lag_7d, price_lag_30d
2. rolling_mean_7d, rolling_std_7d
3. price_momentum_7d (perubahan % 7 hari)
4. month, day_of_week
5. is_holiday_season (flag Ramadan/Natal)
```

**👤 Aulia — Justifikasi Threshold → G5**

Tambah section di `evaluation_prophet.md`:
```
## Justifikasi Threshold
- Z-Score > 2σ: Shewhart Control Charts (1924), standar SPC industri
- CV > 15%: Standar BPS untuk "sangat fluktuatif"  
- Kenaikan > 20%: Ambang TPID untuk inflasi pangan signifikan
```

---

### Hari 5 (Minggu): Review & Integration Test

**👤 Seluruh Tim**
```
☐ python scripts/prepare_dashboard_data.py → no errors
☐ python scripts/save_plots.py → no errors
☐ python -m pytest tests/ → all pass
☐ Cek: tidak ada print() tersisa (hanya logging)
☐ Cek: tidak ada duplikasi CATEGORY_MAP
☐ Code review silang antar anggota
```

---

### ✅ Checkpoint Minggu 1 (20 Mei)

| Gap | Deliverable | Owner | ☐ |
|---|---|---|---|
| G1 | Kode modular (config + etl + anomaly) | Ilhaam | ☐ |
| G2 | Zero duplikasi lintas file | Ilhaam | ☐ |
| G3 | Semua print → logging | Ilhaam | ☐ |
| G4 | Unit tests (10+ test cases) | Arief | ☐ |
| G5 | Threshold punya justifikasi statistik | Aulia | ☐ |
| G6 | Klaim "real-time" diperbaiki | Aulia | ☐ |
| G9 | Feature engineering (9 features) | Ilhaam | ☐ |
| G10 | Hipotesis EDA formal | Arief | ☐ |
| G11 | Baseline comparison (Naive, SMA, EMA vs Prophet) | Aulia | ☐ |
| G21 | Data dictionary | Arief | ☐ |

---

## 📅 MINGGU 2: Azure & Real-Time Pipeline (21-27 Mei)

### Hari 6-7 (Rabu-Kamis): Azure ML + MLflow → G12, G14

**👤 Aulia**

**Hari 6: Setup**
```
1. portal.azure.com → Create → Machine Learning
   - Resource Group: rg-arm-datathon
   - Name: arm-ml-workspace
   - Region: Southeast Asia
2. Download config.json → root project
3. Tambahkan config.json ke .gitignore
4. pip install azureml-core mlflow azureml-mlflow
```

**Hari 7: Training + Logging**
```
1. Buat scripts/train_with_mlflow.py
   - Connect ke Azure ML workspace
   - Loop 18 komoditas
   - Setiap run: log params + metrics + model artifact
2. Jalankan → 18 experiments muncul di ml.azure.com
3. Screenshot MLflow experiments → docs/screenshots/mlflow_experiments.png
4. Screenshot model comparison → docs/screenshots/mlflow_comparison.png
```

**👤 Ilhaam — Paralel: Dashboard update**
```
1. Tambahkan timestamp "Data terakhir: [tanggal]" di dashboard
2. Pastikan app.js handle data format baru (jika berubah dari refactor)
3. Test dashboard masih berfungsi normal
```

**👤 Arief — Paralel: Docs + Error Analysis → G14, G18**

Buat `docs/azure_architecture.md`:
```
- Diagram arsitektur (copy dari arm_workflow_dataflow.md)
- Penjelasan setiap Azure service + kenapa dipilih
- Cost estimation
- Kenapa Azure vs AWS/GCP
```

Tambahkan section di `evaluation_prophet.md` → G18:
```
## Error Analysis & Failure Modes

### Komoditas dengan MAPE > 20%
| Komoditas | MAPE | Penyebab | Mitigasi |
|-----------|------|----------|----------|
| Cabai Merah | 29.5% | Volatilitas eksttrem, supply shock | Human review flag, monitoring manual |
| Bawang Merah | 18.2% | Siklus panen irregular | Tambah data curah hujan (future) |

### Apa Risiko Jika Model Salah?
- False positive (prediksi naik, kenyataan stabil): operasi pasar tidak perlu → biaya sia-sia kecil
- False negative (prediksi stabil, kenyataan naik): RISIKO UTAMA → mitigasi: threshold konservatif (2σ bukan 3σ) + dashboard manual review harian

### Strategi Mitigasi
ARM dirancang sebagai DECISION SUPPORT, bukan decision maker.
Model memberikan alert, manusia (TPID) membuat keputusan final.
```

---

### Hari 8-9 (Jumat-Sabtu): Azure Functions + Scraper → G13

**👤 Aulia**

**Hari 8: Development lokal**
```
1. brew install azure-functions-core-tools@4
2. mkdir azure-functions && cd azure-functions
3. func init --python --model V2
4. Buat function_app.py:
   - Timer trigger (daily 08:00 WIB)
   - Scrape PIHPS (hit internal API)
   - Anomaly detection pada data baru
   - Update dashboard_data.json di Blob
   - Kirim Telegram jika anomali
5. Test lokal: func start → trigger manual
```

**Hari 9: Deploy**
```
1. az functionapp create (consumption plan, Southeast Asia)
2. func azure functionapp publish arm-daily-pipeline
3. Set env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, AZURE_STORAGE_CONNECTION
4. Test: trigger manual dari Azure Portal
5. Screenshot: Azure Portal Functions dashboard → docs/screenshots/
```

---

### Hari 10 (Minggu): Telegram Bot → G7, G15

**👤 Arief**
```
1. Chat @BotFather → /newbot → ARM_Alert_Bot
2. Simpan token
3. Buat group "ARM Satgas Pangan" → invite bot
4. Test kirim pesan
5. Integrasikan ke function_app.py
```

Format pesan dengan rekomendasi SPESIFIK (menutup G7):
```
🚨 ARM Alert — [tanggal]

🌶️ Cabai Merah Keriting: Rp 85.000 (+42% dari MA30)
   Status: KRITIS (Z-Score: 3.1σ)
   ⚡ Aksi: Operasi pasar di Pasar Peunayong
   
🧅 Bawang Merah: Rp 52.000 (+18% dari MA30)
   Status: WASPADA (Z-Score: 2.3σ)
   ⚡ Aksi: Monitor intensif 3 hari ke depan

🔗 Dashboard: [link]
```

---

### Hari 11-12 (Senin-Selasa): Notebook + Integration → G16

**👤 Aulia — Notebook Reprodusibilitas → G16**

Buat `notebooks/analysis_walkthrough.ipynb`:
```
Cell 1: "# Aceh Resilience Monitor — Analisis End-to-End"
        Problem statement, research questions

Cell 2: "## 1. Data Loading & Cleaning"
        from scripts.etl import load_all_data
        df = load_all_data()
        df.head(), df.describe()

Cell 3: "## 2. Exploratory Data Analysis"
        Key plots: distribusi, trend, seasonality
        Link ke hipotesis yang tervalidasi

Cell 4: "## 3. Feature Engineering"
        from scripts.etl import add_features
        df = add_features(df)
        Tampilkan features baru

Cell 5: "## 4. Model Training & Evaluation"
        Baseline comparison table
        Prophet results per komoditas
        AutoML comparison (if available)

Cell 6: "## 5. Anomaly Detection"
        from scripts.anomaly import detect_anomalies
        Demo: deteksi anomali pada data real

Cell 7: "## 6. Hasil & Rekomendasi"
        Ringkasan temuan
        Rekomendasi kebijakan
        Limitasi
```

**👤 Seluruh Tim — Integration Test**
```
End-to-end test:
☐ Azure Function trigger → data masuk Blob
☐ Dashboard menampilkan data terbaru
☐ Telegram alert terkirim
☐ MLflow experiments tercatat di Azure ML Studio
☐ Notebook bisa di-run dari awal sampai akhir
☐ All unit tests pass
```

---

### ✅ Checkpoint Minggu 2 (27 Mei)

| Gap | Deliverable | Owner | ☐ |
|---|---|---|---|
| G12 | Azure ML + 18 MLflow experiments | Aulia | ☐ |
| G13 | Azure Functions deployed + daily trigger | Aulia | ☐ |
| G14 | Azure architecture documented | Arief | ☐ |
| G15 | Telegram bot active | Arief | ☐ |
| G7 | Rekomendasi spesifik per komoditas | Arief | ☐ |
| G16 | Notebook `analysis_walkthrough.ipynb` | Aulia | ☐ |
| G18 | Error analysis + failure modes documented | Arief | ☐ |

---

## 📅 MINGGU 3: Presentasi, Polish & Submit (28 Mei - 5 Juni)

### Hari 13-14 (Rabu-Kamis): Dokumentasi Final → G19, G20

**👤 Aulia — Update evaluation_prophet.md**
```
Pastikan berisi:
☐ Baseline comparison (Naive, SMA, EMA vs Prophet)
☐ AutoML comparison (jika ada)
☐ Error analysis & failure modes
☐ Justifikasi threshold
☐ Model parameter documentation (MLflow reference)
```

**👤 Ilhaam — Update project_brief + README**
```
project_brief_final.md:
☐ Update teknologi (+ Azure ML, Functions, Telegram)
☐ Update arsitektur diagram
☐ Hapus semua "real-time" → "daily automated"

README.md:
☐ Tambah section "Arsitektur Sistem" (mermaid diagram)
☐ Tambah section "Azure Services" 
☐ Tambah section "Cara Menjalankan" (setup instructions)
☐ Tambah screenshots Azure ML Studio + Functions
☐ Tambah section "Skalabilitas" → G19:
   "Arsitektur modular: untuk ekspansi ke 34 provinsi, cukup 
    tambahkan data source per provinsi. Azure Functions scale
    otomatis. Cost per provinsi: ~$0/bulan (free tier)."
```

**👤 Arief — Etika & Limitasi → G20**

Tambah di README atau buat `docs/limitations.md`:
```
## Limitasi & Pertimbangan Etis

### Limitasi Teknis
- Model univariat (belum include faktor cuaca, BBM, dll)
- Data PIHPS terbatas pada pasar tradisional
- Prophet kurang akurat untuk komoditas dengan CV > 25%

### Pertimbangan Etis
- ARM adalah decision SUPPORT, bukan decision MAKER
- Risiko false negative: harga naik tapi model bilang aman
  → Mitigasi: threshold konservatif (2σ) + human oversight
- Data publik, tidak ada informasi sensitif personal
- Transparansi: semua threshold dan metode terdokumentasi

### Apa yang Terjadi Jika Model Salah?
- TPID tetap memiliki mekanisme manual
- ARM menambah layer deteksi, BUKAN mengganti proses existing
- Dashboard menampilkan confidence interval, bukan single number
```

---

### Hari 15-16 (Jumat-Sabtu): Slide Presentasi → G17

**👤 Arief — Buat slide deck**

Struktur 12 slides (asumsi 10-15 menit presentasi):

```
Slide 1:  Cover — "Aceh Resilience Monitor"
Slide 2:  Problem — Volatilitas harga, birokrasi reaktif (data + angka)
Slide 3:  Data — 18 komoditas, 3 tahun, 14.000+ data points
Slide 4:  Methodology — CRISP-DM pipeline + diagram arsitektur
Slide 5:  EDA Highlights — 3 insight paling mengejutkan (bukan semua 13)
Slide 6:  Model — Prophet vs baselines + MAPE comparison table
Slide 7:  Azure Architecture — Diagram + 4 layanan + kenapa Azure
Slide 8:  LIVE DEMO — Buka dashboard, tunjukkan: KPI → EWS → Detail → Forecast
Slide 9:  Telegram Alert — Tunjukkan screenshot notifikasi real
Slide 10: Impact — "ARM berpotensi menghemat Rp X melalui early intervention"
Slide 11: Honest Limitations — 3 limitasi + cara mitigasi + future roadmap
Slide 12: Thank You + Q&A
```

**Speaking role:**
```
Aulia:  Slides 4, 6, 7 (teknis: methodology, model, Azure)
Ilhaam: Slides 3, 5, 8 (data, EDA, LIVE DEMO dashboard)
Arief:  Slides 2, 9, 10, 11 (problem, alert, impact, limitations)
```

**👤 Aulia + Ilhaam — Siapkan live demo**
```
Checklist demo:
☐ Dashboard loads < 3 detik
☐ KPI cards menampilkan data terbaru
☐ EWS cards menampilkan 3 komoditas kritis
☐ Klik komoditas → detail panel muncul smooth
☐ Klik "Tampilkan Prediksi 90 Hari" → forecast overlay
☐ Anomaly table menampilkan data
☐ Mobile responsive (jika juri tanya)
```

---

### Hari 17-18 (Minggu-Senin): Drill Presentasi → G22

**👤 Seluruh Tim**

**Latihan 1 (Hari 17):**
```
- Present full 12 slides + demo
- Record video (untuk self-review)
- Catat: waktu per slide, transisi yang kasar, demo yang lag
```

**Latihan 2 (Hari 18) — Fokus Q&A drill:**

| # | Pertanyaan Juri | Siapa Jawab | Jawaban Inti |
|---|---|---|---|
| 1 | "Kenapa Prophet, bukan model lain?" | Aulia | "Kami compare 4 model. Prophet MAPE terendah (7.74%) + interpretable + handle seasonality native." |
| 2 | "Model gagal di cabai. Solusinya?" | Aulia | "MAPE 29% karena supply shock. Mitigasi: ARM sebagai decision support, bukan decision maker. Human review tetap diperlukan." |
| 3 | "Sudah divalidasi stakeholder?" | Arief | "Belum formal. Ini limitasi kami. Next step: pilot dengan TPID Aceh. Namun, data dan metode kami mengacu pada standar BPS dan BI." |
| 4 | "Bisa scale ke provinsi lain?" | Ilhaam | "Ya. Arsitektur modular. Cukup tambahkan data source di Azure Functions. PIHPS mencakup 34 provinsi." |
| 5 | "Apa kontribusi masing-masing?" | Semua | Aulia: ML + Azure. Ilhaam: ETL + Frontend. Arief: Testing + Docs + Telegram. |
| 6 | "Kenapa Azure, bukan AWS?" | Aulia | "MLflow native di Azure ML. Static Web Apps zero-config. Free tier covers all. Plus: datathon Microsoft." |
| 7 | "Risiko jika model salah?" | Arief | "False negative = risiko utama. Mitigasi: threshold konservatif (2σ), confidence interval di dashboard, human oversight." |
| 8 | "Bedanya dengan dashboard BI yang sudah ada?" | Ilhaam | "PIHPS hanya tampilkan harga. ARM PREDIKSI 90 hari + DETEKSI anomali + KIRIM alert + REKOMENDASIKAN aksi." |

---

### Hari 19-20 (Selasa-Rabu): Final Review

**👤 Seluruh Tim**
```
☐ Full pipeline test: Azure Function → Blob → Dashboard → Telegram
☐ pytest tests/ → ALL PASS
☐ Notebook bisa run dari awal sampai akhir
☐ Semua link di README berfungsi
☐ .gitignore benar (config.json, .env excluded)
☐ Merge semua branch ke main
☐ Clone repo dari scratch → test README instructions
☐ Dashboard live di Azure
☐ Slide deck final
```

### Hari 21 (Kamis 5 Juni): 🚀 SUBMIT

```
☐ Final push ke GitHub
☐ Verify live dashboard
☐ Submit link repo + link dashboard
☐ 🎉 DONE — sekarang tinggal tunggu & latihan presentasi
```

---

## 📊 Proyeksi Skor Final

| Pilar | Bobot | Sekarang | Setelah Minggu 1 | Setelah Minggu 2 | Setelah Minggu 3 |
|---|:---:|:---:|:---:|:---:|:---:|
| Metodologi & EDA | 25% | 80% | 90% | 92% | **95%** |
| Model & Kode | 25% | 56% | 78% | 85% | **92%** |
| AI & Azure | 30% | 53% | 55% | 85% | **95%** |
| Insight & Solusi | 20% | 80% | 85% | 88% | **95%** |
| **TOTAL** | 100% | **66** | **76** | **87** | **95** |

---

## 🏷️ Final Role Summary

| | Aulia (ML & Azure) | Ilhaam (Code & Frontend) | Arief (Test, Docs & Comms) |
|---|---|---|---|
| **M1** | Baseline comparison, fix klaim | Refactor kode, feature engineering | Unit tests, hipotesis EDA, data dictionary |
| **M2** | Azure ML + MLflow, Azure Functions, notebook | Dashboard update, integration test | Azure architecture doc, Telegram bot, error analysis |
| **M3** | Update evaluation docs, demo prep | Update README + project brief, demo prep | Slide presentasi, etika/limitasi, Q&A drill |

> [!IMPORTANT]
> **Urutan WAJIB:**
> 1. Refactor kode DULU (Hari 1-2) — semua bergantung pada ini
> 2. Azure ML + Functions (Hari 6-9) — butuh modul yang sudah di-refactor
> 3. Presentasi TERAKHIR (Hari 15-18) — butuh semua fitur sudah jadi untuk demo
