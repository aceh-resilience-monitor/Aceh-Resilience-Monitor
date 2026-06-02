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
from scripts.etl import aggregate_prices, add_holiday_features

logger = logging.getLogger(__name__)

# Suppress Prophet/Stan verbose output
warnings.filterwarnings('ignore', category=FutureWarning)


# List of holiday feature columns used as Prophet Extra Regressors
# Author: Aulia (ML & Azure) — G12 Meugang Feature Engineering
HOLIDAY_REGRESSORS = [
    'is_meugang_season',  # Tradisi Meugang Aceh (H-2 s/d H-0)
    'is_ramadan_prep',    # 7 hari menjelang Ramadan
    'is_nataru',          # Natal + Tahun Baru (20 Des - 2 Jan)
    'is_wet_season',      # Musim hujan BMKG Sumatera (Okt-Apr)
]


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
    - Extra Regressors: Meugang, Ramadan, Nataru, Wet Season (G12)

    Args:
        df_commodity: DataFrame with columns 'ds' (datetime) and 'y' (price)
                      May also contain holiday feature columns.
        yearly_seasonality: Enable yearly seasonality detection
        weekly_seasonality: Enable weekly seasonality detection

    Returns:
        Fitted Prophet model

    Author: Aulia (ML & Azure)
    """
    from prophet import Prophet

    model = Prophet(
        yearly_seasonality=yearly_seasonality,
        weekly_seasonality=weekly_seasonality,
        daily_seasonality=False,
        seasonality_mode='multiplicative',
        changepoint_prior_scale=0.05,
    )

    # Register holiday Extra Regressors if columns are present (G12)
    # Author: Aulia (ML & Azure) — Meugang local wisdom feature engineering
    registered = []
    for regressor in HOLIDAY_REGRESSORS:
        if regressor in df_commodity.columns:
            model.add_regressor(regressor)
            registered.append(regressor)

    if registered:
        logger.info("Prophet regressors registered: %s", ', '.join(registered))

    model.fit(df_commodity)
    return model


def predict_future(
    model: 'Prophet',
    periods: int = FORECAST_DAYS,
) -> pd.DataFrame:
    """
    Generate forecast from a trained Prophet model.

    Injects holiday features into the future dataframe so Prophet
    can apply learned regressor effects to predictions. This is the
    key step that makes Meugang predictions work for future dates.

    Args:
        model: Fitted Prophet model
        periods: Number of days to forecast (default: 90)

    Returns:
        DataFrame with columns: ds, yhat, yhat_lower, yhat_upper

    Author: Aulia (ML & Azure)
    """
    future = model.make_future_dataframe(periods=periods)

    # Inject holiday features into future dataframe (deterministic)
    # Author: Aulia (ML & Azure) — G12 Prophet Extra Regressor injection
    # Without this, Prophet will crash with "Regressor is_meugang_season
    # missing from dataframe" error.
    if any(reg in (model.extra_regressors or {}) for reg in HOLIDAY_REGRESSORS):
        future = add_holiday_features(future)

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

    # Inject holiday features into training data (Meugang, Ramadan, Nataru, wet season)
    # Author: Aulia (ML & Azure) — G12 Feature Engineering
    prophet_df = add_holiday_features(prophet_df)

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
