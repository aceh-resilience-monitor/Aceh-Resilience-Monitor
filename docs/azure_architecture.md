# ☁️ ARM Azure Architecture Documentation

> **Dokumentasi arsitektur teknis untuk integrasi Azure Services ke dalam Aceh Resilience Monitor**
>
> Author: Arief (Test, Docs & Comms) — G14

---

## 📋 Daftar Isi
1. [Diagram Arsitektur](#1-diagram-arsitektur)
2. [Azure Services yang Digunakan](#2-azure-services)
3. [Justifikasi Azure vs AWS/GCP](#3-justifikasi-azure)
4. [Estimasi Biaya](#4-estimasi-biaya)
5. [Skalabilitas](#5-skalabilitas)

---

## 1. Diagram Arsitektur

```mermaid
flowchart TB
    subgraph TRIGGER ["⏰ Timer Trigger (08:00 WIB)"]
        T1["Azure Functions<br/>Cron: 0 0 1 * * *"]
    end

    subgraph INGESTION ["📥 Data Ingestion"]
        S1["PIHPS Scraper<br/>(harga harian)"]
        B1["Azure Blob Storage<br/>(arm-raw-data)<br/>2021.json ... 2026.json"]
    end

    subgraph PROCESSING ["🧠 Processing (In-Memory / RAM)"]
        E1["ETL Layer<br/>load_all_data()"]
        FE["Feature Engineering<br/>add_holiday_features()"]
        A1["Z-Score Anomaly<br/>detect_anomalies()"]
        F1["Prophet Forecasting<br/>84 models × Meugang"]
        SP["Spike Detection<br/>detect_future_spikes()"]
    end

    subgraph OUTPUT ["📤 Output Layer"]
        TG["Telegram Bot API<br/>ARM_Alert_Bot"]
        DB["dashboard_data.json<br/>(~1.2 MB, publik)"]
        ML["Azure ML Studio<br/>MLflow Metrics"]
    end

    subgraph FRONTEND ["🌐 Frontend"]
        WEB["Azure Static Web Apps<br/>Dashboard ARM"]
        USER["Browser Juri / TPID"]
    end

    T1 --> S1
    S1 --> B1
    B1 --> E1
    E1 --> FE
    FE --> A1
    FE --> F1
    A1 --> SP
    F1 --> SP
    SP --> TG
    SP --> DB
    SP --> ML
    DB --> WEB
    WEB --> USER
```

---

## 2. Azure Services yang Digunakan

| # | Service | Fungsi | Justifikasi |
|---|---------|--------|-------------|
| 1 | **Azure Blob Storage** | Data Lake (raw JSON per tahun) + Dashboard Feed (publik JSON) | Murah, scalable, REST API native. Pemisahan Private vs Public container. |
| 2 | **Azure Functions** | Serverless daily pipeline (scrape + ETL + ML + alert) | Pay-per-execution, auto-scale, timer trigger native. Consumption Plan = $0 untuk workload kecil. |
| 3 | **Azure Static Web Apps** | Hosting dashboard web (HTML/CSS/JS) | Zero-config deployment dari GitHub, SSL otomatis, CDN global. Free tier unlimited. |
| 4 | **Azure ML + MLflow** | Experiment tracking, model metrics logging, QA audit | MLflow native integration, visual comparison 84 model, production drift monitoring. |

### Alur Data per Service

```
[Azure Functions]
    │
    ├── READ ──► [Blob Storage: arm-raw-data/2021-2026.json] (Private)
    │
    ├── WRITE ─► [Blob Storage: $web/dashboard_data.json] (Public)
    │
    ├── SEND ──► [Telegram Bot API → Grup TPID Aceh]
    │
    └── LOG ───► [Azure ML Studio via MLflow API]

[Azure Static Web Apps]
    │
    └── FETCH ─► [Blob Storage: $web/dashboard_data.json] (Browser download)
```

---

## 3. Justifikasi Azure vs AWS/GCP

| Kriteria | Azure | AWS | GCP |
|----------|-------|-----|-----|
| **MLflow Integration** | Native di Azure ML ✅ | SageMaker (terpisah) | Vertex AI (terpisah) |
| **Static Web Hosting** | Static Web Apps (zero-config) ✅ | S3 + CloudFront (manual) | Firebase Hosting |
| **Serverless Functions** | Functions (Python v2) ✅ | Lambda | Cloud Functions |
| **Free Tier** | Sangat dermawan ✅ | Terbatas | Terbatas |
| **Relevansi Datathon** | Datathon Microsoft ✅ | ❌ | ❌ |

> **Kesimpulan:** Azure dipilih karena:
> 1. **MLflow terintegrasi native** di Azure ML Studio — tidak perlu setup terpisah
> 2. **Static Web Apps** zero-config dari GitHub — deploy otomatis
> 3. **Free tier mencakup semua kebutuhan** ARM — $0/bulan
> 4. **Konteks datathon Dicoding** — ekosistem Microsoft Azure

---

## 4. Estimasi Biaya

| Service | Tier | Harga/Bulan | Catatan |
|---------|------|-------------|---------|
| Azure Blob Storage | Free tier (5 GB) | **$0** | Raw data ~70 MB + dashboard ~1.2 MB |
| Azure Functions | Consumption Plan | **$0** | 1 eksekusi/hari × ~40 detik. Free: 1M eksekusi + 400K GB-s |
| Azure Static Web Apps | Free tier | **$0** | Unlimited bandwidth, SSL, CDN |
| Azure ML + MLflow | Free tier (workspace) | **$0** | Experiment tracking gratis. Compute hanya jika training di cloud. |
| **TOTAL** | | **$0/bulan** | Semua di free tier |

> **Golden Statement untuk Juri:**
> *"Seluruh infrastruktur cloud ARM berjalan di Azure Free Tier dengan total biaya $0 per bulan, membuktikan bahwa sistem monitoring pangan cerdas bisa diakses oleh pemerintah daerah mana pun tanpa hambatan biaya."*

---

## 5. Skalabilitas

### Horizontal Scaling (Ekspansi ke 34 Provinsi)

```
Saat Ini:  3 daerah × 21 komoditas = 84 model Prophet (~40 detik)
Target:   34 provinsi × 21 komoditas = bisa ribuan model

Solusi:
├── Azure Functions: Auto-scale otomatis (Consumption Plan)
├── Blob Storage: Unlimited storage
├── Data Source: PIHPS mencakup 34 provinsi nasional
└── Kode: Arsitektur modular → tambah data source = tambah provinsi
```

### Estimasi Waktu per Skala

| Skala | Model | Estimasi Waktu | Plan |
|-------|-------|----------------|------|
| 3 daerah (saat ini) | 84 | ~40 detik | Consumption (gratis) |
| 10 kota | 210 | ~2 menit | Consumption (gratis) |
| 34 provinsi | 714 | ~5-8 menit | Premium ($0-20/bulan) |
| Nasional granular | 5000+ | ~30 menit | Dedicated ($50+/bulan) |

> **Golden Statement untuk Juri:**
> *"Arsitektur ARM bersifat modular. Untuk ekspansi ke 34 provinsi, cukup tambahkan data source per provinsi di Azure Functions. PIHPS Bank Indonesia sudah mencakup seluruh Indonesia. Cost per provinsi tambahan: ~$0 (masih di free tier)."*
