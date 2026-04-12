# 🛡️ Aceh Resilience Monitor (ARM)

**Platform Intelijen Harga Pangan** — Datathon Dicoding × Microsoft Elevate Training Center

> Topik: Ketahanan Pangan & Agrikultur Modern

ARM adalah platform intelijen bisnis end-to-end untuk mendeteksi anomali harga pangan strategis. Platform ini menyatukan data harian dari 18 komoditas pangan selama 3 tahun (2023–2025) menjadi dashboard interaktif yang siap pakai untuk pengambilan keputusan.

---

## 📁 Struktur Proyek

```
datathon-dicoding/
├── data/                       # Data mentah
│   ├── 2023.xlsx
│   ├── 2024.xlsx
│   └── 2025.xlsx
├── scripts/                    # Script pengolahan data
│   ├── eda.ipynb               # Notebook EDA (Jupyter)
│   ├── save_plots.py           # Generate 13 plot EDA
│   └── prepare_dashboard_data.py  # Transform data → JSON dashboard
├── plots/                      # Output 13 plot EDA (PNG)
├── dashboard/                  # Web dashboard ARM
│   ├── index.html              # Halaman utama
│   ├── style.css               # Styling (dark theme)
│   ├── app.js                  # Logika Chart.js
│   ├── dashboard_data.js       # Data embedded (generated)
│   └── dashboard_data.json     # Data JSON (generated)
├── docs/                       # Dokumentasi
│   ├── project_brief.md        # Brief proyek datathon
│   ├── data_analysis.md        # Analisis data lengkap
│   ├── eda_interpretation.md   # Interpretasi 13 plot EDA
│   └── fabric_recommendation.md # Rekomendasi arsitektur Microsoft Fabric
├── requirements.txt            # Dependencies Python
└── README.md
```

---

## 🚀 Quick Start

### 1. Buka Dashboard (tanpa instalasi)

```bash
open dashboard/index.html
```

Dashboard bisa langsung dibuka di browser — tidak perlu server.

### 2. Regenerasi Data (opsional)

Jika ingin memproses ulang dari data mentah:

```bash
# Install dependencies
pip install -r requirements.txt

# Generate plot EDA
python scripts/save_plots.py

# Generate data dashboard
python scripts/prepare_dashboard_data.py

# Buat JS embedded (untuk akses file://)
cd dashboard && echo "const DASHBOARD_DATA = $(cat dashboard_data.json);" > dashboard_data.js
```

---

## 🛒 Komoditas yang Dipantau (18 Komoditas)

| Kategori | Komoditas |
|----------|-----------|
| **Beras** | Bawah I, Bawah II, Medium I, Medium II, Super I, Super II |
| **Daging Ayam** | Ayam Ras Segar |
| **Daging Sapi** | Kualitas 1 |
| **Telur Ayam** | Ras Segar |
| **Bawang Merah** | Ukuran Sedang |
| **Bawang Putih** | Ukuran Sedang |
| **Cabai Merah** | Keriting |
| **Cabai Rawit** | Hijau |
| **Minyak Goreng** | Curah, Kemasan Bermerk 1, Kemasan Bermerk 2 |
| **Gula Pasir** | Kualitas Premium, Lokal |

---

## 📈 Temuan Utama

| Insight | Detail |
|---------|--------|
| **Komoditas paling inflasioner** | Minyak Goreng Curah (+29.5%), Daging Ayam (+29.3%) |
| **Komoditas paling volatil** | Cabai Merah Keriting (CV 35.5% di 2025) |
| **Komoditas paling stabil** | Daging Sapi (CV 2%), satu-satunya yang turun (-0.2%) |
| **Efek Ramadan/Lebaran** | Daging Sapi naik tajam hanya di bulan Maret (Z = +2.82) |
| **Regime change** | Beras mengalami jump harga di awal 2024, tidak pernah turun |
| **Anomali terbesar** | Cabai Merah Keriting > Rp 152.500 di Q4 2025 |

---

## 📝 Dokumentasi

- [Project Brief](docs/project_brief.md) — Deskripsi proyek dan problem statement
- [Data Analysis](docs/data_analysis.md) — Statistik deskriptif dan perubahan harga
- [EDA Interpretation](docs/eda_interpretation.md) — Interpretasi 13 visualisasi
- [Fabric Recommendation](docs/fabric_recommendation.md) — Arsitektur Microsoft Fabric

---

## ⚙️ Format Data

- Harga dalam **Rupiah (Rp)** dengan format string berkoma (contoh: `"20,000"`)
- Kolom tanggal berformat `DD/ MM/ YYYY`
- Data hanya mencakup **hari kerja** (Senin–Jumat)

## 📄 Lisensi

Dataset ini digunakan untuk keperluan Datathon Dicoding.
