"""
Tests for scripts/anomaly.py — Z-Score anomaly detection.
"""

import pytest

from scripts.anomaly import classify_severity, detect_anomalies, detect_future_spikes


class TestClassifySeverity:
    """Test severity classification based on Z-Score."""

    def test_critical_high_positive(self):
        assert classify_severity(3.5) == 'critical'

    def test_critical_high_negative(self):
        assert classify_severity(-3.5) == 'critical'

    def test_critical_exact_boundary(self):
        # |z| > 3.0 is critical, so exactly 3.0 should be warning
        assert classify_severity(3.0) == 'warning'

    def test_warning_moderate_positive(self):
        assert classify_severity(2.5) == 'warning'

    def test_warning_moderate_negative(self):
        assert classify_severity(-2.5) == 'warning'

    def test_warning_at_threshold(self):
        assert classify_severity(2.0) == 'warning'


class TestDetectAnomalies:
    """Test anomaly detection on synthetic data."""

    def test_stable_data_no_anomaly(self, sample_stable_prices):
        """Perfectly stable prices should produce no anomalies."""
        anomalies = detect_anomalies(sample_stable_prices, window=30, threshold=2.0)
        assert len(anomalies) == 0

    def test_spike_detected(self, sample_spike_prices):
        """A sudden 67% price spike should be detected as anomaly."""
        anomalies = detect_anomalies(sample_spike_prices, window=30, threshold=2.0)
        assert len(anomalies) > 0
        # The spike should be detected with positive deviation
        spike_anomalies = [a for a in anomalies if a['deviation_pct'] > 0]
        assert len(spike_anomalies) > 0

    def test_spike_severity_is_critical(self, sample_spike_prices):
        """A 67% spike should produce at least one critical anomaly."""
        anomalies = detect_anomalies(sample_spike_prices, window=30, threshold=2.0)
        critical = [a for a in anomalies if a['severity'] == 'critical']
        assert len(critical) > 0

    def test_anomaly_has_required_fields(self, sample_spike_prices):
        """Each anomaly dict should have all required fields."""
        anomalies = detect_anomalies(sample_spike_prices, window=30, threshold=2.0)
        assert len(anomalies) > 0

        required_fields = {'commodity', 'date', 'price', 'ma30', 'std30',
                           'z_score', 'deviation_pct', 'severity'}
        for anomaly in anomalies:
            assert required_fields.issubset(anomaly.keys())

    def test_empty_df_returns_empty(self):
        """Empty DataFrame should return empty list."""
        import pandas as pd
        empty_df = pd.DataFrame()
        assert detect_anomalies(empty_df) == []

    def test_sorted_by_date_descending(self, sample_spike_prices):
        """Anomalies should be sorted newest first."""
        anomalies = detect_anomalies(sample_spike_prices, window=30, threshold=2.0)
        if len(anomalies) > 1:
            dates = [a['date'] for a in anomalies]
            assert dates == sorted(dates, reverse=True)


class TestDetectFutureSpikes:
    """Test future spike detection from forecasts."""

    def test_high_spike_detected(self):
        """A large predicted spike should be detected."""
        forecasts = {
            'Cabai Merah Keriting': {
                'aggregated': {
                    'dates': ['2025-04-01', '2025-04-02'],
                    'yhat': [100000, 120000],  # 100% increase from 60000
                    'yhat_lower': [90000, 110000],
                    'yhat_upper': [110000, 130000],
                }
            }
        }
        latest_prices = {'Cabai Merah Keriting': 60000}
        spikes = detect_future_spikes(forecasts, latest_prices, threshold_pct=15.0)
        assert len(spikes) > 0
        assert spikes[0]['spike_pct'] > 15

    def test_no_spike_when_stable(self):
        """Stable forecast should not flag spikes."""
        forecasts = {
            'Gula Pasir Lokal': {
                'aggregated': {
                    'dates': ['2025-04-01', '2025-04-02'],
                    'yhat': [15100, 15200],  # Only ~1% increase
                    'yhat_lower': [14800, 14900],
                    'yhat_upper': [15400, 15500],
                }
            }
        }
        latest_prices = {'Gula Pasir Lokal': 15000}
        spikes = detect_future_spikes(forecasts, latest_prices, threshold_pct=15.0)
        assert len(spikes) == 0

    def test_spike_has_required_fields(self):
        """Spike predictions should have all expected fields."""
        forecasts = {
            'Cabai Rawit Hijau': {
                'aggregated': {
                    'dates': ['2025-04-01'],
                    'yhat': [120000],
                    'yhat_lower': [100000],
                    'yhat_upper': [140000],
                }
            }
        }
        latest_prices = {'Cabai Rawit Hijau': 50000}
        spikes = detect_future_spikes(forecasts, latest_prices, threshold_pct=15.0)
        assert len(spikes) > 0

        required = {'commodity', 'shortName', 'current_price', 'price',
                     'spike_pct', 'severity', 'action'}
        assert required.issubset(spikes[0].keys())

    def test_sorted_by_spike_pct_descending(self):
        """Spikes should be sorted by severity (largest first)."""
        forecasts = {
            'Cabai Merah Keriting': {
                'aggregated': {
                    'dates': ['2025-04-01'],
                    'yhat': [100000],
                    'yhat_lower': [90000],
                    'yhat_upper': [110000],
                }
            },
            'Cabai Rawit Hijau': {
                'aggregated': {
                    'dates': ['2025-04-01'],
                    'yhat': [200000],
                    'yhat_lower': [180000],
                    'yhat_upper': [220000],
                }
            },
        }
        latest_prices = {
            'Cabai Merah Keriting': 60000,
            'Cabai Rawit Hijau': 50000,
        }
        spikes = detect_future_spikes(forecasts, latest_prices, threshold_pct=15.0)
        if len(spikes) > 1:
            pcts = [s['spike_pct'] for s in spikes]
            assert pcts == sorted(pcts, reverse=True)
