#!/usr/bin/env python
"""그리드 서치 파라미터 최적화 — 4개 전략 × 파라미터 조합 탐색"""

import itertools
import json
import sys
from datetime import datetime

from app.trading.backtest import (
    fetch_chart_from_yfinance,
    run_backtest,
    run_bollinger_backtest,
    run_kama_backtest,
    run_breakout_backtest,
    to_yfinance_ticker,
)


def load_chart_data(config: dict) -> dict[str, list]:
    """종목별 차트 데이터를 한 번에 로드 (캐싱)"""
    end_date = config.get("end_date") or datetime.now().strftime("%Y%m%d")
    charts = {}
    for sym in config["symbols"]:
        code = sym["code"]
        name = sym["name"]
        ticker = to_yfinance_ticker(code)
        try:
            chart = fetch_chart_from_yfinance(ticker, config["start_date"], end_date)
            if chart:
                charts[name] = chart
        except Exception as e:
            print(f"[WARN] {code} {name}: {e}", file=sys.stderr)
    return charts


def evaluate_sma(charts: dict, capital: int, params: dict) -> dict:
    """SMA 전략 평가"""
    returns = []
    for name, chart in charts.items():
        r = run_backtest(
            chart=chart, initial_capital=capital,
            order_amount=params.get("order_amount", 1_000_000),
            short_period=params["short_period"],
            long_period=params["long_period"],
            use_advanced=params.get("use_advanced", True),
            rsi_period=params.get("rsi_period", 14),
            rsi_overbought=params.get("rsi_overbought", 70),
            rsi_oversold=params.get("rsi_oversold", 30),
            volume_ma_period=params.get("volume_ma_period", 15),
            obv_ma_period=params.get("obv_ma_period", 20),
            stop_loss_pct=params.get("stop_loss_pct", 0),
            max_holding_days=params.get("max_holding_days", 0),
            trailing_stop_pct=params.get("trailing_stop_pct", 0),
            capital_ratio=params.get("capital_ratio", 0),
            min_sma_gap_pct=params.get("min_sma_gap_pct", 0),
            min_profit_pct=params.get("min_profit_pct", 0),
            take_profit_pct=params.get("take_profit_pct", 0),
            sell_cooldown_bars=params.get("sell_cooldown_bars", 0),
            split_buy_count=params.get("split_buy_count", 1),
        )
        returns.append(r.total_return_pct)
    return {"avg_return": sum(returns) / len(returns) if returns else 0, "returns": returns}


def evaluate_bollinger(charts: dict, capital: int, params: dict) -> dict:
    """볼린저 전략 평가"""
    returns = []
    for name, chart in charts.items():
        r = run_bollinger_backtest(
            chart=chart, initial_capital=capital,
            order_amount=params.get("order_amount", 1_000_000),
            period=params.get("period", 20),
            num_std=params.get("num_std", 2.0),
            max_holding_days=params.get("max_holding_days", 5),
            trailing_stop_pct=params.get("trailing_stop_pct", 0),
            stop_loss_pct=params.get("stop_loss_pct", 0),
            min_bandwidth=params.get("min_bandwidth", 0),
            take_profit_pct=params.get("take_profit_pct", 0),
            min_profit_pct=params.get("min_profit_pct", 0),
            capital_ratio=params.get("capital_ratio", 0),
            volume_ma_period=params.get("volume_ma_period", None),
            split_buy_count=params.get("split_buy_count", 1),
        )
        returns.append(r.total_return_pct)
    return {"avg_return": sum(returns) / len(returns) if returns else 0, "returns": returns}


def evaluate_kama(charts: dict, capital: int, params: dict) -> dict:
    """KAMA 전략 평가"""
    returns = []
    for name, chart in charts.items():
        r = run_kama_backtest(
            chart=chart, initial_capital=capital,
            order_amount=params.get("order_amount", 1_000_000),
            er_period=params.get("er_period", 10),
            fast_period=params.get("fast_period", 2),
            slow_period=params.get("slow_period", 30),
            signal_period=params.get("signal_period", 10),
            stop_loss_pct=params.get("stop_loss_pct", 0),
            trailing_stop_pct=params.get("trailing_stop_pct", 0),
            take_profit_pct=params.get("take_profit_pct", 0),
            max_holding_days=params.get("max_holding_days", 0),
            capital_ratio=params.get("capital_ratio", 0),
        )
        returns.append(r.total_return_pct)
    return {"avg_return": sum(returns) / len(returns) if returns else 0, "returns": returns}


def evaluate_breakout(charts: dict, capital: int, params: dict) -> dict:
    """브레이크아웃 전략 평가"""
    returns = []
    for name, chart in charts.items():
        r = run_breakout_backtest(
            chart=chart, initial_capital=capital,
            order_amount=params.get("order_amount", 1_000_000),
            upper_period=params.get("upper_period", 20),
            lower_period=params.get("lower_period", 10),
            stop_loss_pct=params.get("stop_loss_pct", 0),
            trailing_stop_pct=params.get("trailing_stop_pct", 0),
            take_profit_pct=params.get("take_profit_pct", 0),
            max_holding_days=params.get("max_holding_days", 0),
            capital_ratio=params.get("capital_ratio", 0),
            volume_filter=params.get("volume_filter", False),
            volume_ma_period=params.get("volume_ma_period", 20),
        )
        returns.append(r.total_return_pct)
    return {"avg_return": sum(returns) / len(returns) if returns else 0, "returns": returns}


def grid_search_sma(charts, capital):
    """SMA 파라미터 그리드 서치"""
    best = {"avg_return": -9999, "params": {}}
    grid = list(itertools.product(
        [5, 7, 10, 15],          # short_period
        [20, 30, 40, 50],        # long_period
        [True, False],           # use_advanced
        [0.0, 3.0, 5.0, 7.0],   # stop_loss_pct
        [0, 15, 30],             # max_holding_days
        [0.0, 2.0, 4.0],        # trailing_stop_pct
        [0.3, 0.5, 0.7, 1.0],   # capital_ratio
    ))
    total = len(grid)
    print(f"\n[SMA] 그리드 서치: {total}개 조합")

    for idx, (short, long_, adv, sl, mhd, ts, cr) in enumerate(grid):
        if short >= long_:
            continue
        params = {
            "short_period": short, "long_period": long_,
            "use_advanced": adv, "stop_loss_pct": sl,
            "max_holding_days": mhd, "trailing_stop_pct": ts,
            "capital_ratio": cr,
        }
        result = evaluate_sma(charts, capital, params)
        if result["avg_return"] > best["avg_return"]:
            best = {"avg_return": result["avg_return"], "params": params, "returns": result["returns"]}
            print(f"  [{idx+1}/{total}] NEW BEST: {result['avg_return']:.2f}% | {params}")

    return best


def grid_search_bollinger(charts, capital):
    """볼린저 파라미터 그리드 서치"""
    best = {"avg_return": -9999, "params": {}}
    grid = list(itertools.product(
        [15, 20, 25, 30],        # period
        [1.5, 2.0, 2.5, 3.0],   # num_std
        [3, 5, 10, 20],          # max_holding_days
        [0.0, 3.0, 5.0],        # stop_loss_pct
        [0.0, 2.0, 4.0],        # trailing_stop_pct
        [0.3, 0.5, 0.7, 1.0],   # capital_ratio
        [0.0, 3.0, 5.0],        # take_profit_pct
    ))
    total = len(grid)
    print(f"\n[Bollinger] 그리드 서치: {total}개 조합")

    for idx, (period, std, mhd, sl, ts, cr, tp) in enumerate(grid):
        params = {
            "period": period, "num_std": std,
            "max_holding_days": mhd, "stop_loss_pct": sl,
            "trailing_stop_pct": ts, "capital_ratio": cr,
            "take_profit_pct": tp,
        }
        result = evaluate_bollinger(charts, capital, params)
        if result["avg_return"] > best["avg_return"]:
            best = {"avg_return": result["avg_return"], "params": params, "returns": result["returns"]}
            print(f"  [{idx+1}/{total}] NEW BEST: {result['avg_return']:.2f}% | {params}")

    return best


def grid_search_kama(charts, capital):
    """KAMA 파라미터 그리드 서치"""
    best = {"avg_return": -9999, "params": {}}
    grid = list(itertools.product(
        [5, 8, 10, 15],          # er_period
        [2, 3, 5],               # fast_period
        [20, 30, 40],            # slow_period
        [5, 8, 10, 15],          # signal_period
        [0.0, 3.0, 5.0, 7.0],   # stop_loss_pct
        [0.0, 2.0, 4.0],        # trailing_stop_pct
        [0, 15, 30],             # max_holding_days
        [0.3, 0.5, 0.7, 1.0],   # capital_ratio
    ))
    total = len(grid)
    print(f"\n[KAMA] 그리드 서치: {total}개 조합")

    for idx, (er, fast, slow, sig, sl, ts, mhd, cr) in enumerate(grid):
        params = {
            "er_period": er, "fast_period": fast,
            "slow_period": slow, "signal_period": sig,
            "stop_loss_pct": sl, "trailing_stop_pct": ts,
            "max_holding_days": mhd, "capital_ratio": cr,
        }
        result = evaluate_kama(charts, capital, params)
        if result["avg_return"] > best["avg_return"]:
            best = {"avg_return": result["avg_return"], "params": params, "returns": result["returns"]}
            print(f"  [{idx+1}/{total}] NEW BEST: {result['avg_return']:.2f}% | {params}")

    return best


def grid_search_breakout(charts, capital):
    """브레이크아웃 파라미터 그리드 서치"""
    best = {"avg_return": -9999, "params": {}}
    grid = list(itertools.product(
        [10, 15, 20, 30, 40],    # upper_period
        [5, 7, 10, 15, 20],      # lower_period
        [0.0, 3.0, 5.0, 7.0],   # stop_loss_pct
        [0.0, 2.0, 4.0],        # trailing_stop_pct
        [0, 15, 30],             # max_holding_days
        [0.3, 0.5, 0.7, 1.0],   # capital_ratio
        [True, False],           # volume_filter
    ))
    total = len(grid)
    print(f"\n[Breakout] 그리드 서치: {total}개 조합")

    for idx, (up, lo, sl, ts, mhd, cr, vf) in enumerate(grid):
        if lo >= up:
            continue
        params = {
            "upper_period": up, "lower_period": lo,
            "stop_loss_pct": sl, "trailing_stop_pct": ts,
            "max_holding_days": mhd, "capital_ratio": cr,
            "volume_filter": vf,
        }
        result = evaluate_breakout(charts, capital, params)
        if result["avg_return"] > best["avg_return"]:
            best = {"avg_return": result["avg_return"], "params": params, "returns": result["returns"]}
            print(f"  [{idx+1}/{total}] NEW BEST: {result['avg_return']:.2f}% | {params}")

    return best


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/backtest_config.json"
    strategy_filter = sys.argv[2] if len(sys.argv) > 2 else "all"

    with open(config_path) as f:
        config = json.load(f)

    capital = config["initial_capital"]

    print("차트 데이터 로딩 중...")
    charts = load_chart_data(config)
    print(f"로딩 완료: {len(charts)}개 종목\n")

    results = {}

    if strategy_filter in ("all", "sma"):
        results["SMA"] = grid_search_sma(charts, capital)
    if strategy_filter in ("all", "bollinger"):
        results["Bollinger"] = grid_search_bollinger(charts, capital)
    if strategy_filter in ("all", "kama"):
        results["KAMA"] = grid_search_kama(charts, capital)
    if strategy_filter in ("all", "breakout"):
        results["Breakout"] = grid_search_breakout(charts, capital)

    print("\n" + "=" * 80)
    print("  최적화 결과 요약")
    print("=" * 80)

    stock_names = list(charts.keys())

    for strategy, best in results.items():
        print(f"\n[{strategy}] 최고 평균 수익률: {best['avg_return']:.2f}%")
        print(f"  파라미터: {json.dumps(best['params'], ensure_ascii=False)}")
        if "returns" in best:
            for i, name in enumerate(stock_names):
                if i < len(best["returns"]):
                    print(f"    {name}: {best['returns'][i]:.2f}%")

    # 결과 저장
    output = {
        "timestamp": datetime.now().isoformat(),
        "period": f"{config['start_date']} ~ {config.get('end_date', 'now')}",
        "stock_count": len(charts),
        "stock_names": stock_names,
        "best_params": {k: {"avg_return": v["avg_return"], "params": v["params"], "per_stock": v.get("returns", [])} for k, v in results.items()},
    }
    out_path = "/tmp/optimize_grid_result.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n결과 저장: {out_path}")


if __name__ == "__main__":
    main()
