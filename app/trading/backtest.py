"""백테스트 엔진 — yfinance 데이터로 전략 시뮬레이션"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.models import ChartData, SignalType
from app.trading.strategy import compute_obv, compute_rsi, compute_sma


def to_yfinance_ticker(symbol: str) -> str:
    """KIS 종목코드 → yfinance 티커 ("005930" → "005930.KS")"""
    return f"{symbol}.KS"


def fetch_chart_from_yfinance(ticker: str, start: str, end: str) -> list[ChartData]:
    """yfinance DataFrame → list[ChartData] 변환.

    Args:
        ticker: yfinance 티커 (e.g. "005930.KS")
        start: 시작일 "YYYYMMDD"
        end: 종료일 "YYYYMMDD" (inclusive)
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError(
            "yfinance 패키지가 필요합니다. 설치: uv sync --extra backtest"
        )

    start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
    # yfinance end는 exclusive이므로 +1일
    end_dt = datetime.strptime(end, "%Y%m%d") + timedelta(days=1)
    end_fmt = end_dt.strftime("%Y-%m-%d")

    df = yf.download(ticker, start=start_fmt, end=end_fmt, progress=False)
    if df.empty:
        return []

    # yfinance MultiIndex 처리 (단일 티커도 MultiIndex 반환 가능)
    if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
        df = df.droplevel(level=1, axis=1)

    result: list[ChartData] = []
    for date, row in df.iterrows():
        result.append(
            ChartData(
                date=date.strftime("%Y%m%d"),
                open=round(row["Open"]),
                high=round(row["High"]),
                low=round(row["Low"]),
                close=round(row["Close"]),
                volume=round(row["Volume"]),
            )
        )
    return result


@dataclass
class Trade:
    date: str
    side: str  # "buy" / "sell"
    price: int
    quantity: int


@dataclass
class BacktestResult:
    total_return_pct: float
    buy_and_hold_pct: float
    trade_count: int
    win_rate: float
    max_drawdown_pct: float
    sharpe_ratio: float | None
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


def _crossover_signal(
    today_short: float | None,
    today_long: float | None,
    yesterday_short: float | None,
    yesterday_long: float | None,
) -> SignalType:
    """SMA 크로스오버 시그널 판단 (evaluate_signal과 동일 로직)."""
    if any(v is None for v in [today_short, today_long, yesterday_short, yesterday_long]):
        return SignalType.HOLD
    if yesterday_short <= yesterday_long and today_short > today_long:
        return SignalType.BUY
    if yesterday_short >= yesterday_long and today_short < today_long:
        return SignalType.SELL
    return SignalType.HOLD


def run_backtest(
    chart: list[ChartData],
    initial_capital: int = 10_000_000,
    order_amount: int = 500_000,
    short_period: int = 5,
    long_period: int = 20,
    use_advanced: bool = False,
    rsi_period: int = 14,
    rsi_overbought: float = 70.0,
    rsi_oversold: float = 30.0,
    volume_ma_period: int = 20,
    obv_ma_period: int = 20,
) -> BacktestResult:
    """과거 차트 데이터로 전략 시뮬레이션."""
    if len(chart) < long_period + 1:
        return BacktestResult(
            total_return_pct=0.0,
            buy_and_hold_pct=0.0,
            trade_count=0,
            win_rate=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=None,
        )

    # 지표를 한 번에 미리 계산 — O(n)
    closes = [float(c.close) for c in chart]
    short_sma = compute_sma(closes, short_period)
    long_sma = compute_sma(closes, long_period)

    if use_advanced:
        rsi_values = compute_rsi(closes, rsi_period)
        volumes = [float(c.volume) for c in chart]
        vol_sma = compute_sma(volumes, volume_ma_period)
        obv_values = compute_obv(closes, volumes)
        obv_sma = compute_sma(obv_values, obv_ma_period)

    cash = float(initial_capital)
    holding_qty = 0
    holding_avg_price = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = []
    completed_trades: list[float] = []  # 매수→매도 페어별 손익률

    for i in range(len(chart)):
        close = chart[i].close

        if i >= long_period:
            # SMA 크로스오버 시그널
            signal = _crossover_signal(
                short_sma[i], long_sma[i],
                short_sma[i - 1], long_sma[i - 1],
            )

            # Advanced: RSI + 거래량 필터
            if use_advanced and signal != SignalType.HOLD:
                rsi = rsi_values[i]
                if rsi is not None:
                    if signal == SignalType.BUY and rsi > rsi_overbought:
                        signal = SignalType.HOLD
                    elif signal == SignalType.SELL and rsi < rsi_oversold:
                        signal = SignalType.HOLD

                if signal != SignalType.HOLD:
                    v_sma = vol_sma[i]
                    vol_confirmed = v_sma is not None and v_sma > 0 and volumes[i] > v_sma
                    if not vol_confirmed:
                        signal = SignalType.HOLD

                # OBV 필터
                if signal != SignalType.HOLD:
                    o_sma = obv_sma[i]
                    if o_sma is not None:
                        obv_above = obv_values[i] > o_sma
                        if signal == SignalType.BUY and not obv_above:
                            signal = SignalType.HOLD
                        elif signal == SignalType.SELL and obv_above:
                            signal = SignalType.HOLD

            # 주문 실행
            if signal == SignalType.BUY and holding_qty == 0:
                qty = order_amount // close
                if qty > 0 and cash >= qty * close:
                    cash -= qty * close
                    holding_qty = qty
                    holding_avg_price = float(close)
                    trades.append(Trade(date=chart[i].date, side="buy", price=close, quantity=qty))

            elif signal == SignalType.SELL and holding_qty > 0:
                cash += holding_qty * close
                pnl_pct = (close - holding_avg_price) / holding_avg_price * 100
                completed_trades.append(pnl_pct)
                trades.append(Trade(date=chart[i].date, side="sell", price=close, quantity=holding_qty))
                holding_qty = 0
                holding_avg_price = 0.0

        # 일별 자산 = 현금 + 보유주식 평가액
        equity = cash + holding_qty * close
        equity_curve.append(equity)

    # 메트릭 계산
    final_equity = equity_curve[-1] if equity_curve else float(initial_capital)
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100

    first_close = chart[0].close
    last_close = chart[-1].close
    buy_and_hold_pct = (last_close - first_close) / first_close * 100

    win_count = sum(1 for pnl in completed_trades if pnl > 0)
    win_rate = (win_count / len(completed_trades) * 100) if completed_trades else 0.0

    max_drawdown_pct = _calc_max_drawdown(equity_curve)
    sharpe_ratio = _calc_sharpe_ratio(equity_curve)

    return BacktestResult(
        total_return_pct=round(total_return_pct, 2),
        buy_and_hold_pct=round(buy_and_hold_pct, 2),
        trade_count=len(trades),
        win_rate=round(win_rate, 2),
        max_drawdown_pct=round(max_drawdown_pct, 2),
        sharpe_ratio=round(sharpe_ratio, 4) if sharpe_ratio is not None else None,
        trades=trades,
        equity_curve=equity_curve,
    )


def _calc_max_drawdown(equity_curve: list[float]) -> float:
    """최대 낙폭(MDD) 계산. max((peak - trough) / peak) * 100"""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _calc_sharpe_ratio(equity_curve: list[float]) -> float | None:
    """일간 수익률 기반 연율화 Sharpe ratio. mean / std * sqrt(252)"""
    if len(equity_curve) < 3:
        return None
    daily_returns = [
        (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
        for i in range(1, len(equity_curve))
    ]
    mean_ret = sum(daily_returns) / len(daily_returns)
    variance = sum((r - mean_ret) ** 2 for r in daily_returns) / len(daily_returns)
    std_ret = math.sqrt(variance)
    if std_ret == 0:
        return None
    return mean_ret / std_ret * math.sqrt(252)
