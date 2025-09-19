"""
국내주식 실시간 데이터 타입 정의
KIS WebSocket API를 통한 국내주식 실시간 데이터 처리
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class MarketType(Enum):
    """시장 구분"""
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    KONEX = "KONEX"


class TradingSession(Enum):
    """거래 세션"""
    PRE_MARKET = "PRE_MARKET"      # 장전 시간외
    REGULAR = "REGULAR"            # 정규 장
    AFTER_HOURS = "AFTER_HOURS"   # 장후 시간외
    CLOSED = "CLOSED"              # 장 마감


@dataclass
class DomesticMarketData:
    """국내주식 실시간 시장 데이터"""
    symbol: str                    # 종목코드 (6자리)
    market_type: MarketType        # 시장 구분
    timestamp: datetime            # 데이터 수신 시간

    # 가격 정보
    current_price: float           # 현재가
    open_price: float              # 시가
    high_price: float              # 고가
    low_price: float               # 저가
    previous_close: float          # 전일종가

    # 거래량 정보
    volume: int                    # 거래량
    volume_turnover: float         # 거래대금

    # 변동 정보
    change: float                  # 전일대비
    change_percent: float          # 등락율
    change_sign: str               # 대비구분 (1:상승, 2:보합, 3:하락, 4:상한, 5:하한)

    # 호가 정보
    bid_price: float               # 매수 1호가
    ask_price: float               # 매도 1호가
    bid_volume: int                # 매수 1호가 잔량
    ask_volume: int                # 매도 1호가 잔량

    # 거래 세션
    trading_session: TradingSession = TradingSession.REGULAR

    # 원시 데이터 (디버깅용)
    raw_data: Optional[Dict[str, Any]] = None

    def get_change_color(self) -> str:
        """변동에 따른 색상 반환 (한국 주식: 빨강=상승, 파랑=하락)"""
        if self.change > 0:
            return "RED"    # 상승
        elif self.change < 0:
            return "BLUE"   # 하락
        else:
            return "WHITE"  # 보합

    def get_change_arrow(self) -> str:
        """변동에 따른 화살표 반환"""
        if self.change > 0:
            return "▲"
        elif self.change < 0:
            return "▼"
        else:
            return "→"

    def format_price(self, price: float) -> str:
        """가격을 한국 원화 형식으로 포맷"""
        if price >= 100000000:  # 1억 이상
            return f"{price/100000000:.1f}억원"
        elif price >= 10000:    # 1만 이상
            return f"{price/10000:.0f}만원"
        else:
            return f"{price:,.0f}원"

    def is_price_limit(self) -> bool:
        """상한가/하한가 여부"""
        return self.change_sign in ["4", "5"]

    def get_trading_strength(self) -> str:
        """거래 강도 계산 (매수/매도 비율)"""
        if self.bid_volume == 0 and self.ask_volume == 0:
            return "보통"

        total_volume = self.bid_volume + self.ask_volume
        if total_volume == 0:
            return "보통"

        buy_ratio = self.bid_volume / total_volume

        if buy_ratio > 0.7:
            return "매수강세"
        elif buy_ratio < 0.3:
            return "매도강세"
        else:
            return "보통"


@dataclass
class TradingSignal:
    """매매 신호"""
    symbol: str
    signal_type: str               # "BUY" 또는 "SELL"
    confidence: float              # 신뢰도 (0.0 ~ 1.0)
    reason: str                    # 신호 발생 이유
    price: float                   # 신호 발생 시점 가격
    timestamp: datetime            # 신호 발생 시간
    strategy_name: str             # 전략 이름

    # 추가 정보
    target_quantity: int = 1       # 목표 수량
    stop_loss: Optional[float] = None      # 손절가
    take_profit: Optional[float] = None    # 익절가


# 기본 시장 설정
DEFAULT_MARKETS = {
    # 주요 KOSPI 종목
    "005930": MarketType.KOSPI,    # 삼성전자
    "000660": MarketType.KOSPI,    # SK하이닉스
    "035420": MarketType.KOSPI,    # NAVER
    "051910": MarketType.KOSPI,    # LG화학
    "006400": MarketType.KOSPI,    # 삼성SDI
    "035720": MarketType.KOSPI,    # 카카오
    "207940": MarketType.KOSPI,    # 삼성바이오로직스
    "068270": MarketType.KOSPI,    # 셀트리온
    "323410": MarketType.KOSPI,    # 카카오뱅크

    # 주요 KOSDAQ 종목
    "247540": MarketType.KOSDAQ,   # 에코프로비엠
    "086520": MarketType.KOSDAQ,   # 에코프로
    "091990": MarketType.KOSDAQ,   # 셀트리온헬스케어
    "196170": MarketType.KOSDAQ,   # 알테오젠
    "039030": MarketType.KOSDAQ,   # 이오테크닉스
}


class TradingHours:
    """국내주식 거래시간 관리"""

    def __init__(self):
        # 정규장: 09:00 ~ 15:30
        # 장전 시간외: 08:00 ~ 09:00
        # 장후 시간외: 15:40 ~ 18:00
        pass

    def get_current_session(self) -> TradingSession:
        """현재 거래 세션 반환"""
        now = datetime.now()
        current_time = now.time()

        # 주말은 장 마감
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return TradingSession.CLOSED

        # 장전 시간외: 08:00 ~ 09:00
        if current_time >= datetime.strptime("08:00", "%H:%M").time() and \
           current_time < datetime.strptime("09:00", "%H:%M").time():
            return TradingSession.PRE_MARKET

        # 정규장: 09:00 ~ 15:30
        if current_time >= datetime.strptime("09:00", "%H:%M").time() and \
           current_time <= datetime.strptime("15:30", "%H:%M").time():
            return TradingSession.REGULAR

        # 장후 시간외: 15:40 ~ 18:00
        if current_time >= datetime.strptime("15:40", "%H:%M").time() and \
           current_time <= datetime.strptime("18:00", "%H:%M").time():
            return TradingSession.AFTER_HOURS

        # 나머지 시간은 장 마감
        return TradingSession.CLOSED

    def is_market_open(self) -> bool:
        """시장 개장 여부"""
        session = self.get_current_session()
        return session in [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_HOURS]