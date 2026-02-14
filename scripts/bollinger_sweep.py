#!/usr/bin/env python
"""볼린저밴드 파라미터 스윕 — 최적 조합 탐색"""

import sys
from datetime import datetime, timedelta
from itertools import product

from app.trading.backtest import (
    fetch_chart_from_yfinance,
    run_bollinger_backtest,
    to_yfinance_ticker,
)

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

END_DATE = datetime.now().strftime("%Y%m%d")
START_DATE = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
INITIAL_CAPITAL = 10_000_000

# 스윕 파라미터
PERIODS = [10, 15, 20]
NUM_STDS = [1.5, 1.8, 2.0]
MAX_HOLDINGS = [5, 10, 15, 20]
# 자본금 대비 주문비율 (100% = 전체 투입)
ORDER_RATIOS = [0.5, 0.8, 1.0]


def main():
    # 데이터 미리 로드
    chart_data = {}
    for code, name in SYMBOLS:
        ticker = to_yfinance_ticker(code)
        try:
            chart = fetch_chart_from_yfinance(ticker, START_DATE, END_DATE)
            if chart:
                chart_data[code] = (name, chart)
        except Exception as e:
            print(f"[WARN] {code} {name} 로드 실패: {e}", file=sys.stderr)

    print(f"로드 완료: {len(chart_data)}종목, 기간: {START_DATE}~{END_DATE}")
    print()

    # 파라미터 조합 스윕
    combos = list(product(PERIODS, NUM_STDS, MAX_HOLDINGS, ORDER_RATIOS))
    print(f"테스트할 조합: {len(combos)}개")
    print()

    results = []

    for period, num_std, max_hold, order_ratio in combos:
        order_amount = int(INITIAL_CAPITAL * order_ratio)
        returns = []
        win_rates = []
        mdds = []
        sharpes = []
        trade_counts = []

        for code, (name, chart) in chart_data.items():
            r = run_bollinger_backtest(
                chart=chart,
                initial_capital=INITIAL_CAPITAL,
                order_amount=order_amount,
                period=period,
                num_std=num_std,
                max_holding_days=max_hold,
            )
            returns.append(r.total_return_pct)
            trade_counts.append(r.trade_count)
            if r.trade_count > 0:
                win_rates.append(r.win_rate)
            mdds.append(r.max_drawdown_pct)
            if r.sharpe_ratio is not None:
                sharpes.append(r.sharpe_ratio)

        n = len(returns)
        avg_ret = sum(returns) / n
        avg_trades = sum(trade_counts) / n
        avg_win = sum(win_rates) / len(win_rates) if win_rates else 0
        worst_mdd = max(mdds)
        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0

        results.append({
            "period": period,
            "num_std": num_std,
            "max_hold": max_hold,
            "order_ratio": order_ratio,
            "avg_ret": avg_ret,
            "avg_trades": avg_trades,
            "avg_win": avg_win,
            "worst_mdd": worst_mdd,
            "avg_sharpe": avg_sharpe,
        })

    # 수익률 기준 정렬
    results.sort(key=lambda x: x["avg_ret"], reverse=True)

    print(f"{'Rank':<5} {'Period':>6} {'σ':>5} {'Hold':>5} {'Ratio':>6} "
          f"{'수익률':>8} {'거래수':>6} {'승률':>7} {'MDD':>8} {'Sharpe':>8}")
    print("-" * 80)

    for i, r in enumerate(results[:20]):
        print(
            f"{i+1:<5} {r['period']:>6} {r['num_std']:>5.1f} {r['max_hold']:>5} "
            f"{r['order_ratio']:>5.0%} "
            f"{r['avg_ret']:>+7.2f}% {r['avg_trades']:>6.1f} "
            f"{r['avg_win']:>6.1f}% {-r['worst_mdd']:>7.2f}% "
            f"{r['avg_sharpe']:>8.4f}"
        )

    # 종목별 Best 파라미터 성과
    best = results[0]
    print()
    print(f"{'='*80}")
    print(f"Best 파라미터: period={best['period']}, σ={best['num_std']}, "
          f"hold={best['max_hold']}, ratio={best['order_ratio']:.0%}")
    print(f"{'='*80}")

    order_amount = int(INITIAL_CAPITAL * best["order_ratio"])
    print(f"\n{'종목':<16} {'수익률':>8} {'B&H':>8} {'거래':>4} {'승률':>7} {'MDD':>8} {'Sharpe':>8}")
    print("-" * 70)

    stock_results = []
    for code, (name, chart) in chart_data.items():
        r = run_bollinger_backtest(
            chart=chart,
            initial_capital=INITIAL_CAPITAL,
            order_amount=order_amount,
            period=best["period"],
            num_std=best["num_std"],
            max_holding_days=best["max_hold"],
        )
        label = f"{code} {name}"
        print(
            f"{label:<16} {r.total_return_pct:>+7.2f}% {r.buy_and_hold_pct:>+7.2f}% "
            f"{r.trade_count:>4} {r.win_rate:>6.1f}% {-r.max_drawdown_pct:>7.2f}% "
            f"{r.sharpe_ratio if r.sharpe_ratio else 0:>8.4f}"
        )
        stock_results.append((code, name, r))

    # 수익률 순 정렬
    stock_results.sort(key=lambda x: x[2].total_return_pct, reverse=True)
    print()
    print("종목별 수익률 순위 (포트폴리오 편입 추천):")
    for i, (code, name, r) in enumerate(stock_results):
        flag = "★" if r.total_return_pct > 0 and r.win_rate >= 50 else " "
        print(f"  {i+1}. {flag} {code} {name}: {r.total_return_pct:+.2f}% "
              f"(승률 {r.win_rate:.0f}%, MDD {-r.max_drawdown_pct:.2f}%)")


if __name__ == "__main__":
    main()
