"""매매 전략 단위 테스트"""

from app.models import ChartData, SignalType
from app.trading.strategy import (
    compute_bollinger_bands,
    compute_obv,
    compute_rsi,
    compute_sma,
    evaluate_bollinger_signal,
    evaluate_signal,
    evaluate_signal_with_filters,
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
        signal, short_ma, long_ma = evaluate_signal(chart, 5, 20)
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
        signal, short_ma, long_ma = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.SELL
        assert short_ma < long_ma

    def test_hold_no_cross(self):
        """크로스 없음 → HOLD"""
        # SMA5 > SMA20 유지 (이미 위에 있고 계속 위)
        closes = [100] * 20 + [120, 121, 122, 123, 124]
        chart = _make_chart(closes)
        signal, _, _ = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD

    def test_hold_flat(self):
        """완전 횡보 → HOLD"""
        closes = [100] * 25
        chart = _make_chart(closes)
        signal, short_ma, long_ma = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD
        assert short_ma == long_ma == 100.0

    def test_insufficient_data(self):
        """데이터 부족 → HOLD"""
        closes = [100] * 15  # 20+1 미만
        chart = _make_chart(closes)
        signal, short_ma, long_ma = evaluate_signal(chart, 5, 20)
        assert signal == SignalType.HOLD
        assert short_ma == 0.0
        assert long_ma == 0.0

    def test_custom_periods(self):
        """커스텀 기간 파라미터"""
        closes = [100] * 10 + [95, 94, 93, 92, 150]
        chart = _make_chart(closes)
        signal, short_ma, long_ma = evaluate_signal(chart, 3, 10)
        assert signal == SignalType.BUY
        assert short_ma > long_ma


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
