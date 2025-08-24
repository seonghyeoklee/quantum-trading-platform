#!/usr/bin/env python3
"""
실시간 데이터 Pydantic 모델
키움 공식 가이드 기반 응답 구조
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import BaseModel, Field


class RealtimeValues(BaseModel):
    """실시간 값 리스트"""
    # 공통 필드들
    account_number: Optional[str] = Field(None, alias="9201", description="계좌번호")
    order_number: Optional[str] = Field(None, alias="9203", description="주문번호")
    manager_id: Optional[str] = Field(None, alias="9205", description="관리자사번")
    symbol_code: Optional[str] = Field(None, alias="9001", description="종목코드,업종코드")
    order_business_type: Optional[str] = Field(None, alias="912", description="주문업무분류")
    order_status: Optional[str] = Field(None, alias="913", description="주문상태")
    symbol_name: Optional[str] = Field(None, alias="302", description="종목명")
    order_quantity: Optional[str] = Field(None, alias="900", description="주문수량")
    order_price: Optional[str] = Field(None, alias="901", description="주문가격")
    unfilled_quantity: Optional[str] = Field(None, alias="902", description="미체결수량")
    executed_amount: Optional[str] = Field(None, alias="903", description="체결누계금액")
    original_order_number: Optional[str] = Field(None, alias="904", description="원주문번호")
    order_type: Optional[str] = Field(None, alias="905", description="주문구분")
    trade_type: Optional[str] = Field(None, alias="906", description="매매구분")
    buy_sell_type: Optional[str] = Field(None, alias="907", description="매도수구분")
    order_execution_time: Optional[str] = Field(None, alias="908", description="주문/체결시간")
    execution_number: Optional[str] = Field(None, alias="909", description="체결번호")
    execution_price: Optional[str] = Field(None, alias="910", description="체결가")
    execution_quantity: Optional[str] = Field(None, alias="911", description="체결량")
    current_price: Optional[str] = Field(None, alias="10", description="현재가")
    best_ask_price: Optional[str] = Field(None, alias="27", description="(최우선)매도호가")
    best_bid_price: Optional[str] = Field(None, alias="28", description="(최우선)매수호가")
    unit_execution_price: Optional[str] = Field(None, alias="914", description="단위체결가")
    unit_execution_quantity: Optional[str] = Field(None, alias="915", description="단위체결량")
    daily_commission: Optional[str] = Field(None, alias="938", description="당일매매수수료")
    daily_tax: Optional[str] = Field(None, alias="939", description="당일매매세금")
    rejection_reason: Optional[str] = Field(None, alias="919", description="거부사유")
    screen_number: Optional[str] = Field(None, alias="920", description="화면번호")
    terminal_number: Optional[str] = Field(None, alias="921", description="터미널번호")
    credit_type: Optional[str] = Field(None, alias="922", description="신용구분")
    loan_date: Optional[str] = Field(None, alias="923", description="대출일")
    after_hours_price: Optional[str] = Field(None, alias="10010", description="시간외단일가_현재가")
    exchange_type: Optional[str] = Field(None, alias="2134", description="거래소구분")
    exchange_name: Optional[str] = Field(None, alias="2135", description="거래소구분명")
    sor_flag: Optional[str] = Field(None, alias="2136", description="SOR여부")

    class Config:
        extra = "allow"
        populate_by_name = True

    def get_field_value(self, field_code: str) -> Optional[str]:
        """필드 코드로 값 조회"""
        # 실제 데이터에서는 원본 딕셔너리에서 조회해야 함
        return getattr(self, field_code, None)


class RealtimeData(BaseModel):
    """실시간 데이터 아이템"""
    type: str = Field(..., description="실시간 항목 (TR 명)")
    name: Optional[str] = Field(None, description="실시간 항목명")
    item: Optional[str] = Field(None, description="종목코드")
    values: Dict[str, str] = Field(default_factory=dict, description="실시간 값 리스트")

    class Config:
        extra = "allow"

    def get_parsed_values(self) -> RealtimeValues:
        """values를 파싱된 모델로 변환"""
        return RealtimeValues.model_validate(self.values)

    def get_field_value(self, field_code: str) -> Optional[str]:
        """필드 코드로 값 직접 조회"""
        return self.values.get(field_code)


class RealtimeResponse(BaseModel):
    """키움 실시간 WebSocket 응답"""
    return_code: Optional[int] = Field(None, description="결과코드")
    return_msg: Optional[str] = Field(None, description="결과메시지")
    trnm: Optional[str] = Field(None, description="서비스명")
    data: Optional[List[RealtimeData]] = Field(default_factory=list, description="실시간 데이터 리스트")

    # PING/PONG용 추가 필드
    timestamp: Optional[str] = Field(None, description="타임스탬프")
    seq: Optional[str] = Field(None, description="시퀀스")

    class Config:
        extra = "allow"

    @property
    def is_ping(self) -> bool:
        """PING 메시지인지 확인"""
        return self.trnm == "PING"

    @property
    def is_login_response(self) -> bool:
        """로그인 응답인지 확인"""
        return self.trnm == "LOGIN"

    @property
    def is_registration_response(self) -> bool:
        """등록/해지 응답인지 확인"""
        return self.trnm in ["REG", "REMOVE"]

    @property
    def is_realtime_data(self) -> bool:
        """실시간 데이터인지 확인"""
        return self.trnm == "REAL"

    @property
    def is_success(self) -> bool:
        """성공 응답인지 확인"""
        return self.return_code == 0 if self.return_code is not None else True

    def get_data_by_type(self, realtime_type: str) -> List[RealtimeData]:
        """특정 타입의 데이터만 필터링"""
        if not self.data:
            return []
        return [item for item in self.data if item.type == realtime_type]

    def get_data_by_symbol(self, symbol: str) -> List[RealtimeData]:
        """특정 종목의 데이터만 필터링"""
        if not self.data:
            return []
        return [item for item in self.data if item.item == symbol]
