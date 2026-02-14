"""시장 국면 기반 전략 선택 리포트 — 통합 분석

yfinance로 코스피 + 종목 데이터를 가져와:
1. 현재 국면 판별 + 시장 분석
2. 국면별 백테스트 (4개 전략)
3. 국면-전략 히트맵 매트릭스
4. 전략 추천
→ 단일 HTML 리포트로 생성

사용법:
    uv run python scripts/generate_regime_report.py
"""

import json
import sys
from datetime import datetime, timedelta

# 프로젝트 루트를 path에 추가
sys.path.insert(0, ".")

from app.models import ChartData
from app.trading.backtest import (
    RegimeBacktestResult,
    run_regime_segmented_backtest,
)
from app.trading.regime import (
    REGIME_KR,
    MarketRegime,
    detect_current_regime,
    segment_by_regime,
)
from app.trading.strategy import compute_rsi, compute_sma


def fetch_index_data(ticker: str, start: str, end: str) -> dict:
    """yfinance로 지수 데이터 조회."""
    import yfinance as yf

    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        return {"dates": [], "values": []}
    if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
        df = df.droplevel(level=1, axis=1)
    dates = [d.strftime("%Y-%m-%d") for d in df.index]
    values = [round(float(v), 2) for v in df["Close"]]
    return {"dates": dates, "values": values}


def fetch_chart(ticker: str, start: str, end: str) -> list[ChartData]:
    """yfinance → list[ChartData]."""
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


# --- 종목 목록 ---
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

STRATEGY_COLORS = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444"]
STRATEGY_LABELS = ["SMA 기본", "SMA+리스크", "SMA+Adv+리스크", "볼린저"]

REGIME_COLORS = {
    "strong_bull": ("#22c55e", "rgba(34,197,94,0.15)"),
    "bull": ("#4ade80", "rgba(74,222,128,0.15)"),
    "sideways": ("#facc15", "rgba(250,204,21,0.15)"),
    "bear": ("#f87171", "rgba(248,113,113,0.15)"),
    "strong_bear": ("#ef4444", "rgba(239,68,68,0.15)"),
}

REGIME_EMOJI = {
    "strong_bull": "&#x1F680;",
    "bull": "&#x2197;&#xFE0F;",
    "sideways": "&#x2194;&#xFE0F;",
    "bear": "&#x2198;&#xFE0F;",
    "strong_bear": "&#x1F4C9;",
}


def collect_data() -> dict:
    """모든 데이터 수집."""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")  # 2년
    start_ymd = start_date.replace("-", "")
    end_ymd = end_date.replace("-", "")

    print("코스피 데이터 조회...")
    kospi = fetch_index_data("^KS11", start_date, end_date)
    closes = kospi["values"]
    dates = kospi["dates"]

    # 현재 국면
    regime_info = detect_current_regime([float(v) for v in closes])

    # SMA 시리즈 (차트용)
    sma20 = compute_sma(closes, 20)
    sma60 = compute_sma(closes, 60)
    sma120 = compute_sma(closes, 120)
    rsi14 = compute_rsi(closes, 14)

    # 국면 구간
    periods = segment_by_regime([float(v) for v in closes], dates)

    # 수익률 계산
    def pct_change(vals, days):
        if len(vals) < days + 1:
            return None
        return round((vals[-1] - vals[-(days + 1)]) / vals[-(days + 1)] * 100, 2)

    perf = {
        "1w": pct_change(closes, 5),
        "1m": pct_change(closes, 21),
        "3m": pct_change(closes, 63),
        "6m": pct_change(closes, 126),
        "1y": pct_change(closes, 252),
    }

    # 글로벌 지수
    print("글로벌 지수 조회...")
    indices = {}
    index_tickers = {
        "^KS11": "코스피",
        "^KQ11": "코스닥",
        "^GSPC": "S&P 500",
        "^IXIC": "나스닥",
        "^VIX": "VIX",
        "USDKRW=X": "USD/KRW",
    }
    for ticker, name in index_tickers.items():
        try:
            data = fetch_index_data(ticker, start_date, end_date)
            data["name"] = name
            indices[ticker] = data
        except Exception:
            pass

    # 종목별 국면 백테스트
    print("종목별 국면 백테스트 실행...")
    stock_results = []
    for symbol, name in SYMBOLS.items():
        ticker = f"{symbol}.KS"
        print(f"  {name} ({symbol})...")
        try:
            chart = fetch_chart(ticker, start_date, end_date)
            if len(chart) < 120:
                print(f"    데이터 부족 ({len(chart)}개) - 스킵")
                continue

            regime_results = run_regime_segmented_backtest(
                chart,
                initial_capital=10_000_000,
                order_amount=1_000_000,
                short_period=10,
                long_period=40,
            )

            # 거래량 분석
            volumes = [c.volume for c in chart]
            closes_list = [c.close for c in chart]
            vol_today = volumes[-1]
            vol_20avg = sum(volumes[-21:-1]) / 20 if len(volumes) >= 21 else 1
            vol_ratio = vol_today / vol_20avg if vol_20avg > 0 else 0
            price_chg_5d = (
                (closes_list[-1] - closes_list[-6]) / closes_list[-6] * 100
                if len(closes_list) > 6
                else 0
            )

            if price_chg_5d > 2 and vol_ratio > 1.5:
                vol_verdict = "상승+거래량확인"
            elif price_chg_5d > 2 and vol_ratio < 0.8:
                vol_verdict = "거래량부족"
            elif price_chg_5d < -2 and vol_ratio > 1.5:
                vol_verdict = "투매주의"
            elif price_chg_5d < -2 and vol_ratio < 0.8:
                vol_verdict = "소폭조정"
            elif vol_ratio > 2.0:
                vol_verdict = "거래급증"
            else:
                vol_verdict = "보통"

            # 현재 국면 + RSI + 모멘텀
            regime_stock = detect_current_regime([float(v) for v in closes_list])
            rsi_stock = regime_stock.rsi14 if regime_stock else 50.0
            regime_val = regime_stock.regime.value if regime_stock else "sideways"
            regime_kr_stock = REGIME_KR.get(regime_stock.regime, "판별불가") if regime_stock else "판별불가"
            mom_20d = (
                (closes_list[-1] - closes_list[-21]) / closes_list[-21] * 100
                if len(closes_list) > 21
                else 0
            )

            stock_results.append({
                "symbol": symbol,
                "name": name,
                "regime_results": regime_results,
                "first_price": chart[0].close,
                "last_price": chart[-1].close,
                "vol_ratio": round(vol_ratio, 1),
                "vol_verdict": vol_verdict,
                "price_chg_5d": round(price_chg_5d, 1),
                "current_regime": regime_val,
                "current_regime_kr": regime_kr_stock,
                "rsi": round(rsi_stock, 1),
                "mom_20d": round(mom_20d, 1),
            })
        except Exception as e:
            print(f"    오류: {e}")

    return {
        "kospi": {
            "dates": dates,
            "closes": closes,
            "sma20": sma20,
            "sma60": sma60,
            "sma120": sma120,
            "rsi14": rsi14,
            "regime": regime_info,
            "periods": periods,
            "perf": perf,
        },
        "indices": indices,
        "stock_results": stock_results,
        "generated_at": end_date,
    }


def build_heatmap(stock_results: list[dict]) -> dict[str, dict[str, dict]]:
    """국면-전략 히트맵 매트릭스 집계.

    Returns:
        {regime_value: {strategy_label: {"returns": [...], "avg": float, "count": int}}}
    """
    heatmap: dict[str, dict[str, dict]] = {}

    for regime in MarketRegime:
        heatmap[regime.value] = {}
        for label in STRATEGY_LABELS + ["Buy & Hold"]:
            heatmap[regime.value][label] = {"returns": [], "avg": 0.0, "count": 0}

    for stock in stock_results:
        for rr in stock["regime_results"]:
            regime = rr.regime
            if regime not in heatmap:
                continue
            for label, br in rr.strategy_results.items():
                if label in heatmap[regime]:
                    heatmap[regime][label]["returns"].append(br.total_return_pct)
            # Buy & Hold
            bnh_vals = [br.buy_and_hold_pct for br in rr.strategy_results.values()]
            if bnh_vals:
                heatmap[regime]["Buy & Hold"]["returns"].append(bnh_vals[0])

    # 평균 계산
    for regime in heatmap:
        for label in heatmap[regime]:
            rets = heatmap[regime][label]["returns"]
            heatmap[regime][label]["count"] = len(rets)
            heatmap[regime][label]["avg"] = round(sum(rets) / len(rets), 2) if rets else 0.0

    return heatmap


def generate_html(data: dict) -> str:
    """데이터 → HTML 리포트 생성."""
    kospi = data["kospi"]
    indices = data["indices"]
    stock_results = data["stock_results"]
    regime_info = kospi["regime"]

    # 현재 국면 스타일링
    if regime_info:
        regime_val = regime_info.regime.value
        regime_kr = REGIME_KR[regime_info.regime]
        last = regime_info.last_price
        sma20_val = regime_info.sma20
        sma60_val = regime_info.sma60
        sma120_val = regime_info.sma120
        rsi_val = regime_info.rsi14 or 50.0
    else:
        regime_val = "sideways"
        regime_kr = "판별 불가"
        last = kospi["closes"][-1] if kospi["closes"] else 0
        sma20_val = sma60_val = sma120_val = last
        rsi_val = 50.0

    rc, rbg = REGIME_COLORS.get(regime_val, ("#888", "rgba(136,136,136,0.15)"))
    re = REGIME_EMOJI.get(regime_val, "")

    # 수익률 카드
    perf = kospi["perf"]

    def perf_class(v):
        if v is None:
            return "", "-"
        return ("positive" if v > 0 else "negative" if v < 0 else ""), f"{v:+.1f}%"

    # SMA 위치 설명
    sma_desc_parts = []
    for label, val in [("SMA20", sma20_val), ("SMA60", sma60_val), ("SMA120", sma120_val)]:
        if val and val > 0:
            diff_pct = (last - val) / val * 100
            pos = "위" if last > val else "아래"
            sma_desc_parts.append(f"{label} {pos} ({diff_pct:+.1f}%)")
    sma_desc = " | ".join(sma_desc_parts) if sma_desc_parts else ""

    # RSI 설명
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

    # 글로벌 지수 테이블
    global_rows = ""
    for ticker in ["^KS11", "^KQ11", "^GSPC", "^IXIC", "^VIX", "USDKRW=X"]:
        if ticker not in indices:
            continue
        idx = indices[ticker]
        vals = idx["values"]
        if not vals:
            continue

        def _pct(days):
            if len(vals) < days + 1:
                return "-"
            p = (vals[-1] - vals[-(days + 1)]) / vals[-(days + 1)] * 100
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

    # 히트맵 매트릭스
    heatmap = build_heatmap(stock_results)

    # 히트맵 테이블 생성
    regime_order = [
        MarketRegime.STRONG_BULL, MarketRegime.BULL,
        MarketRegime.SIDEWAYS, MarketRegime.BEAR, MarketRegime.STRONG_BEAR,
    ]
    all_labels = STRATEGY_LABELS + ["Buy & Hold"]

    heatmap_rows = ""
    for label in all_labels:
        cells = ""
        for regime in regime_order:
            rv = regime.value
            cell = heatmap[rv][label]
            avg = cell["avg"]
            count = cell["count"]
            if count == 0:
                cells += '<td class="heat-cell">-</td>'
            else:
                # 색상: 초록(양수) ~ 빨강(음수)
                if avg > 0:
                    intensity = min(avg / 15.0, 1.0)
                    bg = f"rgba(34,197,94,{0.1 + intensity * 0.4:.2f})"
                    tc = "#22c55e"
                elif avg < 0:
                    intensity = min(abs(avg) / 15.0, 1.0)
                    bg = f"rgba(239,68,68,{0.1 + intensity * 0.4:.2f})"
                    tc = "#ef4444"
                else:
                    bg = "rgba(136,136,136,0.1)"
                    tc = "#888"
                cells += f'<td class="heat-cell" style="background:{bg};color:{tc}">{avg:+.2f}%<br><span class="heat-count">({count}건)</span></td>'
        label_style = "font-weight:700" if label == "Buy & Hold" else ""
        heatmap_rows += f'<tr><td style="{label_style}">{label}</td>{cells}</tr>'

    # 전략 추천 박스
    best_strategy = ""
    best_avg = -999
    if regime_info:
        rv = regime_info.regime.value
        for label in STRATEGY_LABELS:
            cell = heatmap[rv][label]
            if cell["count"] > 0 and cell["avg"] > best_avg:
                best_avg = cell["avg"]
                best_strategy = label

    if best_strategy:
        recommend_html = f"""
        <div class="recommend-box">
            <div class="recommend-label">현재 국면 최적 전략 추천<span class="help" data-tip="위 히트맵에서 현재 국면에 해당하는 열의 전략 중 평균 수익률이 가장 높은 것을 추천합니다. 과거 데이터 기반이므로 참고용으로 활용하세요.">?</span></div>
            <div class="recommend-regime">{re} 현재: <strong>{regime_kr}</strong></div>
            <div class="recommend-strategy">추천: <strong>{best_strategy}</strong></div>
            <div class="recommend-avg">평균 수익률: <span class="{'positive' if best_avg > 0 else 'negative'}">{best_avg:+.2f}%</span></div>
        </div>"""
    else:
        recommend_html = ""

    # 국면 타임라인 데이터
    periods = kospi["periods"]
    timeline_segments = []
    total_days = len(kospi["closes"])
    for p in periods:
        pct_start = p.start_index / total_days * 100
        pct_width = (p.end_index - p.start_index + 1) / total_days * 100
        rcolor, _ = REGIME_COLORS.get(p.regime.value, ("#888", ""))
        rkr = REGIME_KR[p.regime]
        days = p.end_index - p.start_index + 1
        timeline_segments.append(
            f'<div class="tl-seg" style="left:{pct_start:.1f}%;width:{pct_width:.1f}%;background:{rcolor}44;border-bottom:3px solid {rcolor}" '
            f'title="{rkr} ({days}일)\n{p.start_date} ~ {p.end_date}"></div>'
        )
    timeline_html = "\n".join(timeline_segments)

    # 차트 데이터 (JSON)
    kospi_dates_json = json.dumps(kospi["dates"])
    kospi_closes_json = json.dumps(kospi["closes"])
    sma20_json = json.dumps(kospi["sma20"])
    sma60_json = json.dumps(kospi["sma60"])
    sma120_json = json.dumps(kospi["sma120"])
    rsi_json = json.dumps(kospi["rsi14"])

    # 국면 배경색 구간 (차트 플러그인용)
    regime_zones = []
    for p in periods:
        _, bg = REGIME_COLORS.get(p.regime.value, ("", "rgba(136,136,136,0.05)"))
        regime_zones.append({
            "start": p.start_index,
            "end": p.end_index,
            "color": bg,
        })
    regime_zones_json = json.dumps(regime_zones)

    # 정규화 비교 차트
    norm_datasets = []
    colors_map = {"^KS11": "#3b82f6", "^KQ11": "#8b5cf6", "^GSPC": "#f59e0b", "^IXIC": "#10b981"}
    for ticker, color in colors_map.items():
        if ticker not in indices:
            continue
        vals = indices[ticker]["values"]
        if not vals:
            continue
        base = vals[0] if vals[0] != 0 else 1
        normed = [round(v / base * 100, 2) for v in vals]
        norm_datasets.append({
            "label": indices[ticker]["name"],
            "data": normed,
            "color": color,
        })
    norm_json = json.dumps(norm_datasets, ensure_ascii=False)
    norm_dates = json.dumps(indices.get("^KS11", {}).get("dates", []))

    # 종목-전략 매트릭스
    stock_matrix_rows = ""
    for stock in stock_results:
        sym = stock["symbol"]
        name = stock["name"]

        # 전략별 · 국면별 수익률 집계
        all_labels = STRATEGY_LABELS + ["Buy & Hold"]
        strat_returns_all: dict[str, list[float]] = {label: [] for label in all_labels}
        strat_regime_detail: dict[str, dict[str, list[float]]] = {label: {} for label in all_labels}

        for rr in stock["regime_results"]:
            first_br = next(iter(rr.strategy_results.values()), None)
            if first_br:
                strat_returns_all["Buy & Hold"].append(first_br.buy_and_hold_pct)
                strat_regime_detail["Buy & Hold"].setdefault(rr.regime_kr, []).append(first_br.buy_and_hold_pct)
            for label in STRATEGY_LABELS:
                br = rr.strategy_results.get(label)
                if br:
                    strat_returns_all[label].append(br.total_return_pct)
                    strat_regime_detail[label].setdefault(rr.regime_kr, []).append(br.total_return_pct)

        # 평균 계산
        avgs: dict[str, float | None] = {}
        for label in all_labels:
            rets = strat_returns_all[label]
            avgs[label] = round(sum(rets) / len(rets), 2) if rets else None

        # 최적 전략 (B&H 제외)
        valid_strats = {k: v for k, v in avgs.items() if v is not None and k in STRATEGY_LABELS}
        best_label = max(valid_strats, key=valid_strats.get) if valid_strats else None

        cells = ""
        for label in all_labels:
            avg = avgs[label]
            if avg is not None:
                # 툴팁: 종목·전략 헤더 + 국면별 세부 + 요약
                tips = [f"[ {name} · {label} ]", ""]
                best_rk, best_ravg = None, -999.0
                for rk, rets in strat_regime_detail[label].items():
                    avg_r = sum(rets) / len(rets)
                    arrow = "▲" if avg_r > 0 else "▼" if avg_r < 0 else "―"
                    tips.append(f"  {arrow} {rk}: {avg_r:+.1f}% ({len(rets)}구간)")
                    if avg_r > best_ravg:
                        best_ravg = avg_r
                        best_rk = rk
                if best_rk:
                    tips.append("")
                    tips.append(f"→ {best_rk}에서 가장 효과적")
                tip = "&#10;".join(tips)

                # 히트맵 색상
                if avg > 0:
                    intensity = min(avg / 15.0, 1.0)
                    bg = f"rgba(34,197,94,{0.1 + intensity * 0.4:.2f})"
                elif avg < 0:
                    intensity = min(abs(avg) / 15.0, 1.0)
                    bg = f"rgba(239,68,68,{0.1 + intensity * 0.4:.2f})"
                else:
                    bg = "rgba(136,136,136,0.1)"

                cls = "positive" if avg > 0 else "negative" if avg < 0 else ""
                best_cls = " best-cell" if label == best_label else ""
                bold = "font-weight:700;" if label == "Buy & Hold" else ""
                cells += f'<td class="heat-cell tip-cell{best_cls}" style="background:{bg};{bold}" data-tip="{tip}"><span class="{cls}">{avg:+.2f}%</span></td>'
            else:
                cells += '<td class="heat-cell">-</td>'

        # 거래량 컬럼
        vr = stock.get("vol_ratio", 0)
        vv = stock.get("vol_verdict", "-")
        chg5 = stock.get("price_chg_5d", 0)
        if "확인" in vv:
            vol_color, vol_bg = "#22c55e", "rgba(34,197,94,0.12)"
        elif "부족" in vv or "투매" in vv:
            vol_color, vol_bg = "#ef4444", "rgba(239,68,68,0.12)"
        elif "급증" in vv:
            vol_color, vol_bg = "#f59e0b", "rgba(245,158,11,0.12)"
        else:
            vol_color, vol_bg = "#888", "transparent"
        vol_tip = f"[ {name} 거래량 ]&#10;&#10;금일/20일평균: {vr:.1f}x&#10;5일 등락: {chg5:+.1f}%&#10;판정: {vv}"
        vol_cell = f'<td class="heat-cell tip-cell" style="background:{vol_bg};text-align:center" data-tip="{vol_tip}"><span style="color:{vol_color};font-weight:600">{vr:.1f}x</span><br><span style="font-size:10px;color:{vol_color}">{vv}</span></td>'

        stock_matrix_rows += f'        <tr><td><strong>{sym}</strong> <span class="ticker">{name}</span></td>{cells}{vol_cell}</tr>\n'

    # --- 종합 추천 빌드 ---
    scored_stocks = []
    for stock in stock_results:
        cur_regime = stock.get("current_regime", "sideways")
        rsi_s = stock.get("rsi", 50)
        vr_s = stock.get("vol_ratio", 0)
        vv_s = stock.get("vol_verdict", "보통")
        chg5_s = stock.get("price_chg_5d", 0)
        mom20_s = stock.get("mom_20d", 0)

        # 현재 국면에서 전략별 과거 수익률
        regime_perf: dict[str, list[float]] = {}
        for rr in stock["regime_results"]:
            if rr.regime == cur_regime:
                for label, br in rr.strategy_results.items():
                    regime_perf.setdefault(label, []).append(br.total_return_pct)
        strat_avgs_rec = {}
        for label in STRATEGY_LABELS:
            rets = regime_perf.get(label, [])
            strat_avgs_rec[label] = sum(rets) / len(rets) if rets else None
        valid_s = {k: v for k, v in strat_avgs_rec.items() if v is not None}
        best_strat_s = max(valid_s, key=valid_s.get) if valid_s else "SMA 기본"
        best_ret_s = valid_s.get(best_strat_s, 0)

        # 점수 계산
        score = 0
        reasons_pro: list[str] = []
        reasons_con: list[str] = []
        reasons_neu: list[str] = []

        # (1) 백테스트 수익률
        score += best_ret_s * 2
        if best_ret_s > 3:
            reasons_pro.append(f"{stock['current_regime_kr']} 국면에서 {best_strat_s} 전략 과거 평균 {best_ret_s:+.1f}% — 검증된 조합")
        elif best_ret_s > 0:
            reasons_pro.append(f"{stock['current_regime_kr']} 국면에서 {best_strat_s} 전략 과거 {best_ret_s:+.1f}%")
        else:
            reasons_con.append(f"현재 국면({stock['current_regime_kr']})에서 과거 전략 수익률이 {best_ret_s:+.1f}%로 부진")

        # (2) 거래량 확인
        if "확인" in vv_s:
            score += 10
            reasons_pro.append(f"거래량 {vr_s:.1f}x — 상승에 거래량 동반, 신뢰도 높음")
        elif "부족" in vv_s:
            score -= 5
            reasons_con.append(f"거래량 {vr_s:.1f}x — 상승했지만 거래량 부족, 지속 불확실")
        elif "투매" in vv_s:
            score -= 8
            reasons_con.append(f"거래량 {vr_s:.1f}x — 하락 + 거래 급증, 투매 가능성")
        elif "급증" in vv_s:
            score += 5
            reasons_neu.append(f"거래량 {vr_s:.1f}x — 거래 급증, 변곡점 가능성")
        else:
            reasons_neu.append(f"거래량 {vr_s:.1f}x — 특이사항 없음")

        # (3) RSI
        if rsi_s < 35:
            score += 15
            reasons_pro.append(f"RSI {rsi_s:.0f} — 과매도 구간, 반등 기대")
        elif rsi_s < 45:
            score += 5
            reasons_pro.append(f"RSI {rsi_s:.0f} — 저점 근처, 진입 여력 충분")
        elif rsi_s > 75:
            score -= 15
            reasons_con.append(f"RSI {rsi_s:.0f} — 과매수, 조정 가능성 높음")
        elif rsi_s > 65:
            score -= 5
            reasons_con.append(f"RSI {rsi_s:.0f} — 과매수 접근 중, 진입 주의")
        else:
            reasons_neu.append(f"RSI {rsi_s:.0f} — 중립 구간")

        # (4) 모멘텀
        if chg5_s > 10:
            score -= 5
            reasons_con.append(f"5일 {chg5_s:+.1f}% 급등 — 추격매수 위험")
        elif chg5_s > 5:
            reasons_neu.append(f"5일 {chg5_s:+.1f}% — 상승 모멘텀 유지 중")
        elif -5 < chg5_s < 0:
            score += 5
            reasons_pro.append(f"5일 {chg5_s:+.1f}% — 소폭 조정, 진입 기회")
        elif chg5_s < -5:
            reasons_con.append(f"5일 {chg5_s:+.1f}% — 단기 급락 주의")

        scored_stocks.append({
            **stock,
            "score": round(score, 1),
            "best_strat": best_strat_s,
            "best_ret": best_ret_s,
            "reasons_pro": reasons_pro,
            "reasons_con": reasons_con,
            "reasons_neu": reasons_neu,
        })

    scored_stocks.sort(key=lambda x: x["score"], reverse=True)

    # 추천 카드 HTML 생성
    rec_cards = ""
    for i, s in enumerate(scored_stocks[:5], 1):
        r_rc_s, _ = REGIME_COLORS.get(s["current_regime"], ("#888", ""))
        rank_cls = " rank-1" if i == 1 else ""

        reasons_html = ""
        for r in s["reasons_pro"]:
            reasons_html += f'<div class="rec-reason pro">&#10003; {r}</div>'
        for r in s["reasons_neu"]:
            reasons_html += f'<div class="rec-reason neutral">&#9679; {r}</div>'
        for r in s["reasons_con"]:
            reasons_html += f'<div class="rec-reason con">&#10007; {r}</div>'

        rec_cards += f"""
        <div class="rec-card">
            <div class="rec-rank{rank_cls}">{i}</div>
            <div class="rec-body">
                <div class="rec-header">
                    <span class="rec-name">{s['name']}</span>
                    <span class="rec-code">{s['symbol']}</span>
                    <span class="rec-badge" style="background:{r_rc_s}22;color:{r_rc_s};border:1px solid {r_rc_s}">{s['current_regime_kr']}</span>
                    <span style="color:#888;font-size:13px">{s['last_price']:,.0f}원</span>
                </div>
                <div class="rec-strat">추천 전략: <strong>{s['best_strat']}</strong></div>
                <div class="rec-reasons">{reasons_html}</div>
            </div>
        </div>"""

    stock_recommend_html = f"""
    <div class="rec-section">
        <h2>종합 추천<span class="help" data-tip="현재 국면에서의 백테스트 수익률, 거래량 확인 여부, RSI 위치, 단기 모멘텀을 종합 점수화한 순위입니다.">?</span></h2>
        <p style="color:#888;font-size:13px;margin-bottom:16px">국면 백테스트 + 거래량 + RSI + 모멘텀을 종합한 투자 우선순위입니다.</p>
        {rec_cards}
        <div class="rec-disclaimer">위 추천은 과거 백테스트 + 기술적 지표 기반이며, 미래 수익을 보장하지 않습니다. 모의투자 환경에서 검증 후 활용하세요.</div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>시장 국면 기반 전략 선택 리포트</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Pretendard', sans-serif; background: #0f1117; color: #e0e0e0; }}
.container {{ max-width: 1300px; margin: 0 auto; padding: 24px; }}
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

/* Timeline */
.timeline-section {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 20px 0; }}
.timeline-section h2 {{ font-size: 18px; color: #fff; margin-bottom: 16px; }}
.timeline {{ position: relative; height: 40px; background: #252830; border-radius: 8px; overflow: hidden; margin-bottom: 8px; }}
.tl-seg {{ position: absolute; top: 0; height: 100%; cursor: pointer; transition: opacity 0.2s; }}
.tl-seg:hover {{ opacity: 0.7; }}
.tl-legend {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 8px; }}
.tl-legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; color: #aaa; }}
.tl-legend-dot {{ width: 12px; height: 12px; border-radius: 3px; }}

/* Heatmap */
.heatmap-section {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 20px 0; }}
.heatmap-section h2 {{ font-size: 18px; color: #fff; margin-bottom: 16px; }}
.heat-cell {{ text-align: center !important; font-weight: 600; font-size: 14px; padding: 14px 10px !important; }}
.heat-count {{ font-size: 10px; font-weight: 400; color: #888; }}

/* Recommend */
.recommend-box {{ background: {rbg}; border: 1px solid {rc}; border-radius: 12px; padding: 24px; margin: 20px 0; text-align: center; }}
.recommend-label {{ font-size: 12px; color: #aaa; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }}
.recommend-regime {{ font-size: 16px; color: #ccc; margin-bottom: 4px; }}
.recommend-strategy {{ font-size: 24px; color: #fff; margin-bottom: 8px; }}
.recommend-avg {{ font-size: 18px; }}

/* Tooltip */
.help {{ display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; border-radius: 50%; background: #333; color: #888; font-size: 11px; cursor: help; position: relative; margin-left: 6px; vertical-align: middle; flex-shrink: 0; font-weight: 400; }}
.help:hover {{ background: #444; color: #ccc; }}
.help:hover::after {{ content: attr(data-tip); position: absolute; bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%); background: #2a2d37; color: #e0e0e0; padding: 10px 14px; border-radius: 8px; font-size: 12px; white-space: normal; width: max-content; max-width: 300px; z-index: 100; line-height: 1.6; font-weight: 400; box-shadow: 0 4px 12px rgba(0,0,0,0.4); border: 1px solid #3a3d47; pointer-events: none; }}
.help:hover::before {{ content: ''; position: absolute; bottom: calc(100% + 2px); left: 50%; transform: translateX(-50%); border: 6px solid transparent; border-top-color: #3a3d47; z-index: 101; }}

/* Stock details */
.stock-detail {{ margin: 8px 0; }}
.stock-toggle {{ width: 100%; background: #1a1d27; border: 1px solid #252830; border-radius: 8px; padding: 12px 16px; color: #e0e0e0; cursor: pointer; display: flex; align-items: center; gap: 12px; font-size: 14px; text-align: left; }}
.stock-toggle:hover {{ background: #22252f; }}
.stock-toggle .stock-code {{ font-weight: 700; color: #fff; }}
.stock-toggle .stock-name {{ color: #888; flex: 1; }}
.stock-toggle .arrow {{ color: #555; margin-left: auto; }}
.stock-body {{ background: #1a1d27; border: 1px solid #252830; border-top: none; border-radius: 0 0 8px 8px; padding: 16px; }}
.stock-desc {{ color: #888; font-size: 13px; line-height: 1.6; margin-bottom: 14px; }}
.stock-desc strong {{ color: #ccc; }}
.regime-table {{ font-size: 13px; }}
.regime-table th {{ font-size: 12px; padding: 8px; }}
.regime-table td {{ padding: 8px; }}
.date-cell {{ font-size: 11px; color: #aaa; white-space: nowrap; }}
.days-sub {{ font-size: 10px; color: #666; }}
.best-cell {{ border-left: 3px solid #3b82f6 !important; }}
.best-dot {{ display: inline-block; width: 3px; height: 14px; background: #3b82f6; vertical-align: middle; margin: 0 4px; border-radius: 1px; }}
.tip-cell {{ position: relative; cursor: help; }}
.tip-cell:hover::after {{ content: attr(data-tip); position: absolute; bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%); background: #2a2d37; color: #e0e0e0; padding: 12px 16px; border-radius: 10px; font-size: 12px; white-space: pre-line; width: max-content; max-width: 280px; z-index: 100; line-height: 1.9; font-weight: 400; box-shadow: 0 6px 20px rgba(0,0,0,0.5); border: 1px solid #3a3d47; pointer-events: none; }}
.tip-cell:hover::before {{ content: ''; position: absolute; bottom: calc(100% + 2px); left: 50%; transform: translateX(-50%); border: 6px solid transparent; border-top-color: #3a3d47; z-index: 101; }}
.heatmap-section tbody tr:hover {{ background: rgba(255,255,255,0.04); }}

/* Recommendation */
.rec-section {{ background: #1a1d27; border-radius: 12px; padding: 24px; margin: 20px 0; }}
.rec-section h2 {{ font-size: 18px; color: #fff; margin-bottom: 16px; }}
.rec-card {{ background: #0f1117; border: 1px solid #252830; border-radius: 10px; padding: 20px; margin: 12px 0; display: flex; gap: 20px; }}
.rec-rank {{ font-size: 32px; font-weight: 800; color: #3b82f6; min-width: 40px; text-align: center; line-height: 1; padding-top: 4px; }}
.rec-rank.rank-1 {{ color: #f59e0b; }}
.rec-body {{ flex: 1; }}
.rec-header {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }}
.rec-name {{ font-size: 18px; font-weight: 700; color: #fff; }}
.rec-code {{ font-size: 13px; color: #555; }}
.rec-badge {{ display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.rec-strat {{ font-size: 15px; color: #e0e0e0; margin-bottom: 10px; }}
.rec-strat strong {{ color: #3b82f6; }}
.rec-reasons {{ display: flex; flex-direction: column; gap: 4px; }}
.rec-reason {{ font-size: 13px; color: #aaa; line-height: 1.5; }}
.rec-reason.pro {{ color: #4ade80; }}
.rec-reason.con {{ color: #f87171; }}
.rec-reason.neutral {{ color: #facc15; }}
.rec-disclaimer {{ color: #555; font-size: 12px; margin-top: 16px; padding: 12px; border: 1px solid #252830; border-radius: 8px; }}

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
        <h1>시장 국면 기반 전략 선택 리포트</h1>
        <p>yfinance 기반 | {data["generated_at"]} 기준 | 2년 데이터 분석 | {len(stock_results)}개 종목</p>
    </header>

    <!-- 1. 현재 국면 배너 -->
    <div class="regime-banner">
        <div class="regime-badge">{re} {regime_kr}<span class="help" data-tip="SMA 20/60/120일 이동평균선의 정배열(상승)·역배열(하락) 여부로 판별합니다. 현재가가 모든 이평선 위 = 강한 상승, 아래 = 강한 하락.">?</span></div>
        <div class="regime-value">KOSPI {last:,.0f}</div>
        <div class="regime-sma">{sma_desc}</div>
    </div>

    <!-- 수익률 카드 -->
    <div style="display:flex;align-items:center;gap:6px;margin:20px 0 4px"><span style="font-size:14px;color:#aaa">코스피 수익률</span><span class="help" data-tip="해당 기간 동안 코스피 지수의 변동률입니다. 예: 1개월 = 최근 21거래일 전 대비 현재 지수 변화.">?</span></div>
    <div class="perf-row">
        <div class="perf-card"><div class="label">1주</div><div class="value {perf_class(perf['1w'])[0]}">{perf_class(perf['1w'])[1]}</div></div>
        <div class="perf-card"><div class="label">1개월</div><div class="value {perf_class(perf['1m'])[0]}">{perf_class(perf['1m'])[1]}</div></div>
        <div class="perf-card"><div class="label">3개월</div><div class="value {perf_class(perf['3m'])[0]}">{perf_class(perf['3m'])[1]}</div></div>
        <div class="perf-card"><div class="label">6개월</div><div class="value {perf_class(perf['6m'])[0]}">{perf_class(perf['6m'])[1]}</div></div>
        <div class="perf-card"><div class="label">1년</div><div class="value {perf_class(perf['1y'])[0]}">{perf_class(perf['1y'])[1]}</div></div>
    </div>

    <!-- 지표 카드 -->
    <div class="indicator-row">
        <div class="indicator">
            <div class="label">SMA 20<span class="help" data-tip="최근 20일 종가의 단순평균. 단기 추세를 나타냅니다. 현재가가 위에 있으면 단기 상승 추세.">?</span></div>
            <div class="val">{sma20_val:,.0f}</div>
            <div class="sub">{'위' if last > sma20_val else '아래'} {abs((last - sma20_val) / sma20_val * 100):.1f}%</div>
        </div>
        <div class="indicator">
            <div class="label">SMA 60<span class="help" data-tip="최근 60일(약 3개월) 종가의 단순평균. 중기 추세를 나타냅니다.">?</span></div>
            <div class="val">{sma60_val:,.0f}</div>
            <div class="sub">{'위' if last > sma60_val else '아래'} {abs((last - sma60_val) / sma60_val * 100):.1f}%</div>
        </div>
        <div class="indicator">
            <div class="label">SMA 120<span class="help" data-tip="최근 120일(약 6개월) 종가의 단순평균. 장기 추세를 나타냅니다. 국면 판별의 핵심 기준선.">?</span></div>
            <div class="val">{sma120_val:,.0f}</div>
            <div class="sub">{'위' if last > sma120_val else '아래'} {abs((last - sma120_val) / sma120_val * 100):.1f}%</div>
        </div>
        <div class="indicator">
            <div class="label">RSI (14)<span class="help" data-tip="상대강도지수. 14일간 상승/하락 폭의 비율. 70 이상 = 과매수(조정 가능성), 30 이하 = 과매도(반등 가능성).">?</span></div>
            <div class="val" style="color:{rsi_color}">{rsi_val:.1f}</div>
            <div class="sub">{rsi_desc}</div>
        </div>
    </div>

    <!-- 2. 코스피 차트 + SMA + 국면 배경색 -->
    <div class="section">
        <h2>코스피 지수 + 이동평균선 + 국면 구간<span class="help" data-tip="파란 실선이 코스피 지수, 점선이 이동평균선(SMA). 배경색은 국면을 나타냅니다. 초록=상승, 노란=횡보, 빨간=하락. 이평선이 정배열(단기>중기>장기)이면 상승 추세.">?</span></h2>
        <div class="chart-box"><canvas id="kospiChart"></canvas></div>
    </div>

    <!-- RSI -->
    <div class="section">
        <h2>RSI (14)<span class="help" data-tip="빨간 점선(70) 위 = 과매수 구간, 초록 점선(30) 아래 = 과매도 구간. 극단 영역에서는 추세 반전 가능성이 높아집니다.">?</span></h2>
        <div class="chart-box-sm"><canvas id="rsiChart"></canvas></div>
    </div>

    <!-- 6. 국면 타임라인 -->
    <div class="timeline-section">
        <h2>국면 타임라인<span class="help" data-tip="과거 2년간 코스피의 국면 변화를 시간순으로 표시합니다. 색상 구간 위에 마우스를 올리면 국면 종류, 기간, 날짜를 확인할 수 있습니다.">?</span></h2>
        <div class="timeline">{timeline_html}</div>
        <div class="tl-legend">
            <div class="tl-legend-item"><div class="tl-legend-dot" style="background:#22c55e"></div>강한 상승</div>
            <div class="tl-legend-item"><div class="tl-legend-dot" style="background:#4ade80"></div>상승</div>
            <div class="tl-legend-item"><div class="tl-legend-dot" style="background:#facc15"></div>횡보</div>
            <div class="tl-legend-item"><div class="tl-legend-dot" style="background:#f87171"></div>하락</div>
            <div class="tl-legend-item"><div class="tl-legend-dot" style="background:#ef4444"></div>강한 하락</div>
        </div>
    </div>

    <!-- 7. 국면-전략 히트맵 -->
    <div class="heatmap-section">
        <h2>국면-전략 수익률 히트맵<span class="help" data-tip="이 표가 핵심입니다. 11개 종목의 2년 데이터를 국면별로 나눈 뒤, 각 구간에서 4개 전략을 독립 실행한 평균 수익률입니다. 진한 초록 = 높은 수익, 진한 빨강 = 큰 손실. (N건)은 해당 국면이 발생한 구간 수.">?</span></h2>
        <p style="color:#888;font-size:13px;margin-bottom:16px">각 국면에서 전략별 평균 수익률. 11개 종목 × 국면별 구간의 집계. 각 구간은 독립 자본(1,000만원)으로 시뮬레이션.</p>
        <table>
            <thead>
                <tr>
                    <th style="text-align:left">전략<span class="help" data-tip="SMA 기본: 이동평균 크로스오버만. SMA+리스크: 손절(5%)+보유기간 제한 추가. SMA+Adv+리스크: RSI·거래량·OBV 필터까지 추가. 볼린저: 밴드 하단 반등 매수, 상단 도달 매도. B&amp;H: 매수 후 보유(아무것도 안 함).">?</span></th>
                    <th style="text-align:center;color:#22c55e">강한 상승</th>
                    <th style="text-align:center;color:#4ade80">상승</th>
                    <th style="text-align:center;color:#facc15">횡보</th>
                    <th style="text-align:center;color:#f87171">하락</th>
                    <th style="text-align:center;color:#ef4444">강한 하락</th>
                </tr>
            </thead>
            <tbody>{heatmap_rows}</tbody>
        </table>
    </div>

    <!-- 8. 전략 추천 -->
    {recommend_html}

    <!-- 글로벌 지수 비교 -->
    <div class="section">
        <h2>글로벌 지수 비교 (정규화, 시작=100)<span class="help" data-tip="2년 전 시점을 100으로 놓고 현재까지의 상대적 변동을 비교합니다. 코스피가 나스닥보다 낮으면 같은 기간 수익률이 열위라는 뜻입니다.">?</span></h2>
        <div class="chart-box"><canvas id="normChart"></canvas></div>
    </div>

    <div class="section">
        <h2>글로벌 지수 수익률<span class="help" data-tip="주요 글로벌 지수의 기간별 수익률입니다. VIX는 변동성 지수로 높을수록 시장 불안, USD/KRW은 원달러 환율입니다.">?</span></h2>
        <table>
            <thead><tr><th>지수</th><th>현재</th><th>1주</th><th>1개월</th><th>3개월</th><th>1년</th></tr></thead>
            <tbody>{global_rows}</tbody>
        </table>
    </div>

    <!-- 9. 종목-전략 매트릭스 -->
    <div class="heatmap-section">
        <h2>종목별 전략 수익률 매트릭스<span class="help" data-tip="각 종목의 2년 차트를 국면 구간별로 나눈 뒤, 4개 전략을 독립 시뮬레이션한 평균 수익률입니다. 셀에 마우스를 올리면 국면별 세부 수익률을 확인할 수 있습니다.">?</span></h2>
        <p style="color:#888;font-size:13px;margin-bottom:16px">각 종목의 2년 데이터를 국면별로 나눠 전략을 독립 시뮬레이션한 평균 수익률입니다. 셀 위에 마우스를 올리면 어떤 국면에서 효과적인지 볼 수 있습니다. <span class="best-dot"></span>= 해당 종목 최적 전략.</p>
        <table>
            <thead>
                <tr>
                    <th style="text-align:left">종목</th>
                    <th style="text-align:center">SMA 기본</th>
                    <th style="text-align:center">SMA+리스크</th>
                    <th style="text-align:center">SMA+Adv+리스크</th>
                    <th style="text-align:center">볼린저</th>
                    <th style="text-align:center;font-weight:700">Buy &amp; Hold</th>
                    <th style="text-align:center">거래량<span class="help" data-tip="금일 거래량 / 최근 20일 평균 거래량. 1.0x 이상이면 평균 이상. 가격 상승 시 거래량 동반(1.5x+) = 신뢰도 높음, 거래량 부족(0.8x 이하) = 주의.">?</span></th>
                </tr>
            </thead>
            <tbody>
{stock_matrix_rows}
            </tbody>
        </table>
    </div>

    <!-- 10. 종합 추천 -->
    {stock_recommend_html}
</div>

<footer>Quantum Trading Platform — Market Regime Strategy Report</footer>

<script>
const dates = {kospi_dates_json};
const closes = {kospi_closes_json};
const sma20 = {sma20_json};
const sma60 = {sma60_json};
const sma120 = {sma120_json};
const rsiData = {rsi_json};
const regimeZones = {regime_zones_json};

const step = Math.max(1, Math.floor(dates.length / 12));
const labels = dates.map((d, i) => i % step === 0 ? d.slice(2, 7) : '');

// KOSPI chart with regime background
const regimeBgPlugin = {{
    id: 'regimeBg',
    beforeDraw(chart) {{
        const ctx = chart.ctx;
        const xAxis = chart.scales.x;
        const yAxis = chart.scales.y;
        ctx.save();
        regimeZones.forEach(zone => {{
            const x1 = xAxis.getPixelForValue(zone.start);
            const x2 = xAxis.getPixelForValue(zone.end);
            ctx.fillStyle = zone.color;
            ctx.fillRect(x1, yAxis.top, x2 - x1, yAxis.bottom - yAxis.top);
        }});
        ctx.restore();
    }}
}};

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
    }},
    plugins: [regimeBgPlugin]
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
        plugins: {{ legend: {{ display: false }} }},
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
            const y70 = yAxis.getPixelForValue(70);
            ctx.save();
            ctx.strokeStyle = 'rgba(239,68,68,0.4)';
            ctx.setLineDash([4,4]);
            ctx.beginPath(); ctx.moveTo(xAxis.left, y70); ctx.lineTo(xAxis.right, y70); ctx.stroke();
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
    print("=" * 60)
    print("시장 국면 기반 전략 선택 리포트 생성")
    print("=" * 60)

    data = collect_data()
    html = generate_html(data)

    out = "regime_strategy_report.html"
    with open(out, "w") as f:
        f.write(html)
    print(f"\nReport generated: {out}")
