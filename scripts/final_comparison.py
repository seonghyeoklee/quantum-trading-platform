#!/usr/bin/env python
"""최종 비교 — 최적화된 4개 전략 vs B&H 종합 성능 비교"""

import json
from datetime import datetime

from app.trading.backtest import (
    BacktestResult,
    fetch_chart_from_yfinance,
    run_backtest,
    run_bollinger_backtest,
    run_kama_backtest,
    run_breakout_backtest,
    to_yfinance_ticker,
)


def load_charts(config):
    end_date = config.get("end_date") or datetime.now().strftime("%Y%m%d")
    charts = {}
    for sym in config["symbols"]:
        ticker = to_yfinance_ticker(sym["code"])
        try:
            chart = fetch_chart_from_yfinance(ticker, config["start_date"], end_date)
            if chart:
                charts[sym["name"]] = chart
        except:
            pass
    return charts


def main():
    with open("scripts/backtest_config.json") as f:
        config = json.load(f)

    capital = config["initial_capital"]
    print("차트 데이터 로딩...")
    charts = load_charts(config)
    names = list(charts.keys())
    print(f"{len(charts)}개 종목\n")

    # 최적화된 파라미터
    strategies = {
        "SMA최적": lambda chart: run_backtest(
            chart=chart, initial_capital=capital, order_amount=1_000_000,
            short_period=9, long_period=39, use_advanced=True, capital_ratio=1.0,
            stop_loss_pct=20, rsi_period=12, rsi_overbought=80, rsi_oversold=44,
            volume_ma_period=16, obv_ma_period=9,
        ),
        "KAMA최적": lambda chart: run_kama_backtest(
            chart=chart, initial_capital=capital, order_amount=1_000_000,
            er_period=15, fast_period=6, slow_period=32, signal_period=12,
            stop_loss_pct=10, capital_ratio=1.0,
        ),
        "Breakout최적": lambda chart: run_breakout_backtest(
            chart=chart, initial_capital=capital, order_amount=1_000_000,
            upper_period=20, lower_period=15, capital_ratio=1.0,
        ),
        "Bollinger최적": lambda chart: run_bollinger_backtest(
            chart=chart, initial_capital=capital, order_amount=1_000_000,
            period=20, num_std=2.0, max_holding_days=20, capital_ratio=1.0,
        ),
    }

    # 결과 수집
    all_results: dict[str, dict[str, BacktestResult]] = {}
    for name, chart in charts.items():
        all_results[name] = {}
        for strat_name, fn in strategies.items():
            all_results[name][strat_name] = fn(chart)

    # 요약 테이블
    strat_names = list(strategies.keys()) + ["B&H"]

    print(f"{'':>14s}", end="")
    for s in strat_names:
        print(f" | {s:>12s}", end="")
    print()
    print("-" * (14 + len(strat_names) * 15))

    strat_sums = {s: 0.0 for s in strat_names}
    strat_trades = {s: 0 for s in strat_names[:-1]}
    strat_wins = {s: [] for s in strat_names[:-1]}
    strat_mdd = {s: 0.0 for s in strat_names[:-1]}
    strat_sharpe = {s: [] for s in strat_names[:-1]}

    for name in names:
        bnh = all_results[name][list(strategies.keys())[0]].buy_and_hold_pct
        print(f"{name:>14s}", end="")

        row_vals = {}
        for strat_name in list(strategies.keys()):
            r = all_results[name][strat_name]
            val = r.total_return_pct
            row_vals[strat_name] = val
            strat_sums[strat_name] += val
            strat_trades[strat_name] += r.trade_count
            if r.trade_count > 0:
                strat_wins[strat_name].append(r.win_rate)
            strat_mdd[strat_name] = max(strat_mdd[strat_name], r.max_drawdown_pct)
            if r.sharpe_ratio is not None:
                strat_sharpe[strat_name].append(r.sharpe_ratio)
            print(f" | {val:>10.1f}%", end="")

        row_vals["B&H"] = bnh
        strat_sums["B&H"] += bnh
        print(f" | {bnh:>10.1f}%", end="")

        best = max(row_vals, key=row_vals.get)
        print(f"  ← {best}" if best != "B&H" else "")

    n = len(names)
    print("-" * (14 + len(strat_names) * 15))
    print(f"{'평균':>14s}", end="")
    for s in strat_names:
        avg = strat_sums[s] / n
        print(f" | {avg:>10.1f}%", end="")
    print()

    # 상세 지표
    print(f"\n{'='*90}")
    print("전략별 상세 지표")
    print(f"{'='*90}")
    print(f"{'전략':>14s} | {'평균수익률':>10s} | {'총거래':>6s} | {'평균승률':>8s} | {'최악MDD':>8s} | {'Sharpe':>8s}")
    print("-" * 70)
    for s in list(strategies.keys()):
        avg_ret = strat_sums[s] / n
        avg_win = sum(strat_wins[s]) / len(strat_wins[s]) if strat_wins[s] else 0
        avg_sharpe = sum(strat_sharpe[s]) / len(strat_sharpe[s]) if strat_sharpe[s] else 0
        print(f"{s:>14s} | {avg_ret:>9.1f}% | {strat_trades[s]:>6d} | {avg_win:>7.1f}% | {strat_mdd[s]:>7.2f}% | {avg_sharpe:>8.4f}")

    # B&H 대비 초과수익
    print(f"\n{'='*90}")
    print("B&H 대비 초과수익 (Alpha)")
    print(f"{'='*90}")
    bnh_avg = strat_sums["B&H"] / n
    for s in list(strategies.keys()):
        alpha = strat_sums[s] / n - bnh_avg
        print(f"  {s}: {alpha:+.1f}%")

    # 종목별 최적 전략
    print(f"\n{'='*90}")
    print("종목별 최적 전략")
    print(f"{'='*90}")
    for name in names:
        bnh = all_results[name][list(strategies.keys())[0]].buy_and_hold_pct
        best_strat = None
        best_val = bnh
        for strat_name in strategies.keys():
            val = all_results[name][strat_name].total_return_pct
            if val > best_val:
                best_val = val
                best_strat = strat_name
        if best_strat:
            print(f"  {name}: {best_strat} ({best_val:.1f}%) > B&H ({bnh:.1f}%)")
        else:
            print(f"  {name}: B&H ({bnh:.1f}%) — 능동전략 열위")


if __name__ == "__main__":
    main()
