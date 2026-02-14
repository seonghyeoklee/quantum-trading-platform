"""시장 국면 판별 단위 테스트"""

from app.trading.regime import (
    MarketRegime,
    RegimeInfo,
    RegimePeriod,
    classify_regime,
    detect_current_regime,
    segment_by_regime,
)


class TestClassifyRegime:
    """classify_regime: 5가지 국면 정확 판별"""

    def test_strong_bull(self):
        """last > SMA20 > SMA60 > SMA120 → strong_bull"""
        assert classify_regime(last=1000, sma20=950, sma60=900, sma120=850) == MarketRegime.STRONG_BULL

    def test_bull(self):
        """last > SMA60 AND SMA20 > SMA60, but not strong_bull"""
        # last > SMA60, SMA20 > SMA60, but SMA60 > SMA120 is not satisfied by last > SMA20
        # e.g. last=1000, SMA20=950, SMA60=900, SMA120=920 (SMA60 < SMA120)
        assert classify_regime(last=1000, sma20=950, sma60=900, sma120=920) == MarketRegime.BULL

    def test_bull_sma20_above_last(self):
        """SMA20 > last but last > SMA60 AND SMA20 > SMA60 → bull"""
        assert classify_regime(last=950, sma20=960, sma60=900, sma120=850) == MarketRegime.BULL

    def test_strong_bear(self):
        """last < SMA20 < SMA60 < SMA120 → strong_bear"""
        assert classify_regime(last=800, sma20=850, sma60=900, sma120=950) == MarketRegime.STRONG_BEAR

    def test_bear(self):
        """last < SMA60 AND SMA20 < SMA60, but not strong_bear"""
        # last < SMA60, SMA20 < SMA60, but SMA60 < SMA120 not forming complete reverse
        assert classify_regime(last=800, sma20=850, sma60=900, sma120=880) == MarketRegime.BEAR

    def test_bear_sma20_below_last(self):
        """SMA20 < last but last < SMA60 AND SMA20 < SMA60 → bear"""
        assert classify_regime(last=850, sma20=840, sma60=900, sma120=950) == MarketRegime.BEAR

    def test_sideways_mixed(self):
        """SMA들이 혼재 → sideways"""
        # last > SMA60 but SMA20 < SMA60
        assert classify_regime(last=950, sma20=880, sma60=900, sma120=920) == MarketRegime.SIDEWAYS

    def test_sideways_narrow_range(self):
        """last < SMA60, SMA20 > SMA60 → 엇갈림 → sideways"""
        # last=1000 < sma60=1005, but sma20=1010 > sma60=1005 → 모순 → sideways
        assert classify_regime(last=1000, sma20=1010, sma60=1005, sma120=998) == MarketRegime.SIDEWAYS

    def test_sideways_last_below_sma60_but_sma20_above(self):
        """last < SMA60이지만 SMA20 > SMA60 → sideways"""
        # last=890 < sma60=900, but sma20=950 > sma60=900 → 엇갈림
        assert classify_regime(last=890, sma20=950, sma60=900, sma120=850) == MarketRegime.SIDEWAYS


class TestDetectCurrentRegime:
    """detect_current_regime: 종가 리스트로 현재 국면 판별"""

    def test_insufficient_data_returns_none(self):
        """120개 미만 데이터 → None"""
        closes = [1000.0] * 100
        assert detect_current_regime(closes) is None

    def test_steady_uptrend_strong_bull(self):
        """꾸준한 상승 → strong_bull"""
        # 150일 꾸준히 상승: 500 → 649
        closes = [500.0 + i for i in range(150)]
        result = detect_current_regime(closes)
        assert result is not None
        assert result.regime == MarketRegime.STRONG_BULL
        assert result.last_price == closes[-1]
        assert result.sma20 > 0
        assert result.sma60 > 0
        assert result.sma120 > 0

    def test_steady_downtrend_strong_bear(self):
        """꾸준한 하락 → strong_bear"""
        closes = [1000.0 - i for i in range(150)]
        result = detect_current_regime(closes)
        assert result is not None
        assert result.regime == MarketRegime.STRONG_BEAR

    def test_flat_prices_sideways(self):
        """일정한 가격 → sideways"""
        closes = [1000.0] * 150
        result = detect_current_regime(closes)
        assert result is not None
        assert result.regime == MarketRegime.SIDEWAYS

    def test_returns_regime_info_fields(self):
        """RegimeInfo의 모든 필드가 올바르게 채워짐"""
        closes = [500.0 + i for i in range(150)]
        result = detect_current_regime(closes)
        assert result is not None
        assert isinstance(result, RegimeInfo)
        assert result.rsi14 is not None
        assert 0 <= result.rsi14 <= 100


class TestSegmentByRegime:
    """segment_by_regime: 차트를 국면 구간으로 분할"""

    def test_insufficient_data_returns_empty(self):
        """120개 미만 데이터 → 빈 리스트"""
        closes = [1000.0] * 100
        dates = [str(i) for i in range(100)]
        assert segment_by_regime(closes, dates) == []

    def test_single_regime_one_period(self):
        """단일 국면 → 1개 구간"""
        closes = [500.0 + i for i in range(150)]
        dates = [f"2024{(i // 28 + 1):02d}{(i % 28 + 1):02d}" for i in range(150)]
        periods = segment_by_regime(closes, dates)
        assert len(periods) >= 1
        # 모든 구간의 시작~끝이 데이터 범위 내
        for p in periods:
            assert 0 <= p.start_index <= p.end_index < len(closes)
            assert p.start_date == dates[p.start_index]
            assert p.end_date == dates[p.end_index]

    def test_regime_transition(self):
        """상승 → 하락 전환 시 2개 이상 구간"""
        # 150일 상승 + 150일 하락 = 국면 전환 발생
        closes = [500.0 + i for i in range(150)] + [650.0 - i for i in range(150)]
        dates = [str(20240101 + i) for i in range(300)]
        periods = segment_by_regime(closes, dates)
        assert len(periods) >= 2
        # 구간이 연속적인지 확인
        for i in range(1, len(periods)):
            assert periods[i].start_index == periods[i - 1].end_index + 1

    def test_periods_cover_all_data(self):
        """모든 구간이 인덱스 119부터 마지막까지 커버"""
        closes = [500.0 + i for i in range(200)]
        dates = [str(20240101 + i) for i in range(200)]
        periods = segment_by_regime(closes, dates)
        assert len(periods) >= 1
        assert periods[0].start_index == 119
        assert periods[-1].end_index == len(closes) - 1

    def test_period_dates_match_indices(self):
        """각 구간의 start_date/end_date가 인덱스와 일치"""
        closes = [1000.0 + (i % 50) - 25 for i in range(200)]
        dates = [f"D{i:04d}" for i in range(200)]
        periods = segment_by_regime(closes, dates)
        for p in periods:
            assert p.start_date == dates[p.start_index]
            assert p.end_date == dates[p.end_index]
