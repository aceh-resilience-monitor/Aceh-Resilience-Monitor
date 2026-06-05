import numpy as np
import pytest
from scripts.evaluate_baseline import (
    calculate_mape,
    calculate_mae,
    calculate_rmse,
)

def test_metrics_basic():
    # Perfect predictions
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([100.0, 200.0, 300.0])
    assert calculate_mape(y_true, y_pred) == 0.0
    assert calculate_mae(y_true, y_pred) == 0.0
    assert calculate_rmse(y_true, y_pred) == 0.0

def test_metrics_with_errors():
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([90.0, 220.0, 300.0])
    
    # MAPE: (|100-90|/100 + |200-220|/200 + 0) / 3 = (0.1 + 0.1 + 0) / 3 = 0.0667 -> 6.67%
    assert pytest.approx(calculate_mape(y_true, y_pred), 0.01) == 6.67
    
    # MAE: (10 + 20 + 0) / 3 = 10.0
    assert calculate_mae(y_true, y_pred) == 10.0
    
    # RMSE: sqrt((10^2 + 20^2 + 0) / 3) = sqrt((100+400)/3) = sqrt(166.67) = 12.91
    assert pytest.approx(calculate_rmse(y_true, y_pred), 0.01) == 12.91

def test_metrics_with_nans_and_zeros():
    # Nan and zero inputs should be filtered out safely without division by zero
    y_true = np.array([100.0, 0.0, np.nan, 300.0])
    y_pred = np.array([90.0, 50.0, 100.0, 300.0])
    
    # Only index 0 and 3 are valid
    # MAPE: (|100-90|/100 + 0) / 2 = 0.1 / 2 = 0.05 -> 5.0%
    assert pytest.approx(calculate_mape(y_true, y_pred), 0.01) == 5.0
    
    # MAE: (10 + 0) / 2 = 5.0
    assert calculate_mae(y_true, y_pred) == 5.0
    
    # RMSE: sqrt((10^2 + 0^2)/2) = sqrt(50) = 7.07
    assert pytest.approx(calculate_rmse(y_true, y_pred), 0.01) == 7.07
