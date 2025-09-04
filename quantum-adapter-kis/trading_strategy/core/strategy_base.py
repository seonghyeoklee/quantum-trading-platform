"""
전략 베이스 클래스
모든 매매 전략의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class StrategyConfig:
    """전략 설정"""
    symbol: str
    symbol_name: str
    investment_amount: float = 10000000  # 투자금액 (기본 1000만원)
    stop_loss_percent: float = -5.0      # 손절률 (기본 -5%)
    take_profit_percent: float = 10.0    # 익절률 (기본 +10%)
    is_active: bool = True               # 활성화 여부

class StrategyBase(ABC):
    """전략 베이스 클래스"""
    
    def __init__(self, config: StrategyConfig):
        """
        Args:
            config: 전략 설정
        """
        self.config = config
        self.name = self.__class__.__name__
        self.position: Optional[Dict[str, Any]] = None
        self.trade_history: List[Dict[str, Any]] = []
        
        logger.info(f"{self.name} 전략 초기화: {config.symbol_name}")
    
    @abstractmethod
    async def analyze_signal(self, market_data: Dict[str, Any]) -> Optional[str]:
        """
        신호 분석 (추상 메서드)
        
        Args:
            market_data: 시장 데이터
        
        Returns:
            'BUY', 'SELL', 'HOLD' 또는 None
        """
        pass
    
    @abstractmethod
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        전략 정보 반환 (추상 메서드)
        
        Returns:
            전략 정보 딕셔너리
        """
        pass
    
    def update_position(self, position_data: Dict[str, Any]):
        """포지션 업데이트"""
        self.position = position_data
        logger.info(f"{self.name} 포지션 업데이트: {position_data}")
    
    def add_trade_record(self, trade_data: Dict[str, Any]):
        """거래 기록 추가"""
        trade_data['timestamp'] = datetime.now().isoformat()
        trade_data['strategy'] = self.name
        self.trade_history.append(trade_data)
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """성과 요약"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'total_profit': 0,
                'win_rate': 0,
                'max_drawdown': 0
            }
        
        buy_trades = [t for t in self.trade_history if t.get('type') == 'BUY']
        sell_trades = [t for t in self.trade_history if t.get('type') == 'SELL']
        
        total_profit = sum(t.get('profit', 0) for t in sell_trades)
        winning_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        
        return {
            'total_trades': len(buy_trades),
            'total_profit': total_profit,
            'win_rate': len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0,
            'winning_trades': len(winning_trades),
            'losing_trades': len(sell_trades) - len(winning_trades)
        }