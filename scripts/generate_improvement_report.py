#!/usr/bin/env python
"""SMA 크로스오버 매매 품질 개선 전/후 비교 백테스트 리포트"""

import json
import sys
from datetime import datetime

from app.trading.backtest import (
    BacktestResult,
    fetch_chart_from_yfinance,
    run_backtest,
    to_yfinance_ticker,
)
from app.report_theme import wrap_html


# 감시 종목 (현재 운용 포트폴리오)
SYMBOLS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("035420", "NAVER"),
    ("005490", "POSCO홀딩스"),
    ("105560", "KB금융"),
    ("009540", "HD한국조선해양"),
    ("034020", "두산에너빌리티"),
    ("298040", "효성중공업"),
    ("064350", "현대로템"),
    ("010120", "LS일렉트릭"),
]

# 공통 파라미터
COMMON = dict(
    initial_capital=10_000_000,
    order_amount=1_000_000,
    stop_loss_pct=5.0,
    max_holding_days=20,
    trailing_stop_pct=3.0,
)

# 개선 전 (기존)
BEFORE = dict(
    short_period=5,
    long_period=20,
    min_sma_gap_pct=0.0,
    min_profit_pct=0.0,
    sell_cooldown_bars=0,
    **COMMON,
)

# 개선 후 (신규)
AFTER = dict(
    short_period=10,
    long_period=40,
    min_sma_gap_pct=0.1,
    min_profit_pct=1.0,
    sell_cooldown_bars=1,  # 일봉 기준 1바(=1일) 쿨다운
    **COMMON,
)

SCENARIOS = [
    ("개선 전 SMA(5/20)", BEFORE),
    ("개선 후 SMA(10/40)", AFTER),
]

START_DATE = "20250301"  # 최근 1년


def _run_all(end_date: str) -> list[dict]:
    results = []
    for code, name in SYMBOLS:
        ticker = to_yfinance_ticker(code)
        print(f"  {code} {name} 데이터 조회 중...", file=sys.stderr)
        try:
            chart = fetch_chart_from_yfinance(ticker, START_DATE, end_date)
        except Exception as e:
            print(f"  [WARN] {code} {name} 실패: {e}", file=sys.stderr)
            continue
        if not chart:
            print(f"  [WARN] {code} {name} 데이터 없음", file=sys.stderr)
            continue

        row = {
            "symbol": code,
            "name": name,
            "data_points": len(chart),
            "first_price": chart[0].close,
            "last_price": chart[-1].close,
            "strategies": [],
        }
        for label, params in SCENARIOS:
            r = run_backtest(chart=chart, **params)
            row["strategies"].append({
                "label": label,
                "total_return_pct": r.total_return_pct,
                "buy_and_hold_pct": r.buy_and_hold_pct,
                "trade_count": r.trade_count,
                "win_rate": r.win_rate,
                "max_drawdown_pct": r.max_drawdown_pct,
                "sharpe_ratio": r.sharpe_ratio,
                "equity_curve": r.equity_curve,
                "trades": [
                    {"date": t.date, "side": t.side, "price": t.price, "qty": t.quantity, "reason": t.reason}
                    for t in r.trades
                ],
            })
        results.append(row)
    return results


_EXTRA_CSS = """
.summary-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin: 24px 0; }
.diff-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }
.diff-card { background: #1a1d27; border-radius: 10px; padding: 16px; text-align: center; }
.diff-card .label { font-size: 12px; color: #888; margin-bottom: 4px; }
.diff-card .value { font-size: 24px; font-weight: 700; }
.overview-chart { background: #1a1d27; border-radius: 12px; padding: 24px; margin: 24px 0; }
.overview-chart h2 { font-size: 18px; margin-bottom: 16px; color: #fff; }
.table-section { background: #1a1d27; border-radius: 12px; padding: 24px; margin: 24px 0; overflow-x: auto; }
.table-section h2 { font-size: 18px; margin-bottom: 16px; color: #fff; }
.param-section { background: #1a1d27; border-radius: 12px; padding: 24px; margin: 24px 0; }
.param-section h2 { font-size: 18px; margin-bottom: 16px; color: #fff; }
.param-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.param-card { background: #252830; border-radius: 8px; padding: 16px; }
.param-card h4 { color: #aaa; font-size: 13px; margin-bottom: 8px; }
.param-card table { font-size: 12px; }
.param-card th { background: transparent; color: #666; font-size: 11px; padding: 4px 8px; }
.param-card td { border-bottom: 1px solid #1e2028; padding: 4px 8px; }
.changed { color: #fbbf24; font-weight: 600; }
th { padding: 10px 8px; white-space: nowrap; position: sticky; top: 0; }
td { padding: 10px 8px; white-space: nowrap; }
.strategy-header { text-align: center !important; font-size: 12px; padding: 6px 8px; }
.trades-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
.trade-section h4 { font-size: 14px; margin-bottom: 8px; }
.buy { color: #ef4444; font-weight: 600; }
.sell { color: #3b82f6; font-weight: 600; }
.no-trades { color: #555; font-size: 13px; }
.arrow { font-size: 16px; color: #888; }
@media (max-width: 900px) {
    .summary-row { grid-template-columns: 1fr; }
    .diff-row { grid-template-columns: repeat(2, 1fr); }
    .param-grid { grid-template-columns: 1fr; }
}
"""


def generate_html(data: list[dict]) -> str:
    n_stocks = len(data)
    colors = ["#ef4444", "#22c55e"]  # 빨강(개선 전), 초록(개선 후)

    # Aggregate
    agg = []
    for si in range(2):
        returns = [r["strategies"][si]["total_return_pct"] for r in data]
        mdds = [r["strategies"][si]["max_drawdown_pct"] for r in data]
        win_rates = [r["strategies"][si]["win_rate"] for r in data]
        trade_counts = [r["strategies"][si]["trade_count"] for r in data]
        sharpes = [r["strategies"][si]["sharpe_ratio"] for r in data if r["strategies"][si]["sharpe_ratio"] is not None]
        agg.append({
            "label": data[0]["strategies"][si]["label"],
            "avg_return": sum(returns) / len(returns),
            "avg_mdd": sum(mdds) / len(mdds),
            "avg_win_rate": sum(win_rates) / len(win_rates),
            "total_trades": sum(trade_counts),
            "avg_sharpe": sum(sharpes) / len(sharpes) if sharpes else None,
        })

    # Diff cards
    d_return = agg[1]["avg_return"] - agg[0]["avg_return"]
    d_winrate = agg[1]["avg_win_rate"] - agg[0]["avg_win_rate"]
    d_trades = agg[1]["total_trades"] - agg[0]["total_trades"]
    d_mdd = agg[1]["avg_mdd"] - agg[0]["avg_mdd"]
    trade_reduction_pct = (d_trades / agg[0]["total_trades"] * 100) if agg[0]["total_trades"] > 0 else 0

    def _diff_color(val, invert=False):
        if invert:
            return "positive" if val < 0 else "negative" if val > 0 else ""
        return "positive" if val > 0 else "negative" if val < 0 else ""

    diff_cards = f"""
    <div class="diff-card">
        <div class="label">수익률 변화</div>
        <div class="value {_diff_color(d_return)}">{d_return:+.2f}%p</div>
    </div>
    <div class="diff-card">
        <div class="label">승률 변화</div>
        <div class="value {_diff_color(d_winrate)}">{d_winrate:+.1f}%p</div>
    </div>
    <div class="diff-card">
        <div class="label">거래 횟수 변화</div>
        <div class="value {_diff_color(d_trades, invert=True)}">{d_trades:+d}건 ({trade_reduction_pct:+.0f}%)</div>
    </div>
    <div class="diff-card">
        <div class="label">MDD 변화</div>
        <div class="value {_diff_color(d_mdd, invert=True)}">{d_mdd:+.2f}%p</div>
    </div>"""

    # Summary cards
    summary_cards = ""
    for si, a in enumerate(agg):
        sharpe_str = f'{a["avg_sharpe"]:.2f}' if a["avg_sharpe"] is not None else "-"
        ret_class = "positive" if a["avg_return"] > 0 else "negative"
        summary_cards += f"""
        <div class="summary-card" style="border-top: 4px solid {colors[si]}">
            <h3>{a["label"]}</h3>
            <div class="metric-main {ret_class}">{a["avg_return"]:+.2f}%</div>
            <div class="metric-label">평균 수익률</div>
            <div class="metric-grid">
                <div><span class="metric-value">{a["avg_win_rate"]:.1f}%</span><span class="metric-sub">승률</span></div>
                <div><span class="metric-value">{a["avg_mdd"]:.2f}%</span><span class="metric-sub">평균 MDD</span></div>
                <div><span class="metric-value">{a["total_trades"]}</span><span class="metric-sub">총 거래</span></div>
                <div><span class="metric-value">{sharpe_str}</span><span class="metric-sub">Sharpe</span></div>
            </div>
        </div>"""

    # Stock table
    stock_rows = ""
    stock_detail_sections = ""
    for row in data:
        sym = row["symbol"]
        name = row["name"]
        bnh = row["strategies"][0]["buy_and_hold_pct"]

        cells = ""
        for si, s in enumerate(row["strategies"]):
            ret = s["total_return_pct"]
            ret_class = "positive" if ret > 0 else "negative" if ret < 0 else ""
            sharpe_str = f'{s["sharpe_ratio"]:.2f}' if s["sharpe_ratio"] is not None else "-"
            cells += f"""
                <td class="{ret_class}">{ret:+.2f}%</td>
                <td>{s["trade_count"]}</td>
                <td>{s["win_rate"]:.1f}%</td>
                <td>{s["max_drawdown_pct"]:.2f}%</td>
                <td>{sharpe_str}</td>"""

        stock_rows += f"""
        <tr>
            <td class="stock-cell">
                <span class="stock-code">{sym}</span>
                <span class="stock-name">{name}</span>
            </td>
            <td class="{'positive' if bnh > 0 else 'negative'}">{bnh:+.1f}%</td>
            {cells}
            <td><button class="detail-btn" onclick="toggleDetail('{sym}')">상세</button></td>
        </tr>"""

        # Detail: equity curves + trade tables
        equity_datasets = []
        for si, s in enumerate(row["strategies"]):
            curve = s["equity_curve"]
            step = max(1, len(curve) // 200)
            sampled = curve[::step]
            equity_datasets.append({"label": s["label"], "data": sampled, "color": colors[si]})

        trade_tables = ""
        for si, s in enumerate(row["strategies"]):
            if not s["trades"]:
                trade_tables += f'<div class="trade-section"><h4 style="color:{colors[si]}">{s["label"]}</h4><p class="no-trades">거래 없음</p></div>'
                continue
            trade_rows_html = ""
            for t in s["trades"]:
                reason_badge = ""
                if t["reason"] == "stop_loss":
                    reason_badge = '<span class="badge badge-red">손절</span>'
                elif t["reason"] == "max_holding":
                    reason_badge = '<span class="badge badge-orange">보유한도</span>'
                elif t["reason"] == "trailing_stop":
                    reason_badge = '<span class="badge badge-orange">트레일링</span>'
                elif t["reason"] == "signal":
                    reason_badge = '<span class="badge badge-blue">시그널</span>'
                side_class = "buy" if t["side"] == "buy" else "sell"
                trade_rows_html += f"""
                    <tr>
                        <td>{t["date"]}</td>
                        <td class="{side_class}">{t["side"].upper()}</td>
                        <td>{t["price"]:,}</td>
                        <td>{t["qty"]}</td>
                        <td>{reason_badge}</td>
                    </tr>"""
            trade_tables += f"""
            <div class="trade-section">
                <h4 style="color:{colors[si]}">{s["label"]}</h4>
                <table class="trade-table">
                    <thead><tr><th>날짜</th><th>구분</th><th>가격</th><th>수량</th><th>사유</th></tr></thead>
                    <tbody>{trade_rows_html}</tbody>
                </table>
            </div>"""

        equity_json = json.dumps(equity_datasets, ensure_ascii=False)
        stock_detail_sections += f"""
        <div id="detail-{sym}" class="detail-panel" style="display:none">
            <h3>{sym} {name} 상세</h3>
            <div class="chart-container">
                <canvas id="chart-{sym}"></canvas>
            </div>
            <script>
                window.chartData_{sym} = {equity_json};
            </script>
            <div class="trades-grid">{trade_tables}</div>
        </div>"""

    # Bar chart data
    bar_data = json.dumps({
        "symbols": [f'{r["name"]}' for r in data],
        "bnh": [round(r["strategies"][0]["buy_and_hold_pct"], 2) for r in data],
        "strategies": [
            {
                "label": data[0]["strategies"][si]["label"],
                "data": [round(r["strategies"][si]["total_return_pct"], 2) for r in data],
                "color": colors[si],
            }
            for si in range(2)
        ],
    }, ensure_ascii=False)

    body = f"""<div class="container">
    <header>
        <h1>SMA 크로스오버 매매 품질 개선 백테스트</h1>
        <p>2025.03.01 ~ 현재 | 초기자본 1,000만원 | 종목당 100만원 | {n_stocks}개 종목</p>
    </header>

    <div class="diff-row">{diff_cards}</div>
    <div class="summary-row">{summary_cards}</div>

    <div class="param-section">
        <h2>파라미터 변경 사항</h2>
        <div class="param-grid">
            <div class="param-card">
                <h4>개선 전 (기존)</h4>
                <table>
                    <tr><th>SMA 기간</th><td>단기 5 / 장기 20</td></tr>
                    <tr><th>최소 갭 필터</th><td>없음</td></tr>
                    <tr><th>매도 수익률 게이트</th><td>없음</td></tr>
                    <tr><th>매도 후 쿨다운</th><td>없음</td></tr>
                    <tr><th>손절</th><td>5%</td></tr>
                    <tr><th>트레일링 스탑</th><td>3%</td></tr>
                    <tr><th>보유기간 제한</th><td>20일</td></tr>
                </table>
            </div>
            <div class="param-card">
                <h4>개선 후 (신규)</h4>
                <table>
                    <tr><th>SMA 기간</th><td class="changed">단기 10 / 장기 40</td></tr>
                    <tr><th>최소 갭 필터</th><td class="changed">0.1%</td></tr>
                    <tr><th>매도 수익률 게이트</th><td class="changed">1.0%</td></tr>
                    <tr><th>매도 후 쿨다운</th><td class="changed">1일</td></tr>
                    <tr><th>손절</th><td>5%</td></tr>
                    <tr><th>트레일링 스탑</th><td>3%</td></tr>
                    <tr><th>보유기간 제한</th><td>20일</td></tr>
                </table>
            </div>
        </div>
    </div>

    <div class="overview-chart">
        <h2>종목별 수익률 비교</h2>
        <div style="height:400px"><canvas id="overviewChart"></canvas></div>
    </div>

    <div class="table-section">
        <h2>종목별 상세 지표</h2>
        <table>
            <thead>
                <tr>
                    <th rowspan="2">종목</th>
                    <th rowspan="2">B&H</th>
                    <th colspan="5" class="strategy-header" style="color:{colors[0]}; border-bottom:2px solid {colors[0]}">개선 전 SMA(5/20)</th>
                    <th colspan="5" class="strategy-header" style="color:{colors[1]}; border-bottom:2px solid {colors[1]}">개선 후 SMA(10/40)</th>
                    <th rowspan="2"></th>
                </tr>
                <tr>
                    <th>수익률</th><th>거래</th><th>승률</th><th>MDD</th><th>SR</th>
                    <th>수익률</th><th>거래</th><th>승률</th><th>MDD</th><th>SR</th>
                </tr>
            </thead>
            <tbody>{stock_rows}</tbody>
        </table>
    </div>

    {stock_detail_sections}
</div>

<footer>Quantum Trading Platform — SMA Improvement Backtest Report</footer>"""

    js = f"""const barData = {bar_data};

const ctx = document.getElementById('overviewChart').getContext('2d');
const datasets = [
    {{ label: 'Buy & Hold', data: barData.bnh, backgroundColor: 'rgba(255,255,255,0.12)', borderColor: '#555', borderWidth: 1, borderRadius: 3 }},
    ...barData.strategies.map(s => ({{
        label: s.label, data: s.data, backgroundColor: s.color + '99', borderColor: s.color, borderWidth: 1, borderRadius: 3
    }}))
];
new Chart(ctx, {{
    type: 'bar',
    data: {{ labels: barData.symbols, datasets }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
            legend: {{ labels: {{ color: '#aaa', font: {{ size: 12 }} }} }},
            tooltip: {{ callbacks: {{ label: ctx => ctx.dataset.label + ': ' + ctx.parsed.y.toFixed(2) + '%' }} }}
        }},
        scales: {{
            x: {{ ticks: {{ color: '#888', font: {{ size: 11 }} }}, grid: {{ color: '#1e2028' }} }},
            y: {{ ticks: {{ color: '#888', callback: v => v + '%' }}, grid: {{ color: '#1e2028' }} }}
        }}
    }}
}});

function toggleDetail(sym) {{
    const el = document.getElementById('detail-' + sym);
    if (el.style.display === 'none') {{
        el.style.display = 'block';
        const canvas = document.getElementById('chart-' + sym);
        if (!canvas.dataset.rendered) {{
            const chartData = window['chartData_' + sym];
            const ctx2 = canvas.getContext('2d');
            new Chart(ctx2, {{
                type: 'line',
                data: {{
                    labels: chartData[0].data.map((_, i) => i),
                    datasets: chartData.map(d => ({{
                        label: d.label, data: d.data, borderColor: d.color,
                        backgroundColor: d.color + '11', borderWidth: 1.5,
                        pointRadius: 0, fill: false, tension: 0.1
                    }}))
                }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    plugins: {{ legend: {{ labels: {{ color: '#aaa', font: {{ size: 11 }} }} }} }},
                    scales: {{
                        x: {{ display: false }},
                        y: {{ ticks: {{ color: '#888', callback: v => (v/10000).toFixed(0) + '만' }}, grid: {{ color: '#1e2028' }} }}
                    }}
                }}
            }});
            canvas.dataset.rendered = 'true';
        }}
    }} else {{
        el.style.display = 'none';
    }}
}}"""

    return wrap_html(
        title="SMA 매매 품질 개선 백테스트",
        body=body,
        extra_css=_EXTRA_CSS,
        extra_js=js,
    )


def main():
    end_date = datetime.now().strftime("%Y%m%d")
    print(f"백테스트 기간: {START_DATE} ~ {end_date}", file=sys.stderr)
    print(f"종목 수: {len(SYMBOLS)}", file=sys.stderr)

    data = _run_all(end_date)
    if not data:
        print("ERROR: 유효한 종목 데이터 없음", file=sys.stderr)
        sys.exit(1)

    html = generate_html(data)
    out = "sma_improvement_report.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"\nReport: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
