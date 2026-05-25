"""
ARM train_with_mlflow.py — Prophet Model Training and MLflow Experiment Tracking
================================================================================
Trains 21 commodity-level Prophet models and logs parameters, metrics,
and model artifacts to MLflow (integrated with Azure ML or run locally).

Features:
- Dual Mode: Detects config.json to connect to Azure ML Workspace;
             Falls back to local sqlite tracking if config.json is missing.
- Backtesting: Splits historical data (Holdout last 90 days) to calculate true
               evaluation metrics (MAE, RMSE, MAPE).
- Final Model Logging: Fits model on the entire dataset after evaluation and
                       logs it to MLflow as a reusable artifact.

Usage:
    python scripts/train_with_mlflow.py
"""

import logging
import os
import sys
import warnings
from datetime import timedelta
import numpy as np
import pandas as pd

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add root directory to python path to allow absolute imports
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    import mlflow
    import mlflow.prophet
except ImportError:
    logger.error("MLflow is not installed. Please run: pip install mlflow")
    sys.exit(1)

try:
    from prophet import Prophet
except ImportError:
    logger.error("Prophet is not installed. Please run: pip install prophet")
    sys.exit(1)

# Import ARM modules
try:
    from scripts.config import ALL_REGIONS, FORECAST_DAYS
    from scripts.etl import load_all_data, aggregate_prices
except ImportError as e:
    logger.error(f"Failed to import ARM modules: {e}")
    sys.exit(1)


def setup_mlflow_tracking():
    """
    Sets up MLflow tracking URI.
    If config.json is found in the project root, it attempts to connect to Azure ML.
    Otherwise, it runs in local sqlite mode (saved under mlflow.db).
    """
    config_path = os.path.join(root_dir, "config.json")
    
    if os.path.exists(config_path):
        try:
            logger.info("config.json found! Connecting to Azure ML Workspace...")
            from azureml.core import Workspace
            
            ws = Workspace.from_config(path=config_path)
            mlflow.set_tracking_uri(ws.get_mlflow_tracking_uri())
            logger.info(f"Connected to Azure ML Workspace: {ws.name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Azure ML (will fallback to local mode): {e}")
    
    # Fallback to local SQLite database so code doesn't crash
    local_db = "sqlite:///mlflow.db"
    mlflow.set_tracking_uri(local_db)
    logger.info(f"Running MLflow in LOCAL mode (logs saved to {local_db})")
    return False


def calculate_metrics(y_true, y_pred):
    """
    Calculates evaluation metrics using pure numpy (no scikit-learn dependency).
    """
    # Filter out any NaN or zero elements in true values to prevent division by zero in MAPE
    mask = (y_true > 0) & (~np.isnan(y_true)) & (~np.isnan(y_pred))
    
    if np.sum(mask) == 0:
        return 0.0, 0.0, 0.0
        
    y_t = y_true[mask]
    y_p = y_pred[mask]
    
    mae = np.mean(np.abs(y_t - y_p))
    rmse = np.sqrt(np.mean((y_t - y_p) ** 2))
    mape = np.mean(np.abs((y_t - y_p) / y_t)) * 100
    
    return float(mae), float(rmse), float(mape)


def train_and_log_models():
    # 1. Setup Tracking
    setup_mlflow_tracking()
    mlflow.set_experiment("arm-prophet-forecasting")
    
    # 2. Load and Aggregate Data (Provincial average for aggregated model)
    logger.info("Loading cleaned dataset...")
    df = load_all_data()
    df_agg = aggregate_prices(df, by='province')
    
    commodities = df_agg['commodity'].unique()
    logger.info(f"Starting training pipeline for {len(commodities)} commodities...")
    
    summary_results = []
    
    for idx, commodity in enumerate(commodities, 1):
        df_comm = df_agg[df_agg['commodity'] == commodity].copy()
        
        # Prepare data for Prophet: must have columns 'ds' and 'y'
        pdf = df_comm[['date', 'price']].rename(columns={'date': 'ds', 'price': 'y'}).copy()
        pdf['ds'] = pd.to_datetime(pdf['ds'])
        pdf = pdf.sort_values('ds').reset_index(drop=True)
        
        # Insufficient data check
        if len(pdf) < 60:
            logger.warning(f"Skipping {commodity}: insufficient data ({len(pdf)} rows)")
            continue
            
        logger.info(f"[{idx}/{len(commodities)}] Logging run for: {commodity}")
        
        # Start MLflow run
        with mlflow.start_run(run_name=f"prophet-{commodity.lower().replace(' ', '_')}"):
            # ────────────────────────────────────────────────────────
            # 1. Log Hyperparameters & Parameters
            # ────────────────────────────────────────────────────────
            mlflow.log_param("commodity", commodity)
            mlflow.log_param("yearly_seasonality", True)
            mlflow.log_param("weekly_seasonality", False)
            mlflow.log_param("daily_seasonality", False)
            mlflow.log_param("seasonality_mode", "multiplicative")
            mlflow.log_param("changepoint_prior_scale", 0.05)
            mlflow.log_param("total_historical_days", len(pdf))
            
            # ────────────────────────────────────────────────────────
            # 2. Backtesting (Train/Test Split) for Metrics Evaluation
            # ────────────────────────────────────────────────────────
            # Split the last 90 days as validation dataset
            split_date = pdf['ds'].max() - timedelta(days=90)
            train_pdf = pdf[pdf['ds'] <= split_date].copy()
            val_pdf = pdf[pdf['ds'] > split_date].copy()
            
            mae, rmse, mape = 0.0, 0.0, 0.0
            
            if len(train_pdf) >= 30 and len(val_pdf) > 0:
                try:
                    # Train model on training partition
                    eval_model = Prophet(
                        yearly_seasonality=True,
                        weekly_seasonality=False,
                        daily_seasonality=False,
                        seasonality_mode='multiplicative',
                        changepoint_prior_scale=0.05
                    )
                    eval_model.fit(train_pdf)
                    
                    # Predict validation period
                    future = eval_model.make_future_dataframe(periods=len(val_pdf))
                    forecast = eval_model.predict(future)
                    
                    # Merge predictions and actuals on date to align correctly
                    merged = pd.merge(
                        val_pdf[['ds', 'y']], 
                        forecast[['ds', 'yhat']], 
                        on='ds', 
                        how='inner'
                    )
                    
                    # Calculate metrics
                    mae, rmse, mape = calculate_metrics(merged['y'].values, merged['yhat'].values)
                except Exception as e:
                    logger.error(f"Validation split training failed for {commodity}: {e}")
            else:
                logger.warning(f"Could not perform backtesting split for {commodity} due to short data")
            
            # ────────────────────────────────────────────────────────
            # 3. Log Performance Metrics
            # ────────────────────────────────────────────────────────
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("rmse", rmse)
            mlflow.log_metric("mape", mape)
            
            # Determine performance rating
            if mape < 10.0:
                rating = "Sangat Baik"
            elif mape < 20.0:
                rating = "Baik"
            else:
                rating = "Perlu Tuning"
                
            summary_results.append({
                "Commodity": commodity,
                "MAPE (%)": round(mape, 2),
                "MAE (Rp)": round(mae, 0),
                "RMSE (Rp)": round(rmse, 0),
                "Rating": rating
            })
            
            # ────────────────────────────────────────────────────────
            # 4. Train Final Model on 100% Data and Log as Artifact
            # ────────────────────────────────────────────────────────
            final_model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05
            )
            final_model.fit(pdf)
            
            # Save final model state
            mlflow.prophet.log_model(final_model, artifact_path="model")
            logger.info(f"✅ {commodity} logged. MAPE = {mape:.2f}% | Rating = {rating}")
            
    # ────────────────────────────────────────────────────────
    # 5. Print Executive Summary Table
    # ────────────────────────────────────────────────────────
    df_summary = pd.DataFrame(summary_results)
    print("\n" + "="*80)
    print("                      📊 SUMMARY OF MLFLOW RUNS")
    print("="*80)
    print(df_summary.to_string(index=False))
    print("="*80)
    print("Semua runs berhasil dicatat di MLflow tracking server!")
    print("Untuk melihat dashboard MLflow, jalankan: mlflow ui")
    print("="*80 + "\n")


if __name__ == "__main__":
    train_and_log_models()
