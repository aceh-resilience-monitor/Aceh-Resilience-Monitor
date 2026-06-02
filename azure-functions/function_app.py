"""
ARM Azure Functions — Daily Serverless Pipeline
=================================================
Timer-triggered Azure Function that runs every day at 08:00 WIB (01:00 UTC).
Executes the full ARM pipeline: Scrape → ETL → Anomaly Detection →
Prophet Forecasting → Telegram Alerts → Dashboard Update → MLflow Logging.

Architecture: Hybrid Approach (Opsi A)
- Training: On-the-fly di RAM (tidak download model dari Registry)
- MLflow: Production tracking (log metrik harian ke Azure ML Studio)
- Data: Opsi A — file per-tahun di Blob Storage (2021.json ... 2026.json)

Author: Aulia (ML & Azure) — G13 Azure Functions Pipeline

Usage:
    # Local development
    func start

    # Deploy to Azure
    func azure functionapp publish arm-daily-pipeline
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, List, Optional, Tuple

import azure.functions as func
import numpy as np
import pandas as pd

# ── Setup path for importing ARM modules ──
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from scripts.config import (
    ALL_REGIONS,
    CATEGORY_MAP,
    FORECAST_DAYS,
    SHORT_NAMES,
    setup_logging,
)
from scripts.etl import add_holiday_features
from scripts.anomaly import detect_anomalies, detect_future_spikes
from scripts.forecast import forecast_all_commodities
from scripts.telegram_alert import send_daily_alert
from scripts.scraper import scrape_daily_pihps

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# AZURE FUNCTIONS APP — V2 Programming Model
# Author: Aulia (ML & Azure) — G13
# ══════════════════════════════════════════════════════════════════════

app = func.FunctionApp()


# ══════════════════════════════════════════════════════════════════════
# BLOB STORAGE HELPERS
# Author: Aulia (ML & Azure)
# ══════════════════════════════════════════════════════════════════════

def _get_blob_service():
    """Get Azure Blob Storage service client."""
    from azure.storage.blob import BlobServiceClient

    conn_str = os.environ.get('AZURE_STORAGE_CONNECTION_STRING', '')
    if not conn_str:
        raise ValueError(
            "AZURE_STORAGE_CONNECTION_STRING not set. "
            "Configure in Azure Portal → Function App → Configuration."
        )
    return BlobServiceClient.from_connection_string(conn_str)


def _download_blob_json(container: str, blob_name: str) -> list:
    """Download a JSON file from Blob Storage and parse it."""
    try:
        blob_service = _get_blob_service()
        blob_client = blob_service.get_blob_client(container, blob_name)
        data = blob_client.download_blob().readall()
        return json.loads(data.decode('utf-8'))
    except Exception as e:
        logger.warning("Could not download %s/%s: %s", container, blob_name, e)
        return []


def _upload_blob_json(container: str, blob_name: str, data, content_type='application/json'):
    """Upload JSON data to Blob Storage."""
    from azure.storage.blob import ContentSettings

    blob_service = _get_blob_service()
    blob_client = blob_service.get_blob_client(container, blob_name)

    if isinstance(data, (dict, list)):
        content = json.dumps(data, ensure_ascii=False, default=str)
    else:
        content = data

    blob_client.upload_blob(
        content.encode('utf-8'),
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type)
    )
    logger.info("Uploaded %s/%s (%d bytes)", container, blob_name, len(content))


def update_blob_with_new_data(container: str, blob_name: str) -> int:
    """
    Download f"{year}.json" from Blob Storage, run scrape_daily_pihps,
    append any new records, and upload it back.
    Returns the number of new records added.
    """
    logger.info("Downloading existing records from Blob: %s/%s", container, blob_name)
    existing_records = _download_blob_json(container, blob_name)
    
    # Run the daily PIHPS scraper
    new_records = scrape_daily_pihps(existing_records)
    
    if new_records:
        updated_records = existing_records + new_records
        # Sort by date (tanggal) chronologically
        updated_records.sort(key=lambda x: x.get('tanggal', ''))
        
        logger.info("Uploading updated records to Blob: %s/%s", container, blob_name)
        _upload_blob_json(container, blob_name, updated_records)
        return len(new_records)
        
    logger.info("No new records to append to blob.")
    return 0


# ══════════════════════════════════════════════════════════════════════
# DATA LOADING FROM BLOB STORAGE (Opsi A: file per-tahun)
# Author: Aulia (ML & Azure)
# ══════════════════════════════════════════════════════════════════════

def load_all_data_from_blob() -> pd.DataFrame:
    """
    Load all historical data from Azure Blob Storage.

    Uses Opsi A structure: separate JSON files per year (2021.json ... 2026.json)
    in the 'arm-raw-data' container. Merges all years into a single DataFrame
    in RAM, exactly like the local load_all_data() function.

    Author: Aulia (ML & Azure)
    """
    container = os.environ.get('ARM_BLOB_CONTAINER', 'arm-raw-data')
    years = range(2021, datetime.now().year + 1)
    all_records = []

    for year in years:
        blob_name = f"{year}.json"
        records = _download_blob_json(container, blob_name)
        if records:
            # Filter level 2 only (sub-commodities, not parent categories)
            level2 = [r for r in records if r.get('level') == 2]
            all_records.extend(level2)
            logger.info("Loaded %d level-2 records from %s", len(level2), blob_name)

    if not all_records:
        logger.error("No records loaded from Blob Storage!")
        return pd.DataFrame()

    df = pd.DataFrame(all_records).copy()

    # Clean & Transform (same logic as etl.py load_from_dataup_json)
    df['name'] = df['name'].str.strip()
    known_commodities = set(CATEGORY_MAP.keys())
    df = df[df['name'].isin(known_commodities)].copy()

    df['price'] = pd.to_numeric(
        df['harga'].astype(str).str.replace(',', '', regex=False),
        errors='coerce'
    )
    df['date'] = pd.to_datetime(df['tanggal'])
    df['commodity'] = df['name']
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['category'] = df['commodity'].map(CATEGORY_MAP)

    columns = ['date', 'commodity', 'price', 'year', 'month', 'category', 'daerah', 'sumber']
    df = df[[c for c in columns if c in df.columns]].dropna(subset=['price']).copy()
    df = df.sort_values(['date', 'commodity']).reset_index(drop=True)

    logger.info("Total records from Blob: %d | commodities: %d",
                len(df), df['commodity'].nunique())
    return df


# ══════════════════════════════════════════════════════════════════════
# DASHBOARD DATA COMPRESSION
# Author: Ilhaam (Code & Frontend)
# ══════════════════════════════════════════════════════════════════════

def compress_dashboard_data(
    df: pd.DataFrame,
    anomalies: List[dict],
    forecasts: Dict,
    spikes: List[dict],
) -> dict:
    """
    Compress full pipeline output into a lightweight dashboard_data.json.

    Reduction tactics:
    1. Weekly resampling for historical trends (85% size reduction)
    2. 90-day window for recent daily data
    3. Limit anomalies to 200 most recent
    4. Only forecast coordinates (yhat, yhat_lower, yhat_upper)

    Author: Ilhaam (Code & Frontend)
    """
    latest_date = df['date'].max()
    commodities = sorted(df['commodity'].unique().tolist())

    # Aggregate to provincial level for dashboard
    df_prov = df.groupby(['date', 'commodity'], as_index=False)['price'].mean()
    df_prov['price'] = df_prov['price'].round(0)

    dashboard = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'total_commodities': len(commodities),
            'latest_date': latest_date.strftime('%Y-%m-%d'),
            'data_source': 'Azure Functions Daily Pipeline',
        },
        'commodities': commodities,
        'timeseries': {},
        'timeseriesRecentDaily': {},
        'forecasts': forecasts,
        'anomalies': anomalies[:200],
        'spikes': spikes,
    }

    for commodity in commodities:
        cdf = df_prov[df_prov['commodity'] == commodity].sort_values('date')

        # Weekly resampled historical data
        if not cdf.empty:
            weekly = cdf.set_index('date')['price'].resample('W').mean().dropna()
            dashboard['timeseries'][commodity] = {
                'dates': weekly.index.strftime('%Y-%m-%d').tolist(),
                'prices': weekly.round(0).tolist(),
            }

            # Recent 90 days daily data
            recent_start = latest_date - pd.Timedelta(days=90)
            recent = cdf[cdf['date'] >= recent_start]
            dashboard['timeseriesRecentDaily'][commodity] = {
                'dates': recent['date'].dt.strftime('%Y-%m-%d').tolist(),
                'prices': recent['price'].round(0).tolist(),
            }

    return dashboard


# ══════════════════════════════════════════════════════════════════════
# MLFLOW PRODUCTION TRACKING
# Author: Aulia (ML & Azure) — G12 Production Metrics
# ══════════════════════════════════════════════════════════════════════

def log_daily_metrics_to_mlflow(anomalies: List[dict], spikes: List[dict]):
    """
    Log daily production metrics to Azure ML via MLflow.

    This creates a continuous monitoring graph in Azure ML Studio
    that tracks model performance and alert counts over time.

    Author: Aulia (ML & Azure) — Hybrid Architecture Production Tracking
    """
    try:
        import mlflow

        config_path = os.path.join(root_dir, "config.json")
        if os.path.exists(config_path):
            from azureml.core import Workspace
            ws = Workspace.from_config(path=config_path)
            mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
        else:
            mlflow.set_tracking_uri("sqlite:///mlflow.db")

        mlflow.set_experiment("arm-daily-production")

        with mlflow.start_run(run_name=f"daily-{datetime.now().strftime('%Y%m%d')}"):
            mlflow.log_metric("total_anomalies", len(anomalies))
            mlflow.log_metric("critical_anomalies",
                              sum(1 for a in anomalies if a.get('severity') == 'critical'))
            mlflow.log_metric("total_spikes", len(spikes))
            mlflow.log_metric("max_spike_pct",
                              max((s['spike_pct'] for s in spikes), default=0))
            mlflow.log_param("date", datetime.now().strftime('%Y-%m-%d'))
            mlflow.log_param("pipeline", "azure-functions-daily")

        logger.info("Daily metrics logged to MLflow successfully")

    except Exception as e:
        logger.warning("Could not log to MLflow (non-fatal): %s", e)


# ══════════════════════════════════════════════════════════════════════
# MAIN PIPELINE — TIMER TRIGGER
# Author: Aulia (ML & Azure) — G13 Azure Functions
# ══════════════════════════════════════════════════════════════════════

@app.timer_trigger(
    schedule="0 0 1 * * *",  # 01:00 UTC = 08:00 WIB
    arg_name="timer",
    run_on_startup=False,
)
def arm_daily_pipeline(timer: func.TimerRequest) -> None:
    """
    ARM Daily Pipeline — runs every morning at 08:00 WIB.

    Pipeline steps:
    0. Scrape today's data from PIHPS and update Blob Storage (Opsi A) (BARU)
    1. Load all historical data from Blob Storage (Opsi A: per-year files)
    2. Run Z-Score anomaly detection (reactive alerts)
    3. Run Prophet forecasting with Meugang regressors (84 models)
    4. Detect future price spikes (proactive EWS alerts)
    5. Send Telegram alerts to TPID Aceh group
    6. Compress and upload dashboard_data.json to public Blob
    7. Log daily metrics to Azure ML via MLflow

    Author: Aulia (ML & Azure) — G13 Azure Functions Pipeline
    """
    setup_logging()
    start_time = datetime.now()
    logger.info("═" * 60)
    logger.info("ARM Daily Pipeline started at %s", start_time.isoformat())
    logger.info("═" * 60)

    try:
        # ── Step 0: Scrape hari ini (BARU) ──
        logger.info("Step 0/7: Scraping today's data from PIHPS...")
        raw_container = os.environ.get('ARM_BLOB_CONTAINER', 'arm-raw-data')
        current_year = datetime.now().year
        blob_name = f"{current_year}.json"
        try:
            new_records_count = update_blob_with_new_data(raw_container, blob_name)
            logger.info("Step 0 Complete: Added %d new records to Blob.", new_records_count)
        except Exception as e:
            logger.error("Step 0 Failed (Scraper error, continuing to Step 1): %s", e)

        # ── Step 1: Load Data from Blob Storage ──
        logger.info("Step 1/7: Loading data from Blob Storage...")
        df = load_all_data_from_blob()
        if df.empty:
            logger.error("No data loaded! Aborting pipeline.")
            return

        latest_date = df['date'].max()
        commodities = sorted(df['commodity'].unique().tolist())
        logger.info("Data loaded: %d records, %d commodities, latest: %s",
                     len(df), len(commodities), latest_date.strftime('%Y-%m-%d'))

        # ── Step 2: Z-Score Anomaly Detection ──
        logger.info("Step 2/7: Running anomaly detection...")
        # Aggregate to regional level (kabupaten/kota) for Z-Score, and provincial level for latest prices
        from scripts.etl import aggregate_prices
        df_prov = aggregate_prices(df, by='province')
        df_region = aggregate_prices(df, by='region')
        anomalies = detect_anomalies(df_region, commodities, group_by='daerah')
        logger.info("Anomalies detected: %d", len(anomalies))

        # ── Step 3: Prophet Forecasting with Meugang Regressors ──
        logger.info("Step 3/7: Training 84 Prophet models (21 commodities × 4)...")
        forecasts = forecast_all_commodities(
            df, commodities, latest_date,
            periods=FORECAST_DAYS, per_region=True
        )
        logger.info("Forecasting complete: %d commodities", len(forecasts))

        # ── Step 4: Detect Future Price Spikes ──
        logger.info("Step 4/7: Detecting future price spikes...")
        latest_prices = {}
        for commodity in commodities:
            cdf = df_prov[df_prov['commodity'] == commodity].sort_values('date')
            if not cdf.empty:
                latest_prices[commodity] = float(cdf['price'].iloc[-1])
        spikes = detect_future_spikes(forecasts, latest_prices)
        logger.info("Spikes predicted: %d", len(spikes))

        # ── Step 5: Send Telegram Alerts ──
        logger.info("Step 5/7: Sending Telegram alerts...")
        # Filter anomalies to today only for Telegram
        today_str = latest_date.strftime('%Y-%m-%d')
        today_anomalies = [a for a in anomalies if a['date'] == today_str]
        send_daily_alert(
            anomalies=today_anomalies,
            spikes=spikes,
            date_str=latest_date.strftime('%d %B %Y'),
        )

        # ── Step 6: Compress & Upload Dashboard Data ──
        logger.info("Step 6/7: Compressing dashboard data...")
        dashboard_data = compress_dashboard_data(df, anomalies, forecasts, spikes)
        public_container = os.environ.get('ARM_PUBLIC_CONTAINER', '$web')
        _upload_blob_json(public_container, 'dashboard_data.json', dashboard_data)
        logger.info("Dashboard data uploaded to %s/dashboard_data.json", public_container)

        # ── Step 7: Log Metrics to MLflow ──
        logger.info("Step 7/7: Logging daily metrics to MLflow...")
        log_daily_metrics_to_mlflow(anomalies, spikes)

        # ── Pipeline Complete ──
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("═" * 60)
        logger.info("✅ ARM Daily Pipeline completed in %.1f seconds", elapsed)
        logger.info("   Anomalies: %d | Spikes: %d | Models: %d",
                     len(anomalies), len(spikes), len(commodities) * 4)
        logger.info("═" * 60)

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error("❌ Pipeline failed after %.1f seconds: %s", elapsed, str(e))
        raise
