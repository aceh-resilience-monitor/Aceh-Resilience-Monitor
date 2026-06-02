"""
ARM Scraper — Daily PIHPS Data Scraping in Python
==================================================
Scrapes daily commodity price data from the Bank Indonesia hargapangan API.
Ports the Node.js scraping logic from dataup/helper.js and dataup/daily_update.js.

Author: AI Agent
"""

import sys
import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Ensure project root is in sys.path when running script directly
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from scripts.config import REGIONS, PRICE_SOURCES

logger = logging.getLogger(__name__)

def generate_key(item: dict) -> str:
    """Generate a unique composite key for deduplication."""
    return f"{item.get('tanggal')}|{item.get('name')}|{item.get('daerah')}|{item.get('sumber')}"

def fetch_data_from_api(date_str: str, regency_id: int, price_type_id: int, retries: int = 3) -> List[dict]:
    """
    Fetch raw JSON data from BI hargapangan endpoint with automatic retries.
    """
    url = "https://www.bi.go.id/hargapangan/WebSite/TabelHarga/GetGridDataDaerah"
    params = {
        'price_type_id': price_type_id,
        'comcat_id': '',
        'province_id': 1,  # Default to Aceh (1)
        'regency_id': regency_id,
        'market_id': '',
        'tipe_laporan': 1,
        'start_date': date_str,
        'end_date': date_str
    }
    
    for attempt in range(1, retries + 1):
        try:
            logger.debug("Attempt %d/%d: GET %s with params %s", attempt, retries, url, params)
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            if res_json and isinstance(res_json, dict) and 'data' in res_json:
                return res_json['data']
            return []
        except Exception as e:
            if attempt == retries:
                logger.error("API Request failed for %s - Regency: %d, PriceType: %d after %d attempts. Error: %s",
                             date_str, regency_id, price_type_id, retries, e)
                return []
            else:
                logger.warning("Network error on %s (Regency: %d, PriceType: %d) - %s. Retrying... (%d/%d)",
                               date_str, regency_id, price_type_id, e, attempt, retries)
                time.sleep(2)
    return []

def process_api_data(api_data: List[dict], date_str: str, regency_id: int, price_type_id: int) -> List[dict]:
    """
    Process raw API data to assign parent categories (komoditas),
    clean up dynamic date keys, and map region and price source names.
    """
    if not api_data:
        return []
        
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        date_key = dt.strftime("%d/%m/%Y")  # API uses DD/MM/YYYY for the price field key
    except Exception as e:
        logger.error("Failed to parse date %s: %s", date_str, e)
        return []
        
    results = []
    current_category = ""
    
    for item in api_data:
        # Identify level 1 parent to assign parent categories to sub-commodities
        level = item.get('level')
        try:
            level_val = int(level) if level is not None else 0
        except ValueError:
            level_val = 0
            
        if level_val == 1:
            current_category = item.get('name', '').strip()
            
        harga = item.get(date_key)
        if harga == '-' or harga is None:
            harga = None
            
        cleaned_item = item.copy()
        if date_key in cleaned_item:
            del cleaned_item[date_key]
            
        daerah = REGIONS.get(regency_id, f"Unknown ({regency_id})")
        sumber = PRICE_SOURCES.get(price_type_id, f"Unknown ({price_type_id})")
        
        # Build standard output record matching historical schema
        processed_item = {
            "no": cleaned_item.get("no", ""),
            "name": cleaned_item.get("name", "").strip(),
            "level": level_val,
            "tanggal": date_str,
            "komoditas": current_category if current_category else cleaned_item.get("name", "").strip(),
            "harga": harga,
            "daerah": daerah,
            "sumber": sumber
        }
        results.append(processed_item)
        
    return results

def process_date(date_str: str, existing_keys: set) -> List[dict]:
    """
    Fetch, process, and deduplicate data for a single date across all regions and sources.
    """
    daily_data = []
    has_data = False
    
    logger.info("Fetching PIHPS data for date: %s", date_str)
    
    for regency_id in sorted(REGIONS.keys()):
        for price_type_id in sorted(PRICE_SOURCES.keys()):
            api_data = fetch_data_from_api(date_str, regency_id, price_type_id)
            
            if api_data:
                processed = process_api_data(api_data, date_str, regency_id, price_type_id)
                daily_data.extend(processed)
                has_data = True
                
            # Sleep to respect API rate limits
            time.sleep(0.5)
            
    if has_data and daily_data:
        new_entries = []
        for item in daily_data:
            key = generate_key(item)
            if key not in existing_keys:
                existing_keys.add(key)
                new_entries.append(item)
        return new_entries
    else:
        logger.info("No data found from API for date: %s", date_str)
        return []

def scrape_daily_pihps(existing_records: List[dict], run_date: Optional[str] = None) -> List[dict]:
    """
    Main orchestrator for daily scraping.
    If run_date is None, defaults to today.
    If today's data is empty, looks back 7 days to fetch missing updates.
    """
    logger.info("Starting PIHPS daily scraper orchestrator...")
    
    if run_date:
        try:
            today_dt = datetime.strptime(run_date, "%Y-%m-%d")
        except ValueError:
            logger.error("Invalid run_date format %s. Using today instead.", run_date)
            today_dt = datetime.now()
    else:
        today_dt = datetime.now()
        
    today_str = today_dt.strftime("%Y-%m-%d")
    
    # Create O(1) lookup set for existing records
    existing_keys = set()
    for item in existing_records:
        existing_keys.add(generate_key(item))
        
    logger.info("Initialized deduplicator with %d existing keys.", len(existing_keys))
    
    # 1. Fetch today's data
    today_new_entries = process_date(today_str, existing_keys)
    
    total_new_entries = []
    
    # 2. If no data today, run lookback check for the last 7 days
    if not today_new_entries:
        logger.info("No new records found for today (%s). Running 7-day lookback pipeline...", today_str)
        for i in range(1, 8):
            past_dt = today_dt - timedelta(days=i)
            past_date_str = past_dt.strftime("%Y-%m-%d")
            past_entries = process_date(past_date_str, existing_keys)
            if past_entries:
                logger.info("Found %d new records on past date: %s", len(past_entries), past_date_str)
                total_new_entries.extend(past_entries)
    else:
        logger.info("Found %d new records for today (%s).", len(today_new_entries), today_str)
        total_new_entries.extend(today_new_entries)
        
    if total_new_entries:
        logger.info("Successfully fetched %d new total records from PIHPS.", len(total_new_entries))
    else:
        logger.info("No new records found. System is already up to date.")
        
    return total_new_entries

if __name__ == "__main__":
    # Self-test when run directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Running standalone scraper test...")
    # Mock some existing records
    mock_existing = [
        {
            "tanggal": "2026-06-01",
            "komoditas": "Beras",
            "daerah": "Banda Aceh",
            "sumber": "Pasar Tradisional"
        }
    ]
    # Scrape yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    new_records = scrape_daily_pihps(mock_existing, run_date=yesterday)
    logger.info("Scraped test completed. New records found: %d", len(new_records))
