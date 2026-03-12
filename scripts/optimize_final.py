#!/usr/bin/env python
"""최종 SMA 최적화 — 단계별 단일 변수 Hill Climbing"""

import json
from datetime import datetime

from app.trading.backtest import (
    fetch_chart_from_yfinance,
    run_backtest,
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


def evaluate(charts, capital, params):
    returns = []
    for chart in charts.values():
        r = run_backtest(chart=chart, initial_capital=capital, order_amount=1_000_000, **params)
        returns.append(r.total_return_pct)
    avg = sum(returns) / len(returns)
    return avg, returns


def hill_climb_param(charts, capital, base_params, param_name, values, names):
    """단일 파라미터 hill climbing"""
    best_avg = -9999
    best_val = base_params.get(param_name)
    best_returns = []

    for val in values:
        params = {**base_params, param_name: val}
        if "short_period" in params and "long_period" in params:
            if params["short_period"] >= params["long_period"]:
                continue
        avg, returns = evaluate(charts, capital, params)
        if avg > best_avg:
            best_avg = avg
            best_val = val
            best_returns = returns

    return best_val, best_avg, best_returns


def main():
    with open("scripts/backtest_config.json") as f:
        config = json.load(f)

    capital = config["initial_capital"]
    print("차트 데이터 로딩...")
    charts = load_charts(config)
    names = list(charts.keys())
    print(f"{len(charts)}개 종목 로드 완료\n")

    # 2차 최적: 471.39%
    params = {
        "short_period": 11, "long_period": 38,
        "use_advanced": True, "capital_ratio": 1.0,
        "stop_loss_pct": 0.0, "max_holding_days": 0,
        "trailing_stop_pct": 0.0, "rsi_period": 14,
        "rsi_overbought": 80, "rsi_oversold": 35,
        "volume_ma_period": 15, "obv_ma_period": 20,
        "min_sma_gap_pct": 0.0, "min_profit_pct": 0.0,
        "take_profit_pct": 0.0, "sell_cooldown_bars": 0,
        "split_buy_count": 1,
    }

    avg, rets = evaluate(charts, capital, params)
    print(f"시작점: {avg:.2f}%\n")

    # Hill climbing: 각 파라미터를 순차적으로 최적화, 수렴할 때까지 반복
    search_space = {
        "short_period": list(range(5, 20)),
        "long_period": list(range(25, 60)),
        "rsi_period": [10, 12, 14, 16, 18, 20],
        "rsi_overbought": list(range(65, 90)),
        "rsi_oversold": list(range(20, 45)),
        "volume_ma_period": list(range(5, 30)),
        "obv_ma_period": list(range(5, 30)),
        "capital_ratio": [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0],
        "stop_loss_pct": [0, 3, 5, 7, 10, 15, 20],
        "trailing_stop_pct": [0, 2, 3, 4, 5, 7, 10],
        "take_profit_pct": [0, 5, 8, 10, 15, 20, 25, 30],
        "max_holding_days": [0, 5, 10, 15, 20, 30, 50],
        "min_sma_gap_pct": [0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5],
        "min_profit_pct": [0, 0.2, 0.3, 0.5, 1.0],
        "sell_cooldown_bars": [0, 2, 3, 5, 7, 10],
        "split_buy_count": [1, 2, 3],
    }

    for iteration in range(5):
        improved = False
        print(f"\n=== Round {iteration + 1} ===")

        for param_name, values in search_space.items():
            old_val = params[param_name]
            best_val, best_avg, best_returns = hill_climb_param(
                charts, capital, params, param_name, values, names
            )

            if best_avg > avg + 0.01:  # 의미 있는 개선만 적용
                params[param_name] = best_val
                avg = best_avg
                rets = best_returns
                improved = True
                worst = min(rets)
                negatives = sum(1 for r in rets if r < 0)
                print(f"  {param_name}: {old_val} → {best_val} → {avg:.2f}% (worst: {worst:.1f}%, neg: {negatives})")

        if not improved:
            print("  수렴 — 더 이상 개선 없음")
            break

    print(f"\n{'='*80}")
    print(f"최종 결과: {avg:.2f}%")
    print(f"파라미터: {json.dumps(params, indent=2)}")
    for i, n in enumerate(names):
        if i < len(rets):
            marker = " ★" if rets[i] > 100 else (" ▼" if rets[i] < 0 else "")
            print(f"  {n}: {rets[i]:.2f}%{marker}")

    with open("/tmp/sma_final_result.json", "w") as f:
        json.dump({
            "avg_return": avg,
            "params": params,
            "per_stock": {names[i]: rets[i] for i in range(min(len(names), len(rets)))},
        }, f, indent=2, ensure_ascii=False)
    print(f"\n저장: /tmp/sma_final_result.json")


if __name__ == "__main__":
    main()
