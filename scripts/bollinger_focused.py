#!/usr/bin/env python
"""선호 5종목 볼린저밴드 집중 백테스트"""

import sys
from datetime import datetime, timedelta

from app.trading.backtest import (
    fetch_chart_from_yfinance,
    run_bollinger_backtest,
    to_yfinance_ticker,
)

SYMBOLS = [
    ("005930", "삼성전자"),
    ("000660", "SK하이닉스"),
    ("005380", "현대차"),
    ("034020", "두산에너빌리티"),
    ("298040", "효성중공업"),
]

END_DATE = datetime.now().strftime("%Y%m%d")
START_DATE = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

# 자본금: 종목당 1,000만원 (총 5,000만원)
CAPITAL_PER_STOCK = 10_000_000

# Best 파라미터
PERIOD = 10
NUM_STD = 1.8
MAX_HOLD = 15
ORDER_RATIO = 0.8


def main():
    print(f"{'='*70}")
    print(f"선호 5종목 볼린저밴드 집중 백테스트")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"종목당 자본: {CAPITAL_PER_STOCK:,}원 (총 {CAPITAL_PER_STOCK * len(SYMBOLS):,}원)")
    print(f"파라미터: period={PERIOD}, σ={NUM_STD}, hold={MAX_HOLD}, 투입비율={ORDER_RATIO:.0%}")
    print(f"{'='*70}\n")

    order_amount = int(CAPITAL_PER_STOCK * ORDER_RATIO)
    total_capital = CAPITAL_PER_STOCK * len(SYMBOLS)
    portfolio_pnl = 0.0
    portfolio_trades = 0

    print(f"{'종목':<16} {'수익률':>8} {'손익(원)':>12} {'B&H':>8} {'거래':>4} {'승률':>7} {'MDD':>8} {'Sharpe':>8}")
    print("-" * 80)

    for code, name in SYMBOLS:
        ticker = to_yfinance_ticker(code)
        try:
            chart = fetch_chart_from_yfinance(ticker, START_DATE, END_DATE)
        except Exception as e:
            print(f"  {code} {name}: 데이터 실패 ({e})", file=sys.stderr)
            continue
        if not chart:
            continue

        r = run_bollinger_backtest(
            chart=chart,
            initial_capital=CAPITAL_PER_STOCK,
            order_amount=order_amount,
            period=PERIOD,
            num_std=NUM_STD,
            max_holding_days=MAX_HOLD,
        )

        pnl = r.equity_curve[-1] - CAPITAL_PER_STOCK if r.equity_curve else 0
        portfolio_pnl += pnl
        portfolio_trades += r.trade_count

        label = f"{code} {name}"
        print(
            f"{label:<16} {r.total_return_pct:>+7.2f}% {pnl:>+12,.0f} "
            f"{r.buy_and_hold_pct:>+7.2f}% {r.trade_count:>4} "
            f"{r.win_rate:>6.1f}% {-r.max_drawdown_pct:>7.2f}% "
            f"{r.sharpe_ratio if r.sharpe_ratio else 0:>8.4f}"
        )

    portfolio_ret = portfolio_pnl / total_capital * 100

    print(f"\n{'='*70}")
    print(f"포트폴리오 합산")
    print(f"{'='*70}")
    print(f"  총 투자금:  {total_capital:>14,}원")
    print(f"  총 손익:    {portfolio_pnl:>+14,.0f}원")
    print(f"  총 수익률:  {portfolio_ret:>+13.2f}%")
    print(f"  총 거래수:  {portfolio_trades:>14}건")


if __name__ == "__main__":
    main()
