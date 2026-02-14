#!/usr/bin/env python
"""볼린저밴드 백테스트 시각화 HTML 리포트 생성"""

import json
import os
import sys
import webbrowser
from datetime import datetime, timedelta

from app.trading.backtest import (
    BacktestResult,
    Trade,
    fetch_chart_from_yfinance,
    run_bollinger_backtest,
    to_yfinance_ticker,
)
from app.models import ChartData
from app.trading.strategy import compute_bollinger_bands

SYMBOLS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("034020", "두산에너빌리티"),
    ("298040", "효성중공업"),
]

END_DATE = datetime.now().strftime("%Y%m%d")
START_DATE = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

CAPITAL_PER_STOCK = 10_000_000
PERIOD = 10
NUM_STD = 1.8
MAX_HOLD = 15
ORDER_RATIO = 0.8


def build_stock_data(
    code: str,
    name: str,
    chart: list[ChartData],
    result: BacktestResult,
    period: int,
    num_std: float,
) -> dict:
    """종목별 차트+밴드+거래 데이터를 dict로 변환."""
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

    # 매매 쌍 (매수→매도) 손익 계산
    trade_pairs = []
    buy_stack = []
    for t in result.trades:
        if t.side == "buy":
            buy_stack.append(t)
        elif t.side == "sell" and buy_stack:
            b = buy_stack.pop(0)
            pnl = (t.price - b.price) * b.quantity
            pnl_pct = (t.price - b.price) / b.price * 100
            trade_pairs.append({
                "buy_date": b.date,
                "buy_price": b.price,
                "sell_date": t.date,
                "sell_price": t.price,
                "qty": b.quantity,
                "pnl": pnl,
                "pnl_pct": round(pnl_pct, 2),
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
<title>볼린저밴드 백테스트 리포트</title>
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
</style>
</head>
<body>

<h1>볼린저밴드 단타 백테스트 리포트</h1>
<div class="params">
  기간: __PERIOD_RANGE__ | period=__BB_PERIOD__, σ=__BB_STD__, 보유제한=__BB_HOLD__일, 투입비율=__ORDER_RATIO__% | 종목당 자본: __CAPITAL__원
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

// 종목별 섹션 렌더
const container = document.getElementById('stock-sections');

DATA.forEach((stock, idx) => {
  const s = stock.summary;
  const pnl = stock.equity[stock.equity.length-1] - CAPITAL;

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
      <div class="metric"><div class="label">Sharpe</div><div class="value">${s.sharpe_ratio ?? 'N/A'}</div></div>
    </div>
    <div class="legend">
      <div class="legend-item"><span class="legend-dot" style="background:#666"></span>종가</div>
      <div class="legend-item"><span class="legend-dot" style="background:rgba(255,152,0,0.5)"></span>볼린저밴드</div>
      <div class="legend-item"><span class="legend-dot" style="background:#f44336"></span>매수</div>
      <div class="legend-item"><span class="legend-dot" style="background:#2196f3"></span>매도</div>
    </div>
    <div class="chart-container">
      <canvas id="price-${idx}" height="260"></canvas>
    </div>
    <div class="chart-container">
      <canvas id="equity-${idx}" height="140"></canvas>
    </div>
    <button class="toggle-btn" onclick="toggleTable('table-${idx}')">거래 내역 보기/숨기기</button>
    <div id="table-${idx}" style="display:none">
      <table class="trade-table">
        <thead><tr><th>#</th><th>매수일</th><th>매수가</th><th>매도일</th><th>매도가</th><th>수량</th><th>손익</th><th>수익률</th></tr></thead>
        <tbody>
          ${stock.trade_pairs.map((p, i) => `
            <tr>
              <td>${i+1}</td>
              <td>${fmtDate(p.buy_date)}</td>
              <td>${p.buy_price.toLocaleString()}</td>
              <td>${fmtDate(p.sell_date)}</td>
              <td>${p.sell_price.toLocaleString()}</td>
              <td>${p.qty}</td>
              <td class="${p.pnl>=0?'pnl-pos':'pnl-neg'}">${p.pnl>=0?'+':''}${p.pnl.toLocaleString()}</td>
              <td class="${p.pnl_pct>=0?'pnl-pos':'pnl-neg'}">${p.pnl_pct>=0?'+':''}${p.pnl_pct}%</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
  container.appendChild(section);

  // 가격 차트 그리기
  drawPriceChart(`price-${idx}`, stock);
  drawEquityChart(`equity-${idx}`, stock);
});

function fmtDate(d) {
  if (d.length === 8) return d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6);
  return d;
}

function toggleTable(id) {
  const el = document.getElementById(id);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function drawPriceChart(canvasId, stock) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height;
  const pad = {t:20, b:30, l:60, r:20};
  const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;

  // 데이터 범위
  const validCloses = stock.closes;
  const allVals = [...validCloses];
  stock.uppers.forEach((v,i) => { if(v!==null) allVals.push(v); });
  stock.lowers.forEach((v,i) => { if(v!==null) allVals.push(v); });
  const minV = Math.min(...allVals) * 0.97;
  const maxV = Math.max(...allVals) * 1.03;
  const n = validCloses.length;

  function x(i) { return pad.l + (i / (n-1)) * cW; }
  function y(v) { return pad.t + (1 - (v - minV) / (maxV - minV)) * cH; }

  // 볼린저밴드 영역
  ctx.beginPath();
  let started = false;
  for (let i = 0; i < n; i++) {
    if (stock.uppers[i] !== null) {
      if (!started) { ctx.moveTo(x(i), y(stock.uppers[i])); started = true; }
      else ctx.lineTo(x(i), y(stock.uppers[i]));
    }
  }
  for (let i = n-1; i >= 0; i--) {
    if (stock.lowers[i] !== null) ctx.lineTo(x(i), y(stock.lowers[i]));
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(255,152,0,0.08)';
  ctx.fill();

  // 상단밴드
  ctx.beginPath(); started = false;
  for (let i = 0; i < n; i++) {
    if (stock.uppers[i] !== null) {
      if (!started) { ctx.moveTo(x(i), y(stock.uppers[i])); started = true; }
      else ctx.lineTo(x(i), y(stock.uppers[i]));
    }
  }
  ctx.strokeStyle = 'rgba(255,152,0,0.4)'; ctx.lineWidth = 1; ctx.stroke();

  // 하단밴드
  ctx.beginPath(); started = false;
  for (let i = 0; i < n; i++) {
    if (stock.lowers[i] !== null) {
      if (!started) { ctx.moveTo(x(i), y(stock.lowers[i])); started = true; }
      else ctx.lineTo(x(i), y(stock.lowers[i]));
    }
  }
  ctx.strokeStyle = 'rgba(255,152,0,0.4)'; ctx.lineWidth = 1; ctx.stroke();

  // 중간밴드 (SMA)
  ctx.beginPath(); started = false;
  for (let i = 0; i < n; i++) {
    if (stock.middles[i] !== null) {
      if (!started) { ctx.moveTo(x(i), y(stock.middles[i])); started = true; }
      else ctx.lineTo(x(i), y(stock.middles[i]));
    }
  }
  ctx.strokeStyle = 'rgba(255,152,0,0.25)'; ctx.lineWidth = 1; ctx.setLineDash([4,4]); ctx.stroke(); ctx.setLineDash([]);

  // 종가 라인
  ctx.beginPath();
  ctx.moveTo(x(0), y(validCloses[0]));
  for (let i = 1; i < n; i++) ctx.lineTo(x(i), y(validCloses[i]));
  ctx.strokeStyle = '#888'; ctx.lineWidth = 1.5; ctx.stroke();

  // 매수 마커
  const dateIndex = {};
  stock.dates.forEach((d, i) => { dateIndex[d] = i; });

  stock.buys.forEach(b => {
    const i = dateIndex[b.date];
    if (i === undefined) return;
    ctx.beginPath();
    const bx = x(i), by = y(b.price);
    ctx.moveTo(bx, by+4); ctx.lineTo(bx-6, by+14); ctx.lineTo(bx+6, by+14); ctx.closePath();
    ctx.fillStyle = '#f44336'; ctx.fill();
    // 세로선
    ctx.beginPath(); ctx.moveTo(bx, pad.t); ctx.lineTo(bx, pad.t+cH);
    ctx.strokeStyle = 'rgba(244,67,54,0.2)'; ctx.lineWidth = 1; ctx.stroke();
  });

  // 매도 마커
  stock.sells.forEach(s => {
    const i = dateIndex[s.date];
    if (i === undefined) return;
    ctx.beginPath();
    const sx = x(i), sy = y(s.price);
    ctx.moveTo(sx, sy-4); ctx.lineTo(sx-6, sy-14); ctx.lineTo(sx+6, sy-14); ctx.closePath();
    ctx.fillStyle = '#2196f3'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(sx, pad.t); ctx.lineTo(sx, pad.t+cH);
    ctx.strokeStyle = 'rgba(33,150,243,0.2)'; ctx.lineWidth = 1; ctx.stroke();
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

  // X축 날짜
  ctx.textAlign = 'center'; ctx.fillStyle = '#555';
  const xSteps = Math.min(6, n-1);
  for (let i = 0; i <= xSteps; i++) {
    const di = Math.round(i * (n-1) / xSteps);
    const d = stock.dates[di];
    ctx.fillText(fmtDate(d), x(di), H - 8);
  }
}

function drawEquityChart(canvasId, stock) {
  const canvas = document.getElementById(canvasId);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height;
  const pad = {t:15, b:25, l:60, r:20};
  const cW = W - pad.l - pad.r, cH = H - pad.t - pad.b;

  const eq = stock.equity;
  const n = eq.length;
  const minE = Math.min(...eq) * 0.998;
  const maxE = Math.max(...eq) * 1.002;

  function x(i) { return pad.l + (i / (n-1)) * cW; }
  function y(v) { return pad.t + (1 - (v - minE) / (maxE - minE)) * cH; }

  // 기준선 (초기자본)
  ctx.beginPath(); ctx.moveTo(pad.l, y(CAPITAL)); ctx.lineTo(W-pad.r, y(CAPITAL));
  ctx.strokeStyle = '#444'; ctx.lineWidth = 1; ctx.setLineDash([4,4]); ctx.stroke(); ctx.setLineDash([]);

  // 자산 곡선 fill
  ctx.beginPath();
  ctx.moveTo(x(0), y(CAPITAL));
  for (let i = 0; i < n; i++) ctx.lineTo(x(i), y(eq[i]));
  ctx.lineTo(x(n-1), y(CAPITAL));
  ctx.closePath();
  const finalAbove = eq[eq.length-1] >= CAPITAL;
  ctx.fillStyle = finalAbove ? 'rgba(244,67,54,0.1)' : 'rgba(33,150,243,0.1)';
  ctx.fill();

  // 자산 곡선 라인
  ctx.beginPath();
  ctx.moveTo(x(0), y(eq[0]));
  for (let i = 1; i < n; i++) ctx.lineTo(x(i), y(eq[i]));
  ctx.strokeStyle = finalAbove ? '#f44336' : '#2196f3'; ctx.lineWidth = 1.5; ctx.stroke();

  // Y축
  ctx.fillStyle = '#666'; ctx.font = '11px monospace'; ctx.textAlign = 'right';
  [minE, CAPITAL, maxE].forEach(v => {
    ctx.fillText((Math.round(v/10000)).toLocaleString()+'만', pad.l-6, y(v)+4);
  });

  // 라벨
  ctx.fillStyle = '#888'; ctx.font = '11px sans-serif'; ctx.textAlign = 'left';
  ctx.fillText('자산 곡선', pad.l + 4, pad.t + 12);
}
</script>
</body>
</html>"""


def main():
    order_amount = int(CAPITAL_PER_STOCK * ORDER_RATIO)
    stocks_data = []

    print("데이터 로드 중...")
    for code, name in SYMBOLS:
        ticker = to_yfinance_ticker(code)
        try:
            chart = fetch_chart_from_yfinance(ticker, START_DATE, END_DATE)
        except Exception as e:
            print(f"  {code} {name} 실패: {e}", file=sys.stderr)
            continue
        if not chart:
            continue

        result = run_bollinger_backtest(
            chart=chart,
            initial_capital=CAPITAL_PER_STOCK,
            order_amount=order_amount,
            period=PERIOD,
            num_std=NUM_STD,
            max_holding_days=MAX_HOLD,
        )

        sd = build_stock_data(code, name, chart, result, PERIOD, NUM_STD)
        stocks_data.append(sd)
        print(f"  {code} {name}: {result.total_return_pct:+.2f}% ({result.trade_count}건)")

    # HTML 생성
    json_data = json.dumps(stocks_data, ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("__JSON_DATA__", json_data)
    html = html.replace("__CAPITAL_RAW__", str(CAPITAL_PER_STOCK))
    html = html.replace("__PERIOD_RANGE__", f"{START_DATE[:4]}-{START_DATE[4:6]}-{START_DATE[6:]} ~ {END_DATE[:4]}-{END_DATE[4:6]}-{END_DATE[6:]}")
    html = html.replace("__BB_PERIOD__", str(PERIOD))
    html = html.replace("__BB_STD__", str(NUM_STD))
    html = html.replace("__BB_HOLD__", str(MAX_HOLD))
    html = html.replace("__ORDER_RATIO__", str(int(ORDER_RATIO * 100)))
    html = html.replace("__CAPITAL__", f"{CAPITAL_PER_STOCK:,}")

    out_path = os.path.join(os.path.dirname(__file__), "..", "backtest_report.html")
    out_path = os.path.abspath(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n리포트 생성 완료: {out_path}")

    # 브라우저로 열기
    webbrowser.open(f"file://{out_path}")


if __name__ == "__main__":
    main()
