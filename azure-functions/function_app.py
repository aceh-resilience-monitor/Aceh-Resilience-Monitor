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
    ALL_SOURCES,
    CATEGORY_MAP,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    CV_HIGH,
    CHANGE_HIGH,
    FORECAST_DAYS,
    SHORT_NAMES,
    setup_logging,
)
from scripts.etl import add_holiday_features, aggregate_prices
from scripts.anomaly import detect_anomalies, detect_future_spikes
from scripts.forecast import forecast_all_commodities
from scripts.telegram_alert import send_daily_alert
from scripts.scraper import scrape_daily_pihps
from scripts.prepare_dashboard_data import (
    build_timeseries,
    build_timeseries_daily_recent,
    build_commodity_cards,
    build_yoy_data,
    build_seasonality,
    build_volatility,
    build_correlation,
    build_category_monthly,
    build_regional_data,
    build_price_by_source,
    build_alert_feed,
    generate_executive_summary,
)

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
    Compress full pipeline output into dashboard_data.json.

    Now delegates to builder functions from prepare_dashboard_data.py
    to ensure Azure pipeline output is IDENTICAL to local pipeline output.

    Author: Aulia (ML & Azure)
    """
    latest_date = df['date'].max()
    commodities = sorted(df['commodity'].unique().tolist())

    # ── Filter for consumer-facing markets (same as local pipeline) ──
    df_consumer = df[df['sumber'].isin(['Pasar Tradisional', 'Pasar Modern'])]
    df_prov = aggregate_prices(df_consumer, by='province')

    # ── Enrich anomalies with shortName and category ──
    for a in anomalies:
        comm = a['commodity']
        a['shortName'] = SHORT_NAMES.get(comm, comm)
        a['category'] = CATEGORY_MAP.get(comm, 'Lainnya')

    # ── 1. Timeseries ──
    timeseries = build_timeseries(df_prov, commodities)
    ts_daily_recent = build_timeseries_daily_recent(df_prov, commodities, latest_date)

    # ── 2. Commodity cards ──
    commodity_cards, latest_prices = build_commodity_cards(
        df_prov, commodities, anomalies, latest_date
    )

    # ── 3. Analytical sections ──
    yoy_data = build_yoy_data(df_prov, commodities)
    seasonality = build_seasonality(df_prov, commodities)
    volatility = build_volatility(df_prov, commodities)
    correlation = build_correlation(df_prov, commodities)
    category_monthly = build_category_monthly(df_prov)

    # ── 4. Regional data (Tier 2 dashboard) ──
    regional = build_regional_data(df_consumer, commodities)
    price_by_source = build_price_by_source(df, commodities)

    # ── 5. Regional forecasts ──
    regional_forecasts = {}
    for commodity in commodities:
        if commodity in forecasts:
            regional_forecasts[commodity] = {
                k: v for k, v in forecasts[commodity].items()
                if k != 'aggregated'
            }

    # ── 6. KPI summary ──
    recent_start = (latest_date - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
    n_critical = len([c for c in commodity_cards if c['status'] == 'critical'])
    n_warning = len([c for c in commodity_cards if c['status'] == 'warning'])

    kpi = {
        'totalCommodities': len(commodities),
        'criticalAlerts': n_critical,
        'warningAlerts': n_warning,
        'avgPriceChange': round(
            float(pd.Series([c['totalChange'] for c in commodity_cards]).mean()), 1
        ),
        'dataStartDate': df_prov['date'].min().strftime('%Y-%m-%d'),
        'dataEndDate': latest_date.strftime('%Y-%m-%d'),
        'totalDataPoints': len(df),
        'recentAnomalies': len([a for a in anomalies if a['date'] >= recent_start]),
        'totalRegions': len(ALL_REGIONS),
        'totalSources': len(ALL_SOURCES),
    }

    # ── 7. Alert feed + Executive summary ──
    alert_feed = build_alert_feed(anomalies, spikes)
    ai_insight = generate_executive_summary(anomalies, spikes, kpi)

    # ── 8. Extract aggregated forecasts ──
    forecasts_aggregated = {}
    for commodity in commodities:
        if commodity in forecasts and 'aggregated' in forecasts[commodity]:
            forecasts_aggregated[commodity] = forecasts[commodity]['aggregated']

    # ── 9. Assemble final JSON ──
    return {
        'kpi': kpi,
        'commodityCards': commodity_cards,
        'timeseries': timeseries,
        'timeseriesRecentDaily': ts_daily_recent,
        'anomalies': anomalies[:200],
        'alertFeed': alert_feed,
        'yoyData': yoy_data,
        'seasonality': seasonality,
        'volatility': volatility,
        'correlation': correlation,
        'categoryMonthly': category_monthly,
        'forecasts': forecasts_aggregated,
        'categories': list(sorted(set(CATEGORY_MAP.values()))),
        'categoryIcons': CATEGORY_ICONS,
        'categoryColors': CATEGORY_COLORS,
        'aiInsight': ai_insight,
        'regional': regional,
        'priceBySource': price_by_source,
        'regionalForecasts': regional_forecasts,
        'regions': ALL_REGIONS,
        'priceSources': ALL_SOURCES,
    }


# ══════════════════════════════════════════════════════════════════════
# MLFLOW PRODUCTION TRACKING
# Author: Aulia (ML & Azure) — G12 Production Metrics
# ══════════════════════════════════════════════════════════════════════

def setup_mlflow_tracking() -> bool:
    """Setup MLflow tracking URI using config.json or Managed Identity."""
    try:
        import mlflow
        config_path = os.path.join(root_dir, "config.json")
        if os.path.exists(config_path):
            from azureml.core import Workspace
            ws = Workspace.from_config(path=config_path)
            mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
            logger.info("Connected to Azure ML Workspace via config.json.")
            return True
        elif os.environ.get('ARM_SUBSCRIPTION_ID') and os.environ.get('ARM_RESOURCE_GROUP') and os.environ.get('ARM_WORKSPACE_NAME'):
            from azureml.core import Workspace
            from azureml.core.authentication import MsiAuthentication
            try:
                auth = MsiAuthentication()
                ws = Workspace(
                    subscription_id=os.environ['ARM_SUBSCRIPTION_ID'],
                    resource_group=os.environ['ARM_RESOURCE_GROUP'],
                    workspace_name=os.environ['ARM_WORKSPACE_NAME'],
                    auth=auth
                )
                mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
                logger.info("Connected to Azure ML Workspace via Managed Identity.")
                return True
            except Exception as msi_err:
                logger.warning("Failed to connect via Managed Identity: %s", msi_err)
                mlflow.set_tracking_uri("sqlite:///mlflow.db")
                return False
        else:
            mlflow.set_tracking_uri("sqlite:///mlflow.db")
            logger.info("Connected to local SQLite database (mlflow.db).")
            return False
    except Exception as e:
        logger.warning("Could not initialize MLflow tracking: %s", e)
        return False


def log_daily_metrics_to_mlflow(anomalies: List[dict], spikes: List[dict]):
    """
    Log daily production metrics to Azure ML via MLflow.

    This creates a continuous monitoring graph in Azure ML Studio
    that tracks model performance and alert counts over time.

    Author: Aulia (ML & Azure) — Hybrid Architecture Production Tracking
    """
    try:
        import mlflow
        setup_mlflow_tracking()

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
    schedule="0 0 1,7 * * *",  # Run at 01:00 UTC (08:00 WIB) & 07:00 UTC (14:00 WIB)
    arg_name="timer",
    run_on_startup=False,
)
def arm_daily_pipeline(timer: func.TimerRequest) -> None:
    """
    ARM Daily Pipeline — runs twice daily: 08:00 WIB and 14:00 WIB.

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
    # Initialize MLflow tracking globally at startup to log all 84 models (Aulia)
    setup_mlflow_tracking()
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
