# 🚀 Week 2 Implementation Walkthrough

## Summary

Implemented 7 of 8 phases for Week 2 deliverables targeting score improvement from ~76 → ~87.

## Changes Made

### Phase 1: Holiday Feature Engineering — [etl.py](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/scripts/etl.py)
- Added `MEUGANG_DATES` lookup (2021-2026) and `RAMADAN_START_DATES`
- New function `add_holiday_features(df)` producing **4 deterministic flags**:
  - `is_meugang_season` — Tradisi Meugang Aceh (H-2 s/d H-0)
  - `is_ramadan_prep` — 7 hari menjelang Ramadan
  - `is_nataru` — Natal + Tahun Baru (20 Des - 2 Jan)
  - `is_wet_season` — Musim hujan BMKG (Oktober-April)
- Auto-detects `date` vs `ds` column (historical vs Prophet future)

### Phase 2: Prophet Extra Regressors — [forecast.py](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/scripts/forecast.py)
- `train_prophet()` now registers holiday regressors via `model.add_regressor()`
- `predict_future()` injects holiday features into future dataframe
- `_forecast_single_series()` enriches training data with `add_holiday_features()`

### Phase 3: MLflow Upgrade — [train_with_mlflow.py](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/scripts/train_with_mlflow.py)
- Holiday features injected before training + backtesting
- Logs `extra_regressors` and `has_meugang_regressor` to MLflow
- Final model trained with regressors

### Phase 4: Azure Functions — [function_app.py](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/azure-functions/function_app.py)
- Timer trigger at 08:00 WIB (01:00 UTC)
- 7-step pipeline: Load Blob → Z-Score → Prophet → EWS → Telegram → Dashboard → MLflow
- Opsi A: per-year JSON files from Blob Storage

### Phase 5: Telegram Alerts — [telegram_alert.py](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/scripts/telegram_alert.py)
- Premium-formatted daily reports
- Commodity-specific action recommendations (G7): "operasi pasar cabai", "lepas buffer stock beras", etc.
- Graceful fallback to console when bot token not configured

### Phase 6: Requirements — [requirements.txt](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/requirements.txt)
- Added: mlflow, azureml-core, azureml-mlflow, azure-storage-blob, requests

### Phase 7: Documentation
- [azure_architecture.md](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/docs/azure_architecture.md) — Architecture diagram, service justification, $0/month cost
- [evaluation_prophet.md](file:///Users/auliamuzhaffar/Documents/Datathon/datathon-dicoding/evaluation_prophet.md) — Error analysis (G18), risk matrix, Meugang feature section

## Testing & Verification

| Test | Result |
|------|--------|
| `pytest tests/ -v` | **56 passed** ✅ |
| Holiday features (historical) | meugang=5311, ramadan=4490, nataru=7504, wet=127250 ✅ |
| Holiday features (future) | meugang=9, nataru=12 for 2026 ✅ |
| Telegram module format | Premium message output ✅ |
| Azure Functions syntax | Valid ✅ |

## Remaining

- Phase 8: `notebooks/analysis_walkthrough.ipynb` (G16 reproducibility)
- Azure Functions deploy (`func azure functionapp publish`)
- MLflow end-to-end training (requires Prophet + Azure ML login)
