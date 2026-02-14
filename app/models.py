from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class EventType(str, Enum):
    """저널 이벤트 타입"""

    SIGNAL = "signal"
    ORDER = "order"
    FORCE_CLOSE = "force_close"
    ENGINE_START = "engine_start"
    ENGINE_STOP = "engine_stop"
    REGIME_CHANGE = "regime_change"
    STRATEGY_CHANGE = "strategy_change"


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
    reason: str = ""  # "signal" / "stop_loss" / "trailing_stop" / "max_holding" / "force_close"


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

    # 전략 선택: "sma_crossover" (기본) 또는 "bollinger"
    strategy_type: str = "sma_crossover"

    # 리스크 관리 (SMA 크로스오버 전략용)
    stop_loss_pct: float = 0.0       # 0=비활성
    max_holding_days: int = 0        # 0=비활성

    # 볼린저밴드 파라미터
    bollinger_period: int = 20
    bollinger_num_std: float = 2.0
    bollinger_max_holding_days: int = 5
    bollinger_max_daily_trades: int = 5


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
    current_regime: str | None = None  # 현재 시장 국면 (auto_regime 활성 시)


class TradeEvent(BaseModel):
    """저널용 통합 이벤트"""

    event_type: EventType
    timestamp: datetime
    symbol: str = ""
    # 시그널 필드
    signal: str = ""
    current_price: int = 0
    short_ma: float = 0.0
    long_ma: float = 0.0
    rsi: float | None = None
    volume_confirmed: bool | None = None
    upper_band: float | None = None
    middle_band: float | None = None
    lower_band: float | None = None
    # 주문 필드
    side: str = ""
    quantity: int = 0
    order_no: str = ""
    success: bool = False
    reason: str = ""
    entry_price: float = 0.0
    # 이벤트 상세
    detail: str = ""

    @classmethod
    def from_signal(cls, signal: TradingSignal) -> TradeEvent:
        """TradingSignal → 시그널 이벤트"""
        return cls(
            event_type=EventType.SIGNAL,
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            signal=signal.signal.value,
            current_price=signal.current_price,
            short_ma=signal.short_ma,
            long_ma=signal.long_ma,
            rsi=signal.rsi,
            volume_confirmed=signal.volume_confirmed,
            upper_band=signal.upper_band,
            middle_band=signal.middle_band,
            lower_band=signal.lower_band,
        )

    @classmethod
    def from_order(
        cls,
        symbol: str,
        side: str,
        quantity: int,
        result: dict,
        reason: str,
        current_price: int,
        entry_price: float = 0.0,
        *,
        event_type: EventType = EventType.ORDER,
        timestamp: datetime | None = None,
    ) -> TradeEvent:
        """주문 결과 → 주문/강제청산 이벤트"""
        return cls(
            event_type=event_type,
            timestamp=timestamp or datetime.now(),
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_no=result.get("order_no", ""),
            success=result.get("success", False),
            reason=reason,
            current_price=current_price,
            entry_price=entry_price,
        )

    @classmethod
    def engine_event(
        cls,
        event_type: EventType,
        detail: str = "",
        *,
        timestamp: datetime | None = None,
    ) -> TradeEvent:
        """엔진 시작/중지/국면변경/전략변경 이벤트"""
        return cls(
            event_type=event_type,
            timestamp=timestamp or datetime.now(),
            detail=detail,
        )
