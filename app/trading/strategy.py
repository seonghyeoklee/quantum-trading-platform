"""매매 전략 - SMA 크로스오버 + 볼린저밴드 반전 + KAMA + 브레이크아웃"""

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
    reason_detail: str = ""


class BollingerResult(NamedTuple):
    signal: SignalType
    upper_band: float
    middle_band: float
    lower_band: float
    volume_confirmed: bool = True
    obv_confirmed: bool = True
    reason_detail: str = ""


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


def compute_ema(prices: list[float], period: int) -> list[float | None]:
    """지수이동평균(EMA) 계산. period-1 미만 구간은 None."""
    if period <= 0 or len(prices) < period:
        return [None] * len(prices)

    result: list[float | None] = [None] * (period - 1)
    # 첫 EMA는 SMA로 시작
    sma = sum(prices[:period]) / period
    result.append(sma)
    multiplier = 2.0 / (period + 1)

    for i in range(period, len(prices)):
        prev_ema = result[-1]
        ema = prices[i] * multiplier + prev_ema * (1 - multiplier)
        result.append(ema)

    return result


class MACDResult(NamedTuple):
    macd_line: float      # MACD = fast_EMA - slow_EMA
    signal_line: float    # Signal = EMA(MACD, signal_period)
    histogram: float      # Histogram = MACD - Signal


def compute_macd(
    prices: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> MACDResult | None:
    """MACD 계산. 데이터 부족 시 None 반환."""
    if len(prices) < slow + signal:
        return None

    fast_ema = compute_ema(prices, fast)
    slow_ema = compute_ema(prices, slow)

    # MACD line = fast_EMA - slow_EMA (slow_ema가 None이 아닌 구간부터)
    macd_values: list[float] = []
    macd_start = slow - 1  # slow EMA가 유효해지는 시작 인덱스
    for i in range(macd_start, len(prices)):
        if fast_ema[i] is not None and slow_ema[i] is not None:
            macd_values.append(fast_ema[i] - slow_ema[i])

    if len(macd_values) < signal:
        return None

    # Signal line = EMA of MACD values
    signal_ema = compute_ema(macd_values, signal)
    if signal_ema[-1] is None:
        return None

    macd_line = macd_values[-1]
    signal_line = signal_ema[-1]
    histogram = macd_line - signal_line

    return MACDResult(
        macd_line=macd_line,
        signal_line=signal_line,
        histogram=histogram,
    )


def evaluate_signal(
    chart: list[ChartData],
    short_period: int = 5,
    long_period: int = 20,
    volume_ma_period: int | None = None,
    min_gap_pct: float = 0.0,
) -> tuple[SignalType, float, float, str]:
    """
    이동평균 크로스오버 시그널 판단.

    volume_ma_period가 설정되면 BUY 시그널에 거래량 SMA 필터 적용:
    현재 거래량 > 거래량 SMA 이면 확인, 아니면 HOLD로 차단.
    SELL에는 미적용 (매도 차단하면 안 됨).

    Returns:
        (signal, short_ma_today, long_ma_today, reason_detail)
    """
    if len(chart) < long_period + 1:
        return SignalType.HOLD, 0.0, 0.0, "데이터 부족"

    closes = [c.close for c in chart]
    short_ma = compute_sma(closes, short_period)
    long_ma = compute_sma(closes, long_period)

    # 오늘과 전일의 MA 값
    today_short = short_ma[-1]
    today_long = long_ma[-1]
    yesterday_short = short_ma[-2]
    yesterday_long = long_ma[-2]

    if any(v is None for v in [today_short, today_long, yesterday_short, yesterday_long]):
        return SignalType.HOLD, 0.0, 0.0, "MA 계산 불가"

    signal = SignalType.HOLD
    reason = ""

    # 골든크로스: 전일 SMA5 <= SMA20 → 오늘 SMA5 > SMA20
    if yesterday_short <= yesterday_long and today_short > today_long:
        signal = SignalType.BUY
        reason = f"골든크로스 (단기MA {today_short:.1f} > 장기MA {today_long:.1f})"

    # 데드크로스: 전일 SMA5 >= SMA20 → 오늘 SMA5 < SMA20
    elif yesterday_short >= yesterday_long and today_short < today_long:
        signal = SignalType.SELL
        reason = f"데드크로스 (단기MA {today_short:.1f} < 장기MA {today_long:.1f})"

    else:
        reason = f"크로스 없음 (단기MA {today_short:.1f}, 장기MA {today_long:.1f})"

    # 최소 갭 필터 (SMA 간 갭이 기준 미만이면 HOLD)
    if min_gap_pct > 0 and signal != SignalType.HOLD and today_long > 0:
        gap = abs(today_short - today_long) / today_long * 100
        if gap < min_gap_pct:
            reason += f" → 갭 부족 ({gap:.3f}% < {min_gap_pct}%)"
            signal = SignalType.HOLD

    # 거래량 필터 (BUY 시그널에만 적용)
    if volume_ma_period is not None and signal == SignalType.BUY:
        volumes = [float(c.volume) for c in chart]
        vol_sma = compute_sma(volumes, volume_ma_period)
        current_vol_sma = vol_sma[-1] if vol_sma else None
        if current_vol_sma is not None and current_vol_sma > 0:
            if volumes[-1] <= current_vol_sma:
                reason += f" → 거래량 부족({volumes[-1]:.0f} ≤ SMA{volume_ma_period} {current_vol_sma:.0f}) HOLD"
                signal = SignalType.HOLD
        else:
            reason += " → 거래량 SMA 계산 불가 HOLD"
            signal = SignalType.HOLD

    return signal, today_short, today_long, reason


def compute_rsi(prices: list[float], period: int = 14) -> list[float | None]:
    """Wilder's RSI 계산. period 미만 구간은 None."""
    if len(prices) < 2:
        return [None] * len(prices)

    result: list[float | None] = [None]  # 첫 번째는 변화량 없으므로 None

    # 가격 변화량
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    avg_gain = 0.0
    avg_loss = 0.0

    for i in range(len(deltas)):
        if i < period - 1:
            result.append(None)
        elif i == period - 1:
            # 첫 RSI: 단순 평균
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(100.0 - 100.0 / (1.0 + rs))
        else:
            # Wilder's smoothing (반복)
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(100.0 - 100.0 / (1.0 + rs))

    return result


def detect_rsi_divergence(
    prices: list[float],
    rsi_values: list[float | None],
    lookback: int = 14,
) -> str | None:
    """RSI 다이버전스 감지.

    최근 lookback 봉 내에서 로컬 극값(저점 또는 고점) 2개를 찾아
    가격과 RSI의 방향 불일치를 판단한다.

    Returns:
        "bullish"  — 가격은 저점 하락, RSI는 저점 상승 (상승 반전 신호)
        "bearish"  — 가격은 고점 상승, RSI는 고점 하락 (하락 반전 신호)
        None       — 다이버전스 없음 또는 데이터 부족
    """
    if len(prices) < lookback + 2 or len(rsi_values) < lookback + 2:
        return None

    # 분석 범위: 최근 lookback 봉 (마지막 봉 제외 — 아직 확정 안 된 봉)
    start = len(prices) - lookback - 1
    end = len(prices) - 1  # exclusive for local extrema scan

    # 유효한 RSI 값이 있는 구간만 사용
    valid_indices = [
        i for i in range(start, end)
        if rsi_values[i] is not None
    ]
    if len(valid_indices) < 3:
        return None

    # 로컬 저점 찾기 (prices[i] < prices[i-1] and prices[i] < prices[i+1])
    local_lows: list[int] = []
    for idx in range(1, len(valid_indices) - 1):
        i = valid_indices[idx]
        prev_i = valid_indices[idx - 1]
        next_i = valid_indices[idx + 1]
        if prices[i] <= prices[prev_i] and prices[i] <= prices[next_i]:
            local_lows.append(i)

    # 로컬 고점 찾기
    local_highs: list[int] = []
    for idx in range(1, len(valid_indices) - 1):
        i = valid_indices[idx]
        prev_i = valid_indices[idx - 1]
        next_i = valid_indices[idx + 1]
        if prices[i] >= prices[prev_i] and prices[i] >= prices[next_i]:
            local_highs.append(i)

    # Bullish divergence: 최근 2개 저점에서 가격↓ RSI↑
    if len(local_lows) >= 2:
        prev_low, curr_low = local_lows[-2], local_lows[-1]
        prev_rsi = rsi_values[prev_low]
        curr_rsi = rsi_values[curr_low]
        if prev_rsi is not None and curr_rsi is not None:
            if prices[curr_low] < prices[prev_low] and curr_rsi > prev_rsi:
                return "bullish"

    # Bearish divergence: 최근 2개 고점에서 가격↑ RSI↓
    if len(local_highs) >= 2:
        prev_high, curr_high = local_highs[-2], local_highs[-1]
        prev_rsi = rsi_values[prev_high]
        curr_rsi = rsi_values[curr_high]
        if prev_rsi is not None and curr_rsi is not None:
            if prices[curr_high] > prices[prev_high] and curr_rsi < prev_rsi:
                return "bearish"

    return None


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


def compute_atr(chart: list[ChartData], period: int = 14) -> list[float | None]:
    """ATR (Average True Range) 계산 — Wilder smoothing.

    TR = max(high-low, |high-prev_close|, |low-prev_close|)
    첫 ATR = 최초 period개 TR의 단순평균.
    이후 ATR = (prev_ATR * (period-1) + TR) / period.
    """
    n = len(chart)
    if n < 2:
        return [None] * n

    # True Range 계산
    tr_values: list[float] = [float(chart[0].high - chart[0].low)]  # 첫 봉은 H-L
    for i in range(1, n):
        h = float(chart[i].high)
        l = float(chart[i].low)
        pc = float(chart[i - 1].close)
        tr_values.append(max(h - l, abs(h - pc), abs(l - pc)))

    result: list[float | None] = [None] * n
    if n < period:
        return result

    # 첫 ATR: 단순평균
    first_atr = sum(tr_values[:period]) / period
    result[period - 1] = first_atr

    # Wilder smoothing
    prev_atr = first_atr
    for i in range(period, n):
        atr = (prev_atr * (period - 1) + tr_values[i]) / period
        result[i] = atr
        prev_atr = atr

    return result


def compute_kama(
    prices: list[float],
    er_period: int = 10,
    fast_period: int = 2,
    slow_period: int = 30,
) -> list[float | None]:
    """KAMA (Kaufman Adaptive Moving Average) 계산.

    ER = |price[i] - price[i-er_period]| / sum(|price[j] - price[j-1]| for j in window)
    SC = (ER * (fast_sc - slow_sc) + slow_sc)^2
    KAMA[i] = KAMA[i-1] + SC * (price[i] - KAMA[i-1])
    """
    n = len(prices)
    if n <= er_period:
        return [None] * n

    fast_sc = 2.0 / (fast_period + 1)
    slow_sc = 2.0 / (slow_period + 1)

    result: list[float | None] = [None] * n
    # 첫 KAMA = 첫 유효 시점의 종가
    result[er_period] = prices[er_period]
    prev_kama = prices[er_period]

    for i in range(er_period + 1, n):
        direction = abs(prices[i] - prices[i - er_period])
        volatility = sum(
            abs(prices[j] - prices[j - 1]) for j in range(i - er_period + 1, i + 1)
        )
        er = direction / volatility if volatility != 0 else 0.0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        kama = prev_kama + sc * (prices[i] - prev_kama)
        result[i] = kama
        prev_kama = kama

    return result


def compute_donchian_channels(
    chart: list[ChartData],
    upper_period: int = 20,
    lower_period: int = 10,
) -> list[tuple[float | None, float | None]]:
    """도치안 채널 계산.

    upper = 전일까지 upper_period일 최고가 (look-ahead bias 방지)
    lower = 전일까지 lower_period일 최저가
    반환: [(upper, lower), ...] — 데이터 부족 구간은 (None, None)
    """
    n = len(chart)
    result: list[tuple[float | None, float | None]] = []

    for i in range(n):
        # 전일까지(i-1)의 데이터 사용, 최소 period 봉 필요
        u: float | None = None
        l: float | None = None
        if i >= upper_period:
            u = max(float(chart[j].high) for j in range(i - upper_period, i))
        if i >= lower_period:
            l = min(float(chart[j].low) for j in range(i - lower_period, i))
        result.append((u, l))

    return result


def evaluate_signal_with_filters(
    chart: list[ChartData],
    short_period: int = 5,
    long_period: int = 20,
    rsi_period: int = 14,
    rsi_overbought: float = 70.0,
    rsi_oversold: float = 30.0,
    volume_ma_period: int = 20,
    obv_ma_period: int = 20,
    use_rsi_divergence: bool = False,
    use_macd_filter: bool = False,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    min_gap_pct: float = 0.0,
    regime: str | None = None,
) -> StrategyResult:
    """SMA 크로스오버 + RSI 필터 + 거래량 확인 + OBV 확인 + RSI 다이버전스 + MACD

    regime 파라미터:
    - None (기본): 기존 필터 동작 그대로
    - "strong_bull"/"bull": BUY 시 OBV 스킵, RSI 과매수 80으로 완화, 거래량 스킵
    - "bear"/"strong_bear": 기존 필터 + RSI>60 시 BUY 차단
    """
    # 1) 기존 SMA 크로스오버 시그널
    raw_signal, short_ma, long_ma, base_reason = evaluate_signal(
        chart, short_period, long_period, min_gap_pct=min_gap_pct,
    )

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

    # 5) 국면 인식 필터 조정
    is_bull_regime = regime in ("strong_bull", "bull")
    is_bear_regime = regime in ("bear", "strong_bear")

    # 강세장: RSI 과매수 기준 완화
    effective_rsi_overbought = 80.0 if is_bull_regime else rsi_overbought

    # 5) 필터 적용 + 근거 추적
    signal = raw_signal
    reason = base_reason
    filter_reasons: list[str] = []

    if signal != SignalType.HOLD:
        # 약세장 추가 필터: RSI>60이면 BUY 차단
        if is_bear_regime and signal == SignalType.BUY and current_rsi is not None:
            if current_rsi > 60:
                filter_reasons.append(
                    f"약세장 RSI 경고({current_rsi:.1f} > 60)"
                )
                signal = SignalType.HOLD

        # RSI 필터
        if current_rsi is not None:
            if signal == SignalType.BUY and current_rsi > effective_rsi_overbought:
                filter_reasons.append(
                    f"RSI 과매수({current_rsi:.1f} > {effective_rsi_overbought:.0f})"
                )
                signal = SignalType.HOLD
            elif signal == SignalType.SELL and current_rsi < rsi_oversold:
                filter_reasons.append(
                    f"RSI 과매도({current_rsi:.1f} < {rsi_oversold:.0f})"
                )
                signal = SignalType.HOLD

        # 거래량 확인 (BUY에만 적용 — 강세장에서는 스킵)
        if signal == SignalType.BUY and not volume_confirmed and not is_bull_regime:
            filter_reasons.append("거래량 미확인")
            signal = SignalType.HOLD

        # OBV 확인 (거래량 필터 통과한 경우만 — 강세장 BUY는 스킵)
        if signal != SignalType.HOLD:
            if signal == SignalType.BUY and not obv_confirmed and not is_bull_regime:
                filter_reasons.append("OBV 하락추세")
                signal = SignalType.HOLD
            elif signal == SignalType.SELL and obv_confirmed:
                # SELL인데 OBV가 상승추세면 매도 차단
                filter_reasons.append("OBV 상승추세")
                signal = SignalType.HOLD

        # RSI 다이버전스 필터
        if signal != SignalType.HOLD and use_rsi_divergence:
            divergence = detect_rsi_divergence(closes, rsi_values)
            if signal == SignalType.BUY and divergence == "bearish":
                filter_reasons.append("RSI 약세 다이버전스")
                signal = SignalType.HOLD
            elif signal == SignalType.SELL and divergence == "bullish":
                filter_reasons.append("RSI 강세 다이버전스")
                signal = SignalType.HOLD

        # MACD 필터
        if signal != SignalType.HOLD and use_macd_filter:
            macd_result = compute_macd(closes, macd_fast, macd_slow, macd_signal)
            if macd_result is not None:
                hist = macd_result.histogram
                if signal == SignalType.BUY and hist < 0:
                    filter_reasons.append(
                        f"MACD 히스토그램 음수({hist:.4f})"
                    )
                    signal = SignalType.HOLD
                elif signal == SignalType.SELL and hist > 0:
                    filter_reasons.append(
                        f"MACD 히스토그램 양수({hist:.4f})"
                    )
                    signal = SignalType.HOLD

    if filter_reasons:
        reason += " → " + " & ".join(filter_reasons) + " → HOLD"

    return StrategyResult(
        signal=signal,
        raw_signal=raw_signal,
        short_ma=short_ma,
        long_ma=long_ma,
        rsi=current_rsi,
        volume_confirmed=volume_confirmed,
        obv_confirmed=obv_confirmed,
        reason_detail=reason,
    )


def compute_bollinger_bands(
    prices: list[float], period: int = 20, num_std: float = 2.0
) -> list[tuple[float | None, float | None, float | None]]:
    """볼린저밴드 계산. (upper, middle, lower) 튜플 리스트 반환."""
    sma = compute_sma(prices, period)
    result: list[tuple[float | None, float | None, float | None]] = []
    for i in range(len(prices)):
        if sma[i] is None:
            result.append((None, None, None))
        else:
            window = prices[i - period + 1 : i + 1]
            mean = sma[i]
            std = (sum((x - mean) ** 2 for x in window) / period) ** 0.5
            result.append((mean + num_std * std, mean, mean - num_std * std))
    return result


def is_bullish_engulfing(chart: list[ChartData], index: int) -> bool:
    """강세 장악형 캔들: 전봉 음봉 + 현봉 양봉, 현봉 몸통이 전봉 몸통을 감싼다."""
    if index < 1 or index >= len(chart):
        return False
    prev = chart[index - 1]
    curr = chart[index]
    # 전봉 음봉 (close < open), 현봉 양봉 (close > open)
    if prev.close >= prev.open or curr.close <= curr.open:
        return False
    # 현봉 시가 <= 전봉 종가, 현봉 종가 > 전봉 시가 (몸통 완전 감쌈)
    return curr.open <= prev.close and curr.close > prev.open


def is_bearish_engulfing(chart: list[ChartData], index: int) -> bool:
    """약세 장악형 캔들: 전봉 양봉 + 현봉 음봉, 현봉 몸통이 전봉 몸통을 감싼다."""
    if index < 1 or index >= len(chart):
        return False
    prev = chart[index - 1]
    curr = chart[index]
    # 전봉 양봉 (close > open), 현봉 음봉 (close < open)
    if prev.close <= prev.open or curr.close >= curr.open:
        return False
    # 현봉 시가 >= 전봉 종가, 현봉 종가 < 전봉 시가
    return curr.open >= prev.close and curr.close < prev.open


def detect_double_bottom(
    chart: list[ChartData],
    bands: list[tuple[float | None, float | None, float | None]],
    lookback: int = 20,
) -> bool:
    """이중바닥 패턴 감지.

    lookback 내 하단밴드 근처(밴드폭 10% 이내) 저점 2개 탐색.
    두 번째 저점 = 현재봉, bullish engulfing 필요.
    두 번째 저점 <= 첫 번째 저점 * 1.02 (대략 동일 수준).
    """
    if len(chart) < 3 or len(bands) < 3:
        return False

    last_idx = len(chart) - 1
    upper, _, lower = bands[last_idx]
    if upper is None or lower is None:
        return False

    band_width = upper - lower
    if band_width <= 0:
        return False

    threshold = band_width * 0.1  # 밴드폭 10% 이내

    # 두 번째 저점 = 현재봉, bullish engulfing 확인
    if not is_bullish_engulfing(chart, last_idx):
        return False

    curr_low = chart[last_idx].low
    curr_lower = lower
    if curr_low > curr_lower + threshold:
        return False  # 하단밴드 근처가 아님

    # lookback 내 첫 번째 저점 찾기
    start = max(1, last_idx - lookback)
    for i in range(start, last_idx - 1):
        _, _, i_lower = bands[i]
        if i_lower is None:
            continue
        i_band_width = (bands[i][0] or 0) - (bands[i][2] or 0)
        if i_band_width <= 0:
            continue
        i_threshold = i_band_width * 0.1
        if chart[i].low <= i_lower + i_threshold:
            # 첫 번째 저점 발견, 수준 비교
            if curr_low <= chart[i].low * 1.02:
                return True

    return False


def detect_double_top(
    chart: list[ChartData],
    bands: list[tuple[float | None, float | None, float | None]],
    lookback: int = 20,
) -> bool:
    """이중천장 패턴 감지.

    lookback 내 상단밴드 근처 고점 2개.
    두 번째 고점 = 현재봉, bearish engulfing 필요.
    두 번째 고점 >= 첫 번째 고점 * 0.98 (대략 동일 수준).
    """
    if len(chart) < 3 or len(bands) < 3:
        return False

    last_idx = len(chart) - 1
    upper, _, lower = bands[last_idx]
    if upper is None or lower is None:
        return False

    band_width = upper - lower
    if band_width <= 0:
        return False

    threshold = band_width * 0.1

    if not is_bearish_engulfing(chart, last_idx):
        return False

    curr_high = chart[last_idx].high
    if curr_high < upper - threshold:
        return False

    start = max(1, last_idx - lookback)
    for i in range(start, last_idx - 1):
        i_upper, _, i_lower = bands[i]
        if i_upper is None or i_lower is None:
            continue
        i_band_width = i_upper - i_lower
        if i_band_width <= 0:
            continue
        i_threshold = i_band_width * 0.1
        if chart[i].high >= i_upper - i_threshold:
            if curr_high >= chart[i].high * 0.98:
                return True

    return False


def evaluate_bollinger_signal(
    chart: list[ChartData],
    period: int = 20,
    num_std: float = 2.0,
    volume_ma_period: int | None = None,
    min_bandwidth: float = 0.0,
    min_sell_bandwidth: float = 0.0,
    use_middle_exit: bool = False,
    use_engulfing_filter: bool = False,
    use_double_pattern: bool = False,
    rsi_period: int = 14,
    rsi_overbought: float = 70.0,
    rsi_oversold: float = 30.0,
    obv_ma_period: int | None = None,
    bandwidth_percentile: float = 0.0,
    bandwidth_lookback: int = 100,
) -> BollingerResult:
    """볼린저밴드 반전 시그널 판단.

    - BUY: 전봉 종가 ≤ 하단밴드 AND 현봉 종가 > 하단밴드 (하단 반등)
    - SELL: 현봉 종가 ≥ 상단밴드 (상단 도달 = 익절)
    - HOLD: 그 외

    volume_ma_period가 설정되면 매수 시그널에 거래량 SMA 필터 적용:
    현재 거래량 > 거래량 SMA 이면 확인, 아니면 HOLD로 차단.

    min_sell_bandwidth: 매도 전용 밴드폭 필터. 밴드폭이 기준 미만이면 SELL→HOLD.
    use_middle_exit: True이면 현재가 < 중간밴드일 때 SELL 시그널 생성.
    """
    if len(chart) < period + 1:
        return BollingerResult(
            signal=SignalType.HOLD,
            upper_band=0.0,
            middle_band=0.0,
            lower_band=0.0,
            reason_detail="데이터 부족",
        )

    closes = [float(c.close) for c in chart]
    bands = compute_bollinger_bands(closes, period, num_std)

    upper, middle, lower = bands[-1]
    _, _, prev_lower = bands[-2]

    if any(v is None for v in [upper, middle, lower, prev_lower]):
        return BollingerResult(
            signal=SignalType.HOLD,
            upper_band=0.0,
            middle_band=0.0,
            lower_band=0.0,
            reason_detail="밴드 계산 불가",
        )

    current_close = closes[-1]
    prev_close = closes[-2]

    signal = SignalType.HOLD
    reason = ""

    # 밴드 폭이 0이면 (표준편차 0 = 무변동) 시그널 없음
    if upper <= lower:
        return BollingerResult(
            signal=SignalType.HOLD,
            upper_band=upper,
            middle_band=middle,
            lower_band=lower,
            reason_detail="밴드 폭 0 (무변동)",
        )

    # 적응형 밴드폭 필터 (bandwidth_percentile > 0이면 동적 기준 사용)
    effective_min_bandwidth = min_bandwidth
    if bandwidth_percentile > 0 and middle > 0 and len(chart) > period:
        bw_history: list[float] = []
        lookback_start = max(0, len(chart) - bandwidth_lookback)
        for idx in range(lookback_start, len(chart)):
            u_h, m_h, l_h = bands[idx]
            if u_h is not None and m_h is not None and l_h is not None and m_h > 0:
                bw_history.append((u_h - l_h) / m_h * 100)
        if bw_history:
            sorted_bw = sorted(bw_history)
            pct_idx = max(0, min(int(len(sorted_bw) * bandwidth_percentile / 100), len(sorted_bw) - 1))
            effective_min_bandwidth = max(min_bandwidth, sorted_bw[pct_idx])

    # 밴드 폭 최소 필터 (장 초반 노이즈 방지)
    if effective_min_bandwidth > 0 and middle > 0:
        bandwidth = (upper - lower) / middle * 100
        if bandwidth < effective_min_bandwidth:
            return BollingerResult(
                signal=SignalType.HOLD,
                upper_band=upper,
                middle_band=middle,
                lower_band=lower,
                reason_detail=f"밴드 폭 부족 ({bandwidth:.2f}% < {effective_min_bandwidth:.1f}%)",
            )

    # BUY: 전봉 종가 ≤ 하단밴드 AND 현봉 종가 > 하단밴드 (반등 확인)
    if prev_close <= prev_lower and current_close > lower:
        signal = SignalType.BUY
        reason = f"하단 반등 (현재가 {current_close:.1f} > 하한 {lower:.1f})"
    # SELL: 현봉 종가 ≥ 상단밴드 (상단 도달)
    elif current_close >= upper:
        signal = SignalType.SELL
        reason = f"상단 도달 (현재가 {current_close:.1f} ≥ 상한 {upper:.1f})"
    # 중간밴드 이탈 매도 (보유 시에만 적용 — 엔진에서 has_position 전달)
    elif use_middle_exit and current_close < middle:
        signal = SignalType.SELL
        reason = f"중간밴드 이탈 (현재가 {current_close:.1f} < 중간 {middle:.1f})"
    else:
        reason = f"밴드 내 위치 (하한 {lower:.1f} < 현재가 {current_close:.1f} < 상한 {upper:.1f})"

    # 매도 전용 밴드폭 필터 (밴드가 좁을 때 의미 없는 매도 차단)
    if min_sell_bandwidth > 0 and signal == SignalType.SELL and middle > 0:
        bandwidth = (upper - lower) / middle * 100
        if bandwidth < min_sell_bandwidth:
            reason += f" → 매도 밴드폭 부족({bandwidth:.2f}% < {min_sell_bandwidth:.1f}%) → HOLD"
            signal = SignalType.HOLD

    # 장악형 캔들 필터 (로스 카메론 방식)
    if use_engulfing_filter and signal != SignalType.HOLD:
        last_idx = len(chart) - 1
        if signal == SignalType.BUY and not is_bullish_engulfing(chart, last_idx):
            reason += " → 강세 장악형 캔들 미감지 → HOLD"
            signal = SignalType.HOLD
        elif signal == SignalType.SELL and not is_bearish_engulfing(chart, last_idx):
            reason += " → 약세 장악형 캔들 미감지 → HOLD"
            signal = SignalType.HOLD

    # 이중바닥/천장 패턴 필터
    if use_double_pattern and signal != SignalType.HOLD:
        if signal == SignalType.BUY and not detect_double_bottom(chart, bands):
            reason += " → 이중바닥 미감지 → HOLD"
            signal = SignalType.HOLD
        elif signal == SignalType.SELL and not detect_double_top(chart, bands):
            reason += " → 이중천장 미감지 → HOLD"
            signal = SignalType.HOLD

    # RSI 극단 필터 (engulfing 또는 double pattern 활성 시만 적용)
    if (use_engulfing_filter or use_double_pattern) and signal != SignalType.HOLD:
        rsi_values = compute_rsi(closes, rsi_period)
        current_rsi = rsi_values[-1] if rsi_values else None
        if current_rsi is not None:
            if signal == SignalType.BUY and current_rsi > rsi_oversold:
                reason += f" → RSI 과매도 아님({current_rsi:.1f} > {rsi_oversold:.0f}) → HOLD"
                signal = SignalType.HOLD
            elif signal == SignalType.SELL and current_rsi < rsi_overbought:
                reason += f" → RSI 과매수 아님({current_rsi:.1f} < {rsi_overbought:.0f}) → HOLD"
                signal = SignalType.HOLD

    # 거래량/OBV 공통 데이터 (필터 활성 시 한번만 계산)
    volumes: list[float] | None = None
    if volume_ma_period is not None or obv_ma_period is not None:
        volumes = [float(c.volume) for c in chart]

    # 거래량 필터 (매수 시그널에만 적용)
    volume_confirmed = True
    if volume_ma_period is not None and signal == SignalType.BUY and volumes is not None:
        vol_sma = compute_sma(volumes, volume_ma_period)
        current_vol_sma = vol_sma[-1] if vol_sma else None
        if current_vol_sma is not None and current_vol_sma > 0:
            volume_confirmed = volumes[-1] > current_vol_sma
        else:
            volume_confirmed = False
        if not volume_confirmed:
            reason += " → 거래량 미확인 → HOLD"
            signal = SignalType.HOLD

    # OBV 필터 (거래량 필터 통과 후 적용, obv_ma_period=None이면 비활성)
    obv_confirmed = True
    if obv_ma_period is not None and signal != SignalType.HOLD and volumes is not None:
        obv_values = compute_obv(closes, volumes)
        obv_sma = compute_sma(obv_values, obv_ma_period)
        current_obv_sma = obv_sma[-1] if obv_sma else None
        if current_obv_sma is not None:
            obv_confirmed = obv_values[-1] > current_obv_sma
        else:
            obv_confirmed = False
        if signal == SignalType.BUY and not obv_confirmed:
            reason += " → OBV 하락추세 → HOLD"
            signal = SignalType.HOLD
        elif signal == SignalType.SELL and obv_confirmed:
            reason += " → OBV 상승추세 → HOLD"
            signal = SignalType.HOLD

    return BollingerResult(
        signal=signal,
        upper_band=upper,
        middle_band=middle,
        lower_band=lower,
        volume_confirmed=volume_confirmed,
        obv_confirmed=obv_confirmed,
        reason_detail=reason,
    )


class KAMAResult(NamedTuple):
    signal: SignalType
    kama: float
    signal_line: float
    atr: float | None = None
    volume_confirmed: bool = True
    reason_detail: str = ""


def evaluate_kama_signal(
    chart: list[ChartData],
    er_period: int = 10,
    fast_period: int = 2,
    slow_period: int = 30,
    signal_period: int = 10,
    volume_filter: bool = False,
    volume_ma_period: int = 20,
    atr_period: int = 14,
) -> KAMAResult:
    """KAMA 크로스오버 시그널 판단.

    KAMA vs Signal Line(SMA of KAMA) 크로스오버.
    KAMA 골든크로스 → BUY, 데드크로스 → SELL.
    """
    min_data = er_period + signal_period + 2
    if len(chart) < min_data:
        return KAMAResult(
            signal=SignalType.HOLD, kama=0.0, signal_line=0.0,
            reason_detail="데이터 부족",
        )

    closes = [float(c.close) for c in chart]
    kama_values = compute_kama(closes, er_period, fast_period, slow_period)

    # KAMA의 SMA = signal line
    valid_kama = [v for v in kama_values if v is not None]
    if len(valid_kama) < signal_period + 1:
        return KAMAResult(
            signal=SignalType.HOLD, kama=0.0, signal_line=0.0,
            reason_detail="KAMA 계산 불가",
        )

    # signal line: KAMA 유효 값의 SMA
    kama_signal_sma = compute_sma(valid_kama, signal_period)
    if kama_signal_sma[-1] is None or kama_signal_sma[-2] is None:
        return KAMAResult(
            signal=SignalType.HOLD, kama=0.0, signal_line=0.0,
            reason_detail="시그널 라인 계산 불가",
        )

    today_kama = valid_kama[-1]
    today_signal = kama_signal_sma[-1]
    yesterday_kama = valid_kama[-2]
    yesterday_signal = kama_signal_sma[-2]

    # ATR 계산
    atr_values = compute_atr(chart, atr_period)
    current_atr = atr_values[-1]

    signal = SignalType.HOLD
    reason = ""

    # 골든크로스: 전일 KAMA <= Signal → 오늘 KAMA > Signal
    if yesterday_kama <= yesterday_signal and today_kama > today_signal:
        signal = SignalType.BUY
        reason = f"KAMA 골든크로스 (KAMA {today_kama:.1f} > Signal {today_signal:.1f})"
    # 데드크로스: 전일 KAMA >= Signal → 오늘 KAMA < Signal
    elif yesterday_kama >= yesterday_signal and today_kama < today_signal:
        signal = SignalType.SELL
        reason = f"KAMA 데드크로스 (KAMA {today_kama:.1f} < Signal {today_signal:.1f})"
    else:
        reason = f"KAMA 크로스 없음 (KAMA {today_kama:.1f}, Signal {today_signal:.1f})"

    # 거래량 필터 (BUY만)
    volume_confirmed = True
    if volume_filter and signal == SignalType.BUY:
        volumes = [float(c.volume) for c in chart]
        vol_sma = compute_sma(volumes, volume_ma_period)
        current_vol_sma = vol_sma[-1] if vol_sma else None
        if current_vol_sma is not None and current_vol_sma > 0:
            volume_confirmed = volumes[-1] > current_vol_sma
        else:
            volume_confirmed = False
        if not volume_confirmed:
            reason += " → 거래량 미확인 → HOLD"
            signal = SignalType.HOLD

    return KAMAResult(
        signal=signal,
        kama=today_kama,
        signal_line=today_signal,
        atr=current_atr,
        volume_confirmed=volume_confirmed,
        reason_detail=reason,
    )


class BreakoutResult(NamedTuple):
    signal: SignalType
    upper_channel: float
    lower_channel: float
    atr: float | None = None
    volume_confirmed: bool = True
    reason_detail: str = ""


def evaluate_breakout_signal(
    chart: list[ChartData],
    upper_period: int = 20,
    lower_period: int = 10,
    atr_filter: float = 0.0,
    atr_period: int = 14,
    volume_filter: bool = True,
    volume_ma_period: int = 20,
) -> BreakoutResult:
    """도치안 채널 브레이크아웃 시그널 판단.

    전일 N일 최고가 돌파 → BUY (look-ahead bias 방지)
    전일 M일 최저가 이탈 → SELL
    """
    min_data = max(upper_period, lower_period) + 1
    if len(chart) < min_data:
        return BreakoutResult(
            signal=SignalType.HOLD, upper_channel=0.0, lower_channel=0.0,
            reason_detail="데이터 부족",
        )

    channels = compute_donchian_channels(chart, upper_period, lower_period)
    upper, lower = channels[-1]

    if upper is None or lower is None:
        return BreakoutResult(
            signal=SignalType.HOLD, upper_channel=0.0, lower_channel=0.0,
            reason_detail="채널 계산 불가",
        )

    current_close = float(chart[-1].close)

    # ATR 계산
    atr_values = compute_atr(chart, atr_period)
    current_atr = atr_values[-1]

    signal = SignalType.HOLD
    reason = ""

    # BUY: 현재 종가 > 전일까지 N일 최고가
    if current_close > upper:
        signal = SignalType.BUY
        reason = f"상단 돌파 (종가 {current_close:.1f} > 채널상단 {upper:.1f})"
    # SELL: 현재 종가 < 전일까지 M일 최저가
    elif current_close < lower:
        signal = SignalType.SELL
        reason = f"하단 이탈 (종가 {current_close:.1f} < 채널하단 {lower:.1f})"
    else:
        reason = f"채널 내 (하단 {lower:.1f} ≤ 종가 {current_close:.1f} ≤ 상단 {upper:.1f})"

    # ATR 필터: 변동성이 충분할 때만 매매 (BUY만)
    if atr_filter > 0 and signal == SignalType.BUY and current_atr is not None:
        if current_close > 0:
            atr_pct = current_atr / current_close * 100
            if atr_pct < atr_filter:
                reason += f" → ATR 부족({atr_pct:.2f}% < {atr_filter:.1f}%) → HOLD"
                signal = SignalType.HOLD

    # 거래량 필터 (BUY만)
    volume_confirmed = True
    if volume_filter and signal == SignalType.BUY:
        volumes = [float(c.volume) for c in chart]
        vol_sma = compute_sma(volumes, volume_ma_period)
        current_vol_sma = vol_sma[-1] if vol_sma else None
        if current_vol_sma is not None and current_vol_sma > 0:
            volume_confirmed = volumes[-1] > current_vol_sma
        else:
            volume_confirmed = False
        if not volume_confirmed:
            reason += " → 거래량 미확인 → HOLD"
            signal = SignalType.HOLD

    return BreakoutResult(
        signal=signal,
        upper_channel=upper,
        lower_channel=lower,
        atr=current_atr,
        volume_confirmed=volume_confirmed,
        reason_detail=reason,
    )
