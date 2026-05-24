"""
=============================================================================
  EXPLORATORY DATA ANALYSIS (EDA) - Aceh Resilience Monitor
  Dataset: Harga Komoditas Pangan Aceh (2021-2026)
  
  Cara menjalankan:
    cd eda
    pip install -r requirements.txt
    python eda.py
=============================================================================
"""

import os
import sys
import json
import logging
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')

# ============================================================================
# KONFIGURASI
# ============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "dataup" / "data"   # ../dataup/data/
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
REPORTS_DIR = OUTPUT_DIR / "reports"
SUMMARY_DIR = OUTPUT_DIR / "summary"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "eda.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)
plt.rcParams.update({
    "figure.figsize": (12, 6),
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})


# ============================================================================
# 1. DATA LOADING & CLEANING
# ============================================================================
def create_output_dirs():
    """Buat folder output jika belum ada."""
    for d in [OUTPUT_DIR, CHARTS_DIR, REPORTS_DIR, SUMMARY_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Output directories ready.")


def parse_harga(val):
    """Konversi string harga Indonesia '15,650' -> float 15650.0"""
    if val is None or val == "" or val == "-":
        return np.nan
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return np.nan


def load_json_files(data_dir: Path):
    """Baca semua file JSON, gabung jadi satu DataFrame."""
    json_files = sorted(data_dir.glob("*.json"))
    if not json_files:
        logger.error(f"Tidak ada file JSON di {data_dir}")
        sys.exit(1)

    frames, failed = [], []
    for fp in json_files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                df = pd.json_normalize(raw)
            elif isinstance(raw, dict):
                for v in raw.values():
                    if isinstance(v, list):
                        df = pd.json_normalize(v)
                        break
                else:
                    df = pd.json_normalize([raw])
            else:
                df = pd.DataFrame([raw])
            df["_source_file"] = fp.name
            frames.append(df)
            logger.info(f"  [OK] {fp.name}: {len(df):,} baris")
        except Exception as e:
            failed.append((fp.name, str(e)))
            logger.warning(f"  [FAIL] {fp.name}: {e}")

    if failed:
        logger.warning(f"File gagal dibaca: {len(failed)}")
    if not frames:
        logger.error("Tidak ada data yang berhasil dibaca.")
        sys.exit(1)

    df_all = pd.concat(frames, ignore_index=True)
    logger.info(f"Total data gabungan: {len(df_all):,} baris, {len(df_all.columns)} kolom")
    return df_all, json_files, failed


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Bersihkan dan transformasi DataFrame."""
    df = df.copy()
    if "harga" in df.columns:
        df["harga_numeric"] = df["harga"].apply(parse_harga)
    if "tanggal" in df.columns:
        df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
        df["tahun"] = df["tanggal"].dt.year
        df["bulan"] = df["tanggal"].dt.month
        df["hari"] = df["tanggal"].dt.day
        df["bulan_tahun"] = df["tanggal"].dt.to_period("M")
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    return df


# ============================================================================
# 2. DATASET INFO
# ============================================================================
def dataset_info(df, json_files, failed):
    """Ringkasan informasi dataset."""
    dup_count = df.duplicated().sum()
    info = {
        "Jumlah File JSON": len(json_files),
        "File Gagal Dibaca": len(failed),
        "Total Baris": len(df),
        "Total Kolom": len(df.columns),
        "Nama Kolom": ", ".join(df.columns.tolist()),
        "Memory Usage (MB)": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
        "Duplicate Rows": int(dup_count),
        "Duplicate Pct (%)": round(dup_count / len(df) * 100, 2),
    }
    dtypes = df.dtypes.astype(str).to_dict()
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)

    logger.info("=" * 60)
    logger.info("INFORMASI DATASET")
    logger.info("=" * 60)
    for k, v in info.items():
        logger.info(f"  {k}: {v}")
    return info, dtypes, missing, missing_pct


# ============================================================================
# 3. STATISTIK DESKRIPTIF
# ============================================================================
def descriptive_statistics(df):
    """Hitung statistik deskriptif untuk kolom numerik."""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not num_cols:
        return pd.DataFrame()

    records = []
    for col in num_cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        mode_val = s.mode()
        records.append({
            "Kolom": col, "Count": int(s.count()),
            "Mean": round(s.mean(), 2), "Median": round(s.median(), 2),
            "Modus": round(mode_val.iloc[0], 2) if len(mode_val) > 0 else np.nan,
            "Std Dev": round(s.std(), 2),
            "Min": round(s.min(), 2), "Max": round(s.max(), 2),
            "Q25": round(s.quantile(0.25), 2),
            "Q50": round(s.quantile(0.50), 2),
            "Q75": round(s.quantile(0.75), 2),
            "Skewness": round(s.skew(), 4),
            "Kurtosis": round(s.kurtosis(), 4),
        })
    return pd.DataFrame(records)


# ============================================================================
# 4. ANALISIS WAKTU
# ============================================================================
def time_analysis(df):
    """Analisis temporal."""
    if "tanggal" not in df.columns or df["tanggal"].isnull().all():
        return {}

    tanggal = df["tanggal"].dropna()
    date_range = pd.date_range(tanggal.min(), tanggal.max(), freq="D")
    existing_dates = tanggal.dt.date.unique()
    missing_dates = set(date_range.date) - set(existing_dates)
    daily_count = df.groupby(df["tanggal"].dt.date).size()

    result = {
        "Tanggal Awal": str(tanggal.min().date()),
        "Tanggal Akhir": str(tanggal.max().date()),
        "Total Hari Unik": len(existing_dates),
        "Total Missing Dates": len(missing_dates),
        "Rata-rata Update/Hari": round(daily_count.mean(), 1),
        "daily_count": daily_count,
    }
    logger.info(f"Analisis waktu: {result['Tanggal Awal']} s/d {result['Tanggal Akhir']}, "
                f"missing dates: {len(missing_dates)}")
    return result


# ============================================================================
# 5. ANALISIS HARGA
# ============================================================================
def price_analysis(df):
    """Analisis harga komoditas."""
    if "harga_numeric" not in df.columns or "komoditas" not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    valid = df.dropna(subset=["harga_numeric"])
    komod_stats = valid.groupby("komoditas")["harga_numeric"].agg(
        ["mean", "median", "min", "max", "std", "count"]
    ).round(0).reset_index()
    komod_stats.columns = ["Komoditas", "Rata-rata", "Median", "Min", "Max", "Std Dev", "Jumlah Data"]
    komod_stats["Volatilitas (%)"] = (
        (komod_stats["Std Dev"] / komod_stats["Rata-rata"]) * 100
    ).round(2)
    komod_stats = komod_stats.sort_values("Rata-rata", ascending=False)

    # Perubahan harga harian
    change_records = []
    if "tanggal" in df.columns:
        for kom in valid["komoditas"].unique():
            sub = valid[valid["komoditas"] == kom]
            daily_avg = sub.groupby(sub["tanggal"].dt.date)["harga_numeric"].mean().sort_index()
            if len(daily_avg) < 2:
                continue
            pct = daily_avg.pct_change().dropna()
            change_records.append({
                "Komoditas": kom,
                "Avg Daily Change (%)": round(pct.mean() * 100, 4),
                "Max Increase (%)": round(pct.max() * 100, 2),
                "Max Decrease (%)": round(pct.min() * 100, 2),
            })
    change_df = pd.DataFrame(change_records)
    if not change_df.empty:
        change_df = change_df.sort_values("Avg Daily Change (%)", ascending=False)
    return komod_stats, change_df


# ============================================================================
# 6. ANALISIS WILAYAH
# ============================================================================
def region_analysis(df):
    """Analisis harga per wilayah."""
    if "daerah" not in df.columns or "harga_numeric" not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    valid = df.dropna(subset=["harga_numeric"])
    region_stats = valid.groupby("daerah")["harga_numeric"].agg(
        ["mean", "median", "min", "max", "count"]
    ).round(0).reset_index()
    region_stats.columns = ["Daerah", "Rata-rata", "Median", "Min", "Max", "Jumlah Data"]
    region_stats = region_stats.sort_values("Rata-rata", ascending=False)

    cross = pd.DataFrame()
    if "komoditas" in df.columns:
        cross = valid.pivot_table(
            values="harga_numeric", index="komoditas", columns="daerah", aggfunc="mean"
        ).round(0)
    return region_stats, cross


# ============================================================================
# 7. VISUALISASI
# ============================================================================
def plot_missing_values(df):
    fig, ax = plt.subplots(figsize=(12, 5))
    sample = df.isnull().astype(int).sample(min(500, len(df)), random_state=42)
    sns.heatmap(sample.T, cbar=True, yticklabels=True, cmap="YlOrRd", ax=ax)
    ax.set_title("Missing Value Heatmap (Sample)")
    fig.savefig(CHARTS_DIR / "01_missing_values_heatmap.png")
    plt.close(fig)
    logger.info("  [OK] Missing value heatmap")


def plot_histograms(df):
    if "harga_numeric" not in df.columns:
        return
    fig, ax = plt.subplots(figsize=(12, 6))
    data = df["harga_numeric"].dropna()
    ax.hist(data, bins=50, color="#4C72B0", edgecolor="white", alpha=0.85)
    ax.set_title("Distribusi Harga Seluruh Komoditas")
    ax.set_xlabel("Harga (Rp)")
    ax.set_ylabel("Frekuensi")
    ax.axvline(data.mean(), color="red", linestyle="--", label=f"Mean: {data.mean():,.0f}")
    ax.axvline(data.median(), color="green", linestyle="--", label=f"Median: {data.median():,.0f}")
    ax.legend()
    fig.savefig(CHARTS_DIR / "02_histogram_harga.png")
    plt.close(fig)
    logger.info("  [OK] Histogram harga")


def plot_boxplot_komoditas(df):
    if "harga_numeric" not in df.columns or "komoditas" not in df.columns:
        return
    valid = df.dropna(subset=["harga_numeric"])
    fig, ax = plt.subplots(figsize=(14, 7))
    order = valid.groupby("komoditas")["harga_numeric"].median().sort_values(ascending=False).index
    sns.boxplot(data=valid, x="komoditas", y="harga_numeric", order=order, ax=ax, palette="Set2")
    ax.set_title("Boxplot Harga per Komoditas")
    ax.set_xlabel("Komoditas")
    ax.set_ylabel("Harga (Rp)")
    ax.tick_params(axis="x", rotation=35)
    fig.savefig(CHARTS_DIR / "03_boxplot_komoditas.png")
    plt.close(fig)
    logger.info("  [OK] Boxplot komoditas")


def plot_avg_price_bar(komod_stats):
    if komod_stats.empty:
        return
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = sns.color_palette("viridis", len(komod_stats))
    bars = ax.barh(komod_stats["Komoditas"], komod_stats["Rata-rata"], color=colors)
    ax.set_title("Rata-rata Harga per Komoditas (2021-2026)")
    ax.set_xlabel("Harga (Rp)")
    for bar, val in zip(bars, komod_stats["Rata-rata"]):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                f"Rp {val:,.0f}", va="center", fontsize=9)
    fig.savefig(CHARTS_DIR / "04_avg_price_bar.png")
    plt.close(fig)
    logger.info("  [OK] Bar chart rata-rata harga")


def plot_time_series(df):
    if "tanggal" not in df.columns or "harga_numeric" not in df.columns or "komoditas" not in df.columns:
        return
    valid = df.dropna(subset=["harga_numeric", "tanggal"])
    monthly = valid.groupby([valid["tanggal"].dt.to_period("M"), "komoditas"])["harga_numeric"].mean().reset_index()
    monthly["tanggal"] = monthly["tanggal"].dt.to_timestamp()

    fig, ax = plt.subplots(figsize=(16, 8))
    for kom in monthly["komoditas"].unique():
        sub = monthly[monthly["komoditas"] == kom]
        ax.plot(sub["tanggal"], sub["harga_numeric"], label=kom, linewidth=1.5)
    ax.set_title("Tren Harga Bulanan per Komoditas")
    ax.set_xlabel("Waktu")
    ax.set_ylabel("Harga Rata-rata (Rp)")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    fig.savefig(CHARTS_DIR / "05_timeseries_monthly.png")
    plt.close(fig)
    logger.info("  [OK] Time series bulanan")


def plot_yearly_trend(df):
    if "tahun" not in df.columns:
        return
    yearly = df.groupby("tahun").size().reset_index(name="jumlah")
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(yearly["tahun"].astype(str), yearly["jumlah"], color="#4C72B0", edgecolor="white")
    ax.set_title("Jumlah Data per Tahun")
    ax.set_xlabel("Tahun")
    ax.set_ylabel("Jumlah Baris")
    for bar, val in zip(bars, yearly["jumlah"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 200,
                f"{val:,}", ha="center", fontsize=10)
    fig.savefig(CHARTS_DIR / "06_yearly_data_count.png")
    plt.close(fig)
    logger.info("  [OK] Bar chart tahunan")


def plot_region_heatmap(cross_df):
    if cross_df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cross_df, annot=True, fmt=",.0f", cmap="YlGnBu", linewidths=0.5, ax=ax)
    ax.set_title("Rata-rata Harga: Komoditas vs Daerah")
    fig.savefig(CHARTS_DIR / "07_region_heatmap.png")
    plt.close(fig)
    logger.info("  [OK] Region heatmap")


def plot_volatility(komod_stats):
    if komod_stats.empty or "Volatilitas (%)" not in komod_stats.columns:
        return
    sorted_df = komod_stats.sort_values("Volatilitas (%)", ascending=True)
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#e74c3c" if v > 50 else "#3498db" for v in sorted_df["Volatilitas (%)"]]
    ax.barh(sorted_df["Komoditas"], sorted_df["Volatilitas (%)"], color=colors)
    ax.set_title("Volatilitas Harga per Komoditas (Coefficient of Variation %)")
    ax.set_xlabel("Volatilitas (%)")
    fig.savefig(CHARTS_DIR / "08_volatility.png")
    plt.close(fig)
    logger.info("  [OK] Volatility chart")


# ============================================================================
# 8. REPORT GENERATION
# ============================================================================
def save_outputs(df, info, dtypes, missing, missing_pct, stats_df,
                 komod_stats, change_df, region_stats, time_result):
    """Simpan hasil ke CSV, Excel, JSON, dan Markdown."""
    if not stats_df.empty:
        stats_df.to_csv(SUMMARY_DIR / "statistics.csv", index=False)
        stats_df.to_excel(SUMMARY_DIR / "statistics.xlsx", index=False)
        stats_df.to_json(SUMMARY_DIR / "statistics.json", orient="records", indent=2)
        logger.info("  [OK] statistics.csv / .xlsx / .json")
    if not komod_stats.empty:
        komod_stats.to_csv(SUMMARY_DIR / "komoditas_stats.csv", index=False)
    if not region_stats.empty:
        region_stats.to_csv(SUMMARY_DIR / "region_stats.csv", index=False)

    generate_markdown_report(info, dtypes, missing, missing_pct, stats_df,
                             komod_stats, change_df, region_stats, time_result)


def generate_markdown_report(info, dtypes, missing, missing_pct, stats_df,
                             komod_stats, change_df, region_stats, time_result):
    """Generate laporan EDA lengkap dalam Markdown."""
    lines = []
    lines.append("# Laporan EDA - Harga Komoditas Pangan Aceh")
    lines.append(f"\n> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Section 1
    lines.append("## 1. Informasi Dataset\n")
    for k, v in info.items():
        lines.append(f"- **{k}:** {v}")

    lines.append("\n### Tipe Data per Kolom\n")
    lines.append("| Kolom | Tipe Data |")
    lines.append("|---|---|")
    for col, dtype in dtypes.items():
        lines.append(f"| {col} | {dtype} |")

    lines.append("\n### Missing Values\n")
    lines.append("| Kolom | Missing | Persentase (%) |")
    lines.append("|---|---|---|")
    for col in missing.index:
        lines.append(f"| {col} | {missing[col]} | {missing_pct[col]}% |")

    # Section 2
    if not stats_df.empty:
        lines.append("\n## 2. Statistik Deskriptif\n")
        lines.append(stats_df.to_markdown(index=False))

    # Section 3
    if time_result:
        lines.append("\n## 3. Analisis Waktu\n")
        for k in ["Tanggal Awal", "Tanggal Akhir", "Total Hari Unik",
                   "Total Missing Dates", "Rata-rata Update/Hari"]:
            if k in time_result:
                lines.append(f"- **{k}:** {time_result[k]}")

    # Section 4
    if not komod_stats.empty:
        lines.append("\n## 4. Analisis Harga per Komoditas\n")
        lines.append(komod_stats.to_markdown(index=False))
    if not change_df.empty:
        lines.append("\n### Perubahan Harga Harian\n")
        lines.append(change_df.to_markdown(index=False))

    # Section 5
    if not region_stats.empty:
        lines.append("\n## 5. Analisis Wilayah\n")
        lines.append(region_stats.to_markdown(index=False))

    # Section 6
    lines.append("\n## 6. Visualisasi\n")
    lines.append("Semua chart tersimpan di folder `output/charts/`:\n")
    for chart in sorted(CHARTS_DIR.glob("*.png")):
        lines.append(f"- `{chart.name}`")

    lines.append("\n---")
    lines.append(f"\n*Laporan ini di-generate secara otomatis oleh `eda.py`*")

    report_path = REPORTS_DIR / "eda_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"  [OK] {report_path}")


# ============================================================================
# MAIN
# ============================================================================
def main():
    start = datetime.now()
    logger.info("=" * 60)
    logger.info("  MEMULAI EXPLORATORY DATA ANALYSIS (EDA)")
    logger.info("=" * 60)

    create_output_dirs()

    logger.info("\n[1/8] Membaca file JSON...")
    df_raw, json_files, failed = load_json_files(DATA_DIR)

    logger.info("\n[2/8] Membersihkan data...")
    df = clean_dataframe(df_raw)

    logger.info("\n[3/8] Menganalisis informasi dataset...")
    info, dtypes, missing, missing_pct = dataset_info(df, json_files, failed)

    logger.info("\n[4/8] Menghitung statistik deskriptif...")
    stats_df = descriptive_statistics(df)

    logger.info("\n[5/8] Menganalisis dimensi waktu...")
    time_result = time_analysis(df)

    logger.info("\n[6/8] Menganalisis harga komoditas...")
    komod_stats, change_df = price_analysis(df)

    logger.info("\n[7/8] Menganalisis wilayah...")
    region_stats, cross_df = region_analysis(df)

    logger.info("\n[8/8] Membuat visualisasi...")
    try:
        plot_missing_values(df)
        plot_histograms(df)
        plot_boxplot_komoditas(df)
        plot_avg_price_bar(komod_stats)
        plot_time_series(df)
        plot_yearly_trend(df)
        plot_region_heatmap(cross_df)
        plot_volatility(komod_stats)
    except Exception as e:
        logger.error(f"Error saat membuat visualisasi: {e}")

    logger.info("\nMenyimpan output...")
    save_outputs(df, info, dtypes, missing, missing_pct, stats_df,
                 komod_stats, change_df, region_stats, time_result)

    elapsed = (datetime.now() - start).total_seconds()
    logger.info(f"\n{'=' * 60}")
    logger.info(f"  EDA SELESAI dalam {elapsed:.1f} detik")
    logger.info(f"  Output: {OUTPUT_DIR}")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
