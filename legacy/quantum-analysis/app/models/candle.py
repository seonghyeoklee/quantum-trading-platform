from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional

class StockCandle(BaseModel):
    """주식 캔들 데이터 모델"""
    
    id: Optional[int] = None
    symbol: str = Field(..., min_length=1, max_length=20, description="종목코드")
    timeframe: str = Field(..., description="시간 단위 (1m, 5m, 15m, 30m, 1h, 1d)")
    timestamp: datetime = Field(..., description="시간")
    open_price: Decimal = Field(..., gt=0, description="시가")
    high_price: Decimal = Field(..., gt=0, description="고가")
    low_price: Decimal = Field(..., gt=0, description="저가")
    close_price: Decimal = Field(..., gt=0, description="종가")
    volume: int = Field(..., ge=0, description="거래량")
    created_at: Optional[datetime] = None
    
    @validator('timeframe')
    def validate_timeframe(cls, v):
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '1d', '1w', '1M']
        if v not in valid_timeframes:
            raise ValueError(f'Invalid timeframe: {v}. Must be one of {valid_timeframes}')
        return v
    
    @validator('high_price')
    def validate_high_price(cls, v, values):
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('High price cannot be lower than low price')
        return v
    
    @validator('open_price')
    def validate_open_price(cls, v, values):
        if 'low_price' in values and 'high_price' in values:
            if v < values['low_price'] or v > values['high_price']:
                raise ValueError('Open price must be between low and high prices')
        return v
    
    @validator('close_price')
    def validate_close_price(cls, v, values):
        if 'low_price' in values and 'high_price' in values:
            if v < values['low_price'] or v > values['high_price']:
                raise ValueError('Close price must be between low and high prices')
        return v
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }
    
    # 기술적 분석을 위한 계산 메서드들
    
    def body_size(self) -> Decimal:
        """몸통 크기 계산"""
        return abs(self.close_price - self.open_price)
    
    def upper_shadow_length(self) -> Decimal:
        """상한가 길이"""
        body_top = max(self.open_price, self.close_price)
        return self.high_price - body_top
    
    def lower_shadow_length(self) -> Decimal:
        """하한가 길이"""
        body_bottom = min(self.open_price, self.close_price)
        return body_bottom - self.low_price
    
    def is_bullish(self) -> bool:
        """양봉 여부"""
        return self.close_price > self.open_price
    
    def is_bearish(self) -> bool:
        """음봉 여부"""
        return self.close_price < self.open_price
    
    def is_doji(self) -> bool:
        """도지 여부"""
        return self.close_price == self.open_price
    
    def price_range(self) -> Decimal:
        """가격 범위 (고가 - 저가)"""
        return self.high_price - self.low_price
    
    def typical_price(self) -> Decimal:
        """대표가격 (HLC/3)"""
        return (self.high_price + self.low_price + self.close_price) / 3