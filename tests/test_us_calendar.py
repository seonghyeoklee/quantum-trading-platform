"""미국 시장 캘린더 단위 테스트"""

from datetime import date, datetime, time, timezone, timedelta

import pytest

from app.trading.calendar import (
    US_ET,
    US_HOLIDAYS,
    US_MARKET_CLOSE,
    US_MARKET_OPEN,
    is_us_market_open,
    is_us_trading_day,
)


class TestUSMarketConstants:
    def test_market_open_time(self):
        assert US_MARKET_OPEN == time(9, 30)

    def test_market_close_time(self):
        assert US_MARKET_CLOSE == time(16, 0)


class TestIsUSTradingDay:
    def test_weekday_not_holiday(self):
        """평일 + 비공휴일 → 매매일"""
        assert is_us_trading_day(date(2026, 2, 10)) is True  # 화요일

    def test_saturday(self):
        assert is_us_trading_day(date(2026, 2, 14)) is False  # 토요일

    def test_sunday(self):
        assert is_us_trading_day(date(2026, 2, 15)) is False  # 일요일

    def test_christmas(self):
        assert is_us_trading_day(date(2025, 12, 25)) is False

    def test_new_years_day(self):
        assert is_us_trading_day(date(2026, 1, 1)) is False

    def test_thanksgiving_2025(self):
        assert is_us_trading_day(date(2025, 11, 27)) is False

    def test_good_friday_2026(self):
        assert is_us_trading_day(date(2026, 4, 3)) is False

    def test_independence_day_observed_2026(self):
        """2026-07-04 토요일 → 2026-07-03 금요일 observed"""
        assert is_us_trading_day(date(2026, 7, 3)) is False

    def test_juneteenth_2026(self):
        assert is_us_trading_day(date(2026, 6, 19)) is False

    def test_holidays_has_mlk_2026(self):
        assert date(2026, 1, 19) in US_HOLIDAYS


class TestIsUSMarketOpen:
    """is_us_market_open 테스트 — ET 시간대 변환 포함"""

    def _make_et(self, hour, minute, d=None):
        """ET 시간대 datetime 생성"""
        if d is None:
            d = date(2026, 2, 10)  # 화요일
        return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=US_ET)

    def test_market_open_930(self):
        """09:30 ET → 개장"""
        now_et = self._make_et(9, 30)
        assert is_us_market_open(now_et) is True

    def test_market_before_open(self):
        """09:29 ET → 미개장"""
        now_et = self._make_et(9, 29)
        assert is_us_market_open(now_et) is False

    def test_market_at_close(self):
        """16:00 ET → 폐장 (close 시각은 미포함)"""
        now_et = self._make_et(16, 0)
        assert is_us_market_open(now_et) is False

    def test_market_before_close(self):
        """15:59 ET → 장중"""
        now_et = self._make_et(15, 59)
        assert is_us_market_open(now_et) is True

    def test_holiday_closed(self):
        """2026-01-01 (New Year) 10:00 ET → 휴장"""
        now_et = self._make_et(10, 0, d=date(2026, 1, 1))
        assert is_us_market_open(now_et) is False

    def test_weekend_closed(self):
        """토요일 12:00 ET → 폐장"""
        now_et = self._make_et(12, 0, d=date(2026, 2, 14))  # 토요일
        assert is_us_market_open(now_et) is False

    def test_kst_to_et_conversion(self):
        """KST 시간 → ET 변환 후 판단.
        KST 2026-02-11 00:00 = ET 2026-02-10 10:00 (EST, UTC-5) → 장중
        """
        kst = timezone(timedelta(hours=9))
        now_kst = datetime(2026, 2, 11, 0, 0, 0, tzinfo=kst)
        assert is_us_market_open(now_kst) is True

    def test_kst_morning_us_closed(self):
        """KST 오전 9시 = ET 전일 19:00 → 미국 폐장"""
        kst = timezone(timedelta(hours=9))
        now_kst = datetime(2026, 2, 10, 9, 0, 0, tzinfo=kst)
        # ET = 2026-02-09 19:00 → 월요일이지만 16:00 이후
        # 실제로 2026-02-09 is Monday, so ET 19:00 > 16:00 → closed
        assert is_us_market_open(now_kst) is False

    def test_midday_et(self):
        """12:00 ET → 장중"""
        now_et = self._make_et(12, 0)
        assert is_us_market_open(now_et) is True
