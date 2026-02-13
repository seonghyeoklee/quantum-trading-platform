"""매매일/장시간 판단 모듈"""

from datetime import date, datetime, time

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
MARKET_CLOSE = time(15, 20)


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
