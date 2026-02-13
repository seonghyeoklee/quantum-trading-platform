"""이동평균 크로스오버 전략 단위 테스트"""

from app.models import ChartData, SignalType
from app.trading.strategy import compute_sma, evaluate_signal


def _make_chart(closes: list[int]) -> list[ChartData]:
    """테스트용 차트 데이터 생성"""
    return [
        ChartData(
            date=f"2025{(i // 28 + 1):02d}{(i % 28 + 1):02d}",
            open=c,
            high=c + 100,
            low=c - 100,
            close=c,
            volume=1000,
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
