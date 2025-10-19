"""
Pydantic 모델 정의

API 요청/응답 및 데이터 구조를 정의합니다.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# === 열거형 정의 ===

class OrderSide(str, Enum):
    """주문 방향"""
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    """주문 유형"""
    MARKET = "market"      # 시장가
    LIMIT = "limit"        # 지정가
    STOP_LOSS = "stop_loss"  # 손절
    TAKE_PROFIT = "take_profit"  # 익절

class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING = "pending"      # 대기
    FILLED = "filled"        # 체결
    PARTIALLY_FILLED = "partially_filled"  # 부분체결
    CANCELLED = "cancelled"  # 취소
    REJECTED = "rejected"    # 거부

class SignalType(str, Enum):
    """매매 신호 유형"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class TradingStatus(str, Enum):
    """거래 상태"""
    ACTIVE = "active"        # 활성
    PAUSED = "paused"        # 일시정지
    STOPPED = "stopped"      # 중지
    ERROR = "error"          # 오류

# === 시장 데이터 모델 ===

class CandleData(BaseModel):
    """캔들 데이터"""
    symbol: str = Field(..., description="종목코드")
    timestamp: datetime = Field(..., description="시간")
    open_price: float = Field(..., description="시가")
    high_price: float = Field(..., description="고가")
    low_price: float = Field(..., description="저가")
    close_price: float = Field(..., description="종가")
    volume: int = Field(..., description="거래량")
    amount: float = Field(..., description="거래대금")

class OrderBookData(BaseModel):
    """호가창 데이터"""
    symbol: str = Field(..., description="종목코드")
    timestamp: datetime = Field(..., description="시간")
    
    # 매도 호가 (1~10호가)
    ask_prices: List[float] = Field(..., description="매도 호가")
    ask_volumes: List[int] = Field(..., description="매도 잔량")
    
    # 매수 호가 (1~10호가)
    bid_prices: List[float] = Field(..., description="매수 호가")
    bid_volumes: List[int] = Field(..., description="매수 잔량")
    
    # 추가 정보
    total_ask_volume: int = Field(..., description="총 매도 잔량")
    total_bid_volume: int = Field(..., description="총 매수 잔량")

class TechnicalIndicators(BaseModel):
    """기술적 지표"""
    symbol: str = Field(..., description="종목코드")
    timestamp: datetime = Field(..., description="시간")
    
    # 추세 지표
    ema_5: Optional[float] = Field(None, description="5일 지수이동평균")
    ema_20: Optional[float] = Field(None, description="20일 지수이동평균")
    
    # 모멘텀 지표
    rsi: Optional[float] = Field(None, description="RSI")
    macd: Optional[float] = Field(None, description="MACD")
    macd_signal: Optional[float] = Field(None, description="MACD 신호선")
    macd_histogram: Optional[float] = Field(None, description="MACD 히스토그램")
    
    # 변동성 지표
    bb_upper: Optional[float] = Field(None, description="볼린저밴드 상단")
    bb_middle: Optional[float] = Field(None, description="볼린저밴드 중간")
    bb_lower: Optional[float] = Field(None, description="볼린저밴드 하단")
    
    # 거래량 지표
    vwap: Optional[float] = Field(None, description="거래량가중평균가격")
    volume_sma: Optional[float] = Field(None, description="거래량 이동평균")

# === 매매 신호 모델 ===

class TradingSignal(BaseModel):
    """매매 신호"""
    symbol: str = Field(..., description="종목코드")
    signal_type: SignalType = Field(..., description="신호 유형")
    timestamp: datetime = Field(..., description="신호 발생 시간")
    
    # 신호 강도 및 근거
    strength: float = Field(..., ge=0.0, le=1.0, description="신호 강도 (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도 (0-1)")
    
    # 신호 근거
    technical_score: float = Field(..., description="기술적 분석 점수")
    microstructure_score: float = Field(..., description="시장 미시구조 점수")
    sentiment_score: float = Field(..., description="센티먼트 점수")
    
    # 가격 정보
    current_price: float = Field(..., description="현재가")
    target_price: Optional[float] = Field(None, description="목표가")
    stop_loss_price: Optional[float] = Field(None, description="손절가")
    
    # 추가 정보
    reasoning: str = Field(..., description="신호 발생 이유")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

# === 주문 모델 ===

class OrderRequest(BaseModel):
    """주문 요청"""
    symbol: str = Field(..., description="종목코드")
    side: OrderSide = Field(..., description="주문 방향")
    order_type: OrderType = Field(..., description="주문 유형")
    quantity: int = Field(..., gt=0, description="주문 수량")
    price: Optional[float] = Field(None, description="주문 가격 (지정가인 경우)")

class Order(BaseModel):
    """주문 정보"""
    order_id: str = Field(..., description="주문 ID")
    symbol: str = Field(..., description="종목코드")
    side: OrderSide = Field(..., description="주문 방향")
    order_type: OrderType = Field(..., description="주문 유형")
    quantity: int = Field(..., description="주문 수량")
    price: Optional[float] = Field(None, description="주문 가격")
    
    # 상태 정보
    status: OrderStatus = Field(..., description="주문 상태")
    filled_quantity: int = Field(default=0, description="체결 수량")
    remaining_quantity: int = Field(..., description="미체결 수량")
    avg_fill_price: Optional[float] = Field(None, description="평균 체결가")
    
    # 시간 정보
    created_at: datetime = Field(..., description="주문 생성 시간")
    updated_at: datetime = Field(..., description="주문 수정 시간")
    filled_at: Optional[datetime] = Field(None, description="체결 시간")

# === 포지션 모델 ===

class Position(BaseModel):
    """포지션 정보"""
    symbol: str = Field(..., description="종목코드")
    quantity: int = Field(..., description="보유 수량")
    avg_price: float = Field(..., description="평균 매수가")
    current_price: float = Field(..., description="현재가")
    
    # 손익 정보
    unrealized_pnl: float = Field(..., description="미실현 손익")
    unrealized_pnl_percent: float = Field(..., description="미실현 손익률")
    
    # 리스크 관리
    stop_loss_price: Optional[float] = Field(None, description="손절가")
    take_profit_price: Optional[float] = Field(None, description="익절가")
    
    # 시간 정보
    opened_at: datetime = Field(..., description="포지션 오픈 시간")
    updated_at: datetime = Field(..., description="포지션 업데이트 시간")

# === 계좌 모델 ===

class AccountBalance(BaseModel):
    """계좌 잔고"""
    total_balance: float = Field(..., description="총 자산")
    available_cash: float = Field(..., description="사용 가능 현금")
    stock_value: float = Field(..., description="주식 평가액")
    
    # 손익 정보
    total_pnl: float = Field(..., description="총 손익")
    total_pnl_percent: float = Field(..., description="총 손익률")
    daily_pnl: float = Field(..., description="일일 손익")
    daily_pnl_percent: float = Field(..., description="일일 손익률")
    
    # 업데이트 시간
    updated_at: datetime = Field(..., description="업데이트 시간")

# === 시스템 상태 모델 ===

class SystemStatus(BaseModel):
    """시스템 상태"""
    trading_status: TradingStatus = Field(..., description="거래 상태")
    active_positions: int = Field(..., description="활성 포지션 수")
    pending_orders: int = Field(..., description="대기 주문 수")
    
    # 성능 지표
    total_trades_today: int = Field(..., description="오늘 총 거래 수")
    win_rate: float = Field(..., description="승률")
    profit_factor: float = Field(..., description="수익 팩터")
    
    # 시스템 정보
    uptime: str = Field(..., description="가동 시간")
    last_signal_time: Optional[datetime] = Field(None, description="마지막 신호 시간")
    
    # 연결 상태
    kis_api_connected: bool = Field(..., description="KIS API 연결 상태")
    database_connected: bool = Field(..., description="데이터베이스 연결 상태")
    websocket_connected: bool = Field(..., description="웹소켓 연결 상태")

# === API 응답 모델 ===

class ApiResponse(BaseModel):
    """기본 API 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시간")

class DataResponse(ApiResponse):
    """데이터 포함 응답"""
    data: Any = Field(..., description="응답 데이터")

class ListResponse(ApiResponse):
    """리스트 데이터 응답"""
    data: List[Any] = Field(..., description="응답 데이터 리스트")
    total: int = Field(..., description="전체 개수")
    page: int = Field(default=1, description="페이지 번호")
    size: int = Field(default=50, description="페이지 크기")

# === 백테스팅 모델 ===

class BacktestRequest(BaseModel):
    """백테스팅 요청"""
    start_date: datetime = Field(..., description="시작 날짜")
    end_date: datetime = Field(..., description="종료 날짜")
    initial_capital: float = Field(..., description="초기 자본")
    symbols: List[str] = Field(..., description="대상 종목")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="전략 파라미터")

class BacktestResult(BaseModel):
    """백테스팅 결과"""
    total_return: float = Field(..., description="총 수익률")
    annual_return: float = Field(..., description="연간 수익률")
    sharpe_ratio: float = Field(..., description="샤프 비율")
    max_drawdown: float = Field(..., description="최대 낙폭")
    
    # 거래 통계
    total_trades: int = Field(..., description="총 거래 수")
    win_rate: float = Field(..., description="승률")
    profit_factor: float = Field(..., description="수익 팩터")
    avg_trade_return: float = Field(..., description="평균 거래 수익률")
    
    # 상세 결과
    daily_returns: List[float] = Field(..., description="일별 수익률")
    equity_curve: List[float] = Field(..., description="자산 곡선")
    trades: List[Dict[str, Any]] = Field(..., description="거래 내역")
