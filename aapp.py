"""
Pill Inspection Dashboard — app.py
===================================
Run this alongside main.py to get a live web dashboard.
Visit: http://127.0.0.1:5000

Install: pip install flask
"""

import json
from pathlib import Path
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
RESULTS_FILE = "results.json"

# ──────────────────────────────────────────────────────────────
# HTML Dashboard (single-file, no external files needed)
# ──────────────────────────────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Pill Inspection Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@300;400;600;700&display=swap" rel="stylesheet"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg:        #080c10;
    --panel:     #0d1318;
    --border:    #1a2a35;
    --green:     #00e676;
    --red:       #ff1744;
    --yellow:    #ffd600;
    --blue:      #00b0ff;
    --text:      #cdd8e0;
    --muted:     #4a6070;
    --mono:      'Share Tech Mono', monospace;
    --sans:      'Barlow', sans-serif;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    min-height: 100vh;
    padding: 24px;
  }

  /* Scanline overlay */
  body::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 999;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.07) 2px,
      rgba(0,0,0,0.07) 4px
    );
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--border);
    padding-bottom: 18px;
    margin-bottom: 28px;
    flex-wrap: wrap;
    gap: 12px;
  }

  .logo-block h1 {
    font-family: var(--mono);
    font-size: 1.35rem;
    color: var(--green);
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  .logo-block p {
    font-size: 0.75rem;
    color: var(--muted);
    font-family: var(--mono);
    margin-top: 3px;
    letter-spacing: 1px;
  }

  .live-badge {
    display: flex; align-items: center; gap: 8px;
    font-family: var(--mono); font-size: 0.75rem;
    color: var(--green); letter-spacing: 1px;
  }

  .pulse {
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
    animation: pulse 1.4s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.7); }
  }

  /* KPI row */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px;
    margin-bottom: 24px;
  }

  .kpi {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    transition: border-color .25s;
  }

  .kpi:hover { border-color: var(--blue); }

  .kpi::after {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent, var(--blue));
    border-radius: 10px 10px 0 0;
  }

  .kpi-label {
    font-size: 0.68rem; letter-spacing: 2px;
    text-transform: uppercase; color: var(--muted);
    font-family: var(--mono); margin-bottom: 8px;
  }

  .kpi-value {
    font-family: var(--mono); font-size: 2rem;
    font-weight: 700; line-height: 1;
  }

  .kpi-sub {
    font-size: 0.7rem; color: var(--muted);
    margin-top: 5px; font-family: var(--mono);
  }

  /* Charts row */
  .charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
    margin-bottom: 24px;
  }

  @media (max-width: 760px) { .charts-grid { grid-template-columns: 1fr; } }

  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
  }

  .panel-title {
    font-family: var(--mono); font-size: 0.72rem;
    letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); margin-bottom: 16px;
  }

  .chart-wrap { position: relative; height: 220px; }

  /* Batch table */
  .table-wrap { overflow-x: auto; }

  table {
    width: 100%; border-collapse: collapse;
    font-family: var(--mono); font-size: 0.8rem;
  }

  thead th {
    text-align: left; padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--muted); letter-spacing: 1px;
    font-size: 0.68rem; text-transform: uppercase;
  }

  tbody tr {
    border-bottom: 1px solid #111a22;
    transition: background .15s;
  }

  tbody tr:hover { background: rgba(255,255,255,0.03); }

  tbody td {
    padding: 10px 12px; color: var(--text);
  }

  .badge {
    display: inline-block; padding: 2px 10px;
    border-radius: 20px; font-size: 0.7rem;
    font-weight: 700; letter-spacing: 1px;
  }

  .badge-good { background: rgba(0,230,118,0.15); color: var(--green); border: 1px solid rgba(0,230,118,0.3); }
  .badge-fail { background: rgba(255,23,68,0.15);  color: var(--red);   border: 1px solid rgba(255,23,68,0.3); }

  .bar-bg { background: var(--border); border-radius: 4px; height: 6px; margin-top: 4px; }
  .bar-fill { height: 100%; border-radius: 4px; transition: width .4s ease; }

  .empty-state {
    text-align: center; padding: 60px 20px;
    color: var(--muted); font-family: var(--mono);
    font-size: 0.85rem; letter-spacing: 1px;
  }

  .empty-state .icon { font-size: 2.5rem; margin-bottom: 14px; opacity: .4; }

  footer {
    margin-top: 28px; text-align: center;
    font-family: var(--mono); font-size: 0.65rem;
    color: var(--muted); letter-spacing: 1px;
  }
</style>
</head>
<body>

<header>
  <div class="logo-block">
    <h1>⬡ Pill Inspection System</h1>
    <p>REAL-TIME QUALITY CONTROL DASHBOARD</p>
  </div>
  <div class="live-badge">
    <div class="pulse"></div>
    LIVE · AUTO-REFRESH 3s
  </div>
</header>

<!-- KPI Cards -->
<div class="kpi-grid" id="kpiGrid">
  <div class="kpi" style="--accent:var(--blue)">
    <div class="kpi-label">Total Batches</div>
    <div class="kpi-value" id="kTotalBatches">—</div>
    <div class="kpi-sub">inspected</div>
  </div>
  <div class="kpi" style="--accent:var(--green)">
    <div class="kpi-label">GOOD Batches</div>
    <div class="kpi-value" id="kGood" style="color:var(--green)">—</div>
    <div class="kpi-sub" id="kGoodPct">—</div>
  </div>
  <div class="kpi" style="--accent:var(--red)">
    <div class="kpi-label">FAIL Batches</div>
    <div class="kpi-value" id="kFail" style="color:var(--red)">—</div>
    <div class="kpi-sub" id="kFailPct">—</div>
  </div>
  <div class="kpi" style="--accent:var(--green)">
    <div class="kpi-label">Total Normal</div>
    <div class="kpi-value" id="kNormal" style="color:var(--green)">—</div>
    <div class="kpi-sub">pills passed</div>
  </div>
  <div class="kpi" style="--accent:var(--red)">
    <div class="kpi-label">Total Defects</div>
    <div class="kpi-value" id="kDefect" style="color:var(--red)">—</div>
    <div class="kpi-sub">pills rejected</div>
  </div>
  <div class="kpi" style="--accent:var(--yellow)">
    <div class="kpi-label">Avg Normal %</div>
    <div class="kpi-value" id="kAvgPct" style="color:var(--yellow)">—</div>
    <div class="kpi-sub">across all batches</div>
  </div>
</div>

<!-- Charts -->
<div class="charts-grid">
  <div class="panel">
    <div class="panel-title">Normal % per Batch</div>
    <div class="chart-wrap"><canvas id="lineChart"></canvas></div>
  </div>
  <div class="panel">
    <div class="panel-title">Normal vs Defect Distribution</div>
    <div class="chart-wrap"><canvas id="donutChart"></canvas></div>
  </div>
</div>

<div class="charts-grid">
  <div class="panel">
    <div class="panel-title">Pills per Batch (Normal / Defect)</div>
    <div class="chart-wrap"><canvas id="barChart"></canvas></div>
  </div>
  <div class="panel">
    <div class="panel-title">Batch Status History</div>
    <div class="chart-wrap"><canvas id="statusChart"></canvas></div>
  </div>
</div>

<!-- Batch Table -->
<div class="panel" style="margin-bottom:24px">
  <div class="panel-title">Batch Log</div>
  <div class="table-wrap" id="tableWrap">
    <div class="empty-state">
      <div class="icon">🔬</div>
      <p>Waiting for batches from main.py …</p>
    </div>
  </div>
</div>

<footer>PILL INSPECTION SYSTEM · AUTO-REFRESH EVERY 3 SECONDS · RESULTS READ FROM results.json</footer>

<script>
// ── Chart defaults ────────────────────────────────────────────
Chart.defaults.color = '#4a6070';
Chart.defaults.borderColor = '#1a2a35';
Chart.defaults.font.family = "'Share Tech Mono', monospace";

const GREEN  = '#00e676';
const RED    = '#ff1744';
const YELLOW = '#ffd600';
const BLUE   = '#00b0ff';
const MUTED  = '#1a2a35';

// ── Create charts ─────────────────────────────────────────────
const lineChart = new Chart(document.getElementById('lineChart'), {
  type: 'line',
  data: { labels: [], datasets: [{
    label: 'Normal %',
    data: [], borderColor: GREEN, backgroundColor: 'rgba(0,230,118,0.08)',
    borderWidth: 2, pointRadius: 4, pointBackgroundColor: GREEN,
    tension: 0.35, fill: true,
  }]},
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { min: 0, max: 100, grid: { color: '#1a2a35' },
           ticks: { callback: v => v + '%' }},
      x: { grid: { color: '#1a2a35' }},
    },
  }
});

const donutChart = new Chart(document.getElementById('donutChart'), {
  type: 'doughnut',
  data: {
    labels: ['Normal', 'Defect'],
    datasets: [{
      data: [0, 0],
      backgroundColor: ['rgba(0,230,118,0.8)', 'rgba(255,23,68,0.8)'],
      borderColor: ['#00e676','#ff1744'], borderWidth: 2,
      hoverOffset: 6,
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    cutout: '65%',
    plugins: { legend: { position: 'bottom', labels: { padding: 16, font: { size: 11 }}}},
  }
});

const barChart = new Chart(document.getElementById('barChart'), {
  type: 'bar',
  data: {
    labels: [],
    datasets: [
      { label: 'Normal', data: [], backgroundColor: 'rgba(0,230,118,0.75)', borderRadius: 4 },
      { label: 'Defect', data: [], backgroundColor: 'rgba(255,23,68,0.75)',  borderRadius: 4 },
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'top', labels: { padding: 12, font: { size: 11 }}}},
    scales: {
      x: { stacked: false, grid: { color: '#1a2a35' }},
      y: { stacked: false, grid: { color: '#1a2a35' }},
    },
  }
});

const statusChart = new Chart(document.getElementById('statusChart'), {
  type: 'bar',
  data: {
    labels: ['GOOD', 'FAIL'],
    datasets: [{
      label: 'Batches',
      data: [0, 0],
      backgroundColor: ['rgba(0,230,118,0.75)', 'rgba(255,23,68,0.75)'],
      borderRadius: 6,
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }},
    scales: {
      x: { grid: { color: '#1a2a35' }},
      y: { grid: { color: '#1a2a35' }, ticks: { stepSize: 1 }},
    },
  }
});

// ── Fetch & update ────────────────────────────────────────────
async function refresh() {
  let batches = [];
  try {
    const res = await fetch('/api/results');
    batches   = await res.json();
  } catch(e) { return; }

  if (!batches.length) return;

  const last20 = batches.slice(-20);

  // KPIs
  const totalBatches = batches.length;
  const goodBatches  = batches.filter(b => b.status === 'GOOD').length;
  const failBatches  = totalBatches - goodBatches;
  const totalNormal  = batches.reduce((s,b) => s + b.normal, 0);
  const totalDefect  = batches.reduce((s,b) => s + b.defect, 0);
  const avgPct       = batches.reduce((s,b) => s + b.normal_pct, 0) / totalBatches;

  document.getElementById('kTotalBatches').textContent = totalBatches;
  document.getElementById('kGood').textContent         = goodBatches;
  document.getElementById('kGoodPct').textContent      = `${((goodBatches/totalBatches)*100).toFixed(1)}% of batches`;
  document.getElementById('kFail').textContent         = failBatches;
  document.getElementById('kFailPct').textContent      = `${((failBatches/totalBatches)*100).toFixed(1)}% of batches`;
  document.getElementById('kNormal').textContent       = totalNormal.toLocaleString();
  document.getElementById('kDefect').textContent       = totalDefect.toLocaleString();
  document.getElementById('kAvgPct').textContent       = avgPct.toFixed(1) + '%';

  // Line chart
  lineChart.data.labels   = last20.map(b => `#${b.batch_id}`);
  lineChart.data.datasets[0].data = last20.map(b => b.normal_pct);
  lineChart.update('none');

  // Donut
  donutChart.data.datasets[0].data = [totalNormal, totalDefect];
  donutChart.update('none');

  // Bar chart
  barChart.data.labels = last20.map(b => `#${b.batch_id}`);
  barChart.data.datasets[0].data = last20.map(b => b.normal);
  barChart.data.datasets[1].data = last20.map(b => b.defect);
  barChart.update('none');

  // Status chart
  statusChart.data.datasets[0].data = [goodBatches, failBatches];
  statusChart.update('none');

  // Table
  const sorted = [...batches].reverse();
  const rows   = sorted.map(b => {
    const pct   = b.normal_pct;
    const color = pct >= 75 ? GREEN : RED;
    const badge = b.status === 'GOOD'
      ? '<span class="badge badge-good">GOOD</span>'
      : '<span class="badge badge-fail">FAIL</span>';
    return `
      <tr>
        <td>#${b.batch_id}</td>
        <td>${b.timestamp}</td>
        <td>${b.total}</td>
        <td style="color:${GREEN}">${b.normal}</td>
        <td style="color:${RED}">${b.defect}</td>
        <td>
          <div style="color:${color};font-weight:700">${pct.toFixed(1)}%</div>
          <div class="bar-bg"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
        </td>
        <td>${badge}</td>
      </tr>`;
  }).join('');

  document.getElementById('tableWrap').innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Batch</th><th>Time</th><th>Total</th>
          <th>Normal</th><th>Defect</th><th>Normal %</th><th>Status</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/results")
def api_results():
    path = Path(RESULTS_FILE)
    if not path.exists():
        return jsonify([])
    try:
        data = json.loads(path.read_text())
        return jsonify(data)
    except (json.JSONDecodeError, ValueError):
        return jsonify([])


@app.route("/api/latest")
def api_latest():
    path = Path(RESULTS_FILE)
    if not path.exists():
        return jsonify({})
    try:
        data = json.loads(path.read_text())
        return jsonify(data[-1] if data else {})
    except (json.JSONDecodeError, ValueError):
        return jsonify({})


# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n  ┌─────────────────────────────────────────┐")
    print("  │   Pill Inspection Dashboard             │")
    print("  │   Open → http://127.0.0.1:5000          │")
    print("  │   Reads → results.json (auto-refresh)   │")
    print("  └─────────────────────────────────────────┘\n")
    app.run(debug=False, port=5000)
