"""
전략 설정 데이터 모델

전략 실행을 위한 설정과 파라미터들을 정의하는 모델
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class StrategyType(Enum):
    """전략 타입"""
    MOVING_AVERAGE_CROSSOVER = "moving_average_crossover"
    RSI_MEAN_REVERSION = "rsi_mean_reversion"
    BOLLINGER_BANDS = "bollinger_bands"
    MACD_DIVERGENCE = "macd_divergence"


class RiskLevel(Enum):
    """리스크 레벨"""
    CONSERVATIVE = "conservative"  # 보수적
    MODERATE = "moderate"         # 보통
    AGGRESSIVE = "aggressive"     # 공격적


class StrategyConfig(BaseModel):
    """
    전략 설정 모델
    
    전략 실행에 필요한 모든 설정과 파라미터를 정의한다.
    """
    
    # 기본 설정
    strategy_name: str = Field(description="전략명")
    strategy_type: StrategyType = Field(description="전략 타입")
    enabled: bool = Field(default=True, description="전략 활성화 여부")
    
    # 대상 종목
    target_symbols: List[str] = Field(description="대상 종목 리스트 (6자리 코드)")
    
    # 리스크 관리
    risk_level: RiskLevel = Field(default=RiskLevel.MODERATE, description="리스크 레벨")
    max_position_size: Decimal = Field(description="최대 포지션 크기 (원)")
    max_positions: int = Field(default=5, description="최대 동시 포지션 수")
    stop_loss_ratio: float = Field(default=0.05, description="손절 비율")
    take_profit_ratio: float = Field(default=0.10, description="익절 비율")
    
    # 실행 설정  
    execution_interval: int = Field(default=60, description="실행 주기 (초)")
    min_confidence: float = Field(default=0.7, description="최소 신뢰도")
    dry_run: bool = Field(default=True, description="모의 실행 여부")
    
    # 전략별 파라미터
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="전략별 파라미터")
    
    # 알림 설정
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "signal_generated": True,
            "order_executed": True, 
            "position_closed": True,
            "error_occurred": True
        },
        description="알림 설정"
    )
    
    @validator('target_symbols')
    def validate_symbols(cls, v):
        """종목 코드 검증"""
        for symbol in v:
            if not symbol.isdigit() or len(symbol) != 6:
                raise ValueError(f"잘못된 종목코드 형식: {symbol}")
        return v
    
    @validator('stop_loss_ratio', 'take_profit_ratio')
    def validate_ratios(cls, v):
        """비율 검증"""
        if not 0.0 < v <= 1.0:
            raise ValueError("비율은 0.0과 1.0 사이여야 합니다")
        return v
    
    @validator('min_confidence')
    def validate_confidence(cls, v):
        """신뢰도 검증"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("신뢰도는 0.0과 1.0 사이여야 합니다")
        return v
    
    def get_strategy_param(self, key: str, default: Any = None) -> Any:
        """전략 파라미터 조회"""
        return self.strategy_params.get(key, default)
        
    def set_strategy_param(self, key: str, value: Any) -> None:
        """전략 파라미터 설정"""
        self.strategy_params[key] = value
        
    def get_risk_multiplier(self) -> float:
        """리스크 레벨에 따른 배수 반환"""
        multipliers = {
            RiskLevel.CONSERVATIVE: 0.5,
            RiskLevel.MODERATE: 1.0,
            RiskLevel.AGGRESSIVE: 2.0
        }
        return multipliers.get(self.risk_level, 1.0)
        
    def calculate_position_size(self, available_capital: Decimal, confidence: float) -> Decimal:
        """신뢰도와 리스크 레벨을 고려한 포지션 크기 계산"""
        base_size = min(available_capital * Decimal("0.1"), self.max_position_size)
        risk_multiplier = Decimal(str(self.get_risk_multiplier()))
        confidence_multiplier = Decimal(str(confidence))
        
        return base_size * risk_multiplier * confidence_multiplier