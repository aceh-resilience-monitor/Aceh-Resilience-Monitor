"""
ARM Telegram Alert Module — Daily EWS Notification System
==========================================================
Sends automated daily reports to TPID Aceh (Tim Pengendali Inflasi Daerah)
via Telegram Bot API with two alert types:

1. Z-Score Anomaly (Reactive): Today's unusual price movements
2. Prophet Spike/EWS (Proactive): 90-day predicted price surges

Key functions:
    format_daily_report()     — Format full daily report message
    send_telegram_message()   — Send via Bot API (or console fallback)
    send_daily_alert()        — Orchestrator: format + send

Author: Arief (Test, Docs & Comms) — G7, G15

Usage:
    from scripts.telegram_alert import send_daily_alert
    send_daily_alert(anomalies, spikes, date_str='2026-05-30')
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests

from scripts.config import (
    CATEGORY_ICONS,
    CATEGORY_MAP,
    SHORT_NAMES,
)

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# COMMODITY-SPECIFIC ACTION RECOMMENDATIONS (G7)
# Author: Arief (Test, Docs & Comms)
# ══════════════════════════════════════════════════════════════════════
# Rekomendasi aksi SPESIFIK per kategori komoditas (menutup Gap G7:
# "Rekomendasi terlalu generic"). Setiap kategori mendapat aksi yang
# relevan dengan rantai pasoknya masing-masing.
# ══════════════════════════════════════════════════════════════════════

COMMODITY_ACTIONS: Dict[str, Dict[str, str]] = {
    'Cabai Merah': {
        'critical': "Segera lakukan operasi pasar & inspeksi rantai pasok cabai di pasar utama.",
        'warning': "Monitor intensif stok cabai 3 hari ke depan. Siapkan jalur distribusi alternatif.",
        'prediction': "Koordinasi dengan Dinas Pertanian untuk memastikan pasokan cabai dari petani lokal.",
    },
    'Cabai Rawit': {
        'critical': "Segera inspeksi gudang pedagang besar cabai rawit. Waspadai penimbunan.",
        'warning': "Pantau pasokan cabai rawit dari sentra produksi. Siapkan stok cadangan.",
        'prediction': "Dinas Perdagangan siapkan operasi pasar cabai rawit preventif.",
    },
    'Bawang Merah': {
        'critical': "Segera lakukan operasi pasar bawang merah & cek distribusi dari Brebes/Sumatera Utara.",
        'warning': "Monitor stok bawang merah di gudang pedagang besar.",
        'prediction': "Siapkan jalur impor/antar-pulau bawang merah sebagai cadangan.",
    },
    'Bawang Putih': {
        'critical': "Cek stok bawang putih impor di distributor utama. Segera koordinasi BULOG.",
        'warning': "Monitor harga bawang putih impor dan stok gudang.",
        'prediction': "Pastikan kelancaran jalur impor bawang putih via Belawan/Sabang.",
    },
    'Beras': {
        'critical': "Segera lepas cadangan pangan (buffer stock) beras dari gudang BULOG daerah.",
        'warning': "Monitor stok beras di gudang BULOG. Siapkan distribusi rastra.",
        'prediction': "Dinas Perdagangan koordinasi BULOG untuk penyaluran beras bersubsidi.",
    },
    'Daging Sapi': {
        'critical': "Koordinasi RPH (Rumah Potong Hewan) & importir daging. Cek pasokan sapi hidup.",
        'warning': "Monitor pasokan daging sapi dari RPH. Waspadai menjelang Meugang/Lebaran.",
        'prediction': "Siapkan operasi pasar daging sapi menjelang hari raya. Koordinasi BULOG.",
    },
    'Daging Ayam': {
        'critical': "Inspeksi distribusi ayam ras dari peternakan ke pasar. Cek harga di tingkat peternak.",
        'warning': "Monitor harga ayam di tingkat peternak vs pasar. Waspadai margin tidak wajar.",
        'prediction': "Koordinasi dengan asosiasi peternak ayam untuk stabilitas pasokan.",
    },
    'Telur Ayam': {
        'critical': "Koordinasi distribusi telur dari sentra peternakan. Cek stok gudang distributor.",
        'warning': "Monitor harga telur di tingkat peternak. Pastikan distribusi lancar.",
        'prediction': "Siapkan jalur distribusi alternatif telur dari provinsi tetangga.",
    },
    'Minyak Goreng': {
        'critical': "Cek stok minyak goreng di gudang distributor utama. Segera operasi pasar.",
        'warning': "Monitor ketersediaan minyak goreng curah & bermerk di pasar.",
        'prediction': "Pastikan program Minyakita tersedia cukup di pasar tradisional.",
    },
    'Gula Pasir': {
        'critical': "Cek stok gula di PTPN & distributor. Koordinasi BULOG untuk pasokan darurat.",
        'warning': "Monitor harga gula pasir. Waspadai menjelang Ramadan/Lebaran.",
        'prediction': "Koordinasi PTPN & importir untuk stabilitas pasokan gula pasir.",
    },
}

# Default action jika kategori tidak ditemukan
DEFAULT_ACTIONS = {
    'critical': "Segera lakukan investigasi rantai pasok. Koordinasi Satgas Pangan daerah.",
    'warning': "Monitor intensif 3 hari ke depan. Siapkan rencana mitigasi.",
    'prediction': "Pantau perkembangan harga & siapkan rencana aksi preventif.",
}


def _get_action(commodity: str, severity: str) -> str:
    """
    Get commodity-specific action recommendation based on severity.

    Author: Arief (Test, Docs & Comms) — G7 Specific Recommendations
    """
    category = CATEGORY_MAP.get(commodity, '')
    actions = COMMODITY_ACTIONS.get(category, DEFAULT_ACTIONS)
    return actions.get(severity, DEFAULT_ACTIONS.get(severity, ''))


def _get_icon(commodity: str) -> str:
    """Get emoji icon for a commodity category."""
    category = CATEGORY_MAP.get(commodity, '')
    return CATEGORY_ICONS.get(category, '📦')


def _get_severity_badge(severity: str, z_score: float = 0) -> str:
    """Get severity badge text."""
    if severity == 'critical' or abs(z_score) > 3:
        return "KRITIS 🔴"
    elif severity == 'warning' or abs(z_score) > 2:
        return "WASPADA 🟡"
    return "INFO 🔵"


# ══════════════════════════════════════════════════════════════════════
# MESSAGE FORMATTING
# Author: Arief (Test, Docs & Comms)
# ══════════════════════════════════════════════════════════════════════

def format_zscore_section(anomalies: List[dict], max_items: int = 5) -> str:
    """
    Format Z-Score anomalies into Telegram message section.

    Only includes anomalies from the most recent date. Shows max_items
    sorted by severity (critical first, then by |z_score| descending).

    Author: Arief (Test, Docs & Comms) — G15 Telegram Alert
    """
    # Filter out province-wide anomalies (we only want per-region/kabupaten/kota or market-type)
    filtered_anomalies = [
        a for a in anomalies
        if a.get('daerah') and a.get('daerah') != 'Provinsi Aceh'
    ]

    if not filtered_anomalies:
        return "✅ Tidak ada anomali harga hari ini. Semua komoditas dalam kondisi stabil.\n"

    # Sort: critical first, then by |z_score| descending
    sorted_anomalies = sorted(
        filtered_anomalies,
        key=lambda x: (0 if x.get('severity') == 'critical' else 1, -abs(x.get('z_score', 0)))
    )

    lines = []
    for a in sorted_anomalies[:max_items]:
        icon = _get_icon(a['commodity'])
        short_name = SHORT_NAMES.get(a['commodity'], a['commodity'])
        badge = _get_severity_badge(a.get('severity', 'warning'), a.get('z_score', 0))
        daerah = a.get('daerah', 'Provinsi Aceh')
        action = _get_action(a['commodity'], a.get('severity', 'warning'))

        lines.append(
            f"{icon} {short_name} ({daerah})\n"
            f"• Harga: Rp {a['price']:,.0f} / kg\n"
            f"• Status: {badge} (Z-Score: {abs(a['z_score']):.1f}σ | "
            f"{a['deviation_pct']:+.1f}% dari MA30)\n"
            f"• ⚡ Aksi: {action}\n"
        )

    return '\n'.join(lines)


def format_ews_section(spikes: List[dict], max_items: int = 5) -> str:
    """
    Format Prophet EWS (Early Warning System) predictions into Telegram section.

    Author: Arief (Test, Docs & Comms) — G15 Telegram Alert
    """
    # Filter out province-wide spikes (we only want per-region/kabupaten/kota or market-type)
    filtered_spikes = [
        s for s in spikes
        if s.get('daerah') and s.get('daerah') != 'Provinsi Aceh'
    ]

    if not filtered_spikes:
        return "✅ Tidak ada prediksi lonjakan harga dalam 90 hari ke depan.\n"

    lines = []
    for s in filtered_spikes[:max_items]:
        icon = s.get('icon', '📦')
        short_name = s.get('shortName', s['commodity'])
        daerah = s.get('daerah', 'Provinsi Aceh')
        severity_emoji = "🔴" if s['spike_pct'] >= 50 else "🟡"
        action = _get_action(s['commodity'], 'prediction')

        lines.append(
            f"{icon} {short_name} ({daerah})\n"
            f"• Harga Saat Ini: Rp {s['current_price']:,.0f} / kg\n"
            f"• Prediksi Puncak: Rp {s['price']:,.0f} / kg "
            f"(Kenaikan {s['spike_pct']:+.1f}% {severity_emoji})\n"
            f"• ⚡ Aksi: {action}\n"
        )

    return '\n'.join(lines)


def format_daily_report(
    anomalies: List[dict],
    spikes: List[dict],
    date_str: Optional[str] = None,
    dashboard_url: str = "https://thankful-river-084494910.7.azurestaticapps.net",
) -> str:
    """
    Format complete daily report message for Telegram.

    Combines Z-Score anomaly alerts (reactive) and Prophet EWS predictions
    (proactive) into a single premium-formatted message.

    Args:
        anomalies: List of anomaly dicts from detect_anomalies()
        spikes: List of spike dicts from detect_future_spikes()
        date_str: Date string for the report header (default: today)
        dashboard_url: URL to the ARM dashboard

    Returns:
        Formatted Telegram message string (Markdown-compatible)

    Author: Arief (Test, Docs & Comms) — G7, G15
    """
    if date_str is None:
        date_str = datetime.now().strftime('%d %B %Y')

    # ── Header ──
    header = (
        f"📢 ACEH RESILIENCE MONITOR (ARM) — LAPORAN HARIAN 📢\n"
        f"Tanggal: {date_str}\n"
    )

    # ── Section 1: Z-Score Anomalies (Reactive) ──
    section1 = (
        f"\n⚠️ 1. ANOMALI HARGA HARI INI (Reaktif - Z-Score)\n"
        f"{'─' * 40}\n"
        f"{format_zscore_section(anomalies)}"
    )

    # ── Section 2: Prophet EWS (Proactive) ──
    section2 = (
        f"\n🔮 2. PERINGATAN DINI 90 HARI (Proaktif - Prophet EWS)\n"
        f"{'─' * 40}\n"
        f"{format_ews_section(spikes)}"
    )

    # ── Footer ──
    footer = (
        f"\n{'─' * 40}\n"
        f"🔗 Dashboard ARM: {dashboard_url}\n"
        f"🤖 Powered by Prophet + Azure ML + MLflow"
    )

    return f"{header}{section1}{section2}{footer}"


# ══════════════════════════════════════════════════════════════════════
# TELEGRAM BOT API
# Author: Arief (Test, Docs & Comms)
# ══════════════════════════════════════════════════════════════════════

def send_telegram_message(
    message: str,
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """
    Send a message via Telegram Bot API.

    Falls back to console output if token/chat_id are not configured.
    Reads from environment variables if not provided as arguments.

    Args:
        message: The message text to send
        token: Telegram Bot token (default: env TELEGRAM_BOT_TOKEN)
        chat_id: Telegram chat ID (default: env TELEGRAM_CHAT_ID)

    Returns:
        True if message sent successfully, False otherwise

    Author: Arief (Test, Docs & Comms) — G15 Telegram Bot
    """
    if token is None:
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if chat_id is None:
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

    if not token or not chat_id:
        logger.warning(
            "Telegram credentials not configured. "
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables."
        )
        logger.info("Telegram message (console fallback):\n%s", message)
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("Telegram alert sent successfully to chat %s", chat_id)
            return True
        else:
            logger.error(
                "Telegram API error %d: %s",
                response.status_code, response.text
            )
            return False
    except requests.RequestException as e:
        logger.error("Failed to send Telegram message: %s", str(e))
        return False


def send_daily_alert(
    anomalies: List[dict],
    spikes: List[dict],
    date_str: Optional[str] = None,
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> bool:
    """
    Orchestrator: format daily report and send via Telegram.

    Args:
        anomalies: List of anomaly dicts from detect_anomalies()
        spikes: List of spike dicts from detect_future_spikes()
        date_str: Date for report header (default: today)
        token: Telegram Bot token (default: env variable)
        chat_id: Telegram chat ID (default: env variable)

    Returns:
        True if sent successfully

    Author: Arief (Test, Docs & Comms) — G7, G15
    """
    report = format_daily_report(anomalies, spikes, date_str)

    # Telegram has a 4096 character limit per message
    if len(report) > 4000:
        logger.warning("Report too long (%d chars), truncating...", len(report))
        report = report[:3990] + "\n\n... (truncated)"

    return send_telegram_message(report, token=token, chat_id=chat_id)
