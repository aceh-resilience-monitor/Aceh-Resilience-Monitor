"""
Tests for scripts/scraper.py — Scraper and API parsing validation.

Author: Arief (Test, Docs & Comms)
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from scripts.scraper import (
    generate_key,
    process_api_data,
    fetch_data_from_api,
    scrape_daily_pihps
)

class TestScraperUnit:
    """Validate core scraper components and data processing."""

    def test_generate_key(self):
        item = {
            "tanggal": "2026-06-02",
            "name": "Beras Kualitas Bawah I",
            "daerah": "Banda Aceh",
            "sumber": "Pasar Tradisional"
        }
        assert generate_key(item) == "2026-06-02|Beras Kualitas Bawah I|Banda Aceh|Pasar Tradisional"

    def test_process_api_data_success(self):
        api_data = [
            {
                "no": "1",
                "name": "Beras",
                "level": 1,
                "02/06/2026": "-"
            },
            {
                "no": "2",
                "name": "Beras Kualitas Bawah I",
                "level": 2,
                "02/06/2026": "13,600"
            }
        ]
        
        processed = process_api_data(api_data, "2026-06-02", regency_id=1, price_type_id=1)
        
        assert len(processed) == 2
        
        # Test level 1 item
        level1 = processed[0]
        assert level1["level"] == 1
        assert level1["komoditas"] == "Beras"
        assert level1["harga"] is None
        assert level1["daerah"] == "Banda Aceh"
        assert level1["sumber"] == "Pasar Tradisional"
        
        # Test level 2 item
        level2 = processed[1]
        assert level2["level"] == 2
        assert level2["name"] == "Beras Kualitas Bawah I"
        assert level2["komoditas"] == "Beras"  # inherited from level 1
        assert level2["harga"] == "13,600"
        assert level2["daerah"] == "Banda Aceh"
        assert level2["sumber"] == "Pasar Tradisional"
        assert "02/06/2026" not in level2  # Cleaned key

    def test_process_api_data_empty(self):
        assert process_api_data([], "2026-06-02", 1, 1) == []
        assert process_api_data(None, "2026-06-02", 1, 1) == []

    @patch("scripts.scraper.requests.get")
    def test_fetch_data_from_api_network_failure(self, mock_get):
        mock_get.side_effect = Exception("Connection Timeout")
        
        # Should return empty after attempts
        res = fetch_data_from_api("2026-06-02", 1, 1, retries=2)
        assert res == []
        assert mock_get.call_count == 2


class TestScraperOrchestration:
    """Validate lookback logic and deduplication flow."""

    @patch("scripts.scraper.time.sleep")
    @patch("scripts.scraper.fetch_data_from_api")
    def test_scrape_daily_pihps_today_has_data(self, mock_fetch, mock_sleep):
        # Setup mock fetch to return mock API data for 2026-06-02
        # There are 3 dates in lookback window * 3 regions * 4 sources = 36 total calls to fetch_data_from_api
        mock_api_data = [
            {"no": "2", "name": "Beras Kualitas Bawah I", "level": 2, "02/06/2026": "13,600"}
        ]
        mock_fetch.return_value = mock_api_data
        
        # Run scraping with empty existing list
        new_records = scrape_daily_pihps([], run_date="2026-06-02")
        
        # Should have fetched and returned elements (36 processed elements)
        assert len(new_records) == 36
        assert mock_fetch.call_count == 36
        
        # Verify overwrite logic: existing records of successfully scraped dates are removed in-place
        existing_records = [{"tanggal": "2026-06-02", "name": "Old Rice", "level": 2}]
        with patch("scripts.scraper.fetch_data_from_api") as mock_fetch_again:
            mock_fetch_again.return_value = mock_api_data
            new_records_again = scrape_daily_pihps(existing_records, run_date="2026-06-02")
            assert len(new_records_again) == 36
            # Date '2026-06-02' was successfully scraped, so existing list should have been cleared of it
            assert len(existing_records) == 0

    @patch("scripts.scraper.time.sleep")
    @patch("scripts.scraper.fetch_data_from_api")
    def test_scrape_daily_pihps_lookback_trigger(self, mock_fetch, mock_sleep):
        # Let's say today (2026-06-02) has no data
        # Let's mock: today returns [], yesterday (2026-06-01) returns data, day before (2026-05-31) returns []
        def side_effect(date_str, regency_id, price_type_id):
            if date_str == "2026-06-01":
                return [{"no": "2", "name": "Beras Kualitas Bawah I", "level": 2, "01/06/2026": "13,600"}]
            return []
            
        mock_fetch.side_effect = side_effect
        
        new_records = scrape_daily_pihps([], run_date="2026-06-02")
        
        # In python implementation, lookback always checks 3 days:
        # Today (2026-06-02) -> 12 calls
        # Yesterday (2026-06-01) -> 12 calls
        # Day before (2026-05-31) -> 12 calls
        # Total = 36 calls
        assert mock_fetch.call_count == 36
        # And we should have 12 records from 2026-06-01
        assert len(new_records) == 12
        assert all(r["tanggal"] == "2026-06-01" for r in new_records)

