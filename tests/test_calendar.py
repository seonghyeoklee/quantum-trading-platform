"""매매일/장시간 판단 테스트"""

from datetime import date, datetime, time

from app.trading.calendar import KR_HOLIDAYS, is_market_open, is_trading_day


class TestIsTradingDay:
    def test_weekday_is_trading_day(self):
        """평일(공휴일 아닌)은 매매일"""
        # 2026-02-12 목요일
        assert is_trading_day(date(2026, 2, 12)) is True

    def test_saturday_not_trading_day(self):
        """토요일은 매매일 아님"""
        # 2026-02-14 토요일
        assert is_trading_day(date(2026, 2, 14)) is False

    def test_sunday_not_trading_day(self):
        """일요일은 매매일 아님"""
        # 2026-02-15 일요일
        assert is_trading_day(date(2026, 2, 15)) is False

    def test_holiday_not_trading_day(self):
        """공휴일은 매매일 아님"""
        # 2026-02-17 설날
        assert date(2026, 2, 17) in KR_HOLIDAYS
        assert is_trading_day(date(2026, 2, 17)) is False

    def test_new_year_not_trading_day(self):
        """신정은 매매일 아님"""
        assert is_trading_day(date(2026, 1, 1)) is False

    def test_substitute_holiday_not_trading_day(self):
        """대체공휴일도 매매일 아님"""
        # 2026-03-02 삼일절 대체공휴일
        assert is_trading_day(date(2026, 3, 2)) is False


class TestIsMarketOpen:
    def test_market_open_during_hours(self):
        """장 시간 내 (09:00~15:20)"""
        # 2026-02-12 목요일 10:30
        dt = datetime(2026, 2, 12, 10, 30, 0)
        assert is_market_open(dt) is True

    def test_market_open_at_start(self):
        """장 시작 정각"""
        dt = datetime(2026, 2, 12, 9, 0, 0)
        assert is_market_open(dt) is True

    def test_market_closed_at_close(self):
        """장 마감 정각 (15:30:00)은 주문 불가"""
        dt = datetime(2026, 2, 12, 15, 30, 0)
        assert is_market_open(dt) is False

    def test_market_open_just_before_close(self):
        """장 마감 직전 (15:29:59)은 주문 가능"""
        dt = datetime(2026, 2, 12, 15, 29, 59)
        assert is_market_open(dt) is True

    def test_market_closed_before_open(self):
        """장 시작 전"""
        dt = datetime(2026, 2, 12, 8, 59, 59)
        assert is_market_open(dt) is False

    def test_market_closed_after_close(self):
        """장 마감 후"""
        dt = datetime(2026, 2, 12, 15, 31, 0)
        assert is_market_open(dt) is False

    def test_market_closed_on_weekend(self):
        """주말에는 장 시간이어도 닫힘"""
        # 2026-02-14 토요일 10:00
        dt = datetime(2026, 2, 14, 10, 0, 0)
        assert is_market_open(dt) is False

    def test_market_closed_on_holiday(self):
        """공휴일에는 장 시간이어도 닫힘"""
        # 2026-02-17 설날 10:00
        dt = datetime(2026, 2, 17, 10, 0, 0)
        assert is_market_open(dt) is False
