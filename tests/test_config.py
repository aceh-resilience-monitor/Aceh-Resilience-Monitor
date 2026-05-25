"""
Tests for scripts/config.py — Constants integrity validation.
"""

from scripts.config import (
    ALL_REGIONS,
    ALL_SOURCES,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    CATEGORY_MAP,
    CHANGE_HIGH,
    CV_HIGH,
    DATA_DIR,
    DATAUP_DIR,
    DASHBOARD_DIR,
    FORECAST_DAYS,
    MA_WINDOW_DAYS,
    PLOT_DIR,
    PROJECT_ROOT,
    REGIONS,
    SHORT_NAMES,
    SPIKE_THRESHOLD_PCT,
    ZSCORE_CRITICAL,
    ZSCORE_THRESHOLD,
)


class TestCategoryMap:
    """Validate CATEGORY_MAP integrity."""

    def test_has_21_commodities(self):
        assert len(CATEGORY_MAP) == 21

    def test_maps_to_10_categories(self):
        categories = set(CATEGORY_MAP.values())
        assert len(categories) == 10

    def test_contains_original_18_commodities(self):
        original_18 = [
            'Beras Kualitas Bawah I', 'Beras Kualitas Bawah II',
            'Beras Kualitas Medium I', 'Beras Kualitas Medium II',
            'Beras Kualitas Super I', 'Beras Kualitas Super II',
            'Daging Ayam Ras Segar', 'Daging Sapi Kualitas 1',
            'Telur Ayam Ras Segar',
            'Bawang Merah Ukuran Sedang', 'Bawang Putih Ukuran Sedang',
            'Cabai Merah Keriting', 'Cabai Rawit Hijau',
            'Minyak Goreng Curah', 'Minyak Goreng Kemasan Bermerk 1',
            'Minyak Goreng Kemasan Bermerk 2',
            'Gula Pasir Kualitas Premium', 'Gula Pasir Lokal',
        ]
        for commodity in original_18:
            assert commodity in CATEGORY_MAP, f"Missing: {commodity}"

    def test_contains_3_new_commodities(self):
        new_3 = ['Cabai Merah Besar', 'Cabai Rawit Merah', 'Daging Sapi Kualitas 2']
        for commodity in new_3:
            assert commodity in CATEGORY_MAP, f"Missing new commodity: {commodity}"


class TestShortNames:
    """Validate SHORT_NAMES matches CATEGORY_MAP."""

    def test_keys_match_category_map(self):
        assert set(SHORT_NAMES.keys()) == set(CATEGORY_MAP.keys())

    def test_all_values_are_non_empty_strings(self):
        for key, value in SHORT_NAMES.items():
            assert isinstance(value, str) and len(value) > 0, f"Empty short name for: {key}"


class TestCategoryIcons:
    """Validate CATEGORY_ICONS covers all categories."""

    def test_covers_all_categories(self):
        categories = set(CATEGORY_MAP.values())
        for cat in categories:
            assert cat in CATEGORY_ICONS, f"Missing icon for category: {cat}"


class TestCategoryColors:
    """Validate CATEGORY_COLORS covers all categories."""

    def test_covers_all_categories(self):
        categories = set(CATEGORY_MAP.values())
        for cat in categories:
            assert cat in CATEGORY_COLORS, f"Missing color for category: {cat}"

    def test_colors_are_hex_format(self):
        for cat, color in CATEGORY_COLORS.items():
            assert color.startswith('#'), f"Non-hex color for {cat}: {color}"


class TestRegionsAndSources:
    """Validate regional and source mappings."""

    def test_regions_has_3_entries(self):
        assert len(REGIONS) == 3

    def test_all_regions_list(self):
        assert len(ALL_REGIONS) == 3
        assert 'Banda Aceh' in ALL_REGIONS
        assert 'Lhokseumawe' in ALL_REGIONS
        assert 'Meulaboh' in ALL_REGIONS

    def test_sources_has_4_entries(self):
        assert len(ALL_SOURCES) == 4

    def test_all_sources_list(self):
        expected = ['Pasar Tradisional', 'Pasar Modern', 'Pedagang Besar', 'Produsen']
        for source in expected:
            assert source in ALL_SOURCES, f"Missing source: {source}"


class TestPaths:
    """Validate path definitions."""

    def test_project_root_exists(self):
        assert PROJECT_ROOT.exists()

    def test_data_dir_defined(self):
        assert DATA_DIR is not None

    def test_dataup_dir_defined(self):
        assert DATAUP_DIR is not None

    def test_dashboard_dir_defined(self):
        assert DASHBOARD_DIR is not None


class TestThresholds:
    """Validate threshold values are sensible."""

    def test_zscore_threshold_positive(self):
        assert ZSCORE_THRESHOLD > 0

    def test_zscore_critical_greater_than_threshold(self):
        assert ZSCORE_CRITICAL > ZSCORE_THRESHOLD

    def test_cv_high_positive(self):
        assert CV_HIGH > 0

    def test_change_high_positive(self):
        assert CHANGE_HIGH > 0

    def test_spike_threshold_positive(self):
        assert SPIKE_THRESHOLD_PCT > 0

    def test_ma_window_positive(self):
        assert MA_WINDOW_DAYS > 0

    def test_forecast_days_positive(self):
        assert FORECAST_DAYS > 0
