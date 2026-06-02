/**
 * Aceh Resilience Monitor (ARM) — Dashboard Application
 * Interactive commodity price monitoring & anomaly detection
 * 
 * Author: Ilhaam (Code & Frontend)
 */

// ── Globals ──────────────────────────────────────────────────────
let DATA = null;
let charts = {};
let selectedCommodity = null;
let activeCategory = 'all';
let showForecast = false;
let selectedRegion = 'aggregated';
let spatialCommodity = 'Cabai Merah Keriting';
let activeTab = 'tab-executive';

// ── Tab Navigation (Modul E) ─────────────────────────────────────
function switchTab(tabId) {
  activeTab = tabId;
  // Toggle tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  // Toggle tab content
  document.querySelectorAll('.tab-content').forEach(tc => {
    tc.classList.toggle('active', tc.id === tabId);
  });
  // Resize Chart.js instances to prevent "gepeng" on hidden tabs
  requestAnimationFrame(() => {
    Object.values(charts).forEach(c => {
      if (c && typeof c.resize === 'function') {
        c.resize();
      }
    });
  });
  // Lazy-render tab content on first visit
  if (tabId === 'tab-spatial' && !window._spatialRendered) {
    window._spatialRendered = true;
    renderSpatialTab();
  }
  if (tabId === 'tab-margin' && !window._marginRendered) {
    window._marginRendered = true;
    renderMarginHealthTab();
  }
  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function onSpatialCommodityChange(commodity) {
  spatialCommodity = commodity;
  renderRegionalAnalysis(commodity);
  renderRegionalChart(commodity);
}

function changeRegion(region) {
  selectedRegion = region;
  renderCommodityGrid();
  updateSVGMap();
  
  if (selectedCommodity) {
    showCommodityDetail(selectedCommodity);
  } else {
    updatePriceTrendChart();
  }

  // Re-render spatial tab if it was already rendered
  if (window._spatialRendered) {
    renderSpatialTab();
  }

  // Smooth scroll to Commodity Status Section
  const target = document.getElementById('section-status');
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ── Color Palettes ───────────────────────────────────────────────
const CATEGORY_COLORS = {
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
};

const STATUS_COLORS = {
  normal: '#22c55e',
  warning: '#f59e0b',
  critical: '#ef4444',
  prediction: '#a855f7', // Purple for forecasts
};

const MONTH_LABELS = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];

// ── Utility Functions ────────────────────────────────────────────
function formatPrice(val) {
  if (val == null) return '-';
  return 'Rp ' + Math.round(val).toLocaleString('id-ID');
}

function formatPriceShort(val) {
  if (val >= 1000) return (val / 1000).toFixed(0) + 'K';
  return val.toFixed(0);
}

function formatChange(val) {
  const sign = val > 0 ? '+' : '';
  return sign + val.toFixed(1) + '%';
}

function getChangeClass(val) {
  if (val > 5) return 'positive';
  if (val < -5) return 'negative';
  return 'neutral';
}

function delay(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ── Load Data ────────────────────────────────────────────────────
async function loadData() {
  try {
    // 1. Try fetching from Azure Blob Storage (Data Lake)
    const blobUrl = 'https://armdatalake2026.blob.core.windows.net/arm-data/dashboard_data.json';
    const resp = await fetch(blobUrl);
    if (resp.ok) {
      DATA = await resp.json();
      console.log("Data loaded successfully from Azure Blob Storage (Data Lake)!");
      return true;
    } else {
      throw new Error(`Blob fetch failed with status: ${resp.status}`);
    }
  } catch (e) {
    console.warn('Azure Blob Storage fetch failed (likely CORS not configured). Falling back to local data.', e);
    
    // 2. Fallback to embedded local data (Safe mechanism for Datathon)
    if (typeof DASHBOARD_DATA !== 'undefined') {
      DATA = DASHBOARD_DATA;
      console.log("Data loaded from local fallback.");
      return true;
    }
    return false;
  }
}

// ── Initialize App ───────────────────────────────────────────────
async function initApp() {
  const loaded = await loadData();
  if (!loaded) {
    document.getElementById('loading-text').textContent = 'Gagal memuat data!';
    return;
  }

  // Tab 1 (Executive) — render immediately
  renderKPIs();
  renderCommodityGrid();
  renderAlertFeed();
  renderAnomalyTable();
  renderSeasonalityHeatmap();
  renderVolatilityHeatmap();
  updateSVGMap();

  // Tab 4 (Forecast) — render chart instances
  renderEarlyWarning();
  renderPriceTrendChart();
  renderYoYChart();
  renderCategoryAreaChart();

  // Populate spatial commodity dropdown
  populateSpatialDropdown();

  // Update date display
  document.getElementById('data-date-range').textContent =
    `${DATA.kpi.dataStartDate} — ${DATA.kpi.dataEndDate}`;

  // Default tab
  switchTab('tab-executive');

  // Hide loading
  await delay(400);
  document.getElementById('loading-overlay').classList.add('hidden');
}

// ── Render KPIs ──────────────────────────────────────────────────
function renderKPIs() {
  const k = DATA.kpi;
  const grid = document.getElementById('kpi-grid');
  const kpis = [
    {
      label: 'Total Komoditas Dipantau',
      value: k.totalCommodities,
      color: 'teal',
      detail: '18 komoditas pangan strategis',
    },
    {
      label: 'Status Kritis',
      value: k.criticalAlerts,
      color: 'red',
      detail: 'Komoditas dengan volatilitas/kenaikan tinggi',
    },
    {
      label: 'Status Waspada',
      value: k.warningAlerts,
      color: 'yellow',
      detail: 'Komoditas perlu perhatian',
    },
    {
      label: 'Rata-rata Kenaikan (3 Thn)',
      value: formatChange(k.avgPriceChange),
      color: k.avgPriceChange > 15 ? 'red' : 'blue',
      detail: '2023 → 2025 seluruh komoditas',
    },
    {
      label: 'Anomali (90 Hari Terakhir)',
      value: k.recentAnomalies,
      color: 'purple',
      detail: 'Lonjakan harga di luar 2σ dari MA30',
    },
    {
      label: 'Total Data Point',
      value: k.totalDataPoints.toLocaleString('id-ID'),
      color: 'green',
      detail: `${k.dataStartDate} s/d ${k.dataEndDate}`,
    },
  ];

  grid.innerHTML = kpis.map(kpi => `
    <div class="kpi-card ${kpi.color}" id="kpi-${kpi.label.replace(/\s/g, '-')}">
      <div class="kpi-label">${kpi.label}</div>
      <div class="kpi-value ${kpi.color}">${kpi.value}</div>
      <div class="kpi-detail">${kpi.detail}</div>
    </div>
  `).join('');
}

// ── Early Warning System (menggunakan data prediksi Prophet nyata) ───
function renderEarlyWarning() {
  const container = document.getElementById('early-warning-grid');
  if (!container) return;

  // Ambil data PREDIKSI nyata dari alertFeed (severity === 'prediction')
  // Ini adalah output langsung dari model Meta Prophet yang meramal 90 hari ke depan
  const predictions = (DATA.alertFeed || [])
    .filter(a => a.severity === 'prediction')
    .sort((a, b) => b.spike_pct - a.spike_pct); // Urutkan dari lonjakan terbesar

  if (predictions.length === 0) {
    container.innerHTML = `<div class="glass-card" style="grid-column: 1 / -1; text-align: center; color: var(--text-muted);"><p>Tidak ada prediksi lonjakan harga saat ini.</p></div>`;
    return;
  }

  // Buat lookup icon dari commodityCards
  const iconMap = {};
  (DATA.commodityCards || []).forEach(c => {
    iconMap[c.commodity] = c.icon;
  });

  // Simpan ke window agar bisa diakses modal
  window._allPredictions = predictions;
  window._iconMap = iconMap;

  // Helper: render 1 kartu prediksi
  function buildCard(p) {
    const icon = iconMap[p.commodity] || '📦';
    const spikePct = p.spike_pct.toFixed(1);
    const currentPrice = formatPrice(p.current_price);
    const predictedPrice = formatPrice(p.price);
    const isExtreme = p.spike_pct >= 50;
    const borderColor = isExtreme ? 'var(--status-critical)' : 'var(--status-warning)';
    const bgGlow    = isExtreme ? 'rgba(239, 68, 68, 0.12)' : 'rgba(234, 179, 8, 0.08)';
    const textColor = isExtreme ? 'var(--status-critical)' : 'var(--status-warning)';
    const badge     = isExtreme ? 'EKSTREM 🔴' : 'WASPADA 🟡';
    const badgeBg   = isExtreme ? 'rgba(239,68,68,0.2)' : 'rgba(234,179,8,0.2)';
    const badgeBorder = isExtreme ? 'rgba(239,68,68,0.3)' : 'rgba(234,179,8,0.3)';
    const rec = p.action || 'Siapkan stok cadangan.';
    return `
      <div class="kpi-card" style="border-top: 4px solid ${borderColor}; position: relative; overflow: hidden; background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, ${bgGlow} 0%, transparent 100%); pointer-events: none;"></div>
        <div class="kpi-title" style="display: flex; align-items: center; justify-content: space-between; font-weight: 600;">
          <span style="font-size: 1.05rem; display: flex; align-items: center; gap: 4px;">
            <span>${icon}</span>
            <span>${p.shortName}</span>
            ${p.daerah ? `<span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal; margin-left: 2px;">[${p.daerah}]</span>` : ''}
          </span>
          <span style="font-size: 0.7rem; padding: 2px 8px; border-radius: 12px; background: ${badgeBg}; color: ${textColor}; font-weight: bold; border: 1px solid ${badgeBorder};">${badge}</span>
        </div>
        <div class="kpi-value" style="color: ${textColor}; font-size: 2rem; margin-top: 0.8rem; text-shadow: 0 0 12px ${bgGlow};">
          +${spikePct}%
          <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal; text-shadow: none; display: block; margin-top: 2px;">Prediksi Lonjakan 90 Hari (Meta Prophet)</span>
        </div>
        <div style="margin-top: 0.8rem; display: flex; gap: 8px;">
          <div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 8px; padding: 6px 10px;">
            <div style="font-size: 0.7rem; color: var(--text-muted); margin-bottom: 2px;">Harga Sekarang</div>
            <div style="font-size: 0.9rem; color: var(--text-main); font-weight: 600;">${currentPrice}</div>
          </div>
          <div style="flex: 1; background: rgba(239,68,68,0.08); border-radius: 8px; padding: 6px 10px; border: 1px solid ${badgeBorder};">
            <div style="font-size: 0.7rem; color: var(--text-muted); margin-bottom: 2px;">Prediksi Harga</div>
            <div style="font-size: 0.9rem; color: ${textColor}; font-weight: 600;">${predictedPrice}</div>
          </div>
        </div>
        <div style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.08); font-size: 0.82rem; color: #94a3b8; display: flex; align-items: flex-start; gap: 6px;">
          <span style="color: var(--status-warning); flex-shrink: 0;">⚡</span>
          <span>${rec}</span>
        </div>
      </div>
    `;
  }

  // Tampilkan Top 3 saja di kartu utama
  let html = predictions.slice(0, 3).map(buildCard).join('');

  // Jika ada >3 prediksi, tampilkan tombol "Lihat Semua"
  if (predictions.length > 3) {
    html += `
      <div style="grid-column: 1 / -1; display: flex; justify-content: center; margin-top: 0.5rem;">
        <button onclick="showAllPredictionsModal()"
          style="display: flex; align-items: center; gap: 8px; padding: 10px 24px;
                 background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15);
                 border-radius: 20px; color: var(--text-main); font-size: 0.88rem;
                 cursor: pointer; font-family: inherit; transition: background 0.2s;"
          onmouseover="this.style.background='rgba(255,255,255,0.1)'"
          onmouseout="this.style.background='rgba(255,255,255,0.05)'">
          📋 Lihat Semua Prediksi
          <span style="background: var(--status-warning); color: #000; font-weight: bold;
                       font-size: 0.75rem; padding: 1px 7px; border-radius: 10px;">${predictions.length}</span>
        </button>
      </div>
    `;
  }

  container.innerHTML = html;
}

// ── Modal: Tabel Semua Prediksi Prophet ──────────────────────────
function showAllPredictionsModal() {
  const predictions = window._allPredictions || [];
  const iconMap = window._iconMap || {};

  const rows = predictions.map((p, i) => {
    const icon = iconMap[p.commodity] || '📦';
    const isExtreme = p.spike_pct >= 50;
    const textColor = isExtreme ? '#ef4444' : '#eab308';
    const badge = isExtreme ? '🔴 EKSTREM' : '🟡 WASPADA';
    return `
      <tr style="border-bottom: 1px solid rgba(255,255,255,0.07);"
          onmouseover="this.style.background='rgba(255,255,255,0.04)'"
          onmouseout="this.style.background='transparent'">
        <td style="padding: 10px 12px; color: #94a3b8; font-size: 0.8rem;">${i + 1}</td>
        <td style="padding: 10px 12px; font-weight: 600;">
          ${icon} ${p.shortName}
          ${p.daerah ? `<span style="font-size: 0.75rem; color: var(--text-muted); font-weight: normal; margin-left: 4px;">[${p.daerah}]</span>` : ''}
        </td>
        <td style="padding: 10px 12px; color: ${textColor}; font-weight: 700; font-size: 1.05rem;">+${p.spike_pct.toFixed(1)}%</td>
        <td style="padding: 10px 12px; color: #cbd5e1;">${formatPrice(p.current_price)}</td>
        <td style="padding: 10px 12px; color: ${textColor}; font-weight: 600;">${formatPrice(p.price)}</td>
        <td style="padding: 10px 12px;">
          <span style="font-size: 0.72rem; padding: 2px 8px; border-radius: 10px;
                       background: ${isExtreme ? 'rgba(239,68,68,0.2)' : 'rgba(234,179,8,0.2)'};
                       color: ${textColor}; font-weight: bold;">${badge}</span>
        </td>
      </tr>`;
  }).join('');

  document.body.insertAdjacentHTML('beforeend', `
    <div id="predictions-modal-overlay"
         onclick="if(event.target.id==='predictions-modal-overlay') closePredictionsModal()"
         style="position: fixed; inset: 0; z-index: 9999;
                background: rgba(0,0,0,0.7); backdrop-filter: blur(6px);
                display: flex; align-items: center; justify-content: center; padding: 20px;">
      <div style="background: linear-gradient(145deg, #1e293b, #0f172a);
                  border: 1px solid rgba(255,255,255,0.12); border-radius: 16px;
                  width: 100%; max-width: 820px; max-height: 85vh;
                  display: flex; flex-direction: column; overflow: hidden;
                  box-shadow: 0 25px 60px rgba(0,0,0,0.5);">
        <div style="padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.08);
                    display: flex; align-items: center; justify-content: space-between;">
          <div>
            <h3 style="margin: 0; font-size: 1.1rem; color: #f1f5f9;">🚨 Semua Prediksi Lonjakan Harga</h3>
            <p style="margin: 4px 0 0; font-size: 0.8rem; color: #64748b;">
              Output Meta Prophet — ${predictions.length} komoditas diprediksi melonjak &gt;15% dalam 90 hari
            </p>
          </div>
          <button onclick="closePredictionsModal()"
                  style="background: rgba(255,255,255,0.08); border: none; border-radius: 8px;
                         width: 32px; height: 32px; color: #94a3b8; cursor: pointer; font-size: 1.1rem;">✕</button>
        </div>
        <div style="overflow-y: auto; padding: 12px 0;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; color: #e2e8f0;">
            <thead>
              <tr style="background: rgba(255,255,255,0.04);">
                <th style="padding: 10px 12px; text-align: left; color: #64748b; font-weight: 500;">#</th>
                <th style="padding: 10px 12px; text-align: left; color: #64748b; font-weight: 500;">Komoditas</th>
                <th style="padding: 10px 12px; text-align: left; color: #64748b; font-weight: 500;">Prediksi Naik</th>
                <th style="padding: 10px 12px; text-align: left; color: #64748b; font-weight: 500;">Harga Saat Ini</th>
                <th style="padding: 10px 12px; text-align: left; color: #64748b; font-weight: 500;">Prediksi Harga</th>
                <th style="padding: 10px 12px; text-align: left; color: #64748b; font-weight: 500;">Status</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
        <div style="padding: 14px 24px; border-top: 1px solid rgba(255,255,255,0.08);
                    font-size: 0.75rem; color: #475569; text-align: center;">
          ⚡ Prediksi oleh <strong style="color:#94a3b8;">Meta Prophet</strong> · MAPE rata-rata: <strong style="color:#94a3b8;">7.74%</strong>
        </div>
      </div>
    </div>
  `);
}

function closePredictionsModal() {
  const el = document.getElementById('predictions-modal-overlay');
  if (el) el.remove();
}


// ── Render Commodity Status Grid ─────────────────────────────────
function renderCommodityGrid() {
  const grid = document.getElementById('commodity-grid');
  let cards = DATA.commodityCards;

  // Remap cards for specific region (Tier 2 regional support)
  if (selectedRegion && selectedRegion !== 'aggregated') {
    cards = cards.map(c => {
      const regData = DATA.regional[c.commodity] ? DATA.regional[c.commodity][selectedRegion] : null;
      if (regData) {
        let status = 'normal';
        if (regData.cv > 15) status = 'critical';
        else if (regData.cv > 5) status = 'warning';
        return {
          ...c,
          latestPrice: regData.latestPrice || 0,
          cvLatest: regData.cv || 0,
          status: status,
          recentAnomalies: 0  // region specific anomalies
        };
      }
      return c;
    });
  }

  // Sort: critical first, then warning, then normal
  const order = { critical: 0, warning: 1, normal: 2 };
  const sorted = [...cards].sort((a, b) => order[a.status] - order[b.status]);

  grid.innerHTML = sorted.map(c => `
    <div class="commodity-card status-${c.status}" 
         data-commodity="${c.commodity}"
         onclick="selectCommodity('${c.commodity}')"
         id="card-${c.commodity.replace(/\s/g, '-')}">
      <div class="commodity-header">
        <span class="commodity-icon">${c.icon}</span>
        <span class="commodity-name">${c.shortName}</span>
      </div>
      <div class="commodity-price">${formatPrice(c.latestPrice)}</div>
      <div class="commodity-meta">
        <span class="commodity-change ${getChangeClass(c.totalChange)}">
          ${formatChange(c.totalChange)}
        </span>
        <span class="commodity-cv">CV ${c.cvLatest}%</span>
      </div>
      <div class="mt-1">
        <span class="status-badge ${c.status}">
          ${c.status === 'critical' ? '🔴 Kritis' : c.status === 'warning' ? '🟡 Waspada' : '🟢 Aman'}
        </span>
        ${c.recentAnomalies > 0 ? `<span class="notif-count" style="margin-left:6px">${c.recentAnomalies}</span>` : ''}
      </div>
    </div>
  `).join('');
}

// ── Select Commodity (drill-down) ────────────────────────────────
function selectCommodity(commodity) {
  // Toggle selection
  if (selectedCommodity === commodity) {
    selectedCommodity = null;
    document.querySelectorAll('.commodity-card').forEach(c => c.classList.remove('selected'));
    document.getElementById('detail-panel').classList.remove('active');
    updatePriceTrendChart();
    renderRegionalAnalysis('Cabai Merah Keriting');
    return;
  }

  selectedCommodity = commodity;

  // Highlight card
  document.querySelectorAll('.commodity-card').forEach(c => {
    c.classList.toggle('selected', c.dataset.commodity === commodity);
  });

  // Show detail panel
  showCommodityDetail(commodity);

  // Update price chart to show only this commodity
  updatePriceTrendChart(commodity);

  // Scroll to detail
  document.getElementById('detail-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showCommodityDetail(commodity) {
  const panel = document.getElementById('detail-panel');
  let card = DATA.commodityCards.find(c => c.commodity === commodity);
  
  // Remap card values for regional view
  if (selectedRegion && selectedRegion !== 'aggregated') {
    const regData = DATA.regional[commodity] ? DATA.regional[commodity][selectedRegion] : null;
    if (regData) {
      let status = 'normal';
      if (regData.cv > 15) status = 'critical';
      else if (regData.cv > 5) status = 'warning';
      card = {
        ...card,
        latestPrice: regData.latestPrice || 0,
        cvLatest: regData.cv || 0,
        status: status
      };
    }
  }

  const vol = DATA.volatility[commodity];
  const anomalies = DATA.anomalies.filter(a => a.commodity === commodity).slice(0, 15);

  // Supply Chain Price-by-Source (Tier 3 supply chain monitoring)
  const sourceData = DATA.priceBySource[commodity] || {};
  const hasSourceData = Object.keys(sourceData).length > 0;
  let supplyChainHtml = '';
  if (hasSourceData) {
    const prodPrice = sourceData['Produsen'] ? sourceData['Produsen'].latestPrice : null;
    const bigPrice = sourceData['Pedagang Besar'] ? sourceData['Pedagang Besar'].latestPrice : null;
    const tradPrice = sourceData['Pasar Tradisional'] ? sourceData['Pasar Tradisional'].latestPrice : null;
    const modPrice = sourceData['Pasar Modern'] ? sourceData['Pasar Modern'].latestPrice : null;
    
    let spreadHtml = '';
    if (prodPrice && tradPrice) {
      const spreadPct = ((tradPrice - prodPrice) / prodPrice * 100).toFixed(1);
      spreadHtml = `<span style="font-size: 11px; color: #f43f5e; font-weight: 600; background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.2); padding: 4px 10px; border-radius: 20px; display: inline-flex; align-items: center; gap: 4px;">📈 Margin Rantai Pasok: +${spreadPct}%</span>`;
    }
    
    supplyChainHtml = `
      <div style="display: flex; flex-direction: column; gap: 16px; padding: 20px; background: rgba(30, 41, 59, 0.4); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); margin-top: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <h4 style="margin: 0; display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: #f1f5f9;">
            <span style="font-size: 16px;">⛓️</span> Rantai Pasok & Disparitas Harga (Berdasarkan Sumber)
          </h4>
          ${spreadHtml}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
          
          <!-- Petani/Produsen -->
          <div style="background: ${prodPrice ? 'rgba(16, 185, 129, 0.04)' : 'rgba(255, 255, 255, 0.01)'}; border: 1px solid ${prodPrice ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)'}; border-top: 4px solid ${prodPrice ? '#10b981' : '#475569'}; border-radius: 8px; padding: 14px 12px; text-align: center; position: relative; transition: all 0.2s;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 8px;">🌾 Petani/Produsen</div>
            <div style="font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: ${prodPrice ? '#10b981' : '#64748b'};">${prodPrice ? formatPrice(prodPrice) : 'Tidak ada data'}</div>
          </div>
          
          <!-- Pedagang Besar -->
          <div style="background: ${bigPrice ? 'rgba(20, 184, 166, 0.04)' : 'rgba(255, 255, 255, 0.01)'}; border: 1px solid ${bigPrice ? 'rgba(20, 184, 166, 0.15)' : 'rgba(255, 255, 255, 0.05)'}; border-top: 4px solid ${bigPrice ? '#14b8a6' : '#475569'}; border-radius: 8px; padding: 14px 12px; text-align: center; position: relative; transition: all 0.2s;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 8px;">🏢 Pedagang Besar</div>
            <div style="font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: ${bigPrice ? '#14b8a6' : '#64748b'};">${bigPrice ? formatPrice(bigPrice) : 'Tidak ada data'}</div>
          </div>
          
          <!-- Pasar Tradisional -->
          <div style="background: ${tradPrice ? 'rgba(245, 158, 11, 0.04)' : 'rgba(255, 255, 255, 0.01)'}; border: 1px solid ${tradPrice ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255, 255, 255, 0.05)'}; border-top: 4px solid ${tradPrice ? '#f59e0b' : '#475569'}; border-radius: 8px; padding: 14px 12px; text-align: center; position: relative; transition: all 0.2s;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 8px;">🧺 Pasar Tradisional</div>
            <div style="font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: ${tradPrice ? '#f59e0b' : '#64748b'};">${tradPrice ? formatPrice(tradPrice) : 'Tidak ada data'}</div>
          </div>
          
          <!-- Pasar Modern -->
          <div style="background: ${modPrice ? 'rgba(236, 72, 153, 0.04)' : 'rgba(255, 255, 255, 0.01)'}; border: 1px solid ${modPrice ? 'rgba(236, 72, 153, 0.15)' : 'rgba(255, 255, 255, 0.05)'}; border-top: 4px solid ${modPrice ? '#ec4899' : '#475569'}; border-radius: 8px; padding: 14px 12px; text-align: center; position: relative; transition: all 0.2s;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 8px;">🛒 Pasar Modern</div>
            <div style="font-size: 16px; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: ${modPrice ? '#ec4899' : '#64748b'};">${modPrice ? formatPrice(modPrice) : 'Tidak ada data'}</div>
          </div>
          
        </div>
      </div>
    `;
  }

  panel.classList.add('active');
  panel.innerHTML = `
    <div class="glass-card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
        <div>
          <h3 style="font-size:18px;font-weight:700">${card.icon} ${commodity}</h3>
          <span class="text-muted text-sm">Kategori: ${card.category} | Status: 
            <span class="status-badge ${card.status}">${card.status === 'critical' ? '🔴 Kritis' : card.status === 'warning' ? '🟡 Waspada' : '🟢 Aman'}</span>
          </span>
        </div>
        <button class="chart-btn" onclick="selectCommodity('${commodity}')">✕ Tutup</button>
      </div>
      <div class="kpi-grid" style="grid-template-columns:repeat(4,1fr)">
        <div class="kpi-card teal">
          <div class="kpi-label">Harga Terakhir</div>
          <div class="kpi-value teal" style="font-size:20px">${formatPrice(card.latestPrice)}</div>
        </div>
        <div class="kpi-card ${card.totalChange > 20 ? 'red' : 'blue'}">
          <div class="kpi-label">Total Perubahan</div>
          <div class="kpi-value ${card.totalChange > 20 ? 'red' : 'blue'}" style="font-size:20px">${formatChange(card.totalChange)}</div>
        </div>
        <div class="kpi-card ${card.cvLatest > 15 ? 'red' : 'yellow'}">
          <div class="kpi-label">Volatilitas Terbaru (CV)</div>
          <div class="kpi-value ${card.cvLatest > 15 ? 'red' : 'yellow'}" style="font-size:20px">${card.cvLatest}%</div>
        </div>
        <div class="kpi-card purple">
          <div class="kpi-label">Anomali (90 Hari)</div>
          <div class="kpi-value purple" style="font-size:20px">${card.recentAnomalies}</div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px" class="mt-2">
        <div>
          <h4 class="mb-1">📊 Volatilitas Per Tahun</h4>
          ${Object.keys(vol).filter(k => !isNaN(k)).sort().map(year => `
            <div class="stat-row"><span class="stat-label">${year}</span><span class="stat-value">${vol[year]}%</span></div>
          `).join('')}
        </div>
        <div>
          <h4 class="mb-1">⚠️ Anomali Terdeteksi</h4>
          ${anomalies.length === 0 ? '<p class="text-muted text-sm">Tidak ada anomali terdeteksi</p>' :
            `<div style="max-height:180px;overflow-y:auto">
              ${anomalies.map(a => `
                <div class="stat-row">
                  <span class="stat-label">${a.date}</span>
                  <span class="anomaly-deviation ${a.deviation_pct > 0 ? 'positive' : 'negative'}">
                    ${formatChange(a.deviation_pct)} dari MA30
                  </span>
                </div>
              `).join('')}
            </div>`
          }
        </div>
      </div>
      ${supplyChainHtml}
    </div>
  `;
}

// ── Analisis Komparatif Regional & Margin Rantai Pasok (Tier 2/3) ──
function renderRegionalAnalysis(commodity) {
  const card = DATA.commodityCards.find(c => c.commodity === commodity) || { icon: '📦' };
  const icon = card.icon;

  // Update subtitle
  const subtitleEl = document.getElementById('regional-analysis-subtitle');
  if (subtitleEl) {
    subtitleEl.innerHTML = `Perbandingan harga antar daerah utama dan analisis margin rantai pasok untuk <strong>${icon} ${commodity}</strong>`;
  }

  // 1. A. Peta Disparitas Harga (3-Column Comparison Grid)
  const regionalData = DATA.regional[commodity] || {};
  const regions = ['Banda Aceh', 'Lhokseumawe', 'Meulaboh'];
  let prices = {};
  let changes = {};
  let cvs = {};

  regions.forEach(r => {
    const rData = regionalData[r];
    if (rData && rData.prices && rData.prices.length > 0) {
      prices[r] = rData.latestPrice;
      cvs[r] = rData.cv;
      const histPrices = rData.prices;
      const prevPrice = histPrices.length >= 30 ? histPrices[histPrices.length - 30] : histPrices[0];
      changes[r] = prevPrice ? ((rData.latestPrice - prevPrice) / prevPrice * 100) : 0;
    } else {
      prices[r] = null;
      changes[r] = 0;
      cvs[r] = 0;
    }
  });

  // Calculate disparity alerts
  let disparityAlerts = {};
  regions.forEach(r => {
    if (prices[r]) {
      const otherPrices = regions.filter(o => o !== r).map(o => prices[o]).filter(p => p !== null && p > 0);
      if (otherPrices.length > 0) {
        const avgOthers = otherPrices.reduce((sum, val) => sum + val, 0) / otherPrices.length;
        if (prices[r] > avgOthers * 1.15) {
          disparityAlerts[r] = '🔴 Gangguan Distribusi';
        } else if (prices[r] > avgOthers * 1.08) {
          disparityAlerts[r] = '⚠️ Disparitas Tinggi';
        }
      }
    }
  });

  let disparityHtml = `
    <h3 style="font-size: 15px; font-weight: 700; margin: 0 0 16px 0; display: flex; align-items: center; justify-content: space-between; color: #f1f5f9; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px;">
      <span>📊 Perbandingan Harga Antar Daerah</span>
      <span style="font-size: 11px; font-weight: normal; background: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 12px; color: #94a3b8;">Tren MoM</span>
    </h3>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; flex: 1;">
  `;

  regions.forEach(r => {
    const priceVal = prices[r];
    const pctChange = changes[r];
    const cvVal = cvs[r];
    const alertText = disparityAlerts[r];
    
    // Highlight if selected in the navbar
    const isSelectedRegion = (r === selectedRegion);
    const borderStyle = isSelectedRegion 
      ? 'border: 2px solid #eab308; box-shadow: 0 0 12px rgba(234, 179, 8, 0.15);' 
      : 'border: 1px solid rgba(255,255,255,0.06);';
    
    const changeText = pctChange >= 0 ? `▲ +${pctChange.toFixed(1)}%` : `▼ ${pctChange.toFixed(1)}%`;
    const changeColor = pctChange > 5 ? '#ef4444' : (pctChange < -5 ? '#10b981' : '#cbd5e1');
    
    disparityHtml += `
      <div style="background: rgba(30, 41, 59, 0.3); border-radius: 8px; padding: 16px 10px; display: flex; flex-direction: column; justify-content: space-between; min-height: 180px; position: relative; transition: all 0.2s; ${borderStyle}">
        ${isSelectedRegion ? `<span style="position: absolute; top: -8px; left: 50%; transform: translateX(-50%); font-size: 8px; font-weight: bold; background: #eab308; color: #0f172a; padding: 1px 6px; border-radius: 8px; text-transform: uppercase; z-index: 10;">Daerah Aktif</span>` : ''}
        <div>
          <div style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; text-align: center; margin-bottom: 8px;">📍 ${r}</div>
          <div style="font-size: 16px; font-weight: 700; color: #f8fafc; font-family: 'JetBrains Mono', monospace; text-align: center; margin-top: 4px;">
            ${priceVal ? formatPrice(priceVal) : '<span style="color: #64748b; font-size: 11px; font-weight: normal;">Tidak ada data</span>'}
          </div>
        </div>
        <div style="text-align: center; margin-top: 12px; display: flex; flex-direction: column; gap: 4px; align-items: center;">
          <span style="font-size: 13px; font-weight: 700; color: ${changeColor};">${priceVal ? changeText : '-'}</span>
          <span style="font-size: 9px; color: #64748b;">CV: ${priceVal ? cvVal + '%' : '-'}</span>
        </div>
        ${alertText ? `
          <div style="margin-top: 10px; font-size: 9px; font-weight: bold; background: ${alertText.includes('Gangguan') ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)'}; color: ${alertText.includes('Gangguan') ? '#ef4444' : '#f59e0b'}; padding: 3px 4px; border-radius: 4px; text-align: center; border: 1px solid ${alertText.includes('Gangguan') ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)'};">
             ${alertText}
          </div>
        ` : ''}
      </div>
    `;
  });

  disparityHtml += `
    </div>
    <div style="margin-top: 12px; font-size: 10px; color: #64748b; text-align: center; font-style: italic; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; margin-bottom: 0;">
      *Disparitas dihitung berdasarkan perbandingan deviasi harga antar daerah secara otomatis.
    </div>
  `;
  
  const dispEl = document.getElementById('card-regional-disparity');
  if (dispEl) dispEl.innerHTML = disparityHtml;


  // 2. B. Price Source Margin Analysis (Markup Chain Flow)
  const sourceData = DATA.priceBySource[commodity] || {};
  const prodPrice = sourceData['Produsen'] ? sourceData['Produsen'].latestPrice : null;
  const bigPrice = sourceData['Pedagang Besar'] ? sourceData['Pedagang Besar'].latestPrice : null;
  const tradPrice = sourceData['Pasar Tradisional'] ? sourceData['Pasar Tradisional'].latestPrice : null;

  const hasProd = prodPrice !== null && prodPrice > 0;
  const hasBig = bigPrice !== null && bigPrice > 0;
  const hasTrad = tradPrice !== null && tradPrice > 0;

  let marginHtml = `
    <h3 style="font-size: 15px; font-weight: 700; margin: 0 0 16px 0; color: #f1f5f9; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px;">
      <span>⛓️ Margin Rantai Pasok & Markup Flow</span>
    </h3>
    <div style="display: flex; flex-direction: column; justify-content: space-between; flex: 1; gap: 16px;">
      
      <!-- Visual Chain Flow -->
      <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(30, 41, 59, 0.2); border: 1px solid rgba(255,255,255,0.04); border-radius: 12px; padding: 20px 10px; position: relative;">
  `;
  
  // Node 1: Produsen
  marginHtml += `
    <div style="text-align: center; flex: 1;">
      <div style="font-size: 9px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">🌾 Produsen</div>
      <div style="font-size: 13px; font-weight: 700; color: ${hasProd ? '#10b981' : '#64748b'}; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
        ${hasProd ? formatPrice(prodPrice) : 'Tidak ada data'}
      </div>
    </div>
  `;
  
  // Connector 1
  if (hasProd && hasBig) {
    const m1 = ((bigPrice - prodPrice) / prodPrice * 100).toFixed(1);
    marginHtml += `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 0.8; position: relative;">
        <span style="font-size: 9px; font-weight: 700; background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.2); padding: 1px 5px; border-radius: 8px; z-index: 2;">+${m1}%</span>
        <div style="width: 100%; height: 2px; background: linear-gradient(to right, #10b981, #14b8a6); position: absolute; top: 50%; transform: translateY(-50%); z-index: 1;"></div>
      </div>
    `;
  } else {
    marginHtml += `
      <div style="display: flex; align-items: center; justify-content: center; flex: 0.8; position: relative;">
        <div style="width: 100%; height: 2px; background: rgba(255,255,255,0.05); border-style: dashed; border-width: 1px;"></div>
      </div>
    `;
  }
  
  // Node 2: Pedagang Besar
  marginHtml += `
    <div style="text-align: center; flex: 1;">
      <div style="font-size: 9px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">🏢 P. Besar</div>
      <div style="font-size: 13px; font-weight: 700; color: ${hasBig ? '#14b8a6' : '#64748b'}; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
        ${hasBig ? formatPrice(bigPrice) : 'Tidak ada data'}
      </div>
    </div>
  `;
  
  // Connector 2
  if (hasBig && hasTrad) {
    const m2 = ((tradPrice - bigPrice) / bigPrice * 100).toFixed(1);
    marginHtml += `
      <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 0.8; position: relative;">
        <span style="font-size: 9px; font-weight: 700; background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.2); padding: 1px 5px; border-radius: 8px; z-index: 2;">+${m2}%</span>
        <div style="width: 100%; height: 2px; background: linear-gradient(to right, #14b8a6, #f59e0b); position: absolute; top: 50%; transform: translateY(-50%); z-index: 1;"></div>
      </div>
    `;
  } else {
    marginHtml += `
      <div style="display: flex; align-items: center; justify-content: center; flex: 0.8; position: relative;">
        <div style="width: 100%; height: 2px; background: rgba(255,255,255,0.05); border-style: dashed; border-width: 1px;"></div>
      </div>
    `;
  }
  
  // Node 3: Pasar Tradisional
  marginHtml += `
    <div style="text-align: center; flex: 1;">
      <div style="font-size: 9px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">🧺 P. Tradisional</div>
      <div style="font-size: 13px; font-weight: 700; color: ${hasTrad ? '#f59e0b' : '#64748b'}; font-family: 'JetBrains Mono', monospace; margin-top: 4px;">
        ${hasTrad ? formatPrice(tradPrice) : 'Tidak ada data'}
      </div>
    </div>
  `;
  
  marginHtml += `
      </div>
  `;
  
  // Summary Card (Total Margin)
  if (hasProd && hasTrad) {
    const totalM = ((tradPrice - prodPrice) / prodPrice * 100).toFixed(1);
    marginHtml += `
      <div style="background: linear-gradient(135deg, rgba(244, 63, 94, 0.08) 0%, rgba(15, 23, 42, 0.4) 100%); border: 1px solid rgba(244, 63, 94, 0.2); border-radius: 8px; padding: 12px; display: flex; align-items: center; justify-content: space-between;">
        <div style="text-align: left;">
          <span style="font-size: 11px; color: #f43f5e; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: block;">Total Margin Rantai Pasok</span>
          <span style="font-size: 9px; color: #64748b; margin-top: 2px; display: block;">Selisih harga tingkat konsumen vs petani</span>
        </div>
        <span style="font-size: 18px; font-weight: 800; color: #f43f5e; text-shadow: 0 0 10px rgba(244, 63, 94, 0.2);">+${totalM}%</span>
      </div>
    `;
  } else {
    marginHtml += `
      <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 12px; text-align: center; display: flex; flex-direction: column; gap: 4px; justify-content: center;">
        <span style="font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Margin Total Tidak Tersedia</span>
        <span style="font-size: 9px; color: #64748b;">Kalkulasi lengkap memerlukan data Produsen & Pasar Tradisional.</span>
      </div>
    `;
  }
  
  marginHtml += `
    </div>
  `;
  
  const margEl = document.getElementById('card-margin-analysis');
  if (margEl) margEl.innerHTML = marginHtml;
}

// ── Price Trend Chart ────────────────────────────────────────────
function renderPriceTrendChart() {
  const ctx = document.getElementById('chart-price-trend').getContext('2d');

  // Category filter buttons
  const controls = document.getElementById('trend-category-filter');
  const categories = ['all', ...DATA.categories];
  controls.innerHTML = categories.map(cat => `
    <button class="chart-btn ${cat === 'all' ? 'active' : ''}" 
            onclick="filterTrendCategory('${cat}')"
            data-category="${cat}">
      ${cat === 'all' ? '🔍 Semua' : (DATA.categoryIcons[cat] || '') + ' ' + cat}
    </button>
  `).join('');

  charts.priceTrend = new Chart(ctx, {
    type: 'line',
    data: { datasets: [] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11 },
            boxWidth: 12,
            padding: 12,
            usePointStyle: true,
          },
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          titleFont: { family: 'Inter', weight: '600' },
          bodyFont: { family: 'JetBrains Mono', size: 12 },
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatPrice(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'month',
            displayFormats: { month: 'MMM yy' },
          },
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', font: { size: 10 } },
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: (v) => formatPriceShort(v),
          },
        },
      },
    },
  });

  updatePriceTrendChart();
}

function toggleForecast() {
  showForecast = !showForecast;
  const btn = document.getElementById('toggle-forecast-btn');
  btn.classList.toggle('active', showForecast);
  btn.innerHTML = showForecast ? '✨ Sembunyikan Prediksi' : '🔮 Tampilkan Prediksi 90 Hari';
  updatePriceTrendChart(selectedCommodity);
}

function updatePriceTrendChart(singleCommodity = null) {
  // Reconstruct timeseries and forecast references for regional support (Tier 2 regional forecasts)
  let ts = DATA.timeseries;
  let forecasts = DATA.forecasts || {};
  
  if (selectedRegion && selectedRegion !== 'aggregated') {
    ts = {};
    for (const [commodity, regDict] of Object.entries(DATA.regional)) {
      if (regDict[selectedRegion]) {
        ts[commodity] = {
          shortName: DATA.commodityCards.find(c => c.commodity === commodity)?.shortName || commodity,
          category: DATA.commodityCards.find(c => c.commodity === commodity)?.category || '',
          dates: regDict[selectedRegion].dates,
          prices: regDict[selectedRegion].prices
        };
      }
    }
    
    forecasts = {};
    for (const [commodity, regFcDict] of Object.entries(DATA.regionalForecasts)) {
      if (regFcDict[selectedRegion]) {
        forecasts[commodity] = regFcDict[selectedRegion];
      }
    }
  }

  const datasets = [];

  for (const [commodity, data] of Object.entries(ts)) {
    if (singleCommodity && commodity !== singleCommodity) continue;
    if (!singleCommodity && activeCategory !== 'all' && data.category !== activeCategory) continue;

    const color = CATEGORY_COLORS[data.category] || '#94a3b8';
    
    // 1. Main historical data
    datasets.push({
      label: data.shortName,
      data: data.dates.map((d, i) => ({ x: d, y: data.prices[i] })),
      borderColor: color,
      backgroundColor: color + '15',
      borderWidth: singleCommodity ? 2.5 : 1.5,
      pointRadius: singleCommodity ? 2 : 0,
      pointHoverRadius: 4,
      fill: !!singleCommodity,
      tension: 0.3,
      order: 10
    });

    // 2. Forecast data (if enabled)
    if (showForecast && forecasts[commodity]) {
      const fc = forecasts[commodity];
      const lastHistDate = data.dates[data.dates.length - 1];
      const lastHistPrice = data.prices[data.prices.length - 1];

      // Add a bridge point from the last historical data to the first forecast
      const forecastPoints = [
        { x: lastHistDate, y: lastHistPrice },
        ...fc.dates.map((d, i) => ({ x: d, y: fc.yhat[i] }))
      ];

      datasets.push({
        label: `${data.shortName} (Prediksi)`,
        data: forecastPoints,
        borderColor: color,
        borderDash: [5, 5],
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
        tension: 0.4,
        order: 5
      });

      // 3. Confidence Interval (Shaded Area)
      if (singleCommodity) {
        const lowerPoints = [
            { x: lastHistDate, y: lastHistPrice },
            ...fc.dates.map((d, i) => ({ x: d, y: fc.yhat_lower[i] }))
        ];
        const upperPoints = [
            { x: lastHistDate, y: lastHistPrice },
            ...fc.dates.map((d, i) => ({ x: d, y: fc.yhat_upper[i] }))
        ];

        datasets.push({
          label: `${data.shortName} (Batas Atas)`,
          data: upperPoints,
          borderColor: 'transparent',
          backgroundColor: color + '10',
          pointRadius: 0,
          fill: false,
          tension: 0.4,
          order: 20
        });

        datasets.push({
          label: `${data.shortName} (Batas Bawah)`,
          data: lowerPoints,
          borderColor: 'transparent',
          backgroundColor: color + '10',
          pointRadius: 0,
          fill: '-1', // Fill between this and the previous dataset (Upper)
          tension: 0.4,
          order: 21
        });
      }
    }
  }

  charts.priceTrend.data.datasets = datasets;
  charts.priceTrend.update('none');
}

function filterTrendCategory(category) {
  activeCategory = category;
  document.querySelectorAll('#trend-category-filter .chart-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.category === category);
  });
  if (selectedCommodity) {
    selectedCommodity = null;
    document.querySelectorAll('.commodity-card').forEach(c => c.classList.remove('selected'));
    document.getElementById('detail-panel').classList.remove('active');
  }
  updatePriceTrendChart();
}

// ── YoY Comparison Chart ─────────────────────────────────────────
function renderYoYChart() {
  const ctx = document.getElementById('chart-yoy').getContext('2d');
  const yoy = DATA.yoyData;
  const labels = yoy.map(y => y.shortName);

  charts.yoy = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: '2024 → 2025',
          data: yoy.map(y => y.change_24_25),
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: '2025 → 2026',
          data: yoy.map(y => y.change_25_26),
          backgroundColor: 'rgba(239, 68, 68, 0.7)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11 },
            padding: 16,
            usePointStyle: true,
          },
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.raw > 0 ? '+' : ''}${ctx.raw.toFixed(1)}%`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: (v) => v + '%',
          },
        },
        y: {
          grid: { display: false },
          ticks: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 10 },
          },
        },
      },
    },
  });
}

// ── Seasonality Heatmap ──────────────────────────────────────────
function renderSeasonalityHeatmap() {
  const container = document.getElementById('seasonality-heatmap');
  const season = DATA.seasonality;
  const commodities = Object.keys(season);

  // Color scale: green (negative/cheap) → white (neutral) → red (expensive)
  function zScoreColor(z) {
    const clamped = Math.max(-3, Math.min(3, z));
    if (clamped >= 0) {
      const intensity = clamped / 3;
      const r = 239, g = Math.round(68 + (1 - intensity) * 187), b = Math.round(68 + (1 - intensity) * 187);
      return `rgba(${r}, ${g}, ${b}, ${0.2 + intensity * 0.6})`;
    } else {
      const intensity = Math.abs(clamped) / 3;
      const r = Math.round(34 + (1 - intensity) * 221), g = 197, b = Math.round(94 + (1 - intensity) * 161);
      return `rgba(${r}, ${g}, ${b}, ${0.2 + intensity * 0.6})`;
    }
  }

  function textColor(z) {
    return Math.abs(z) > 1.5 ? '#fff' : '#94a3b8';
  }

  let html = '<div class="heatmap-grid">';

  // Header row
  html += '<div class="heatmap-row">';
  html += '<div class="heatmap-label"></div>';
  MONTH_LABELS.forEach(m => {
    html += `<div class="heatmap-cell heatmap-header">${m}</div>`;
  });
  html += '</div>';

  // Data rows
  commodities.forEach(commodity => {
    const d = season[commodity];
    html += '<div class="heatmap-row">';
    html += `<div class="heatmap-label" title="${commodity}">${d.shortName}</div>`;
    d.values.forEach((v, i) => {
      const bg = zScoreColor(v);
      const tc = textColor(v);
      html += `<div class="heatmap-cell" style="background:${bg};color:${tc}" 
               title="${commodity} — ${MONTH_LABELS[i]}: Z=${v.toFixed(2)}">${v.toFixed(1)}</div>`;
    });
    html += '</div>';
  });

  html += '</div>';
  container.innerHTML = html;
}

// ── Volatility Heatmap ───────────────────────────────────────────
function renderVolatilityHeatmap() {
  const container = document.getElementById('volatility-heatmap');
  const vol = DATA.volatility;
  const commodities = Object.keys(vol);

  // Sort by latest CV descending
  const maxYear = Object.keys(vol[commodities[0]] || {}).filter(k => !isNaN(k)).sort().reverse()[0] || '2025';
  commodities.sort((a, b) => (vol[b][maxYear] || 0) - (vol[a][maxYear] || 0));

  function cvColor(cv) {
    if (cv > 20) return { bg: 'rgba(239, 68, 68, 0.6)', text: '#fff' };
    if (cv > 10) return { bg: 'rgba(245, 158, 11, 0.5)', text: '#fff' };
    if (cv > 5) return { bg: 'rgba(245, 158, 11, 0.25)', text: '#fcd34d' };
    return { bg: 'rgba(34, 197, 94, 0.15)', text: '#86efac' };
  }

  let html = '<div class="heatmap-grid">';

  // Header row
  html += '<div class="heatmap-row">';
  html += '<div class="heatmap-label"></div>';
  const years = Object.keys(vol[commodities[0]] || {}).filter(k => !isNaN(k)).sort();
  years.forEach(y => {
    html += `<div class="heatmap-cell heatmap-header">${y}</div>`;
  });
  html += '</div>';

  commodities.forEach(commodity => {
    const d = vol[commodity];
    html += '<div class="heatmap-row">';
    html += `<div class="heatmap-label" title="${commodity}">${d.shortName}</div>`;
    years.forEach(y => {
      const v = d[y] || 0;
      const c = cvColor(v);
      html += `<div class="heatmap-cell" style="background:${c.bg};color:${c.text};min-width:80px"
               title="${commodity} ${y}: CV=${v}%">${v}%</div>`;
    });
    html += '</div>';
  });

  html += '</div>';
  container.innerHTML = html;
}

// ── Alert Feed ───────────────────────────────────────────────────
function renderAlertFeed() {
  const container = document.getElementById('alert-feed');
  const alerts = DATA.alertFeed.slice(0, 25);

  container.innerHTML = alerts.map((a, i) => `
    <div class="alert-item" style="animation-delay: ${i * 50}ms">
      <div class="alert-indicator ${a.severity}"></div>
      <div class="alert-content">
        <div class="alert-title">${a.shortName} — ${
          a.severity === 'critical' ? '🚨 KRITIS' : 
          a.severity === 'prediction' ? '🔮 PREDIKSI' : '⚠️ WASPADA'
        }</div>
        <div class="alert-detail">
          ${a.severity === 'prediction' 
            ? `Prediksi: ${formatPrice(a.price)} (Spike ${formatChange(a.spike_pct)})`
            : `Harga: ${formatPrice(a.price)} | MA30: ${formatPrice(a.ma30)} | Deviasi: ${formatChange(a.deviation_pct)}`
          }
        </div>
        <div class="alert-action">↳ ${a.action}</div>
      </div>
      <div class="alert-date">${a.date}</div>
    </div>
  `).join('');
}

// ── Anomaly Table ────────────────────────────────────────────────
function renderAnomalyTable() {
  const container = document.getElementById('anomaly-table-body');
  // Show most recent anomalies, limit to 50 for performance
  const anomalies = DATA.anomalies.slice(0, 50);

  container.innerHTML = anomalies.map(a => `
    <tr>
      <td class="font-mono">${a.date}</td>
      <td>${a.shortName}</td>
      <td>${a.category}</td>
      <td class="font-mono">${formatPrice(a.price)}</td>
      <td class="font-mono">${formatPrice(a.ma30)}</td>
      <td class="anomaly-deviation ${a.deviation_pct > 0 ? 'positive' : 'negative'}">
        ${formatChange(a.deviation_pct)}
      </td>
      <td class="font-mono">${a.z_score.toFixed(1)}σ</td>
      <td class="severity-cell ${a.severity}">${a.severity === 'critical' ? '🔴 Kritis' : '🟡 Waspada'}</td>
    </tr>
  `).join('');
}

// ── Category Stacked Area Chart ──────────────────────────────────
function renderCategoryAreaChart() {
  const ctx = document.getElementById('chart-category-area').getContext('2d');
  const cm = DATA.categoryMonthly;
  const categories = Object.keys(cm.categories).filter(c => c !== 'Daging Sapi'); // exclude outlier

  const datasets = categories.map(cat => ({
    label: cat,
    data: cm.categories[cat],
    backgroundColor: (CATEGORY_COLORS[cat] || '#666') + '80',
    borderColor: CATEGORY_COLORS[cat] || '#666',
    borderWidth: 1,
    fill: true,
    tension: 0.3,
    pointRadius: 0,
  }));

  charts.categoryArea = new Chart(ctx, {
    type: 'line',
    data: {
      labels: cm.dates,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 10 },
            boxWidth: 10,
            padding: 10,
            usePointStyle: true,
          },
        },
        tooltip: {
          mode: 'nearest',
          intersect: false,
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleFont: { family: 'Inter', size: 12, weight: '600' },
          bodyFont: { family: 'Inter', size: 11 },
          padding: 10,
          callbacks: {
            title: (items) => {
              if (!items.length) return '';
              const d = new Date(items[0].parsed.x);
              return d.toLocaleDateString('id-ID', { month: 'long', year: 'numeric' });
            },
            label: (tooltipItem) => ` ${tooltipItem.dataset.label}: ${formatPrice(tooltipItem.raw)}`,
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: { unit: 'quarter', displayFormats: { quarter: 'MMM yy' } },
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', font: { size: 10 } },
          stacked: true,
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: {
            color: '#64748b',
            font: { size: 10 },
            callback: (v) => formatPriceShort(v),
          },
          stacked: true,
        },
      },
    },
  });
}



// ── Navigation between tab sections ──────────────────────────────
function switchSection(sectionId) {
  document.querySelectorAll('.nav-section-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.section === sectionId);
  });
  // Smooth scroll to section
  const target = document.getElementById(sectionId);
  if (target) {
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// ══════════════════════════════════════════════════════════════════
// MODUL G: Spatial Tab — Regional Chart + Arbitrage Advisor
// ══════════════════════════════════════════════════════════════════

function populateSpatialDropdown() {
  const select = document.getElementById('spatial-commodity-select');
  if (!select || !DATA.commodityCards) return;
  select.innerHTML = DATA.commodityCards.map(c =>
    `<option value="${c.commodity}" ${c.commodity === spatialCommodity ? 'selected' : ''}>${c.icon} ${c.shortName}</option>`
  ).join('');
}

function renderSpatialTab() {
  renderRegionalAnalysis(spatialCommodity);
  renderRegionalChart(spatialCommodity);
  renderArbitrageAdvisor();
}

function renderRegionalChart(commodity) {
  const canvas = document.getElementById('chart-regional-comparison');
  if (!canvas) return;

  // Destroy previous instance
  if (charts.regionalComparison) {
    charts.regionalComparison.destroy();
  }

  const regionalData = DATA.regional[commodity] || {};
  const regions = ['Banda Aceh', 'Lhokseumawe', 'Meulaboh'];
  const regionColors = { 'Banda Aceh': '#3b82f6', 'Lhokseumawe': '#f59e0b', 'Meulaboh': '#10b981' };

  const datasets = regions.map(r => {
    const rData = regionalData[r];
    if (!rData || !rData.dates || !rData.prices) return null;
    return {
      label: r,
      data: rData.dates.map((d, i) => ({ x: d, y: rData.prices[i] })),
      borderColor: regionColors[r],
      backgroundColor: regionColors[r] + '15',
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      fill: false,
      tension: 0.3,
    };
  }).filter(Boolean);

  charts.regionalComparison = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, usePointStyle: true, padding: 12 },
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          bodyFont: { family: 'JetBrains Mono', size: 12 },
          callbacks: { label: (ctx) => `${ctx.dataset.label}: ${formatPrice(ctx.parsed.y)}` },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: { unit: 'month', displayFormats: { month: 'MMM yy' } },
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', font: { size: 10 } },
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: '#64748b', font: { size: 10 }, callback: (v) => formatPriceShort(v) },
        },
      },
    },
  });
}

function renderArbitrageAdvisor() {
  const container = document.getElementById('arbitrage-advisor-grid');
  if (!container) return;

  const regions = ['Banda Aceh', 'Lhokseumawe', 'Meulaboh'];
  const opportunities = [];

  // Scan ALL commodities for price disparity > 30%
  (DATA.commodityCards || []).forEach(card => {
    const regData = DATA.regional[card.commodity] || {};
    const prices = {};
    regions.forEach(r => {
      if (regData[r] && regData[r].latestPrice > 0) {
        prices[r] = regData[r].latestPrice;
      }
    });

    const validRegions = Object.keys(prices);
    if (validRegions.length < 2) return;

    // Find max and min
    let maxRegion = validRegions[0], minRegion = validRegions[0];
    validRegions.forEach(r => {
      if (prices[r] > prices[maxRegion]) maxRegion = r;
      if (prices[r] < prices[minRegion]) minRegion = r;
    });

    const diff = prices[maxRegion] - prices[minRegion];
    const diffPct = (diff / prices[minRegion]) * 100;

    if (diffPct > 30) {
      opportunities.push({
        commodity: card.commodity,
        shortName: card.shortName,
        icon: card.icon,
        maxRegion,
        minRegion,
        maxPrice: prices[maxRegion],
        minPrice: prices[minRegion],
        diffPct,
        diffRupiah: diff,
      });
    }
  });

  // Sort by disparity descending
  opportunities.sort((a, b) => b.diffPct - a.diffPct);

  if (opportunities.length === 0) {
    container.innerHTML = `
      <div class="glass-card arbitrage-no-data">
        <p style="font-size:28px; margin-bottom:12px;">✅</p>
        <p style="font-size:16px; font-weight:600; color:var(--status-normal); margin-bottom:6px;">Tidak Ada Disparitas Ekstrem</p>
        <p>Seluruh komoditas memiliki selisih harga antar daerah di bawah 30%. Distribusi berjalan baik.</p>
      </div>`;
    return;
  }

  container.innerHTML = `<div class="arbitrage-grid">` + opportunities.map(o => {
    const isExtreme = o.diffPct > 60;
    const cardClass = isExtreme ? 'extreme' : '';
    const badgeColor = isExtreme ? 'var(--status-critical)' : 'var(--status-warning)';
    const badgeBg = isExtreme ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)';
    const badgeText = isExtreme ? '🔴 KRITIS' : '🟡 DISPARITAS';

    return `
      <div class="arbitrage-card ${cardClass}">
        <div class="arbitrage-header">
          <span style="font-size:15px; font-weight:700;">${o.icon} ${o.shortName}</span>
          <span class="arbitrage-badge" style="color:${badgeColor}; background:${badgeBg}; border:1px solid ${badgeColor}30;">${badgeText}</span>
        </div>
        <div style="display:flex; gap:12px; margin-bottom:8px;">
          <div style="flex:1; text-align:center; padding:10px; background:rgba(239,68,68,0.06); border-radius:8px; border:1px solid rgba(239,68,68,0.1);">
            <div style="font-size:9px; color:var(--text-muted); font-weight:700; text-transform:uppercase;">📍 ${o.maxRegion} (Termahal)</div>
            <div style="font-size:15px; font-weight:700; color:var(--status-critical); font-family:'JetBrains Mono',monospace; margin-top:4px;">${formatPrice(o.maxPrice)}</div>
          </div>
          <div style="flex:1; text-align:center; padding:10px; background:rgba(34,197,94,0.06); border-radius:8px; border:1px solid rgba(34,197,94,0.1);">
            <div style="font-size:9px; color:var(--text-muted); font-weight:700; text-transform:uppercase;">📍 ${o.minRegion} (Termurah)</div>
            <div style="font-size:15px; font-weight:700; color:var(--status-normal); font-family:'JetBrains Mono',monospace; margin-top:4px;">${formatPrice(o.minPrice)}</div>
          </div>
        </div>
        <div style="text-align:center; font-size:18px; font-weight:800; color:${badgeColor}; margin:8px 0;">
          Selisih: +${o.diffPct.toFixed(1)}% (${formatPrice(o.diffRupiah)})
        </div>
        <div class="arbitrage-recommendation">
          <strong>💡 REKOMENDASI ARBITRASE:</strong><br>
          Harga ${o.shortName} di ${o.maxRegion} (${formatPrice(o.maxPrice)}) jauh lebih tinggi dibanding ${o.minRegion} (${formatPrice(o.minPrice)}). Selisih: +${o.diffPct.toFixed(1)}%.<br>
          <strong>⚡ Aksi:</strong> Mobilisasi stok dari ${o.minRegion} ke ${o.maxRegion} untuk menekan disparitas harga.
        </div>
      </div>`;
  }).join('') + `</div>`;
}

// ══════════════════════════════════════════════════════════════════
// MODUL H: Margin Health Tab — Supply Chain for ALL commodities
// ══════════════════════════════════════════════════════════════════

function renderMarginHealthTab() {
  const summaryContainer = document.getElementById('margin-summary-cards');
  const gridContainer = document.getElementById('margin-health-grid');
  if (!summaryContainer || !gridContainer) return;

  let healthy = 0, warning = 0, danger = 0;
  const cards = [];

  (DATA.commodityCards || []).forEach(card => {
    const src = DATA.priceBySource[card.commodity] || {};
    const prodPrice = src['Produsen'] ? src['Produsen'].latestPrice : null;
    const bigPrice = src['Pedagang Besar'] ? src['Pedagang Besar'].latestPrice : null;
    const tradPrice = src['Pasar Tradisional'] ? src['Pasar Tradisional'].latestPrice : null;
    const modPrice = src['Pasar Modern'] ? src['Pasar Modern'].latestPrice : null;

    const hasProd = prodPrice && prodPrice > 0;
    const hasBig = bigPrice && bigPrice > 0;
    const hasTrad = tradPrice && tradPrice > 0;
    const hasMod = modPrice && modPrice > 0;

    let healthStatus = 'no-data';
    let markup1 = null;   // Produsen → Pedagang Besar
    let markup2 = null;   // Pedagang Besar → Pasar Tradisional
    let markup3 = null;   // Pedagang Besar → Pasar Modern (SETINGKAT dengan markup2!)
    let totalTrad = null;  // Produsen → Pasar Tradisional (jalur tradisional)
    let totalMod = null;   // Produsen → Pasar Modern (jalur modern)

    if (hasProd && hasBig) markup1 = ((bigPrice - prodPrice) / prodPrice * 100);
    if (hasBig && hasTrad) markup2 = ((tradPrice - bigPrice) / bigPrice * 100);
    if (hasBig && hasMod)  markup3 = ((modPrice - bigPrice) / bigPrice * 100);
    if (hasProd && hasTrad) totalTrad = ((tradPrice - prodPrice) / prodPrice * 100);
    if (hasProd && hasMod)  totalMod = ((modPrice - prodPrice) / prodPrice * 100);

    // Health status: gunakan margin TERBURUK (max) dari kedua jalur
    const maxTotal = Math.max(totalTrad || 0, totalMod || 0);
    if (totalTrad !== null || totalMod !== null) {
      if (maxTotal > 40) { healthStatus = 'danger'; danger++; }
      else if (maxTotal > 20) { healthStatus = 'warning'; warning++; }
      else { healthStatus = 'good'; healthy++; }
    }

    cards.push({ ...card, prodPrice, bigPrice, tradPrice, modPrice, hasProd, hasBig, hasTrad, hasMod, healthStatus, markup1, markup2, markup3, totalTrad, totalMod, maxTotal });
  });

  // Sort: danger first
  const order = { danger: 0, warning: 1, good: 2, 'no-data': 3 };
  cards.sort((a, b) => (order[a.healthStatus] ?? 3) - (order[b.healthStatus] ?? 3));

  // Summary KPI cards
  summaryContainer.innerHTML = `
    <div class="kpi-card green">
      <div class="kpi-label">Rantai Pasok Sehat</div>
      <div class="kpi-value green">${healthy}</div>
      <div class="kpi-detail">Markup &lt;20% — distribusi efisien</div>
    </div>
    <div class="kpi-card yellow">
      <div class="kpi-label">Perlu Perhatian</div>
      <div class="kpi-value yellow">${warning}</div>
      <div class="kpi-detail">Markup 20-40% — inefisiensi distribusi</div>
    </div>
    <div class="kpi-card red">
      <div class="kpi-label">Tidak Wajar</div>
      <div class="kpi-value red">${danger}</div>
      <div class="kpi-detail">Markup &gt;40% — potensi penimbunan</div>
    </div>`;

  // Color helper
  function mColor(val) {
    if (val === null) return '#64748b';
    return val > 20 ? '#ef4444' : val > 10 ? '#f59e0b' : '#3b82f6';
  }
  function mkBadge(val, color) {
    const txt = val !== null ? (val >= 0 ? '+' : '') + val.toFixed(1) + '%' : '—';
    return `<span class="margin-tl-badge" style="color:${color}; background:${color}15; border:1px solid ${color}30;">${txt}</span>`;
  }
  function statusColor(val) {
    if (val === null) return '#64748b';
    return val > 40 ? '#ef4444' : val > 20 ? '#f59e0b' : '#10b981';
  }
  function barWidth(val) {
    if (val === null || val <= 0) return 0;
    return Math.min(val / 100 * 100, 100);  // cap at 100%
  }

  // Margin cards grid
  gridContainer.innerHTML = cards.map(c => {
    const healthClass = c.healthStatus === 'good' ? 'health-good' : c.healthStatus === 'warning' ? 'health-warning' : c.healthStatus === 'danger' ? 'health-danger' : '';
    const badgeClass = c.healthStatus === 'good' ? 'good' : c.healthStatus === 'warning' ? 'warning' : c.healthStatus === 'danger' ? 'danger' : '';
    const badgeLabel = c.healthStatus === 'good' ? 'SEHAT' : c.healthStatus === 'warning' ? 'WASPADA' : c.healthStatus === 'danger' ? 'TIDAK WAJAR' : 'NO DATA';

    const m1c = mColor(c.markup1);
    const m2c = mColor(c.markup2);
    const m3c = mColor(c.markup3);

    // Summary footer with severity bars
    let footerHtml = '';
    if (c.totalTrad !== null || c.totalMod !== null) {
      const tradColor = statusColor(c.totalTrad);
      const modColor = statusColor(c.totalMod);
      footerHtml = `
        <div class="margin-summary-footer">
          <div class="margin-summary-channel">
            <div class="margin-summary-channel-label">Jalur Tradisional</div>
            <div class="margin-summary-channel-value" style="color:${tradColor}">${c.totalTrad !== null ? '+' + c.totalTrad.toFixed(1) + '%' : '—'}</div>
            <div class="margin-severity-bar">
              <div class="margin-severity-fill" style="width:${barWidth(c.totalTrad)}%; background:${tradColor};"></div>
            </div>
          </div>
          <div class="margin-summary-channel">
            <div class="margin-summary-channel-label">Jalur Modern</div>
            <div class="margin-summary-channel-value" style="color:${modColor}">${c.totalMod !== null ? '+' + c.totalMod.toFixed(1) + '%' : '—'}</div>
            <div class="margin-severity-bar">
              <div class="margin-severity-fill" style="width:${barWidth(c.totalMod)}%; background:${modColor};"></div>
            </div>
          </div>
        </div>`;
    }

    return `
      <div class="margin-card ${healthClass}">
        <div class="margin-card-header">
          <div class="margin-card-title">${c.icon} ${c.shortName}</div>
          <span class="health-badge ${badgeClass}">${badgeLabel}</span>
        </div>

        <div class="margin-timeline">
          <!-- Node: Produsen -->
          <div class="margin-tl-node level-produsen">
            <span class="margin-tl-label">Produsen</span>
            <span class="margin-tl-price" style="color:${c.hasProd ? '#10b981' : '#64748b'}">${c.hasProd ? formatPrice(c.prodPrice) : '—'}</span>
          </div>

          <!-- Connector -->
          <div class="margin-tl-connector">
            ${mkBadge(c.markup1, m1c)}
          </div>

          <!-- Node: Pedagang Besar -->
          <div class="margin-tl-node level-pedagang">
            <span class="margin-tl-label">Pedagang Besar</span>
            <span class="margin-tl-price" style="color:${c.hasBig ? '#14b8a6' : '#64748b'}">${c.hasBig ? formatPrice(c.bigPrice) : '—'}</span>
          </div>

          <!-- Fork: two retail channels side-by-side -->
          <div class="margin-fork-wrapper">
            <div class="margin-fork-label">Distribusi Retail</div>
            <div class="margin-fork-grid">
              <div class="margin-fork-panel panel-trad">
                <div class="margin-fork-panel-label">Pasar Tradisional</div>
                <div class="margin-fork-panel-price" style="color:${c.hasTrad ? '#f59e0b' : '#64748b'}">${c.hasTrad ? formatPrice(c.tradPrice) : '—'}</div>
                <div class="margin-fork-panel-markup" style="color:${m2c}; background:${m2c}15; border:1px solid ${m2c}30;">${c.markup2 !== null ? (c.markup2 >= 0 ? '+' : '') + c.markup2.toFixed(1) + '%' : '—'}</div>
              </div>
              <div class="margin-fork-panel panel-mod">
                <div class="margin-fork-panel-label">Pasar Modern</div>
                <div class="margin-fork-panel-price" style="color:${c.hasMod ? '#ec4899' : '#64748b'}">${c.hasMod ? formatPrice(c.modPrice) : '—'}</div>
                <div class="margin-fork-panel-markup" style="color:${m3c}; background:${m3c}15; border:1px solid ${m3c}30;">${c.markup3 !== null ? (c.markup3 >= 0 ? '+' : '') + c.markup3.toFixed(1) + '%' : '—'}</div>
              </div>
            </div>
          </div>
        </div>

        ${footerHtml}

        ${c.healthStatus === 'danger' ? `
          <div class="margin-warning-text">
            🚨 Potensi penimbunan/spekulasi — Perlu investigasi Satgas Pangan
          </div>` : ''}
      </div>`;
  }).join('');
}

// ══════════════════════════════════════════════════════════════════
// MODUL I: SVG Map Aceh — Update glow based on anomalies
// ══════════════════════════════════════════════════════════════════

function updateSVGMap() {
  if (!DATA || !DATA.anomalies) return;

  const regionMapping = {
    'Banda Aceh': 'region-banda-aceh',
    'Lhokseumawe': 'region-lhokseumawe',
    'Meulaboh': 'region-meulaboh',
  };

  // Aggregate anomaly severity per region from recent anomalies
  const regionStatus = { 'Banda Aceh': 'normal', 'Lhokseumawe': 'normal', 'Meulaboh': 'normal' };

  // Check recent anomalies (last 30 days) for each region
  const recentAnomalies = DATA.anomalies.slice(0, 100);
  recentAnomalies.forEach(a => {
    if (a.daerah && regionStatus[a.daerah] !== undefined) {
      if (a.z_score > 3) regionStatus[a.daerah] = 'critical';
      else if (a.z_score > 2 && regionStatus[a.daerah] !== 'critical') regionStatus[a.daerah] = 'warning';
    }
  });

  // Also check alertFeed for regional anomalies
  (DATA.alertFeed || []).forEach(a => {
    if (a.daerah && regionStatus[a.daerah] !== undefined && a.severity !== 'prediction') {
      if (a.severity === 'critical') regionStatus[a.daerah] = 'critical';
      else if (a.severity === 'warning' && regionStatus[a.daerah] !== 'critical') regionStatus[a.daerah] = 'warning';
    }
  });

  // Apply CSS classes
  Object.entries(regionMapping).forEach(([region, svgId]) => {
    const el = document.getElementById(svgId);
    if (!el) return;
    el.classList.remove('glow-anomaly-red', 'glow-anomaly-yellow', 'glow-normal');
    if (regionStatus[region] === 'critical') el.classList.add('glow-anomaly-red');
    else if (regionStatus[region] === 'warning') el.classList.add('glow-anomaly-yellow');
    else el.classList.add('glow-normal');
  });

  // Update summary text
  const summaryEl = document.getElementById('map-status-summary');
  if (summaryEl) {
    const critical = Object.values(regionStatus).filter(s => s === 'critical').length;
    const warn = Object.values(regionStatus).filter(s => s === 'warning').length;
    const normal = Object.values(regionStatus).filter(s => s === 'normal').length;
    summaryEl.innerHTML = `
      <span style="color:var(--status-critical); font-weight:600;">${critical} Kritis</span> · 
      <span style="color:var(--status-warning); font-weight:600;">${warn} Waspada</span> · 
      <span style="color:var(--status-normal); font-weight:600;">${normal} Normal</span>
      <span style="margin-left:8px; color:var(--text-muted);">— Update otomatis berdasarkan data anomali terbaru</span>
    `;
  }
}

// ── Init on DOM Load ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', initApp);
