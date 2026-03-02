"""일일 매매 저널 — JSONL 로깅 + HTML 리포트 생성"""

import json
import logging
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from app.models import TradeEvent
from app.report_theme import CHART_JS_CDN

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


# ---- 종목 코드 → 이름 매핑 ----

STOCK_NAMES: dict[str, str] = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "035420": "NAVER",
    "005490": "POSCO홀딩스",
    "105560": "KB금융",
    "009540": "한국조선해양",
    "034020": "두산에너빌리티",
    "298040": "효성중공업",
    "064350": "현대로템",
    "010120": "LS일렉트릭",
}

REASON_LABELS: dict[str, str] = {
    "signal": "시그널",
    "stop_loss": "손절",
    "trailing_stop": "트레일링",
    "take_profit": "목표수익",
    "max_holding": "보유한도",
    "force_close": "장마감",
}

REASON_COLORS: dict[str, str] = {
    "signal": "#3b82f6",
    "stop_loss": "#ef4444",
    "trailing_stop": "#f59e0b",
    "take_profit": "#10b981",
    "max_holding": "#8b5cf6",
    "force_close": "#6b7280",
}

_WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


# ---- 매수-매도 매칭 ----


def _match_trades(events: list[TradeEvent]) -> list[dict]:
    """매수-매도 FIFO 매칭 + 크로스데이 지원 (entry_price fallback)"""
    buy_queue: dict[str, list[TradeEvent]] = defaultdict(list)
    trades: list[dict] = []

    orders = [
        e
        for e in events
        if e.event_type in ("order", "force_close") and e.success
    ]

    for o in orders:
        if o.side == "buy":
            buy_queue[o.symbol].append(o)
        elif o.side == "sell":
            if buy_queue[o.symbol]:
                buy = buy_queue[o.symbol].pop(0)
                pnl = (o.current_price - buy.current_price) * o.quantity
                pnl_rate = (
                    (o.current_price - buy.current_price) / buy.current_price * 100
                    if buy.current_price > 0
                    else 0
                )
                trades.append(
                    {
                        "symbol": o.symbol,
                        "name": STOCK_NAMES.get(o.symbol, o.symbol),
                        "buy_time": buy.timestamp.strftime("%H:%M"),
                        "sell_time": o.timestamp.strftime("%H:%M"),
                        "buy_price": buy.current_price,
                        "sell_price": o.current_price,
                        "quantity": o.quantity,
                        "amount": buy.current_price * o.quantity,
                        "pnl": pnl,
                        "pnl_rate": pnl_rate,
                        "reason": o.reason or "signal",
                        "reason_detail": o.reason_detail or "",
                        "hold_min": int(
                            (o.timestamp - buy.timestamp).total_seconds() / 60
                        ),
                    }
                )
            elif o.entry_price > 0:
                # 크로스데이: 이전 날 매수, 오늘 매도
                pnl = (o.current_price - o.entry_price) * o.quantity
                pnl_rate = (
                    (o.current_price - o.entry_price) / o.entry_price * 100
                    if o.entry_price > 0
                    else 0
                )
                trades.append(
                    {
                        "symbol": o.symbol,
                        "name": STOCK_NAMES.get(o.symbol, o.symbol),
                        "buy_time": "전일",
                        "sell_time": o.timestamp.strftime("%H:%M"),
                        "buy_price": o.entry_price,
                        "sell_price": o.current_price,
                        "quantity": o.quantity,
                        "amount": o.entry_price * o.quantity,
                        "pnl": pnl,
                        "pnl_rate": pnl_rate,
                        "reason": o.reason or "signal",
                        "reason_detail": o.reason_detail or "",
                        "hold_min": 0,
                    }
                )

    return trades


# ---- 모바일 카드 UI CSS ----

_MOBILE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{
  font-family:-apple-system,'Pretendard',sans-serif;
  background:#0f1117;color:#e2e8f0;
  -webkit-font-smoothing:antialiased;
  -webkit-text-size-adjust:100%;
}
.wrap{max-width:480px;margin:0 auto;padding:16px 16px 32px}

/* 색상 유틸 */
.pos{color:#22c55e} .neg{color:#ef4444}

/* 헤더 */
.hdr{text-align:center;padding:12px 0 16px}
.hdr-date{font-size:1.4rem;font-weight:800;color:#fff}
.hdr-sub{color:#64748b;font-size:0.78rem;margin-top:4px}

/* 히어로 */
.hero{background:#1e293b;border-radius:16px;padding:20px;margin-bottom:12px;text-align:center}
.hero-top{margin-bottom:4px}
.hero-label{color:#64748b;font-size:0.75rem}
.hero-pnl{font-size:2.6rem;font-weight:800;letter-spacing:-1px;line-height:1.1}
.hero-unit{font-size:1rem;font-weight:400;margin-left:2px}
.hero-row{display:flex;justify-content:center;gap:0;margin-top:14px}
.hero-item{flex:1;display:flex;flex-direction:column;align-items:center}
.hero-divider{width:1px;background:#334155;margin:0 4px}
.hi-label{color:#64748b;font-size:0.68rem;margin-bottom:2px}
.hi-val{font-size:0.92rem;font-weight:600}

/* 승률 + 도넛 */
.stat-row{display:flex;gap:16px;align-items:center;background:#1e293b;border-radius:16px;padding:16px;margin-bottom:12px}
.stat-box{flex-shrink:0}
.stat-nums{flex:1}
.sn-main{font-size:1.8rem;font-weight:800;line-height:1}
.sn-label{font-size:0.75rem;color:#64748b;font-weight:400;margin-left:4px}
.sn-grid{display:flex;gap:12px;margin-top:6px}
.sn-item{font-size:0.78rem;color:#94a3b8;display:flex;align-items:center;gap:4px}
.sn-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.sn-detail{display:flex;flex-direction:column;font-size:0.78rem}

/* 지표 스트립 */
.metric-strip{display:flex;gap:8px;margin-bottom:12px}
.ms-card{flex:1;background:#1e293b;border-radius:12px;padding:12px;display:flex;flex-direction:column}
.ms-label{color:#64748b;font-size:0.68rem;margin-bottom:4px}
.ms-val{font-size:1.1rem;font-weight:700}
.ms-sub{color:#64748b;font-size:0.65rem;margin-top:2px}

/* 사유 pill */
.pill-row{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.pill{display:flex;align-items:center;gap:6px;background:#1e293b;border-radius:20px;padding:6px 12px}
.pill-count{font-size:0.78rem;font-weight:600}
.pill-pnl{font-size:0.78rem;font-weight:600}
.reason-badge{color:#fff;padding:2px 7px;border-radius:4px;font-size:0.65rem;font-weight:600;white-space:nowrap}

/* 차트 */
.chart-section{background:#1e293b;border-radius:12px;padding:16px;margin-bottom:12px}
.chart-wrap{height:180px;position:relative}
.sec-title{font-size:0.92rem;font-weight:600;color:#f1f5f9;margin-bottom:10px}

/* 종목 성과 리스트 */
.sym-list{margin-bottom:12px}
.sym-row{display:flex;align-items:center;padding:10px 12px;background:#1e293b;border-radius:10px;margin-bottom:6px}
.sym-name{flex:1;font-weight:600;font-size:0.85rem}
.sym-meta{color:#64748b;font-size:0.75rem;width:36px;text-align:center}
.sym-pnl{font-weight:700;font-size:0.88rem;width:80px;text-align:right}
.sym-rate{font-size:0.75rem;width:52px;text-align:right}
.tc-code{color:#64748b;font-size:0.68rem;font-weight:400;margin-left:6px}

/* 매매 카드 */
.trade-list{display:flex;flex-direction:column;gap:8px}
.trade-card{background:#1e293b;border-radius:12px;padding:14px 14px 10px;position:relative}
.tc-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.tc-name{font-weight:700;font-size:0.88rem}
.tc-pnl{font-size:1rem;font-weight:800}
.tc-bar-track{height:4px;background:#0f1117;border-radius:2px;margin-bottom:10px;overflow:hidden}
.tc-bar{height:100%;border-radius:2px;transition:width .3s}
.tc-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px 10px}
.tc-cell{display:flex;flex-direction:column}
.tc-label{color:#475569;font-size:0.62rem;text-transform:uppercase;letter-spacing:0.5px}
.tc-val{font-size:0.78rem;font-weight:500}

/* 감시 종목 태그 */
.tag-row{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.sym-tag{background:#252830;color:#94a3b8;padding:4px 10px;border-radius:6px;font-size:0.75rem}

/* 접기 상세 */
details{margin-top:16px}
summary{cursor:pointer;font-size:0.88rem;font-weight:600;color:#94a3b8;padding:10px 0}
summary:hover{color:#f1f5f9}
.log-table{width:100%;border-collapse:collapse;font-size:0.72rem;margin-top:8px}
.log-table th{background:#1e293b;color:#64748b;font-weight:600;padding:6px 8px;text-align:left}
.log-table td{padding:5px 8px;border-bottom:1px solid #1e293b;color:#94a3b8}
.buy-badge{background:#065f46;color:#10b981;padding:2px 6px;border-radius:4px;font-size:0.68rem;font-weight:600}
.sell-badge{background:#7f1d1d;color:#ef4444;padding:2px 6px;border-radius:4px;font-size:0.68rem;font-weight:600}
.hold-badge{background:#374151;color:#9ca3af;padding:2px 6px;border-radius:4px;font-size:0.68rem;font-weight:600}
.reason-detail{color:#64748b;font-size:0.72rem;max-width:200px}
.empty-msg{text-align:center;padding:40px 16px;color:#64748b;font-size:0.85rem}
.footer{text-align:center;padding:24px 0 8px;color:#334155;font-size:0.7rem}
"""


def _wrap_mobile(title: str, body: str, extra_js: str = "") -> str:
    """모바일 최적화 HTML 쉘"""
    js_block = f"<script>\n{extra_js}\n</script>" if extra_js else ""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>{title}</title>
<script src="{CHART_JS_CDN}"></script>
<style>{_MOBILE_CSS}</style>
</head>
<body>
{body}
{js_block}
</body>
</html>"""


def _build_signal_log(signals: list[TradeEvent]) -> str:
    """시그널 로그 <details> 섹션 (접기)"""
    signal_rows = ""
    for s in signals:
        ts = s.timestamp.strftime("%H:%M:%S")
        sig_class = (
            "buy-badge"
            if s.signal == "BUY"
            else "sell-badge" if s.signal == "SELL" else "hold-badge"
        )
        reason_str = s.signal_reason or ""
        reason_style = ' style="color:#64748b"' if s.signal in ("HOLD", "") else ""
        bb_str = ""
        if s.upper_band is not None:
            bb_str = f"{s.upper_band:.0f}/{s.middle_band:.0f}/{s.lower_band:.0f}"

        signal_rows += f"""
            <tr>
                <td>{ts}</td><td>{s.symbol}</td>
                <td><span class="{sig_class}">{s.signal}</span></td>
                <td class="reason-detail"{reason_style}>{reason_str}</td>
                <td>{s.current_price:,.0f}</td>
                <td>{bb_str}</td>
            </tr>"""

    empty = '<tr><td colspan="6" style="text-align:center;color:#475569">시그널 없음</td></tr>'
    return f"""
    <details>
        <summary>시그널 로그 ({len(signals)}건)</summary>
        <table class="log-table">
            <thead><tr>
                <th>시각</th><th>종목</th><th>시그널</th><th>판단 근거</th><th>현재가</th><th>BB</th>
            </tr></thead>
            <tbody>{signal_rows or empty}</tbody>
        </table>
    </details>"""


def _build_order_log(orders: list[TradeEvent]) -> str:
    """주문 이력 <details> 섹션 (접기)"""
    order_rows = ""
    for o in orders:
        ts = o.timestamp.strftime("%H:%M:%S")
        side_label = "매수" if o.side == "buy" else "매도"
        side_class = "buy-badge" if o.side == "buy" else "sell-badge"
        reason_color = REASON_COLORS.get(o.reason, "#6b7280")
        reason_badge = (
            f'<span class="reason-badge" style="background:{reason_color}">'
            f"{REASON_LABELS.get(o.reason, o.reason)}</span>"
            if o.reason
            else ""
        )
        detail_str = o.reason_detail or ""
        pnl_str = ""
        if o.side == "sell" and o.entry_price > 0 and o.current_price > 0:
            pnl = (o.current_price - o.entry_price) * o.quantity
            pc = "pos" if pnl >= 0 else "neg"
            pnl_str = f'<span class="{pc}">{pnl:+,.0f}</span>'

        order_rows += f"""
            <tr>
                <td>{ts}</td><td>{o.symbol}</td>
                <td><span class="{side_class}">{side_label}</span></td>
                <td>{o.quantity}</td><td>{o.current_price:,.0f}</td>
                <td>{reason_badge}</td><td class="reason-detail">{detail_str}</td>
                <td>{pnl_str}</td>
            </tr>"""

    empty = '<tr><td colspan="8" style="text-align:center;color:#475569">주문 없음</td></tr>'
    return f"""
    <details>
        <summary>주문 이력 ({len(orders)}건)</summary>
        <table class="log-table">
            <thead><tr>
                <th>시각</th><th>종목</th><th>구분</th><th>수량</th><th>가격</th><th>사유</th><th>상세</th><th>손익</th>
            </tr></thead>
            <tbody>{order_rows or empty}</tbody>
        </table>
    </details>"""


def _extract_engine_info(
    events: list[TradeEvent],
) -> tuple[str, str, str, list[str]]:
    """엔진 시작/종료 시각, 전략명, 감시 종목 추출"""
    starts = [e for e in events if e.event_type == "engine_start"]
    stops = [e for e in events if e.event_type == "engine_stop"]
    start_str = starts[0].timestamp.strftime("%H:%M") if starts else "-"
    stop_str = stops[-1].timestamp.strftime("%H:%M") if stops else "-"

    strat_events = [e for e in events if e.event_type == "strategy_change"]
    strategy_name = "볼린저 밴드"
    if strat_events:
        detail = strat_events[-1].detail or ""
        if "sma" in detail.lower():
            strategy_name = "SMA 크로스오버"

    watch_symbols: list[str] = []
    if starts:
        detail = starts[0].detail or ""
        if "symbols=" in detail:
            import ast

            try:
                syms = ast.literal_eval(detail.split("symbols=")[1])
                watch_symbols = syms
            except Exception:
                pass

    return start_str, stop_str, strategy_name, watch_symbols


def _build_report_html(d: date, events: list[TradeEvent]) -> str:
    """모바일 카드 UI 통합 리포트 (성과 분석 + 시그널/주문 접기)"""

    # ---- 이벤트 분류 ----
    signals = [e for e in events if e.event_type == "signal"]
    orders = [e for e in events if e.event_type in ("order", "force_close")]

    # ---- 매수-매도 매칭 ----
    trades = _match_trades(events)

    # ---- 엔진 정보 ----
    start_str, stop_str, strategy_name, watch_symbols = _extract_engine_info(events)

    # ---- 접기 섹션 (항상 렌더) ----
    signal_log_html = _build_signal_log(signals)
    order_log_html = _build_order_log(orders)

    # ---- 매매 없는 경우 ----
    if not trades:
        body = f"""<div class="wrap">
  <div class="hdr">
    <div class="hdr-date">{d.strftime('%Y.%m.%d')} ({_WEEKDAY_KO[d.weekday()]})</div>
    <div class="hdr-sub">{strategy_name} · {start_str}~{stop_str}</div>
  </div>
  <div class="empty-msg">매매 기록이 없습니다</div>
  {order_log_html}
  {signal_log_html}
  <div class="footer">Quantum Trading Platform · 매매 저널</div>
</div>"""
        return _wrap_mobile(f"매매 저널 — {d.isoformat()}", body)

    # ---- 종합 지표 ----
    total_pnl = sum(t["pnl"] for t in trades)
    total_amount = sum(t["amount"] for t in trades)
    total_return = total_pnl / total_amount * 100 if total_amount else 0
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] < 0]
    evens = [t for t in trades if t["pnl"] == 0]
    win_rate = (
        len(wins) / (len(wins) + len(losses)) * 100 if (wins or losses) else 0
    )
    avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["pnl"] for t in losses) / len(losses) if losses else 0
    best = max(trades, key=lambda t: t["pnl"])
    worst = min(trades, key=lambda t: t["pnl"])
    avg_hold = sum(t["hold_min"] for t in trades) / len(trades)

    total_pnl_class = "pos" if total_pnl >= 0 else "neg"
    total_pnl_sign = "+" if total_pnl >= 0 else ""

    # ---- 사유별 분류 ----
    reason_stats: dict[str, dict] = {}
    for t in trades:
        r = t["reason"]
        if r not in reason_stats:
            reason_stats[r] = {"count": 0, "pnl": 0}
        reason_stats[r]["count"] += 1
        reason_stats[r]["pnl"] += t["pnl"]

    # ---- 종목별 분류 ----
    symbol_stats: dict[str, dict] = {}
    for t in trades:
        s = t["symbol"]
        if s not in symbol_stats:
            symbol_stats[s] = {"name": t["name"], "count": 0, "pnl": 0, "amount": 0}
        symbol_stats[s]["count"] += 1
        symbol_stats[s]["pnl"] += t["pnl"]
        symbol_stats[s]["amount"] += t["amount"]

    # ---- 매매 카드 ----
    trade_cards = ""
    for t in trades:
        pc = "pos" if t["pnl"] >= 0 else "neg"
        rc = REASON_COLORS.get(t["reason"], "#6b7280")
        rl = REASON_LABELS.get(t["reason"], t["reason"])
        bar_pct = min(abs(t["pnl"]) / (abs(best["pnl"]) or 1) * 100, 100)
        bar_c = "#22c55e" if t["pnl"] >= 0 else "#ef4444"

        trade_cards += f"""
      <div class="trade-card">
        <div class="tc-head">
          <div class="tc-name">{t['name']}<span class="tc-code">{t['symbol']}</span></div>
          <span class="tc-pnl {pc}">{t['pnl']:+,.0f}원</span>
        </div>
        <div class="tc-bar-track"><div class="tc-bar" style="width:{bar_pct:.0f}%;background:{bar_c}"></div></div>
        <div class="tc-grid">
          <div class="tc-cell"><span class="tc-label">매수</span><span class="tc-val">{t['buy_time']} · {t['buy_price']:,.0f}</span></div>
          <div class="tc-cell"><span class="tc-label">매도</span><span class="tc-val">{t['sell_time']} · {t['sell_price']:,.0f}</span></div>
          <div class="tc-cell"><span class="tc-label">수량</span><span class="tc-val">{t['quantity']}주</span></div>
          <div class="tc-cell"><span class="tc-label">수익률</span><span class="tc-val {pc}">{t['pnl_rate']:+.2f}%</span></div>
          <div class="tc-cell"><span class="tc-label">보유</span><span class="tc-val">{t['hold_min']}분</span></div>
          <div class="tc-cell"><span class="tc-label">사유</span><span class="reason-badge" style="background:{rc}">{rl}</span></div>
        </div>
      </div>"""

    # ---- 종목별 성과 카드 ----
    sym_cards = ""
    for sym, st in sorted(
        symbol_stats.items(), key=lambda x: x[1]["pnl"], reverse=True
    ):
        pc = "pos" if st["pnl"] >= 0 else "neg"
        ret = st["pnl"] / st["amount"] * 100 if st["amount"] else 0
        sym_cards += f"""
      <div class="sym-row">
        <div class="sym-name">{st['name']}<span class="tc-code">{sym}</span></div>
        <div class="sym-meta">{st['count']}건</div>
        <div class="sym-pnl {pc}">{st['pnl']:+,.0f}</div>
        <div class="sym-rate {pc}">{ret:+.2f}%</div>
      </div>"""

    # ---- 감시 종목 태그 ----
    watch_section = ""
    if watch_symbols:
        watch_tags = "".join(
            f'<span class="sym-tag">{STOCK_NAMES.get(s, s)}</span>'
            for s in watch_symbols
        )
        watch_section = f"""
  <div class="sec-title" style="margin-top:20px">감시 종목</div>
  <div class="tag-row">{watch_tags}</div>"""

    # ---- 사유별 pill ----
    reason_pills = ""
    for r, st in sorted(
        reason_stats.items(), key=lambda x: x[1]["count"], reverse=True
    ):
        pc = "pos" if st["pnl"] >= 0 else "neg"
        reason_pills += f"""
      <div class="pill">
        <span class="reason-badge" style="background:{REASON_COLORS.get(r, '#6b7280')}">{REASON_LABELS.get(r, r)}</span>
        <span class="pill-count">{st['count']}건</span>
        <span class="pill-pnl {pc}">{st['pnl']:+,.0f}</span>
      </div>"""

    # ---- Chart.js 데이터 ----
    donut_data_js = json.dumps([len(wins), len(losses), len(evens)])

    cum_pnl: list[dict] = []
    running = 0.0
    for t in trades:
        running += t["pnl"]
        cum_pnl.append({"time": t["sell_time"], "pnl": running})
    cum_labels_js = json.dumps([p["time"] for p in cum_pnl])
    cum_data_js = json.dumps([p["pnl"] for p in cum_pnl])

    sorted_syms = sorted(
        symbol_stats, key=lambda x: symbol_stats[x]["pnl"], reverse=True
    )
    sym_names_js = json.dumps([symbol_stats[s]["name"] for s in sorted_syms])
    sym_pnl_js = json.dumps([symbol_stats[s]["pnl"] for s in sorted_syms])
    sym_colors_js = json.dumps(
        [
            "#22c55e" if symbol_stats[s]["pnl"] >= 0 else "#ef4444"
            for s in sorted_syms
        ]
    )

    # ---- 본문 HTML ----
    body = f"""<div class="wrap">
  <!-- 헤더 -->
  <div class="hdr">
    <div class="hdr-date">{d.strftime('%Y.%m.%d')} ({_WEEKDAY_KO[d.weekday()]})</div>
    <div class="hdr-sub">{strategy_name} · {start_str}~{stop_str} · {len(watch_symbols)}종목</div>
  </div>

  <!-- 총 손익 히어로 -->
  <div class="hero">
    <div class="hero-top"><span class="hero-label">오늘의 실현손익</span></div>
    <div class="hero-pnl {total_pnl_class}">{total_pnl_sign}{total_pnl:,.0f}<span class="hero-unit">원</span></div>
    <div class="hero-row">
      <div class="hero-item"><span class="hi-label">수익률</span><span class="hi-val {total_pnl_class}">{total_return:+.2f}%</span></div>
      <div class="hero-divider"></div>
      <div class="hero-item"><span class="hi-label">투자금액</span><span class="hi-val">{total_amount / 10000:,.0f}만원</span></div>
      <div class="hero-divider"></div>
      <div class="hero-item"><span class="hi-label">매매</span><span class="hi-val">{len(trades)}건</span></div>
    </div>
  </div>

  <!-- 승률 + 도넛 -->
  <div class="stat-row">
    <div class="stat-box"><canvas id="donutChart" width="100" height="100"></canvas></div>
    <div class="stat-nums">
      <div class="sn-main" style="color:#3b82f6">{win_rate:.0f}%<span class="sn-label">승률</span></div>
      <div class="sn-grid">
        <div class="sn-item"><span class="sn-dot" style="background:#22c55e"></span>승 {len(wins)}</div>
        <div class="sn-item"><span class="sn-dot" style="background:#ef4444"></span>패 {len(losses)}</div>
        <div class="sn-item"><span class="sn-dot" style="background:#475569"></span>무 {len(evens)}</div>
      </div>
      <div class="sn-grid" style="margin-top:8px">
        <div class="sn-detail"><span class="hi-label">평균 수익</span><span class="pos">{avg_win:+,.0f}</span></div>
        <div class="sn-detail"><span class="hi-label">평균 손실</span><span class="neg">{avg_loss:+,.0f}</span></div>
      </div>
    </div>
  </div>

  <!-- 핵심 지표 -->
  <div class="metric-strip">
    <div class="ms-card">
      <span class="ms-label">최대 수익</span>
      <span class="ms-val pos">{best['pnl']:+,.0f}</span>
      <span class="ms-sub">{best['name']} {best['pnl_rate']:+.1f}%</span>
    </div>
    <div class="ms-card">
      <span class="ms-label">최대 손실</span>
      <span class="ms-val neg">{worst['pnl']:+,.0f}</span>
      <span class="ms-sub">{worst['name']} {worst['pnl_rate']:+.1f}%</span>
    </div>
    <div class="ms-card">
      <span class="ms-label">평균 보유</span>
      <span class="ms-val">{avg_hold:.0f}분</span>
    </div>
  </div>

  <!-- 사유별 -->
  <div class="pill-row">{reason_pills}</div>

  <!-- 누적 손익 차트 -->
  <div class="chart-section">
    <div class="sec-title">누적 손익 추이</div>
    <div class="chart-wrap"><canvas id="cumChart"></canvas></div>
  </div>

  <!-- 종목별 손익 차트 -->
  <div class="chart-section">
    <div class="sec-title">종목별 손익</div>
    <div class="chart-wrap"><canvas id="symChart"></canvas></div>
  </div>

  <!-- 종목별 성과 -->
  <div class="sec-title">종목별 성과</div>
  <div class="sym-list">{sym_cards}</div>

  <!-- 매매 내역 -->
  <div class="sec-title" style="margin-top:20px">매매 내역 <span style="color:#64748b;font-weight:400">{len(trades)}건</span></div>
  <div class="trade-list">{trade_cards}</div>

  {watch_section}
  {order_log_html}
  {signal_log_html}

  <div class="footer">Quantum Trading Platform · 매매 저널</div>
</div>"""

    # ---- Chart.js ----
    chart_js = f"""
// 승/패 도넛
const donutCtx = document.getElementById('donutChart').getContext('2d');
new Chart(donutCtx, {{
  type: 'doughnut',
  data: {{
    labels: ['승', '패', '무'],
    datasets: [{{ data: {donut_data_js}, backgroundColor: ['#22c55e','#ef4444','#475569'], borderWidth: 0 }}],
  }},
  options: {{
    cutout: '65%',
    responsive: false,
    plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: true }} }},
  }},
}});

// 누적 손익
const cumCtx = document.getElementById('cumChart').getContext('2d');
const cumData = {cum_data_js};
new Chart(cumCtx, {{
  type: 'line',
  data: {{
    labels: {cum_labels_js},
    datasets: [{{
      data: cumData,
      borderColor: cumData[cumData.length-1] >= 0 ? '#22c55e' : '#ef4444',
      backgroundColor: cumData[cumData.length-1] >= 0 ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
      fill: true, tension: 0.35, pointRadius: 4, borderWidth: 2,
      pointBackgroundColor: cumData.map(v => v >= 0 ? '#22c55e' : '#ef4444'),
    }}],
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#64748b', font: {{ size: 10 }} }}, grid: {{ color: '#1e293b' }} }},
      y: {{ ticks: {{ color: '#64748b', font: {{ size: 10 }}, callback: v => (v/1000).toFixed(0)+'K' }}, grid: {{ color: '#1e293b' }} }},
    }},
  }},
}});

// 종목별 바
const symCtx = document.getElementById('symChart').getContext('2d');
new Chart(symCtx, {{
  type: 'bar',
  data: {{
    labels: {sym_names_js},
    datasets: [{{ data: {sym_pnl_js}, backgroundColor: {sym_colors_js}, borderRadius: 4 }}],
  }},
  options: {{
    responsive: true, maintainAspectRatio: false, indexAxis: 'y',
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ ticks: {{ color: '#64748b', font: {{ size: 10 }}, callback: v => (v/1000).toFixed(0)+'K' }}, grid: {{ color: '#1e293b' }} }},
      y: {{ ticks: {{ color: '#e0e0e0', font: {{ size: 11 }} }}, grid: {{ display: false }} }},
    }},
  }},
}});"""

    return _wrap_mobile(f"매매 저널 — {d.isoformat()}", body, chart_js)
