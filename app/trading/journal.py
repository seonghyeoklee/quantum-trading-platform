"""일일 매매 저널 — JSONL 로깅 + HTML 리포트 생성"""

import json
import logging
from datetime import date, datetime
from pathlib import Path

from app.models import TradeEvent
from app.report_theme import wrap_html

logger = logging.getLogger(__name__)

def _project_root() -> Path:
    """프로젝트 루트 경로 (app/ 상위 디렉토리)"""
    return Path(__file__).resolve().parent.parent.parent


DEFAULT_LOG_DIR = _project_root() / "data" / "journal" / "logs"
DEFAULT_REPORT_DIR = _project_root() / "data" / "journal" / "reports"


class TradingJournal:
    def __init__(self, log_dir: str = ""):
        self._log_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        self._report_dir = (
            Path(log_dir).parent / "reports" if log_dir else DEFAULT_REPORT_DIR
        )
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._report_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, d: date) -> Path:
        return self._log_dir / f"{d.isoformat()}.jsonl"

    def _report_path(self, d: date) -> Path:
        return self._report_dir / f"{d.isoformat()}.html"

    def log_event(self, event: TradeEvent) -> None:
        """이벤트를 JSONL 파일에 1줄 append"""
        path = self._log_path(event.timestamp.date())
        with open(path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def read_events(self, d: date) -> list[TradeEvent]:
        """특정 날짜의 이벤트 목록 반환 (손상된 줄 skip)"""
        path = self._log_path(d)
        if not path.exists():
            return []
        events: list[TradeEvent] = []
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(TradeEvent.model_validate_json(line))
            except Exception:
                logger.warning("JSONL 파싱 실패 (line %d): %s", i, line[:100])
        return events

    def list_dates(self) -> list[str]:
        """기록이 있는 날짜 목록 (YYYY-MM-DD, 내림차순)"""
        if not self._log_dir.exists():
            return []
        dates = sorted(
            (p.stem for p in self._log_dir.glob("*.jsonl")),
            reverse=True,
        )
        return dates

    def generate_daily_report(self, d: date) -> str:
        """일일 리포트 HTML 생성 → 파일 경로 반환"""
        events = self.read_events(d)
        html = _build_report_html(d, events)
        path = self._report_path(d)
        path.write_text(html, encoding="utf-8")
        logger.info("일일 리포트 생성: %s", path)
        return str(path)

    def get_report_path(self, d: date) -> Path:
        return self._report_path(d)


# --- 저널 전용 추가 CSS ---

_JOURNAL_CSS = """
.container { max-width: 1200px; }
h1 { font-size: 1.5rem; margin-bottom: 8px; color: #f1f5f9; }
.subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 24px; }

.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }
.card { background: #1e293b; border-radius: 12px; padding: 20px; }
.card-label { color: #94a3b8; font-size: 0.8rem; margin-bottom: 4px; }
.card-value { font-size: 1.4rem; font-weight: 700; }

.chart-container { background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 32px; height: auto; }

table { font-size: 0.85rem; }
th { background: #1e293b; color: #94a3b8; text-align: left; }
td { border-bottom: 1px solid #1e293b; }
tr:hover { background: rgba(255,255,255,0.03); }

.section { margin-bottom: 32px; background: transparent; padding: 0; }
.section-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 12px; color: #f1f5f9; }

details { margin-bottom: 32px; }
summary { cursor: pointer; font-size: 1.1rem; font-weight: 600; color: #f1f5f9; margin-bottom: 12px; }
summary:hover { color: #3b82f6; }

body { padding: 20px; }
.reason-detail { color: #94a3b8; font-size: 0.8rem; max-width: 280px; }
"""


def _build_report_html(d: date, events: list[TradeEvent]) -> str:
    """다크 테마 일일 매매 저널 HTML 생성"""

    # 이벤트 분류
    signals = [e for e in events if e.event_type == "signal"]
    orders = [e for e in events if e.event_type in ("order", "force_close")]
    buys = [o for o in orders if o.side == "buy"]
    sells = [o for o in orders if o.side == "sell"]
    success_orders = [o for o in orders if o.success]

    # 엔진 가동 시간
    starts = [e for e in events if e.event_type == "engine_start"]
    stops = [e for e in events if e.event_type == "engine_stop"]
    engine_start_str = starts[0].timestamp.strftime("%H:%M:%S") if starts else "-"
    engine_stop_str = stops[-1].timestamp.strftime("%H:%M:%S") if stops else "-"

    # 실현 손익 계산 (매도 주문에서)
    total_pnl = 0.0
    pnl_details = []
    for sell in sells:
        if sell.entry_price > 0 and sell.current_price > 0:
            pnl = (sell.current_price - sell.entry_price) * sell.quantity
            total_pnl += pnl
            pnl_details.append({
                "symbol": sell.symbol,
                "entry": sell.entry_price,
                "exit": sell.current_price,
                "qty": sell.quantity,
                "pnl": pnl,
            })

    # 종목별 주문 그룹
    symbols_in_orders = sorted(set(o.symbol for o in orders if o.symbol))

    # 사유 뱃지 색상
    reason_colors = {
        "signal": "#3b82f6",
        "stop_loss": "#ef4444",
        "trailing_stop": "#f59e0b",
        "max_holding": "#8b5cf6",
        "force_close": "#6b7280",
    }

    # 주문 테이블 행
    order_rows = ""
    for o in orders:
        ts = o.timestamp.strftime("%H:%M:%S")
        side_class = "buy-badge" if o.side == "buy" else "sell-badge"
        side_label = "매수" if o.side == "buy" else "매도"
        reason_color = reason_colors.get(o.reason, "#6b7280")
        reason_badge = f'<span class="reason-badge" style="background:{reason_color}">{o.reason}</span>' if o.reason else ""
        status_icon = "&#10003;" if o.success else "&#10007;"
        status_class = "positive" if o.success else "negative"

        pnl_str = ""
        if o.side == "sell" and o.entry_price > 0 and o.current_price > 0:
            pnl = (o.current_price - o.entry_price) * o.quantity
            pnl_class = "positive" if pnl >= 0 else "negative"
            pnl_str = f'<span class="{pnl_class}">{pnl:+,.0f}</span>'

        detail_str = o.reason_detail or ""

        order_rows += f"""
        <tr>
            <td>{ts}</td>
            <td>{o.symbol}</td>
            <td><span class="{side_class}">{side_label}</span></td>
            <td>{o.quantity}</td>
            <td>{o.current_price:,.0f}</td>
            <td>{reason_badge}</td>
            <td class="reason-detail">{detail_str}</td>
            <td class="{status_class}">{status_icon}</td>
            <td>{pnl_str}</td>
        </tr>"""

    # 시그널 로그 행
    signal_rows = ""
    for s in signals:
        ts = s.timestamp.strftime("%H:%M:%S")
        sig_class = "buy-badge" if s.signal == "BUY" else "sell-badge" if s.signal == "SELL" else "hold-badge"
        rsi_str = f"{s.rsi:.1f}" if s.rsi is not None else "-"
        vol_str = "Y" if s.volume_confirmed else "N" if s.volume_confirmed is not None else "-"
        bb_str = ""
        if s.upper_band is not None:
            bb_str = f"{s.upper_band:.0f}/{s.middle_band:.0f}/{s.lower_band:.0f}"

        signal_rows += f"""
        <tr>
            <td>{ts}</td>
            <td>{s.symbol}</td>
            <td><span class="{sig_class}">{s.signal}</span></td>
            <td>{s.current_price:,.0f}</td>
            <td>{s.short_ma:.0f}</td>
            <td>{s.long_ma:.0f}</td>
            <td>{rsi_str}</td>
            <td>{vol_str}</td>
            <td>{bb_str}</td>
        </tr>"""

    # Chart.js 데이터 (종목별 가격 + BUY/SELL 마커)
    chart_datasets_js = "[]"
    if symbols_in_orders:
        datasets = []
        marker_colors = {"buy": "#10b981", "sell": "#ef4444"}
        for sym in symbols_in_orders:
            sym_orders = [o for o in orders if o.symbol == sym]
            points = []
            for o in sym_orders:
                points.append({
                    "x": o.timestamp.strftime("%H:%M"),
                    "y": o.current_price,
                    "side": o.side,
                })
            buy_points = [p for p in points if p["side"] == "buy"]
            sell_points = [p for p in points if p["side"] == "sell"]
            if buy_points:
                datasets.append({
                    "label": f"{sym} BUY",
                    "data": [{"x": p["x"], "y": p["y"]} for p in buy_points],
                    "backgroundColor": marker_colors["buy"],
                    "borderColor": marker_colors["buy"],
                    "pointRadius": 8,
                    "pointStyle": "triangle",
                    "showLine": False,
                })
            if sell_points:
                datasets.append({
                    "label": f"{sym} SELL",
                    "data": [{"x": p["x"], "y": p["y"]} for p in sell_points],
                    "backgroundColor": marker_colors["sell"],
                    "borderColor": marker_colors["sell"],
                    "pointRadius": 8,
                    "pointStyle": "trianglePerp",
                    "showLine": False,
                })
        chart_datasets_js = json.dumps(datasets, ensure_ascii=False)

    total_pnl_class = "positive" if total_pnl >= 0 else "negative"
    success_rate_str = f"{len(success_orders) / len(orders) * 100:.0f}%" if orders else "-"

    body = f"""<div class="container">
    <h1>매매 저널 &mdash; {d.isoformat()}</h1>
    <p class="subtitle">엔진 가동: {engine_start_str} ~ {engine_stop_str}</p>

    <div class="cards">
        <div class="card">
            <div class="card-label">시그널 수</div>
            <div class="card-value">{len(signals)}</div>
        </div>
        <div class="card">
            <div class="card-label">매수 건수</div>
            <div class="card-value">{len(buys)}</div>
        </div>
        <div class="card">
            <div class="card-label">매도 건수</div>
            <div class="card-value">{len(sells)}</div>
        </div>
        <div class="card">
            <div class="card-label">성공률</div>
            <div class="card-value">{success_rate_str}</div>
        </div>
        <div class="card">
            <div class="card-label">실현 손익</div>
            <div class="card-value {total_pnl_class}">{total_pnl:+,.0f}원</div>
        </div>
    </div>

    <div class="chart-container">
        <canvas id="orderChart" height="200"></canvas>
    </div>

    <div class="section">
        <div class="section-title">주문 이력</div>
        <table>
            <thead>
                <tr>
                    <th>시각</th><th>종목</th><th>구분</th><th>수량</th>
                    <th>가격</th><th>사유</th><th>상세</th><th>결과</th><th>손익</th>
                </tr>
            </thead>
            <tbody>{order_rows if order_rows else '<tr><td colspan="9" style="text-align:center;color:#64748b;">주문 없음</td></tr>'}</tbody>
        </table>
    </div>

    <details>
        <summary>시그널 로그 ({len(signals)}건)</summary>
        <table>
            <thead>
                <tr>
                    <th>시각</th><th>종목</th><th>시그널</th><th>현재가</th>
                    <th>단기MA</th><th>장기MA</th><th>RSI</th><th>거래량</th><th>BB</th>
                </tr>
            </thead>
            <tbody>{signal_rows if signal_rows else '<tr><td colspan="9" style="text-align:center;color:#64748b;">시그널 없음</td></tr>'}</tbody>
        </table>
    </details>
</div>"""

    chart_js = f"""const ctx = document.getElementById('orderChart').getContext('2d');
new Chart(ctx, {{
    type: 'scatter',
    data: {{ datasets: {chart_datasets_js} }},
    options: {{
        responsive: true,
        plugins: {{
            title: {{ display: true, text: '매매 타이밍', color: '#94a3b8' }},
            legend: {{ labels: {{ color: '#94a3b8' }} }},
        }},
        scales: {{
            x: {{ type: 'category', ticks: {{ color: '#64748b' }}, grid: {{ color: '#1e293b' }} }},
            y: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1e293b' }} }},
        }},
    }},
}});"""

    return wrap_html(
        title=f"매매 저널 — {d.isoformat()}",
        body=body,
        extra_css=_JOURNAL_CSS,
        extra_js=chart_js,
    )
