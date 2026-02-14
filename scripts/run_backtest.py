#!/usr/bin/env python
"""포트폴리오 백테스트 CLI — 다종목 동일 파라미터 테스트, JSON 결과 출력"""

import json
import sys
from datetime import datetime

from app.trading.backtest import fetch_chart_from_yfinance, run_backtest, to_yfinance_ticker


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "scripts/backtest_config.json"

    with open(config_path) as f:
        config = json.load(f)

    end_date = config.get("end_date") or datetime.now().strftime("%Y%m%d")
    symbols = config["symbols"]  # [{"code": "005930", "name": "삼성전자", "sector": "..."}]

    params = {
        "initial_capital": config["initial_capital"],
        "order_amount": config["order_amount"],
        "short_period": config["short_period"],
        "long_period": config["long_period"],
        "use_advanced": config["use_advanced"],
        "rsi_period": config["rsi_period"],
        "rsi_overbought": config["rsi_overbought"],
        "rsi_oversold": config["rsi_oversold"],
        "volume_ma_period": config["volume_ma_period"],
        "obv_ma_period": config.get("obv_ma_period", 20),
    }

    stock_results = []
    total_return = 0.0
    total_bnh = 0.0
    total_trades = 0
    total_mdd = 0.0
    sharpe_sum = 0.0
    sharpe_count = 0
    win_sum = 0.0
    win_count = 0

    for sym in symbols:
        code = sym["code"]
        name = sym["name"]
        sector = sym["sector"]
        ticker = to_yfinance_ticker(code)

        try:
            chart = fetch_chart_from_yfinance(ticker, config["start_date"], end_date)
        except Exception as e:
            print(f"[WARN] {code} {name} 데이터 조회 실패: {e}", file=sys.stderr)
            continue

        if not chart:
            print(f"[WARN] {code} {name} 데이터 없음", file=sys.stderr)
            continue

        result = run_backtest(chart=chart, **params)

        sr = {
            "code": code,
            "name": name,
            "sector": sector,
            "data_points": len(chart),
            "total_return_pct": result.total_return_pct,
            "buy_and_hold_pct": result.buy_and_hold_pct,
            "trade_count": result.trade_count,
            "win_rate": result.win_rate,
            "max_drawdown_pct": result.max_drawdown_pct,
            "sharpe_ratio": result.sharpe_ratio,
            "trades": [
                {"date": t.date, "side": t.side, "price": t.price, "qty": t.quantity}
                for t in result.trades
            ],
        }
        stock_results.append(sr)

        total_return += result.total_return_pct
        total_bnh += result.buy_and_hold_pct
        total_trades += result.trade_count
        if result.max_drawdown_pct > total_mdd:
            total_mdd = result.max_drawdown_pct
        if result.sharpe_ratio is not None:
            sharpe_sum += result.sharpe_ratio
            sharpe_count += 1
        if result.trade_count > 0:
            win_sum += result.win_rate
            win_count += 1

    n = len(stock_results)
    if n == 0:
        print(json.dumps({"error": "유효한 종목 데이터 없음"}), file=sys.stderr)
        sys.exit(1)

    output = {
        "period": f"{config['start_date']} ~ {end_date}",
        "stock_count": n,
        "params": {
            "short_period": params["short_period"],
            "long_period": params["long_period"],
            "use_advanced": params["use_advanced"],
            "rsi_period": params["rsi_period"],
            "rsi_overbought": params["rsi_overbought"],
            "rsi_oversold": params["rsi_oversold"],
            "volume_ma_period": params["volume_ma_period"],
            "obv_ma_period": params["obv_ma_period"],
            "order_amount": params["order_amount"],
        },
        "portfolio_summary": {
            "avg_return_pct": round(total_return / n, 2),
            "avg_buy_and_hold_pct": round(total_bnh / n, 2),
            "total_trades": total_trades,
            "avg_win_rate": round(win_sum / win_count, 2) if win_count > 0 else 0.0,
            "worst_mdd_pct": round(total_mdd, 2),
            "avg_sharpe": round(sharpe_sum / sharpe_count, 4) if sharpe_count > 0 else None,
        },
        "stocks": stock_results,
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
