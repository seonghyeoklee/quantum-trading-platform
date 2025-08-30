"""
매매 신호 데이터 모델

전략에서 생성되는 매매 신호를 정의하는 모델
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


class SignalType(Enum):
    """매매 신호 타입"""
    BUY = "BUY"           # 매수 신호
    SELL = "SELL"         # 매도 신호
    HOLD = "HOLD"         # 보유 신호
    CLOSE = "CLOSE"       # 포지션 청산 신호


class SignalStrength(Enum):
    """신호 강도"""
    WEAK = "WEAK"         # 약한 신호
    MODERATE = "MODERATE" # 보통 신호
    STRONG = "STRONG"     # 강한 신호


class TradingSignal(BaseModel):
    """
    매매 신호 모델
    
    전략에서 생성되는 매매 신호의 상세 정보를 담는다.
    """
    
    # 기본 정보
    strategy_name: str = Field(description="전략명")
    symbol: str = Field(description="종목코드 (6자리)")
    signal_type: SignalType = Field(description="매매 신호 타입")
    strength: SignalStrength = Field(description="신호 강도")
    
    # 가격 정보
    current_price: Decimal = Field(description="현재가")
    target_price: Optional[Decimal] = Field(None, description="목표가")
    stop_loss: Optional[Decimal] = Field(None, description="손절가")
    
    # 수량 정보
    quantity: Optional[int] = Field(None, description="매매 수량")
    quantity_ratio: Optional[float] = Field(None, description="포트폴리오 대비 비중")
    
    # 시간 정보
    timestamp: datetime = Field(default_factory=datetime.now, description="신호 생성 시간")
    valid_until: Optional[datetime] = Field(None, description="신호 유효 기한")
    
    # 전략 정보
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="전략 파라미터")
    confidence: float = Field(ge=0.0, le=1.0, description="신호 신뢰도 (0.0-1.0)")
    
    # 분석 정보
    technical_indicators: Dict[str, float] = Field(default_factory=dict, description="기술적 지표값들")
    reason: str = Field(description="매매 신호 발생 이유")
    additional_info: Dict[str, Any] = Field(default_factory=dict, description="추가 정보")
    
    class Config:
        """Pydantic 설정"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v)
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return self.model_dump()
        
    def is_valid(self) -> bool:
        """신호가 유효한지 확인"""
        if self.valid_until is None:
            return True
        return datetime.now() <= self.valid_until
        
    def get_order_side(self) -> str:
        """키움증권 API용 주문 구분 반환"""
        if self.signal_type == SignalType.BUY:
            return "01"  # 매수
        elif self.signal_type == SignalType.SELL:
            return "02"  # 매도
        else:
            raise ValueError(f"주문으로 변환할 수 없는 신호 타입: {self.signal_type}")
            
    def should_execute(self, min_confidence: float = 0.7) -> bool:
        """실행해야 할 신호인지 판단"""
        return (
            self.is_valid() and 
            self.confidence >= min_confidence and
            self.signal_type in [SignalType.BUY, SignalType.SELL]
        )