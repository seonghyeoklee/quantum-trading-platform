"""시장 국면 판별 모듈 — SMA 정배열/역배열 기반"""

from enum import Enum
from typing import NamedTuple

from app.trading.strategy import compute_rsi, compute_sma


class MarketRegime(str, Enum):
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    SIDEWAYS = "sideways"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"


REGIME_KR = {
    MarketRegime.STRONG_BULL: "강한 상승",
    MarketRegime.BULL: "상승",
    MarketRegime.SIDEWAYS: "횡보",
    MarketRegime.BEAR: "하락",
    MarketRegime.STRONG_BEAR: "강한 하락",
}


class RegimeInfo(NamedTuple):
    regime: MarketRegime
    sma20: float
    sma60: float
    sma120: float
    rsi14: float | None
    last_price: float


class RegimePeriod(NamedTuple):
    regime: MarketRegime
    start_index: int
    end_index: int
    start_date: str
    end_date: str


def classify_regime(
    last: float, sma20: float, sma60: float, sma120: float
) -> MarketRegime:
    """현재가와 SMA20/60/120 위치 관계로 국면 판별.

    - strong_bull: last > SMA20 > SMA60 > SMA120 (완전 정배열)
    - bull: last > SMA60 AND SMA20 > SMA60
    - strong_bear: last < SMA20 < SMA60 < SMA120 (완전 역배열)
    - bear: last < SMA60 AND SMA20 < SMA60
    - sideways: 나머지
    """
    if last > sma20 > sma60 > sma120:
        return MarketRegime.STRONG_BULL
    if last > sma60 and sma20 > sma60:
        return MarketRegime.BULL
    if last < sma20 < sma60 < sma120:
        return MarketRegime.STRONG_BEAR
    if last < sma60 and sma20 < sma60:
        return MarketRegime.BEAR
    return MarketRegime.SIDEWAYS


def detect_current_regime(closes: list[float]) -> RegimeInfo | None:
    """종가 리스트로 현재 국면 판별. 데이터 120개 미만이면 None."""
    if len(closes) < 120:
        return None

    sma20_vals = compute_sma(closes, 20)
    sma60_vals = compute_sma(closes, 60)
    sma120_vals = compute_sma(closes, 120)
    rsi_vals = compute_rsi(closes, 14)

    sma20 = sma20_vals[-1]
    sma60 = sma60_vals[-1]
    sma120 = sma120_vals[-1]

    if sma20 is None or sma60 is None or sma120 is None:
        return None

    last = closes[-1]
    regime = classify_regime(last, sma20, sma60, sma120)

    return RegimeInfo(
        regime=regime,
        sma20=sma20,
        sma60=sma60,
        sma120=sma120,
        rsi14=rsi_vals[-1],
        last_price=last,
    )


def segment_by_regime(
    closes: list[float], dates: list[str]
) -> list[RegimePeriod]:
    """종가+날짜 리스트를 국면 구간으로 분할.

    SMA120 계산에 최소 120개 데이터 필요. 부족 시 빈 리스트 반환.
    인덱스 119(0-based)부터 국면 판별 시작.
    """
    if len(closes) < 120 or len(dates) < 120:
        return []

    sma20_vals = compute_sma(closes, 20)
    sma60_vals = compute_sma(closes, 60)
    sma120_vals = compute_sma(closes, 120)

    periods: list[RegimePeriod] = []
    current_regime: MarketRegime | None = None
    start_idx = 0

    for i in range(119, len(closes)):
        s20 = sma20_vals[i]
        s60 = sma60_vals[i]
        s120 = sma120_vals[i]

        if s20 is None or s60 is None or s120 is None:
            continue

        regime = classify_regime(closes[i], s20, s60, s120)

        if current_regime is None:
            current_regime = regime
            start_idx = i
        elif regime != current_regime:
            periods.append(
                RegimePeriod(
                    regime=current_regime,
                    start_index=start_idx,
                    end_index=i - 1,
                    start_date=dates[start_idx],
                    end_date=dates[i - 1],
                )
            )
            current_regime = regime
            start_idx = i

    # 마지막 구간
    if current_regime is not None:
        periods.append(
            RegimePeriod(
                regime=current_regime,
                start_index=start_idx,
                end_index=len(closes) - 1,
                start_date=dates[start_idx],
                end_date=dates[-1],
            )
        )

    return periods
