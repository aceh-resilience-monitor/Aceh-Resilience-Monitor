# 📊 EDA - Harga Komoditas Pangan Aceh

Exploratory Data Analysis otomatis untuk dataset harga komoditas pangan di Provinsi Aceh (2021-2026).

## 📁 Struktur Folder

```
eda/
├── eda.py              # Script utama EDA
├── requirements.txt    # Dependencies Python
├── README.md           # Dokumentasi ini
├── eda.log             # Log file (auto-generated)
└── output/             # Hasil output (auto-generated)
    ├── charts/         # Visualisasi (PNG)
    ├── reports/        # Laporan Markdown
    └── summary/        # CSV, Excel, JSON
```

Data sumber: `../dataup/data/*.json`

## 🚀 Cara Install & Menjalankan

```bash
cd eda
pip install -r requirements.txt
python eda.py
```

## 📈 Hasil Output

### Charts (`output/charts/`)
| File | Deskripsi |
|---|---|
| `01_missing_values_heatmap.png` | Heatmap missing values |
| `02_histogram_harga.png` | Distribusi harga seluruh komoditas |
| `03_boxplot_komoditas.png` | Boxplot harga per komoditas |
| `04_avg_price_bar.png` | Bar chart rata-rata harga |
| `05_timeseries_monthly.png` | Tren harga bulanan |
| `06_yearly_data_count.png` | Jumlah data per tahun |
| `07_region_heatmap.png` | Heatmap harga per wilayah |
| `08_volatility.png` | Volatilitas harga komoditas |

### Reports (`output/reports/`)
- `eda_report.md` — Laporan EDA lengkap dalam Markdown

### Summary (`output/summary/`)
- `statistics.csv` / `.xlsx` / `.json` — Statistik deskriptif
- `komoditas_stats.csv` — Statistik per komoditas
- `region_stats.csv` — Statistik per wilayah

## 🔧 Dependencies

- pandas, numpy, matplotlib, seaborn, openpyxl, scipy
