"""백테스트 엔진 — yfinance 데이터로 전략 시뮬레이션"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.models import ChartData, SignalType
from app.trading.regime import MarketRegime, REGIME_KR, segment_by_regime
from app.trading.strategy import compute_bollinger_bands, compute_obv, compute_rsi, compute_sma


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
    reason: str = ""  # "signal" / "stop_loss" / "max_holding"


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
    stop_loss_pct: float = 0.0,
    max_holding_days: int = 0,
    volume_filter_basic: bool = False,
    capital_ratio: float = 0.0,
    trailing_stop_pct: float = 0.0,
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

    volumes: list[float] = []
    vol_sma: list[float | None] = []

    if use_advanced or volume_filter_basic:
        volumes = [float(c.volume) for c in chart]
        vol_sma = compute_sma(volumes, volume_ma_period)

    if use_advanced:
        rsi_values = compute_rsi(closes, rsi_period)
        obv_values = compute_obv(closes, volumes)
        obv_sma = compute_sma(obv_values, obv_ma_period)

    cash = float(initial_capital)
    holding_qty = 0
    holding_avg_price = 0.0
    holding_since: int | None = None
    holding_peak_price: float = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = []
    completed_trades: list[float] = []  # 매수→매도 페어별 손익률

    for i in range(len(chart)):
        close = chart[i].close
        forced_exit = False

        # 리스크 체크 (시그널 평가 전에 실행)
        if holding_qty > 0:
            # 고점 갱신
            holding_peak_price = max(holding_peak_price, float(close))

            # 0) trailing stop (최우선)
            if not forced_exit and trailing_stop_pct > 0 and holding_peak_price > 0:
                drop_pct = (holding_peak_price - close) / holding_peak_price * 100
                if drop_pct >= trailing_stop_pct:
                    cash += holding_qty * close
                    pnl_pct = (close - holding_avg_price) / holding_avg_price * 100
                    completed_trades.append(pnl_pct)
                    trades.append(Trade(date=chart[i].date, side="sell", price=close, quantity=holding_qty, reason="trailing_stop"))
                    holding_qty = 0
                    holding_avg_price = 0.0
                    holding_since = None
                    holding_peak_price = 0.0
                    forced_exit = True

            # 1) stop-loss
            if not forced_exit and stop_loss_pct > 0:
                loss_pct = (holding_avg_price - close) / holding_avg_price * 100
                if loss_pct >= stop_loss_pct:
                    cash += holding_qty * close
                    pnl_pct = (close - holding_avg_price) / holding_avg_price * 100
                    completed_trades.append(pnl_pct)
                    trades.append(Trade(date=chart[i].date, side="sell", price=close, quantity=holding_qty, reason="stop_loss"))
                    holding_qty = 0
                    holding_avg_price = 0.0
                    holding_since = None
                    holding_peak_price = 0.0
                    forced_exit = True

            # 2) max_holding
            if not forced_exit and max_holding_days > 0 and holding_since is not None:
                if i - holding_since >= max_holding_days:
                    cash += holding_qty * close
                    pnl_pct = (close - holding_avg_price) / holding_avg_price * 100
                    completed_trades.append(pnl_pct)
                    trades.append(Trade(date=chart[i].date, side="sell", price=close, quantity=holding_qty, reason="max_holding"))
                    holding_qty = 0
                    holding_avg_price = 0.0
                    holding_since = None
                    holding_peak_price = 0.0
                    forced_exit = True

        if not forced_exit and i >= long_period:
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

            # 기본 모드 거래량 필터 (BUY에만 적용)
            if volume_filter_basic and not use_advanced and signal == SignalType.BUY:
                v_sma = vol_sma[i]
                vol_confirmed = v_sma is not None and v_sma > 0 and volumes[i] > v_sma
                if not vol_confirmed:
                    signal = SignalType.HOLD

            # 주문 실행
            if signal == SignalType.BUY and holding_qty == 0:
                if capital_ratio > 0:
                    effective_amount = int(cash * capital_ratio)
                else:
                    effective_amount = order_amount
                qty = effective_amount // close
                if qty > 0 and cash >= qty * close:
                    cash -= qty * close
                    holding_qty = qty
                    holding_avg_price = float(close)
                    holding_since = i
                    holding_peak_price = float(close)
                    trades.append(Trade(date=chart[i].date, side="buy", price=close, quantity=qty, reason="signal"))

            elif signal == SignalType.SELL and holding_qty > 0:
                cash += holding_qty * close
                pnl_pct = (close - holding_avg_price) / holding_avg_price * 100
                completed_trades.append(pnl_pct)
                trades.append(Trade(date=chart[i].date, side="sell", price=close, quantity=holding_qty, reason="signal"))
                holding_qty = 0
                holding_avg_price = 0.0
                holding_since = None
                holding_peak_price = 0.0

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


def _parse_hhmm(date_str: str) -> int | None:
    """날짜 문자열에서 HHMM 정수 추출. 분봉 "YYYY-MM-DD HH:MM" → 정수, 일봉이면 None."""
    if " " in date_str and len(date_str) >= 16:
        # "2026-02-05 09:30" → 930
        return int(date_str[11:13]) * 100 + int(date_str[14:16])
    return None


def _parse_date_key(date_str: str) -> str:
    """날짜 문자열에서 날짜 부분만 추출 (일일 카운터용)."""
    if " " in date_str:
        return date_str.split(" ")[0]
    return date_str


def run_bollinger_backtest(
    chart: list[ChartData],
    initial_capital: int = 10_000_000,
    order_amount: int = 1_000_000,
    period: int = 20,
    num_std: float = 2.0,
    max_holding_days: int = 5,
    max_daily_trades: int = 5,
    # 장중 제약 (분봉용, None이면 비활성)
    force_close_minute: int | None = None,
    no_new_buy_minute: int | None = None,
    active_windows: list[tuple[int, int]] | None = None,
    target_order_amount: int | None = None,
    min_quantity: int = 1,
    max_quantity: int = 50,
    # 거래량 필터 (None이면 비활성)
    volume_ma_period: int | None = None,
    capital_ratio: float = 0.0,
    trailing_stop_pct: float = 0.0,
) -> BacktestResult:
    """볼린저밴드 반전 전략 백테스트.

    - BUY: prev_close <= prev_lower AND curr_close > lower (하단 반등)
    - SELL: curr_close >= upper (상단 도달) OR 보유기간 >= max_holding_days (강제 청산)

    장중 제약 (분봉 데이터 전용):
    - force_close_minute: 해당 HHMM 이후 보유분 강제 매도 (e.g. 1510)
    - no_new_buy_minute: 해당 HHMM 이후 신규 매수 금지 (e.g. 1500)
    - active_windows: 매매 허용 시간대 리스트 (e.g. [(930,1100),(1400,1500)])
    - target_order_amount: 동적 수량 계산 (target / 현재가, min~max 범위)
    """
    if len(chart) < period + 1:
        return BacktestResult(
            total_return_pct=0.0,
            buy_and_hold_pct=0.0,
            trade_count=0,
            win_rate=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=None,
        )

    closes = [float(c.close) for c in chart]
    bands = compute_bollinger_bands(closes, period, num_std)

    # 거래량 SMA (필터 활성 시)
    volumes = [float(c.volume) for c in chart]
    vol_sma = compute_sma(volumes, volume_ma_period) if volume_ma_period is not None else None

    cash = float(initial_capital)
    holding_qty = 0
    holding_avg_price = 0.0
    holding_since: int | None = None
    holding_peak_price: float = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = []
    completed_trades: list[float] = []

    daily_buy_count: dict[str, int] = {}

    def _in_active_window(hhmm: int) -> bool:
        if active_windows is None:
            return True
        return any(start <= hhmm < end for start, end in active_windows)

    def _do_sell(i: int, close: int, date: str, reason: str = "") -> None:
        nonlocal cash, holding_qty, holding_avg_price, holding_since, holding_peak_price
        cash += holding_qty * close
        pnl_pct = (close - holding_avg_price) / holding_avg_price * 100
        completed_trades.append(pnl_pct)
        trades.append(Trade(date=date, side="sell", price=close, quantity=holding_qty, reason=reason))
        holding_qty = 0
        holding_avg_price = 0.0
        holding_since = None
        holding_peak_price = 0.0

    for i in range(len(chart)):
        close = chart[i].close
        date = chart[i].date
        hhmm = _parse_hhmm(date)
        day_key = _parse_date_key(date)

        # 장 마감 강제 청산 (분봉 전용)
        if hhmm is not None and force_close_minute is not None:
            if hhmm >= force_close_minute and holding_qty > 0:
                _do_sell(i, close, date, reason="force_close")
                equity_curve.append(cash + holding_qty * close)
                continue

        # 보유 중 고점 갱신
        if holding_qty > 0:
            holding_peak_price = max(holding_peak_price, float(close))

        # 트레일링 스탑 (밴드 평가 전에 우선 처리)
        if holding_qty > 0 and trailing_stop_pct > 0 and holding_peak_price > 0:
            drop_pct = (holding_peak_price - close) / holding_peak_price * 100
            if drop_pct >= trailing_stop_pct:
                _do_sell(i, close, date, reason="trailing_stop")
                equity_curve.append(cash + holding_qty * close)
                continue

        if i >= period:
            upper, middle, lower = bands[i]
            _, _, prev_lower = bands[i - 1]

            if upper is not None and lower is not None and prev_lower is not None and upper > lower:
                prev_close = closes[i - 1]

                # 활성 시간대 체크 (분봉 전용)
                in_window = hhmm is None or _in_active_window(hhmm)

                # SELL: 상단 도달 또는 보유기간 초과 (시간대 무관)
                if holding_qty > 0:
                    days_held = i - holding_since if holding_since is not None else 0
                    if closes[i] >= upper:
                        _do_sell(i, close, date, reason="signal")
                    elif days_held >= max_holding_days:
                        _do_sell(i, close, date, reason="max_holding")

                # BUY: 하단 반등 (활성 시간대 + 매수 금지 시간 + 거래량 필터)
                if holding_qty == 0 and in_window:
                    buy_blocked = (
                        hhmm is not None
                        and no_new_buy_minute is not None
                        and hhmm >= no_new_buy_minute
                    )
                    # 거래량 필터: 현재 거래량 > 거래량 SMA
                    if not buy_blocked and vol_sma is not None:
                        v = vol_sma[i]
                        if v is None or v <= 0 or volumes[i] <= v:
                            buy_blocked = True
                    if not buy_blocked and prev_close <= prev_lower and closes[i] > lower:
                        today_buys = daily_buy_count.get(day_key, 0)
                        if today_buys < max_daily_trades:
                            # 자본 활용 비율 → 동적 수량 → 고정 주문금액
                            if capital_ratio > 0:
                                effective_amount = int(cash * capital_ratio)
                            elif target_order_amount is not None:
                                effective_amount = target_order_amount
                            else:
                                effective_amount = order_amount
                            if target_order_amount is not None and capital_ratio <= 0:
                                qty = max(min_quantity, min(effective_amount // close, max_quantity))
                            else:
                                qty = effective_amount // close
                            if qty > 0 and cash >= qty * close:
                                cash -= qty * close
                                holding_qty = qty
                                holding_avg_price = float(close)
                                holding_since = i
                                holding_peak_price = float(close)
                                daily_buy_count[day_key] = today_buys + 1
                                trades.append(Trade(date=date, side="buy", price=close, quantity=qty, reason="signal"))

        equity = cash + holding_qty * close
        equity_curve.append(equity)

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


@dataclass
class RegimeBacktestResult:
    """국면별 백테스트 결과"""

    regime: str  # MarketRegime value
    regime_kr: str
    days: int
    start_date: str = ""
    end_date: str = ""
    strategy_results: dict[str, BacktestResult] = field(default_factory=dict)


def run_regime_segmented_backtest(
    chart: list[ChartData],
    initial_capital: int = 10_000_000,
    order_amount: int = 500_000,
    short_period: int = 10,
    long_period: int = 40,
    rsi_period: int = 14,
    rsi_overbought: float = 70.0,
    rsi_oversold: float = 30.0,
    volume_ma_period: int = 15,
    obv_ma_period: int = 20,
    stop_loss_pct: float = 5.0,
    max_holding_days: int = 20,
    bollinger_period: int = 20,
    bollinger_num_std: float = 2.0,
    capital_ratio: float = 0.3,
    trailing_stop_pct: float = 0.0,
) -> list[RegimeBacktestResult]:
    """차트를 국면별로 분할하여 4개 전략을 각각 독립 실행.

    전략 4종:
    - SMA 기본: SMA 크로스오버 (필터 없음)
    - SMA+리스크: SMA + stop_loss + max_holding
    - SMA+Adv+리스크: SMA + RSI/거래량/OBV 필터 + 리스크
    - 볼린저: 볼린저밴드 반전 전략

    각 국면 구간에 warm-up 데이터(max(long_period, 120)봉)를 앞에 붙여 SMA 계산 가능하게 함.
    """
    closes = [float(c.close) for c in chart]
    dates = [c.date for c in chart]
    periods = segment_by_regime(closes, dates)

    if not periods:
        return []

    warmup = max(long_period, bollinger_period, 120)
    results: list[RegimeBacktestResult] = []

    for period in periods:
        # warm-up 포함 구간 추출
        pad_start = max(0, period.start_index - warmup)
        segment = chart[pad_start : period.end_index + 1]

        days = period.end_index - period.start_index + 1

        strategies: dict[str, BacktestResult] = {}

        # 1) SMA 기본 (거래량 필터 포함)
        strategies["SMA 기본"] = run_backtest(
            segment,
            initial_capital=initial_capital,
            order_amount=order_amount,
            short_period=short_period,
            long_period=long_period,
            use_advanced=False,
            volume_filter_basic=True,
            capital_ratio=capital_ratio,
            trailing_stop_pct=trailing_stop_pct,
        )

        # 2) SMA + 리스크
        strategies["SMA+리스크"] = run_backtest(
            segment,
            initial_capital=initial_capital,
            order_amount=order_amount,
            short_period=short_period,
            long_period=long_period,
            use_advanced=False,
            stop_loss_pct=stop_loss_pct,
            max_holding_days=max_holding_days,
            capital_ratio=capital_ratio,
            trailing_stop_pct=trailing_stop_pct,
        )

        # 3) SMA + Advanced + 리스크
        strategies["SMA+Adv+리스크"] = run_backtest(
            segment,
            initial_capital=initial_capital,
            order_amount=order_amount,
            short_period=short_period,
            long_period=long_period,
            use_advanced=True,
            rsi_period=rsi_period,
            rsi_overbought=rsi_overbought,
            rsi_oversold=rsi_oversold,
            volume_ma_period=volume_ma_period,
            obv_ma_period=obv_ma_period,
            stop_loss_pct=stop_loss_pct,
            max_holding_days=max_holding_days,
            capital_ratio=capital_ratio,
            trailing_stop_pct=trailing_stop_pct,
        )

        # 4) 볼린저 (trailing_stop은 볼린저 자체 밴드 매도가 있으므로 미적용)
        strategies["볼린저"] = run_bollinger_backtest(
            segment,
            initial_capital=initial_capital,
            order_amount=order_amount,
            period=bollinger_period,
            num_std=bollinger_num_std,
            max_holding_days=max_holding_days,
            capital_ratio=capital_ratio,
        )

        results.append(
            RegimeBacktestResult(
                regime=period.regime.value,
                regime_kr=REGIME_KR[period.regime],
                days=days,
                start_date=period.start_date,
                end_date=period.end_date,
                strategy_results=strategies,
            )
        )

    return results
