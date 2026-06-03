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

import numpy as np
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


def calculate_metrics(y_true, y_pred):
    """Calculates MAE, RMSE, and MAPE metrics using numpy."""
    mask = (y_true > 0) & (~np.isnan(y_true)) & (~np.isnan(y_pred))
    if np.sum(mask) == 0:
        return 0.0, 0.0, 0.0
    y_t = y_true[mask]
    y_p = y_pred[mask]
    mae = np.mean(np.abs(y_t - y_p))
    rmse = np.sqrt(np.mean((y_t - y_p) ** 2))
    mape = np.mean(np.abs((y_t - y_p) / y_t)) * 100
    return float(mae), float(rmse), float(mape)


def _forecast_single_series(
    df_series: pd.DataFrame,
    commodity: str,
    region_label: str,
    periods: int,
) -> Optional[Dict]:
    """
    Train and forecast a single time series. Internal helper.
    Performs backtesting evaluation and logs metrics to MLflow.

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
    prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
    prophet_df = prophet_df.sort_values('ds').reset_index(drop=True)
    prophet_df = add_holiday_features(prophet_df)

    # 1. Backtesting split (Validation on last 90 days)
    mae, rmse, mape = 0.0, 0.0, 0.0
    split_date = prophet_df['ds'].max() - pd.Timedelta(days=90)
    train_pdf = prophet_df[prophet_df['ds'] <= split_date].copy()
    val_pdf = prophet_df[prophet_df['ds'] > split_date].copy()
    
    active_regressors = [r for r in HOLIDAY_REGRESSORS if r in prophet_df.columns]

    if len(train_pdf) >= 30 and len(val_pdf) > 0:
        try:
            from prophet import Prophet
            eval_model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05
            )
            for reg in active_regressors:
                eval_model.add_regressor(reg)
            eval_model.fit(train_pdf)
            
            future = eval_model.make_future_dataframe(periods=len(val_pdf))
            future = add_holiday_features(future)
            forecast = eval_model.predict(future)
            
            merged = pd.merge(
                val_pdf[['ds', 'y']], 
                forecast[['ds', 'yhat']], 
                on='ds', 
                how='inner'
            )
            mae, rmse, mape = calculate_metrics(merged['y'].values, merged['yhat'].values)
        except Exception as eval_err:
            logger.warning("Validation split failed for %s [%s]: %s", commodity, region_label, eval_err)

    # 2. Train final model on 100% data
    try:
        model = train_prophet(prophet_df)
        fc = predict_future(model, periods=periods)

        # 3. Log runs to MLflow (integrated with Azure ML)
        try:
            import mlflow
            import mlflow.prophet
            
            # Support nested child runs under parent run context (Aulia)
            nested = False
            if mlflow.active_run() is not None:
                nested = True
            else:
                mlflow.set_experiment("arm-prophet-forecasting")
            
            # Formulate the run name to represent both commodity and region
            comm_slug = commodity.lower().replace(' ', '_')
            reg_slug = region_label.lower().replace(' ', '_')
            run_name = f"prophet-{comm_slug}-{reg_slug}"
            
            with mlflow.start_run(run_name=run_name, nested=nested):
                mlflow.log_param("commodity", commodity)
                mlflow.log_param("region", region_label)
                mlflow.log_param("yearly_seasonality", True)
                mlflow.log_param("weekly_seasonality", False)
                mlflow.log_param("daily_seasonality", False)
                mlflow.log_param("seasonality_mode", "multiplicative")
                mlflow.log_param("changepoint_prior_scale", 0.05)
                mlflow.log_param("total_historical_days", len(prophet_df))
                mlflow.log_param("extra_regressors", ','.join(active_regressors) if active_regressors else 'none')
                mlflow.log_param("has_meugang_regressor", 'is_meugang_season' in active_regressors)
                
                mlflow.log_metric("mae", mae)
                mlflow.log_metric("rmse", rmse)
                mlflow.log_metric("mape", mape)
                
                # Performance rating
                if mape < 10.0:
                    rating = "Sangat Baik"
                elif mape < 20.0:
                    rating = "Baik"
                else:
                    rating = "Perlu Tuning"
                mlflow.log_param("performance_rating", rating)
                
                # To prevent timeout on serverless consumption plan, we ONLY log model artifacts
                # for the 21 aggregated provincial models. We skip it for the 63 regional models.
                # Avoid using mlflow.prophet.log_model due to Azure ML compatibility issues with /logged-models API (Aulia)
                if region_label == 'aggregated':
                    from prophet.serialize import model_to_json
                    import tempfile
                    import os
                    with tempfile.TemporaryDirectory() as tmpdir:
                        model_json_path = os.path.join(tmpdir, "model.json")
                        with open(model_json_path, "w", encoding="utf-8") as f:
                            f.write(model_to_json(model))
                        mlflow.log_artifact(model_json_path, artifact_path="model")
                    
        except Exception as mlflow_err:
            logger.warning("MLflow logging failed for %s [%s]: %s", commodity, region_label, mlflow_err)

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
