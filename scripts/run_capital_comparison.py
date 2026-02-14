"""자본 활용률 + 트레일링 스탑 개선 효과 비교 백테스트

3가지 구성을 비교:
1. 기존 (capital_ratio=0, order_amount=500K)
2. capital_ratio=0.3
3. capital_ratio=0.3 + trailing_stop=5.0

사용법:
    uv run python scripts/run_capital_comparison.py
"""

import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from app.models import ChartData
from app.trading.backtest import run_backtest, run_bollinger_backtest

SYMBOLS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "035420": "NAVER",
    "005490": "POSCO홀딩스",
    "105560": "KB금융",
    "009540": "HD한국조선해양",
    "034020": "두산에너빌리티",
    "298040": "효성중공업",
    "064350": "현대로템",
    "010120": "LS일렉트릭",
}

# 비교 구성 5가지
CONFIGS = [
    {
        "label": "기존 (고정 50만)",
        "capital_ratio": 0.0,
        "trailing_stop_pct": 0.0,
        "order_amount": 500_000,
    },
    {
        "label": "자본30%",
        "capital_ratio": 0.3,
        "trailing_stop_pct": 0.0,
        "order_amount": 500_000,
    },
    {
        "label": "자본30%+TS5%",
        "capital_ratio": 0.3,
        "trailing_stop_pct": 5.0,
        "order_amount": 500_000,
    },
    {
        "label": "자본30%+TS10%",
        "capital_ratio": 0.3,
        "trailing_stop_pct": 10.0,
        "order_amount": 500_000,
    },
    {
        "label": "자본30%+TS15%",
        "capital_ratio": 0.3,
        "trailing_stop_pct": 15.0,
        "order_amount": 500_000,
    },
]

# 전략별 × 구성별 = 4전략 × 5구성 = 20 시뮬레이션 per 종목
STRATEGIES = [
    {"label": "SMA 기본", "type": "sma", "use_advanced": False, "stop_loss": 0, "max_hold": 0, "vol_basic": True},
    {"label": "SMA+리스크", "type": "sma", "use_advanced": False, "stop_loss": 5.0, "max_hold": 20},
    {"label": "SMA+Adv+리스크", "type": "sma", "use_advanced": True, "stop_loss": 5.0, "max_hold": 20},
    {"label": "볼린저", "type": "bollinger"},
]


def fetch_chart(ticker: str, start: str, end: str) -> list[ChartData]:
    import yfinance as yf

    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        return []
    if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
        df = df.droplevel(level=1, axis=1)
    result = []
    for date, row in df.iterrows():
        result.append(
            ChartData(
                date=date.strftime("%Y%m%d"),
                open=round(row["Open"]),
                high=round(row["High"]),
                low=round(row["Low"]),
                close=round(row["Close"]),
                volume=round(row["Volume"]),
            )
        )
    return result


def run_all():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

    initial_capital = 10_000_000
    results = []

    for code, name in SYMBOLS.items():
        ticker = f"{code}.KS"
        print(f"  {code} {name} ... ", end="", flush=True)
        chart = fetch_chart(ticker, start_date, end_date)
        if len(chart) < 50:
            print("데이터 부족, 건너뜀")
            continue

        first_price = chart[0].close
        last_price = chart[-1].close

        stock_result = {
            "symbol": code,
            "name": name,
            "first_price": first_price,
            "last_price": last_price,
            "configs": [],  # 구성별 전략 결과
        }

        for cfg in CONFIGS:
            config_result = {"label": cfg["label"], "strategies": []}

            for strat in STRATEGIES:
                if strat["type"] == "sma":
                    bt = run_backtest(
                        chart,
                        initial_capital=initial_capital,
                        order_amount=cfg["order_amount"],
                        short_period=10,
                        long_period=40,
                        use_advanced=strat.get("use_advanced", False),
                        stop_loss_pct=strat.get("stop_loss", 0.0),
                        max_holding_days=strat.get("max_hold", 0),
                        volume_filter_basic=strat.get("vol_basic", False),
                        capital_ratio=cfg["capital_ratio"],
                        trailing_stop_pct=cfg["trailing_stop_pct"],
                    )
                else:
                    bt = run_bollinger_backtest(
                        chart,
                        initial_capital=initial_capital,
                        order_amount=cfg["order_amount"],
                        period=20,
                        num_std=2.0,
                        max_holding_days=20,
                        capital_ratio=cfg["capital_ratio"],
                        trailing_stop_pct=cfg["trailing_stop_pct"],
                    )

                config_result["strategies"].append({
                    "label": strat["label"],
                    "total_return_pct": bt.total_return_pct,
                    "buy_and_hold_pct": bt.buy_and_hold_pct,
                    "trade_count": bt.trade_count,
                    "win_rate": bt.win_rate,
                    "max_drawdown_pct": bt.max_drawdown_pct,
                    "sharpe_ratio": bt.sharpe_ratio,
                    "trades": [
                        {"date": t.date, "side": t.side, "price": t.price, "qty": t.quantity, "reason": t.reason}
                        for t in bt.trades
                    ],
                    "equity_curve": bt.equity_curve,
                })

            stock_result["configs"].append(config_result)

        results.append(stock_result)
        print(f"OK ({len(chart)}봉)")

    return results


def generate_html(data: list[dict]) -> str:
    """비교 리포트 HTML 생성"""
    config_labels = [c["label"] for c in CONFIGS]
    strategy_labels = [s["label"] for s in STRATEGIES]
    n_configs = len(config_labels)
    n_strategies = len(strategy_labels)

    config_colors = ["#6b7280", "#3b82f6", "#22c55e", "#f59e0b", "#a855f7"]
    strategy_colors = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444"]

    # 구성별 × 전략별 평균 수익률 집계
    agg = {}  # (config_idx, strat_idx) → list of returns
    for ci in range(n_configs):
        for si in range(n_strategies):
            key = (ci, si)
            agg[key] = {
                "returns": [],
                "mdds": [],
                "win_rates": [],
                "trades": [],
                "sharpes": [],
            }

    for row in data:
        for ci, cfg_result in enumerate(row["configs"]):
            for si, strat_result in enumerate(cfg_result["strategies"]):
                key = (ci, si)
                agg[key]["returns"].append(strat_result["total_return_pct"])
                agg[key]["mdds"].append(strat_result["max_drawdown_pct"])
                agg[key]["win_rates"].append(strat_result["win_rate"])
                agg[key]["trades"].append(strat_result["trade_count"])
                if strat_result["sharpe_ratio"] is not None:
                    agg[key]["sharpes"].append(strat_result["sharpe_ratio"])

    # B&H 평균
    bnh_list = [(r["last_price"] - r["first_price"]) / r["first_price"] * 100 for r in data]
    avg_bnh = sum(bnh_list) / len(bnh_list) if bnh_list else 0

    # 히트맵 데이터 생성 (구성 × 전략)
    heatmap_data = []
    for ci in range(n_configs):
        row_data = []
        for si in range(n_strategies):
            key = (ci, si)
            avg_ret = sum(agg[key]["returns"]) / len(agg[key]["returns"]) if agg[key]["returns"] else 0
            row_data.append(round(avg_ret, 2))
        heatmap_data.append(row_data)

    # Summary cards: 구성별 최고 전략
    summary_cards = ""
    for ci in range(n_configs):
        best_si = max(range(n_strategies), key=lambda si: sum(agg[(ci, si)]["returns"]) / max(len(agg[(ci, si)]["returns"]), 1))
        key = (ci, best_si)
        avg_ret = sum(agg[key]["returns"]) / len(agg[key]["returns"])
        avg_mdd = sum(agg[key]["mdds"]) / len(agg[key]["mdds"])
        avg_wr = sum(agg[key]["win_rates"]) / len(agg[key]["win_rates"])
        total_trades = sum(agg[key]["trades"])
        avg_sharpe = sum(agg[key]["sharpes"]) / len(agg[key]["sharpes"]) if agg[key]["sharpes"] else None
        sharpe_str = f'{avg_sharpe:.2f}' if avg_sharpe is not None else "-"
        ret_class = "positive" if avg_ret > 0 else "negative"

        summary_cards += f"""
        <div class="summary-card" style="border-top: 4px solid {config_colors[ci]}">
            <h3>{config_labels[ci]}</h3>
            <div class="metric-sub" style="margin-bottom:4px">최고 전략: {strategy_labels[best_si]}</div>
            <div class="metric-main {ret_class}">{avg_ret:+.2f}%</div>
            <div class="metric-label">평균 수익률</div>
            <div class="metric-grid">
                <div><span class="metric-value">{avg_wr:.1f}%</span><span class="metric-sub">승률</span></div>
                <div><span class="metric-value">{avg_mdd:.2f}%</span><span class="metric-sub">MDD</span></div>
                <div><span class="metric-value">{total_trades}</span><span class="metric-sub">총거래</span></div>
                <div><span class="metric-value">{sharpe_str}</span><span class="metric-sub">Sharpe</span></div>
            </div>
        </div>"""

    # B&H summary card
    bnh_class = "positive" if avg_bnh > 0 else "negative"
    summary_cards += f"""
    <div class="summary-card" style="border-top: 4px solid #fff">
        <h3>Buy & Hold</h3>
        <div class="metric-sub" style="margin-bottom:4px">패시브 벤치마크</div>
        <div class="metric-main {bnh_class}">{avg_bnh:+.2f}%</div>
        <div class="metric-label">평균 수익률</div>
        <div class="metric-grid">
            <div><span class="metric-value">-</span><span class="metric-sub">승률</span></div>
            <div><span class="metric-value">-</span><span class="metric-sub">MDD</span></div>
            <div><span class="metric-value">0</span><span class="metric-sub">총거래</span></div>
            <div><span class="metric-value">-</span><span class="metric-sub">Sharpe</span></div>
        </div>
    </div>"""

    # 히트맵 테이블
    heatmap_rows = ""
    all_vals = [v for row in heatmap_data for v in row]
    min_val = min(all_vals) if all_vals else 0
    max_val = max(all_vals) if all_vals else 1

    for ci in range(n_configs):
        cells = ""
        for si in range(n_strategies):
            val = heatmap_data[ci][si]
            # 색상 보간: 음수→빨강, 0→회색, 양수→초록
            if val >= 0:
                intensity = min(val / max(max_val, 0.01), 1.0)
                bg = f"rgba(34,197,94,{0.1 + intensity * 0.4})"
            else:
                intensity = min(abs(val) / max(abs(min_val), 0.01), 1.0)
                bg = f"rgba(239,68,68,{0.1 + intensity * 0.4})"
            val_class = "positive" if val > 0 else "negative" if val < 0 else ""
            cells += f'<td class="{val_class}" style="background:{bg};text-align:center;font-weight:600">{val:+.2f}%</td>'

        heatmap_rows += f"""
            <tr>
                <td style="font-weight:600;color:{config_colors[ci]}">{config_labels[ci]}</td>
                {cells}
            </tr>"""

    # 종목별 바차트 데이터 (구성별 최고전략 수익 vs B&H)
    bar_data = {
        "symbols": [r["name"] for r in data],
        "bnh": [round((r["last_price"] - r["first_price"]) / r["first_price"] * 100, 2) for r in data],
        "configs": [],
    }
    for ci in range(n_configs):
        cfg_returns = []
        for row in data:
            strat_rets = [s["total_return_pct"] for s in row["configs"][ci]["strategies"]]
            cfg_returns.append(round(max(strat_rets), 2))
        bar_data["configs"].append({
            "label": config_labels[ci],
            "data": cfg_returns,
            "color": config_colors[ci],
        })
    bar_json = json.dumps(bar_data, ensure_ascii=False)

    # 종목별 상세 테이블 + 상세 패널
    stock_rows = ""
    detail_sections = ""

    for row in data:
        sym = row["symbol"]
        name = row["name"]
        bnh_pct = (row["last_price"] - row["first_price"]) / row["first_price"] * 100

        # 각 구성의 최고 전략 수익률
        cfg_cells = ""
        for ci, cfg_result in enumerate(row["configs"]):
            best = max(cfg_result["strategies"], key=lambda s: s["total_return_pct"])
            ret = best["total_return_pct"]
            ret_class = "positive" if ret > 0 else "negative" if ret < 0 else ""
            cfg_cells += f'<td class="{ret_class}" style="font-weight:600">{ret:+.2f}%</td>'
            cfg_cells += f'<td style="color:#888;font-size:11px">{best["label"]}</td>'

        stock_rows += f"""
        <tr>
            <td class="stock-cell">
                <span class="stock-code">{sym}</span>
                <span class="stock-name">{name}</span>
            </td>
            <td>{row["first_price"]:,}</td>
            <td>{row["last_price"]:,}</td>
            <td class="{'positive' if bnh_pct > 0 else 'negative'}">{bnh_pct:+.1f}%</td>
            {cfg_cells}
            <td><button class="detail-btn" onclick="toggleDetail('{sym}')">상세</button></td>
        </tr>"""

        # 상세 패널: 구성별 전략 비교 테이블 + 자산 곡선
        detail_tables = ""
        equity_datasets = []
        ds_idx = 0
        for ci, cfg_result in enumerate(row["configs"]):
            detail_rows = ""
            for si, s in enumerate(cfg_result["strategies"]):
                ret_class = "positive" if s["total_return_pct"] > 0 else "negative" if s["total_return_pct"] < 0 else ""
                sharpe_str = f'{s["sharpe_ratio"]:.2f}' if s["sharpe_ratio"] is not None else "-"

                # trailing_stop 매매 건수
                ts_count = sum(1 for t in s["trades"] if t.get("reason") == "trailing_stop")
                ts_badge = f' <span class="badge badge-green">{ts_count}TS</span>' if ts_count > 0 else ""

                detail_rows += f"""
                <tr>
                    <td style="color:{strategy_colors[si]}">{s["label"]}</td>
                    <td class="{ret_class}">{s["total_return_pct"]:+.2f}%</td>
                    <td>{s["trade_count"]}</td>
                    <td>{s["win_rate"]:.1f}%</td>
                    <td>{s["max_drawdown_pct"]:.2f}%</td>
                    <td>{sharpe_str}</td>
                    <td>{ts_badge}</td>
                </tr>"""

                # 자산 곡선 (최고전략만)
                curve = s["equity_curve"]
                step = max(1, len(curve) // 200)
                sampled = curve[::step]
                line_colors = ["#6b7280", "#3b82f6", "#22c55e", "#ef4444", "#f59e0b", "#a855f7",
                               "#64748b", "#2563eb", "#16a34a", "#dc2626", "#d97706", "#9333ea"]
                color = line_colors[ds_idx % len(line_colors)]
                equity_datasets.append({
                    "label": f"{cfg_result['label']} / {s['label']}",
                    "data": sampled,
                    "color": color,
                })
                ds_idx += 1

            detail_tables += f"""
            <div class="config-detail">
                <h4 style="color:{config_colors[ci]};margin-bottom:8px">{cfg_result["label"]}</h4>
                <table class="trade-table">
                    <thead><tr><th>전략</th><th>수익률</th><th>거래</th><th>승률</th><th>MDD</th><th>SR</th><th></th></tr></thead>
                    <tbody>{detail_rows}</tbody>
                </table>
            </div>"""

        equity_json = json.dumps(equity_datasets, ensure_ascii=False)
        detail_sections += f"""
        <div id="detail-{sym}" class="detail-panel" style="display:none">
            <h3>{sym} {name} 상세 비교</h3>
            <div class="chart-container"><canvas id="chart-{sym}"></canvas></div>
            <script>window.chartData_{sym} = {equity_json};</script>
            <div class="configs-grid">{detail_tables}</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>자본 활용률 개선 효과 비교</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Pretendard', sans-serif; background: #0f1117; color: #e0e0e0; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
header {{ text-align: center; padding: 40px 0 24px; }}
header h1 {{ font-size: 28px; font-weight: 700; color: #fff; }}
header p {{ color: #888; margin-top: 8px; font-size: 14px; }}
.summary-row {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 24px 0; }}
.summary-card {{ background: #1a1d27; border-radius: 12px; padding: 20px; }}
.summary-card h3 {{ font-size: 14px; color: #aaa; margin-bottom: 4px; }}
.metric-main {{ font-size: 32px; font-weight: 700; }}
.metric-label {{ font-size: 12px; color: #666; margin-bottom: 12px; }}
.metric-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }}
.metric-value {{ font-size: 16px; font-weight: 600; display: block; }}
.metric-sub {{ font-size: 11px; color: #666; }}
.positive {{ color: #22c55e; }}
.negative {{ color: #ef4444; }}
.section {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 24px 0; }}
.section h2 {{ font-size: 18px; margin-bottom: 16px; color: #fff; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: #252830; color: #aaa; font-weight: 600; padding: 10px 8px; text-align: right; white-space: nowrap; }}
th:first-child {{ text-align: left; }}
td {{ padding: 10px 8px; border-bottom: 1px solid #252830; text-align: right; white-space: nowrap; }}
td:first-child {{ text-align: left; }}
.stock-cell {{ display: flex; flex-direction: column; gap: 2px; }}
.stock-code {{ font-weight: 600; color: #fff; font-size: 13px; }}
.stock-name {{ color: #888; font-size: 11px; }}
.detail-btn {{ background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 4px 12px; cursor: pointer; font-size: 12px; }}
.detail-btn:hover {{ background: #1d4ed8; }}
.detail-panel {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 12px 0; }}
.detail-panel h3 {{ font-size: 16px; color: #fff; margin-bottom: 16px; }}
.chart-container {{ height: 300px; margin-bottom: 24px; }}
.configs-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 16px; }}
.config-detail h4 {{ font-size: 14px; }}
.trade-table {{ font-size: 12px; }}
.trade-table th {{ background: #1e2028; font-size: 11px; padding: 6px; }}
.trade-table td {{ padding: 5px 6px; border-bottom: 1px solid #1e2028; }}
.badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }}
.badge-green {{ background: rgba(34,197,94,0.15); color: #4ade80; }}
.heatmap-table td, .heatmap-table th {{ text-align: center; padding: 12px 16px; }}
footer {{ text-align: center; padding: 32px; color: #555; font-size: 12px; }}
@media (max-width: 900px) {{
    .summary-row {{ grid-template-columns: repeat(2, 1fr); }}
    .configs-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>자본 활용률 개선 효과 비교</h1>
        <p>2년간 백테스트 | 초기자본 1,000만원 | {len(data)}개 종목 | 구성 {n_configs}가지 x 전략 {n_strategies}가지</p>
    </header>

    <div class="summary-row">{summary_cards}</div>

    <div class="section">
        <h2>구성별 x 전략별 평균 수익률 히트맵</h2>
        <table class="heatmap-table">
            <thead>
                <tr>
                    <th style="text-align:left">구성</th>
                    {"".join(f'<th style="color:{strategy_colors[si]}">{strategy_labels[si]}</th>' for si in range(n_strategies))}
                </tr>
            </thead>
            <tbody>{heatmap_rows}</tbody>
        </table>
    </div>

    <div class="section">
        <h2>종목별 최고 전략 수익률 비교</h2>
        <div style="height:400px"><canvas id="overviewChart"></canvas></div>
    </div>

    <div class="section">
        <h2>종목별 상세</h2>
        <table>
            <thead>
                <tr>
                    <th>종목</th>
                    <th>시작가</th>
                    <th>종가</th>
                    <th>B&H</th>
                    {"".join(f'<th style="color:{config_colors[ci]}">{config_labels[ci]}</th><th></th>' for ci in range(n_configs))}
                    <th></th>
                </tr>
            </thead>
            <tbody>{stock_rows}</tbody>
        </table>
    </div>

    {detail_sections}
</div>

<footer>Quantum Trading Platform — Capital Utilization Comparison Report</footer>

<script>
const barData = {bar_json};
const ctx = document.getElementById('overviewChart').getContext('2d');
const datasets = [
    {{ label: 'Buy & Hold', data: barData.bnh, backgroundColor: 'rgba(255,255,255,0.12)', borderColor: '#555', borderWidth: 1, borderRadius: 3 }},
    ...barData.configs.map(c => ({{
        label: c.label, data: c.data, backgroundColor: c.color + '99', borderColor: c.color, borderWidth: 1, borderRadius: 3
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
                    plugins: {{ legend: {{ labels: {{ color: '#aaa', font: {{ size: 10 }} }} }} }},
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
    print("=== 자본 활용률 개선 효과 비교 백테스트 ===")
    print()
    data = run_all()

    html = generate_html(data)
    out = "capital_comparison_report.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"\nReport: {out}")

    # 콘솔 요약
    print("\n--- 구성별 평균 수익률 ---")
    for ci, cfg in enumerate(CONFIGS):
        for si, strat in enumerate(STRATEGIES):
            returns = [row["configs"][ci]["strategies"][si]["total_return_pct"] for row in data]
            avg = sum(returns) / len(returns) if returns else 0
            print(f"  {cfg['label']:20s} | {strat['label']:16s} | {avg:+.2f}%")
        print()

    bnh = [(r["last_price"] - r["first_price"]) / r["first_price"] * 100 for r in data]
    print(f"  {'Buy & Hold':20s} | {'':16s} | {sum(bnh)/len(bnh):+.2f}%")
