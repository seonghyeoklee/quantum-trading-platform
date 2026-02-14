"""전략 비교 HTML 리포트 생성"""

import json
import sys


def generate_html(data: list[dict]) -> str:
    # Aggregate portfolio-level stats
    strategy_labels = [s["label"] for s in data[0]["strategies"]]
    n_strategies = len(strategy_labels)

    # Per-strategy aggregate
    agg = []
    for si in range(n_strategies):
        returns = [row["strategies"][si]["total_return_pct"] for row in data]
        bnh = [row["strategies"][si]["buy_and_hold_pct"] for row in data]
        mdds = [row["strategies"][si]["max_drawdown_pct"] for row in data]
        win_rates = [row["strategies"][si]["win_rate"] for row in data]
        trade_counts = [row["strategies"][si]["trade_count"] for row in data]
        sharpes = [row["strategies"][si]["sharpe_ratio"] for row in data if row["strategies"][si]["sharpe_ratio"] is not None]
        agg.append({
            "label": strategy_labels[si],
            "avg_return": sum(returns) / len(returns),
            "avg_bnh": sum(bnh) / len(bnh),
            "avg_mdd": sum(mdds) / len(mdds),
            "avg_win_rate": sum(win_rates) / len(win_rates),
            "total_trades": sum(trade_counts),
            "avg_sharpe": sum(sharpes) / len(sharpes) if sharpes else None,
        })

    # Colors for strategies
    colors = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444"]
    bg_colors = ["rgba(59,130,246,0.08)", "rgba(245,158,11,0.08)", "rgba(16,185,129,0.08)", "rgba(239,68,68,0.08)"]

    # Build per-stock rows
    stock_rows = ""
    stock_detail_sections = ""
    for row in data:
        sym = row["symbol"]
        name = row["name"]
        fp = row["first_price"]
        lp = row["last_price"]
        bnh_pct = (lp - fp) / fp * 100

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
            <td>{fp:,}</td>
            <td>{lp:,}</td>
            <td class="{'positive' if bnh_pct > 0 else 'negative'}">{bnh_pct:+.1f}%</td>
            {cells}
            <td><button class="detail-btn" onclick="toggleDetail('{sym}')">상세</button></td>
        </tr>"""

        # Detail section: equity curves + trades
        # Equity curve data for chart
        equity_datasets = []
        for si, s in enumerate(row["strategies"]):
            curve = s["equity_curve"]
            # Downsample for performance (max 200 points)
            step = max(1, len(curve) // 200)
            sampled = curve[::step]
            equity_datasets.append({
                "label": s["label"],
                "data": sampled,
                "color": colors[si],
            })

        # Trade tables per strategy
        trade_tables = ""
        for si, s in enumerate(row["strategies"]):
            if not s["trades"]:
                trade_tables += f'<div class="trade-section"><h4 style="color:{colors[si]}">{s["label"]}</h4><p class="no-trades">거래 없음</p></div>'
                continue
            trade_rows = ""
            for t in s["trades"]:
                reason_badge = ""
                if t["reason"] == "stop_loss":
                    reason_badge = '<span class="badge badge-red">손절</span>'
                elif t["reason"] == "max_holding":
                    reason_badge = '<span class="badge badge-orange">보유한도</span>'
                elif t["reason"] == "signal":
                    reason_badge = '<span class="badge badge-blue">시그널</span>'
                side_class = "buy" if t["side"] == "buy" else "sell"
                trade_rows += f"""
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
                    <tbody>{trade_rows}</tbody>
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

    # Aggregate summary cards
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

    # Bar chart data for overview
    bar_chart_data = json.dumps({
        "symbols": [f'{r["name"]}' for r in data],
        "bnh": [round(r["strategies"][0]["buy_and_hold_pct"], 2) for r in data],
        "strategies": [
            {"label": strategy_labels[si], "data": [round(r["strategies"][si]["total_return_pct"], 2) for r in data], "color": colors[si]}
            for si in range(n_strategies)
        ]
    }, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>전략 비교 백테스트 리포트</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Pretendard', sans-serif; background: #0f1117; color: #e0e0e0; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
header {{ text-align: center; padding: 40px 0 24px; }}
header h1 {{ font-size: 28px; font-weight: 700; color: #fff; }}
header p {{ color: #888; margin-top: 8px; font-size: 14px; }}
.summary-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 24px 0; }}
.summary-card {{ background: #1a1d27; border-radius: 12px; padding: 20px; }}
.summary-card h3 {{ font-size: 14px; color: #aaa; margin-bottom: 8px; }}
.metric-main {{ font-size: 32px; font-weight: 700; }}
.metric-label {{ font-size: 12px; color: #666; margin-bottom: 12px; }}
.metric-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }}
.metric-value {{ font-size: 16px; font-weight: 600; display: block; }}
.metric-sub {{ font-size: 11px; color: #666; }}
.positive {{ color: #22c55e; }}
.negative {{ color: #ef4444; }}
.overview-chart {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 24px 0; }}
.overview-chart h2 {{ font-size: 18px; margin-bottom: 16px; color: #fff; }}
.table-section {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 24px 0; overflow-x: auto; }}
.table-section h2 {{ font-size: 18px; margin-bottom: 16px; color: #fff; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: #252830; color: #aaa; font-weight: 600; padding: 10px 8px; text-align: right; white-space: nowrap; position: sticky; top: 0; }}
th:first-child {{ text-align: left; }}
td {{ padding: 10px 8px; border-bottom: 1px solid #252830; text-align: right; white-space: nowrap; }}
td:first-child {{ text-align: left; }}
.stock-cell {{ display: flex; flex-direction: column; gap: 2px; }}
.stock-code {{ font-weight: 600; color: #fff; font-size: 13px; }}
.stock-name {{ color: #888; font-size: 11px; }}
.strategy-header {{ text-align: center !important; font-size: 12px; padding: 6px 8px; }}
.detail-btn {{ background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 4px 12px; cursor: pointer; font-size: 12px; }}
.detail-btn:hover {{ background: #1d4ed8; }}
.detail-panel {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 12px 0; }}
.detail-panel h3 {{ font-size: 16px; color: #fff; margin-bottom: 16px; }}
.chart-container {{ height: 300px; margin-bottom: 24px; }}
.trades-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
.trade-section h4 {{ font-size: 14px; margin-bottom: 8px; }}
.trade-table {{ font-size: 12px; }}
.trade-table th {{ background: #1e2028; font-size: 11px; padding: 6px; }}
.trade-table td {{ padding: 5px 6px; border-bottom: 1px solid #1e2028; }}
.buy {{ color: #ef4444; font-weight: 600; }}
.sell {{ color: #3b82f6; font-weight: 600; }}
.badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }}
.badge-red {{ background: rgba(239,68,68,0.15); color: #f87171; }}
.badge-orange {{ background: rgba(245,158,11,0.15); color: #fbbf24; }}
.badge-blue {{ background: rgba(59,130,246,0.15); color: #60a5fa; }}
.no-trades {{ color: #555; font-size: 13px; }}
.divider {{ border: none; border-top: 1px solid #252830; margin: 8px 0; }}
footer {{ text-align: center; padding: 32px; color: #555; font-size: 12px; }}
@media (max-width: 900px) {{
    .summary-row {{ grid-template-columns: repeat(2, 1fr); }}
    .trades-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>전략 비교 백테스트 리포트</h1>
        <p>2024.01.01 ~ 2026.02.14 | 초기자본 1,000만원 | 종목당 주문금액 100만원 | {len(data)}개 종목</p>
    </header>

    <div class="summary-row">{summary_cards}</div>

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
                    <th rowspan="2">시작가</th>
                    <th rowspan="2">종가</th>
                    <th rowspan="2">B&H</th>
                    <th colspan="5" class="strategy-header" style="color:{colors[0]}; border-bottom:2px solid {colors[0]}">SMA 기본</th>
                    <th colspan="5" class="strategy-header" style="color:{colors[1]}; border-bottom:2px solid {colors[1]}">SMA+리스크</th>
                    <th colspan="5" class="strategy-header" style="color:{colors[2]}; border-bottom:2px solid {colors[2]}">SMA+Adv+리스크</th>
                    <th colspan="5" class="strategy-header" style="color:{colors[3]}; border-bottom:2px solid {colors[3]}">볼린저</th>
                    <th rowspan="2"></th>
                </tr>
                <tr>
                    <th>수익률</th><th>거래</th><th>승률</th><th>MDD</th><th>SR</th>
                    <th>수익률</th><th>거래</th><th>승률</th><th>MDD</th><th>SR</th>
                    <th>수익률</th><th>거래</th><th>승률</th><th>MDD</th><th>SR</th>
                    <th>수익률</th><th>거래</th><th>승률</th><th>MDD</th><th>SR</th>
                </tr>
            </thead>
            <tbody>{stock_rows}</tbody>
        </table>
    </div>

    {stock_detail_sections}
</div>

<footer>Quantum Trading Platform — Strategy Comparison Report</footer>

<script>
const barData = {bar_chart_data};

// Overview bar chart
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

// Detail toggle + equity chart
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
}}
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    with open("/tmp/backtest_data.json") as f:
        data = json.load(f)
    html = generate_html(data)
    out = "strategy_comparison_report.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"Report: {out}")
