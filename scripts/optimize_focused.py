#!/usr/bin/env python
"""집중 파라미터 최적화 — 1차 최적 결과 주변의 핵심 변수만 탐색"""

import itertools
import json
from datetime import datetime

from app.trading.backtest import (
    fetch_chart_from_yfinance,
    run_backtest,
    run_kama_backtest,
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


def evaluate_sma(charts, capital, params):
    returns = []
    for chart in charts.values():
        r = run_backtest(chart=chart, initial_capital=capital, order_amount=1_000_000, **params)
        returns.append(r.total_return_pct)
    return sum(returns) / len(returns), returns


def evaluate_kama(charts, capital, params):
    returns = []
    for chart in charts.values():
        r = run_kama_backtest(chart=chart, initial_capital=capital, order_amount=1_000_000, **params)
        returns.append(r.total_return_pct)
    return sum(returns) / len(returns), returns


def run_grid(name, charts, capital, base_params, search_space, eval_fn):
    """단일 전략 그리드 서치"""
    keys = list(search_space.keys())
    values = list(search_space.values())
    grid = list(itertools.product(*values))
    print(f"\n[{name}] {len(grid)}개 조합 탐색 (기본: {json.dumps(base_params)})")

    best_avg = -9999
    best_params = {}
    best_returns = []

    for idx, combo in enumerate(grid):
        params = {**base_params}
        for i, k in enumerate(keys):
            params[k] = combo[i]

        # 유효성 체크
        if "short_period" in params and "long_period" in params:
            if params["short_period"] >= params["long_period"]:
                continue

        avg, returns = eval_fn(charts, capital, params)
        if avg > best_avg:
            best_avg = avg
            best_params = params.copy()
            best_returns = returns[:]
            worst = min(returns)
            names = list(charts.keys())
            negatives = [(names[i], returns[i]) for i in range(len(returns)) if returns[i] < 0]
            print(f"  [{idx+1}/{len(grid)}] {avg:.2f}% (worst: {worst:.1f}%){' NEG:' + str(len(negatives)) if negatives else ''}")
            changed = {k: combo[i] for i, k in enumerate(keys)}
            print(f"    변경: {changed}")

    return best_avg, best_params, best_returns


def main():
    with open("scripts/backtest_config.json") as f:
        config = json.load(f)

    capital = config["initial_capital"]
    print("차트 데이터 로딩...")
    charts = load_charts(config)
    print(f"{len(charts)}개 종목 로드 완료")

    results = {}
    names = list(charts.keys())

    # ============================================================
    # Phase 1: SMA 미세 조정
    # 기본: short=10, long=40, advanced=True, cr=1.0 → 362%
    # ============================================================
    sma_base = {
        "short_period": 10, "long_period": 40,
        "use_advanced": True, "capital_ratio": 1.0,
        "stop_loss_pct": 0.0, "max_holding_days": 0,
        "trailing_stop_pct": 0.0, "rsi_period": 14,
        "rsi_overbought": 70.0, "rsi_oversold": 30.0,
        "volume_ma_period": 15, "obv_ma_period": 20,
        "min_sma_gap_pct": 0.0, "min_profit_pct": 0.0,
        "take_profit_pct": 0.0, "sell_cooldown_bars": 0,
        "split_buy_count": 1,
    }

    # Step 1: MA 기간 최적화
    avg, params, rets = run_grid("SMA-MA기간", charts, capital, sma_base, {
        "short_period": [7, 8, 9, 10, 11, 12, 13, 15],
        "long_period": [30, 35, 38, 40, 42, 45, 50, 55, 60],
    }, evaluate_sma)
    sma_base.update({"short_period": params["short_period"], "long_period": params["long_period"]})
    print(f"  → MA기간 최적: short={params['short_period']}, long={params['long_period']} → {avg:.2f}%")

    # Step 2: Advanced 필터 + RSI 파라미터
    avg, params, rets = run_grid("SMA-필터", charts, capital, sma_base, {
        "use_advanced": [True, False],
        "rsi_overbought": [65, 70, 75, 80, 85],
        "rsi_oversold": [20, 25, 30, 35],
    }, evaluate_sma)
    sma_base.update({
        "use_advanced": params["use_advanced"],
        "rsi_overbought": params["rsi_overbought"],
        "rsi_oversold": params["rsi_oversold"],
    })
    print(f"  → 필터 최적: adv={params['use_advanced']}, RSI({params['rsi_overbought']}/{params['rsi_oversold']}) → {avg:.2f}%")

    # Step 3: 리스크 관리
    avg, params, rets = run_grid("SMA-리스크", charts, capital, sma_base, {
        "stop_loss_pct": [0.0, 3.0, 5.0, 7.0, 10.0, 15.0],
        "trailing_stop_pct": [0.0, 2.0, 3.0, 5.0, 8.0],
        "take_profit_pct": [0.0, 5.0, 10.0, 15.0, 20.0, 30.0],
        "max_holding_days": [0, 10, 20, 30, 50],
    }, evaluate_sma)
    sma_base.update({
        "stop_loss_pct": params["stop_loss_pct"],
        "trailing_stop_pct": params["trailing_stop_pct"],
        "take_profit_pct": params["take_profit_pct"],
        "max_holding_days": params["max_holding_days"],
    })
    print(f"  → 리스크 최적: SL={params['stop_loss_pct']}%, TS={params['trailing_stop_pct']}%, TP={params['take_profit_pct']}%, MHD={params['max_holding_days']} → {avg:.2f}%")

    # Step 4: 갭 필터 + 쿨다운
    avg, params, rets = run_grid("SMA-미세", charts, capital, sma_base, {
        "min_sma_gap_pct": [0.0, 0.05, 0.1, 0.2, 0.3, 0.5],
        "min_profit_pct": [0.0, 0.3, 0.5, 1.0],
        "sell_cooldown_bars": [0, 3, 5, 10],
        "volume_ma_period": [10, 15, 20, 25],
        "obv_ma_period": [10, 15, 20, 25],
    }, evaluate_sma)
    sma_best_avg = avg
    sma_best_params = params
    sma_best_returns = rets
    results["SMA"] = {"avg": avg, "params": params, "returns": rets}

    print(f"\n{'='*80}")
    print(f"[SMA 최종] {avg:.2f}%")
    print(f"  파라미터: {json.dumps(params)}")
    for i, n in enumerate(names):
        if i < len(rets):
            print(f"    {n}: {rets[i]:.2f}%")

    # ============================================================
    # Phase 2: KAMA 미세 조정
    # 기본: er=15, fast=5, slow=30, signal=10, cr=1.0 → 320.78%
    # ============================================================
    kama_base = {
        "er_period": 15, "fast_period": 5, "slow_period": 30,
        "signal_period": 10, "stop_loss_pct": 0.0,
        "trailing_stop_pct": 0.0, "take_profit_pct": 0.0,
        "max_holding_days": 0, "capital_ratio": 1.0,
    }

    # Step 1: KAMA 핵심 파라미터
    avg, params, rets = run_grid("KAMA-핵심", charts, capital, kama_base, {
        "er_period": [10, 12, 14, 15, 16, 18, 20],
        "fast_period": [2, 3, 4, 5, 6, 7],
        "slow_period": [25, 28, 30, 32, 35, 40],
        "signal_period": [5, 8, 10, 12, 15],
    }, evaluate_kama)
    kama_base.update({
        "er_period": params["er_period"],
        "fast_period": params["fast_period"],
        "slow_period": params["slow_period"],
        "signal_period": params["signal_period"],
    })
    print(f"  → KAMA 핵심 최적: er={params['er_period']}, fast={params['fast_period']}, slow={params['slow_period']}, sig={params['signal_period']} → {avg:.2f}%")

    # Step 2: KAMA 리스크
    avg, params, rets = run_grid("KAMA-리스크", charts, capital, kama_base, {
        "stop_loss_pct": [0.0, 3.0, 5.0, 7.0, 10.0, 15.0],
        "trailing_stop_pct": [0.0, 2.0, 3.0, 5.0, 8.0],
        "take_profit_pct": [0.0, 5.0, 10.0, 15.0, 20.0, 30.0],
        "max_holding_days": [0, 10, 20, 30, 50],
    }, evaluate_kama)
    results["KAMA"] = {"avg": avg, "params": params, "returns": rets}

    print(f"\n{'='*80}")
    print(f"[KAMA 최종] {avg:.2f}%")
    print(f"  파라미터: {json.dumps(params)}")
    for i, n in enumerate(names):
        if i < len(rets):
            print(f"    {n}: {rets[i]:.2f}%")

    # ============================================================
    # 최종 비교
    # ============================================================
    print(f"\n{'='*80}")
    print("최종 비교")
    print(f"{'='*80}")
    for strategy, data in sorted(results.items(), key=lambda x: -x[1]["avg"]):
        print(f"\n[{strategy}] 평균 수익률: {data['avg']:.2f}%")
        print(f"  파라미터: {json.dumps(data['params'], indent=4)}")

    # 결과 저장
    output = {
        "timestamp": datetime.now().isoformat(),
        "results": {k: {"avg_return": v["avg"], "params": v["params"], "per_stock": v["returns"]} for k, v in results.items()},
    }
    with open("/tmp/optimize_focused_result.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n결과 저장: /tmp/optimize_focused_result.json")


if __name__ == "__main__":
    main()
