"""
자동매매 시스템 데이터 타입 정의
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json


class SignalType(Enum):
    """매매 신호 타입"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NONE = "NONE"


class PositionType(Enum):
    """포지션 타입"""
    LONG = "LONG"
    SHORT = "SHORT"
    CASH = "CASH"


class OrderType(Enum):
    """주문 타입"""
    MARKET = "MARKET"      # 시장가
    LIMIT = "LIMIT"        # 지정가
    STOP = "STOP"          # 손절


class OrderStatus(Enum):
    """주문 상태"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class MarketData:
    """시장 데이터"""
    symbol: str
    timestamp: datetime
    current_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int

    # 기술적 지표 (옵션)
    rsi: Optional[float] = None
    ma5: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'current_price': self.current_price,
            'open_price': self.open_price,
            'high_price': self.high_price,
            'low_price': self.low_price,
            'volume': self.volume,
            'rsi': self.rsi,
            'ma5': self.ma5,
            'ma20': self.ma20,
            'ma60': self.ma60,
            'bb_upper': self.bb_upper,
            'bb_lower': self.bb_lower,
            'macd': self.macd,
            'macd_signal': self.macd_signal
        }


@dataclass
class Signal:
    """매매 신호"""
    signal_type: SignalType
    confidence: float  # 신뢰도 (0.0 ~ 1.0)
    price: float
    quantity: int
    reason: str
    timestamp: datetime
    strategy_name: str

    # 리스크 관리
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'signal_type': self.signal_type.value,
            'confidence': self.confidence,
            'price': self.price,
            'quantity': self.quantity,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat(),
            'strategy_name': self.strategy_name,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit
        }


@dataclass
class Position:
    """포지션 정보"""
    symbol: str
    position_type: PositionType
    quantity: int
    entry_price: float
    current_price: float
    entry_time: datetime

    def get_unrealized_pnl(self) -> float:
        """미실현 손익 계산"""
        if self.position_type == PositionType.LONG:
            return (self.current_price - self.entry_price) * self.quantity
        elif self.position_type == PositionType.SHORT:
            return (self.entry_price - self.current_price) * self.quantity
        else:
            return 0.0

    def get_unrealized_pnl_percent(self) -> float:
        """미실현 손익률 계산"""
        if self.entry_price == 0:
            return 0.0
        return (self.get_unrealized_pnl() / (self.entry_price * abs(self.quantity))) * 100

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'symbol': self.symbol,
            'position_type': self.position_type.value,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'entry_time': self.entry_time.isoformat(),
            'unrealized_pnl': self.get_unrealized_pnl(),
            'unrealized_pnl_percent': self.get_unrealized_pnl_percent()
        }


@dataclass
class Order:
    """주문 정보"""
    order_id: str
    symbol: str
    order_type: OrderType
    signal_type: SignalType
    quantity: int
    price: float
    status: OrderStatus
    created_time: datetime
    filled_time: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'order_type': self.order_type.value,
            'signal_type': self.signal_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status.value,
            'created_time': self.created_time.isoformat(),
            'filled_time': self.filled_time.isoformat() if self.filled_time else None,
            'filled_price': self.filled_price,
            'filled_quantity': self.filled_quantity
        }


@dataclass
class TradingStats:
    """매매 통계"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    def update_stats(self, pnl: float):
        """통계 업데이트"""
        self.total_trades += 1
        self.total_pnl += pnl

        if pnl > 0:
            self.winning_trades += 1
            self.avg_win = (self.avg_win * (self.winning_trades - 1) + pnl) / self.winning_trades
        else:
            self.losing_trades += 1
            self.avg_loss = (self.avg_loss * (self.losing_trades - 1) + pnl) / self.losing_trades

        # 승률 계산
        self.win_rate = (self.winning_trades / self.total_trades) * 100 if self.total_trades > 0 else 0

        # 수익 팩터 계산
        if self.avg_loss != 0:
            self.profit_factor = abs(self.avg_win / self.avg_loss)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor
        }