from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class StockPrice(BaseModel):
    """현재가 정보"""

    symbol: str
    name: str = ""
    current_price: int = 0
    change: int = 0  # 전일 대비
    change_rate: float = 0.0  # 등락률 (%)
    volume: int = 0  # 누적 거래량
    high: int = 0  # 고가
    low: int = 0  # 저가
    opening: int = 0  # 시가


class ChartData(BaseModel):
    """OHLCV 일봉 데이터"""

    date: str  # YYYYMMDD
    open: int
    high: int
    low: int
    close: int
    volume: int


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradingSignal(BaseModel):
    """매매 시그널"""

    symbol: str
    signal: SignalType
    short_ma: float  # 단기 이동평균
    long_ma: float  # 장기 이동평균
    current_price: int
    timestamp: datetime


class OrderResult(BaseModel):
    """주문 결과"""

    symbol: str
    side: str  # buy / sell
    quantity: int
    order_no: str = ""
    message: str = ""
    success: bool = False
    timestamp: datetime
    filled_quantity: int = 0
    filled_price: int = 0
    order_status: str = ""  # filled / partial / pending / unknown


class Position(BaseModel):
    """보유 포지션"""

    symbol: str
    name: str = ""
    quantity: int = 0
    avg_price: float = 0.0
    current_price: int = 0
    eval_amount: int = 0  # 평가금액
    profit_loss: int = 0  # 평가손익
    profit_loss_rate: float = 0.0  # 수익률 (%)


class EngineStatus(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


class TradingStatus(BaseModel):
    """엔진 상태"""

    status: EngineStatus = EngineStatus.STOPPED
    watch_symbols: list[str] = []
    positions: list[Position] = []
    recent_signals: list[TradingSignal] = []
    recent_orders: list[OrderResult] = []
    started_at: datetime | None = None
    loop_count: int = 0
