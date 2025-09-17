"""
해외주식 자동매매 시스템 데이터 타입
환율, 시차, 세금 등 해외시장 특성을 반영한 데이터 구조
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from decimal import Decimal


class ExchangeType(Enum):
    """거래소 타입"""
    NAS = "NAS"  # NASDAQ
    NYS = "NYS"  # New York Stock Exchange
    AMS = "AMS"  # AMEX
    HKS = "HKS"  # Hong Kong Stock Exchange
    TSE = "TSE"  # Tokyo Stock Exchange
    SHS = "SHS"  # Shanghai Stock Exchange
    SZS = "SZS"  # Shenzhen Stock Exchange


class TradingSession(Enum):
    """거래 세션"""
    PRE_MARKET = "PRE_MARKET"      # 프리마켓
    REGULAR = "REGULAR"            # 정규장
    AFTER_HOURS = "AFTER_HOURS"    # 애프터아워스
    CLOSED = "CLOSED"              # 장 마감


class SignalType(Enum):
    """신호 타입"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NONE = "NONE"


class PositionType(Enum):
    """포지션 타입"""
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class ExchangeRate:
    """환율 정보"""
    base_currency: str = "USD"
    quote_currency: str = "KRW"
    rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def convert_to_krw(self, usd_amount: float) -> float:
        """USD를 KRW로 변환"""
        return usd_amount * self.rate

    def convert_to_usd(self, krw_amount: float) -> float:
        """KRW를 USD로 변환"""
        return krw_amount / self.rate if self.rate > 0 else 0.0


@dataclass
class TradingHours:
    """거래시간 정보 (한국시간 기준)"""
    exchange: ExchangeType
    pre_market_start: str = "18:00"     # KST
    pre_market_end: str = "23:30"       # KST
    regular_start: str = "23:30"        # KST
    regular_end: str = "06:00"          # KST (다음날)
    after_hours_start: str = "06:00"    # KST
    after_hours_end: str = "10:00"      # KST

    def get_current_session(self, current_time: datetime = None) -> TradingSession:
        """현재 거래 세션 확인"""
        if current_time is None:
            current_time = datetime.now()

        time_str = current_time.strftime("%H:%M")

        # 프리마켓 시간
        if self.pre_market_start <= time_str < self.pre_market_end:
            return TradingSession.PRE_MARKET

        # 정규장 시간 (23:30 ~ 06:00, 다음날까지)
        if time_str >= self.regular_start or time_str < self.regular_end:
            return TradingSession.REGULAR

        # 애프터아워스 시간
        if self.after_hours_start <= time_str < self.after_hours_end:
            return TradingSession.AFTER_HOURS

        return TradingSession.CLOSED


@dataclass
class OverseasMarketData:
    """해외주식 시장 데이터"""
    symbol: str
    exchange: ExchangeType
    timestamp: datetime

    # 가격 정보 (USD)
    current_price: float = 0.0
    open_price: float = 0.0
    high_price: float = 0.0
    low_price: float = 0.0
    previous_close: float = 0.0

    # 거래량
    volume: int = 0
    average_volume: int = 0

    # 변동 정보
    change: float = 0.0
    change_percent: float = 0.0

    # 거래 세션
    trading_session: TradingSession = TradingSession.CLOSED

    # 환율 정보
    exchange_rate: Optional[ExchangeRate] = None

    # 추가 정보
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None

    def get_price_krw(self) -> float:
        """현재가를 원화로 변환"""
        if self.exchange_rate:
            return self.exchange_rate.convert_to_krw(self.current_price)
        return 0.0

    def get_change_krw(self) -> float:
        """변동액을 원화로 변환"""
        if self.exchange_rate:
            return self.exchange_rate.convert_to_krw(self.change)
        return 0.0

    def is_market_open(self) -> bool:
        """시장 개장 여부"""
        return self.trading_session in [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_HOURS]


@dataclass
class OverseasPosition:
    """해외주식 포지션"""
    symbol: str
    exchange: ExchangeType
    position_type: PositionType
    quantity: int
    entry_price: float  # USD
    entry_rate: float   # 진입 당시 환율
    current_price: float = 0.0  # USD
    current_rate: float = 0.0   # 현재 환율
    timestamp: datetime = field(default_factory=datetime.now)

    def get_market_value_usd(self) -> float:
        """시장가치 (USD)"""
        return self.quantity * self.current_price

    def get_market_value_krw(self) -> float:
        """시장가치 (KRW)"""
        return self.get_market_value_usd() * self.current_rate

    def get_cost_basis_usd(self) -> float:
        """매입원가 (USD)"""
        return self.quantity * self.entry_price

    def get_cost_basis_krw(self) -> float:
        """매입원가 (KRW, 진입 당시 환율)"""
        return self.get_cost_basis_usd() * self.entry_rate

    def get_unrealized_pnl_usd(self) -> float:
        """미실현 손익 (USD)"""
        if self.position_type == PositionType.LONG:
            return (self.current_price - self.entry_price) * self.quantity
        elif self.position_type == PositionType.SHORT:
            return (self.entry_price - self.current_price) * self.quantity
        return 0.0

    def get_unrealized_pnl_krw(self) -> float:
        """미실현 손익 (KRW, 현재 환율)"""
        return self.get_unrealized_pnl_usd() * self.current_rate

    def get_unrealized_pnl_percent(self) -> float:
        """미실현 손익률 (%)"""
        if self.entry_price == 0:
            return 0.0

        pnl_usd = self.get_unrealized_pnl_usd()
        cost_basis = self.get_cost_basis_usd()

        return (pnl_usd / cost_basis) * 100 if cost_basis > 0 else 0.0

    def get_currency_impact(self) -> float:
        """환율 변동 영향 (KRW)"""
        usd_value = self.get_market_value_usd()
        current_krw_value = usd_value * self.current_rate
        entry_krw_value = usd_value * self.entry_rate
        return current_krw_value - entry_krw_value


@dataclass
class TaxInfo:
    """세금 정보"""
    country: str = "KR"  # 한국
    basic_deduction: float = 2500000.0  # 250만원 기본공제
    tax_rate: float = 0.22  # 22% 양도소득세
    local_tax_rate: float = 0.022  # 2.2% 지방소득세 (22%의 10%)

    def calculate_tax(self, realized_gain: float) -> Dict[str, float]:
        """양도소득세 계산"""
        if realized_gain <= self.basic_deduction:
            return {
                "taxable_income": 0.0,
                "income_tax": 0.0,
                "local_tax": 0.0,
                "total_tax": 0.0
            }

        taxable_income = realized_gain - self.basic_deduction
        income_tax = taxable_income * self.tax_rate
        local_tax = taxable_income * self.local_tax_rate

        return {
            "taxable_income": taxable_income,
            "income_tax": income_tax,
            "local_tax": local_tax,
            "total_tax": income_tax + local_tax
        }


@dataclass
class OverseasTradingSignal:
    """해외주식 매매 신호"""
    symbol: str
    exchange: ExchangeType
    signal_type: SignalType
    confidence: float
    price: float  # USD
    quantity: int
    reason: str
    session: TradingSession
    timestamp: datetime = field(default_factory=datetime.now)

    # 추가 분석 정보
    technical_indicators: Dict[str, Any] = field(default_factory=dict)
    fundamental_data: Dict[str, Any] = field(default_factory=dict)
    market_sentiment: Optional[str] = None


@dataclass
class OverseasOrder:
    """해외주식 주문"""
    order_id: str
    symbol: str
    exchange: ExchangeType
    signal_type: SignalType
    quantity: int
    price: float  # USD
    order_type: str = "LIMIT"  # LIMIT, MARKET
    status: OrderStatus = OrderStatus.PENDING

    # 체결 정보
    filled_quantity: int = 0
    filled_price: float = 0.0
    filled_time: Optional[datetime] = None

    # 환율 정보
    order_rate: float = 0.0    # 주문 당시 환율
    filled_rate: float = 0.0   # 체결 당시 환율

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_filled(self) -> bool:
        """체결 완료 여부"""
        return self.status == OrderStatus.FILLED

    def get_filled_value_usd(self) -> float:
        """체결금액 (USD)"""
        return self.filled_quantity * self.filled_price

    def get_filled_value_krw(self) -> float:
        """체결금액 (KRW)"""
        return self.get_filled_value_usd() * self.filled_rate


# 상수 정의
DEFAULT_EXCHANGES = {
    'TSLA': ExchangeType.NAS,
    'AAPL': ExchangeType.NAS,
    'NVDA': ExchangeType.NAS,
    'MSFT': ExchangeType.NAS,
    'GOOGL': ExchangeType.NAS,
    'AMZN': ExchangeType.NAS,
    'META': ExchangeType.NAS,
    'NFLX': ExchangeType.NAS,
    'AMD': ExchangeType.NAS,
    'INTC': ExchangeType.NAS,
}

TRADING_HOURS_MAP = {
    ExchangeType.NAS: TradingHours(ExchangeType.NAS),
    ExchangeType.NYS: TradingHours(ExchangeType.NYS),
    ExchangeType.AMS: TradingHours(ExchangeType.AMS),
}