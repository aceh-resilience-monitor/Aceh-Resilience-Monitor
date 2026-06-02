"""
ARM Anomaly Detection Module
==============================
Z-Score based anomaly detection for commodity prices.
Supports both historical anomaly detection and future spike prediction.

Author: Aulia (ML & Azure)

Key functions:
    classify_severity()      — Map Z-Score to severity level
    detect_anomalies()       — Find price anomalies in historical data
    detect_future_spikes()   — Identify predicted price spikes from forecasts

Usage:
    from scripts.anomaly import detect_anomalies, detect_future_spikes
    anomalies = detect_anomalies(df, commodities)
    spikes = detect_future_spikes(forecasts, latest_prices)
"""

import logging
import warnings
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Suppress pandas 3.0 chained assignment warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

from scripts.config import (
    MA_WINDOW_DAYS,
    SHORT_NAMES,
    SPIKE_THRESHOLD_PCT,
    ZSCORE_CRITICAL,
    ZSCORE_THRESHOLD,
    CATEGORY_MAP,
    CATEGORY_ICONS,
)

logger = logging.getLogger(__name__)


def classify_severity(z_score: float) -> str:
    """
    Classify anomaly severity based on Z-Score magnitude.

    Thresholds follow Shewhart Control Charts (1924) — industry standard:
    - |z| > 3σ → critical (extremely rare event, < 0.3% probability)
    - |z| > 2σ → warning (unusual event, < 5% probability)

    Args:
        z_score: The Z-Score value (can be positive or negative)

    Returns:
        'critical' or 'warning'
    """
    if abs(z_score) > ZSCORE_CRITICAL:
        return 'critical'
    return 'warning'


def detect_anomalies(
    df: pd.DataFrame,
    commodities: Optional[List[str]] = None,
    window: int = MA_WINDOW_DAYS,
    threshold: float = ZSCORE_THRESHOLD,
    group_by: Optional[str] = None,
) -> List[dict]:
    """
    Detect price anomalies using Moving Average + Z-Score method.

    For each commodity (and optionally per region), calculate:
    - MA = rolling mean of prices over the window
    - STD = rolling standard deviation
    - Z-Score = (price - MA) / STD
    - If |Z-Score| > threshold → anomaly detected

    Args:
        df: DataFrame with columns: date, commodity, price (+ optionally daerah)
        commodities: List of commodity names to analyze. None = all.
        window: Rolling window size in days (default: 30)
        threshold: Z-Score threshold for anomaly detection (default: 2.0)
        group_by: None = aggregated, 'daerah' = per-region detection

    Returns:
        List of anomaly dicts, sorted by date (newest first):
            [{commodity, date, price, ma30, std30, z_score, deviation_pct,
              severity, daerah (if group_by='daerah')}]
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to detect_anomalies")
        return []

    if commodities is None:
        commodities = df['commodity'].unique().tolist()

    # Determine grouping columns
    iter_cols = ['commodity']
    if group_by == 'daerah' and 'daerah' in df.columns:
        iter_cols.append('daerah')

    anomalies = []

    for group_values, group_df in df.groupby(iter_cols):
        if isinstance(group_values, str):
            commodity = group_values
            daerah = None
        else:
            commodity = group_values[0]
            daerah = group_values[1] if len(group_values) > 1 else None

        if commodity not in commodities:
            continue

        ts = group_df.sort_values('date').copy()
        if len(ts) < window:
            continue

        ts['ma'] = ts['price'].rolling(window, min_periods=window).mean()
        ts['std'] = ts['price'].rolling(window, min_periods=window).std()
        ts['z_score'] = (ts['price'] - ts['ma']) / ts['std']

        # Filter anomalies where |z| exceeds threshold
        mask = ts['z_score'].abs() > threshold
        anomaly_rows = ts[mask].copy()

        for _, row in anomaly_rows.iterrows():
            entry = {
                'commodity': commodity,
                'date': row['date'].strftime('%Y-%m-%d'),
                'price': round(float(row['price']), 0),
                'ma30': round(float(row['ma']), 0),
                'std30': round(float(row['std']), 0),
                'z_score': round(float(row['z_score']), 2),
                'deviation_pct': round(
                    (float(row['price']) - float(row['ma'])) / float(row['ma']) * 100, 1
                ),
                'severity': classify_severity(float(row['z_score'])),
            }
            if daerah is not None:
                entry['daerah'] = daerah
            anomalies.append(entry)

    # Sort by date descending (newest first)
    anomalies.sort(key=lambda x: x['date'], reverse=True)

    critical_count = sum(1 for a in anomalies if a['severity'] == 'critical')
    warning_count = sum(1 for a in anomalies if a['severity'] == 'warning')
    logger.info(
        "Detected %d anomalies (%d critical, %d warning) across %d commodities",
        len(anomalies), critical_count, warning_count, len(commodities)
    )
    return anomalies


def detect_future_spikes(
    forecasts: Dict,
    latest_prices: Dict[str, float],
    threshold_pct: float = SPIKE_THRESHOLD_PCT,
) -> List[dict]:
    """
    Detect predicted price spikes from Prophet forecast output.

    Compares the maximum predicted price (yhat) against the current price.
    If the predicted increase exceeds the threshold percentage, it's flagged.

    Args:
        forecasts: Dict of forecasts from forecast.py:
            {commodity: {dates, yhat, yhat_lower, yhat_upper}} or
            {commodity: {region: {dates, yhat, ...}, 'aggregated': {...}}}
        latest_prices: Dict mapping commodity name → current price
        threshold_pct: Minimum predicted increase percentage to flag (default: 15%)

    Returns:
        List of spike predictions, sorted by spike_pct descending:
            [{commodity, shortName, current_price, price, spike_pct,
              severity, action, daerah (if per-region)}]
    """
    spikes = []

    for commodity, fc_data in forecasts.items():
        current_price = latest_prices.get(commodity)
        if current_price is None or current_price <= 0:
            continue

        # Handle both flat and per-region forecast structures
        forecast_entries = {}
        if 'yhat' in fc_data:
            # Flat structure: {dates, yhat, ...}
            forecast_entries['aggregated'] = fc_data
        else:
            # Per-region structure: {region_name: {dates, yhat, ...}}
            forecast_entries = fc_data

        for region_key, fc in forecast_entries.items():
            if 'yhat' not in fc:
                continue

            max_predicted = max(fc['yhat'])
            spike_pct = (max_predicted - current_price) / current_price * 100

            if spike_pct > threshold_pct:
                category = CATEGORY_MAP.get(commodity, '')
                icon = CATEGORY_ICONS.get(category, '📦')
                short_name = SHORT_NAMES.get(commodity, commodity)

                # Generate action recommendation based on severity
                if spike_pct >= 50:
                    action = (
                        f"🔴 Segera siapkan operasi pasar untuk {short_name}. "
                        "Kenaikan diprediksi sangat signifikan."
                    )
                    severity = 'prediction'
                else:
                    action = (
                        f"🟡 Pantau stok {short_name} dan siapkan jalur distribusi alternatif."
                    )
                    severity = 'prediction'

                entry = {
                    'commodity': commodity,
                    'shortName': short_name,
                    'icon': icon,
                    'current_price': round(current_price, 0),
                    'price': round(max_predicted, 0),
                    'spike_pct': round(spike_pct, 1),
                    'severity': severity,
                    'action': action,
                }
                if region_key != 'aggregated':
                    entry['daerah'] = region_key

                spikes.append(entry)

    # Sort by spike_pct descending (largest spike first)
    spikes.sort(key=lambda x: x['spike_pct'], reverse=True)

    logger.info(
        "Detected %d future price spike predictions (threshold: >%.0f%%)",
        len(spikes), threshold_pct
    )
    return spikes
