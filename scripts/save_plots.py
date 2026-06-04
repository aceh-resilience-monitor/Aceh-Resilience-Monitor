"""
ARM Plot Generator
====================
Generate and save all EDA plots from the commodity price dataset.
Imports constants from config and data loading from etl — zero duplication.

Author: Aulia (ML & Azure)

Run from project root:
    python -m scripts.save_plots
"""

import logging
import os
import warnings

import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from scripts.config import (
    CATEGORY_COLORS,
    CATEGORY_MAP,
    PLOT_DIR,
    setup_logging,
)
from scripts.etl import load_all_data, aggregate_prices

warnings.filterwarnings('ignore')

setup_logging()
logger = logging.getLogger(__name__)

# ── Plot styling ──
os.makedirs(PLOT_DIR, exist_ok=True)
sns.set_theme(style='whitegrid', palette='husl', font_scale=1.1)
plt.rcParams.update({
    'figure.figsize': (16, 6),
    'figure.dpi': 150,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
})

MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def main():
    """Generate all 13 EDA plots."""
    # ── Load data ──
    logger.info("Loading data...")
    df = load_all_data()
    df_clean = aggregate_prices(df, by='province')
    logger.info("Loaded %d clean records", len(df_clean))

    commodities = sorted(df_clean['commodity'].unique())
    years = sorted(df_clean['year'].unique())

    # ── PLOT 1: Box plots ──
    logger.info("Plot 1: Box plots...")
    commodities_sorted = df_clean.groupby('commodity')['price'].mean().sort_values(ascending=False).index
    fig, axes = plt.subplots(2, 1, figsize=(18, 14))
    high_price = [c for c in commodities_sorted if df_clean[df_clean['commodity'] == c]['price'].mean() >= 25000]
    low_price = [c for c in commodities_sorted if df_clean[df_clean['commodity'] == c]['price'].mean() < 25000]
    for ax, group, title in zip(axes, [high_price, low_price],
        ['High-Price Commodities (Mean >= Rp 25,000)', 'Low-Price Commodities (Mean < Rp 25,000)']):
        subset = df_clean[df_clean['commodity'].isin(group)]
        order = [c for c in commodities_sorted if c in group]
        sns.boxplot(data=subset, x='commodity', y='price', hue='year', order=order, ax=ax, palette='Set2', fliersize=2)
        ax.set_title(title, fontweight='bold', fontsize=14)
        ax.set_xlabel('')
        ax.set_ylabel('Price (Rp)')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax.tick_params(axis='x', rotation=35)
        ax.legend(title='Year', loc='upper right')
    plt.suptitle('Price Distributions by Commodity & Year', fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/01_boxplots.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 2: Violin plots ──
    logger.info("Plot 2: Violin plots...")
    volatile_commodities = ['Cabai Merah Keriting', 'Cabai Rawit Hijau',
                            'Bawang Merah Ukuran Sedang', 'Daging Ayam Ras Segar']
    volatile_available = [c for c in volatile_commodities if c in commodities]
    fig, axes = plt.subplots(1, len(volatile_available), figsize=(5 * len(volatile_available), 6), sharey=False)
    if len(volatile_available) == 1:
        axes = [axes]
    for ax, commodity in zip(axes, volatile_available):
        subset = df_clean[df_clean['commodity'] == commodity]
        sns.violinplot(data=subset, x='year', y='price', ax=ax, palette='mako', inner='box', cut=0)
        ax.set_title(commodity, fontweight='bold', fontsize=11)
        ax.set_xlabel('Year')
        ax.set_ylabel('Price (Rp)' if ax == axes[0] else '')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
    plt.suptitle('Price Distribution of Most Volatile Commodities', fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/02_violin_volatile.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 3: Time series by category ──
    logger.info("Plot 3: Time series by category...")
    categories = sorted(df_clean['category'].unique())
    n_cats = len(categories)
    fig, axes = plt.subplots(n_cats, 1, figsize=(18, 3.5 * n_cats), sharex=True)
    if n_cats == 1:
        axes = [axes]
    for ax, cat in zip(axes, categories):
        cat_df = df_clean[df_clean['category'] == cat]
        color = CATEGORY_COLORS.get(cat, '#333333')
        for commodity in cat_df['commodity'].unique():
            cdf = cat_df[cat_df['commodity'] == commodity].sort_values('date')
            ax.plot(cdf['date'], cdf['price'], label=commodity, linewidth=0.8, alpha=0.85)
        ax.set_title(f'{cat}', fontweight='bold', fontsize=13, loc='left', color=color)
        ax.set_ylabel('Price (Rp)')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax.legend(loc='upper left', fontsize=8, ncol=3)
        ax.grid(True, alpha=0.3)
        for yr in years[1:]:
            ax.axvline(pd.Timestamp(f'{yr}-01-01'), color='gray', linestyle='--', alpha=0.5)
    axes[-1].set_xlabel('Date')
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.suptitle(f'Daily Commodity Prices ({years[0]}-{years[-1]})', fontsize=18, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/03_timeseries_all.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 4: Volatile commodities + MA ──
    logger.info("Plot 4: Volatile + MA...")
    highlight = ['Cabai Merah Keriting', 'Cabai Rawit Hijau', 'Bawang Merah Ukuran Sedang']
    highlight_available = [c for c in highlight if c in commodities]
    fig, axes = plt.subplots(len(highlight_available), 1, figsize=(18, 4 * len(highlight_available)), sharex=True)
    if len(highlight_available) == 1:
        axes = [axes]
    for ax, commodity in zip(axes, highlight_available):
        cdf = df_clean[df_clean['commodity'] == commodity].sort_values('date')
        ax.fill_between(cdf['date'], cdf['price'], alpha=0.15, color='#E15759')
        ax.plot(cdf['date'], cdf['price'], linewidth=0.6, alpha=0.5, color='#E15759', label='Daily')
        ma30 = cdf.set_index('date')['price'].rolling('30D').mean()
        ax.plot(ma30.index, ma30.values, linewidth=2, color='#4E79A7', label='30-day MA')
        ax.set_title(commodity, fontweight='bold', fontsize=13)
        ax.set_ylabel('Price (Rp)')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        for yr in years[1:]:
            ax.axvline(pd.Timestamp(f'{yr}-01-01'), color='gray', linestyle='--', alpha=0.5)
    plt.suptitle('Volatile Commodities - Daily Prices with 30-Day Moving Average', fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/04_volatile_ma30.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 5: Total price change bar ──
    logger.info("Plot 5: Total price change...")
    yearly_mean = df_clean.groupby(['year', 'commodity'])['price'].mean().unstack(level=0)
    first_year, last_year = years[0], years[-1]
    total_change = ((yearly_mean[last_year] - yearly_mean[first_year]) / yearly_mean[first_year] * 100).sort_values()
    fig, ax = plt.subplots(figsize=(12, 10))
    colors = ['#E15759' if v > 20 else '#F28E2B' if v > 10 else '#59A14F' if v >= 0 else '#4E79A7' for v in total_change.values]
    bars = ax.barh(range(len(total_change)), total_change.values, color=colors, edgecolor='white', height=0.7)
    ax.set_yticks(range(len(total_change)))
    ax.set_yticklabels(total_change.index)
    for bar, val in zip(bars, total_change.values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2, f'{val:+.1f}%', va='center', fontsize=10, fontweight='bold')
    ax.set_xlabel('Total Price Change (%)', fontsize=12)
    ax.set_title(f'Total Price Change {first_year} to {last_year} by Commodity', fontsize=15, fontweight='bold')
    ax.axvline(0, color='black', linewidth=0.8)
    ax.axvline(20, color='red', linewidth=0.8, linestyle='--', alpha=0.5, label='> 20% threshold')
    ax.legend()
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/05_total_change_bar.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 6: YoY grouped bar ──
    logger.info("Plot 6: YoY grouped bar...")
    if len(years) >= 3:
        # Use last 3 years for YoY comparison
        y1, y2, y3 = years[-3], years[-2], years[-1]
        change_y1y2 = ((yearly_mean[y2] - yearly_mean[y1]) / yearly_mean[y1] * 100)
        change_y2y3 = ((yearly_mean[y3] - yearly_mean[y2]) / yearly_mean[y2] * 100)
        commodities_order = total_change.sort_values(ascending=False).index
        x = np.arange(len(commodities_order))
        width = 0.35
        fig, ax = plt.subplots(figsize=(16, 8))
        ax.bar(x - width/2, change_y1y2[commodities_order], width, label=f'{y1}-{y2}', color='#4E79A7', alpha=0.85)
        ax.bar(x + width/2, change_y2y3[commodities_order], width, label=f'{y2}-{y3}', color='#E15759', alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels(commodities_order, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Price Change (%)')
        ax.set_title('Year-over-Year Price Changes by Commodity', fontsize=15, fontweight='bold')
        ax.axhline(0, color='black', linewidth=0.8)
        ax.legend(fontsize=12)
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{PLOT_DIR}/06_yoy_comparison.png', bbox_inches='tight')
        plt.close()

    # ── PLOT 7: CV heatmap ──
    logger.info("Plot 7: CV heatmap...")
    cv_for_heatmap = df_clean.groupby(['year', 'commodity'])['price'].agg(
        lambda x: x.std() / x.mean() * 100 if x.mean() > 0 else 0
    ).unstack(level=0).round(2)
    cv_for_heatmap = cv_for_heatmap.loc[cv_for_heatmap.mean(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(10, 12))
    sns.heatmap(cv_for_heatmap, annot=True, fmt='.1f', cmap='YlOrRd', linewidths=0.5, ax=ax,
                cbar_kws={'label': 'CV (%)'})
    ax.set_title('Price Volatility (CV %) by Commodity & Year', fontsize=14, fontweight='bold')
    ax.set_xlabel('Year')
    ax.set_ylabel('')
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/07_cv_heatmap.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 8: Correlation heatmap ──
    logger.info("Plot 8: Correlation heatmap...")
    price_wide = df_clean.pivot_table(index='date', columns='commodity', values='price')
    price_wide.columns.name = None
    price_wide_sorted = price_wide.sort_index()
    returns_wide = price_wide_sorted.pct_change()
    corr = returns_wide.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    fig, ax = plt.subplots(figsize=(16, 14))
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r', center=0, vmin=-1, vmax=1,
                linewidths=0.5, ax=ax, annot_kws={'size': 8}, cbar_kws={'label': 'Pearson Correlation (Daily Returns)'})
    ax.set_title(f'Daily Returns Correlation Matrix ({years[0]}-{years[-1]})', fontsize=15, fontweight='bold')
    ax.tick_params(axis='both', labelsize=9)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/08_correlation_matrix.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 9: Monthly seasonality ──
    logger.info("Plot 9: Monthly seasonality...")
    monthly_avg = df_clean.groupby(['month', 'commodity'])['price'].mean().reset_index()
    seasonal_commodities = ['Cabai Merah Keriting', 'Cabai Rawit Hijau', 'Bawang Merah Ukuran Sedang',
                            'Daging Ayam Ras Segar', 'Telur Ayam Ras Segar', 'Bawang Putih Ukuran Sedang']
    seasonal_available = [c for c in seasonal_commodities if c in commodities]
    n_plots = min(len(seasonal_available), 6)
    ncols = 3
    nrows = (n_plots + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 5 * nrows))
    axes_flat = axes.flat if hasattr(axes, 'flat') else [axes]
    for i, (ax, commodity) in enumerate(zip(axes_flat, seasonal_available)):
        for year in years[-3:]:  # Last 3 years
            yr_data = df_clean[(df_clean['commodity'] == commodity) & (df_clean['year'] == year)]
            monthly = yr_data.groupby('month')['price'].mean()
            ax.plot(monthly.index, monthly.values, marker='o', markersize=4, label=str(year), linewidth=1.5)
        overall = monthly_avg[monthly_avg['commodity'] == commodity]
        ax.plot(overall['month'], overall['price'], '--', color='black', alpha=0.5, linewidth=2, label='Overall Avg')
        ax.set_title(commodity, fontweight='bold', fontsize=11)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(MONTH_LABELS, fontsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}K'))
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
    # Hide extra axes
    for j in range(i + 1, len(list(axes_flat))):
        axes_flat[j].set_visible(False)
    plt.suptitle('Monthly Seasonality Patterns by Commodity', fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/09_seasonality.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 10: Monthly Z-score heatmap ──
    logger.info("Plot 10: Z-score heatmap...")
    monthly_pivot = df_clean.groupby(['commodity', 'month'])['price'].mean().unstack()
    monthly_normalized = monthly_pivot.apply(lambda x: (x - x.mean()) / x.std(), axis=1)
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(monthly_normalized, annot=True, fmt='.2f', cmap='RdYlGn_r', center=0, linewidths=0.5, ax=ax,
                xticklabels=MONTH_LABELS, cbar_kws={'label': 'Z-Score (higher = more expensive)'})
    ax.set_title('Monthly Price Seasonality Heatmap (Z-Score Normalized)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Month')
    ax.set_ylabel('')
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/10_zscore_heatmap.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 11: Daily returns distribution ──
    logger.info("Plot 11: Daily returns distribution...")
    price_wide_sorted = price_wide.sort_index()
    daily_returns = price_wide_sorted.pct_change() * 100
    returns_stats = daily_returns.describe().T[['mean', 'std', 'min', 'max']].round(3)
    returns_stats.columns = ['Mean Return (%)', 'Std Return (%)', 'Max Drop (%)', 'Max Gain (%)']
    returns_stats = returns_stats.sort_values('Std Return (%)', ascending=False)
    top_volatile = returns_stats.head(6).index.tolist()
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for ax, commodity in zip(axes.flat, top_volatile):
        data = daily_returns[commodity].dropna()
        ax.hist(data, bins=50, color='#4E79A7', alpha=0.7, edgecolor='white', density=True)
        kde_x = np.linspace(data.min(), data.max(), 200)
        kde = stats.gaussian_kde(data)
        ax.plot(kde_x, kde(kde_x), color='#E15759', linewidth=2)
        ax.axvline(0, color='black', linestyle='--', alpha=0.5)
        ax.set_title(commodity, fontweight='bold', fontsize=11)
        ax.set_xlabel('Daily Return (%)')
        ax.set_ylabel('Density' if ax in axes[:, 0] else '')
        mu, sigma = data.mean(), data.std()
        ax.text(0.95, 0.95, f'mu={mu:.3f}%\nsigma={sigma:.2f}%', transform=ax.transAxes, va='top', ha='right',
                fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    plt.suptitle('Distribution of Daily Price Changes - Most Volatile Commodities', fontsize=15, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/11_daily_returns.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 12: Category bar chart ──
    logger.info("Plot 12: Category bar chart...")
    cat_yearly = df_clean.groupby(['year', 'category'])['price'].mean().unstack(level=0).round(0)
    fig, ax = plt.subplots(figsize=(14, 8))
    cat_order = cat_yearly.mean(axis=1).sort_values(ascending=True).index
    x = np.arange(len(cat_order))
    width = 0.25
    plot_years = years[-3:]  # Last 3 years
    for i, year in enumerate(plot_years):
        if year in cat_yearly.columns:
            values = cat_yearly.loc[cat_order, year]
            ax.barh(x + i * width, values, width, label=str(year), alpha=0.85)
    ax.set_yticks(x + width)
    ax.set_yticklabels(cat_order)
    ax.set_xlabel('Average Price (Rp)')
    ax.set_title('Average Price by Category & Year', fontsize=15, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.legend(title='Year')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/12_category_prices.png', bbox_inches='tight')
    plt.close()

    # ── PLOT 13: Stacked area chart ──
    logger.info("Plot 13: Stacked area chart...")
    cat_monthly = df_clean.groupby([df_clean['date'].dt.to_period('M'), 'category'])['price'].mean().unstack()
    cat_monthly.index = cat_monthly.index.to_timestamp()
    fig, ax = plt.subplots(figsize=(18, 8))
    cols_to_plot = [c for c in cat_monthly.columns if c != 'Daging Sapi']
    colors_list = [CATEGORY_COLORS.get(c, '#333') for c in cols_to_plot]
    ax.stackplot(cat_monthly.index, [cat_monthly[c] for c in cols_to_plot], labels=cols_to_plot,
                 colors=colors_list, alpha=0.8)
    ax.set_title('Monthly Average Prices by Category (Stacked, excl. Daging Sapi)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Combined Price (Rp)')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.legend(loc='upper left', fontsize=9, ncol=3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.grid(True, alpha=0.3)
    for yr in years[1:]:
        ax.axvline(pd.Timestamp(f'{yr}-01-01'), color='gray', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/13_stacked_area.png', bbox_inches='tight')
    plt.close()

    logger.info("✅ All 13 plots saved to %s/", PLOT_DIR)


if __name__ == '__main__':
    main()
