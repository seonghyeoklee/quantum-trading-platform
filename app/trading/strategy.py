"""이동평균 크로스오버 전략 - 순수 함수 구현"""

from typing import NamedTuple

from app.models import ChartData, SignalType


class StrategyResult(NamedTuple):
    signal: SignalType  # 최종 시그널 (필터 적용 후)
    raw_signal: SignalType  # 원래 SMA 크로스오버 시그널
    short_ma: float
    long_ma: float
    rsi: float | None
    volume_confirmed: bool
    obv_confirmed: bool


def compute_sma(prices: list[float], period: int) -> list[float | None]:
    """단순이동평균 계산. 데이터 부족 구간은 None."""
    result: list[float | None] = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            window = prices[i - period + 1 : i + 1]
            result.append(sum(window) / period)
    return result


def evaluate_signal(
    chart: list[ChartData],
    short_period: int = 5,
    long_period: int = 20,
) -> tuple[SignalType, float, float]:
    """
    이동평균 크로스오버 시그널 판단.

    Returns:
        (signal, short_ma_today, long_ma_today)
    """
    if len(chart) < long_period + 1:
        return SignalType.HOLD, 0.0, 0.0

    closes = [c.close for c in chart]
    short_ma = compute_sma(closes, short_period)
    long_ma = compute_sma(closes, long_period)

    # 오늘과 전일의 MA 값
    today_short = short_ma[-1]
    today_long = long_ma[-1]
    yesterday_short = short_ma[-2]
    yesterday_long = long_ma[-2]

    if any(v is None for v in [today_short, today_long, yesterday_short, yesterday_long]):
        return SignalType.HOLD, 0.0, 0.0

    # 골든크로스: 전일 SMA5 <= SMA20 → 오늘 SMA5 > SMA20
    if yesterday_short <= yesterday_long and today_short > today_long:
        return SignalType.BUY, today_short, today_long

    # 데드크로스: 전일 SMA5 >= SMA20 → 오늘 SMA5 < SMA20
    if yesterday_short >= yesterday_long and today_short < today_long:
        return SignalType.SELL, today_short, today_long

    return SignalType.HOLD, today_short, today_long


def compute_rsi(prices: list[float], period: int = 14) -> list[float | None]:
    """Wilder's RSI 계산. period 미만 구간은 None."""
    if len(prices) < 2:
        return [None] * len(prices)

    result: list[float | None] = [None]  # 첫 번째는 변화량 없으므로 None

    # 가격 변화량
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    for i in range(len(deltas)):
        if i < period - 1:
            result.append(None)
        elif i == period - 1:
            # 첫 RSI: 단순 평균
            avg_gain = sum(gains[: period]) / period
            avg_loss = sum(losses[: period]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(100.0 - 100.0 / (1.0 + rs))
        else:
            # Wilder's smoothing
            prev_avg_gain = _extract_avg_gain(gains, losses, period, i)
            prev_avg_loss = _extract_avg_loss(gains, losses, period, i)
            avg_gain = (prev_avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (prev_avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(100.0 - 100.0 / (1.0 + rs))

    return result


def _extract_avg_gain(
    gains: list[float], losses: list[float], period: int, up_to: int
) -> float:
    """up_to 이전까지의 Wilder's smoothed avg_gain 재귀 계산."""
    if up_to == period - 1:
        return sum(gains[:period]) / period
    prev = _extract_avg_gain(gains, losses, period, up_to - 1)
    return (prev * (period - 1) + gains[up_to - 1]) / period


def _extract_avg_loss(
    gains: list[float], losses: list[float], period: int, up_to: int
) -> float:
    """up_to 이전까지의 Wilder's smoothed avg_loss 재귀 계산."""
    if up_to == period - 1:
        return sum(losses[:period]) / period
    prev = _extract_avg_loss(gains, losses, period, up_to - 1)
    return (prev * (period - 1) + losses[up_to - 1]) / period


def compute_obv(closes: list[float], volumes: list[float]) -> list[float]:
    """OBV (On-Balance Volume) 계산.

    - close > prev_close → OBV += volume
    - close < prev_close → OBV -= volume
    - close == prev_close → OBV 변화 없음
    """
    if not closes:
        return []
    obv = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv.append(obv[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    return obv


def evaluate_signal_with_filters(
    chart: list[ChartData],
    short_period: int = 5,
    long_period: int = 20,
    rsi_period: int = 14,
    rsi_overbought: float = 70.0,
    rsi_oversold: float = 30.0,
    volume_ma_period: int = 20,
    obv_ma_period: int = 20,
) -> StrategyResult:
    """SMA 크로스오버 + RSI 필터 + 거래량 확인 + OBV 확인"""
    # 1) 기존 SMA 크로스오버 시그널
    raw_signal, short_ma, long_ma = evaluate_signal(chart, short_period, long_period)

    # 2) RSI 계산
    closes = [float(c.close) for c in chart]
    rsi_values = compute_rsi(closes, rsi_period)
    current_rsi = rsi_values[-1] if rsi_values else None

    # 3) 거래량 확인
    volumes = [float(c.volume) for c in chart]
    volume_sma = compute_sma(volumes, volume_ma_period)
    current_volume_sma = volume_sma[-1] if volume_sma else None

    if current_volume_sma is not None and current_volume_sma > 0:
        volume_confirmed = volumes[-1] > current_volume_sma
    else:
        volume_confirmed = False

    # 4) OBV 확인
    obv_values = compute_obv(closes, volumes)
    obv_sma = compute_sma(obv_values, obv_ma_period)
    current_obv_sma = obv_sma[-1] if obv_sma else None

    if current_obv_sma is not None:
        obv_confirmed = obv_values[-1] > current_obv_sma
    else:
        obv_confirmed = False

    # 5) 필터 적용
    signal = raw_signal

    if signal != SignalType.HOLD:
        # RSI 필터
        if current_rsi is not None:
            if signal == SignalType.BUY and current_rsi > rsi_overbought:
                signal = SignalType.HOLD
            elif signal == SignalType.SELL and current_rsi < rsi_oversold:
                signal = SignalType.HOLD

        # 거래량 확인 (RSI 필터 통과한 경우만)
        if signal != SignalType.HOLD and not volume_confirmed:
            signal = SignalType.HOLD

        # OBV 확인 (거래량 필터 통과한 경우만)
        if signal != SignalType.HOLD:
            if signal == SignalType.BUY and not obv_confirmed:
                signal = SignalType.HOLD
            elif signal == SignalType.SELL and obv_confirmed:
                # SELL인데 OBV가 상승추세면 매도 차단
                signal = SignalType.HOLD

    return StrategyResult(
        signal=signal,
        raw_signal=raw_signal,
        short_ma=short_ma,
        long_ma=long_ma,
        rsi=current_rsi,
        volume_confirmed=volume_confirmed,
        obv_confirmed=obv_confirmed,
    )
