# Aceh Resilience Monitor (ARM) — Interactive Dashboard

## Goal

Build the **Aceh Resilience Monitor (ARM)** — a web-based executive dashboard prototype as described in the project brief. This serves as the front-end demo for the datathon, showcasing the end-to-end BI platform for detecting food price anomalies.

## Background

The project brief describes ARM as a platform that:
1. Policymakers open a dashboard showing a map with market indicators (Green/Yellow/Red)
2. Click on "Red" markets to see which commodity triggers the warning
3. View projection charts and anomalies
4. Export reports for market intervention planning
5. Automated alerts when daily price changes are drastic

### Existing Work (✅ Complete)
- Raw data: 3 Excel files (2023-2025)
- 13 EDA plots with interpretations
- Data analysis document
- Microsoft Fabric architecture recommendation

### What We're Building
A stunning interactive web dashboard that brings the ARM concept to life.

---

## Proposed Changes

### Data Processing Layer

#### [NEW] [prepare_dashboard_data.py](file:///Users/ilhaamghiffari/Documents/Personal/Programming/datathon-dicoding/prepare_dashboard_data.py)

Python script to transform the Excel data into JSON format for the dashboard:
- Reuse the existing `load_and_clean()` function from `save_plots.py`
- Generate `dashboard_data.json` containing:
  - Daily prices per commodity (time series)
  - Monthly aggregates with anomaly flags
  - Volatility metrics (CV%) per commodity per year
  - YoY price changes
  - Seasonality Z-scores
  - Latest prices with status indicators (Green/Yellow/Red) based on statistical thresholds
  - Anomaly detection results (prices beyond 2σ from 30-day moving average)

---

### Dashboard Application

#### [NEW] [dashboard/index.html](file:///Users/ilhaamghiffari/Documents/Personal/Programming/datathon-dicoding/dashboard/index.html)

Single-page application with the following sections:

**1. Hero / Overview Panel**
- ARM logo & branding with dark theme
- KPI cards: Total commodities monitored, Current alerts count, Average price change YoY, Data timespan
- Date range indicator

**2. Market Status Overview**
- Visual grid of all 18 commodities with color-coded status indicators:
  - 🟢 Green: CV < 5% and price change < 10%
  - 🟡 Yellow: CV 5-15% or price change 10-20%
  - 🔴 Red: CV > 15% or price change > 20%
- Click on a commodity card to drill-down

**3. Price Trend Charts (Interactive)**
- Multi-line chart with all commodities (filterable by category)
- 30-day moving average overlay
- Anomaly markers on the chart (spikes beyond 2σ)

**4. Anomaly Detection Panel**
- Table/cards showing detected anomalies with:
  - Commodity name, date, price, deviation from MA30
  - Severity level (Warning/Critical)
  - Recommendation for intervention

**5. Seasonality Analysis**
- Heatmap showing Z-score normalized monthly prices
- Interactive month selector

**6. YoY Comparison**
- Grouped bar chart showing 2023→2024 vs 2024→2025 changes
- Highlight commodities with >20% increase

**7. Alert Feed / Early Warning**
- Simulated real-time feed of price alerts
- Alert cards with commodity, price change %, and recommended action

#### [NEW] [dashboard/style.css](file:///Users/ilhaamghiffari/Documents/Personal/Programming/datathon-dicoding/dashboard/style.css)

Premium dark-theme design with:
- Dark navy/charcoal background
- Glassmorphism cards
- Gradient accents (teal → blue → purple)
- Smooth animations and transitions
- Responsive grid layout
- Inter/Outfit typography from Google Fonts

#### [NEW] [dashboard/app.js](file:///Users/ilhaamghiffari/Documents/Personal/Programming/datathon-dicoding/dashboard/app.js)

JavaScript logic using Chart.js for:
- Loading and parsing `dashboard_data.json`
- Rendering interactive charts
- Category/commodity filtering
- Drill-down interactions
- Anomaly highlighting
- Alert simulation

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Layout & Structure | HTML5 semantic elements |
| Styling | Vanilla CSS (dark theme, glassmorphism) |
| Charts | Chart.js (via CDN) |
| Typography | Google Fonts (Inter) |
| Data | Pre-processed JSON from Python |
| Icons | Lucide Icons (via CDN) |

> [!IMPORTANT]
> We're NOT using a framework. This is a static HTML/CSS/JS dashboard that loads pre-processed JSON data. This makes it easy to demo, deploy, and present at the datathon.

---

## Verification Plan

### Automated Tests
- Run `prepare_dashboard_data.py` and verify JSON output structure
- Open `dashboard/index.html` in browser and verify all visualizations render

### Manual Verification
- Check all 7 dashboard sections render correctly
- Verify color-coded status indicators match the EDA findings
- Confirm anomaly detection flags match known anomalies (e.g., Cabai Merah Keriting Q4 2025 spike)
- Test responsive layout at different screen sizes
