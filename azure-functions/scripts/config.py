"""
ARM Configuration — Single Source of Truth
============================================
All constants, mappings, paths, and thresholds used across the ARM project.
Every other module imports from here. No duplication allowed.

Usage:
    from scripts.config import CATEGORY_MAP, SHORT_NAMES, setup_logging
"""

import logging
from pathlib import Path
from typing import Dict, List

# ══════════════════════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════════════════════

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / 'data'                    # Historical Excel files
DATAUP_DIR: Path = PROJECT_ROOT / 'dataup' / 'data'       # Scraped JSON (production)
DASHBOARD_DIR: Path = PROJECT_ROOT / 'dashboard'
PLOT_DIR: Path = PROJECT_ROOT / 'plots'

DATA_YEARS: List[int] = [2023, 2024, 2025]

# ══════════════════════════════════════════════════════════════════════
# COMMODITY MAPPINGS — 21 sub-commodities → 10 categories
# ══════════════════════════════════════════════════════════════════════

CATEGORY_MAP: Dict[str, str] = {
    # Beras (6 variants)
    'Beras Kualitas Bawah I': 'Beras',
    'Beras Kualitas Bawah II': 'Beras',
    'Beras Kualitas Medium I': 'Beras',
    'Beras Kualitas Medium II': 'Beras',
    'Beras Kualitas Super I': 'Beras',
    'Beras Kualitas Super II': 'Beras',
    # Protein hewani
    'Daging Ayam Ras Segar': 'Daging Ayam',
    'Daging Sapi Kualitas 1': 'Daging Sapi',
    'Daging Sapi Kualitas 2': 'Daging Sapi',       # NEW — dari dataup
    'Telur Ayam Ras Segar': 'Telur Ayam',
    # Bumbu dapur
    'Bawang Merah Ukuran Sedang': 'Bawang Merah',
    'Bawang Putih Ukuran Sedang': 'Bawang Putih',
    'Cabai Merah Keriting': 'Cabai Merah',
    'Cabai Merah Besar': 'Cabai Merah',             # NEW — dari dataup
    'Cabai Rawit Hijau': 'Cabai Rawit',
    'Cabai Rawit Merah': 'Cabai Rawit',             # NEW — dari dataup
    # Minyak & gula
    'Minyak Goreng Curah': 'Minyak Goreng',
    'Minyak Goreng Kemasan Bermerk 1': 'Minyak Goreng',
    'Minyak Goreng Kemasan Bermerk 2': 'Minyak Goreng',
    'Gula Pasir Kualitas Premium': 'Gula Pasir',
    'Gula Pasir Lokal': 'Gula Pasir',
}

SHORT_NAMES: Dict[str, str] = {
    'Beras Kualitas Bawah I': 'Beras Bawah I',
    'Beras Kualitas Bawah II': 'Beras Bawah II',
    'Beras Kualitas Medium I': 'Beras Medium I',
    'Beras Kualitas Medium II': 'Beras Medium II',
    'Beras Kualitas Super I': 'Beras Super I',
    'Beras Kualitas Super II': 'Beras Super II',
    'Daging Ayam Ras Segar': 'Daging Ayam',
    'Daging Sapi Kualitas 1': 'Daging Sapi 1',
    'Daging Sapi Kualitas 2': 'Daging Sapi 2',     # NEW
    'Telur Ayam Ras Segar': 'Telur Ayam',
    'Bawang Merah Ukuran Sedang': 'Bawang Merah',
    'Bawang Putih Ukuran Sedang': 'Bawang Putih',
    'Cabai Merah Keriting': 'Cabai Keriting',
    'Cabai Merah Besar': 'Cabai Besar',             # NEW
    'Cabai Rawit Hijau': 'Cabai Rawit Hijau',
    'Cabai Rawit Merah': 'Cabai Rawit Merah',       # NEW
    'Minyak Goreng Curah': 'M. Goreng Curah',
    'Minyak Goreng Kemasan Bermerk 1': 'M. Goreng Merk 1',
    'Minyak Goreng Kemasan Bermerk 2': 'M. Goreng Merk 2',
    'Gula Pasir Kualitas Premium': 'Gula Premium',
    'Gula Pasir Lokal': 'Gula Lokal',
}

CATEGORY_ICONS: Dict[str, str] = {
    'Beras': '🍚',
    'Daging Ayam': '🍗',
    'Daging Sapi': '🥩',
    'Telur Ayam': '🥚',
    'Bawang Merah': '🧅',
    'Bawang Putih': '🧄',
    'Cabai Merah': '🌶️',
    'Cabai Rawit': '🫑',
    'Minyak Goreng': '🫗',
    'Gula Pasir': '🍬',
}

CATEGORY_COLORS: Dict[str, str] = {
    'Beras': '#4E79A7',
    'Daging Ayam': '#F28E2B',
    'Daging Sapi': '#E15759',
    'Telur Ayam': '#76B7B2',
    'Bawang Merah': '#59A14F',
    'Bawang Putih': '#EDC948',
    'Cabai Merah': '#B07AA1',
    'Cabai Rawit': '#FF9DA7',
    'Minyak Goreng': '#9C755F',
    'Gula Pasir': '#BAB0AC',
}

# ══════════════════════════════════════════════════════════════════════
# REGIONAL & SOURCE MAPPINGS — Multi-dimensional data from dataup
# ══════════════════════════════════════════════════════════════════════

REGIONS: Dict[int, str] = {
    1: 'Banda Aceh',
    2: 'Lhokseumawe',
    3: 'Meulaboh',
}

PRICE_SOURCES: Dict[int, str] = {
    1: 'Pasar Tradisional',
    2: 'Pasar Modern',
    3: 'Pedagang Besar',
    4: 'Produsen',
}

ALL_REGIONS: List[str] = list(REGIONS.values())
ALL_SOURCES: List[str] = list(PRICE_SOURCES.values())

# ══════════════════════════════════════════════════════════════════════
# ANOMALY & FORECASTING THRESHOLDS
# ══════════════════════════════════════════════════════════════════════

ZSCORE_THRESHOLD: float = 2.0       # |z| > 2 → warning
ZSCORE_CRITICAL: float = 3.0        # |z| > 3 → critical
CV_HIGH: float = 15.0               # CV > 15% → volatile (standar BPS)
CHANGE_HIGH: float = 20.0           # Price change > 20% → significant (standar TPID)
SPIKE_THRESHOLD_PCT: float = 15.0   # Predicted spike > 15% → alert
MA_WINDOW_DAYS: int = 30            # Moving average window
FORECAST_DAYS: int = 90             # Prophet forecast horizon

# ══════════════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure structured logging for the ARM pipeline.
    Logs are printed to the console AND saved to a physical file (logs/pipeline.log).
    Also suppresses noisy external library warnings (Pandas, Prophet, Stan).
    """
    import warnings
    # Suppress noisy Pandas ChainedAssignment and Copy-on-Write warnings
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', message='.*ChainedAssignmentError.*')
    warnings.filterwarnings('ignore', message='.*returning-a-view-versus-a-copy.*')
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to prevent duplicate log outputs
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. Console stream handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Ensure logs directory exists and setup file logging if possible
    try:
        logs_dir = PROJECT_ROOT / 'logs'
        logs_dir.mkdir(exist_ok=True)
        log_file = logs_dir / 'pipeline.log'
        
        # Physical file handler (persistent audit trail)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file writing/directory creation fails
        print(f"Warning: Could not set up file logging (Read-only environment): {e}")
        
    # Silence noisy libraries
    logging.getLogger('prophet').setLevel(logging.ERROR)
    logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
