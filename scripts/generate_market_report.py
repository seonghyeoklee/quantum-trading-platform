"""시장 국면 분석 HTML 리포트 생성"""

import json


def generate_html(data: dict) -> str:
    indices = data["indices"]
    ka = data["kospi_analysis"]

    # Regime styling
    regime_colors = {
        "strong_bull": ("#22c55e", "rgba(34,197,94,0.15)"),
        "bull": ("#4ade80", "rgba(74,222,128,0.15)"),
        "sideways": ("#facc15", "rgba(250,204,21,0.15)"),
        "bear": ("#f87171", "rgba(248,113,113,0.15)"),
        "strong_bear": ("#ef4444", "rgba(239,68,68,0.15)"),
    }
    regime_emoji = {
        "strong_bull": "&#x1F680;",
        "bull": "&#x2197;&#xFE0F;",
        "sideways": "&#x2194;&#xFE0F;",
        "bear": "&#x2198;&#xFE0F;",
        "strong_bear": "&#x1F4C9;",
    }
    rc, rbg = regime_colors.get(ka["regime"], ("#888", "rgba(136,136,136,0.15)"))
    re = regime_emoji.get(ka["regime"], "")

    # Performance cards
    perf = ka["perf"]
    def perf_class(v):
        if v is None:
            return "", "-"
        return ("positive" if v > 0 else "negative" if v < 0 else ""), f"{v:+.1f}%"

    # SMA position description
    last = ka["last"]
    sma_desc_parts = []
    for label, val in [("SMA20", ka["sma20"]), ("SMA60", ka["sma60"]), ("SMA120", ka["sma120"])]:
        diff_pct = (last - val) / val * 100
        pos = "위" if last > val else "아래"
        sma_desc_parts.append(f'{label} {pos} ({diff_pct:+.1f}%)')
    sma_desc = " | ".join(sma_desc_parts)

    # RSI description
    rsi_val = ka["rsi14"]
    if rsi_val >= 70:
        rsi_desc, rsi_color = "과매수 구간", "#ef4444"
    elif rsi_val <= 30:
        rsi_desc, rsi_color = "과매도 구간", "#22c55e"
    elif rsi_val >= 60:
        rsi_desc, rsi_color = "강세", "#4ade80"
    elif rsi_val <= 40:
        rsi_desc, rsi_color = "약세", "#f87171"
    else:
        rsi_desc, rsi_color = "중립", "#facc15"

    # Global index performance table
    global_rows = ""
    for ticker in ["^KS11", "^KQ11", "^GSPC", "^IXIC", "^VIX", "USDKRW=X"]:
        if ticker not in indices:
            continue
        idx = indices[ticker]
        vals = idx["values"]
        def _pct(days):
            if len(vals) < days + 1:
                return "-"
            p = (vals[-1] - vals[-days-1]) / vals[-days-1] * 100
            cls = "positive" if p > 0 else "negative" if p < 0 else ""
            return f'<span class="{cls}">{p:+.1f}%</span>'
        global_rows += f"""
        <tr>
            <td><strong>{idx["name"]}</strong><br><span class="ticker">{ticker}</span></td>
            <td>{vals[-1]:,.1f}</td>
            <td>{_pct(5)}</td>
            <td>{_pct(21)}</td>
            <td>{_pct(63)}</td>
            <td>{_pct(252)}</td>
        </tr>"""

    # Chart data
    kospi_dates = json.dumps(indices["^KS11"]["dates"])
    kospi_closes = json.dumps(indices["^KS11"]["values"])
    kospi_sma20 = json.dumps(ka["sma20_series"])
    kospi_sma60 = json.dumps(ka["sma60_series"])
    kospi_sma120 = json.dumps(ka["sma120_series"])
    kospi_rsi = json.dumps(ka["rsi14_series"])

    # Normalized comparison (base 100)
    norm_datasets = []
    colors_map = {"^KS11": "#3b82f6", "^KQ11": "#8b5cf6", "^GSPC": "#f59e0b", "^IXIC": "#10b981"}
    for ticker, color in colors_map.items():
        if ticker not in indices:
            continue
        vals = indices[ticker]["values"]
        base = vals[0] if vals[0] != 0 else 1
        normed = [round(v / base * 100, 2) for v in vals]
        norm_datasets.append({
            "label": indices[ticker]["name"],
            "data": normed,
            "color": color,
        })
    norm_json = json.dumps(norm_datasets, ensure_ascii=False)
    norm_dates = json.dumps(indices["^KS11"]["dates"])

    # Analysis text
    analysis_points = []
    if ka["regime"] in ("strong_bull", "bull"):
        analysis_points.append("코스피가 모든 주요 이동평균선 위에 위치 — 추세 매매 유리")
    if rsi_val >= 70:
        analysis_points.append(f"RSI {rsi_val:.0f} — 과매수 경고. 단기 조정 가능성 주의")
    if ka["from_high_pct"] > -3:
        analysis_points.append(f"52주 신고가 근접 ({ka['from_high_pct']:+.1f}%) — 돌파 시 추가 상승 모멘텀")
    if perf["1m"] and perf["1m"] > 10:
        analysis_points.append(f"1개월 {perf['1m']:+.1f}% 급등 — 과열 구간 진입 가능성")

    # VIX/KRW analysis
    if "^VIX" in indices:
        vix_last = indices["^VIX"]["values"][-1]
        if vix_last < 15:
            analysis_points.append(f"VIX {vix_last:.1f} — 낮은 변동성, 안정적 시장")
        elif vix_last > 25:
            analysis_points.append(f"VIX {vix_last:.1f} — 높은 변동성, 위험 선호 감소")
    if "USDKRW=X" in indices:
        krw = indices["USDKRW=X"]["values"][-1]
        krw_vals = indices["USDKRW=X"]["values"]
        krw_1m = (krw - krw_vals[-22]) / krw_vals[-22] * 100 if len(krw_vals) >= 22 else 0
        if krw_1m < -2:
            analysis_points.append(f"원화 강세 (1개월 {krw_1m:+.1f}%) — 외국인 자금 유입 우호적")
        elif krw_1m > 2:
            analysis_points.append(f"원화 약세 (1개월 {krw_1m:+.1f}%) — 외국인 매도 압력 가능")

    # Strategy implication
    if ka["regime"] in ("strong_bull", "bull"):
        strategy_text = """
        <div class="strategy-box bull">
            <h4>전략 시사점: 추세 추종 유리</h4>
            <ul>
                <li>SMA 크로스오버 — 강세장에서는 B&amp;H 대비 열위. <strong>손절을 넓게</strong> (7~10%) 잡아 추세에 오래 탈 것</li>
                <li>볼린저 단타 — MDD는 낮지만 상승분 대부분을 놓침. 보조 전략으로만 활용</li>
                <li><strong>핵심</strong>: 현 국면에서는 매수 후 보유(B&amp;H)가 가장 효율적. 매도 시그널을 보수적으로 운용</li>
            </ul>
        </div>"""
    elif ka["regime"] in ("strong_bear", "bear"):
        strategy_text = """
        <div class="strategy-box bear">
            <h4>전략 시사점: 리스크 관리 우선</h4>
            <ul>
                <li>SMA 크로스오버 + 손절(5%) — 하락장에서 손실 제한 효과</li>
                <li>볼린저 단타 — 하단 반등 매수로 단기 수익 기회</li>
                <li><strong>핵심</strong>: 포지션 축소, 현금 비중 확대, 손절 타이트하게</li>
            </ul>
        </div>"""
    else:
        strategy_text = """
        <div class="strategy-box sideways">
            <h4>전략 시사점: 혼합 운용</h4>
            <ul>
                <li>SMA 크로스오버 — 횡보 시 잦은 크로스로 손실 누적 위험. Advanced 필터 권장</li>
                <li>볼린저 단타 — 밴드 내 반복 매매로 수익 기회</li>
                <li><strong>핵심</strong>: 추세 전환 확인 후 방향성 매매, 그전까지 보수적 운용</li>
            </ul>
        </div>"""

    analysis_html = "\n".join(f"<li>{p}</li>" for p in analysis_points)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>시장 국면 분석 리포트</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Pretendard', sans-serif; background: #0f1117; color: #e0e0e0; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
header {{ text-align: center; padding: 40px 0 16px; }}
header h1 {{ font-size: 28px; font-weight: 700; color: #fff; }}
header p {{ color: #888; margin-top: 8px; font-size: 14px; }}

.regime-banner {{ background: {rbg}; border: 1px solid {rc}; border-radius: 16px; padding: 32px; margin: 24px 0; text-align: center; }}
.regime-badge {{ display: inline-block; background: {rc}22; border: 1px solid {rc}; border-radius: 8px; padding: 6px 20px; font-size: 14px; font-weight: 600; color: {rc}; margin-bottom: 12px; }}
.regime-value {{ font-size: 48px; font-weight: 800; color: #fff; }}
.regime-label {{ font-size: 14px; color: #aaa; margin-top: 4px; }}
.regime-sma {{ font-size: 13px; color: #888; margin-top: 12px; }}

.perf-row {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 20px 0; }}
.perf-card {{ background: #1a1d27; border-radius: 10px; padding: 16px; text-align: center; }}
.perf-card .label {{ font-size: 12px; color: #888; }}
.perf-card .value {{ font-size: 22px; font-weight: 700; margin-top: 4px; }}
.positive {{ color: #22c55e; }}
.negative {{ color: #ef4444; }}

.section {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 20px 0; }}
.section h2 {{ font-size: 18px; color: #fff; margin-bottom: 16px; }}
.chart-box {{ height: 350px; }}
.chart-box-sm {{ height: 150px; }}

.indicator-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }}
.indicator {{ background: #1a1d27; border-radius: 10px; padding: 16px; }}
.indicator .label {{ font-size: 12px; color: #888; }}
.indicator .val {{ font-size: 20px; font-weight: 700; color: #fff; margin-top: 4px; }}
.indicator .sub {{ font-size: 11px; color: #666; margin-top: 2px; }}

table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: #252830; color: #aaa; font-weight: 600; padding: 10px 12px; text-align: right; }}
th:first-child {{ text-align: left; }}
td {{ padding: 10px 12px; border-bottom: 1px solid #252830; text-align: right; }}
td:first-child {{ text-align: left; }}
.ticker {{ color: #555; font-size: 11px; }}

.analysis-box {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 20px 0; }}
.analysis-box h2 {{ font-size: 18px; color: #fff; margin-bottom: 16px; }}
.analysis-box ul {{ list-style: none; }}
.analysis-box li {{ padding: 8px 0; border-bottom: 1px solid #252830; font-size: 14px; line-height: 1.6; }}
.analysis-box li::before {{ content: "\\25CF "; color: {rc}; margin-right: 8px; }}

.strategy-box {{ border-radius: 12px; padding: 24px; margin: 20px 0; }}
.strategy-box.bull {{ background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.3); }}
.strategy-box.bear {{ background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3); }}
.strategy-box.sideways {{ background: rgba(250,204,21,0.08); border: 1px solid rgba(250,204,21,0.3); }}
.strategy-box h4 {{ font-size: 16px; color: #fff; margin-bottom: 12px; }}
.strategy-box ul {{ padding-left: 20px; }}
.strategy-box li {{ padding: 4px 0; font-size: 14px; line-height: 1.6; color: #ccc; }}
.strategy-box strong {{ color: #fff; }}

footer {{ text-align: center; padding: 32px; color: #555; font-size: 12px; }}
@media (max-width: 768px) {{
    .perf-row {{ grid-template-columns: repeat(3, 1fr); }}
    .indicator-row {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>시장 국면 분석</h1>
        <p>yfinance 기반 | {indices['^KS11']['dates'][-1]} 기준 | 2023.01 ~ 현재</p>
    </header>

    <div class="regime-banner">
        <div class="regime-badge">{re} {ka['regime_kr']}</div>
        <div class="regime-value">KOSPI {last:,.0f}</div>
        <div class="regime-label">52주 고점 {ka['high_52w']:,.0f} ({ka['from_high_pct']:+.1f}%) | 52주 저점 {ka['low_52w']:,.0f} ({ka['from_low_pct']:+.1f}%)</div>
        <div class="regime-sma">{sma_desc}</div>
    </div>

    <div class="perf-row">
        <div class="perf-card"><div class="label">1주</div><div class="value {perf_class(perf['1w'])[0]}">{perf_class(perf['1w'])[1]}</div></div>
        <div class="perf-card"><div class="label">1개월</div><div class="value {perf_class(perf['1m'])[0]}">{perf_class(perf['1m'])[1]}</div></div>
        <div class="perf-card"><div class="label">3개월</div><div class="value {perf_class(perf['3m'])[0]}">{perf_class(perf['3m'])[1]}</div></div>
        <div class="perf-card"><div class="label">6개월</div><div class="value {perf_class(perf['6m'])[0]}">{perf_class(perf['6m'])[1]}</div></div>
        <div class="perf-card"><div class="label">1년</div><div class="value {perf_class(perf['1y'])[0]}">{perf_class(perf['1y'])[1]}</div></div>
    </div>

    <div class="indicator-row">
        <div class="indicator">
            <div class="label">SMA 20</div>
            <div class="val">{ka['sma20']:,.0f}</div>
            <div class="sub">{'위' if last > ka['sma20'] else '아래'} {abs((last - ka['sma20']) / ka['sma20'] * 100):.1f}%</div>
        </div>
        <div class="indicator">
            <div class="label">SMA 60</div>
            <div class="val">{ka['sma60']:,.0f}</div>
            <div class="sub">{'위' if last > ka['sma60'] else '아래'} {abs((last - ka['sma60']) / ka['sma60'] * 100):.1f}%</div>
        </div>
        <div class="indicator">
            <div class="label">SMA 120</div>
            <div class="val">{ka['sma120']:,.0f}</div>
            <div class="sub">{'위' if last > ka['sma120'] else '아래'} {abs((last - ka['sma120']) / ka['sma120'] * 100):.1f}%</div>
        </div>
        <div class="indicator">
            <div class="label">RSI (14)</div>
            <div class="val" style="color:{rsi_color}">{rsi_val:.1f}</div>
            <div class="sub">{rsi_desc}</div>
        </div>
    </div>

    <div class="section">
        <h2>코스피 지수 + 이동평균선</h2>
        <div class="chart-box"><canvas id="kospiChart"></canvas></div>
    </div>

    <div class="section">
        <h2>RSI (14)</h2>
        <div class="chart-box-sm"><canvas id="rsiChart"></canvas></div>
    </div>

    <div class="section">
        <h2>글로벌 지수 비교 (2023.01 = 100)</h2>
        <div class="chart-box"><canvas id="normChart"></canvas></div>
    </div>

    <div class="section">
        <h2>글로벌 지수 수익률</h2>
        <table>
            <thead><tr><th>지수</th><th>현재</th><th>1주</th><th>1개월</th><th>3개월</th><th>1년</th></tr></thead>
            <tbody>{global_rows}</tbody>
        </table>
    </div>

    <div class="analysis-box">
        <h2>시장 분석 요약</h2>
        <ul>{analysis_html}</ul>
    </div>

    {strategy_text}
</div>

<footer>Quantum Trading Platform — Market Regime Analysis</footer>

<script>
const dates = {kospi_dates};
const closes = {kospi_closes};
const sma20 = {kospi_sma20};
const sma60 = {kospi_sma60};
const sma120 = {kospi_sma120};
const rsiData = {kospi_rsi};

// Step for labels
const step = Math.max(1, Math.floor(dates.length / 12));
const labels = dates.map((d, i) => i % step === 0 ? d.slice(2, 7) : '');

// KOSPI + SMA chart
new Chart(document.getElementById('kospiChart'), {{
    type: 'line',
    data: {{
        labels: labels,
        datasets: [
            {{ label: '코스피', data: closes, borderColor: '#3b82f6', borderWidth: 2, pointRadius: 0, fill: false }},
            {{ label: 'SMA 20', data: sma20, borderColor: '#f59e0b', borderWidth: 1.2, pointRadius: 0, borderDash: [4,2], fill: false }},
            {{ label: 'SMA 60', data: sma60, borderColor: '#10b981', borderWidth: 1.2, pointRadius: 0, borderDash: [4,2], fill: false }},
            {{ label: 'SMA 120', data: sma120, borderColor: '#ef4444', borderWidth: 1.2, pointRadius: 0, borderDash: [6,3], fill: false }},
        ]
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ labels: {{ color: '#aaa', font: {{ size: 11 }} }} }} }},
        scales: {{
            x: {{ ticks: {{ color: '#666', font: {{ size: 10 }}, maxRotation: 0 }}, grid: {{ color: '#1e2028' }} }},
            y: {{ ticks: {{ color: '#888', callback: v => v.toLocaleString() }}, grid: {{ color: '#1e2028' }} }}
        }}
    }}
}});

// RSI chart
new Chart(document.getElementById('rsiChart'), {{
    type: 'line',
    data: {{
        labels: labels,
        datasets: [{{ label: 'RSI', data: rsiData, borderColor: '#8b5cf6', borderWidth: 1.5, pointRadius: 0, fill: false }}]
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
            legend: {{ display: false }},
            annotation: {{ annotations: {{}} }}
        }},
        scales: {{
            x: {{ ticks: {{ color: '#666', font: {{ size: 10 }}, maxRotation: 0 }}, grid: {{ color: '#1e2028' }} }},
            y: {{ min: 0, max: 100, ticks: {{ color: '#888', stepSize: 10 }}, grid: {{ color: '#1e2028' }} }}
        }}
    }},
    plugins: [{{
        afterDraw(chart) {{
            const ctx = chart.ctx;
            const yAxis = chart.scales.y;
            const xAxis = chart.scales.x;
            // Overbought line
            const y70 = yAxis.getPixelForValue(70);
            ctx.save();
            ctx.strokeStyle = 'rgba(239,68,68,0.4)';
            ctx.setLineDash([4,4]);
            ctx.beginPath(); ctx.moveTo(xAxis.left, y70); ctx.lineTo(xAxis.right, y70); ctx.stroke();
            // Oversold line
            const y30 = yAxis.getPixelForValue(30);
            ctx.strokeStyle = 'rgba(34,197,94,0.4)';
            ctx.beginPath(); ctx.moveTo(xAxis.left, y30); ctx.lineTo(xAxis.right, y30); ctx.stroke();
            ctx.restore();
        }}
    }}]
}});

// Normalized comparison
const normData = {norm_json};
const normDates = {norm_dates};
const normStep = Math.max(1, Math.floor(normDates.length / 12));
const normLabels = normDates.map((d, i) => i % normStep === 0 ? d.slice(2, 7) : '');
new Chart(document.getElementById('normChart'), {{
    type: 'line',
    data: {{
        labels: normLabels,
        datasets: normData.map(d => ({{
            label: d.label, data: d.data, borderColor: d.color, borderWidth: 1.5, pointRadius: 0, fill: false
        }}))
    }},
    options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ labels: {{ color: '#aaa', font: {{ size: 11 }} }} }} }},
        scales: {{
            x: {{ ticks: {{ color: '#666', font: {{ size: 10 }}, maxRotation: 0 }}, grid: {{ color: '#1e2028' }} }},
            y: {{ ticks: {{ color: '#888', callback: v => v }}, grid: {{ color: '#1e2028' }} }}
        }}
    }}
}});
</script>
</body>
</html>"""
    return html


if __name__ == "__main__":
    with open("/tmp/market_analysis.json") as f:
        data = json.load(f)
    html = generate_html(data)
    out = "market_analysis_report.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"Report: {out}")
