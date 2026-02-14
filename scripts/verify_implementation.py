"""구현 검증 스크립트 — 실제 yfinance 데이터로 기능 확인

검증 항목:
1. evaluate_signal() 거래량 필터 동작 확인
2. run_backtest() volume_filter_basic 동작 확인
3. 국면 감지 + 전략 매핑 로직 확인
4. 히트맵 결과 vs CLAUDE.md 문서 일관성
"""

import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta

from app.models import ChartData
from app.trading.backtest import run_backtest, run_bollinger_backtest, run_regime_segmented_backtest
from app.trading.regime import MarketRegime, REGIME_KR, detect_current_regime
from app.trading.strategy import evaluate_signal, compute_sma


# ── yfinance 데이터 가져오기 ──

def fetch_chart(ticker: str, start: str, end: str) -> list[ChartData]:
    import yfinance as yf
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        return []
    if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
        df = df.droplevel(level=1, axis=1)
    result = []
    for date, row in df.iterrows():
        result.append(ChartData(
            date=date.strftime("%Y%m%d"),
            open=round(row["Open"]), high=round(row["High"]),
            low=round(row["Low"]), close=round(row["Close"]),
            volume=round(row["Volume"]),
        ))
    return result


SYMBOLS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "035420": "NAVER",
}

end_date = datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════
# 1. evaluate_signal() 거래량 필터 확인
# ═══════════════════════════════════════════════
print("=" * 70)
print("1. evaluate_signal() 거래량 필터 검증")
print("=" * 70)

ticker = "005930.KS"
chart = fetch_chart(ticker, start_date, end_date)
print(f"삼성전자 데이터: {len(chart)}일")

# 필터 없이
sig_no, s, l = evaluate_signal(chart, 10, 40)
# 필터 있으면 BUY가 차단될 수 있음
sig_vol, sv, lv = evaluate_signal(chart, 10, 40, volume_ma_period=20)

print(f"  volume_ma_period=None → {sig_no.value} (SMA10={s:.0f}, SMA40={l:.0f})")
print(f"  volume_ma_period=20   → {sig_vol.value} (SMA10={sv:.0f}, SMA40={lv:.0f})")
if sig_no.value == "BUY" and sig_vol.value == "HOLD":
    print("  ✓ 거래량 부족으로 BUY → HOLD 차단 확인!")
elif sig_no.value == sig_vol.value:
    print(f"  ✓ 동일 시그널 ({sig_no.value}) — 거래량 조건 충족이거나 BUY 아님")


# ═══════════════════════════════════════════════
# 2. run_backtest() volume_filter_basic 비교
# ═══════════════════════════════════════════════
print()
print("=" * 70)
print("2. run_backtest() volume_filter_basic 비교")
print("=" * 70)

for symbol, name in SYMBOLS.items():
    ticker = f"{symbol}.KS"
    chart = fetch_chart(ticker, start_date, end_date)
    if len(chart) < 50:
        continue

    basic = run_backtest(chart, short_period=10, long_period=40, volume_filter_basic=False)
    with_vol = run_backtest(chart, short_period=10, long_period=40, volume_filter_basic=True, volume_ma_period=20)

    basic_buys = len([t for t in basic.trades if t.side == "buy"])
    vol_buys = len([t for t in with_vol.trades if t.side == "buy"])

    print(f"  {name:8s} | 필터없음: {basic_buys}회 매수, {basic.total_return_pct:+.2f}% | "
          f"거래량필터: {vol_buys}회 매수, {with_vol.total_return_pct:+.2f}%")
    if vol_buys <= basic_buys:
        print(f"          ✓ 거래량 필터 → 매수 {basic_buys - vol_buys}건 차단")
    else:
        print("          ✗ 예상 위반: 거래량 필터가 매수를 더 늘림")


# ═══════════════════════════════════════════════
# 3. 국면 감지 + 전략 매핑 검증
# ═══════════════════════════════════════════════
print()
print("=" * 70)
print("3. 국면 감지 + 자동 전략 매핑 검증")
print("=" * 70)

# 문서 매핑 테이블
REGIME_STRATEGY_MAP = {
    MarketRegime.STRONG_BULL: "SMA_CROSSOVER (+advanced +stop_loss +max_holding)",
    MarketRegime.BULL:        "SMA_CROSSOVER (+advanced +stop_loss +max_holding)",
    MarketRegime.SIDEWAYS:    "BOLLINGER",
    MarketRegime.BEAR:        "BOLLINGER",
    MarketRegime.STRONG_BEAR: "BOLLINGER",
}

# 코스피 지수로 시장 국면 판별
kospi_chart = fetch_chart("^KS11", start_date, end_date)
kospi_closes = [float(c.close) for c in kospi_chart]
kospi_regime = detect_current_regime(kospi_closes)

if kospi_regime:
    regime = kospi_regime.regime
    print(f"  코스피 현재 국면: {REGIME_KR[regime]} ({regime.value})")
    print(f"    현재가: {kospi_regime.last_price:,.0f}")
    print(f"    SMA20:  {kospi_regime.sma20:,.0f}")
    print(f"    SMA60:  {kospi_regime.sma60:,.0f}")
    print(f"    SMA120: {kospi_regime.sma120:,.0f}")
    print(f"    RSI14:  {kospi_regime.rsi14:.1f}")
    print(f"    추천 전략: {REGIME_STRATEGY_MAP[regime]}")
else:
    print("  코스피 국면 판별 불가 (데이터 부족)")

# 각 종목 개별 국면
print()
print("  [종목별 국면]")
for symbol, name in SYMBOLS.items():
    ticker = f"{symbol}.KS"
    chart = fetch_chart(ticker, start_date, end_date)
    closes = [float(c.close) for c in chart]
    info = detect_current_regime(closes)
    if info:
        mapped = REGIME_STRATEGY_MAP[info.regime]
        print(f"  {name:8s} | {REGIME_KR[info.regime]:5s} | RSI {info.rsi14:.0f} | → {mapped}")
    else:
        print(f"  {name:8s} | 판별불가")


# ═══════════════════════════════════════════════
# 4. 국면별 히트맵 — 문서 검증
# ═══════════════════════════════════════════════
print()
print("=" * 70)
print("4. 국면별 전략 수익률 히트맵 (실제 백테스트)")
print("=" * 70)

STRATEGY_LABELS = ["SMA 기본", "SMA+리스크", "SMA+Adv+리스크", "볼린저"]

# 종목별 국면 백테스트 수집
heatmap: dict[str, dict[str, list[float]]] = {}
for regime in MarketRegime:
    heatmap[regime.value] = {label: [] for label in STRATEGY_LABELS + ["Buy & Hold"]}

for symbol, name in SYMBOLS.items():
    ticker = f"{symbol}.KS"
    chart = fetch_chart(ticker, start_date, end_date)
    if len(chart) < 120:
        print(f"  {name}: 데이터 부족 ({len(chart)}일) — 스킵")
        continue

    results = run_regime_segmented_backtest(
        chart, initial_capital=10_000_000, order_amount=1_000_000,
        short_period=10, long_period=40,
    )

    for rr in results:
        rv = rr.regime
        for label, br in rr.strategy_results.items():
            heatmap[rv][label].append(br.total_return_pct)
        bnh = list(rr.strategy_results.values())[0].buy_and_hold_pct
        heatmap[rv]["Buy & Hold"].append(bnh)

# 히트맵 출력
all_labels = STRATEGY_LABELS + ["Buy & Hold"]
regime_order = [MarketRegime.STRONG_BULL, MarketRegime.BULL, MarketRegime.SIDEWAYS, MarketRegime.BEAR, MarketRegime.STRONG_BEAR]

header = f"{'전략':16s}"
for r in regime_order:
    header += f" | {REGIME_KR[r]:>6s}"
print(header)
print("-" * len(header.encode("euc-kr")))

for label in all_labels:
    row = f"{label:16s}"
    for r in regime_order:
        rets = heatmap[r.value][label]
        if rets:
            avg = sum(rets) / len(rets)
            row += f" | {avg:+6.2f}%"
        else:
            row += " |      -"
    print(row)

# 문서 검증: 각 국면에서 최적 전략 확인
print()
print("  [국면별 최적 전략 (B&H 제외)]")
for r in regime_order:
    best_label = None
    best_avg = -999
    for label in STRATEGY_LABELS:
        rets = heatmap[r.value][label]
        if rets:
            avg = sum(rets) / len(rets)
            if avg > best_avg:
                best_avg = avg
                best_label = label
    bnh_rets = heatmap[r.value]["Buy & Hold"]
    bnh_avg = sum(bnh_rets) / len(bnh_rets) if bnh_rets else 0
    mapped = REGIME_STRATEGY_MAP[r]
    print(f"  {REGIME_KR[r]:5s} → 최적: {best_label or '-':16s} ({best_avg:+.2f}%) | B&H: {bnh_avg:+.2f}% | 엔진 매핑: {mapped}")


# ═══════════════════════════════════════════════
# 5. "SMA 기본"에 volume_filter_basic 반영 확인
# ═══════════════════════════════════════════════
print()
print("=" * 70)
print("5. run_regime_segmented_backtest()에서 'SMA 기본' 거래량 필터 활성화 확인")
print("=" * 70)

# 삼성전자로 확인
chart = fetch_chart("005930.KS", start_date, end_date)
if len(chart) >= 120:
    results = run_regime_segmented_backtest(chart, short_period=10, long_period=40)

    # SMA 기본은 volume_filter_basic=True로 호출됨
    # 비교: 직접 volume_filter_basic=False로 호출
    from app.trading.regime import segment_by_regime
    closes_raw = [float(c.close) for c in chart]
    dates_raw = [c.date for c in chart]
    periods = segment_by_regime(closes_raw, dates_raw)

    if periods:
        warmup = max(40, 120)
        p = periods[0]
        pad_start = max(0, p.start_index - warmup)
        segment = chart[pad_start : p.end_index + 1]

        basic_no_vol = run_backtest(segment, short_period=10, long_period=40, volume_filter_basic=False)
        basic_with_vol = run_backtest(segment, short_period=10, long_period=40, volume_filter_basic=True, volume_ma_period=20)

        regime_basic = results[0].strategy_results.get("SMA 기본")

        no_buys = len([t for t in basic_no_vol.trades if t.side == "buy"])
        with_buys = len([t for t in basic_with_vol.trades if t.side == "buy"])
        regime_buys = len([t for t in regime_basic.trades if t.side == "buy"]) if regime_basic else -1

        print(f"  첫 번째 국면 ({REGIME_KR[periods[0].regime]}, {periods[0].start_date}~{periods[0].end_date})")
        print(f"    volume_filter_basic=False → {no_buys}회 매수, {basic_no_vol.total_return_pct:+.2f}%")
        print(f"    volume_filter_basic=True  → {with_buys}회 매수, {basic_with_vol.total_return_pct:+.2f}%")
        print(f"    regime_segmented 'SMA 기본' → {regime_buys}회 매수, {regime_basic.total_return_pct:+.2f}%")

        if regime_buys == with_buys:
            print("    ✓ regime_segmented_backtest가 volume_filter_basic=True로 호출됨 확인!")
        else:
            print("    ⚠ 매수 횟수 불일치 — 추가 확인 필요")


print()
print("=" * 70)
print("검증 완료")
print("=" * 70)
