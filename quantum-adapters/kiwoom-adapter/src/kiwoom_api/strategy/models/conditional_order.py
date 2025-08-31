"""
조건부 매매 주문 모델

사용자가 설정한 가격 조건에 따라 자동으로 매수/매도를 실행하는 시스템
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class ConditionType(str, Enum):
    """조건 타입"""
    PRICE_ABOVE = "price_above"      # 가격이 X원 이상일 때
    PRICE_BELOW = "price_below"      # 가격이 X원 이하일 때
    PRICE_BETWEEN = "price_between"  # 가격이 X~Y원 사이일 때
    RSI_ABOVE = "rsi_above"          # RSI가 X 이상일 때
    RSI_BELOW = "rsi_below"          # RSI가 X 이하일 때
    MA_CROSSOVER_UP = "ma_cross_up"  # 이평선 골든크로스
    MA_CROSSOVER_DOWN = "ma_cross_down"  # 이평선 데드크로스


class OrderAction(str, Enum):
    """주문 실행 동작"""
    BUY = "buy"           # 매수
    SELL = "sell"         # 매도
    BUY_PERCENT = "buy_percent"   # 보유 금액의 X% 매수
    SELL_PERCENT = "sell_percent"  # 보유 주식의 X% 매도


class OrderStatus(str, Enum):
    """주문 상태"""
    ACTIVE = "active"         # 활성 (조건 모니터링 중)
    TRIGGERED = "triggered"   # 조건 만족하여 주문 실행됨
    COMPLETED = "completed"   # 주문 완료
    CANCELLED = "cancelled"   # 주문 취소
    ERROR = "error"          # 오류 발생


class ConditionalOrder(BaseModel):
    """조건부 매매 주문"""
    
    # 기본 정보
    order_id: str = Field(..., description="주문 ID (UUID)")
    user_id: str = Field(..., description="사용자 ID")
    symbol: str = Field(..., description="종목코드")
    symbol_name: str = Field(default="", description="종목명")
    
    # 조건 설정
    condition_type: ConditionType = Field(..., description="조건 타입")
    condition_value: Decimal = Field(..., description="조건 값 (가격, RSI 등)")
    condition_value2: Optional[Decimal] = Field(None, description="조건 값2 (범위 조건용)")
    
    # 주문 실행 설정
    action: OrderAction = Field(..., description="실행 동작")
    quantity: Optional[int] = Field(None, description="주문 수량 (주)")
    amount: Optional[Decimal] = Field(None, description="주문 금액 (원)")
    percentage: Optional[float] = Field(None, description="비율 (%) - 퍼센트 주문용")
    
    # 상태 및 실행 정보
    status: OrderStatus = Field(default=OrderStatus.ACTIVE, description="주문 상태")
    created_at: datetime = Field(default_factory=datetime.now, description="생성 시간")
    triggered_at: Optional[datetime] = Field(None, description="조건 만족 시간")
    completed_at: Optional[datetime] = Field(None, description="주문 완료 시간")
    
    # 실행 결과
    executed_price: Optional[Decimal] = Field(None, description="실제 체결가")
    executed_quantity: Optional[int] = Field(None, description="실제 체결 수량")
    execution_details: Optional[Dict[str, Any]] = Field(None, description="실행 상세 정보")
    
    # 부가 설정
    dry_run: bool = Field(default=True, description="모의 투자 여부")
    valid_until: Optional[datetime] = Field(None, description="주문 유효 기간")
    memo: str = Field(default="", description="메모")
    
    def is_valid(self) -> bool:
        """주문이 유효한지 확인"""
        if self.status not in [OrderStatus.ACTIVE]:
            return False
        
        if self.valid_until and datetime.now() > self.valid_until:
            return False
        
        return True
    
    def check_condition(self, current_data: Dict[str, Any]) -> bool:
        """현재 데이터로 조건 확인"""
        current_price = Decimal(str(current_data.get("current_price", 0)))
        current_rsi = current_data.get("rsi")
        
        if self.condition_type == ConditionType.PRICE_ABOVE:
            return current_price >= self.condition_value
        
        elif self.condition_type == ConditionType.PRICE_BELOW:
            return current_price <= self.condition_value
        
        elif self.condition_type == ConditionType.PRICE_BETWEEN:
            if not self.condition_value2:
                return False
            return self.condition_value <= current_price <= self.condition_value2
        
        elif self.condition_type == ConditionType.RSI_ABOVE:
            return current_rsi is not None and current_rsi >= float(self.condition_value)
        
        elif self.condition_type == ConditionType.RSI_BELOW:
            return current_rsi is not None and current_rsi <= float(self.condition_value)
        
        elif self.condition_type == ConditionType.MA_CROSSOVER_UP:
            short_ma = current_data.get("short_ma")
            long_ma = current_data.get("long_ma")
            prev_short_ma = current_data.get("prev_short_ma")
            prev_long_ma = current_data.get("prev_long_ma")
            
            if all([short_ma, long_ma, prev_short_ma, prev_long_ma]):
                # 골든크로스: 이전에는 단기 < 장기, 현재는 단기 > 장기
                return (prev_short_ma <= prev_long_ma) and (short_ma > long_ma)
        
        elif self.condition_type == ConditionType.MA_CROSSOVER_DOWN:
            short_ma = current_data.get("short_ma")
            long_ma = current_data.get("long_ma")
            prev_short_ma = current_data.get("prev_short_ma")
            prev_long_ma = current_data.get("prev_long_ma")
            
            if all([short_ma, long_ma, prev_short_ma, prev_long_ma]):
                # 데드크로스: 이전에는 단기 > 장기, 현재는 단기 < 장기
                return (prev_short_ma >= prev_long_ma) and (short_ma < long_ma)
        
        return False
    
    def get_condition_description(self) -> str:
        """조건 설명 텍스트 생성"""
        if self.condition_type == ConditionType.PRICE_ABOVE:
            return f"{self.symbol} 가격이 {self.condition_value:,}원 이상일 때"
        
        elif self.condition_type == ConditionType.PRICE_BELOW:
            return f"{self.symbol} 가격이 {self.condition_value:,}원 이하일 때"
        
        elif self.condition_type == ConditionType.PRICE_BETWEEN:
            return f"{self.symbol} 가격이 {self.condition_value:,}~{self.condition_value2:,}원 사이일 때"
        
        elif self.condition_type == ConditionType.RSI_ABOVE:
            return f"{self.symbol} RSI가 {self.condition_value} 이상일 때"
        
        elif self.condition_type == ConditionType.RSI_BELOW:
            return f"{self.symbol} RSI가 {self.condition_value} 이하일 때"
        
        elif self.condition_type == ConditionType.MA_CROSSOVER_UP:
            return f"{self.symbol} 단기이평선이 장기이평선을 상향돌파할 때"
        
        elif self.condition_type == ConditionType.MA_CROSSOVER_DOWN:
            return f"{self.symbol} 단기이평선이 장기이평선을 하향돌파할 때"
        
        return f"{self.symbol} 조건 만족 시"
    
    def get_action_description(self) -> str:
        """실행 동작 설명 텍스트 생성"""
        if self.action == OrderAction.BUY:
            if self.quantity:
                return f"{self.quantity:,}주 매수"
            elif self.amount:
                return f"{self.amount:,}원 매수"
            else:
                return "매수"
        
        elif self.action == OrderAction.SELL:
            if self.quantity:
                return f"{self.quantity:,}주 매도"
            elif self.amount:
                return f"{self.amount:,}원 매도"
            else:
                return "매도"
        
        elif self.action == OrderAction.BUY_PERCENT:
            return f"보유 금액의 {self.percentage}% 매수"
        
        elif self.action == OrderAction.SELL_PERCENT:
            return f"보유 주식의 {self.percentage}% 매도"
        
        return "주문 실행"


class ConditionalOrderRequest(BaseModel):
    """조건부 매매 주문 생성 요청"""
    user_id: str
    symbol: str
    condition_type: ConditionType
    condition_value: Decimal
    condition_value2: Optional[Decimal] = None
    action: OrderAction
    quantity: Optional[int] = None
    amount: Optional[Decimal] = None
    percentage: Optional[float] = None
    valid_hours: Optional[int] = 24  # 유효 시간 (시간)
    dry_run: bool = True
    memo: str = ""


class ConditionalOrderResponse(BaseModel):
    """조건부 매매 주문 응답"""
    order_id: str
    message: str
    condition_description: str
    action_description: str
    status: OrderStatus
    created_at: datetime
    valid_until: Optional[datetime]