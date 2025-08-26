"""
키움 API 이벤트 스키마 정의

Pydantic 기반 표준화된 이벤트 모델들
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """이벤트 타입 정의"""
    STOCK_TRADE = "stock.trade"
    STOCK_PRICE = "stock.price" 
    ORDER_BOOK = "stock.orderbook"
    ORDER_EXECUTED = "trading.order.executed"
    ORDER_FAILED = "trading.order.failed"
    MARKET_DATA = "market.data"
    SCREENING_SIGNAL = "screening.signal"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"  # 에러 이벤트 추가


class BaseEvent(BaseModel):
    """모든 이벤트의 기본 스키마"""
    event_id: str = Field(..., description="이벤트 고유 ID")
    event_type: EventType = Field(..., description="이벤트 타입")
    timestamp: datetime = Field(default_factory=datetime.now, description="이벤트 발생 시간")
    source: str = Field(default="kiwoom_adapter", description="이벤트 발생 소스")
    correlation_id: Optional[str] = Field(None, description="상관관계 ID")


class StockTradeEvent(BaseEvent):
    """주식 체결 이벤트 (WebSocket 0B 타입)"""
    event_type: EventType = Field(default=EventType.STOCK_TRADE)
    
    symbol: str = Field(..., description="종목코드")
    price: int = Field(..., description="체결가격")
    volume: int = Field(..., description="체결수량") 
    trade_time: str = Field(..., description="체결시간 (HHMMSS)")
    change: int = Field(..., description="전일대비")
    change_rate: float = Field(..., description="등락율")
    cumulative_volume: int = Field(..., description="누적거래량")
    
    # 메타데이터
    market_status: Optional[str] = Field(None, description="장 상태")
    trade_type: Optional[str] = Field(None, description="거래 구분")


class OrderBookEvent(BaseEvent):
    """호가 정보 이벤트 (WebSocket 00 타입)"""
    event_type: EventType = Field(default=EventType.ORDER_BOOK)
    
    symbol: str = Field(..., description="종목코드")
    
    # 매수 호가 (10단계)
    bid_prices: list[int] = Field(..., description="매수호가 리스트")
    bid_volumes: list[int] = Field(..., description="매수호가수량 리스트")
    
    # 매도 호가 (10단계)
    ask_prices: list[int] = Field(..., description="매도호가 리스트") 
    ask_volumes: list[int] = Field(..., description="매도호가수량 리스트")
    
    # 추가 정보
    total_bid_volume: int = Field(..., description="매수호가 총 수량")
    total_ask_volume: int = Field(..., description="매도호가 총 수량")


class StockPriceEvent(BaseEvent):
    """현재가 정보 이벤트 (WebSocket 0A 타입)"""
    event_type: EventType = Field(default=EventType.STOCK_PRICE)
    
    symbol: str = Field(..., description="종목코드")
    current_price: int = Field(..., description="현재가")
    change: int = Field(..., description="전일대비")
    change_rate: float = Field(..., description="등락율")
    
    # OHLC 데이터
    open_price: int = Field(..., description="시가")
    high_price: int = Field(..., description="고가")
    low_price: int = Field(..., description="저가")
    prev_close: int = Field(..., description="전일종가")
    
    # 거래량/금액
    volume: int = Field(..., description="거래량")
    amount: int = Field(..., description="거래대금")
    
    # 시장 정보
    market_cap: Optional[int] = Field(None, description="시가총액")
    shares_outstanding: Optional[int] = Field(None, description="상장주식수")


class OrderExecutedEvent(BaseEvent):
    """주문 체결 이벤트 (거래 API 응답)"""
    event_type: EventType = Field(default=EventType.ORDER_EXECUTED)
    
    order_id: str = Field(..., description="주문번호")
    symbol: str = Field(..., description="종목코드")
    side: str = Field(..., description="매매구분 (buy/sell)")
    order_type: str = Field(..., description="주문유형")
    quantity: int = Field(..., description="주문수량")
    price: int = Field(..., description="주문가격")
    
    # 체결 정보
    executed_quantity: int = Field(..., description="체결수량")
    executed_price: int = Field(..., description="체결가격")
    remaining_quantity: int = Field(..., description="미체결수량")
    
    # 거래소 정보
    exchange: str = Field(..., description="거래소구분")
    order_status: str = Field(..., description="주문상태")


class MarketDataEvent(BaseEvent):
    """시장 데이터 이벤트 (API 조회 응답)"""
    event_type: EventType = Field(default=EventType.MARKET_DATA)
    
    api_id: str = Field(..., description="API 식별자 (ka10001 등)")
    request_data: Dict[str, Any] = Field(..., description="요청 데이터")
    response_data: Dict[str, Any] = Field(..., description="응답 데이터")
    
    # 요청 메타정보
    status_code: int = Field(..., description="HTTP 상태 코드")
    response_time_ms: float = Field(..., description="응답 시간 (밀리초)")
    cont_yn: str = Field(default="N", description="연속조회여부")
    next_key: Optional[str] = Field(None, description="연속조회키")


class ScreeningSignalEvent(BaseEvent):
    """조건검색 신호 이벤트 (TR 명령어 결과)"""
    event_type: EventType = Field(default=EventType.SCREENING_SIGNAL)
    
    condition_seq: str = Field(..., description="조건식 일련번호")
    condition_name: str = Field(..., description="조건식 명")
    symbol: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    
    # 신호 정보
    signal_type: str = Field(..., description="신호 유형 (진입/이탈)")
    action_code: str = Field(..., description="액션 코드")
    action_description: str = Field(..., description="액션 설명")
    
    # 추가 데이터
    current_price: Optional[int] = Field(None, description="현재가")
    signal_time: Optional[str] = Field(None, description="신호 발생 시간")


class APIResponseEvent(BaseEvent):
    """일반 API 응답 이벤트"""
    event_type: EventType = Field(default=EventType.API_RESPONSE)
    
    api_endpoint: str = Field(..., description="API 엔드포인트")
    http_method: str = Field(..., description="HTTP 메소드")
    request_id: Optional[str] = Field(None, description="요청 ID")
    
    # 요청/응답 정보
    request_data: Optional[Dict[str, Any]] = Field(None, description="요청 데이터")
    response_data: Dict[str, Any] = Field(..., description="응답 데이터")
    status_code: int = Field(..., description="HTTP 상태 코드")
    response_time_ms: float = Field(..., description="응답 시간")
    
    # 에러 정보 (실패 시)
    error_message: Optional[str] = Field(None, description="에러 메시지")
    error_code: Optional[str] = Field(None, description="에러 코드")


class APIErrorEvent(BaseEvent):
    """키움 API 에러 전용 이벤트"""
    event_type: EventType = Field(default=EventType.API_ERROR)
    
    # 에러 기본 정보
    error_code: str = Field(..., description="키움 에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    severity: str = Field(..., description="에러 심각도 (critical/high/medium/low)")
    category: str = Field(..., description="에러 카테고리")
    
    # 발생 컨텍스트
    api_endpoint: str = Field(..., description="에러 발생 API")
    http_method: str = Field(default="POST", description="HTTP 메소드")
    request_data: Optional[Dict[str, Any]] = Field(None, description="요청 데이터")
    response_data: Optional[Dict[str, Any]] = Field(None, description="응답 데이터")
    
    # 복구 관련 정보
    auto_retry: bool = Field(default=False, description="자동 재시도 가능 여부")
    recovery_action: Optional[str] = Field(None, description="복구 액션")
    retry_count: int = Field(default=0, description="재시도 횟수")
    
    # 사용자 정보
    user_id: Optional[str] = Field(None, description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")
    
    # 메타데이터
    response_time_ms: Optional[float] = Field(None, description="응답 시간")
    http_status_code: Optional[int] = Field(None, description="HTTP 상태 코드")
    stack_trace: Optional[str] = Field(None, description="스택 트레이스")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "error-12345",
                "error_code": "8005",
                "error_message": "Token이 유효하지 않습니다",
                "severity": "high",
                "category": "authentication",
                "api_endpoint": "/api/fn_ka10081",
                "auto_retry": True,
                "recovery_action": "reissue_token"
            }
        }