"""
ARM Forecast Module — Prophet Time Series Forecasting
======================================================
Per-region Prophet models for commodity price prediction.
Supports both aggregated (provincial) and per-region forecasting.

Key functions:
    train_prophet()               — Train a single Prophet model
    predict_future()              — Generate forecast from trained model
    forecast_all_commodities()    — Batch forecast all commodities

Usage:
    from scripts.forecast import forecast_all_commodities
    forecasts = forecast_all_commodities(df, commodities, latest_date, per_region=True)
"""

import logging
import warnings
from typing import Dict, List, Optional

import pandas as pd

from scripts.config import ALL_REGIONS, FORECAST_DAYS
from scripts.etl import aggregate_prices

logger = logging.getLogger(__name__)

# Suppress Prophet/Stan verbose output
warnings.filterwarnings('ignore', category=FutureWarning)


def train_prophet(
    df_commodity: pd.DataFrame,
    yearly_seasonality: bool = True,
    weekly_seasonality: bool = False,
) -> 'Prophet':
    """
    Train a Prophet model for a single commodity time series.

    The model is configured for food commodity price data in Aceh:
    - Yearly seasonality enabled (captures Ramadan, harvest cycles)
    - Weekly seasonality disabled by default (daily prices are noisy)
    - Multiplicative seasonality (price changes are proportional)

    Args:
        df_commodity: DataFrame with columns 'ds' (datetime) and 'y' (price)
        yearly_seasonality: Enable yearly seasonality detection
        weekly_seasonality: Enable weekly seasonality detection

    Returns:
        Fitted Prophet model
    """
    from prophet import Prophet

    model = Prophet(
        yearly_seasonality=yearly_seasonality,
        weekly_seasonality=weekly_seasonality,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05,
    )

    model.fit(df_commodity)
    return model


def predict_future(
    model: 'Prophet',
    periods: int = FORECAST_DAYS,
) -> pd.DataFrame:
    """
    Generate forecast from a trained Prophet model.

    Args:
        model: Fitted Prophet model
        periods: Number of days to forecast (default: 90)

    Returns:
        DataFrame with columns: ds, yhat, yhat_lower, yhat_upper
    """
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    # Return only the forecast period (not historical fitted values)
    forecast_only = forecast.tail(periods)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
    return forecast_only


def _forecast_single_series(
    df_series: pd.DataFrame,
    commodity: str,
    region_label: str,
    periods: int,
) -> Optional[Dict]:
    """
    Train and forecast a single time series. Internal helper.

    Args:
        df_series: DataFrame for this series (must have date, price columns)
        commodity: Commodity name (for logging)
        region_label: Region name or 'aggregated' (for logging)
        periods: Forecast horizon in days

    Returns:
        Dict with keys: dates, yhat, yhat_lower, yhat_upper
        None if insufficient data or training fails
    """
    if len(df_series) < 60:
        logger.warning(
            "Insufficient data for %s [%s]: %d records (need 60+)",
            commodity, region_label, len(df_series)
        )
        return None

    prophet_df = df_series[['date', 'price']].rename(
        columns={'date': 'ds', 'price': 'y'}
    ).copy()

    try:
        model = train_prophet(prophet_df)
        fc = predict_future(model, periods=periods)

        return {
            'dates': fc['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'yhat': fc['yhat'].round(0).tolist(),
            'yhat_lower': fc['yhat_lower'].round(0).tolist(),
            'yhat_upper': fc['yhat_upper'].round(0).tolist(),
        }

    except Exception as e:
        logger.error(
            "Prophet training failed for %s [%s]: %s",
            commodity, region_label, str(e)
        )
        return None


def forecast_all_commodities(
    df: pd.DataFrame,
    commodities: List[str],
    latest_date: pd.Timestamp,
    periods: int = FORECAST_DAYS,
    per_region: bool = True,
) -> Dict:
    """
    Forecast all commodities, optionally per region.

    When per_region=True (Approach A — recommended):
    - Trains 21 × 3 = 63 Prophet models (1 per commodity per region)
    - Also trains 21 aggregated models (provincial average)
    - Returns nested dict with both aggregated and per-region forecasts

    When per_region=False:
    - Trains 21 aggregated models only
    - Returns flat dict

    Args:
        df: Multi-dimensional DataFrame from load_all_data()
        commodities: List of commodity names to forecast
        latest_date: Cutoff date for training data
        periods: Forecast horizon in days (default: 90)
        per_region: If True, also train per-region models

    Returns:
        Dict structure:
        {
            'Cabai Merah Keriting': {
                'aggregated': {dates, yhat, yhat_lower, yhat_upper},
                'Banda Aceh': {dates, yhat, ...},
                'Lhokseumawe': {dates, yhat, ...},
                'Meulaboh': {dates, yhat, ...},
            },
            ...
        }
    """
    forecasts = {}
    total_models = 0
    failed_models = 0

    # Prepare aggregated data (provincial average)
    df_agg = aggregate_prices(df, by='province')

    for commodity in commodities:
        forecasts[commodity] = {}

        # ── Aggregated forecast (provincial average) ──
        df_comm = df_agg[df_agg['commodity'] == commodity].copy()
        result = _forecast_single_series(df_comm, commodity, 'aggregated', periods)
        total_models += 1

        if result:
            forecasts[commodity]['aggregated'] = result
        else:
            failed_models += 1

        # ── Per-region forecasts ──
        if per_region and 'daerah' in df.columns:
            df_regional = aggregate_prices(df, by='region')

            for region in ALL_REGIONS:
                df_region = df_regional[
                    (df_regional['commodity'] == commodity) &
                    (df_regional['daerah'] == region)
                ].copy()

                result = _forecast_single_series(
                    df_region, commodity, region, periods
                )
                total_models += 1

                if result:
                    forecasts[commodity][region] = result
                else:
                    failed_models += 1

    logger.info(
        "Forecasting complete: %d/%d models trained successfully | "
        "%d commodities | per_region=%s | horizon=%d days",
        total_models - failed_models, total_models,
        len(commodities), per_region, periods
    )
    return forecasts
