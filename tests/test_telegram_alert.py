"""
Tests for scripts/telegram_alert.py — Telegram Notification validation.
"""

import pytest
from unittest.mock import patch, MagicMock
from scripts.telegram_alert import (
    _get_action,
    _get_icon,
    _get_severity_badge,
    format_daily_report,
    send_telegram_message,
    send_daily_alert
)

class TestTelegramAlertUnit:
    """Validate helper functions inside telegram_alert.py."""

    def test_get_action_specific(self):
        # Cabai Merah should return specific actions
        assert "operasi pasar" in _get_action("Cabai Merah Keriting", "critical")
        assert "distribusi alternatif" in _get_action("Cabai Merah Keriting", "warning")
        
        # Beras BULOG action
        assert "BULOG" in _get_action("Beras Kualitas Medium I", "critical")

    def test_get_action_default(self):
        # Unknown commodity should fall back to default
        assert "Satgas Pangan" in _get_action("Unknown Commodity", "critical")

    def test_get_icon(self):
        assert _get_icon("Beras Kualitas Bawah I") == "🍚"
        assert _get_icon("Daging Sapi Kualitas 1") == "🥩"
        assert _get_icon("Unknown Commodity") == "📦"

    def test_get_severity_badge(self):
        assert "KRITIS" in _get_severity_badge("critical")
        assert "WASPADA" in _get_severity_badge("warning")
        assert "INFO" in _get_severity_badge("info")


class TestTelegramMessageFormatting:
    """Validate structure and formatting of daily report."""

    def test_format_daily_report_empty(self):
        report = format_daily_report(anomalies=[], spikes=[], date_str="02 June 2026")
        
        assert "📢 ACEH RESILIENCE MONITOR (ARM)" in report
        assert "Tanggal: 02 June 2026" in report
        assert "Tidak ada anomali harga hari ini" in report
        assert "Tidak ada prediksi lonjakan harga" in report
        assert "Powered by Prophet" in report

    def test_format_daily_report_with_data(self):
        anomalies = [
            {
                "commodity": "Cabai Merah Keriting",
                "price": 85000.0,
                "severity": "critical",
                "z_score": 3.4,
                "deviation_pct": 28.5,
                "daerah": "Banda Aceh"
            }
        ]
        
        spikes = [
            {
                "commodity": "Bawang Merah Ukuran Sedang",
                "current_price": 40000.0,
                "price": 62000.0,
                "spike_pct": 55.0,
                "icon": "🧅",
                "shortName": "Bawang Merah",
                "daerah": "Lhokseumawe"
            }
        ]
        
        report = format_daily_report(anomalies, spikes, date_str="02 June 2026")
        
        assert "ANOMALI HARGA HARI INI" in report
        assert "Cabai Keriting (Banda Aceh)" in report
        assert "Z-Score: 3.4σ" in report
        assert "Kenaikan +55.0%" in report
        assert "🧅 Bawang Merah (Lhokseumawe)" in report


class TestTelegramSending:
    """Validate Telegram Bot API integration and credential handling."""

    @patch("scripts.telegram_alert.os.environ.get")
    def test_send_telegram_message_no_credentials(self, mock_env):
        mock_env.return_value = ""
        # Should return False and print fallback message
        res = send_telegram_message("Hello Test", token=None, chat_id=None)
        assert res is False

    @patch("scripts.telegram_alert.requests.post")
    def test_send_telegram_message_success(self, mock_post):
        # Mock status 200 response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        res = send_telegram_message("Hello Test", token="123:ABC", chat_id="456")
        
        assert res is True
        mock_post.assert_called_once()
        
    @patch("scripts.telegram_alert.requests.post")
    def test_send_telegram_message_failure(self, mock_post):
        # Mock status 400 response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        res = send_telegram_message("Hello Test", token="123:ABC", chat_id="456")
        
        assert res is False
