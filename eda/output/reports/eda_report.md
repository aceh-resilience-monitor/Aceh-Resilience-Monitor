# Laporan EDA - Harga Komoditas Pangan Aceh

> Generated: 2026-05-23 21:02:04

## 1. Informasi Dataset

- **Jumlah File JSON:** 6
- **File Gagal Dibaca:** 0
- **Total Baris:** 329460
- **Total Kolom:** 14
- **Nama Kolom:** no, name, level, tanggal, komoditas, harga, daerah, sumber, _source_file, harga_numeric, tahun, bulan, hari, bulan_tahun
- **Memory Usage (MB):** 160.65
- **Duplicate Rows:** 285
- **Duplicate Pct (%):** 0.09

### Tipe Data per Kolom

| Kolom | Tipe Data |
|---|---|
| no | object |
| name | object |
| level | int64 |
| tanggal | datetime64[ns] |
| komoditas | object |
| harga | object |
| daerah | object |
| sumber | object |
| _source_file | object |
| harga_numeric | float64 |
| tahun | int32 |
| bulan | int32 |
| hari | int32 |
| bulan_tahun | period[M] |

### Missing Values

| Kolom | Missing | Persentase (%) |
|---|---|---|
| no | 0 | 0.0% |
| name | 0 | 0.0% |
| level | 0 | 0.0% |
| tanggal | 0 | 0.0% |
| komoditas | 0 | 0.0% |
| harga | 0 | 0.0% |
| daerah | 0 | 0.0% |
| sumber | 0 | 0.0% |
| _source_file | 0 | 0.0% |
| harga_numeric | 0 | 0.0% |
| tahun | 0 | 0.0% |
| bulan | 0 | 0.0% |
| hari | 0 | 0.0% |
| bulan_tahun | 0 | 0.0% |

## 2. Statistik Deskriptif

| Kolom         |   Count |     Mean |   Median |   Modus |   Std Dev |   Min |    Max |   Q25 |   Q50 |   Q75 |   Skewness |   Kurtosis |
|:--------------|--------:|---------:|---------:|--------:|----------:|------:|-------:|------:|------:|------:|-----------:|-----------:|
| level         |  329460 |     1.64 |        2 |       2 |      0.48 |     1 |      2 |     1 |     2 |     2 |    -0.5963 |    -1.6444 |
| harga_numeric |  329460 | 32496.4  |    21000 |  150000 |  33451.4  |  8000 | 200000 | 14750 | 21000 | 33250 |     2.6957 |     6.4988 |
| tahun         |  329460 |  2023.25 |     2023 |    2025 |      1.58 |  2021 |   2026 |  2022 |  2023 |  2025 |     0.0552 |    -1.1699 |
| bulan         |  329460 |     6.28 |        6 |       1 |      3.48 |     1 |     12 |     3 |     6 |     9 |     0.0868 |    -1.2315 |
| hari          |  329460 |    15.67 |       16 |       8 |      8.77 |     1 |     31 |     8 |    16 |    23 |     0.0138 |    -1.1884 |

## 3. Analisis Waktu

- **Tanggal Awal:** 2021-01-01
- **Tanggal Akhir:** 2026-05-22
- **Total Hari Unik:** 1405
- **Total Missing Dates:** 563
- **Rata-rata Update/Hari:** 234.5

## 4. Analisis Harga per Komoditas

| Komoditas     |   Rata-rata |   Median |   Min |    Max |   Std Dev |   Jumlah Data |   Volatilitas (%) |
|:--------------|------------:|---------:|------:|-------:|----------:|--------------:|------------------:|
| Daging Sapi   |      143532 |   148350 | 66000 | 180000 |     12604 |         23465 |              8.78 |
| Cabai Rawit   |       41730 |    40000 |  8250 | 200000 |     16108 |         23978 |             38.6  |
| Cabai Merah   |       40689 |    36500 |  8000 | 197500 |     18675 |         23785 |             45.9  |
| Bawang Merah  |       34874 |    33750 | 12000 | 126250 |     10427 |         22164 |             29.9  |
| Bawang Putih  |       33283 |    33500 | 14500 |  60000 |      8457 |         19393 |             25.41 |
| Telur Ayam    |       27984 |    27750 | 17400 |  60200 |      4672 |         28587 |             16.7  |
| Daging Ayam   |       27001 |    27000 | 14000 |  52500 |      6016 |         21178 |             22.28 |
| Minyak Goreng |       19394 |    19500 | 10350 |  40750 |      3610 |         44958 |             18.61 |
| Gula Pasir    |       16723 |    17000 | 12150 |  58500 |      2236 |         35748 |             13.37 |
| Beras         |       12876 |    13100 |  8600 |  17850 |      2072 |         86204 |             16.09 |

### Perubahan Harga Harian

| Komoditas     |   Avg Daily Change (%) |   Max Increase (%) |   Max Decrease (%) |
|:--------------|-----------------------:|-------------------:|-------------------:|
| Cabai Merah   |                 0.0791 |              40.76 |             -26.16 |
| Bawang Merah  |                 0.0526 |              25.44 |             -23.06 |
| Daging Ayam   |                 0.0462 |              21.33 |             -16.12 |
| Bawang Putih  |                 0.0294 |              19.54 |             -14.93 |
| Cabai Rawit   |                 0.0292 |              38.64 |             -22.92 |
| Beras         |                 0.0244 |               4.05 |              -4.42 |
| Minyak Goreng |                 0.0213 |               9.07 |              -8.34 |
| Gula Pasir    |                 0.0207 |              16.21 |             -13.95 |
| Telur Ayam    |                 0.0156 |               8.39 |              -8.19 |
| Daging Sapi   |                 0.0136 |               8.79 |              -8.08 |

## 5. Analisis Wilayah

| Daerah      |   Rata-rata |   Median |   Min |    Max |   Jumlah Data |
|:------------|------------:|---------:|------:|-------:|--------------:|
| Lhokseumawe |       35713 |    22000 |  8000 | 177500 |        116411 |
| Banda Aceh  |       31547 |    21100 |  8750 | 200000 |        116087 |
| Meulaboh    |       29771 |    20050 |  8750 | 200000 |         96962 |

## 6. Visualisasi

Semua chart tersimpan di folder `output/charts/`:

- `01_missing_values_heatmap.png`
- `02_histogram_harga.png`
- `03_boxplot_komoditas.png`
- `04_avg_price_bar.png`
- `05_timeseries_monthly.png`
- `06_yearly_data_count.png`
- `07_region_heatmap.png`
- `08_volatility.png`

---

*Laporan ini di-generate secara otomatis oleh `eda.py`*