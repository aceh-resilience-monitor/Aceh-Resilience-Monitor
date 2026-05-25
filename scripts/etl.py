"""
ARM ETL Module — Extract, Transform, Load
==========================================
Handles all data loading and transformation for the ARM pipeline.
Supports both historical Excel files and production dataup JSON.

Key functions:
    load_from_dataup_json() — Load scraped JSON data (production source)
    load_all_data()         — Main entry point for data loading
    aggregate_prices()      — Aggregate multi-dimensional data
    add_features()          — Feature engineering for ML models

Usage:
    from scripts.etl import load_all_data, aggregate_prices
    df = load_all_data()
    df_agg = aggregate_prices(df, by='province')
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

import warnings

import numpy as np
import pandas as pd

# Suppress pandas 3.0 chained assignment warnings (our code handles copies correctly)
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

from scripts.config import (
    CATEGORY_MAP,
    DATA_DIR,
    DATA_YEARS,
    DATAUP_DIR,
    PROJECT_ROOT,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# DATA LOADING — Excel (legacy/historical)
# ══════════════════════════════════════════════════════════════════════

def load_and_clean(filepath: Path, year: int) -> pd.DataFrame:
    """
    Load a single Excel commodity price file and return a clean DataFrame.

    The Excel files from PIHPS have a non-standard layout:
    - Row 0: date headers in DD/ MM/ YYYY format
    - Row 1+: commodity data with Roman numeral category markers (I, II, ...)
    - Prices may contain comma separators, dashes, or be NaN

    Args:
        filepath: Path to the .xlsx file
        year: Year label to attach to records

    Returns:
        DataFrame with columns: date, commodity, price, year
    """
    raw = pd.read_excel(filepath, header=None)
    date_strings = raw.iloc[0, 2:].values
    dates = pd.to_datetime(date_strings, format='%d/ %m/ %Y')

    # Filter out Roman numeral category header rows
    roman_numerals = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}
    data_rows = raw.iloc[1:]
    mask = ~data_rows.iloc[:, 0].isin(roman_numerals)
    commodity_data = data_rows[mask].copy()

    records = []
    for _, row in commodity_data.iterrows():
        commodity_name = str(row.iloc[1]).strip()
        prices = row.iloc[2:].values
        for date, price in zip(dates, prices):
            price_str = str(price).strip()
            if pd.isna(price) or price_str in ('', '-', 'nan'):
                price_val = np.nan
            else:
                price_val = float(price_str.replace(',', ''))
            records.append({
                'date': date,
                'commodity': commodity_name,
                'price': price_val,
                'year': year,
            })

    df = pd.DataFrame(records)
    logger.info("Loaded %d records from %s", len(df), filepath.name)
    return df


def load_from_excel(years: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Load and combine Excel files for multiple years.

    Args:
        years: List of years to load. Defaults to DATA_YEARS from config.

    Returns:
        Clean DataFrame with columns: date, commodity, price, year, month, category
    """
    if years is None:
        years = DATA_YEARS

    frames = []
    for y in years:
        filepath = DATA_DIR / f'{y}.xlsx'
        if filepath.exists():
            frames.append(load_and_clean(filepath, y))
        else:
            logger.warning("Excel file not found: %s", filepath)

    if not frames:
        logger.error("No Excel data files found!")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['category'] = df['commodity'].map(CATEGORY_MAP)
    df_clean = df.dropna(subset=['price']).copy()

    logger.info(
        "Loaded %d clean records from Excel (%d years)",
        len(df_clean), len(years)
    )
    return df_clean


# ══════════════════════════════════════════════════════════════════════
# DATA LOADING — dataup JSON (production source)
# ══════════════════════════════════════════════════════════════════════

def load_from_dataup_json(years: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Load scraped data from dataup/data/*.json and transform to pipeline format.

    The dataup scraper produces JSON files with per-day, per-region, per-source
    granularity. This function:
    1. Loads all JSON year-files from DATAUP_DIR
    2. Filters to level 2 only (sub-commodities, not parent categories)
    3. Strips whitespace from commodity names (fixes trailing space bug)
    4. Converts price strings ("13,350") to float (13350.0)
    5. Filters to known CATEGORY_MAP commodities (21 sub-commodities)
    6. Adds enrichment columns (year, month, category)

    Args:
        years: List of years to load. None = load all available.

    Returns:
        DataFrame with columns:
            date, commodity, price, year, month, category, daerah, sumber
    """
    if not DATAUP_DIR.exists():
        logger.error("dataup data directory not found: %s", DATAUP_DIR)
        return pd.DataFrame()

    all_records = []
    json_files = sorted(DATAUP_DIR.glob('*.json'))

    if not json_files:
        logger.error("No JSON files found in %s", DATAUP_DIR)
        return pd.DataFrame()

    for json_file in json_files:
        try:
            file_year = int(json_file.stem)
        except ValueError:
            logger.warning("Skipping non-year file: %s", json_file.name)
            continue

        if years is not None and file_year not in years:
            continue

        with open(json_file, 'r', encoding='utf-8') as f:
            raw = json.load(f)

        # Filter level 2 only (actual sub-commodities, not parent categories)
        level2 = [r for r in raw if r.get('level') == 2]
        all_records.extend(level2)
        logger.info(
            "Loaded %d level-2 records from %s (total raw: %d)",
            len(level2), json_file.name, len(raw)
        )

    if not all_records:
        logger.warning("No records loaded from dataup JSON files")
        return pd.DataFrame()

    df = pd.DataFrame(all_records).copy()

    # ── Clean & Transform ──
    # Strip whitespace from commodity names (fixes "Cabai Merah Keriting " bug)
    df['name'] = df['name'].str.strip()

    # Filter to known commodities only (21 sub-commodities)
    known_commodities = set(CATEGORY_MAP.keys())
    df = df[df['name'].isin(known_commodities)].copy()

    if df.empty:
        logger.warning("No records match CATEGORY_MAP after filtering")
        return pd.DataFrame()

    # Convert price: string "13,350" → float 13350.0
    # Handle null prices (harga is None in JSON)
    df['price'] = pd.to_numeric(
        df['harga'].astype(str).str.replace(',', '', regex=False),
        errors='coerce'
    )

    # Rename & enrich
    df['date'] = pd.to_datetime(df['tanggal'])
    df['commodity'] = df['name']
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['category'] = df['commodity'].map(CATEGORY_MAP)

    # Select final columns, keep multi-dimensional data
    columns = ['date', 'commodity', 'price', 'year', 'month', 'category',
               'daerah', 'sumber']
    df = df[columns].dropna(subset=['price']).copy()

    df = df.sort_values(['date', 'commodity', 'daerah', 'sumber']).reset_index(drop=True)

    logger.info(
        "Loaded %d clean records from dataup JSON | "
        "%d commodities | %d regions | %d sources | date range: %s — %s",
        len(df),
        df['commodity'].nunique(),
        df['daerah'].nunique(),
        df['sumber'].nunique(),
        df['date'].min().strftime('%Y-%m-%d'),
        df['date'].max().strftime('%Y-%m-%d'),
    )
    return df


# ══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

def load_all_data(years: Optional[List[int]] = None) -> pd.DataFrame:
    """
    Main entry point for loading data.
    Uses dataup JSON as the production data source.

    Args:
        years: List of years to load. None = load all available.

    Returns:
        Multi-dimensional DataFrame with daerah and sumber columns.
    """
    return load_from_dataup_json(years)


# ══════════════════════════════════════════════════════════════════════
# AGGREGATION — Reduce multi-dimensional data for different use cases
# ══════════════════════════════════════════════════════════════════════

def aggregate_prices(
    df: pd.DataFrame,
    by: str = 'province',
) -> pd.DataFrame:
    """
    Aggregate multi-dimensional price data for different analysis needs.

    The raw data has granularity: (date × commodity × daerah × sumber).
    This function reduces dimensions based on the 'by' parameter.

    Args:
        df: Multi-dimensional DataFrame from load_all_data()
        by: Aggregation level:
            'province' — Group by (date, commodity) → mean across all daerah & sumber
            'region'   — Group by (date, commodity, daerah) → mean across sumber
            'source'   — Group by (date, commodity, sumber) → mean across daerah
            'full'     — No aggregation, return as-is

    Returns:
        Aggregated DataFrame
    """
    if by == 'full':
        return df.copy()

    group_cols_map = {
        'province': ['date', 'commodity', 'year', 'month', 'category'],
        'region': ['date', 'commodity', 'year', 'month', 'category', 'daerah'],
        'source': ['date', 'commodity', 'year', 'month', 'category', 'sumber'],
    }

    if by not in group_cols_map:
        raise ValueError(f"Invalid aggregation level: {by}. Choose from: {list(group_cols_map.keys())}")

    group_cols = group_cols_map[by]
    # Only use columns that exist in the DataFrame
    group_cols = [c for c in group_cols if c in df.columns]

    result = df.groupby(group_cols, as_index=False)['price'].mean()
    result['price'] = result['price'].round(0)

    logger.info(
        "Aggregated by '%s': %d → %d records",
        by, len(df), len(result)
    )
    return result


# ══════════════════════════════════════════════════════════════════════
# FEATURE ENGINEERING — For ML models (G9)
# ══════════════════════════════════════════════════════════════════════

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add engineered features to the price DataFrame.

    Features added per commodity (and per daerah if present):
    - price_lag_1d, price_lag_7d, price_lag_30d: Lagged prices
    - rolling_mean_7d, rolling_std_7d: Rolling window statistics
    - price_momentum_7d: 7-day price change percentage
    - day_of_week: Day of week encoding (0=Monday, 6=Sunday)
    - is_holiday_season: Binary flag for Ramadan/Natal period

    Args:
        df: DataFrame with at minimum columns: date, commodity, price

    Returns:
        DataFrame with additional feature columns
    """
    df = df.copy()
    df = df.sort_values(['commodity', 'date']).reset_index(drop=True)

    # Determine group columns (include daerah if present for per-region features)
    group_cols = ['commodity']
    if 'daerah' in df.columns:
        group_cols.append('daerah')

    # Lag features
    for lag_days in [1, 7, 30]:
        col_name = f'price_lag_{lag_days}d'
        df[col_name] = df.groupby(group_cols)['price'].shift(lag_days)

    # Rolling statistics
    for window in [7]:
        df[f'rolling_mean_{window}d'] = (
            df.groupby(group_cols)['price']
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
        )
        df[f'rolling_std_{window}d'] = (
            df.groupby(group_cols)['price']
            .transform(lambda x: x.rolling(window, min_periods=1).std())
        )

    # Momentum: 7-day percentage change
    df['price_momentum_7d'] = (
        df.groupby(group_cols)['price']
        .transform(lambda x: x.pct_change(periods=7) * 100)
    )

    # Calendar features
    df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday

    # Holiday season flag (approximate Ramadan + Natal/Tahun Baru)
    # Ramadan shifts each year, using approximate months
    ramadan_periods = {
        2021: (4, 5),   # Apr-May
        2022: (4, 5),   # Apr-May
        2023: (3, 4),   # Mar-Apr
        2024: (3, 4),   # Mar-Apr
        2025: (2, 3),   # Feb-Mar
        2026: (2, 3),   # Feb-Mar
    }

    def is_holiday(row):
        year = row['date'].year
        month = row['date'].month
        # Natal/Tahun Baru season
        if month in (11, 12, 1):
            return 1
        # Ramadan season (approximate)
        ramadan = ramadan_periods.get(year, (3, 4))
        if ramadan[0] <= month <= ramadan[1]:
            return 1
        return 0

    df['is_holiday_season'] = df.apply(is_holiday, axis=1)

    logger.info("Added %d features to DataFrame", 8)  # lag×3 + rolling×2 + momentum + dow + holiday
    return df
