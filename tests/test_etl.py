"""
Tests for scripts/etl.py — Data loading, transformation, and aggregation.

Author: Arief (Test, Docs & Comms)
"""

import pandas as pd
import numpy as np
import pytest

from scripts.config import CATEGORY_MAP


class TestAggregation:
    """Test aggregate_prices() with different aggregation levels."""

    def test_aggregate_by_province(self, sample_multidim_df):
        from scripts.etl import aggregate_prices
        result = aggregate_prices(sample_multidim_df, by='province')

        # Province aggregation should collapse daerah & sumber
        assert 'daerah' not in result.columns
        assert 'sumber' not in result.columns
        # Should have fewer records
        assert len(result) < len(sample_multidim_df)
        # Required columns
        assert set(['date', 'commodity', 'price', 'year', 'month', 'category']).issubset(result.columns)

    def test_aggregate_by_region(self, sample_multidim_df):
        from scripts.etl import aggregate_prices
        result = aggregate_prices(sample_multidim_df, by='region')

        # Region aggregation keeps daerah but collapses sumber
        assert 'daerah' in result.columns
        assert 'sumber' not in result.columns
        assert len(result) < len(sample_multidim_df)

    def test_aggregate_by_source(self, sample_multidim_df):
        from scripts.etl import aggregate_prices
        result = aggregate_prices(sample_multidim_df, by='source')

        # Source aggregation keeps sumber but collapses daerah
        assert 'sumber' in result.columns
        assert 'daerah' not in result.columns

    def test_aggregate_full_returns_copy(self, sample_multidim_df):
        from scripts.etl import aggregate_prices
        result = aggregate_prices(sample_multidim_df, by='full')

        assert len(result) == len(sample_multidim_df)
        # Should be a copy, not same object
        assert result is not sample_multidim_df

    def test_aggregate_invalid_raises(self, sample_multidim_df):
        from scripts.etl import aggregate_prices
        with pytest.raises(ValueError, match="Invalid aggregation level"):
            aggregate_prices(sample_multidim_df, by='invalid')


class TestLoadFromDataupJson:
    """Test load_from_dataup_json() functionality."""

    def test_returns_correct_columns(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        expected_cols = {'date', 'commodity', 'price', 'year', 'month',
                         'category', 'daerah', 'sumber'}
        assert expected_cols.issubset(set(df.columns))

    def test_filters_level2_only(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        # Should not contain parent category names as commodities
        parent_categories = {'Beras', 'Daging Ayam', 'Daging Sapi', 'Telur Ayam',
                             'Bawang Merah', 'Bawang Putih', 'Cabai Merah',
                             'Cabai Rawit', 'Minyak Goreng', 'Gula Pasir'}
        commodities = set(df['commodity'].unique())
        # No parent categories should appear as commodity names
        assert commodities.isdisjoint(parent_categories)

    def test_strips_whitespace(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        # No commodity names should have leading/trailing whitespace
        for name in df['commodity'].unique():
            assert name == name.strip(), f"Whitespace not stripped: '{name}'"

    def test_converts_price_to_float(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        assert df['price'].dtype in [np.float64, np.float32, np.int64, np.int32, float, int]
        assert df['price'].min() > 0  # All prices should be positive

    def test_filters_known_commodities(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        known = set(CATEGORY_MAP.keys())
        actual = set(df['commodity'].unique())
        assert actual.issubset(known), f"Unknown commodities: {actual - known}"

    def test_has_21_commodities(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        assert df['commodity'].nunique() == 21

    def test_has_3_regions(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        assert df['daerah'].nunique() == 3

    def test_has_4_sources(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        assert df['sumber'].nunique() == 4

    def test_category_column_populated(self):
        from scripts.etl import load_from_dataup_json
        df = load_from_dataup_json(years=[2025])

        if df.empty:
            pytest.skip("No dataup data available")

        assert df['category'].notna().all()


class TestLoadAllData:
    """Test load_all_data() entry point."""

    def test_returns_non_empty(self):
        from scripts.etl import load_all_data
        df = load_all_data(years=[2025])

        if df.empty:
            pytest.skip("No data available")

        assert len(df) > 0

    def test_has_multidimensional_columns(self):
        from scripts.etl import load_all_data
        df = load_all_data(years=[2025])

        if df.empty:
            pytest.skip("No data available")

        assert 'daerah' in df.columns
        assert 'sumber' in df.columns
