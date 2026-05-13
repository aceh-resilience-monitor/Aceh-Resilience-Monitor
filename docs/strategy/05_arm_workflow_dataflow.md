# 🔄 ARM Final Project — Workflow & Data Flow Diagrams

> Semua diagram siap dipakai di README, presentasi, dan `docs/azure_architecture.md`.

---

## 1. Arsitektur Sistem (Overview)

```mermaid
graph TB
    subgraph "📥 DATA SOURCE"
        A["🌐 PIHPS BI\n(bi.go.id/hargapangan)\nHarga harian 18 komoditas"]
        B["📄 Historical Excel\n2023.xlsx / 2024.xlsx / 2025.xlsx"]
    end

    subgraph "☁️ AZURE CLOUD PLATFORM"
        subgraph "⚡ Compute"
            C["Azure Functions\nDaily Pipeline\n(Timer: 08:00 WIB)"]
        end
        subgraph "🧠 AI / ML"
            D["Azure Machine Learning\nMLflow Experiment Tracking\nModel Registry"]
        end
        subgraph "📦 Storage"
            E["Azure Blob Storage\n(Data Lake)\nraw/ + processed/ + models/"]
        end
        subgraph "🌐 Hosting"
            F["Azure Static Web Apps\nDashboard ARM\n(Public Access)"]
        end
    end

    subgraph "📲 OUTPUT"
        G["📊 Dashboard ARM\nInteractive Web App"]
        H["📱 Telegram Bot\nReal-time Alerts"]
    end

    A -->|"Scrape daily"| C
    B -->|"Initial load"| E
    C -->|"Fetch + process"| E
    E -->|"Training data"| D
    D -->|"Model + predictions"| E
    C -->|"Generate JSON"| E
    E -->|"dashboard_data.json"| F
    F --> G
    C -->|"If anomaly"| H
```

---

## 2. Data Flow End-to-End (Detail)

```mermaid
flowchart LR
    subgraph "LAYER 1: Data Ingestion"
        A1["Excel 2023-2025\n(format kotor)"]
        A2["PIHPS API\n(daily scrape)"]
    end

    subgraph "LAYER 2: ETL Pipeline"
        B1["load_and_clean()\nParsing tanggal\nHapus header romawi\nString → numeric"]
        B2["add_features()\nlag_1d, lag_7d, lag_30d\nrolling_mean, rolling_std\nmomentum, seasonality flags"]
    end

    subgraph "LAYER 3: Analytics"
        C1["Z-Score Anomaly\nMA30 + 2σ threshold\nSeverity classification"]
        C2["Prophet Forecasting\n18 models × 90 hari\nyhat + confidence interval"]
        C3["Statistical Analysis\nCV%, YoY change\nCorrelation matrix\nSeasonality Z-Score"]
    end

    subgraph "LAYER 4: Intelligence"
        D1["EWS Logic\nTop 3 komoditas kritis\nSpike > 15% detection"]
        D2["Alert Generation\nCritical / Warning\n+ Rekomendasi aksi"]
        D3["Executive Summary\nAzure OpenAI\nor data-driven fallback"]
    end

    subgraph "LAYER 5: Output"
        E1["dashboard_data.json\n→ Azure Blob Storage"]
        E2["MLflow Metrics\n→ Azure ML Studio"]
        E3["Telegram Alert\n→ Satgas Pangan"]
    end

    A1 --> B1
    A2 --> B1
    B1 --> B2
    B2 --> C1
    B2 --> C2
    B2 --> C3
    C1 --> D1
    C2 --> D1
    C1 --> D2
    C3 --> D3
    D1 --> E1
    D2 --> E1
    D3 --> E1
    C2 --> E2
    D2 --> E3
```

---

## 3. ML Training Workflow (Azure ML + MLflow)

```mermaid
flowchart TD
    A["📄 Clean Dataset\n(783 data points × 18 komoditas)"] 
    
    B["🔀 Train/Test Split\nTrain: Jan 2023 – Sep 2025\nTest: Oct – Dec 2025 (90 hari)"]
    
    C["🏋️ Model Training"]
    
    subgraph "MLflow Experiment: arm-prophet-forecasting"
        D1["Run 1: Beras Bawah I\nParams: yearly_seasonality=True\nMetrics: MAPE=1.39%"]
        D2["Run 2: Cabai Merah\nParams: yearly_seasonality=True\nMetrics: MAPE=29.54%"]
        D3["...\n(18 runs total)"]
    end

    E["📊 Baseline Comparison"]
    
    subgraph "Perbandingan Model"
        F1["Naive Forecast → MAPE ~15%"]
        F2["SMA-30 → MAPE ~12%"]
        F3["Prophet → MAPE 7.74% ✅"]
        F4["AutoML (15+ models) → compare"]
    end

    G["🏆 Model Selection\nProphet dipilih:\n- MAPE terendah\n- Interpretable\n- Handle seasonality"]

    H["💾 Model Registry\nAzure ML Model Store\n18 model artifacts (.pkl)"]

    A --> B --> C
    C --> D1
    C --> D2
    C --> D3
    C --> E
    E --> F1
    E --> F2
    E --> F3
    E --> F4
    F3 --> G --> H
```

---

## 4. Daily Automated Pipeline (Azure Functions)

```mermaid
flowchart TD
    A["⏰ Timer Trigger\nSetiap hari 08:00 WIB"]
    
    B["🌐 Step 1: Scrape PIHPS\nFetch harga 18 komoditas\nHari ini dari bi.go.id"]
    
    C{"Data berhasil\ndi-scrape?"}
    
    D["📦 Step 2: Save to Blob\nAppend ke historical_data.json\ndi Azure Blob Storage"]
    
    E["🔍 Step 3: Anomaly Check\nHitung Z-Score harga hari ini\nvs MA30 historis"]
    
    F{"Anomali\nterdeteksi?"}
    
    G["📊 Step 4: Update Dashboard\nGenerate dashboard_data.json\nUpload ke Blob Storage"]
    
    H["📲 Step 5: Send Alert\nTelegram notification\nke Satgas Pangan"]
    
    I["📝 Step 6: Log\nCatat hasil pipeline\ndi Azure Monitor"]
    
    J["⚠️ Error Handler\nLog error\nRetry 3x\nFallback: gunakan data kemarin"]

    A --> B --> C
    C -->|"Ya"| D --> E --> F
    C -->|"Gagal"| J --> I
    F -->|"Ya (Z>2σ)"| H --> G --> I
    F -->|"Tidak"| G
    
    style H fill:#ef4444,color:#fff
    style A fill:#3b82f6,color:#fff
    style G fill:#22c55e,color:#fff
```

---

## 5. Alert & Notification Flow

```mermaid
flowchart LR
    subgraph "Detection Engine"
        A["Harga Hari Ini\n(dari PIHPS)"]
        B["MA30 + Std30\n(dari historis)"]
        C["Z-Score =\n(Harga - MA30) / Std30"]
    end

    subgraph "Classification"
        D{"|Z| > 3σ ?"}
        E["🔴 KRITIS"]
        F{"|Z| > 2σ ?"}
        G["🟡 WASPADA"]
        H["🟢 AMAN"]
    end

    subgraph "Action"
        I["📲 Telegram Alert\n+ Rekomendasi aksi spesifik"]
        J["📊 Dashboard Update\nStatus badge berubah"]
        K["📝 Log saja\nTidak ada aksi"]
    end

    A --> C
    B --> C
    C --> D
    D -->|"Ya"| E --> I
    D -->|"Tidak"| F
    F -->|"Ya"| G --> I
    F -->|"Tidak"| H --> K
    E --> J
    G --> J
    
    style E fill:#ef4444,color:#fff
    style G fill:#f59e0b,color:#000
    style H fill:#22c55e,color:#fff
```

---

## 6. File Map — Kode ↔ Arsitektur (Complete)

```mermaid
graph LR
    subgraph "scripts/"
        S1["config.py\n(constants)"]
        S2["etl.py\n(load + clean + features)"]
        S3["anomaly.py\n(Z-Score detection)"]
        S4["forecast.py\n(Prophet training)"]
        S5["train_with_mlflow.py\n(MLflow logging)"]
        S6["prepare_dashboard_data.py\n(orchestrator)"]
        S7["save_plots.py\n(EDA visualizations)"]
    end

    subgraph "azure-functions/"
        AF["function_app.py\n(daily pipeline + Telegram)"]
    end

    subgraph "notebooks/"
        NB["analysis_walkthrough.ipynb\n(reprodusibilitas end-to-end)"]
    end

    subgraph "dashboard/"
        D1["index.html"]
        D2["app.js"]
        D3["style.css"]
        D4["dashboard_data.json"]
    end

    subgraph "tests/"
        T1["test_etl.py"]
        T2["test_anomaly.py"]
        T3["test_forecast.py"]
        T4["test_config.py"]
    end

    subgraph "docs/"
        DOC1["eda_interpretation.md\n(+ hipotesis formal)"]
        DOC2["azure_architecture.md"]
        DOC3["data_dictionary.md"]
        DOC4["limitations.md\n(etika + skalabilitas)"]
    end

    subgraph "Azure Services"
        AZ1["Azure Blob Storage"]
        AZ2["Azure ML + MLflow"]
        AZ3["Azure Static Web Apps"]
        AZ4["Azure Functions"]
        AZ5["Telegram Bot API"]
    end

    S1 --> S2
    S1 --> S3
    S1 --> S4
    S2 --> S6
    S3 --> S6
    S4 --> S6
    S4 --> S5
    S5 --> AZ2
    S6 --> D4
    D4 --> AZ1
    AF --> AZ4
    AF --> AZ1
    AF --> AZ5
    D1 --> AZ3
    D2 --> AZ3
    D3 --> AZ3
    NB -.->|"imports"| S2
    NB -.->|"imports"| S3
    T1 -.->|"tests"| S2
    T2 -.->|"tests"| S3
    T3 -.->|"tests"| S4
    T4 -.->|"tests"| S1
```

---

## 7. Deliverables Map — File ↔ Pilar Rubrik

```mermaid
graph TD
    subgraph "Pilar 1: Metodologi & EDA — 25%"
        P1A["docs/eda_interpretation.md\n(hipotesis + 13 plot)"]
        P1B["scripts/etl.py\n(cleaning + feature engineering)"]
        P1C["docs/data_dictionary.md"]
        P1D["notebooks/analysis_walkthrough.ipynb"]
    end

    subgraph "Pilar 2: Model & Kualitas Kode — 25%"
        P2A["scripts/config.py + etl.py + anomaly.py\n(modular architecture)"]
        P2B["evaluation_prophet.md\n(baseline + error analysis)"]
        P2C["tests/\n(unit tests)"]
        P2D["scripts/train_with_mlflow.py\n(experiment tracking)"]
    end

    subgraph "Pilar 3: AI & Azure — 30%"
        P3A["Azure ML + MLflow\n(18 experiments logged)"]
        P3B["Azure Functions\n(daily automated pipeline)"]
        P3C["Azure Blob Storage\n(data lake)"]
        P3D["Azure Static Web Apps\n(dashboard hosting)"]
        P3E["docs/azure_architecture.md"]
    end

    subgraph "Pilar 4: Insight & Solusi — 20%"
        P4A["dashboard/app.js\n(EWS cards + rekomendasi)"]
        P4B["Telegram Bot\n(push notifications)"]
        P4C["docs/limitations.md\n(etika + skalabilitas)"]
        P4D["Slide presentasi\n(storytelling)"]
    end
```

---

## 8. Workflow Ringkas (Untuk Presentasi — 1 Slide)

```mermaid
graph LR
    A["🌐 Data\nPIHPS"] 
    B["⚡ Pipeline\nAzure Functions"]
    C["🧠 AI\nAzure ML + Prophet"]
    D["📦 Storage\nAzure Blob"]
    E["📊 Dashboard\nAzure Static Web"]
    F["📲 Alert\nTelegram Bot"]

    A -->|"daily"| B
    B -->|"train"| C
    C -->|"model + predictions"| D
    B -->|"process"| D
    D -->|"serve"| E
    B -->|"if anomaly"| F

    style A fill:#6366f1,color:#fff
    style B fill:#f59e0b,color:#000
    style C fill:#8b5cf6,color:#fff
    style D fill:#3b82f6,color:#fff
    style E fill:#22c55e,color:#fff
    style F fill:#ef4444,color:#fff
```
