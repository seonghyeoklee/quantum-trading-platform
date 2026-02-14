#!/usr/bin/env python
"""볼린저밴드 반전 전략 백테스트 — SMA 크로스오버 전략과 비교"""

import sys
from datetime import datetime, timedelta

from app.trading.backtest import (
    fetch_chart_from_yfinance,
    run_backtest,
    run_bollinger_backtest,
    to_yfinance_ticker,
)

# 감시 종목 리스트
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

# 백테스트 기간: 최근 1년
END_DATE = datetime.now().strftime("%Y%m%d")
START_DATE = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

# 파라미터
INITIAL_CAPITAL = 10_000_000
ORDER_AMOUNT = 1_000_000

# SMA 파라미터
SMA_SHORT = 10
SMA_LONG = 40

# 볼린저밴드 파라미터
BB_PERIOD = 20
BB_NUM_STD = 2.0
BB_MAX_HOLDING = 5
BB_MAX_DAILY = 5


def fmt(val: float | None, suffix: str = "%") -> str:
    if val is None:
        return "N/A"
    return f"{val:+.2f}{suffix}" if suffix == "%" else f"{val:.4f}"


def main():
    print(f"{'='*80}")
    print(f"볼린저밴드 vs SMA 크로스오버 백테스트 비교")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"{'='*80}")
    print()

    # 헤더
    print(f"{'종목':<16} {'전략':<12} {'수익률':>8} {'B&H':>8} {'거래':>4} {'승률':>7} {'MDD':>8} {'Sharpe':>8}")
    print("-" * 80)

    bb_returns = []
    sma_returns = []
    bb_trades_total = 0
    sma_trades_total = 0
    bb_mdd_worst = 0.0
    sma_mdd_worst = 0.0
    bb_sharpes = []
    sma_sharpes = []
    bb_wins = []
    sma_wins = []

    for code, name in SYMBOLS:
        ticker = to_yfinance_ticker(code)

        try:
            chart = fetch_chart_from_yfinance(ticker, START_DATE, END_DATE)
        except Exception as e:
            print(f"  {code} {name}: 데이터 조회 실패 ({e})", file=sys.stderr)
            continue

        if not chart:
            print(f"  {code} {name}: 데이터 없음", file=sys.stderr)
            continue

        # 볼린저밴드 백테스트
        bb = run_bollinger_backtest(
            chart=chart,
            initial_capital=INITIAL_CAPITAL,
            order_amount=ORDER_AMOUNT,
            period=BB_PERIOD,
            num_std=BB_NUM_STD,
            max_holding_days=BB_MAX_HOLDING,
            max_daily_trades=BB_MAX_DAILY,
        )

        # SMA 크로스오버 백테스트
        sma = run_backtest(
            chart=chart,
            initial_capital=INITIAL_CAPITAL,
            order_amount=ORDER_AMOUNT,
            short_period=SMA_SHORT,
            long_period=SMA_LONG,
        )

        label = f"{code} {name}"
        print(
            f"{label:<16} {'Bollinger':<12} {fmt(bb.total_return_pct):>8} {fmt(bb.buy_and_hold_pct):>8} "
            f"{bb.trade_count:>4} {fmt(bb.win_rate):>7} {fmt(-bb.max_drawdown_pct):>8} "
            f"{fmt(bb.sharpe_ratio, ''):>8}"
        )
        print(
            f"{'':<16} {'SMA':<12} {fmt(sma.total_return_pct):>8} {fmt(sma.buy_and_hold_pct):>8} "
            f"{sma.trade_count:>4} {fmt(sma.win_rate):>7} {fmt(-sma.max_drawdown_pct):>8} "
            f"{fmt(sma.sharpe_ratio, ''):>8}"
        )
        print()

        bb_returns.append(bb.total_return_pct)
        sma_returns.append(sma.total_return_pct)
        bb_trades_total += bb.trade_count
        sma_trades_total += sma.trade_count
        bb_mdd_worst = max(bb_mdd_worst, bb.max_drawdown_pct)
        sma_mdd_worst = max(sma_mdd_worst, sma.max_drawdown_pct)
        if bb.sharpe_ratio is not None:
            bb_sharpes.append(bb.sharpe_ratio)
        if sma.sharpe_ratio is not None:
            sma_sharpes.append(sma.sharpe_ratio)
        if bb.trade_count > 0:
            bb_wins.append(bb.win_rate)
        if sma.trade_count > 0:
            sma_wins.append(sma.win_rate)

    # 포트폴리오 합산
    n = len(bb_returns)
    if n == 0:
        print("유효한 종목 데이터 없음")
        sys.exit(1)

    print("=" * 80)
    print("포트폴리오 합산 결과")
    print("=" * 80)
    print(f"{'지표':<24} {'Bollinger':>16} {'SMA':>16}")
    print("-" * 60)
    print(f"{'평균 수익률':<24} {sum(bb_returns)/n:>+15.2f}% {sum(sma_returns)/n:>+15.2f}%")
    print(f"{'총 거래 횟수':<24} {bb_trades_total:>16} {sma_trades_total:>16}")
    bb_avg_win = sum(bb_wins) / len(bb_wins) if bb_wins else 0
    sma_avg_win = sum(sma_wins) / len(sma_wins) if sma_wins else 0
    print(f"{'평균 승률':<24} {bb_avg_win:>15.2f}% {sma_avg_win:>15.2f}%")
    print(f"{'최악 MDD':<24} {-bb_mdd_worst:>15.2f}% {-sma_mdd_worst:>15.2f}%")
    bb_avg_sharpe = sum(bb_sharpes) / len(bb_sharpes) if bb_sharpes else 0
    sma_avg_sharpe = sum(sma_sharpes) / len(sma_sharpes) if sma_sharpes else 0
    print(f"{'평균 Sharpe':<24} {bb_avg_sharpe:>16.4f} {sma_avg_sharpe:>16.4f}")


if __name__ == "__main__":
    main()
