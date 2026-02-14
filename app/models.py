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
    """OHLCV 차트 데이터 (일봉: YYYYMMDD, 분봉: HHMMSS)"""

    date: str  # 일봉: YYYYMMDD, 분봉: HHMMSS
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
    short_ma: float = 0.0  # 단기 이동평균
    long_ma: float = 0.0  # 장기 이동평균
    current_price: int
    timestamp: datetime
    rsi: float | None = None
    volume_confirmed: bool | None = None
    obv_confirmed: bool | None = None
    raw_signal: SignalType | None = None  # 필터 적용 전 원시 시그널

    # 볼린저밴드 필드 (선택적)
    upper_band: float | None = None
    middle_band: float | None = None
    lower_band: float | None = None


class OrderResult(BaseModel):
    """주문 결과"""

    symbol: str
    side: str  # buy / sell
    quantity: int
    order_no: str = ""
    message: str = ""
    success: bool = False
    timestamp: datetime


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


class AccountSummary(BaseModel):
    """계좌 요약"""

    deposit: int = 0  # 예수금총금액
    total_eval: int = 0  # 총평가금액
    net_asset: int = 0  # 순자산금액
    purchase_total: int = 0  # 매입금액합계
    eval_profit_loss: int = 0  # 평가손익합계
    eval_profit_loss_rate: float = 0.0  # 자산증감율


class BacktestRequest(BaseModel):
    """백테스트 요청"""

    symbol: str = "005930"
    start_date: str = "20240101"  # YYYYMMDD
    end_date: str = ""  # 빈 문자열이면 오늘
    initial_capital: int = 10_000_000
    order_amount: int = 500_000
    use_advanced_strategy: bool = False


class EngineStatus(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"


class TradingStatus(BaseModel):
    """엔진 상태"""

    status: EngineStatus = EngineStatus.STOPPED
    watch_symbols: list[str] = []
    recent_signals: list[TradingSignal] = []
    recent_orders: list[OrderResult] = []
    started_at: datetime | None = None
    loop_count: int = 0
