#!/usr/bin/env python3
"""시나리오 백테스트 HTML 리포트 생성.

Usage:
    uv run python scripts/generate_scenario_report.py
    → scenario_test_report.html 생성
"""

import sys
from datetime import date
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.report_theme import wrap_html
from app.trading.scenario import SCENARIOS, ScenarioResult, get_fixture_meta, run_all_scenarios
from app.trading.strategy import compute_bollinger_bands


EXTRA_CSS = """
.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
@media (max-width: 768px) {
    .summary-grid { grid-template-columns: repeat(2, 1fr); }
}

.category-section { margin-bottom: 32px; }
.category-title {
    font-size: 18px; font-weight: 700; color: #fff;
    padding: 12px 0; border-bottom: 1px solid #333; margin-bottom: 16px;
}

.scenario-card {
    background: #1a1d27; border-radius: 10px; padding: 20px;
    margin-bottom: 20px;
}
.scenario-header { display: flex; align-items: center; gap: 10px; }
.scenario-status { font-size: 18px; }
.scenario-name { font-weight: 600; color: #fff; font-size: 15px; }
.scenario-desc { color: #888; font-size: 12px; margin-top: 4px; }

.check-list { margin-top: 12px; padding-left: 8px; }
.check-item { font-size: 12px; padding: 4px 0; color: #ccc; }
.check-pass { color: #4ade80; }
.check-fail { color: #f87171; }

.chart-container { height: 300px; margin: 16px 0; }

.trade-table { width: 100%; font-size: 12px; margin-top: 12px; }
.trade-table th {
    background: #252830; color: #aaa; font-weight: 600;
    padding: 6px 8px; text-align: left; font-size: 11px;
}
.trade-table td {
    padding: 5px 8px; border-bottom: 1px solid #252830;
    text-align: left;
}

.metrics-row {
    display: flex; gap: 24px; margin-top: 12px; flex-wrap: wrap;
}
.metric-item { font-size: 12px; color: #aaa; }
.metric-item span { font-weight: 600; color: #fff; }

.intro-section {
    background: #1a1d27; border-radius: 12px; padding: 24px; margin-bottom: 24px;
    border-left: 3px solid #2563eb;
}
.intro-section h2 { font-size: 16px; color: #fff; margin-bottom: 12px; }
.intro-section p { font-size: 13px; color: #aaa; line-height: 1.7; margin-bottom: 8px; }
.intro-section code { background: #252830; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #93c5fd; }

.analysis-section {
    background: #1a1d27; border-radius: 12px; padding: 24px; margin-bottom: 28px;
    border-left: 3px solid #22c55e;
}
.analysis-section.warn { border-left-color: #f59e0b; }
.analysis-section.fail { border-left-color: #ef4444; }
.analysis-section h2 { font-size: 17px; color: #fff; margin-bottom: 16px; }
.analysis-section h3 { font-size: 14px; color: #60a5fa; margin: 18px 0 8px; }
.analysis-section h3:first-of-type { margin-top: 0; }
.analysis-section p { font-size: 13px; color: #bbb; line-height: 1.7; margin-bottom: 6px; }
.analysis-section ul { margin: 6px 0 10px 18px; font-size: 13px; color: #aaa; line-height: 1.8; }
.analysis-section li { margin-bottom: 2px; }
.analysis-section strong { color: #fff; }
.analysis-section .pair-row {
    display: flex; gap: 12px; margin: 4px 0; font-size: 12px;
}
.pair-ok { color: #4ade80; }
.pair-fail { color: #f87171; }

.coverage-grid {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
    margin: 12px 0;
}
@media (max-width: 768px) {
    .coverage-grid { grid-template-columns: 1fr; }
}
.coverage-card {
    background: #151820; border-radius: 8px; padding: 14px;
}
.coverage-card h4 {
    font-size: 12px; color: #60a5fa; margin-bottom: 8px;
    text-transform: uppercase; letter-spacing: 0.5px;
}
.coverage-card .cov-feature { font-size: 13px; color: #fff; font-weight: 600; }
.coverage-card .cov-detail { font-size: 12px; color: #888; margin-top: 4px; line-height: 1.5; }
.coverage-card .cov-scenarios { font-size: 11px; color: #666; margin-top: 6px; }

.category-desc {
    font-size: 13px; color: #888; margin-bottom: 16px; line-height: 1.6;
    padding: 12px 16px; background: #151820; border-radius: 8px;
}

.context-block {
    margin-top: 14px; padding: 14px; background: #151820; border-radius: 8px;
    font-size: 12px; line-height: 1.7;
}
.context-block dt {
    color: #60a5fa; font-weight: 600; font-size: 11px;
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-top: 10px; margin-bottom: 4px;
}
.context-block dt:first-child { margin-top: 0; }
.context-block dd { color: #bbb; margin-left: 0; }

.param-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.param-tag {
    display: inline-block; padding: 3px 8px; border-radius: 4px;
    font-size: 11px; font-weight: 500;
    background: rgba(59,130,246,0.12); color: #93c5fd;
}

.detail-divider {
    margin-top: 16px; padding-top: 16px;
    border-top: 1px solid #252830;
}

.data-source-badge {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 10px; font-weight: 600; letter-spacing: 0.3px;
    margin-left: 8px; vertical-align: middle;
}
.data-source-badge.real {
    background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3);
}
.data-source-badge.synthetic {
    background: rgba(249,115,22,0.15); color: #fb923c; border: 1px solid rgba(249,115,22,0.3);
}
.data-source-detail {
    font-size: 11px; color: #666; margin-top: 2px;
}
"""


def _build_summary_cards(results: list[ScenarioResult]) -> str:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    rate = passed / total * 100 if total > 0 else 0

    rate_color = "#4ade80" if rate == 100 else "#fbbf24" if rate >= 80 else "#f87171"

    return f"""
    <div class="summary-grid">
        <div class="summary-card">
            <h3>전체 시나리오</h3>
            <div class="metric-main">{total}</div>
        </div>
        <div class="summary-card">
            <h3>PASS</h3>
            <div class="metric-main positive">{passed}</div>
        </div>
        <div class="summary-card">
            <h3>FAIL</h3>
            <div class="metric-main {'negative' if failed > 0 else ''}">{failed}</div>
        </div>
        <div class="summary-card">
            <h3>합격률</h3>
            <div class="metric-main" style="color: {rate_color}">{rate:.0f}%</div>
        </div>
    </div>
    """


def _build_analysis(results: list[ScenarioResult]) -> str:
    """종합 분석 섹션 생성."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    rate = passed / total * 100 if total > 0 else 0

    by_name = {r.scenario.name: r for r in results}
    risk_results = [r for r in results if r.scenario.category == "risk_management"]
    signal_results = [r for r in results if r.scenario.category == "signal_quality"]
    risk_pass = sum(1 for r in risk_results if r.passed)
    signal_pass = sum(1 for r in signal_results if r.passed)

    # 전체 판정
    if rate == 100:
        border_cls = ""
        verdict = "모든 시나리오 PASS — 4개 신규 기능이 설계 의도대로 정상 동작합니다."
        verdict_color = "#4ade80"
    elif rate >= 80:
        border_cls = " warn"
        verdict = f"{failed}개 시나리오 FAIL — 일부 기능에서 예상과 다른 동작이 발견되었습니다. 아래 상세 분석을 확인하세요."
        verdict_color = "#fbbf24"
    else:
        border_cls = " fail"
        verdict = f"{failed}개 시나리오 FAIL — 핵심 기능에 문제가 있습니다. 즉시 수정이 필요합니다."
        verdict_color = "#f87171"

    # 기능별 커버리지 분석
    features = [
        {
            "name": "trailing_stop_grace_minutes",
            "label": "트레일링 스탑 유예 기간",
            "desc": "매수 직후 일시적 변동에 의한 조기 손절 방지. 유예 시간 내에는 트레일링 스탑이 비활성.",
            "scenarios": ["crash_in_grace", "crash_after_grace"],
            "pair_desc": "유예 내 급락(미발동) vs 유예 후 급락(발동)",
        },
        {
            "name": "stop_loss_pct",
            "label": "손절 (Stop-Loss)",
            "desc": "매수가 대비 N% 이상 하락 시 강제 매도. V자 반등 시에는 미발동.",
            "scenarios": ["v_recovery", "gradual_decline"],
            "pair_desc": "안정적 종목 반등(미발동) vs 하락 종목 손절(발동)",
        },
        {
            "name": "min_profit_pct",
            "label": "최소 수익률 게이트",
            "desc": "상단밴드 도달 시 수수료 이하 소액 이익이면 매도 보류. 손실 상태에서는 게이트 미적용.",
            "scenarios": ["small_profit_block", "loss_sell_allowed"],
            "pair_desc": "소액 이익(매도 보류) vs 손실 상태(매도 허용)",
        },
        {
            "name": "min_bandwidth",
            "label": "밴드 폭 최소 필터",
            "desc": "볼린저 밴드가 좁을 때(변동성 부족) 의미 없는 매수 시그널 차단.",
            "scenarios": ["largecap_low_vol", "narrow_oscillation"],
            "pair_desc": "T-Bill ETF 저변동(차단) + 단기 국채 ETF(차단)",
        },
    ]

    coverage_cards = ""
    all_feature_pass = True
    for f in features:
        f_pass = all(by_name[s].passed for s in f["scenarios"] if s in by_name)
        if not f_pass:
            all_feature_pass = False
        icon = "\u2705" if f_pass else "\u274c"
        scenario_tags = " / ".join(
            f'<span class="{"pair-ok" if by_name[s].passed else "pair-fail"}">{s}</span>'
            for s in f["scenarios"] if s in by_name
        )
        coverage_cards += f"""
        <div class="coverage-card">
            <h4>{icon} {f['label']}</h4>
            <div class="cov-feature">{f['name']}</div>
            <div class="cov-detail">{f['desc']}</div>
            <div class="cov-detail" style="margin-top:6px"><strong>짝 검증:</strong> {f['pair_desc']}</div>
            <div class="cov-scenarios">시나리오: {scenario_tags}</div>
        </div>
        """

    # 짝(pair) 테스트 분석
    pairs = [
        ("crash_in_grace", "crash_after_grace", "트레일링 스탑 유예 경계"),
        ("v_recovery", "gradual_decline", "손절선 경계 (4% vs 5%+)"),
        ("small_profit_block", "loss_sell_allowed", "수익률 게이트 경계 (이익 vs 손실)"),
        ("largecap_low_vol", "narrow_oscillation", "밴드 폭 필터 (저변동 + 횡보)"),
    ]

    pair_rows = ""
    for a, b, desc in pairs:
        ra = by_name.get(a)
        rb = by_name.get(b)
        if not ra or not rb:
            continue
        a_ok = ra.passed
        b_ok = rb.passed
        both_ok = a_ok and b_ok
        icon = "\u2705" if both_ok else "\u274c"
        cls_a = "pair-ok" if a_ok else "pair-fail"
        cls_b = "pair-ok" if b_ok else "pair-fail"
        pair_rows += f"""
        <div class="pair-row">
            <span>{icon}</span>
            <span style="color:#fff;min-width:180px">{desc}</span>
            <span class="{cls_a}">{a} {'PASS' if a_ok else 'FAIL'}</span>
            <span style="color:#555">/</span>
            <span class="{cls_b}">{b} {'PASS' if b_ok else 'FAIL'}</span>
        </div>
        """

    # 추가 시나리오: upper_touch_sell, long_holding
    extra_scenarios = ""
    for name, desc in [
        ("upper_touch_sell", "볼린저 상단 도달 시그널 매도가 손절보다 먼저 작동"),
        ("long_holding", "밴드 안 횡보로 시그널이 없을 때 max_holding이 교착 해소"),
    ]:
        r = by_name.get(name)
        if r:
            icon = "\u2705" if r.passed else "\u274c"
            extra_scenarios += f"<li>{icon} <strong>{name}</strong> — {desc}</li>"

    # FAIL 시나리오 상세
    fail_detail = ""
    fail_results = [r for r in results if not r.passed]
    if fail_results:
        fail_items = ""
        for r in fail_results:
            failed_checks = [c for c in r.checks if not c[1]]
            check_lines = "".join(
                f'<li class="pair-fail">{name}: {detail}</li>'
                for name, _, detail in failed_checks
            )
            fail_items += f"""
            <li>
                <strong>{r.scenario.name}</strong> — {r.scenario.description}
                <ul>{check_lines}</ul>
            </li>
            """
        fail_detail = f"""
        <h3>FAIL 시나리오 상세</h3>
        <ul>{fail_items}</ul>
        """

    return f"""
    <div class="analysis-section{border_cls}">
        <h2>종합 분석</h2>
        <p style="font-size:14px;color:{verdict_color};font-weight:600;margin-bottom:16px">{verdict}</p>

        <h3>기능별 커버리지</h3>
        <p>백테스트에 새로 추가된 4개 파라미터가 각각 최소 2개 시나리오로 검증됩니다.
           각 기능은 "발동해야 하는 상황"과 "발동하면 안 되는 상황"을 짝으로 테스트합니다.</p>
        <div class="coverage-grid">{coverage_cards}</div>

        <h3>짝(Pair) 테스트 결과</h3>
        <p>경계값 양쪽을 모두 통과해야 해당 기능이 정확히 동작한다고 판단할 수 있습니다.
           한쪽만 PASS면 발동 조건이 너무 느슨하거나 엄격한 것입니다.</p>
        {pair_rows}

        <h3>독립 시나리오</h3>
        <p>짝 테스트 외에 개별적으로 중요한 동작을 확인하는 시나리오입니다.</p>
        <ul>{extra_scenarios}</ul>

        <h3>카테고리별 요약</h3>
        <ul>
            <li><strong>리스크 관리</strong> ({risk_pass}/{len(risk_results)}) — 손절/트레일링 스탑/보유기간 등 자본 보호 기능.
                {'모든 시나리오 정상.' if risk_pass == len(risk_results) else f'{len(risk_results) - risk_pass}개 실패 — 리스크 관리 로직 점검 필요.'}</li>
            <li><strong>시그널 품질</strong> ({signal_pass}/{len(signal_results)}) — 노이즈 필터링 및 불필요 매매 차단.
                {'모든 시나리오 정상.' if signal_pass == len(signal_results) else f'{len(signal_results) - signal_pass}개 실패 — 필터 로직 점검 필요.'}</li>
        </ul>

        {fail_detail}
    </div>
    """


def _build_scenario_card(idx: int, r: ScenarioResult) -> str:
    status = "PASS" if r.passed else "FAIL"
    icon = "\u2705" if r.passed else "\u274c"
    s = r.scenario

    # 데이터 소스 뱃지
    source_badge = ""
    source_detail = ""
    if s.data_source == "real":
        meta = get_fixture_meta(s.name)
        ticker = meta.get("ticker", "")
        start = meta.get("start", "")
        end = meta.get("end", "")
        period_str = f"{start[:4]}-{start[4:6]}-{start[6:8]} ~ {end[:4]}-{end[4:6]}-{end[6:8]}" if start and end else ""
        source_badge = '<span class="data-source-badge real">REAL DATA</span>'
        if ticker:
            source_detail = f'<div class="data-source-detail">{ticker} {period_str}</div>'
    elif s.data_source == "synthetic":
        source_badge = '<span class="data-source-badge synthetic">SYNTHETIC</span>'
        source_detail = '<div class="data-source-detail">합성 분봉 데이터 (grace_minutes 테스트용)</div>'

    # 시나리오 상세 설명 블록
    context_html = ""
    if s.market_context or s.test_point or s.expected_behavior:
        items = ""
        if s.market_context:
            items += f"<dt>시장 상황</dt><dd>{s.market_context}</dd>"
        if s.test_point:
            items += f"<dt>테스트 핵심</dt><dd>{s.test_point}</dd>"
        if s.expected_behavior:
            items += f"<dt>기대 동작</dt><dd>{s.expected_behavior}</dd>"
        context_html = f'<dl class="context-block">{items}</dl>'

    # 핵심 파라미터 태그
    params_html = ""
    if s.key_params:
        tags = "".join(
            f'<span class="param-tag">{k}: {v}</span>'
            for k, v in s.key_params.items()
        )
        params_html = f'<div class="param-tags">{tags}</div>'

    # 검증 결과
    checks_html = ""
    for name, ok, detail in r.checks:
        cls = "check-pass" if ok else "check-fail"
        mark = "\u2713" if ok else "\u2717"
        checks_html += f'<div class="check-item {cls}">{mark} {name}: {detail}</div>'

    # 매매 내역 테이블
    trades_html = ""
    if r.backtest_result.trades:
        rows = ""
        for i, t in enumerate(r.backtest_result.trades):
            reason_badge = ""
            if t.reason:
                badge_colors = {
                    "signal": "#2563eb",
                    "stop_loss": "#dc2626",
                    "trailing_stop": "#d97706",
                    "max_holding": "#7c3aed",
                    "force_close": "#6b7280",
                }
                bg = badge_colors.get(t.reason, "#6b7280")
                reason_badge = f'<span class="reason-badge" style="background:{bg}">{t.reason}</span>'
            side_cls = "buy-badge" if t.side == "buy" else "sell-badge"
            rows += f"""<tr>
                <td>{i}</td>
                <td><span class="{side_cls}">{t.side.upper()}</span></td>
                <td>{t.price:,.0f}</td>
                <td>{t.quantity}</td>
                <td>{t.date}</td>
                <td>{reason_badge}</td>
            </tr>"""
        trades_html = f"""
        <table class="trade-table">
            <thead><tr>
                <th>#</th><th>Side</th><th>Price</th><th>Qty</th><th>Date</th><th>Reason</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        """
    else:
        trades_html = '<div style="font-size:12px;color:#666;margin-top:8px">거래 없음 (시나리오 의도대로 매매 차단)</div>'

    # 메트릭
    bt = r.backtest_result
    metrics_html = f"""
    <div class="metrics-row">
        <div class="metric-item">수익률: <span class="{'positive' if bt.total_return_pct >= 0 else 'negative'}">{bt.total_return_pct:+.2f}%</span></div>
        <div class="metric-item">거래 수: <span>{bt.trade_count}</span></div>
        <div class="metric-item">승률: <span>{bt.win_rate:.1f}%</span></div>
        <div class="metric-item">MDD: <span class="negative">-{bt.max_drawdown_pct:.2f}%</span></div>
    </div>
    """

    return f"""
    <div class="scenario-card">
        <div class="scenario-header">
            <span class="scenario-status">{icon}</span>
            <div>
                <div class="scenario-name">{s.name} [{status}] {source_badge}</div>
                <div class="scenario-desc">{s.description}</div>
                {source_detail}
            </div>
        </div>
        {params_html}
        {context_html}
        <div class="check-list">{checks_html}</div>
        <div class="detail-divider">
            {metrics_html}
            <div class="chart-container"><canvas id="chart-{idx}"></canvas></div>
            {trades_html}
        </div>
    </div>
    """


def _build_chart_js(results: list[ScenarioResult]) -> str:
    """각 시나리오별 가격 + 볼린저밴드 + 매매 마커 Chart.js 코드 생성."""
    scripts: list[str] = []

    for idx, r in enumerate(results):
        chart = r.chart
        if not chart:
            continue

        closes = [float(c.close) for c in chart]
        period = r.scenario.backtest_params.get("period", 20)
        num_std = r.scenario.backtest_params.get("num_std", 2.0)
        bands = compute_bollinger_bands(closes, period, num_std)

        labels = [c.date.split(" ")[1] if " " in c.date else c.date for c in chart]
        uppers = [b[0] if b[0] is not None else "null" for b in bands]
        middles = [b[1] if b[1] is not None else "null" for b in bands]
        lowers = [b[2] if b[2] is not None else "null" for b in bands]

        # 매매 마커
        buy_points = []
        sell_points = []
        for t in r.backtest_result.trades:
            for ci, cd in enumerate(chart):
                if cd.date == t.date:
                    if t.side == "buy":
                        buy_points.append(f"{{x:{ci},y:{t.price}}}")
                    else:
                        sell_points.append(f"{{x:{ci},y:{t.price}}}")
                    break

        labels_js = str(labels).replace("'", '"')
        closes_js = str(closes)
        uppers_js = str(uppers).replace("'null'", "null").replace("'", "")
        middles_js = str(middles).replace("'null'", "null").replace("'", "")
        lowers_js = str(lowers).replace("'null'", "null").replace("'", "")

        scripts.append(f"""
(function() {{
    const ctx = document.getElementById('chart-{idx}');
    if (!ctx) return;
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: {labels_js},
            datasets: [
                {{
                    label: '가격',
                    data: {closes_js},
                    borderColor: '#60a5fa',
                    borderWidth: 1.5,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.1,
                }},
                {{
                    label: '상단밴드',
                    data: {uppers_js},
                    borderColor: 'rgba(239,68,68,0.4)',
                    borderWidth: 1,
                    borderDash: [4,2],
                    pointRadius: 0,
                    fill: false,
                }},
                {{
                    label: '중간밴드',
                    data: {middles_js},
                    borderColor: 'rgba(156,163,175,0.4)',
                    borderWidth: 1,
                    borderDash: [2,2],
                    pointRadius: 0,
                    fill: false,
                }},
                {{
                    label: '하단밴드',
                    data: {lowers_js},
                    borderColor: 'rgba(34,197,94,0.4)',
                    borderWidth: 1,
                    borderDash: [4,2],
                    pointRadius: 0,
                    fill: false,
                }},
                {{
                    label: 'BUY',
                    data: [{','.join(buy_points)}],
                    type: 'scatter',
                    pointRadius: 8,
                    pointStyle: 'triangle',
                    backgroundColor: '#10b981',
                    borderColor: '#10b981',
                }},
                {{
                    label: 'SELL',
                    data: [{','.join(sell_points)}],
                    type: 'scatter',
                    pointRadius: 8,
                    pointStyle: 'trianglePerimeter',
                    pointRotation: 180,
                    backgroundColor: '#ef4444',
                    borderColor: '#ef4444',
                }},
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ display: true, labels: {{ color: '#aaa', font: {{ size: 10 }} }} }},
            }},
            scales: {{
                x: {{
                    display: true,
                    ticks: {{ color: '#666', maxTicksLimit: 10, font: {{ size: 9 }} }},
                    grid: {{ color: '#1e2028' }},
                }},
                y: {{
                    display: true,
                    ticks: {{ color: '#666', font: {{ size: 10 }} }},
                    grid: {{ color: '#1e2028' }},
                }},
            }},
        }},
    }});
}})();
""")

    return "\n".join(scripts)


def generate_report(results: list[ScenarioResult] | None = None) -> str:
    """시나리오 리포트 HTML 생성."""
    if results is None:
        results = run_all_scenarios()

    today = date.today().isoformat()

    # 카테고리별 그룹핑
    categories: dict[str, list[tuple[int, ScenarioResult]]] = {}
    for idx, r in enumerate(results):
        cat = r.scenario.category
        categories.setdefault(cat, []).append((idx, r))

    category_labels = {
        "risk_management": "리스크 관리",
        "signal_quality": "시그널 품질",
    }
    category_descriptions = {
        "risk_management": (
            "손절(stop_loss), 트레일링 스탑(trailing_stop), 보유기간 초과(max_holding), "
            "유예 기간(grace_minutes) 등 리스크 관리 기능이 다양한 시장 상황에서 "
            "의도한 대로 발동/미발동하는지 검증합니다. "
            "각 시나리오는 짝(pair)으로 구성되어 경계값 양쪽을 모두 테스트합니다."
        ),
        "signal_quality": (
            "밴드 폭 필터(min_bandwidth), 최소 수익률 게이트(min_profit_pct) 등 "
            "시그널 품질 개선 기능이 노이즈 매매를 효과적으로 걸러내는지 검증합니다. "
            "좁은 밴드에서의 의미 없는 매수 차단, 수수료 이하 소액 익절 방지 등을 확인합니다."
        ),
    }

    summary = _build_summary_cards(results)
    analysis = _build_analysis(results)

    real_count = sum(1 for s in SCENARIOS if s.data_source == "real")
    synth_count = sum(1 for s in SCENARIOS if s.data_source == "synthetic")

    intro_html = f"""
    <div class="intro-section">
        <h2>리포트 개요</h2>
        <p>
            볼린저 밴드 전략에 추가된 리스크 관리 기능 4개
            (<code>trailing_stop_grace_minutes</code>, <code>min_profit_pct</code>,
            <code>stop_loss_pct</code>, <code>min_bandwidth</code>)가
            다양한 시장 상황에서 정상 동작하는지 자동 검증한 결과입니다.
        </p>
        <p>
            <strong>{real_count}개 시나리오</strong>는 <span class="data-source-badge real">REAL DATA</span>
            yfinance 실제 과거 일봉 데이터를 사용하고,
            <strong>{synth_count}개 시나리오</strong>는 <span class="data-source-badge synthetic">SYNTHETIC</span>
            합성 분봉 데이터를 사용합니다 (분봉 타임스탬프가 필수인 <code>trailing_stop_grace_minutes</code> 테스트용).
        </p>
        <p>
            각 시나리오는 <code>run_bollinger_backtest()</code>를 실행한 뒤, 매매 결과가 기대와 일치하는지 선언적으로 판정합니다.
            모든 기능은 "발동해야 하는 상황"과 "발동하면 안 되는 상황"을 짝으로 테스트하여 정확성을 이중 검증합니다.
        </p>
    </div>
    """

    # 카테고리별 카드 렌더
    sections_html = ""
    for cat, items in categories.items():
        label = category_labels.get(cat, cat)
        desc = category_descriptions.get(cat, "")
        count = len(items)
        passed = sum(1 for _, r in items if r.passed)
        cards = ""
        for idx, r in items:
            cards += _build_scenario_card(idx, r)

        desc_html = f'<div class="category-desc">{desc}</div>' if desc else ""

        sections_html += f"""
        <div class="category-section">
            <div class="category-title">{label} ({passed}/{count})</div>
            {desc_html}
            {cards}
        </div>
        """

    body = f"""
    <div class="container">
        <header>
            <h1>시나리오 백테스트 리포트</h1>
            <p>{today} &middot; {len(results)}개 시나리오 &middot; 볼린저 밴드 전략 기능 검증</p>
        </header>
        {intro_html}
        {summary}
        {analysis}
        {sections_html}
        <footer>Quantum Trading Platform &middot; Scenario Backtest Report</footer>
    </div>
    """

    chart_js = _build_chart_js(results)

    return wrap_html(
        title=f"시나리오 백테스트 리포트 — {today}",
        body=body,
        extra_css=EXTRA_CSS,
        extra_js=chart_js,
    )


if __name__ == "__main__":
    print("시나리오 실행 중...")
    results = run_all_scenarios()

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    for r in results:
        icon = "\u2705" if r.passed else "\u274c"
        print(f"  {icon} {r.scenario.name}: {r.scenario.description}")
        for name, ok, detail in r.checks:
            mark = "  \u2713" if ok else "  \u2717"
            print(f"    {mark} {name}: {detail}")

    print(f"\n결과: {passed}/{total} PASS")

    html = generate_report(results)
    out = Path("scenario_test_report.html")
    out.write_text(html, encoding="utf-8")
    print(f"리포트 생성: {out.resolve()}")
