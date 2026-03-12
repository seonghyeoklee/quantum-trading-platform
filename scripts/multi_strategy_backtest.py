#!/usr/bin/env python
"""멀티 전략 백테스트 — 4개 전략을 모든 종목에 대해 실행하고 비교"""

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


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/backtest_config.json"

    with open(config_path) as f:
        config = json.load(f)

    end_date = config.get("end_date") or datetime.now().strftime("%Y%m%d")
    symbols = config["symbols"]
    initial_capital = config["initial_capital"]
    order_amount = config.get("order_amount", 1_000_000)

    # 전략별 파라미터
    sma_params = config.get("sma_params", {})
    bollinger_params = config.get("bollinger_params", {})
    kama_params = config.get("kama_params", {})
    breakout_params = config.get("breakout_params", {})

    # 기본 SMA 파라미터 (하위 호환)
    short_period = sma_params.get("short_period", config.get("short_period", 10))
    long_period = sma_params.get("long_period", config.get("long_period", 40))

    all_results = {}

    for sym in symbols:
        code = sym["code"]
        name = sym["name"]
        ticker = to_yfinance_ticker(code)

        try:
            chart = fetch_chart_from_yfinance(ticker, config["start_date"], end_date)
        except Exception as e:
            print(f"[WARN] {code} {name} 데이터 조회 실패: {e}", file=sys.stderr)
            continue

        if not chart:
            print(f"[WARN] {code} {name} 데이터 없음", file=sys.stderr)
            continue

        stock_results = {}

        # 1) SMA 크로스오버
        stock_results["SMA"] = run_backtest(
            chart=chart,
            initial_capital=initial_capital,
            order_amount=order_amount,
            short_period=short_period,
            long_period=long_period,
            use_advanced=sma_params.get("use_advanced", config.get("use_advanced", True)),
            rsi_period=sma_params.get("rsi_period", config.get("rsi_period", 14)),
            rsi_overbought=sma_params.get("rsi_overbought", config.get("rsi_overbought", 70)),
            rsi_oversold=sma_params.get("rsi_oversold", config.get("rsi_oversold", 30)),
            volume_ma_period=sma_params.get("volume_ma_period", config.get("volume_ma_period", 15)),
            obv_ma_period=sma_params.get("obv_ma_period", config.get("obv_ma_period", 20)),
            stop_loss_pct=sma_params.get("stop_loss_pct", 5.0),
            max_holding_days=sma_params.get("max_holding_days", 20),
            trailing_stop_pct=sma_params.get("trailing_stop_pct", 0.0),
            min_sma_gap_pct=sma_params.get("min_sma_gap_pct", 0.0),
            min_profit_pct=sma_params.get("min_profit_pct", 0.0),
            sell_cooldown_bars=sma_params.get("sell_cooldown_bars", 0),
            take_profit_pct=sma_params.get("take_profit_pct", 0.0),
            split_buy_count=sma_params.get("split_buy_count", 1),
        )

        # 2) 볼린저밴드
        stock_results["Bollinger"] = run_bollinger_backtest(
            chart=chart,
            initial_capital=initial_capital,
            order_amount=order_amount,
            period=bollinger_params.get("period", 20),
            num_std=bollinger_params.get("num_std", 2.0),
            max_holding_days=bollinger_params.get("max_holding_days", 5),
            max_daily_trades=bollinger_params.get("max_daily_trades", 5),
            volume_ma_period=bollinger_params.get("volume_ma_period", None),
            trailing_stop_pct=bollinger_params.get("trailing_stop_pct", 0.0),
            min_profit_pct=bollinger_params.get("min_profit_pct", 0.0),
            stop_loss_pct=bollinger_params.get("stop_loss_pct", 0.0),
            min_bandwidth=bollinger_params.get("min_bandwidth", 0.0),
            take_profit_pct=bollinger_params.get("take_profit_pct", 0.0),
            split_buy_count=bollinger_params.get("split_buy_count", 1),
        )

        # 3) KAMA
        stock_results["KAMA"] = run_kama_backtest(
            chart=chart,
            initial_capital=initial_capital,
            order_amount=order_amount,
            er_period=kama_params.get("er_period", 10),
            fast_period=kama_params.get("fast_period", 2),
            slow_period=kama_params.get("slow_period", 30),
            signal_period=kama_params.get("signal_period", 10),
            stop_loss_pct=kama_params.get("stop_loss_pct", 5.0),
            trailing_stop_pct=kama_params.get("trailing_stop_pct", 0.0),
            take_profit_pct=kama_params.get("take_profit_pct", 0.0),
            max_holding_days=kama_params.get("max_holding_days", 0),
        )

        # 4) 브레이크아웃
        stock_results["Breakout"] = run_breakout_backtest(
            chart=chart,
            initial_capital=initial_capital,
            order_amount=order_amount,
            upper_period=breakout_params.get("upper_period", 20),
            lower_period=breakout_params.get("lower_period", 10),
            stop_loss_pct=breakout_params.get("stop_loss_pct", 5.0),
            trailing_stop_pct=breakout_params.get("trailing_stop_pct", 0.0),
            take_profit_pct=breakout_params.get("take_profit_pct", 0.0),
            max_holding_days=breakout_params.get("max_holding_days", 0),
            volume_filter=breakout_params.get("volume_filter", False),
            volume_ma_period=breakout_params.get("volume_ma_period", 20),
        )

        all_results[name] = stock_results

    # 결과 출력
    print("=" * 100)
    print(f"  멀티 전략 백테스트 결과  |  기간: {config['start_date']} ~ {end_date}  |  종목: {len(all_results)}개")
    print("=" * 100)

    # 전략별 집계
    strategy_names = ["SMA", "Bollinger", "KAMA", "Breakout", "B&H"]
    strategy_totals = {s: {"return": 0, "trades": 0, "wins": 0, "win_count": 0, "mdd": 0, "sharpe_sum": 0, "sharpe_n": 0} for s in strategy_names}

    print(f"\n{'종목':>12s} | {'SMA':>10s} | {'Bollinger':>10s} | {'KAMA':>10s} | {'Breakout':>10s} | {'B&H':>10s} | {'Best':>10s}")
    print("-" * 100)

    for name, results in all_results.items():
        bnh = results["SMA"].buy_and_hold_pct
        row = {"B&H": bnh}
        for strategy_name in ["SMA", "Bollinger", "KAMA", "Breakout"]:
            r = results[strategy_name]
            row[strategy_name] = r.total_return_pct

            strategy_totals[strategy_name]["return"] += r.total_return_pct
            strategy_totals[strategy_name]["trades"] += r.trade_count
            if r.trade_count > 0:
                strategy_totals[strategy_name]["wins"] += r.win_rate
                strategy_totals[strategy_name]["win_count"] += 1
            if r.max_drawdown_pct > strategy_totals[strategy_name]["mdd"]:
                strategy_totals[strategy_name]["mdd"] = r.max_drawdown_pct
            if r.sharpe_ratio is not None:
                strategy_totals[strategy_name]["sharpe_sum"] += r.sharpe_ratio
                strategy_totals[strategy_name]["sharpe_n"] += 1

        strategy_totals["B&H"]["return"] += bnh

        best_strategy = max(row, key=row.get)
        best_val = row[best_strategy]

        parts = []
        for s in ["SMA", "Bollinger", "KAMA", "Breakout", "B&H"]:
            val = row[s]
            marker = " *" if s == best_strategy else "  "
            parts.append(f"{val:>8.2f}%{marker}")

        print(f"{name:>12s} | {'|'.join(parts)} | {best_strategy}")

    n = len(all_results)
    if n > 0:
        print("-" * 100)
        parts = []
        for s in strategy_names:
            avg = strategy_totals[s]["return"] / n
            parts.append(f"{avg:>8.2f}%  ")
        print(f"{'평균':>12s} | {'|'.join(parts)} |")

        print("\n" + "=" * 100)
        print("  전략별 상세 지표")
        print("=" * 100)
        print(f"{'전략':>12s} | {'평균수익률':>10s} | {'총거래':>8s} | {'평균승률':>8s} | {'최악MDD':>8s} | {'평균Sharpe':>10s}")
        print("-" * 70)
        for s in ["SMA", "Bollinger", "KAMA", "Breakout"]:
            t = strategy_totals[s]
            avg_ret = t["return"] / n
            avg_win = t["wins"] / t["win_count"] if t["win_count"] > 0 else 0
            avg_sharpe = t["sharpe_sum"] / t["sharpe_n"] if t["sharpe_n"] > 0 else 0
            print(f"{s:>12s} | {avg_ret:>9.2f}% | {t['trades']:>8d} | {avg_win:>7.1f}% | {t['mdd']:>7.2f}% | {avg_sharpe:>10.4f}")

    # JSON 결과도 저장
    json_output = {
        "period": f"{config['start_date']} ~ {end_date}",
        "stock_count": n,
        "strategy_summary": {},
        "stocks": {},
    }

    for s in ["SMA", "Bollinger", "KAMA", "Breakout"]:
        t = strategy_totals[s]
        json_output["strategy_summary"][s] = {
            "avg_return_pct": round(t["return"] / n, 2) if n > 0 else 0,
            "total_trades": t["trades"],
            "avg_win_rate": round(t["wins"] / t["win_count"], 2) if t["win_count"] > 0 else 0,
            "worst_mdd_pct": round(t["mdd"], 2),
            "avg_sharpe": round(t["sharpe_sum"] / t["sharpe_n"], 4) if t["sharpe_n"] > 0 else None,
        }

    for name, results in all_results.items():
        json_output["stocks"][name] = {
            s: {
                "total_return_pct": results[s].total_return_pct,
                "trade_count": results[s].trade_count,
                "win_rate": results[s].win_rate,
                "max_drawdown_pct": results[s].max_drawdown_pct,
                "sharpe_ratio": results[s].sharpe_ratio,
            }
            for s in ["SMA", "Bollinger", "KAMA", "Breakout"]
        }
        json_output["stocks"][name]["buy_and_hold_pct"] = results["SMA"].buy_and_hold_pct

    with open("/tmp/multi_strategy_result.json", "w") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)

    print(f"\n상세 JSON: /tmp/multi_strategy_result.json")


if __name__ == "__main__":
    main()
