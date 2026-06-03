"""
Shared test fixtures for the ARM test suite.

Author: Arief (Test, Docs & Comms)
"""

import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def sample_multidim_df():
    """
    Create a realistic multi-dimensional DataFrame
    mimicking dataup JSON output (3 commodities × 2 regions × 2 sources × 30 days).
    """
    dates = pd.date_range('2025-01-01', periods=30, freq='D')
    commodities = ['Beras Kualitas Bawah I', 'Cabai Merah Keriting', 'Telur Ayam Ras Segar']
    regions = ['Banda Aceh', 'Lhokseumawe']
    sources = ['Pasar Tradisional', 'Pasar Modern']

    records = []
    np.random.seed(42)
    base_prices = {
        'Beras Kualitas Bawah I': 13000,
        'Cabai Merah Keriting': 60000,
        'Telur Ayam Ras Segar': 30000,
    }

    for date in dates:
        for commodity in commodities:
            for region in regions:
                for source in sources:
                    base = base_prices[commodity]
                    # Add some variance by region and source
                    noise = np.random.normal(0, base * 0.02)
                    records.append({
                        'date': date,
                        'commodity': commodity,
                        'price': round(base + noise, 0),
                        'year': date.year,
                        'month': date.month,
                        'category': {
                            'Beras Kualitas Bawah I': 'Beras',
                            'Cabai Merah Keriting': 'Cabai Merah',
                            'Telur Ayam Ras Segar': 'Telur Ayam',
                        }[commodity],
                        'daerah': region,
                        'sumber': source,
                    })

    return pd.DataFrame(records)


@pytest.fixture
def sample_province_df(sample_multidim_df):
    """Aggregated DataFrame at province level (no daerah/sumber)."""
    from scripts.etl import aggregate_prices
    return aggregate_prices(sample_multidim_df, by='province')


@pytest.fixture
def sample_stable_prices():
    """DataFrame with very stable prices (no anomalies expected)."""
    dates = pd.date_range('2025-01-01', periods=90, freq='D')
    records = []
    for date in dates:
        records.append({
            'date': date,
            'commodity': 'Gula Pasir Lokal',
            'price': 15000.0,  # Perfectly stable
            'year': date.year,
            'month': date.month,
            'category': 'Gula Pasir',
        })
    return pd.DataFrame(records)


@pytest.fixture
def sample_spike_prices():
    """DataFrame with a clear price spike for anomaly detection."""
    dates = pd.date_range('2025-01-01', periods=60, freq='D')
    prices = [15000.0] * 50 + [25000.0] * 10  # Sudden 67% spike at day 50
    records = []
    for date, price in zip(dates, prices):
        records.append({
            'date': date,
            'commodity': 'Bawang Merah Ukuran Sedang',
            'price': price,
            'year': date.year,
            'month': date.month,
            'category': 'Bawang Merah',
        })
    return pd.DataFrame(records)
