"""
ARM Dashboard Data Orchestrator
=================================
Prepares dashboard/dashboard_data.json for the ARM web dashboard.
This is a slim orchestrator that delegates all logic to modules:
    config.py   → Constants & mappings
    etl.py      → Data loading & aggregation
    anomaly.py  → Z-Score anomaly detection
    forecast.py → Prophet time series forecasting

Author: Aulia (ML & Azure)

Run from project root:
    python -m scripts.prepare_dashboard_data
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd

from scripts.config import (
    ALL_REGIONS,
    ALL_SOURCES,
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    CATEGORY_MAP,
    CV_HIGH,
    CHANGE_HIGH,
    DASHBOARD_DIR,
    FORECAST_DAYS,
    SHORT_NAMES,
    setup_logging,
)
from scripts.etl import load_all_data, aggregate_prices
from scripts.anomaly import detect_anomalies, detect_future_spikes

setup_logging()
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# SECTION BUILDERS — Each function builds one section of the JSON
# ══════════════════════════════════════════════════════════════════════

def build_timeseries(df_prov, commodities):
    """Build weekly timeseries data for chart rendering."""
    timeseries = {}
    for commodity in commodities:
        cdf = df_prov[df_prov['commodity'] == commodity].sort_values('date')
        weekly = cdf.set_index('date')['price'].resample('W').mean().dropna()
        timeseries[commodity] = {
            'dates': [d.strftime('%Y-%m-%d') for d in weekly.index],
            'prices': [round(p, 0) for p in weekly.values],
            'category': CATEGORY_MAP[commodity],
            'shortName': SHORT_NAMES[commodity],
        }
    return timeseries


def build_timeseries_daily_recent(df_prov, commodities, latest_date, days=90):
    """Build daily timeseries for the most recent N days."""
    recent_start = latest_date - pd.Timedelta(days=days)
    result = {}
    for commodity in commodities:
        cdf = df_prov[
            (df_prov['commodity'] == commodity) &
            (df_prov['date'] >= recent_start)
        ].sort_values('date')
        result[commodity] = {
            'dates': [d.strftime('%Y-%m-%d') for d in cdf['date']],
            'prices': [round(p, 0) for p in cdf['price']],
        }
    return result


def build_commodity_cards(df_prov, commodities, anomalies, latest_date):
    """Build status cards for each commodity."""
    years = sorted(df_prov['year'].unique())
    latest_year = max(years)
    earliest_year = min(years)
    
    yearly_mean = df_prov.groupby(['year', 'commodity'])['price'].mean().unstack(level=0)
    
    # Total change: latest year vs earliest year
    if latest_year in yearly_mean.columns and earliest_year in yearly_mean.columns:
        total_change = (
            (yearly_mean[latest_year] - yearly_mean[earliest_year]) /
            yearly_mean[earliest_year] * 100
        )
    else:
        total_change = pd.Series(0, index=commodities)
    
    # CV for most recent year
    cv_latest = df_prov[df_prov['year'] == latest_year].groupby('commodity')['price'].agg(
        lambda x: x.std() / x.mean() * 100 if x.mean() > 0 else 0
    )
    
    # CV for year 2025 (specifically for frontend compatibility)
    cv_2025 = df_prov[df_prov['year'] == 2025].groupby('commodity')['price'].agg(
        lambda x: x.std() / x.mean() * 100 if x.mean() > 0 else 0
    )
    
    # Latest and previous month prices
    latest_prices = (
        df_prov[df_prov['date'] == df_prov['date'].max()]
        .drop_duplicates(subset='commodity')
        .set_index('commodity')['price']
    )
    prev_month_start = latest_date - pd.Timedelta(days=30)
    prev_month_avg = df_prov[
        (df_prov['date'] >= prev_month_start) & (df_prov['date'] <= latest_date)
    ].groupby('commodity')['price'].mean()
    
    recent_start_str = (latest_date - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
    
    cards = []
    for commodity in commodities:
        cv = cv_latest.get(commodity, 0)
        cv25 = cv_2025.get(commodity, 0)
        change = total_change.get(commodity, 0)
        price = latest_prices.get(commodity, 0)
        prev_avg = prev_month_avg.get(commodity, price)
        month_change = ((price - prev_avg) / prev_avg * 100) if prev_avg else 0
        
        # Status logic (BPS/TPID thresholds)
        if cv > CV_HIGH or abs(change) > CHANGE_HIGH:
            status = 'critical'
        elif cv > 5 or abs(change) > 10:
            status = 'warning'
        else:
            status = 'normal'
        
        recent_anomaly_count = len([
            a for a in anomalies
            if a['commodity'] == commodity and a['date'] >= recent_start_str
        ])
        
        cards.append({
            'commodity': commodity,
            'shortName': SHORT_NAMES[commodity],
            'category': CATEGORY_MAP[commodity],
            'icon': CATEGORY_ICONS.get(CATEGORY_MAP[commodity], '📦'),
            'latestPrice': round(float(price), 0),
            'monthChange': round(float(month_change), 1),
            'totalChange': round(float(change), 1),
            'cvLatest': round(float(cv), 1),
            'cv2025': round(float(cv25), 1),  # added for backward compatibility with frontend hardcoded key
            'status': status,
            'recentAnomalies': recent_anomaly_count,
        })
    
    return cards, latest_prices.to_dict()


def build_yoy_data(df_prov, commodities):
    """Build Year-over-Year comparison data."""
    years = sorted(df_prov['year'].unique())
    yearly_mean = df_prov.groupby(['year', 'commodity'])['price'].mean().unstack(level=0)
    
    yoy_data = []
    for commodity in commodities:
        entry = {
            'commodity': commodity,
            'shortName': SHORT_NAMES[commodity],
            'category': CATEGORY_MAP[commodity],
        }
        # Compute YoY changes for consecutive years
        for i in range(1, len(years)):
            prev_year, curr_year = years[i-1], years[i]
            key = f'change_{prev_year}_{curr_year}'
            if prev_year in yearly_mean.columns and curr_year in yearly_mean.columns:
                prev_val = yearly_mean.loc[commodity, prev_year] if commodity in yearly_mean.index else 0
                curr_val = yearly_mean.loc[commodity, curr_year] if commodity in yearly_mean.index else 0
                val = round((curr_val - prev_val) / prev_val * 100, 1) if prev_val else 0
                entry[key] = val
                
                # Also generate 2-digit key for backward compatibility with dashboard app.js
                prev_short = str(prev_year)[-2:]
                curr_short = str(curr_year)[-2:]
                compat_key = f'change_{prev_short}_{curr_short}'
                entry[compat_key] = val
            else:
                entry[key] = 0
                prev_short = str(prev_year)[-2:]
                curr_short = str(curr_year)[-2:]
                entry[f'change_{prev_short}_{curr_short}'] = 0
        
        # Total change
        if years[0] in yearly_mean.columns and years[-1] in yearly_mean.columns:
            first_val = yearly_mean.loc[commodity, years[0]] if commodity in yearly_mean.index else 0
            last_val = yearly_mean.loc[commodity, years[-1]] if commodity in yearly_mean.index else 0
            entry['total_change'] = round((last_val - first_val) / first_val * 100, 1) if first_val else 0
        else:
            entry['total_change'] = 0
        
        yoy_data.append(entry)
    
    yoy_data.sort(key=lambda x: x['total_change'], reverse=True)
    return yoy_data


def build_seasonality(df_prov, commodities):
    """Build monthly seasonality Z-scores."""
    monthly_pivot = df_prov.groupby(['commodity', 'month'])['price'].mean().unstack()
    monthly_normalized = monthly_pivot.apply(lambda x: (x - x.mean()) / x.std(), axis=1)
    
    result = {}
    for commodity in commodities:
        if commodity in monthly_normalized.index:
            row = monthly_normalized.loc[commodity]
            result[commodity] = {
                'shortName': SHORT_NAMES[commodity],
                'values': [round(v, 2) if not pd.isna(v) else 0 for v in row.values],
            }
    return result


def build_volatility(df_prov, commodities):
    """Build CV (volatility) data per year."""
    years = sorted(df_prov['year'].unique())
    cv_all = df_prov.groupby(['year', 'commodity'])['price'].agg(
        lambda x: x.std() / x.mean() * 100 if x.mean() > 0 else 0
    ).unstack(level=0).round(1)
    
    result = {}
    for commodity in commodities:
        if commodity in cv_all.index:
            entry = {
                'shortName': SHORT_NAMES[commodity],
                'category': CATEGORY_MAP[commodity],
            }
            for y in years:
                entry[str(y)] = round(float(cv_all.loc[commodity, y]), 1) if y in cv_all.columns else 0
            result[commodity] = entry
    return result


def build_correlation(df_prov, commodities):
    """Build price correlation matrix."""
    price_wide = df_prov.pivot_table(index='date', columns='commodity', values='price')
    corr = price_wide.corr().round(2)
    return {
        'commodities': [SHORT_NAMES.get(c, c) for c in corr.columns],
        'matrix': corr.values.tolist(),
    }


def build_category_monthly(df_prov):
    """Build monthly category average prices for stacked area chart."""
    cat_monthly = df_prov.groupby(
        [df_prov['date'].dt.to_period('M'), 'category']
    )['price'].mean().unstack()
    cat_monthly.index = cat_monthly.index.to_timestamp()
    
    result = {
        'dates': [d.strftime('%Y-%m-%d') for d in cat_monthly.index],
        'categories': {},
    }
    for cat in cat_monthly.columns:
        result['categories'][cat] = [
            round(v, 0) if not pd.isna(v) else 0 for v in cat_monthly[cat].values
        ]
    return result


def build_regional_data(df, commodities):
    """
    Build regional price data for Tier 2 dashboard.
    Returns per-region timeseries for each commodity.
    """
    df_reg = aggregate_prices(df, by='region')
    
    regional = {}
    for commodity in commodities:
        regional[commodity] = {}
        for region in ALL_REGIONS:
            cdf = df_reg[
                (df_reg['commodity'] == commodity) &
                (df_reg['daerah'] == region)
            ].sort_values('date')
            
            if cdf.empty:
                continue
            
            prices = cdf['price'].values
            regional[commodity][region] = {
                'dates': [d.strftime('%Y-%m-%d') for d in cdf['date']],
                'prices': [round(float(p), 0) for p in prices],
                'latestPrice': round(float(prices[-1]), 0) if len(prices) > 0 else 0,
                'ma30': round(float(cdf['price'].rolling(30, min_periods=1).mean().iloc[-1]), 0),
                'cv': round(float(cdf['price'].std() / cdf['price'].mean() * 100), 1) if cdf['price'].mean() > 0 else 0,
            }
    
    return regional


def build_price_by_source(df, commodities):
    """
    Build price-by-source data for margin analysis (Tier 2B).
    Shows latest price per source type for each commodity.
    """
    df_src = aggregate_prices(df, by='source')
    latest_date = df_src['date'].max()
    recent = df_src[df_src['date'] >= latest_date - pd.Timedelta(days=7)]
    
    result = {}
    for commodity in commodities:
        result[commodity] = {}
        for source in ALL_SOURCES:
            cdf = recent[
                (recent['commodity'] == commodity) &
                (recent['sumber'] == source)
            ]
            if not cdf.empty:
                result[commodity][source] = {
                    'latestPrice': round(float(cdf['price'].mean()), 0),
                }
    return result


def build_alert_feed(anomalies, future_spikes):
    """Build combined alert feed (predictions first, then historical anomalies)."""
    alert_feed = []
    
    # Historical anomaly alerts (top 50 most recent)
    for a in anomalies[:50]:
        if a['severity'] == 'critical':
            action = 'Segera lakukan operasi pasar / inspeksi rantai pasok'
        else:
            action = 'Monitor harga harian, siapkan rencana intervensi'
        alert_feed.append({**a, 'action': action})
    
    # Future spike predictions go first
    future_spikes.sort(key=lambda x: x.get('date', ''))
    return future_spikes + alert_feed


def generate_executive_summary(anomalies, future_spikes, kpi):
    """Generate data-driven executive summary (replaces Azure OpenAI)."""
    critical_items = [a for a in anomalies[:20] if a['severity'] == 'critical']
    
    # Get unique critical commodities with worst deviation
    critical_details = {}
    for a in critical_items[:10]:
        name = SHORT_NAMES.get(a['commodity'], a['commodity'])
        if name not in critical_details or abs(a['deviation_pct']) > abs(critical_details[name]['deviation_pct']):
            critical_details[name] = a
    
    critical_desc_parts = []
    for name, a in list(critical_details.items())[:3]:
        critical_desc_parts.append(
            f"{name} (lonjakan {a['deviation_pct']:+.1f}% pada {a['date']}, "
            f"harga Rp {a['price']:,.0f} vs rata-rata Rp {a['ma30']:,.0f})"
        )
    critical_desc = "; ".join(critical_desc_parts) if critical_desc_parts else "tidak ada"
    
    # Prediction section
    pred_section = ""
    if future_spikes:
        pred_details = []
        for a in future_spikes[:3]:
            pred_details.append(
                f"{a['shortName']} (diprediksi naik {a['spike_pct']:+.1f}% "
                f"menjadi Rp {a['price']:,.0f} dari harga saat ini Rp {a['current_price']:,.0f})"
            )
        pred_desc = "; ".join(pred_details)
        pred_section = (
            f"\n\n📈 PREDIKSI 90 HARI KE DEPAN: Model machine learning Prophet mendeteksi "
            f"potensi lonjakan signifikan pada {len(future_spikes)} komoditas, terutama: {pred_desc}. "
            f"Kenaikan ini mengindikasikan tekanan inflasi struktural yang perlu diantisipasi "
            f"melalui mekanisme stabilisasi harga preventif."
        )
    
    rec_section = (
        f"\n\n💡 REKOMENDASI STRATEGIS: (1) Prioritaskan operasi pasar untuk komoditas berstatus KRITIS, "
        f"khususnya kelompok hortikultura yang memiliki volatilitas tertinggi; "
        f"(2) Koordinasi dengan Dinas Perindustrian dan Perdagangan Provinsi Aceh untuk "
        f"memastikan kelancaran rantai distribusi dari produsen ke pasar tradisional; "
        f"(3) Aktifkan mekanisme cadangan pangan daerah (buffer stock) untuk komoditas "
        f"yang diprediksi mengalami lonjakan dalam 90 hari ke depan."
    )
    
    return (
        f"🔍 RINGKASAN EKSEKUTIF — Sistem Aceh Resilience Monitor telah menganalisis "
        f"{kpi['totalDataPoints']:,} titik data harga harian dari "
        f"{kpi['totalCommodities']} komoditas pangan strategis "
        f"(periode {kpi['dataStartDate']} s/d {kpi['dataEndDate']}). "
        f"Dalam 90 hari terakhir, terdeteksi {kpi['recentAnomalies']} kejadian "
        f"anomali harga yang melampaui ambang batas statistik (>2σ dari rata-rata bergerak 30 hari). "
        f"Saat ini terdapat {kpi['criticalAlerts']} komoditas berstatus KRITIS dan "
        f"{kpi['warningAlerts']} komoditas berstatus WASPADA."
        f"\n\n⚠️ KOMODITAS KRITIS: {critical_desc}."
        f"{pred_section}"
        f"{rec_section}"
    )


# ══════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════

def main():
    """Main pipeline orchestrator."""
    t_start = time.time()
    
    # ── 1. Load data ──
    logger.info("Loading data from dataup JSON...")
    df = load_all_data()
    df_prov = aggregate_prices(df, by='province')
    
    commodities = sorted(df_prov['commodity'].unique())
    latest_date = df_prov['date'].max()
    logger.info("Loaded %d records, %d commodities, latest: %s",
                len(df), len(commodities), latest_date.strftime('%Y-%m-%d'))
    
    # ── 2. Timeseries ──
    logger.info("Building timeseries data...")
    timeseries = build_timeseries(df_prov, commodities)
    ts_daily_recent = build_timeseries_daily_recent(df_prov, commodities, latest_date)
    
    # ── 3. Anomaly detection (regional level - kabupaten/kota) ──
    logger.info("Detecting anomalies...")
    df_region = aggregate_prices(df, by='region')
    anomalies = detect_anomalies(df_region, commodities, group_by='daerah')
    
    # Enrich anomalies with shortName and category for frontend compatibility
    for a in anomalies:
        comm = a['commodity']
        a['shortName'] = SHORT_NAMES.get(comm, comm)
        a['category'] = CATEGORY_MAP.get(comm, 'Lainnya')
    
    # ── 4. Commodity cards ──
    logger.info("Building commodity status cards...")
    commodity_cards, latest_prices = build_commodity_cards(df_prov, commodities, anomalies, latest_date)
    
    # ── 5. Prophet forecasting (aggregated) ──
    logger.info("Generating %d-day forecasts (per-region)...", FORECAST_DAYS)
    try:
        from scripts.forecast import forecast_all_commodities
        forecasts = forecast_all_commodities(
            df, commodities, latest_date,
            periods=FORECAST_DAYS, per_region=True
        )
    except Exception as e:
        logger.error("Forecasting failed: %s", e)
        forecasts = {}
    
    # ── 6. Future spike detection ──
    logger.info("Detecting future price spikes...")
    future_spikes = detect_future_spikes(forecasts, latest_prices)
    
    # ── 7. Analytical sections ──
    logger.info("Building analytical sections...")
    yoy_data = build_yoy_data(df_prov, commodities)
    seasonality = build_seasonality(df_prov, commodities)
    volatility = build_volatility(df_prov, commodities)
    correlation = build_correlation(df_prov, commodities)
    category_monthly = build_category_monthly(df_prov)
    
    # ── 8. Regional data (Tier 2 dashboard) ──
    logger.info("Building regional comparison data...")
    regional = build_regional_data(df, commodities)
    price_by_source = build_price_by_source(df, commodities)
    
    # Also build regional forecasts dict from the per-region forecasts
    regional_forecasts = {}
    for commodity in commodities:
        if commodity in forecasts:
            regional_forecasts[commodity] = {
                k: v for k, v in forecasts[commodity].items()
                if k != 'aggregated'
            }
    
    # ── 9. KPI summary ──
    recent_start = (latest_date - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
    n_critical = len([c for c in commodity_cards if c['status'] == 'critical'])
    n_warning = len([c for c in commodity_cards if c['status'] == 'warning'])
    
    kpi = {
        'totalCommodities': len(commodities),
        'criticalAlerts': n_critical,
        'warningAlerts': n_warning,
        'avgPriceChange': round(
            float(pd.Series([c['totalChange'] for c in commodity_cards]).mean()), 1
        ),
        'dataStartDate': df_prov['date'].min().strftime('%Y-%m-%d'),
        'dataEndDate': latest_date.strftime('%Y-%m-%d'),
        'totalDataPoints': len(df),
        'recentAnomalies': len([a for a in anomalies if a['date'] >= recent_start]),
        'totalRegions': len(ALL_REGIONS),
        'totalSources': len(ALL_SOURCES),
    }
    
    # ── 10. Alert feed + Executive summary ──
    alert_feed = build_alert_feed(anomalies, future_spikes)
    ai_insight = generate_executive_summary(anomalies, future_spikes, kpi)
    
    # ── 11. Assemble & Save ──
    # Extract aggregated forecasts for backward compatibility
    forecasts_aggregated = {}
    for commodity in commodities:
        if commodity in forecasts and 'aggregated' in forecasts[commodity]:
            forecasts_aggregated[commodity] = forecasts[commodity]['aggregated']
    
    dashboard_data = {
        'kpi': kpi,
        'commodityCards': commodity_cards,
        'timeseries': timeseries,
        'timeseriesRecentDaily': ts_daily_recent,
        'anomalies': anomalies[:200],
        'alertFeed': alert_feed,
        'yoyData': yoy_data,
        'seasonality': seasonality,
        'volatility': volatility,
        'correlation': correlation,
        'categoryMonthly': category_monthly,
        'forecasts': forecasts_aggregated,
        'categories': list(sorted(set(CATEGORY_MAP.values()))),
        'categoryIcons': CATEGORY_ICONS,
        'categoryColors': CATEGORY_COLORS,
        'aiInsight': ai_insight,
        # New multi-dimensional data (Tier 2)
        'regional': regional,
        'priceBySource': price_by_source,
        'regionalForecasts': regional_forecasts,
        'regions': ALL_REGIONS,
        'priceSources': ALL_SOURCES,
    }
    
    # Write JSON
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    output_path = DASHBOARD_DIR / 'dashboard_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=None)
    
    # Also generate embedded JS version (for file:// CORS compatibility)
    output_js_path = DASHBOARD_DIR / 'dashboard_data.js'
    with open(output_js_path, 'w', encoding='utf-8') as f:
        f.write('const DASHBOARD_DATA = ')
        json.dump(dashboard_data, f, ensure_ascii=False, indent=None)
        f.write(';')
    
    elapsed = time.time() - t_start
    file_size = os.path.getsize(output_path) / 1024
    
    logger.info("═" * 60)
    logger.info("✅ Dashboard data saved to %s (%.0f KB)", output_path, file_size)
    logger.info("   Also generated: %s", output_js_path)
    logger.info("   Commodities: %d | Regions: %d | Sources: %d",
                len(commodities), len(ALL_REGIONS), len(ALL_SOURCES))
    logger.info("   Anomalies: %d | Forecasts: %d | Alerts: %d",
                len(anomalies), len(forecasts_aggregated), len(alert_feed))
    logger.info("   Pipeline completed in %.1fs", elapsed)
    logger.info("═" * 60)


if __name__ == '__main__':
    main()
