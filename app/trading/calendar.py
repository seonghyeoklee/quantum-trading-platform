"""매매일/장시간 판단 모듈 (국내 KRX + 미국 NYSE/NASDAQ)"""

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

# 2025~2026 한국 공휴일 (주식시장 휴장일)
# 대체공휴일 포함
KR_HOLIDAYS: set[date] = {
    # 2025
    date(2025, 1, 1),   # 신정
    date(2025, 1, 28),  # 설날 연휴
    date(2025, 1, 29),  # 설날
    date(2025, 1, 30),  # 설날 연휴
    date(2025, 3, 1),   # 삼일절
    date(2025, 3, 3),   # 삼일절 대체공휴일
    date(2025, 5, 5),   # 어린이날
    date(2025, 5, 6),   # 부처님오신날
    date(2025, 6, 6),   # 현충일
    date(2025, 8, 15),  # 광복절
    date(2025, 10, 3),  # 개천절
    date(2025, 10, 5),  # 추석 연휴
    date(2025, 10, 6),  # 추석
    date(2025, 10, 7),  # 추석 연휴
    date(2025, 10, 8),  # 추석 대체공휴일
    date(2025, 10, 9),  # 한글날
    date(2025, 12, 25), # 성탄절
    date(2025, 12, 31), # 주식시장 폐장일
    # 2026
    date(2026, 1, 1),   # 신정
    date(2026, 2, 16),  # 설날 연휴
    date(2026, 2, 17),  # 설날
    date(2026, 2, 18),  # 설날 연휴
    date(2026, 3, 2),   # 삼일절 대체공휴일
    date(2026, 5, 5),   # 어린이날
    date(2026, 5, 24),  # 부처님오신날
    date(2026, 5, 25),  # 부처님오신날 대체공휴일
    date(2026, 6, 6),   # 현충일
    date(2026, 8, 15),  # 광복절
    date(2026, 8, 17),  # 광복절 대체공휴일
    date(2026, 9, 24),  # 추석 연휴
    date(2026, 9, 25),  # 추석
    date(2026, 9, 26),  # 추석 연휴
    date(2026, 10, 3),  # 개천절
    date(2026, 10, 5),  # 개천절 대체공휴일
    date(2026, 10, 9),  # 한글날
    date(2026, 12, 25), # 성탄절
    date(2026, 12, 31), # 주식시장 폐장일
}

MARKET_OPEN = time(9, 0)
MARKET_CLOSE = time(15, 30)


def is_trading_day(d: date) -> bool:
    """매매일 여부 판단 (평일 + 공휴일 아닌 날)"""
    if d.weekday() >= 5:  # 토(5), 일(6)
        return False
    if d in KR_HOLIDAYS:
        return False
    return True


def is_market_open(now: datetime) -> bool:
    """현재 시각이 장 시간인지 판단 (매매일 & 09:00~15:20)"""
    if not is_trading_day(now.date()):
        return False
    current_time = now.time()
    return MARKET_OPEN <= current_time < MARKET_CLOSE


# ──────────────────────────────────────────────
# 미국 시장 (NYSE / NASDAQ / AMEX)
# ──────────────────────────────────────────────

US_ET = ZoneInfo("America/New_York")  # DST 자동 처리
US_MARKET_OPEN = time(9, 30)
US_MARKET_CLOSE = time(16, 0)

# 2025~2026 NYSE 휴장일
US_HOLIDAYS: set[date] = {
    # 2025
    date(2025, 1, 1),    # New Year's Day
    date(2025, 1, 20),   # MLK Jr. Day
    date(2025, 2, 17),   # Presidents' Day
    date(2025, 4, 18),   # Good Friday
    date(2025, 5, 26),   # Memorial Day
    date(2025, 6, 19),   # Juneteenth
    date(2025, 7, 4),    # Independence Day
    date(2025, 9, 1),    # Labor Day
    date(2025, 11, 27),  # Thanksgiving
    date(2025, 12, 25),  # Christmas
    # 2026
    date(2026, 1, 1),    # New Year's Day
    date(2026, 1, 19),   # MLK Jr. Day
    date(2026, 2, 16),   # Presidents' Day
    date(2026, 4, 3),    # Good Friday
    date(2026, 5, 25),   # Memorial Day
    date(2026, 6, 19),   # Juneteenth
    date(2026, 7, 3),    # Independence Day (observed)
    date(2026, 9, 7),    # Labor Day
    date(2026, 11, 26),  # Thanksgiving
    date(2026, 12, 25),  # Christmas
}


def is_us_trading_day(d: date) -> bool:
    """미국 시장 매매일 여부 (평일 + 공휴일 아닌 날)"""
    if d.weekday() >= 5:
        return False
    if d in US_HOLIDAYS:
        return False
    return True


def is_us_market_open(now: datetime) -> bool:
    """현재 시각이 미국 장 시간인지 판단.

    now는 로컬 시각(KST 등)을 받아 ET로 변환 후 판단.
    naive datetime이면 시스템 로컬 시간으로 간주.
    """
    # naive datetime → aware (시스템 로컬)
    if now.tzinfo is None:
        import time as _time
        from datetime import timezone, timedelta as _td
        # 시스템 UTC offset 적용
        utc_offset = _td(seconds=-_time.timezone if _time.daylight == 0 else -_time.altzone)
        now = now.replace(tzinfo=timezone(utc_offset))

    now_et = now.astimezone(US_ET)
    if not is_us_trading_day(now_et.date()):
        return False
    return US_MARKET_OPEN <= now_et.time() < US_MARKET_CLOSE
