"""이동평균 크로스오버 전략 - 순수 함수 구현"""

from app.models import ChartData, SignalType


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
