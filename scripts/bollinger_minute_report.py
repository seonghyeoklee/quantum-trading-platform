#!/usr/bin/env python
"""볼린저밴드 1분봉 백테스트 — 장중 단타 시각화 리포트"""

import json
import os
import sys
import webbrowser

import yfinance as yf

from app.models import ChartData
from app.trading.backtest import run_bollinger_backtest
from app.trading.strategy import compute_bollinger_bands

SYMBOLS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("034020", "두산에너빌리티"),
    ("298040", "효성중공업"),
]

CAPITAL_PER_STOCK = 10_000_000

# === 실제 엔진 설정 그대로 ===
PERIOD = 20
NUM_STD = 2.0
MAX_HOLD_BARS = 9999          # 보유기간 제한 없음 (강제청산이 대체)
MAX_DAILY_TRADES = 5
FORCE_CLOSE = 1510            # 15:10 이후 강제 청산
NO_BUY_AFTER = 1500           # 15:00 이후 매수 금지
ACTIVE_WINDOWS = [(930, 1100), (1400, 1500)]
TARGET_ORDER = 1_000_000      # 동적 수량: 100만원/현재가
MIN_QTY = 1
MAX_QTY = 50


def fetch_minute_chart(ticker: str) -> list[ChartData]:
    """yfinance 1분봉 → ChartData 리스트."""
    df = yf.download(ticker, period="7d", interval="1m", progress=False)
    if df.empty:
        return []

    if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
        df = df.droplevel(level=1, axis=1)

    result = []
    for dt, row in df.iterrows():
        # KST 변환 (UTC+9)
        kst = dt.tz_convert("Asia/Seoul") if dt.tzinfo else dt
        result.append(
            ChartData(
                date=kst.strftime("%Y-%m-%d %H:%M"),
                open=round(row["Open"]),
                high=round(row["High"]),
                low=round(row["Low"]),
                close=round(row["Close"]),
                volume=round(row["Volume"]),
            )
        )
    return result


def build_stock_data(code, name, chart, result, period, num_std):
    closes = [float(c.close) for c in chart]
    bands = compute_bollinger_bands(closes, period, num_std)

    dates = [c.date for c in chart]
    uppers = [b[0] for b in bands]
    middles = [b[1] for b in bands]
    lowers = [b[2] for b in bands]

    buys = [{"date": t.date, "price": t.price, "qty": t.quantity}
            for t in result.trades if t.side == "buy"]
    sells = [{"date": t.date, "price": t.price, "qty": t.quantity}
             for t in result.trades if t.side == "sell"]

    trade_pairs = []
    buy_stack = []
    for t in result.trades:
        if t.side == "buy":
            buy_stack.append(t)
        elif t.side == "sell" and buy_stack:
            b = buy_stack.pop(0)
            pnl = (t.price - b.price) * b.quantity
            pnl_pct = (t.price - b.price) / b.price * 100
            hold_bars = 0
            # 보유 기간(봉 수) 계산
            for i, c in enumerate(chart):
                if c.date == b.date:
                    for j in range(i, len(chart)):
                        if chart[j].date == t.date:
                            hold_bars = j - i
                            break
                    break
            trade_pairs.append({
                "buy_date": b.date,
                "buy_price": b.price,
                "sell_date": t.date,
                "sell_price": t.price,
                "qty": b.quantity,
                "pnl": pnl,
                "pnl_pct": round(pnl_pct, 2),
                "hold_mins": hold_bars,
            })

    return {
        "code": code,
        "name": name,
        "dates": dates,
        "closes": closes,
        "uppers": uppers,
        "middles": middles,
        "lowers": lowers,
        "buys": buys,
        "sells": sells,
        "equity": result.equity_curve,
        "trade_pairs": trade_pairs,
        "summary": {
            "total_return_pct": result.total_return_pct,
            "buy_and_hold_pct": result.buy_and_hold_pct,
            "trade_count": result.trade_count,
            "win_rate": result.win_rate,
            "max_drawdown_pct": result.max_drawdown_pct,
            "sharpe_ratio": result.sharpe_ratio,
        },
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>볼린저밴드 1분봉 백테스트 리포트</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, 'Pretendard', sans-serif; background: #0f1117; color: #e0e0e0; padding: 20px; }
  h1 { text-align: center; margin: 20px 0; color: #fff; font-size: 24px; }
  .params { text-align: center; color: #888; margin-bottom: 30px; font-size: 14px; }
  .stock-section { background: #1a1d28; border-radius: 12px; padding: 20px; margin-bottom: 30px; }
  .stock-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
  .stock-name { font-size: 20px; font-weight: bold; color: #fff; }
  .stock-name span { color: #888; font-size: 14px; font-weight: normal; margin-left: 8px; }
  .metrics { display: flex; gap: 20px; flex-wrap: wrap; }
  .metric { background: #252833; padding: 10px 16px; border-radius: 8px; min-width: 100px; }
  .metric .label { font-size: 11px; color: #888; margin-bottom: 4px; }
  .metric .value { font-size: 18px; font-weight: bold; }
  .metric .value.pos { color: #f44336; }
  .metric .value.neg { color: #2196f3; }
  .chart-container { position: relative; margin: 15px 0; }
  canvas { width: 100% !important; background: #1e2130; border-radius: 8px; }
  .trade-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
  .trade-table th { background: #252833; padding: 8px 12px; text-align: left; color: #aaa; font-weight: normal; }
  .trade-table td { padding: 8px 12px; border-bottom: 1px solid #252833; }
  .trade-table tr:hover { background: #252833; }
  .pnl-pos { color: #f44336; }
  .pnl-neg { color: #2196f3; }
  .toggle-btn { background: #252833; border: 1px solid #333; color: #ccc; padding: 6px 14px;
    border-radius: 6px; cursor: pointer; font-size: 12px; margin-top: 10px; }
  .toggle-btn:hover { background: #333; }
  .legend { display: flex; gap: 16px; margin: 8px 0; font-size: 12px; color: #aaa; }
  .legend-item { display: flex; align-items: center; gap: 4px; }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
  .portfolio-summary { background: #1a1d28; border-radius: 12px; padding: 24px; margin-bottom: 30px; }
  .portfolio-summary h2 { color: #fff; margin-bottom: 16px; font-size: 18px; }
  .day-nav { display: flex; gap: 8px; margin: 10px 0; flex-wrap: wrap; }
  .day-btn { background: #252833; border: 1px solid #333; color: #ccc; padding: 4px 12px;
    border-radius: 4px; cursor: pointer; font-size: 12px; }
  .day-btn:hover, .day-btn.active { background: #444; color: #fff; }
</style>
</head>
<body>

<h1>볼린저밴드 1분봉 단타 백테스트</h1>
<div class="params">
  최근 7거래일 1분봉 (실제 엔진 동일 조건) | BB(__BB_PERIOD__분, σ=__BB_STD__), __BB_HOLD__, 수량=__ORDER_RATIO__ | 종목당 __CAPITAL__원
</div>

<div class="portfolio-summary">
  <h2>포트폴리오 합산</h2>
  <div class="metrics" id="portfolio-metrics"></div>
</div>

<div id="stock-sections"></div>

<script>
const DATA = __JSON_DATA__;
const CAPITAL = __CAPITAL_RAW__;

// 포트폴리오 합산
let totalPnl = 0, totalTrades = 0, winCounts = 0, totalPairs = 0;
DATA.forEach(s => {
  totalPnl += (s.equity[s.equity.length-1] - CAPITAL);
  totalTrades += s.summary.trade_count;
  s.trade_pairs.forEach(p => { totalPairs++; if (p.pnl > 0) winCounts++; });
});
const totalRet = (totalPnl / (CAPITAL * DATA.length) * 100).toFixed(2);
const totalWin = totalPairs > 0 ? (winCounts / totalPairs * 100).toFixed(1) : '0.0';

document.getElementById('portfolio-metrics').innerHTML = `
  <div class="metric"><div class="label">총 투자금</div><div class="value">${(CAPITAL*DATA.length).toLocaleString()}원</div></div>
  <div class="metric"><div class="label">총 손익</div><div class="value ${totalPnl>=0?'pos':'neg'}">${totalPnl>=0?'+':''}${Math.round(totalPnl).toLocaleString()}원</div></div>
  <div class="metric"><div class="label">총 수익률</div><div class="value ${totalRet>=0?'pos':'neg'}">${totalRet>=0?'+':''}${totalRet}%</div></div>
  <div class="metric"><div class="label">총 거래</div><div class="value">${totalTrades}건</div></div>
  <div class="metric"><div class="label">승률</div><div class="value">${totalWin}%</div></div>
`;

const container = document.getElementById('stock-sections');

DATA.forEach((stock, idx) => {
  const s = stock.summary;
  const pnl = stock.equity[stock.equity.length-1] - CAPITAL;

  // 날짜별 그룹핑
  const dayMap = {};
  stock.dates.forEach((d, i) => {
    const day = d.split(' ')[0];
    if (!dayMap[day]) dayMap[day] = [];
    dayMap[day].push(i);
  });
  const days = Object.keys(dayMap).sort();

  const section = document.createElement('div');
  section.className = 'stock-section';
  section.innerHTML = `
    <div class="stock-header">
      <div class="stock-name">${stock.name}<span>${stock.code}</span></div>
    </div>
    <div class="metrics">
      <div class="metric"><div class="label">수익률</div><div class="value ${s.total_return_pct>=0?'pos':'neg'}">${s.total_return_pct>=0?'+':''}${s.total_return_pct}%</div></div>
      <div class="metric"><div class="label">손익</div><div class="value ${pnl>=0?'pos':'neg'}">${pnl>=0?'+':''}${Math.round(pnl).toLocaleString()}원</div></div>
      <div class="metric"><div class="label">B&H</div><div class="value">${s.buy_and_hold_pct>=0?'+':''}${s.buy_and_hold_pct}%</div></div>
      <div class="metric"><div class="label">거래</div><div class="value">${s.trade_count}건</div></div>
      <div class="metric"><div class="label">승률</div><div class="value">${s.win_rate}%</div></div>
      <div class="metric"><div class="label">MDD</div><div class="value neg">-${s.max_drawdown_pct}%</div></div>
    </div>
    <div class="legend">
      <div class="legend-item"><span class="legend-dot" style="background:#666"></span>종가</div>
      <div class="legend-item"><span class="legend-dot" style="background:rgba(255,152,0,0.5)"></span>볼린저밴드</div>
      <div class="legend-item"><span class="legend-dot" style="background:#f44336"></span>매수</div>
      <div class="legend-item"><span class="legend-dot" style="background:#2196f3"></span>매도</div>
    </div>
    <div class="day-nav" id="daynav-${idx}">
      <button class="day-btn active" onclick="showDay(${idx},-1,this)">전체</button>
      ${days.map((d,di) => `<button class="day-btn" onclick="showDay(${idx},${di},this)">${d.slice(5)}</button>`).join('')}
    </div>
    <div class="chart-container">
      <canvas id="price-${idx}" height="320"></canvas>
    </div>
    <div class="chart-container">
      <canvas id="equity-${idx}" height="140"></canvas>
    </div>
    <button class="toggle-btn" onclick="toggleTable('table-${idx}')">거래 내역 보기/숨기기</button>
    <div id="table-${idx}" style="display:none">
      <table class="trade-table">
        <thead><tr><th>#</th><th>매수시각</th><th>매수가</th><th>매도시각</th><th>매도가</th><th>수량</th><th>보유(분)</th><th>손익</th><th>수익률</th></tr></thead>
        <tbody>
          ${stock.trade_pairs.map((p, i) => `
            <tr>
              <td>${i+1}</td>
              <td>${p.buy_date}</td>
              <td>${p.buy_price.toLocaleString()}</td>
              <td>${p.sell_date}</td>
              <td>${p.sell_price.toLocaleString()}</td>
              <td>${p.qty}</td>
              <td>${p.hold_mins}분</td>
              <td class="${p.pnl>=0?'pnl-pos':'pnl-neg'}">${p.pnl>=0?'+':''}${p.pnl.toLocaleString()}</td>
              <td class="${p.pnl_pct>=0?'pnl-pos':'pnl-neg'}">${p.pnl_pct>=0?'+':''}${p.pnl_pct}%</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
  container.appendChild(section);

  // 저장: 날짜별 인덱스 범위
  stock._dayMap = dayMap;
  stock._days = days;
  stock._currentView = {start: 0, end: stock.dates.length - 1};

  drawAll(idx, stock);
});

function showDay(idx, dayIdx, btn) {
  const stock = DATA[idx];
  // 버튼 활성화
  const nav = document.getElementById('daynav-'+idx);
  nav.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  if (dayIdx === -1) {
    stock._currentView = {start: 0, end: stock.dates.length - 1};
  } else {
    const day = stock._days[dayIdx];
    const indices = stock._dayMap[day];
    stock._currentView = {start: indices[0], end: indices[indices.length-1]};
  }
  drawAll(idx, stock);
}

function drawAll(idx, stock) {
  drawPriceChart('price-'+idx, stock, stock._currentView);
  drawEquityChart('equity-'+idx, stock, stock._currentView);
}

function toggleTable(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function drawPriceChart(canvasId, stock, view) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height;
  const pad = {t:20, b:35, l:70, r:20};
  const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;

  const s = view.start, e = view.end;
  const len = e - s + 1;

  // 범위 내 min/max
  let minV = Infinity, maxV = -Infinity;
  for (let i = s; i <= e; i++) {
    const c = stock.closes[i];
    if (c < minV) minV = c;
    if (c > maxV) maxV = c;
    if (stock.uppers[i] !== null) { if (stock.uppers[i] > maxV) maxV = stock.uppers[i]; }
    if (stock.lowers[i] !== null) { if (stock.lowers[i] < minV) minV = stock.lowers[i]; }
  }
  const margin = (maxV - minV) * 0.05 || 100;
  minV -= margin; maxV += margin;

  function x(i) { return pad.l + ((i - s) / Math.max(len-1,1)) * cW; }
  function y(v) { return pad.t + (1 - (v - minV) / (maxV - minV)) * cH; }

  // 볼린저밴드 영역
  ctx.beginPath();
  let started = false;
  for (let i = s; i <= e; i++) {
    if (stock.uppers[i] !== null) {
      if (!started) { ctx.moveTo(x(i), y(stock.uppers[i])); started = true; }
      else ctx.lineTo(x(i), y(stock.uppers[i]));
    }
  }
  for (let i = e; i >= s; i--) {
    if (stock.lowers[i] !== null) ctx.lineTo(x(i), y(stock.lowers[i]));
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(255,152,0,0.08)'; ctx.fill();

  // 밴드 라인
  [['uppers','rgba(255,152,0,0.4)'], ['lowers','rgba(255,152,0,0.4)']].forEach(([key, color]) => {
    ctx.beginPath(); started = false;
    for (let i = s; i <= e; i++) {
      if (stock[key][i] !== null) {
        if (!started) { ctx.moveTo(x(i), y(stock[key][i])); started = true; }
        else ctx.lineTo(x(i), y(stock[key][i]));
      }
    }
    ctx.strokeStyle = color; ctx.lineWidth = 1; ctx.stroke();
  });

  // 중간밴드
  ctx.beginPath(); started = false;
  for (let i = s; i <= e; i++) {
    if (stock.middles[i] !== null) {
      if (!started) { ctx.moveTo(x(i), y(stock.middles[i])); started = true; }
      else ctx.lineTo(x(i), y(stock.middles[i]));
    }
  }
  ctx.strokeStyle = 'rgba(255,152,0,0.25)'; ctx.lineWidth = 1; ctx.setLineDash([4,4]); ctx.stroke(); ctx.setLineDash([]);

  // 종가
  ctx.beginPath();
  ctx.moveTo(x(s), y(stock.closes[s]));
  for (let i = s+1; i <= e; i++) ctx.lineTo(x(i), y(stock.closes[i]));
  ctx.strokeStyle = '#888'; ctx.lineWidth = 1.5; ctx.stroke();

  // 날짜→인덱스 매핑
  const dateIndex = {};
  stock.dates.forEach((d, i) => { dateIndex[d] = i; });

  // 매수/매도 마커
  stock.buys.forEach(b => {
    const i = dateIndex[b.date];
    if (i === undefined || i < s || i > e) return;
    const bx = x(i), by = y(b.price);
    ctx.beginPath(); ctx.moveTo(bx, by+4); ctx.lineTo(bx-6, by+14); ctx.lineTo(bx+6, by+14); ctx.closePath();
    ctx.fillStyle = '#f44336'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(bx, pad.t); ctx.lineTo(bx, pad.t+cH);
    ctx.strokeStyle = 'rgba(244,67,54,0.25)'; ctx.lineWidth = 1; ctx.stroke();
    // 가격 라벨
    ctx.fillStyle = '#f44336'; ctx.font = '10px monospace'; ctx.textAlign = 'center';
    ctx.fillText(b.price.toLocaleString(), bx, by + 26);
  });

  stock.sells.forEach(sl => {
    const i = dateIndex[sl.date];
    if (i === undefined || i < s || i > e) return;
    const sx = x(i), sy = y(sl.price);
    ctx.beginPath(); ctx.moveTo(sx, sy-4); ctx.lineTo(sx-6, sy-14); ctx.lineTo(sx+6, sy-14); ctx.closePath();
    ctx.fillStyle = '#2196f3'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(sx, pad.t); ctx.lineTo(sx, pad.t+cH);
    ctx.strokeStyle = 'rgba(33,150,243,0.25)'; ctx.lineWidth = 1; ctx.stroke();
    ctx.fillStyle = '#2196f3'; ctx.font = '10px monospace'; ctx.textAlign = 'center';
    ctx.fillText(sl.price.toLocaleString(), sx, sy - 18);
  });

  // Y축
  ctx.fillStyle = '#666'; ctx.font = '11px monospace'; ctx.textAlign = 'right';
  const steps = 5;
  for (let i = 0; i <= steps; i++) {
    const v = minV + (maxV - minV) * i / steps;
    const yy = y(v);
    ctx.fillText(Math.round(v).toLocaleString(), pad.l - 6, yy + 4);
    ctx.beginPath(); ctx.moveTo(pad.l, yy); ctx.lineTo(W - pad.r, yy);
    ctx.strokeStyle = '#252833'; ctx.lineWidth = 1; ctx.stroke();
  }

  // X축
  ctx.textAlign = 'center'; ctx.fillStyle = '#555'; ctx.font = '10px monospace';
  const xSteps = Math.min(8, len-1);
  for (let i = 0; i <= xSteps; i++) {
    const di = s + Math.round(i * (len-1) / xSteps);
    const d = stock.dates[di];
    // 시:분 표시 (날짜 뷰) or 날짜+시:분 (전체 뷰)
    const label = len > 400 ? d.slice(5) : d.slice(11);
    ctx.fillText(label, x(di), H - 8);
  }
}

function drawEquityChart(canvasId, stock, view) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height;
  const pad = {t:15, b:25, l:70, r:20};
  const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;

  const s = view.start, e = view.end;
  const len = e - s + 1;

  let minE = Infinity, maxE = -Infinity;
  for (let i = s; i <= e; i++) {
    if (stock.equity[i] < minE) minE = stock.equity[i];
    if (stock.equity[i] > maxE) maxE = stock.equity[i];
  }
  const margin = (maxE - minE) * 0.05 || 10000;
  minE -= margin; maxE += margin;

  function x(i) { return pad.l + ((i - s) / Math.max(len-1,1)) * cW; }
  function y(v) { return pad.t + (1 - (v - minE) / (maxE - minE)) * cH; }

  // 기준선
  if (CAPITAL >= minE && CAPITAL <= maxE) {
    ctx.beginPath(); ctx.moveTo(pad.l, y(CAPITAL)); ctx.lineTo(W-pad.r, y(CAPITAL));
    ctx.strokeStyle = '#444'; ctx.lineWidth = 1; ctx.setLineDash([4,4]); ctx.stroke(); ctx.setLineDash([]);
  }

  // fill
  ctx.beginPath();
  ctx.moveTo(x(s), y(CAPITAL));
  for (let i = s; i <= e; i++) ctx.lineTo(x(i), y(stock.equity[i]));
  ctx.lineTo(x(e), y(CAPITAL));
  ctx.closePath();
  const above = stock.equity[e] >= CAPITAL;
  ctx.fillStyle = above ? 'rgba(244,67,54,0.1)' : 'rgba(33,150,243,0.1)';
  ctx.fill();

  // line
  ctx.beginPath();
  ctx.moveTo(x(s), y(stock.equity[s]));
  for (let i = s+1; i <= e; i++) ctx.lineTo(x(i), y(stock.equity[i]));
  ctx.strokeStyle = above ? '#f44336' : '#2196f3'; ctx.lineWidth = 1.5; ctx.stroke();

  // Y축
  ctx.fillStyle = '#666'; ctx.font = '11px monospace'; ctx.textAlign = 'right';
  [minE, CAPITAL, maxE].forEach(v => {
    if (v >= minE && v <= maxE)
      ctx.fillText((Math.round(v/10000)).toLocaleString()+'만', pad.l-6, y(v)+4);
  });

  ctx.fillStyle = '#888'; ctx.font = '11px sans-serif'; ctx.textAlign = 'left';
  ctx.fillText('자산 곡선', pad.l + 4, pad.t + 12);
}
</script>
</body>
</html>"""


def main():
    stocks_data = []

    print("1분봉 데이터 로드 중... (실제 엔진 동일 조건)")
    for code, name in SYMBOLS:
        ticker = f"{code}.KS"
        chart = fetch_minute_chart(ticker)
        if not chart:
            print(f"  {code} {name}: 데이터 없음", file=sys.stderr)
            continue

        result = run_bollinger_backtest(
            chart=chart,
            initial_capital=CAPITAL_PER_STOCK,
            period=PERIOD,
            num_std=NUM_STD,
            max_holding_days=MAX_HOLD_BARS,
            max_daily_trades=MAX_DAILY_TRADES,
            force_close_minute=FORCE_CLOSE,
            no_new_buy_minute=NO_BUY_AFTER,
            active_windows=ACTIVE_WINDOWS,
            target_order_amount=TARGET_ORDER,
            min_quantity=MIN_QTY,
            max_quantity=MAX_QTY,
        )

        sd = build_stock_data(code, name, chart, result, PERIOD, NUM_STD)
        stocks_data.append(sd)

        pnl = result.equity_curve[-1] - CAPITAL_PER_STOCK if result.equity_curve else 0
        print(f"  {code} {name}: {result.total_return_pct:+.2f}% ({result.trade_count}건, {len(chart)}봉) 손익: {pnl:+,.0f}원")

    json_data = json.dumps(stocks_data, ensure_ascii=False)

    params_label = (
        f"period={PERIOD}분, σ={NUM_STD}, 강제청산={FORCE_CLOSE}, "
        f"매수금지={NO_BUY_AFTER}, 활성시간={ACTIVE_WINDOWS}, "
        f"동적수량={TARGET_ORDER:,}원/{MIN_QTY}~{MAX_QTY}주"
    )

    html = HTML_TEMPLATE
    html = html.replace("__JSON_DATA__", json_data)
    html = html.replace("__CAPITAL_RAW__", str(CAPITAL_PER_STOCK))
    html = html.replace("__BB_PERIOD__", str(PERIOD))
    html = html.replace("__BB_STD__", str(NUM_STD))
    html = html.replace("__BB_HOLD__", "장마감 청산")
    html = html.replace("__ORDER_RATIO__", f"동적({TARGET_ORDER//10000}만)")
    html = html.replace("__CAPITAL__", f"{CAPITAL_PER_STOCK:,}")

    out_path = os.path.join(os.path.dirname(__file__), "..", "backtest_minute_report.html")
    out_path = os.path.abspath(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n리포트 생성: {out_path}")
    webbrowser.open(f"file://{out_path}")


if __name__ == "__main__":
    main()
