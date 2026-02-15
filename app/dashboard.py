"""실시간 트레이딩 대시보드 — HTML 쉘 + JS 폴링"""

from app.report_theme import wrap_html

_DASHBOARD_CSS = """
/* --- 대시보드 레이아웃 --- */
header { padding: 24px 0 12px; display: flex; justify-content: space-between; align-items: center; }
header h1 { font-size: 22px; }
#last-update { color: #888; font-size: 12px; }

.cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.card { background: #1a1d27; border-radius: 10px; padding: 16px; }
.card-label { font-size: 12px; color: #888; margin-bottom: 4px; }
.card-value { font-size: 24px; font-weight: 700; color: #fff; }
.card-sub { font-size: 12px; margin-top: 4px; }

.status-badge { display: inline-block; padding: 2px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; }
.status-running { background: #065f46; color: #10b981; }
.status-stopped { background: #7f1d1d; color: #ef4444; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.section { margin: 12px 0; }
.section h2 { font-size: 15px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px; }

#pnl-chart-wrap { height: 240px; position: relative; }

table { font-size: 12px; }
th { padding: 8px 10px; font-size: 11px; }
td { padding: 7px 10px; }

.empty-msg { color: #555; font-size: 13px; text-align: center; padding: 32px; }

/* --- 반응형 --- */
@media (max-width: 900px) {
  .cards { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .cards { grid-template-columns: 1fr; }
  .container { padding: 12px; }
}
""".strip()

_BODY_HTML = """
<div class="container">
  <header>
    <h1>Quantum Trading Dashboard</h1>
    <span id="last-update">--</span>
  </header>

  <!-- 요약 카드 -->
  <div class="cards">
    <div class="card">
      <div class="card-label">엔진 상태</div>
      <div class="card-value"><span id="status-badge" class="status-badge status-stopped">STOPPED</span></div>
      <div class="card-sub" id="engine-meta">--</div>
    </div>
    <div class="card">
      <div class="card-label">전략</div>
      <div class="card-value" id="strategy-name">--</div>
      <div class="card-sub" id="strategy-detail">--</div>
    </div>
    <div class="card">
      <div class="card-label">예수금</div>
      <div class="card-value" id="deposit-value">--</div>
      <div class="card-sub" id="deposit-detail">--</div>
    </div>
    <div class="card">
      <div class="card-label">평가손익</div>
      <div class="card-value" id="pnl-value">--</div>
      <div class="card-sub" id="pnl-detail">--</div>
    </div>
  </div>

  <!-- 포지션 테이블 -->
  <div class="section">
    <h2>보유 포지션</h2>
    <table>
      <thead>
        <tr>
          <th style="text-align:left">종목</th>
          <th>수량</th>
          <th>평균가</th>
          <th>현재가</th>
          <th>평가금액</th>
          <th>손익</th>
          <th>수익률</th>
        </tr>
      </thead>
      <tbody id="positions-body">
        <tr><td colspan="7" class="empty-msg">데이터 로딩 중...</td></tr>
      </tbody>
    </table>
  </div>

  <!-- P&L 추이 차트 -->
  <div class="section">
    <h2>당일 평가손익 추이</h2>
    <div id="pnl-chart-wrap">
      <canvas id="pnl-chart"></canvas>
    </div>
  </div>

  <!-- 시그널 + 주문 -->
  <div class="two-col">
    <div class="section">
      <h2>최근 시그널 <span style="font-size:11px;color:#555;font-weight:400">(20건)</span></h2>
      <table>
        <thead>
          <tr>
            <th style="text-align:left">시각</th>
            <th style="text-align:left">종목</th>
            <th>신호</th>
            <th>가격</th>
            <th>단기MA</th>
            <th>장기MA</th>
          </tr>
        </thead>
        <tbody id="signals-body">
          <tr><td colspan="6" class="empty-msg">--</td></tr>
        </tbody>
      </table>
    </div>
    <div class="section">
      <h2>최근 주문 <span style="font-size:11px;color:#555;font-weight:400">(20건)</span></h2>
      <table>
        <thead>
          <tr>
            <th style="text-align:left">시각</th>
            <th style="text-align:left">종목</th>
            <th>매수/매도</th>
            <th>수량</th>
            <th>사유</th>
          </tr>
        </thead>
        <tbody id="orders-body">
          <tr><td colspan="5" class="empty-msg">--</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <footer>Quantum Trading Platform &mdash; Dashboard</footer>
</div>
""".strip()

_DASHBOARD_JS = r"""
/* ---------- state ---------- */
let pnlHistory = [];
let pnlChart = null;

/* ---------- helpers ---------- */
function fmt(n) {
  if (n == null) return '--';
  return Number(n).toLocaleString('ko-KR', {maximumFractionDigits: 0});
}
function fmtPct(n) {
  if (n == null) return '--';
  const sign = n >= 0 ? '+' : '';
  return sign + Number(n).toFixed(2) + '%';
}
function fmtTime(ts) {
  if (!ts) return '--';
  const d = new Date(ts);
  return d.toLocaleTimeString('ko-KR', {hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false});
}
function pnlClass(n) { return n >= 0 ? 'positive' : 'negative'; }

function signalBadge(sig) {
  const cls = sig === 'BUY' ? 'buy-badge' : sig === 'SELL' ? 'sell-badge' : 'hold-badge';
  return `<span class="${cls}">${sig}</span>`;
}
function reasonBadge(reason) {
  if (!reason) return '';
  const colors = {signal:'#2563eb', stop_loss:'#dc2626', trailing_stop:'#ea580c', max_holding:'#d97706', force_close:'#7c3aed'};
  const bg = colors[reason] || '#555';
  return `<span class="reason-badge" style="background:${bg}">${reason}</span>`;
}

/* ---------- fetch wrappers ---------- */
async function safeFetch(url) {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

/* ---------- status polling (5s) ---------- */
async function fetchStatus() {
  const data = await safeFetch('/trading/status');
  if (!data) return;
  updateStatusUI(data);
  updateSignalsTable(data.recent_signals || []);
  updateOrdersTable(data.recent_orders || []);
  document.getElementById('last-update').textContent = '갱신 ' + fmtTime(new Date().toISOString());
}

function updateStatusUI(data) {
  const badge = document.getElementById('status-badge');
  const running = data.status === 'RUNNING';
  badge.textContent = data.status;
  badge.className = 'status-badge ' + (running ? 'status-running' : 'status-stopped');

  const parts = [];
  if (data.active_market) parts.push(data.active_market);
  if (data.current_regime) parts.push(data.current_regime);
  if (data.loop_count) parts.push('tick ' + data.loop_count);
  document.getElementById('engine-meta').textContent = parts.join(' · ') || '--';
}

function updateSignalsTable(signals) {
  const tbody = document.getElementById('signals-body');
  if (!signals.length) { tbody.innerHTML = '<tr><td colspan="6" class="empty-msg">시그널 없음</td></tr>'; return; }
  tbody.innerHTML = signals.slice(0, 20).map(s => `<tr>
    <td style="text-align:left">${fmtTime(s.timestamp)}</td>
    <td style="text-align:left">${s.symbol}</td>
    <td>${signalBadge(s.signal)}</td>
    <td>${fmt(s.current_price)}</td>
    <td>${fmt(s.short_ma)}</td>
    <td>${fmt(s.long_ma)}</td>
  </tr>`).join('');
}

function updateOrdersTable(orders) {
  const tbody = document.getElementById('orders-body');
  if (!orders.length) { tbody.innerHTML = '<tr><td colspan="5" class="empty-msg">주문 없음</td></tr>'; return; }
  tbody.innerHTML = orders.slice(0, 20).map(o => `<tr>
    <td style="text-align:left">${fmtTime(o.timestamp)}</td>
    <td style="text-align:left">${o.symbol}</td>
    <td>${o.side === 'buy' ? '<span class="buy-badge">매수</span>' : '<span class="sell-badge">매도</span>'}</td>
    <td>${o.quantity}</td>
    <td>${reasonBadge(o.reason)}</td>
  </tr>`).join('');
}

/* ---------- positions polling (10s) ---------- */
async function fetchPositions() {
  const data = await safeFetch('/trading/positions');
  if (!data) return;
  updatePositionsUI(data);
  updateAccountSummary(data);
  recordPnlSnapshot(data);
  updatePnlChart();
}

function updatePositionsUI(data) {
  const tbody = document.getElementById('positions-body');
  const rows = [];
  for (const market of ['domestic', 'us']) {
    const positions = (data[market] && data[market].positions) || [];
    for (const p of positions) {
      if (!p.quantity) continue;
      rows.push(`<tr>
        <td style="text-align:left"><div class="stock-cell"><span class="stock-code">${p.symbol}</span><span class="stock-name">${p.name || ''}</span></div></td>
        <td>${fmt(p.quantity)}</td>
        <td>${fmt(p.avg_price)}</td>
        <td>${fmt(p.current_price)}</td>
        <td>${fmt(p.eval_amount)}</td>
        <td class="${pnlClass(p.profit_loss)}">${fmt(p.profit_loss)}</td>
        <td class="${pnlClass(p.profit_loss_rate)}">${fmtPct(p.profit_loss_rate)}</td>
      </tr>`);
    }
  }
  tbody.innerHTML = rows.length ? rows.join('') : '<tr><td colspan="7" class="empty-msg">보유 포지션 없음</td></tr>';
}

function updateAccountSummary(data) {
  let deposit = 0, totalPnl = 0, totalPnlRate = 0, totalEval = 0;
  for (const market of ['domestic', 'us']) {
    const s = (data[market] && data[market].summary) || {};
    deposit += (s.deposit || 0);
    totalPnl += (s.eval_profit_loss || 0);
    totalEval += (s.total_eval || 0);
  }
  if (totalEval > 0 && deposit > 0) totalPnlRate = (totalPnl / (totalEval - totalPnl + deposit)) * 100;

  document.getElementById('deposit-value').textContent = fmt(deposit);
  document.getElementById('deposit-detail').textContent = '총평가 ' + fmt(totalEval);

  const pnlEl = document.getElementById('pnl-value');
  pnlEl.textContent = (totalPnl >= 0 ? '+' : '') + fmt(totalPnl);
  pnlEl.className = 'card-value ' + pnlClass(totalPnl);
  document.getElementById('pnl-detail').innerHTML = `<span class="${pnlClass(totalPnlRate)}">${fmtPct(totalPnlRate)}</span>`;
}

/* ---------- P&L 추이 ---------- */
function recordPnlSnapshot(data) {
  let totalPnl = 0;
  for (const market of ['domestic', 'us']) {
    const s = (data[market] && data[market].summary) || {};
    totalPnl += (s.eval_profit_loss || 0);
  }
  const now = new Date();
  const label = now.toLocaleTimeString('ko-KR', {hour:'2-digit', minute:'2-digit', hour12:false});

  if (pnlHistory.length && pnlHistory[pnlHistory.length - 1].label === label) {
    pnlHistory[pnlHistory.length - 1].value = totalPnl;
  } else {
    pnlHistory.push({label, value: totalPnl});
  }
  if (pnlHistory.length > 200) pnlHistory.shift();
}

function updatePnlChart() {
  if (!pnlHistory.length) return;
  const labels = pnlHistory.map(p => p.label);
  const values = pnlHistory.map(p => p.value);
  const lastVal = values[values.length - 1];
  const color = lastVal >= 0 ? '#22c55e' : '#ef4444';

  if (!pnlChart) {
    const ctx = document.getElementById('pnl-chart').getContext('2d');
    pnlChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          data: values,
          borderColor: color,
          backgroundColor: color + '18',
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: '#666', maxTicksLimit: 12 }, grid: { color: '#252830' } },
          y: { ticks: { color: '#666', callback: v => fmt(v) }, grid: { color: '#252830' } },
        }
      }
    });
  } else {
    pnlChart.data.labels = labels;
    pnlChart.data.datasets[0].data = values;
    pnlChart.data.datasets[0].borderColor = color;
    pnlChart.data.datasets[0].backgroundColor = color + '18';
    pnlChart.update('none');
  }
}

/* ---------- strategy (1회) ---------- */
async function fetchStrategy() {
  const data = await safeFetch('/trading/strategy');
  if (!data) return;
  document.getElementById('strategy-name').textContent = data.strategy_type || '--';
  const parts = [];
  if (data.use_minute_chart) parts.push('분봉');
  else parts.push('일봉');
  if (data.use_advanced_strategy) parts.push('RSI+OBV');
  if (data.stop_loss_pct) parts.push('손절 ' + data.stop_loss_pct + '%');
  if (data.trailing_stop_pct) parts.push('트레일링 ' + data.trailing_stop_pct + '%');
  document.getElementById('strategy-detail').textContent = parts.join(' · ') || '--';
}

/* ---------- init ---------- */
document.addEventListener('DOMContentLoaded', () => {
  fetchStatus();
  fetchPositions();
  fetchStrategy();
  setInterval(fetchStatus, 5000);
  setInterval(fetchPositions, 10000);
});
""".strip()


def build_dashboard_html() -> str:
    """대시보드 HTML 반환 — 서버 데이터 주입 없이 JS 폴링으로 채움"""
    return wrap_html(
        title="Trading Dashboard",
        body=_BODY_HTML,
        extra_css=_DASHBOARD_CSS,
        extra_js=_DASHBOARD_JS,
        include_chartjs=True,
    )
