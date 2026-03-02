#!/usr/bin/env python
"""take_profit / split_buy 기능 백테스트 비교 (v2)

채널 기준 목표가(10~25%) + 볼린저/SMA 양 전략 비교
"""

import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta
from app.models import ChartData
from app.trading.backtest import run_bollinger_backtest, run_backtest

SYMBOLS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "035420": "NAVER",
    "005490": "POSCO홀딩스",
    "105560": "KB금융",
    "009540": "HD한국조선해양",
    "034020": "두산에너빌리티",
    "298040": "효성중공업",
    "064350": "현대로템",
    "010120": "LS일렉트릭",
}

# 볼린저 공통 파라미터
BB_BASE = dict(
    initial_capital=10_000_000,
    order_amount=1_000_000,
    period=20,
    num_std=2.0,
    max_holding_days=20,
    max_daily_trades=5,
    volume_ma_period=20,
    trailing_stop_pct=4.0,
    trailing_stop_grace_minutes=30,
    min_profit_pct=1.0,
    stop_loss_pct=5.0,
    min_bandwidth=2.0,
)

# SMA 공통 파라미터
SMA_BASE = dict(
    initial_capital=10_000_000,
    order_amount=1_000_000,
    short_period=7,
    long_period=20,
    use_advanced=True,
    rsi_period=14,
    rsi_overbought=70.0,
    rsi_oversold=30.0,
    volume_ma_period=15,
    obv_ma_period=20,
    stop_loss_pct=5.0,
    max_holding_days=20,
    trailing_stop_pct=4.0,
    min_profit_pct=1.0,
    min_sma_gap_pct=0.1,
    sell_cooldown_bars=5,
)


def fetch_chart(ticker: str, start: str, end: str) -> list[ChartData]:
    import yfinance as yf
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        return []
    if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
        df = df.droplevel(level=1, axis=1)
    return [
        ChartData(
            date=date.strftime("%Y%m%d"),
            open=round(row["Open"]),
            high=round(row["High"]),
            low=round(row["Low"]),
            close=round(row["Close"]),
            volume=round(row["Volume"]),
        )
        for date, row in df.iterrows()
    ]


def run_one(strategy: str, chart: list[ChartData], params: dict):
    """전략별 백테스트 실행"""
    if strategy.startswith("BB"):
        return run_bollinger_backtest(chart=chart, **params)
    else:
        return run_backtest(chart=chart, **params)


def print_section(title: str, strategies: dict, charts: dict):
    """전략 그룹 결과 출력"""
    print(f"\n{'=' * 90}")
    print(f"  {title}")
    print(f"{'=' * 90}")

    results = {}
    for strat_name, (strat_type, params) in strategies.items():
        returns = []
        win_rates = []
        trade_counts = []
        mdds = []
        sharpes = []
        bnh_returns = []
        reason_counts: dict[str, int] = {}
        per_stock: list[dict] = []

        for symbol, chart in charts.items():
            r = run_one(strat_type, chart, params)
            returns.append(r.total_return_pct)
            bnh_returns.append(r.buy_and_hold_pct)
            trade_counts.append(r.trade_count)
            mdds.append(r.max_drawdown_pct)
            if r.trade_count > 0:
                win_rates.append(r.win_rate)
            if r.sharpe_ratio is not None:
                sharpes.append(r.sharpe_ratio)
            for t in r.trades:
                if t.side == "sell":
                    reason_counts[t.reason] = reason_counts.get(t.reason, 0) + 1
            per_stock.append({
                "symbol": symbol,
                "name": SYMBOLS[symbol],
                "return": r.total_return_pct,
                "bnh": r.buy_and_hold_pct,
                "trades": r.trade_count,
                "win_rate": r.win_rate,
                "mdd": r.max_drawdown_pct,
            })

        n = len(returns)
        results[strat_name] = {
            "avg_return": sum(returns) / n,
            "avg_bnh": sum(bnh_returns) / n,
            "avg_win_rate": sum(win_rates) / len(win_rates) if win_rates else 0,
            "total_trades": sum(trade_counts),
            "avg_mdd": sum(mdds) / n,
            "avg_sharpe": sum(sharpes) / len(sharpes) if sharpes else 0,
            "reason_counts": reason_counts,
            "per_stock": per_stock,
        }

    # 요약 테이블
    print(f"\n{'전략':<22} {'수익률':>8} {'B&H':>8} {'승률':>7} {'총매매':>6} {'MDD':>7} {'Sharpe':>8} {'vs기준':>8}")
    print("-" * 90)

    first_key = list(results.keys())[0]
    baseline_ret = results[first_key]["avg_return"]

    for strat_name, r in results.items():
        diff = r["avg_return"] - baseline_ret
        diff_str = f"{diff:+.2f}%" if strat_name != first_key else ""
        print(
            f"{strat_name:<22} "
            f"{r['avg_return']:>+7.2f}% "
            f"{r['avg_bnh']:>+7.2f}% "
            f"{r['avg_win_rate']:>6.1f}% "
            f"{r['total_trades']:>5}건 "
            f"{r['avg_mdd']:>6.2f}% "
            f"{r['avg_sharpe']:>7.4f} "
            f"{diff_str:>8}"
        )

    # 매도 사유
    reasons = ["signal", "trailing_stop", "take_profit", "stop_loss", "max_holding"]
    rl = {"signal": "시그널", "trailing_stop": "트레일링", "take_profit": "목표수익",
          "stop_loss": "손절", "max_holding": "보유한도"}
    print(f"\n{'전략':<22}" + "".join(f" {rl.get(r,r):>8}" for r in reasons))
    print("-" * 90)
    for strat_name, r in results.items():
        rc = r["reason_counts"]
        row = f"{strat_name:<22}"
        for reason in reasons:
            row += f" {rc.get(reason, 0):>8}"
        print(row)

    # 종목별 상세 (최적 전략)
    print(f"\n{'종목':<18}", end="")
    for name in results:
        print(f" {name:>12}", end="")
    print()
    print("-" * 90)

    for i, symbol in enumerate(charts):
        name = SYMBOLS[symbol]
        row = f"{name:<18}"
        for strat_name, r in results.items():
            ps = r["per_stock"][i]
            row += f" {ps['return']:>+11.2f}%"
        print(row)

    return results


def main():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_1y = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    start_2y = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")

    print("=" * 90)
    print("  take_profit / split_buy 백테스트 비교 (v2)")
    print(f"  기간: 1년({start_1y}~) / 2년({start_2y}~)")
    print("=" * 90)

    # 데이터 로드 (2년)
    charts_2y: dict[str, list[ChartData]] = {}
    charts_1y: dict[str, list[ChartData]] = {}
    for symbol, name in SYMBOLS.items():
        ticker = f"{symbol}.KS"
        print(f"  로드: {name}...", end="", flush=True)
        chart = fetch_chart(ticker, start_2y, end_date)
        if len(chart) >= 60:
            charts_2y[symbol] = chart
            # 1년 데이터 슬라이싱
            one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            charts_1y[symbol] = [c for c in chart if c.date >= one_year_ago]
            print(f" 2y={len(chart)}일, 1y={len(charts_1y[symbol])}일")
        else:
            print(f" 스킵 ({len(chart)}일)")

    # ==============================
    # 1. 볼린저 — 목표가 비교 (1년)
    # ==============================
    bb_strategies = {
        "BB 기준선": ("BB", {**BB_BASE}),
        "BB+TP10%": ("BB", {**BB_BASE, "take_profit_pct": 10.0}),
        "BB+TP15%": ("BB", {**BB_BASE, "take_profit_pct": 15.0}),
        "BB+TP20%": ("BB", {**BB_BASE, "take_profit_pct": 20.0}),
        "BB+TP25%": ("BB", {**BB_BASE, "take_profit_pct": 25.0}),
    }
    print_section("볼린저 밴드 — 목표가 레벨 비교 (1년)", bb_strategies, charts_1y)

    # ==============================
    # 2. SMA — 목표가 비교 (1년)
    # ==============================
    sma_strategies = {
        "SMA 기준선": ("SMA", {**SMA_BASE}),
        "SMA+TP10%": ("SMA", {**SMA_BASE, "take_profit_pct": 10.0}),
        "SMA+TP15%": ("SMA", {**SMA_BASE, "take_profit_pct": 15.0}),
        "SMA+TP20%": ("SMA", {**SMA_BASE, "take_profit_pct": 20.0}),
    }
    print_section("SMA 크로스오버 — 목표가 레벨 비교 (1년)", sma_strategies, charts_1y)

    # ==============================
    # 3. 분할매수 조합 (1년)
    # ==============================
    split_strategies = {
        "BB 기준선": ("BB", {**BB_BASE}),
        "BB+분할2": ("BB", {**BB_BASE, "split_buy_count": 2}),
        "BB+분할3": ("BB", {**BB_BASE, "split_buy_count": 3}),
        "BB+TP15%+분할3": ("BB", {**BB_BASE, "take_profit_pct": 15.0, "split_buy_count": 3}),
    }
    print_section("볼린저 — 분할매수 조합 비교 (1년)", split_strategies, charts_1y)

    # ==============================
    # 4. 2년 장기 (시장 순환 포함)
    # ==============================
    long_strategies = {
        "BB 기준선 2Y": ("BB", {**BB_BASE}),
        "BB+TP15% 2Y": ("BB", {**BB_BASE, "take_profit_pct": 15.0}),
        "BB+TP20% 2Y": ("BB", {**BB_BASE, "take_profit_pct": 20.0}),
        "BB+TP15%+분할3 2Y": ("BB", {**BB_BASE, "take_profit_pct": 15.0, "split_buy_count": 3}),
        "SMA 기준선 2Y": ("SMA", {**SMA_BASE}),
        "SMA+TP15% 2Y": ("SMA", {**SMA_BASE, "take_profit_pct": 15.0}),
    }
    print_section("장기 2년 백테스트 (시장 순환 포함)", long_strategies, charts_2y)

    print("\n완료\n")


if __name__ == "__main__":
    main()
