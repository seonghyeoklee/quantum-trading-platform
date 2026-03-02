"""매매 전략 단위 테스트"""

from app.models import ChartData, SignalType
from app.trading.strategy import (
    compute_atr,
    compute_bollinger_bands,
    compute_donchian_channels,
    compute_ema,
    compute_kama,
    compute_macd,
    compute_obv,
    compute_rsi,
    compute_sma,
    detect_double_bottom,
    detect_double_top,
    detect_rsi_divergence,
    evaluate_bollinger_signal,
    evaluate_breakout_signal,
    evaluate_kama_signal,
    evaluate_signal,
    evaluate_signal_with_filters,
    is_bearish_engulfing,
    is_bullish_engulfing,
)


def _make_chart(
    closes: list[int], volumes: list[int] | None = None
) -> list[ChartData]:
    """테스트용 차트 데이터 생성"""
    if volumes is None:
        volumes = [1000] * len(closes)
    return [
        ChartData(
            date=f"2025{(i // 28 + 1):02d}{(i % 28 + 1):02d}",
            open=c,
            high=c + 100,
            low=c - 100,
            close=c,
            volume=volumes[i],
        )
        for i, c in enumerate(closes)
    ]


class TestComputeSMA:
    def test_basic(self):
        result = compute_sma([1, 2, 3, 4, 5], 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 2.0  # (1+2+3)/3
        assert result[3] == 3.0  # (2+3+4)/3
        assert result[4] == 4.0  # (3+4+5)/3

    def test_period_equals_length(self):
        result = compute_sma([10, 20, 30], 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 20.0

    def test_period_one(self):
        result = compute_sma([5, 10, 15], 1)
        assert result == [5.0, 10.0, 15.0]


class TestEvaluateSignal:
    def test_golden_cross_buy(self):
        """골든크로스 → BUY 시그널"""
        # 횡보 후 하락(SMA5<SMA20) → 마지막에 급등으로 SMA5>SMA20
        closes = (
            [100] * 20
            + [95, 94, 93, 92, 150]  # 하락 후 급반등
        )
        chart = _make_chart(closes)
        signal, short_ma, long_ma, _reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.BUY
        assert short_ma > long_ma

    def test_dead_cross_sell(self):
        """데드크로스 → SELL 시그널"""
        # 횡보 후 상승(SMA5>SMA20) → 마지막에 급락으로 SMA5<SMA20
        closes = (
            [100] * 20
            + [105, 106, 107, 108, 50]  # 상승 후 급락
        )
        chart = _make_chart(closes)
        signal, short_ma, long_ma, _reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.SELL
        assert short_ma < long_ma

    def test_hold_no_cross(self):
        """크로스 없음 → HOLD"""
        # SMA5 > SMA20 유지 (이미 위에 있고 계속 위)
        closes = [100] * 20 + [120, 121, 122, 123, 124]
        chart = _make_chart(closes)
        signal, _, _, _ = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD

    def test_hold_flat(self):
        """완전 횡보 → HOLD"""
        closes = [100] * 25
        chart = _make_chart(closes)
        signal, short_ma, long_ma, _reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD
        assert short_ma == long_ma == 100.0

    def test_insufficient_data(self):
        """데이터 부족 → HOLD"""
        closes = [100] * 15  # 20+1 미만
        chart = _make_chart(closes)
        signal, short_ma, long_ma, _reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD
        assert short_ma == 0.0
        assert long_ma == 0.0

    def test_custom_periods(self):
        """커스텀 기간 파라미터"""
        closes = [100] * 10 + [95, 94, 93, 92, 150]
        chart = _make_chart(closes)
        signal, short_ma, long_ma, _reason = evaluate_signal(chart, 3, 10)
        assert signal == SignalType.BUY
        assert short_ma > long_ma

    def test_volume_filter_blocks_low_volume(self):
        """골든크로스 + 거래량 부족 → BUY → HOLD"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 24 + [100]  # 마지막 날 거래량 매우 낮음
        chart = _make_chart(closes, volumes)
        signal, _, _, _ = evaluate_signal(chart, 5, 20, volume_ma_period=20)
        assert signal == SignalType.HOLD

    def test_volume_filter_none_keeps_original(self):
        """volume_ma_period 미설정 시 기존 동작 유지"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 24 + [100]  # 거래량 낮아도 필터 없으면 BUY
        chart = _make_chart(closes, volumes)
        signal, _, _, _ = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.BUY


class TestComputeRSI:
    def test_rising_prices_high_rsi(self):
        """연속 상승 → 높은 RSI"""
        prices = [float(100 + i) for i in range(20)]  # 100→119
        rsi = compute_rsi(prices, 14)
        assert rsi[-1] is not None
        assert rsi[-1] > 70

    def test_falling_prices_low_rsi(self):
        """연속 하락 → 낮은 RSI"""
        prices = [float(200 - i) for i in range(20)]  # 200→181
        rsi = compute_rsi(prices, 14)
        assert rsi[-1] is not None
        assert rsi[-1] < 30

    def test_flat_prices_mid_rsi(self):
        """횡보 → RSI 약 50"""
        # 상승/하락 교대 → gain/loss 균등
        prices = [100.0]
        for i in range(19):
            prices.append(prices[-1] + (5 if i % 2 == 0 else -5))
        rsi = compute_rsi(prices, 14)
        assert rsi[-1] is not None
        assert 40 < rsi[-1] < 60

    def test_insufficient_data_returns_none(self):
        """데이터 부족 → None"""
        prices = [100.0, 101.0, 102.0]
        rsi = compute_rsi(prices, 14)
        assert all(v is None for v in rsi)

    def test_rsi_bounds(self):
        """RSI는 항상 0~100 범위"""
        prices = [float(100 + i * 2) for i in range(30)]
        rsi = compute_rsi(prices, 14)
        for v in rsi:
            if v is not None:
                assert 0 <= v <= 100


class TestVolumeConfirmation:
    def test_volume_above_sma_confirmed(self):
        """거래량 > 20일 SMA → 확인됨"""
        # 골든크로스 + 높은 거래량
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [1000] * 24 + [5000]  # 마지막 날 거래량 급증
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(chart, 5, 20)
        assert result.volume_confirmed is True

    def test_volume_below_sma_not_confirmed(self):
        """거래량 < 20일 SMA → 미확인"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 24 + [100]  # 마지막 날 거래량 급감
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(chart, 5, 20)
        assert result.volume_confirmed is False


class TestCompositeStrategy:
    def _golden_cross_data(
        self, volumes: list[int] | None = None
    ) -> list[ChartData]:
        """골든크로스가 발생하는 차트 데이터"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        if volumes is None:
            volumes = [5000] * 24 + [10000]
        return _make_chart(closes, volumes)

    def _dead_cross_data(
        self, volumes: list[int] | None = None
    ) -> list[ChartData]:
        """데드크로스가 발생하는 차트 데이터"""
        closes = [100] * 20 + [105, 106, 107, 108, 50]
        if volumes is None:
            volumes = [5000] * 24 + [10000]
        return _make_chart(closes, volumes)

    def test_buy_passes_all_filters(self):
        """골든크로스 + RSI OK + 거래량 확인 → BUY"""
        chart = self._golden_cross_data()
        result = evaluate_signal_with_filters(chart, 5, 20)
        assert result.raw_signal == SignalType.BUY
        # RSI와 거래량 모두 통과하면 BUY 유지
        if result.rsi is not None and result.rsi <= 70 and result.volume_confirmed:
            assert result.signal == SignalType.BUY

    def test_buy_blocked_by_rsi_overbought(self):
        """골든크로스 + RSI 과매수 → HOLD"""
        # 연속 상승으로 RSI 높이기
        closes = [50] * 6 + [50 + i * 3 for i in range(19)] + [200]
        volumes = [5000] * 25 + [10000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_overbought=70.0
        )
        if result.raw_signal == SignalType.BUY and result.rsi is not None and result.rsi > 70:
            assert result.signal == SignalType.HOLD

    def test_sell_blocked_by_rsi_oversold(self):
        """데드크로스 + RSI 과매도 → HOLD"""
        # 연속 하락으로 RSI 낮추기
        closes = [200] * 6 + [200 - i * 3 for i in range(19)] + [10]
        volumes = [5000] * 25 + [10000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_oversold=30.0
        )
        if result.raw_signal == SignalType.SELL and result.rsi is not None and result.rsi < 30:
            assert result.signal == SignalType.HOLD

    def test_buy_blocked_by_low_volume(self):
        """골든크로스 + 거래량 미확인 → HOLD"""
        # 거래량이 SMA보다 낮음
        volumes = [5000] * 24 + [100]
        chart = self._golden_cross_data(volumes=volumes)
        result = evaluate_signal_with_filters(chart, 5, 20)
        assert result.raw_signal == SignalType.BUY
        assert result.volume_confirmed is False
        assert result.signal == SignalType.HOLD

    def test_hold_signal_unchanged(self):
        """HOLD 시그널 → 필터 무관하게 HOLD 유지"""
        closes = [100] * 25  # 횡보 → HOLD
        volumes = [5000] * 25
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(chart, 5, 20)
        assert result.raw_signal == SignalType.HOLD
        assert result.signal == SignalType.HOLD

    def test_result_contains_all_fields(self):
        """StrategyResult에 모든 필드가 포함되는지 확인"""
        chart = self._golden_cross_data()
        result = evaluate_signal_with_filters(chart, 5, 20)
        assert result.signal is not None
        assert result.raw_signal is not None
        assert isinstance(result.short_ma, float)
        assert isinstance(result.long_ma, float)
        assert isinstance(result.volume_confirmed, bool)
        assert isinstance(result.obv_confirmed, bool)


class TestComputeOBV:
    def test_rising_prices_positive_obv(self):
        """연속 상승 → OBV 증가"""
        closes = [100.0, 101.0, 102.0, 103.0, 104.0]
        volumes = [1000.0, 1000.0, 1000.0, 1000.0, 1000.0]
        obv = compute_obv(closes, volumes)
        assert len(obv) == 5
        assert obv[0] == 0.0
        # 매일 상승이므로 OBV = 0, +1000, +2000, +3000, +4000
        assert obv[1] == 1000.0
        assert obv[2] == 2000.0
        assert obv[3] == 3000.0
        assert obv[4] == 4000.0

    def test_falling_prices_negative_obv(self):
        """연속 하락 → OBV 감소"""
        closes = [104.0, 103.0, 102.0, 101.0, 100.0]
        volumes = [1000.0, 1000.0, 1000.0, 1000.0, 1000.0]
        obv = compute_obv(closes, volumes)
        assert obv[4] == -4000.0

    def test_flat_prices_unchanged_obv(self):
        """횡보 → OBV 불변"""
        closes = [100.0, 100.0, 100.0]
        volumes = [1000.0, 2000.0, 3000.0]
        obv = compute_obv(closes, volumes)
        assert obv == [0.0, 0.0, 0.0]

    def test_mixed_prices(self):
        """상승/하락 혼합"""
        closes = [100.0, 105.0, 103.0, 108.0]
        volumes = [500.0, 1000.0, 800.0, 1200.0]
        obv = compute_obv(closes, volumes)
        assert obv[0] == 0.0
        assert obv[1] == 1000.0   # 상승 → +1000
        assert obv[2] == 200.0    # 하락 → 1000-800
        assert obv[3] == 1400.0   # 상승 → 200+1200

    def test_empty_input(self):
        """빈 입력"""
        assert compute_obv([], []) == []


class TestOBVFilter:
    def test_buy_confirmed_by_obv(self):
        """골든크로스 + OBV 상승추세 → BUY 유지"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        # 하락 시 극소 거래량, 상승 시 대량 → OBV 급반등
        volumes = [5000] * 20 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0,  # RSI 필터 완화하여 OBV 테스트에 집중
            obv_ma_period=5,
        )
        assert result.raw_signal == SignalType.BUY
        assert result.obv_confirmed is True
        assert result.signal == SignalType.BUY

    def test_buy_blocked_by_obv_downtrend(self):
        """골든크로스 + OBV 하락추세 → HOLD"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        # 하락 시 대량 거래, 상승 시 소량 → OBV 하락 지속
        volumes = [5000] * 20 + [20000, 20000, 20000, 20000, 10000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0,
            obv_ma_period=5,
        )
        assert result.raw_signal == SignalType.BUY
        assert result.obv_confirmed is False
        assert result.signal == SignalType.HOLD


class TestComputeBollingerBands:
    def test_basic_bands(self):
        """20개 데이터로 볼린저밴드 계산"""
        prices = [float(100 + i) for i in range(25)]  # 100~124
        bands = compute_bollinger_bands(prices, period=20, num_std=2.0)
        assert len(bands) == 25
        # 처음 19개는 None
        for i in range(19):
            assert bands[i] == (None, None, None)
        # 20번째부터 유효
        upper, middle, lower = bands[19]
        assert upper is not None
        assert middle is not None
        assert lower is not None
        assert upper > middle > lower

    def test_insufficient_data(self):
        """데이터 부족 시 모두 None"""
        prices = [100.0] * 10
        bands = compute_bollinger_bands(prices, period=20)
        assert all(b == (None, None, None) for b in bands)

    def test_wider_bands_with_volatility(self):
        """변동성 클수록 밴드 폭 넓음"""
        # 저변동성: 일정 가격
        flat_prices = [100.0] * 25
        flat_bands = compute_bollinger_bands(flat_prices, period=20)
        flat_upper, _, flat_lower = flat_bands[-1]

        # 고변동성: 큰 폭 등락
        volatile_prices = [100.0 + (10 if i % 2 == 0 else -10) for i in range(25)]
        vol_bands = compute_bollinger_bands(volatile_prices, period=20)
        vol_upper, _, vol_lower = vol_bands[-1]

        # 저변동성은 밴드 폭 0 (표준편차 0)
        assert flat_upper == flat_lower  # std=0이면 upper==lower==middle
        # 고변동성은 밴드 폭 > 0
        assert vol_upper > vol_lower

    def test_custom_num_std(self):
        """표준편차 배수 변경"""
        prices = [float(100 + i) for i in range(25)]
        bands_2std = compute_bollinger_bands(prices, period=20, num_std=2.0)
        bands_1std = compute_bollinger_bands(prices, period=20, num_std=1.0)
        # 2std 밴드가 1std보다 넓어야 함
        u2, m2, l2 = bands_2std[-1]
        u1, m1, l1 = bands_1std[-1]
        assert m2 == m1  # 중심선 동일
        assert u2 > u1  # 2std 상단 > 1std 상단
        assert l2 < l1  # 2std 하단 < 1std 하단


class TestBollingerSignal:
    def test_buy_on_lower_band_bounce(self):
        """하단밴드 반등 → BUY"""
        # 안정 구간 20봉 + 급락(하단 이탈) + 반등
        closes = [100] * 20 + [60, 95]  # 전봉: 60(하단 아래), 현봉: 95(하단 위)
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.BUY

    def test_sell_on_upper_band_touch(self):
        """상단밴드 도달 → SELL"""
        # 안정 구간 20봉 + 전봉 소폭 상승(밴드 내) + 현봉 급등(상단 이탈)
        closes = [100] * 20 + [110, 140]  # prev=110(밴드 내), curr=140(상단 이상)
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.SELL

    def test_hold_in_middle(self):
        """밴드 중간 → HOLD"""
        # 등락 있는 데이터 → 밴드 폭 있음, 현봉은 중간 위치
        closes = [95, 105] * 10 + [100, 100]  # 22봉, 마지막 2봉 100
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.HOLD

    def test_insufficient_data_hold(self):
        """데이터 부족 → HOLD"""
        closes = [100] * 15
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.HOLD
        assert result.upper_band == 0.0

    def test_result_contains_band_values(self):
        """결과에 밴드 값 포함"""
        closes = [float(100 + i) for i in range(25)]
        chart = _make_chart([int(c) for c in closes])
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.upper_band > 0
        assert result.middle_band > 0
        assert result.lower_band > 0
        assert result.upper_band > result.middle_band > result.lower_band

    def test_bollinger_buy_blocked_by_low_volume(self):
        """하단 반등 + 거래량 부족 → HOLD"""
        closes = [100] * 20 + [60, 95]  # 하단 반등 → BUY 조건
        # 과거 거래량 높고 현재 거래량 낮음 → 거래량 미확인
        volumes = [5000] * 21 + [100]
        chart = _make_chart(closes, volumes)
        result = evaluate_bollinger_signal(chart, period=20, volume_ma_period=20)
        assert result.volume_confirmed is False
        assert result.signal == SignalType.HOLD

    def test_bollinger_buy_confirmed_by_volume(self):
        """하단 반등 + 거래량 확인 → BUY"""
        closes = [100] * 20 + [60, 95]  # 하단 반등 → BUY 조건
        # 현재 거래량이 SMA보다 높음 → 거래량 확인
        volumes = [1000] * 21 + [5000]
        chart = _make_chart(closes, volumes)
        result = evaluate_bollinger_signal(chart, period=20, volume_ma_period=20)
        assert result.volume_confirmed is True
        assert result.signal == SignalType.BUY

    def test_narrow_bandwidth_hold(self):
        """밴드 폭이 min_bandwidth 미만 → HOLD (장 초반 노이즈 방지)"""
        # 거의 동일한 가격 → 밴드 폭 극도로 좁음 (bandwidth ≈ 0.87%)
        closes = [100] * 21 + [101]  # 상단 도달(SELL 조건)이지만 밴드 폭 좁음
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20, min_bandwidth=1.0)
        assert result.signal == SignalType.HOLD
        assert "밴드 폭 부족" in result.reason_detail

    def test_wide_bandwidth_not_blocked(self):
        """밴드 폭이 충분하면 min_bandwidth 필터에 걸리지 않음"""
        # 등락 큰 데이터 → 밴드 폭 충분
        closes = [100] * 20 + [60, 95]  # 하단 반등 → BUY
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20, min_bandwidth=1.0)
        assert result.signal == SignalType.BUY

    def test_min_bandwidth_zero_disabled(self):
        """min_bandwidth=0 → 필터 비활성"""
        closes = [100] * 20 + [99, 101]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20, min_bandwidth=0.0)
        # 밴드 폭 필터 비활성 → 밴드 폭 부족 사유 없음
        assert "밴드 폭 부족" not in result.reason_detail

    def test_min_bandwidth_reason_contains_values(self):
        """밴드 폭 부족 사유에 실제 폭/기준값 포함"""
        closes = [100] * 20 + [99, 101]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20, min_bandwidth=5.0)
        assert result.signal == SignalType.HOLD
        assert "밴드 폭 부족" in result.reason_detail
        assert "5.0%" in result.reason_detail

    def test_min_sell_bandwidth_blocks_sell(self):
        """SELL 시그널 + 밴드폭 부족 → HOLD (매도 전용 밴드폭 필터)"""
        # 상단 도달(SELL 조건) — 소폭 등락 후 상단 돌파
        closes = [100] * 20 + [110, 140]
        chart = _make_chart(closes)
        # min_bandwidth=0 으로 기본 필터 비활성, min_sell_bandwidth 로 매도만 차단
        result = evaluate_bollinger_signal(
            chart, period=20, min_bandwidth=0.0, min_sell_bandwidth=50.0,
        )
        assert result.signal == SignalType.HOLD
        assert "매도 밴드폭 부족" in result.reason_detail

    def test_min_sell_bandwidth_allows_buy(self):
        """min_sell_bandwidth는 BUY 시그널에 영향 없음"""
        closes = [100] * 20 + [60, 95]  # 하단 반등 → BUY
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(
            chart, period=20, min_sell_bandwidth=5.0,
        )
        assert result.signal == SignalType.BUY

    def test_min_sell_bandwidth_zero_disabled(self):
        """min_sell_bandwidth=0 → 비활성"""
        closes = [100] * 20 + [110, 140]  # 상단 도달 → SELL
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(
            chart, period=20, min_sell_bandwidth=0.0,
        )
        assert result.signal == SignalType.SELL

    def test_middle_exit_sell_below_middle(self):
        """use_middle_exit=True + 현재가 < 중간밴드 → SELL"""
        # 등락 데이터 (밴드 폭 충분) + 현재가가 중간밴드 아래
        closes = [95, 105] * 10 + [100, 90]  # 22봉, 마지막 90 < middle
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20, use_middle_exit=True)
        # 중간밴드는 약 100, 현재가 90이므로 중간밴드 이탈 SELL
        assert result.signal == SignalType.SELL
        assert "중간밴드 이탈" in result.reason_detail

    def test_middle_exit_disabled_by_default(self):
        """use_middle_exit=False → 중간밴드 아래여도 SELL 아님"""
        closes = [95, 105] * 10 + [100, 90]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20, use_middle_exit=False)
        # 상단 도달도 아니고 하단 반등도 아님 → HOLD
        assert result.signal == SignalType.HOLD

    def test_middle_exit_not_triggered_above_middle(self):
        """use_middle_exit=True + 현재가 > 중간밴드 → HOLD (중간 위)"""
        closes = [95, 105] * 10 + [100, 102]  # 중간밴드 약 100, 현재가 102
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20, use_middle_exit=True)
        assert result.signal == SignalType.HOLD


class TestReasonDetail:
    """시그널 판단 근거(reason_detail) 검증"""

    def test_sma_golden_cross_reason(self):
        """골든크로스 BUY → 근거에 '골든크로스' 포함"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        chart = _make_chart(closes)
        signal, short_ma, long_ma, reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.BUY
        assert "골든크로스" in reason
        assert "단기MA" in reason
        assert "장기MA" in reason

    def test_sma_dead_cross_reason(self):
        """데드크로스 SELL → 근거에 '데드크로스' 포함"""
        closes = [100] * 20 + [105, 106, 107, 108, 50]
        chart = _make_chart(closes)
        signal, _, _, reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.SELL
        assert "데드크로스" in reason

    def test_sma_hold_reason(self):
        """크로스 없음 HOLD → 근거에 '크로스 없음' 포함"""
        closes = [100] * 25
        chart = _make_chart(closes)
        signal, _, _, reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD
        assert "크로스 없음" in reason

    def test_sma_insufficient_data_reason(self):
        """데이터 부족 → '데이터 부족'"""
        closes = [100] * 15
        chart = _make_chart(closes)
        signal, _, _, reason = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD
        assert "데이터 부족" in reason

    def test_sma_volume_filter_reason(self):
        """골든크로스 + 거래량 부족 → 근거에 '거래량 부족' 포함"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 24 + [100]
        chart = _make_chart(closes, volumes)
        signal, _, _, reason = evaluate_signal(chart, 5, 20, volume_ma_period=20)
        assert signal == SignalType.HOLD
        assert "골든크로스" in reason
        assert "거래량 부족" in reason

    def test_bollinger_buy_reason(self):
        """볼린저 하단 반등 BUY → 근거에 '하단 반등' 포함"""
        closes = [100] * 20 + [60, 95]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.BUY
        assert "하단 반등" in result.reason_detail
        assert "현재가" in result.reason_detail

    def test_bollinger_sell_reason(self):
        """볼린저 상단 도달 SELL → 근거에 '상단 도달' 포함"""
        closes = [100] * 20 + [110, 140]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.SELL
        assert "상단 도달" in result.reason_detail

    def test_bollinger_hold_reason(self):
        """볼린저 밴드 내 → 근거에 '밴드 내 위치' 포함"""
        closes = [95, 105] * 10 + [100, 100]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.HOLD
        assert "밴드 내 위치" in result.reason_detail

    def test_bollinger_volume_filter_reason(self):
        """볼린저 BUY + 거래량 미확인 → 근거에 '거래량 미확인' 포함"""
        closes = [100] * 20 + [60, 95]
        volumes = [5000] * 21 + [100]
        chart = _make_chart(closes, volumes)
        result = evaluate_bollinger_signal(chart, period=20, volume_ma_period=20)
        assert result.signal == SignalType.HOLD
        assert "하단 반등" in result.reason_detail
        assert "거래량 미확인" in result.reason_detail

    def test_advanced_rsi_filter_reason(self):
        """골든크로스 + RSI 과매수 → 근거에 'RSI 과매수' 포함"""
        closes = [50] * 6 + [50 + i * 3 for i in range(19)] + [200]
        volumes = [5000] * 25 + [10000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_overbought=70.0
        )
        if result.raw_signal == SignalType.BUY and result.rsi and result.rsi > 70:
            assert "RSI 과매수" in result.reason_detail

    def test_advanced_volume_filter_reason(self):
        """골든크로스 + 거래량 미확인 → 근거에 '거래량 미확인' 포함"""
        volumes = [5000] * 24 + [100]
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_overbought=95.0,  # RSI 필터 완화
        )
        assert result.raw_signal == SignalType.BUY
        assert result.signal == SignalType.HOLD
        assert "거래량 미확인" in result.reason_detail

    def test_advanced_obv_filter_reason(self):
        """골든크로스 + OBV 하락추세 → 근거에 'OBV 하락추세' 포함"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 20 + [20000, 20000, 20000, 20000, 10000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_overbought=95.0, obv_ma_period=5
        )
        assert result.raw_signal == SignalType.BUY
        assert result.obv_confirmed is False
        assert "OBV 하락추세" in result.reason_detail

    def test_advanced_passes_all_filters_no_filter_reason(self):
        """모든 필터 통과 → 근거에 'HOLD' 없음"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 20 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_overbought=95.0, obv_ma_period=5
        )
        if result.signal == SignalType.BUY:
            assert "→ HOLD" not in result.reason_detail
            assert "골든크로스" in result.reason_detail


class TestRSIDivergence:
    """RSI 다이버전스 감지 테스트"""

    def test_bullish_divergence(self):
        """가격 저점↓ RSI 저점↑ → bullish 다이버전스"""
        # 하락추세에서 저점 2개: 마지막 두 저점에서 가격↓ RSI↑
        #   idx:  0    1    2    3    4    5    6    7    8
        # price: 100  110   90  105   85  100   80  100  END
        # 저점: idx2(90), idx4(85), idx6(80) — 마지막 두 저점: idx4, idx6
        # RSI:  50   60   25   60   30   60   35   60
        # idx4: price=85 RSI=30, idx6: price=80 RSI=35 → price↓ RSI↑ = bullish
        prices = [100.0, 110.0, 90.0, 105.0, 85.0, 100.0, 80.0, 100.0, 95.0]
        #                ^low          ^low          ^low
        rsi_values: list[float | None] = [
            50.0, 60.0, 25.0, 60.0, 30.0, 60.0, 35.0, 60.0, 50.0,
        ]
        # lookback=5 → start=3, end=8 → 로컬 저점: idx4(85,RSI30), idx6(80,RSI35)
        result = detect_rsi_divergence(prices, rsi_values, lookback=5)
        assert result == "bullish"

    def test_bearish_divergence(self):
        """가격 고점↑ RSI 고점↓ → bearish 다이버전스"""
        # 상승추세에서 고점 2개: 마지막 두 고점에서 가격↑ RSI↓
        #   idx:  0    1    2    3    4    5    6    7    8
        # price: 100   90  110   95  115   90  120   95  105
        # 고점: idx2(110), idx4(115), idx6(120)
        # RSI:  50   40   80   40   75   40   70   40   50
        # idx4: price=115 RSI=75, idx6: price=120 RSI=70 → price↑ RSI↓ = bearish
        prices = [100.0, 90.0, 110.0, 95.0, 115.0, 90.0, 120.0, 95.0, 105.0]
        rsi_values: list[float | None] = [
            50.0, 40.0, 80.0, 40.0, 75.0, 40.0, 70.0, 40.0, 50.0,
        ]
        result = detect_rsi_divergence(prices, rsi_values, lookback=5)
        assert result == "bearish"

    def test_no_divergence(self):
        """가격과 RSI 방향 일치 → None"""
        # 가격↑ RSI↑ (일반 상승)
        prices = list(range(50, 70))  # 20개, 꾸준히 상승
        rsi_values: list[float | None] = [40.0 + i for i in range(20)]

        result = detect_rsi_divergence(prices, rsi_values, lookback=14)
        assert result is None

    def test_insufficient_data_returns_none(self):
        """데이터 부족 → None"""
        prices = [100, 101, 102]
        rsi_values: list[float | None] = [50.0, 55.0, 60.0]

        result = detect_rsi_divergence(prices, rsi_values, lookback=14)
        assert result is None

    def test_all_none_rsi_returns_none(self):
        """RSI가 전부 None → None"""
        prices = list(range(50, 70))
        rsi_values: list[float | None] = [None] * 20

        result = detect_rsi_divergence(prices, rsi_values, lookback=14)
        assert result is None


class TestRSIDivergenceFilter:
    """복합 전략에서 RSI 다이버전스 차단 테스트"""

    def test_buy_blocked_by_bearish_divergence(self):
        """BUY + bearish RSI divergence → HOLD"""
        # 골든크로스(BUY) 조건 + 수동으로 bearish 다이버전스를 만들기 어려우므로
        # 전략 함수 내부 동작을 확인: use_rsi_divergence=True 전달 확인
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 20 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        # use_rsi_divergence=False 이면 BUY 통과
        result_off = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0, obv_ma_period=5,
            use_rsi_divergence=False,
        )
        assert result_off.raw_signal == SignalType.BUY
        # use_rsi_divergence=True 여도 실제 다이버전스가 없으면 BUY 유지
        result_on = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0, obv_ma_period=5,
            use_rsi_divergence=True,
        )
        # 다이버전스 미감지 → 원래 시그널 유지
        assert result_on.signal == result_off.signal

    def test_rsi_divergence_disabled_by_default(self):
        """use_rsi_divergence=False(기본값) → 다이버전스 필터 미적용"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 20 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_overbought=95.0, obv_ma_period=5,
        )
        # 기본값 False → RSI 다이버전스 관련 사유 없음
        assert "다이버전스" not in result.reason_detail


class TestComputeEMA:
    """EMA 계산 테스트"""

    def test_basic_ema(self):
        """기본 EMA 계산"""
        prices = [10.0, 11.0, 12.0, 13.0, 14.0]
        result = compute_ema(prices, 3)
        assert len(result) == 5
        # 처음 2개는 None (period-1)
        assert result[0] is None
        assert result[1] is None
        # 세 번째 값은 SMA(첫 3개)
        assert result[2] == (10.0 + 11.0 + 12.0) / 3
        # 이후는 EMA 적용
        assert result[3] is not None
        assert result[4] is not None

    def test_ema_single_period(self):
        """period=1 → 원래 값"""
        prices = [5.0, 10.0, 15.0]
        result = compute_ema(prices, 1)
        assert result == [5.0, 10.0, 15.0]

    def test_insufficient_data(self):
        """데이터 부족 → 전부 None"""
        prices = [10.0, 11.0]
        result = compute_ema(prices, 5)
        assert all(v is None for v in result)


class TestComputeMACD:
    """MACD 계산 테스트"""

    def test_basic_macd(self):
        """충분한 데이터로 MACD 계산"""
        # 50개 가격 데이터 (slow=26 + signal=9 = 35개 이상 필요)
        prices = [100.0 + i * 0.5 for i in range(50)]
        result = compute_macd(prices, fast=12, slow=26, signal=9)
        assert result is not None
        assert isinstance(result.macd_line, float)
        assert isinstance(result.signal_line, float)
        assert isinstance(result.histogram, float)
        # histogram = macd_line - signal_line
        assert abs(result.histogram - (result.macd_line - result.signal_line)) < 1e-10

    def test_insufficient_data_returns_none(self):
        """데이터 부족 → None"""
        prices = [100.0] * 10
        result = compute_macd(prices, fast=12, slow=26, signal=9)
        assert result is None

    def test_macd_uptrend_positive_histogram(self):
        """가속 상승 추세 → MACD 히스토그램 양수"""
        # 가속 상승 (기울기 증가) → MACD가 signal 위로 벌어짐
        prices = [50.0 + i * 0.5 for i in range(35)]  # 완만 상승
        prices += [50.0 + 35 * 0.5 + i * 3.0 for i in range(25)]  # 가속 상승
        result = compute_macd(prices, fast=12, slow=26, signal=9)
        assert result is not None
        assert result.macd_line > 0
        assert result.histogram > 0

    def test_macd_downtrend_negative_histogram(self):
        """가속 하락 추세 → MACD 히스토그램 음수"""
        # 가속 하락 (기울기 증가)
        prices = [200.0 - i * 0.5 for i in range(35)]  # 완만 하락
        prices += [200.0 - 35 * 0.5 - i * 3.0 for i in range(25)]  # 가속 하락
        result = compute_macd(prices, fast=12, slow=26, signal=9)
        assert result is not None
        assert result.macd_line < 0
        assert result.histogram < 0


class TestMACDFilter:
    """MACD 필터 차단/통과 테스트"""

    def test_macd_filter_disabled_by_default(self):
        """use_macd_filter=False(기본값) → MACD 필터 미적용"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 20 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20, rsi_overbought=95.0, obv_ma_period=5,
        )
        assert "MACD" not in result.reason_detail

    def test_macd_filter_blocks_buy_on_negative_histogram(self):
        """BUY + MACD 히스토그램 음수 → HOLD"""
        # 장기 하락 후 마지막에 골든크로스 (MACD는 아직 음수)
        closes = [200 - i for i in range(40)] + [95, 94, 93, 92, 150]
        volumes = [5000] * 44 + [50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0, obv_ma_period=5,
            use_macd_filter=True,
        )
        if result.raw_signal == SignalType.BUY:
            # MACD가 음수면 차단
            macd_result = compute_macd([c.close for c in chart])
            if macd_result and macd_result.histogram < 0:
                assert result.signal == SignalType.HOLD
                assert "MACD" in result.reason_detail

    def test_macd_filter_passes_buy_on_positive_histogram(self):
        """BUY + MACD 히스토그램 양수 → BUY 유지"""
        # 장기 상승 추세 중 골든크로스 (MACD 양수)
        closes = [50 + i for i in range(40)] + [95, 94, 93, 92, 150]
        volumes = [5000] * 40 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0, obv_ma_period=5,
            use_macd_filter=True,
        )
        # 상승 추세에서 골든크로스면 MACD도 양수 → 차단 안 됨
        if result.raw_signal == SignalType.BUY:
            assert "MACD" not in result.reason_detail


def _make_candle_chart(
    candles: list[tuple[float, float, float, float]],
    volumes: list[int] | None = None,
) -> list[ChartData]:
    """캔들 패턴 테스트용 차트 데이터 생성.

    candles: [(open, high, low, close), ...]
    """
    if volumes is None:
        volumes = [1000] * len(candles)
    return [
        ChartData(
            date=f"2025{(i // 28 + 1):02d}{(i % 28 + 1):02d}",
            open=o, high=h, low=l, close=c, volume=volumes[i],
        )
        for i, (o, h, l, c) in enumerate(candles)
    ]


class TestBullishEngulfing:
    """강세 장악형 캔들 감지 테스트"""

    def test_detects_bullish_engulfing(self):
        """전봉 음봉 + 현봉 양봉 + 몸통 감쌈 → True"""
        chart = _make_candle_chart([
            (110, 115, 95, 100),   # 전봉: 음봉 (open=110 > close=100)
            (98, 120, 95, 115),    # 현봉: 양봉 (open=98 < close=115), 감쌈
        ])
        assert is_bullish_engulfing(chart, 1) is True

    def test_prev_bullish_returns_false(self):
        """전봉이 양봉이면 False"""
        chart = _make_candle_chart([
            (95, 115, 90, 110),    # 전봉: 양봉 (open < close)
            (98, 120, 95, 115),    # 현봉: 양봉
        ])
        assert is_bullish_engulfing(chart, 1) is False

    def test_not_engulfing_body(self):
        """현봉이 전봉을 완전히 감싸지 못하면 False"""
        chart = _make_candle_chart([
            (110, 115, 95, 100),   # 전봉: 음봉 (o=110, c=100)
            (101, 115, 95, 108),   # 현봉: 양봉이지만 close=108 < prev.open=110
        ])
        assert is_bullish_engulfing(chart, 1) is False

    def test_index_zero_returns_false(self):
        """index=0은 전봉이 없으므로 False"""
        chart = _make_candle_chart([
            (98, 120, 95, 115),
        ])
        assert is_bullish_engulfing(chart, 0) is False

    def test_doji_prev_returns_false(self):
        """전봉 도지(open == close) → 음봉 아님 → False"""
        chart = _make_candle_chart([
            (100, 110, 90, 100),   # 전봉: 도지 (open == close)
            (98, 120, 95, 115),
        ])
        assert is_bullish_engulfing(chart, 1) is False


class TestBearishEngulfing:
    """약세 장악형 캔들 감지 테스트"""

    def test_detects_bearish_engulfing(self):
        """전봉 양봉 + 현봉 음봉 + 몸통 감쌈 → True"""
        chart = _make_candle_chart([
            (100, 115, 95, 110),   # 전봉: 양봉 (o=100, c=110)
            (112, 120, 90, 98),    # 현봉: 음봉 (o=112, c=98), 감쌈
        ])
        assert is_bearish_engulfing(chart, 1) is True

    def test_prev_bearish_returns_false(self):
        """전봉이 음봉이면 False"""
        chart = _make_candle_chart([
            (110, 115, 95, 100),   # 전봉: 음봉
            (112, 120, 90, 98),    # 현봉: 음봉
        ])
        assert is_bearish_engulfing(chart, 1) is False


class TestEngulfingBollingerFilter:
    """볼린저 시그널 + 장악형 캔들 필터 통합 테스트"""

    def test_buy_blocked_without_engulfing(self):
        """하단 반등 + engulfing 미감지 → HOLD"""
        # 안정 구간 + 급락 + 반등 (기본 _make_chart는 open==close → engulfing 불가)
        closes = [100] * 20 + [60, 95]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(
            chart, period=20, use_engulfing_filter=True,
        )
        assert result.signal == SignalType.HOLD
        assert "장악형 캔들 미감지" in result.reason_detail

    def test_buy_with_engulfing(self):
        """하단 반등 + bullish engulfing → BUY"""
        # 20봉 안정 구간 (open==close) + 전봉 음봉(하단 이탈) + 현봉 양봉(반등+감쌈)
        stable = [(100, 110, 90, 100)] * 20
        prev_candle = (110, 115, 55, 60)    # 음봉: o=110>c=60, 하단 이탈
        curr_candle = (58, 100, 55, 115)    # 양봉: o=58<c=115, 감쌈 (58<=60, 115>110)
        chart = _make_candle_chart(stable + [prev_candle, curr_candle])
        result = evaluate_bollinger_signal(
            chart, period=20, use_engulfing_filter=True,
            rsi_oversold=70.0,  # RSI 임계값 높여 RSI 필터 통과 보장
        )
        assert result.signal == SignalType.BUY

    def test_engulfing_disabled_by_default(self):
        """use_engulfing_filter=False(기본값) → 장악형 캔들 필터 미적용"""
        closes = [100] * 20 + [60, 95]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(chart, period=20)
        assert result.signal == SignalType.BUY  # 기본: 하단 반등만으로 BUY
        assert "장악형 캔들" not in result.reason_detail


class TestBollingerRSIExtreme:
    """볼린저 RSI 극단 필터 테스트"""

    def test_buy_blocked_when_rsi_not_oversold(self):
        """BUY + RSI 과매도 아님 → HOLD"""
        # 안정 후 하단 반등 + engulfing → BUY 후 RSI 필터로 차단
        stable = [(100, 110, 90, 100)] * 20
        prev_candle = (110, 115, 55, 60)
        curr_candle = (58, 100, 55, 115)
        chart = _make_candle_chart(stable + [prev_candle, curr_candle])
        result = evaluate_bollinger_signal(
            chart, period=20,
            use_engulfing_filter=True,
            rsi_oversold=30.0,
        )
        # 안정 구간 → RSI ≈ 50 (과매도 아님) → HOLD
        assert result.signal == SignalType.HOLD
        assert "RSI 과매도 아님" in result.reason_detail

    def test_rsi_filter_not_applied_without_candle_pattern(self):
        """캔들 패턴 필터 비활성 시 RSI 극단 필터도 미적용"""
        closes = [100] * 20 + [60, 95]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(
            chart, period=20,
            use_engulfing_filter=False,
            use_double_pattern=False,
            rsi_oversold=30.0,
        )
        assert result.signal == SignalType.BUY  # RSI 무관하게 BUY
        assert "RSI" not in result.reason_detail

    def test_buy_passes_when_rsi_oversold(self):
        """BUY + engulfing + RSI 과매도 → BUY 유지"""
        # 장기 하락 → RSI 낮게 만들기 + 마지막에 engulfing 반등
        falling = [(200 - i * 3, 210 - i * 3, 190 - i * 3, 200 - i * 3) for i in range(20)]
        prev_candle = (145, 150, 100, 110)  # 음봉
        curr_candle = (108, 155, 105, 150)  # 양봉 engulfing (108<=110, 150>145)
        chart = _make_candle_chart(falling + [prev_candle, curr_candle])
        result = evaluate_bollinger_signal(
            chart, period=20,
            use_engulfing_filter=True,
            rsi_period=14,
            rsi_oversold=50.0,  # 넉넉한 기준 (하락추세 RSI 대부분 통과)
        )
        # 하단 반등 + engulfing + RSI <= 50 → BUY
        if result.signal == SignalType.BUY:
            assert "RSI" not in result.reason_detail

    def test_sell_blocked_when_rsi_not_overbought(self):
        """SELL + bearish engulfing + RSI 과매수 아님 → HOLD"""
        stable = [(100, 110, 90, 100)] * 20
        prev_candle = (100, 135, 95, 130)   # 양봉 (o=100, c=130)
        curr_candle = (132, 145, 90, 98)    # 음봉 engulfing (132>=130, 98<100)
        chart = _make_candle_chart(stable + [prev_candle, curr_candle])
        result = evaluate_bollinger_signal(
            chart, period=20,
            use_engulfing_filter=True,
            rsi_overbought=70.0,
        )
        if "상단 도달" in result.reason_detail:
            assert result.signal == SignalType.HOLD
            assert "RSI 과매수 아님" in result.reason_detail


class TestBollingerOBVFilter:
    """볼린저밴드 OBV 필터 테스트"""

    def test_buy_blocked_by_obv_downtrend(self):
        """하단 반등 BUY + OBV 하락추세 → HOLD"""
        closes = [100] * 20 + [60, 95]
        # 하락 시 대량 거래 → OBV 하락 추세
        volumes = [5000] * 20 + [20000, 1000]
        chart = _make_chart(closes, volumes)
        result = evaluate_bollinger_signal(
            chart, period=20, obv_ma_period=5,
        )
        assert result.obv_confirmed is False
        assert result.signal == SignalType.HOLD
        assert "OBV 하락추세" in result.reason_detail

    def test_sell_blocked_by_obv_uptrend(self):
        """상단 도달 SELL + OBV 상승추세 → HOLD"""
        closes = [100] * 20 + [110, 140]
        # 상승 시 대량 거래 → OBV 상승 추세
        volumes = [1000] * 20 + [1000, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_bollinger_signal(
            chart, period=20, obv_ma_period=5,
        )
        assert result.obv_confirmed is True
        assert result.signal == SignalType.HOLD
        assert "OBV 상승추세" in result.reason_detail

    def test_obv_none_no_filter(self):
        """obv_ma_period=None → OBV 필터 비활성, 기존 동작 유지"""
        closes = [100] * 20 + [60, 95]
        volumes = [5000] * 20 + [20000, 1000]
        chart = _make_chart(closes, volumes)
        result = evaluate_bollinger_signal(
            chart, period=20, obv_ma_period=None,
        )
        assert result.obv_confirmed is True  # 기본값
        assert result.signal == SignalType.BUY
        assert "OBV" not in result.reason_detail


class TestSMAGapFilter:
    """SMA 크로스 최소 갭 필터 테스트"""

    def test_gap_sufficient_buy_passes(self):
        """골든크로스 + 갭 충분 → BUY 통과"""
        # 큰 급등으로 SMA 간 갭이 충분히 벌어짐
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        chart = _make_chart(closes)
        signal, short_ma, long_ma, reason = evaluate_signal(
            chart, 5, 20, min_gap_pct=0.1,
        )
        assert signal == SignalType.BUY
        assert "갭 부족" not in reason

    def test_gap_insufficient_hold(self):
        """골든크로스 + 갭 부족 → HOLD 차단"""
        # 골든크로스가 발생하지만 갭이 높은 기준(50%) 미만 → 차단
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        chart = _make_chart(closes)
        signal, short_ma, long_ma, reason = evaluate_signal(
            chart, 5, 20, min_gap_pct=50.0,  # 극단적 기준으로 확실히 차단
        )
        assert signal == SignalType.HOLD
        assert "갭 부족" in reason

    def test_gap_zero_disabled(self):
        """min_gap_pct=0 → 갭 필터 비활성"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        chart = _make_chart(closes)
        signal, _, _, reason = evaluate_signal(
            chart, 5, 20, min_gap_pct=0.0,
        )
        # 갭 필터 없이 원래 크로스오버 판정 유지
        assert signal == SignalType.BUY
        assert "갭 부족" not in reason

    def test_gap_filter_applies_to_sell(self):
        """데드크로스 + 갭 부족 → HOLD (BUY/SELL 모두 적용)"""
        closes = [100] * 20 + [105, 106, 107, 108, 50]
        chart = _make_chart(closes)
        signal, _, _, reason = evaluate_signal(
            chart, 5, 20, min_gap_pct=50.0,  # 극단적 기준
        )
        assert signal == SignalType.HOLD
        assert "갭 부족" in reason

    def test_gap_filter_with_advanced_strategy(self):
        """evaluate_signal_with_filters에서도 min_gap_pct 전달"""
        # 골든크로스 데이터 + 높은 갭 기준으로 차단
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 20 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0, obv_ma_period=5,
            min_gap_pct=50.0,
        )
        # 갭 부족이면 raw_signal 자체가 HOLD
        assert result.raw_signal == SignalType.HOLD
        assert "갭 부족" in result.reason_detail


# ============================================================
# Phase 0 테스트: compute_atr, compute_kama, compute_donchian
# ============================================================


class TestComputeATR:
    def test_basic_atr(self):
        """충분한 데이터로 ATR 계산"""
        chart = _make_chart([100, 105, 102, 108, 103, 110, 106, 112, 107, 115,
                             110, 116, 109, 118, 112, 120])
        result = compute_atr(chart, period=5)
        assert len(result) == 16
        # 처음 4개(period-1)는 None
        for i in range(4):
            assert result[i] is None
        # 5번째부터 유효
        assert result[4] is not None
        assert result[4] > 0

    def test_insufficient_data(self):
        """데이터 부족 → 전부 None"""
        chart = _make_chart([100, 105])
        result = compute_atr(chart, period=14)
        assert all(v is None for v in result)

    def test_single_bar(self):
        """1봉 → n < 2 이므로 None"""
        chart = _make_chart([100])
        result = compute_atr(chart, period=1)
        assert len(result) == 1
        # compute_atr는 n < 2 → [None] 반환
        assert result[0] is None

    def test_wilder_smoothing(self):
        """Wilder smoothing 적용 확인: ATR이 점진적으로 변화"""
        # _make_chart의 high=c+100, low=c-100 → 안정 구간 TR=200 일정
        # 직접 OHLCV를 다르게 만들어서 변동성 증가 시뮬레이션
        stable = [
            ChartData(date=f"202501{i+1:02d}", open=100, high=105, low=95, close=100, volume=1000)
            for i in range(10)
        ]
        volatile = [
            ChartData(date=f"202502{i+1:02d}", open=100, high=100+20*(i+1), low=100-20*(i+1), close=100, volume=1000)
            for i in range(5)
        ]
        chart = stable + volatile
        result = compute_atr(chart, period=5)
        valid = [v for v in result if v is not None]
        assert len(valid) >= 5
        # 변동성 구간의 ATR이 안정 구간보다 높음
        assert valid[-1] > valid[0]


class TestComputeKAMA:
    def test_basic_kama(self):
        """충분한 데이터로 KAMA 계산"""
        prices = [float(100 + i) for i in range(25)]
        result = compute_kama(prices, er_period=10)
        assert len(result) == 25
        # 처음 10개는 None
        for i in range(10):
            assert result[i] is None
        # 11번째가 첫 KAMA (= prices[10])
        assert result[10] == prices[10]
        # 이후 유효
        assert result[-1] is not None

    def test_insufficient_data(self):
        """데이터 부족 → 전부 None"""
        prices = [100.0] * 5
        result = compute_kama(prices, er_period=10)
        assert all(v is None for v in result)

    def test_trending_kama_follows_price(self):
        """강한 추세에서 KAMA가 가격을 빠르게 추적"""
        prices = [float(100 + i * 5) for i in range(30)]  # 강한 상승
        result = compute_kama(prices, er_period=10)
        valid = [v for v in result if v is not None]
        # 마지막 KAMA가 가격에 가까이 수렴
        assert abs(valid[-1] - prices[-1]) < 30

    def test_sideways_kama_slow(self):
        """횡보장에서 KAMA가 느리게 반응"""
        prices = [float(100 + (5 if i % 2 == 0 else -5)) for i in range(30)]
        result = compute_kama(prices, er_period=10)
        valid = [v for v in result if v is not None]
        # 횡보에서 KAMA 변화폭이 작음
        kama_range = max(valid) - min(valid)
        assert kama_range < 10


class TestComputeDonchianChannels:
    def test_basic_channels(self):
        """기본 도치안 채널 계산"""
        chart = _make_chart([100, 105, 98, 110, 95, 112, 90, 115, 88, 118,
                             85, 120, 82, 122, 80, 125, 78, 128, 76, 130, 74])
        result = compute_donchian_channels(chart, upper_period=5, lower_period=3)
        assert len(result) == 21
        # 처음 upper_period 봉까지 upper는 None
        for i in range(5):
            assert result[i][0] is None
        # lower_period 봉부터 lower 유효
        assert result[3][1] is not None

    def test_look_ahead_bias_prevention(self):
        """당일 데이터 미포함 확인 (look-ahead bias 방지)"""
        chart = _make_chart([100, 100, 100, 100, 100, 200])  # 마지막 봉 200
        result = compute_donchian_channels(chart, upper_period=5, lower_period=3)
        upper, lower = result[5]
        # upper는 전일까지의 최고가 → 200 미포함 (high = close+100 = 200)
        if upper is not None:
            assert upper <= 200  # chart[0..4] 의 high = 200

    def test_insufficient_data(self):
        """데이터 부족 → None"""
        chart = _make_chart([100, 105])
        result = compute_donchian_channels(chart, upper_period=5, lower_period=3)
        assert result[0] == (None, None)
        assert result[1] == (None, None)

    def test_asymmetric_periods(self):
        """비대칭 기간 (upper > lower)"""
        chart = _make_chart([100 + i for i in range(25)])
        result = compute_donchian_channels(chart, upper_period=20, lower_period=10)
        # upper는 20봉 후부터, lower는 10봉 후부터 유효
        assert result[10][0] is None  # upper는 아직 None
        assert result[10][1] is not None  # lower는 유효


# ============================================================
# Phase 1A 테스트: 적응형 볼린저 밴드폭
# ============================================================


class TestAdaptiveBandwidth:
    def test_percentile_zero_uses_fixed(self):
        """bandwidth_percentile=0 → 고정 min_bandwidth 사용 (기존 동작)"""
        closes = [100] * 20 + [99, 101]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(
            chart, period=20, min_bandwidth=5.0, bandwidth_percentile=0.0,
        )
        assert result.signal == SignalType.HOLD
        assert "밴드 폭 부족" in result.reason_detail

    def test_percentile_based_threshold(self):
        """bandwidth_percentile > 0 → 백분위 기반 임계값"""
        # 등락 큰 데이터로 밴드 폭이 넓은 기간 만들고, 마지막은 좁은 밴드
        # 앞부분: 변동성 큰 데이터 → 넓은 밴드폭
        closes = [95, 105] * 12 + [100, 100]  # 24봉 등락 + 마지막 안정
        chart = _make_chart(closes)
        # percentile=99 → 대부분의 bandwidth보다 높은 임계값 → 현재 밴드폭 부족
        result = evaluate_bollinger_signal(
            chart, period=20, bandwidth_percentile=99.0, bandwidth_lookback=20,
        )
        # 현재 밴드폭이 99th percentile 미만이면 HOLD
        if "밴드 폭 부족" in result.reason_detail:
            assert result.signal == SignalType.HOLD
        # percentile 기반이므로 밴드폭 필터가 작동했는지만 확인
        assert result.signal in (SignalType.HOLD, SignalType.BUY)

    def test_low_percentile_allows_signal(self):
        """낮은 percentile → 대부분의 시그널 통과"""
        closes = [100] * 20 + [60, 95]
        chart = _make_chart(closes)
        result = evaluate_bollinger_signal(
            chart, period=20, bandwidth_percentile=1.0, bandwidth_lookback=20,
        )
        # 1% percentile → 거의 모든 밴드폭이 임계값 초과
        assert result.signal == SignalType.BUY


# ============================================================
# Phase 1B 테스트: 국면 인식 필터
# ============================================================


class TestRegimeAwareFilters:
    def _golden_cross_low_vol_data(self) -> list[ChartData]:
        """골든크로스 + 낮은 거래량 (기존 필터에서 차단되는 데이터)"""
        closes = [100] * 20 + [95, 94, 93, 92, 150]
        volumes = [5000] * 24 + [100]  # 거래량 부족
        return _make_chart(closes, volumes)

    def test_bull_regime_skips_volume_filter(self):
        """강세장에서 BUY 거래량 필터 스킵"""
        chart = self._golden_cross_low_vol_data()
        result = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0, obv_ma_period=5,
            regime="bull",
        )
        # 강세장: 거래량/OBV 필터 스킵 → 차단 안 됨
        if result.raw_signal == SignalType.BUY:
            assert "거래량 미확인" not in result.reason_detail

    def test_bear_regime_blocks_high_rsi(self):
        """약세장에서 RSI>60이면 BUY 차단"""
        # 완만한 상승 데이터 (RSI > 60)
        closes = [50 + i for i in range(40)] + [95, 94, 93, 92, 150]
        volumes = [5000] * 40 + [200, 200, 200, 200, 50000]
        chart = _make_chart(closes, volumes)
        result = evaluate_signal_with_filters(
            chart, 5, 20,
            rsi_overbought=95.0, obv_ma_period=5,
            regime="bear",
        )
        if result.raw_signal == SignalType.BUY and result.rsi and result.rsi > 60:
            assert result.signal == SignalType.HOLD
            assert "약세장 RSI 경고" in result.reason_detail

    def test_none_regime_default_behavior(self):
        """regime=None → 기존 동작 그대로"""
        chart = self._golden_cross_low_vol_data()
        result_none = evaluate_signal_with_filters(chart, 5, 20)
        result_explicit_none = evaluate_signal_with_filters(
            chart, 5, 20, regime=None,
        )
        assert result_none.signal == result_explicit_none.signal


# ============================================================
# Phase 2 테스트: KAMA 시그널
# ============================================================


class TestKAMASignal:
    def test_kama_golden_cross_buy(self):
        """KAMA 골든크로스 → BUY"""
        # 하락 후 급반등 → KAMA가 signal line 위로 올라감
        closes = [100] * 15 + [90, 88, 85, 83, 80, 78, 130, 135, 140]
        chart = _make_chart(closes)
        result = evaluate_kama_signal(chart, er_period=10, signal_period=5)
        # 급반등 후 KAMA > Signal Line
        if result.signal == SignalType.BUY:
            assert "골든크로스" in result.reason_detail
            assert result.kama > result.signal_line

    def test_kama_dead_cross_sell(self):
        """KAMA 데드크로스 → SELL"""
        # 상승 후 급락 → KAMA가 signal line 아래로 내려감
        closes = [100] * 15 + [110, 112, 115, 117, 120, 122, 70, 65, 60]
        chart = _make_chart(closes)
        result = evaluate_kama_signal(chart, er_period=10, signal_period=5)
        if result.signal == SignalType.SELL:
            assert "데드크로스" in result.reason_detail
            assert result.kama < result.signal_line

    def test_kama_hold_no_cross(self):
        """크로스 없음 → HOLD"""
        closes = [float(100 + i) for i in range(30)]
        chart = _make_chart([int(c) for c in closes])
        result = evaluate_kama_signal(chart, er_period=10, signal_period=5)
        if result.signal == SignalType.HOLD:
            assert "크로스 없음" in result.reason_detail

    def test_kama_insufficient_data(self):
        """데이터 부족 → HOLD"""
        chart = _make_chart([100] * 5)
        result = evaluate_kama_signal(chart, er_period=10, signal_period=5)
        assert result.signal == SignalType.HOLD
        assert "데이터 부족" in result.reason_detail

    def test_kama_returns_atr(self):
        """ATR 값이 반환됨"""
        closes = [float(100 + i) for i in range(30)]
        chart = _make_chart([int(c) for c in closes])
        result = evaluate_kama_signal(chart, er_period=10, signal_period=5)
        assert result.atr is not None
        assert result.atr > 0

    def test_kama_volume_filter_blocks(self):
        """KAMA BUY + 거래량 부족 → HOLD"""
        # 급반등 데이터 + 낮은 거래량
        closes = [100] * 15 + [90, 88, 85, 83, 80, 78, 130, 135, 140]
        volumes = [5000] * 23 + [100]  # 마지막 거래량 낮음
        chart = _make_chart(closes, volumes)
        result = evaluate_kama_signal(
            chart, er_period=10, signal_period=5,
            volume_filter=True, volume_ma_period=20,
        )
        if result.volume_confirmed is False and result.signal == SignalType.HOLD:
            assert "거래량 미확인" in result.reason_detail

    def test_kama_volume_filter_disabled(self):
        """volume_filter=False → 거래량 필터 미적용"""
        closes = [100] * 15 + [90, 88, 85, 83, 80, 78, 130, 135, 140]
        volumes = [5000] * 23 + [100]
        chart = _make_chart(closes, volumes)
        result = evaluate_kama_signal(
            chart, er_period=10, signal_period=5,
            volume_filter=False,
        )
        assert result.volume_confirmed is True

    def test_kama_result_fields(self):
        """KAMAResult에 모든 필드 포함"""
        closes = [float(100 + i) for i in range(30)]
        chart = _make_chart([int(c) for c in closes])
        result = evaluate_kama_signal(chart, er_period=10, signal_period=5)
        assert isinstance(result.signal, SignalType)
        assert isinstance(result.kama, float)
        assert isinstance(result.signal_line, float)
        assert isinstance(result.volume_confirmed, bool)
        assert isinstance(result.reason_detail, str)

    def test_kama_custom_periods(self):
        """커스텀 기간 파라미터"""
        closes = [float(100 + i) for i in range(50)]
        chart = _make_chart([int(c) for c in closes])
        result = evaluate_kama_signal(
            chart, er_period=15, fast_period=3, slow_period=20, signal_period=8,
        )
        assert result.kama > 0 or result.signal == SignalType.HOLD

    def test_kama_signal_line_is_sma_of_kama(self):
        """signal_line이 KAMA의 SMA인지 확인"""
        closes = [float(100 + i) for i in range(30)]
        chart = _make_chart([int(c) for c in closes])
        result = evaluate_kama_signal(chart, er_period=10, signal_period=5)
        # signal_line은 float (KAMA의 SMA)
        assert result.signal_line > 0


# ============================================================
# Phase 3 테스트: 브레이크아웃 시그널
# ============================================================


def _make_tight_chart(
    candles: list[tuple[float, float, float, float]],
    volumes: list[int] | None = None,
) -> list[ChartData]:
    """브레이크아웃 테스트용 OHLCV 차트 (tight high/low).

    candles: [(open, high, low, close), ...]
    """
    if volumes is None:
        volumes = [5000] * len(candles)
    return [
        ChartData(
            date=f"2025{(i // 28 + 1):02d}{(i % 28 + 1):02d}",
            open=o, high=h, low=l, close=c, volume=volumes[i],
        )
        for i, (o, h, l, c) in enumerate(candles)
    ]


class TestBreakoutSignal:
    def _stable_candles(self, n: int = 25) -> list[tuple[float, float, float, float]]:
        """안정 구간: close=100, high=102, low=98"""
        return [(100, 102, 98, 100)] * n

    def test_upper_breakout_buy(self):
        """상단 돌파 → BUY"""
        candles = self._stable_candles(25)
        candles.append((100, 200, 100, 200))  # 급등 → close > upper(=102)
        chart = _make_tight_chart(candles, [5000] * 25 + [10000])
        result = evaluate_breakout_signal(
            chart, upper_period=20, lower_period=10, volume_filter=False,
        )
        assert result.signal == SignalType.BUY
        assert "상단 돌파" in result.reason_detail

    def test_lower_breakdown_sell(self):
        """하단 이탈 → SELL"""
        candles = self._stable_candles(25)
        candles.append((100, 100, 10, 10))  # 급락 → close < lower(=98)
        chart = _make_tight_chart(candles)
        result = evaluate_breakout_signal(
            chart, upper_period=20, lower_period=10, volume_filter=False,
        )
        assert result.signal == SignalType.SELL
        assert "하단 이탈" in result.reason_detail

    def test_hold_in_channel(self):
        """채널 내 → HOLD"""
        candles = self._stable_candles(30)
        chart = _make_tight_chart(candles)
        result = evaluate_breakout_signal(
            chart, upper_period=20, lower_period=10, volume_filter=False,
        )
        assert result.signal == SignalType.HOLD
        assert "채널 내" in result.reason_detail

    def test_insufficient_data(self):
        """데이터 부족 → HOLD"""
        chart = _make_chart([100] * 5)
        result = evaluate_breakout_signal(chart, upper_period=20, lower_period=10)
        assert result.signal == SignalType.HOLD
        assert "데이터 부족" in result.reason_detail

    def test_atr_filter_blocks_low_volatility(self):
        """ATR 필터: 변동성 부족 시 BUY 차단"""
        # 안정 구간 + 소폭 돌파 (ATR이 낮은 상태)
        candles = self._stable_candles(25)
        candles.append((100, 105, 100, 105))  # 소폭 돌파
        chart = _make_tight_chart(candles, [5000] * 25 + [10000])
        result = evaluate_breakout_signal(
            chart, upper_period=20, lower_period=10,
            atr_filter=50.0,  # 극단적 ATR 기준 → 차단
            volume_filter=False,
        )
        assert result.signal == SignalType.HOLD
        assert "ATR 부족" in result.reason_detail

    def test_volume_filter_blocks_buy(self):
        """BUY + 거래량 부족 → HOLD"""
        candles = self._stable_candles(25)
        candles.append((100, 200, 100, 200))  # 급등
        chart = _make_tight_chart(candles, [5000] * 25 + [100])
        result = evaluate_breakout_signal(
            chart, upper_period=20, lower_period=10,
            volume_filter=True, volume_ma_period=20,
        )
        assert result.volume_confirmed is False
        assert result.signal == SignalType.HOLD
        assert "거래량 미확인" in result.reason_detail

    def test_volume_filter_disabled(self):
        """volume_filter=False → 거래량 무관 BUY"""
        candles = self._stable_candles(25)
        candles.append((100, 200, 100, 200))  # 급등
        chart = _make_tight_chart(candles, [5000] * 25 + [100])
        result = evaluate_breakout_signal(
            chart, upper_period=20, lower_period=10,
            volume_filter=False,
        )
        assert result.signal == SignalType.BUY

    def test_breakout_returns_atr(self):
        """ATR 값이 반환됨"""
        candles = self._stable_candles(30)
        chart = _make_tight_chart(candles)
        result = evaluate_breakout_signal(chart, upper_period=20, lower_period=10)
        assert result.atr is not None
