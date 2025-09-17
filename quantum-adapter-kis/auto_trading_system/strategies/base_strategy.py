"""
기본 전략 인터페이스 (Strategy Pattern)
모든 매매 전략의 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..core.data_types import MarketData, Signal, SignalType, PositionType


class BaseStrategy(ABC):
    """전략 베이스 클래스"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Args:
            name: 전략 이름
            config: 전략 설정
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"strategy.{name}")

        # 전략별 기본 설정
        self.min_confidence = self.config.get('min_confidence', 0.6)
        self.position_size = self.config.get('position_size', 100)  # 기본 수량
        self.stop_loss_percent = self.config.get('stop_loss_percent', 5.0)  # 손절률
        self.take_profit_percent = self.config.get('take_profit_percent', 10.0)  # 익절률

        # 내부 상태
        self.is_active = True
        self.last_signal_time: Optional[datetime] = None
        self.signal_history: List[Signal] = []

    @abstractmethod
    def analyze_signal(self, market_data: MarketData) -> Optional[Signal]:
        """
        신호 분석 (추상 메서드)

        Args:
            market_data: 시장 데이터

        Returns:
            Signal or None
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

    def get_entry_conditions(self) -> Dict[str, Any]:
        """
        진입 조건 반환

        Returns:
            진입 조건 딕셔너리
        """
        return {
            'min_confidence': self.min_confidence,
            'position_size': self.position_size
        }

    def get_exit_conditions(self) -> Dict[str, Any]:
        """
        청산 조건 반환

        Returns:
            청산 조건 딕셔너리
        """
        return {
            'stop_loss_percent': self.stop_loss_percent,
            'take_profit_percent': self.take_profit_percent
        }

    def update_config(self, new_config: Dict[str, Any]):
        """전략 설정 업데이트"""
        self.config.update(new_config)

        # 기본 설정들 재로드
        self.min_confidence = self.config.get('min_confidence', self.min_confidence)
        self.position_size = self.config.get('position_size', self.position_size)
        self.stop_loss_percent = self.config.get('stop_loss_percent', self.stop_loss_percent)
        self.take_profit_percent = self.config.get('take_profit_percent', self.take_profit_percent)

        self.logger.info(f"전략 설정 업데이트: {new_config}")

    def add_signal_to_history(self, signal: Signal):
        """신호 히스토리에 추가"""
        self.signal_history.append(signal)
        self.last_signal_time = signal.timestamp

        # 히스토리 크기 제한 (최근 100개)
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]

    def get_recent_signals(self, count: int = 10) -> List[Signal]:
        """최근 신호 조회"""
        return self.signal_history[-count:] if self.signal_history else []

    def calculate_stop_loss(self, entry_price: float, position_type: PositionType) -> float:
        """손절가 계산"""
        if position_type == PositionType.LONG:
            return entry_price * (1 - self.stop_loss_percent / 100)
        elif position_type == PositionType.SHORT:
            return entry_price * (1 + self.stop_loss_percent / 100)
        return entry_price

    def calculate_take_profit(self, entry_price: float, position_type: PositionType) -> float:
        """익절가 계산"""
        if position_type == PositionType.LONG:
            return entry_price * (1 + self.take_profit_percent / 100)
        elif position_type == PositionType.SHORT:
            return entry_price * (1 - self.take_profit_percent / 100)
        return entry_price

    def create_signal(
        self,
        signal_type: SignalType,
        market_data: MarketData,
        confidence: float,
        reason: str,
        quantity: Optional[int] = None
    ) -> Signal:
        """신호 생성 헬퍼 메서드"""

        quantity = quantity or self.position_size

        # 손절/익절가 설정
        stop_loss = None
        take_profit = None

        if signal_type == SignalType.BUY:
            stop_loss = self.calculate_stop_loss(market_data.current_price, PositionType.LONG)
            take_profit = self.calculate_take_profit(market_data.current_price, PositionType.LONG)
        elif signal_type == SignalType.SELL:
            # 매도는 기존 포지션의 청산이므로 손절/익절 없음
            pass

        signal = Signal(
            signal_type=signal_type,
            confidence=confidence,
            price=market_data.current_price,
            quantity=quantity,
            reason=reason,
            timestamp=market_data.timestamp,
            strategy_name=self.name,
            stop_loss=stop_loss,
            take_profit=take_profit
        )

        self.add_signal_to_history(signal)
        return signal

    def is_valid_signal(self, signal: Signal) -> bool:
        """신호 유효성 검증"""
        if not self.is_active:
            return False

        if signal.confidence < self.min_confidence:
            self.logger.debug(f"신호 신뢰도 부족: {signal.confidence} < {self.min_confidence}")
            return False

        return True

    def activate(self):
        """전략 활성화"""
        self.is_active = True
        self.logger.info(f"전략 '{self.name}' 활성화")

    def deactivate(self):
        """전략 비활성화"""
        self.is_active = False
        self.logger.info(f"전략 '{self.name}' 비활성화")

    def get_status(self) -> Dict[str, Any]:
        """전략 상태 조회"""
        return {
            'name': self.name,
            'is_active': self.is_active,
            'config': self.config,
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'signal_count': len(self.signal_history),
            'entry_conditions': self.get_entry_conditions(),
            'exit_conditions': self.get_exit_conditions()
        }


class StrategyContext:
    """전략 컨텍스트 (Strategy Pattern)"""

    def __init__(self, strategy: BaseStrategy):
        """
        Args:
            strategy: 초기 전략
        """
        self._strategy = strategy
        self.logger = logging.getLogger("strategy_context")

    def set_strategy(self, strategy: BaseStrategy):
        """
        전략 변경 (런타임)

        Args:
            strategy: 새로운 전략
        """
        old_name = self._strategy.name if self._strategy else "None"
        self._strategy = strategy
        self.logger.info(f"전략 변경: {old_name} -> {strategy.name}")

    def get_strategy(self) -> BaseStrategy:
        """현재 전략 반환"""
        return self._strategy

    def execute_strategy(self, market_data: MarketData) -> Optional[Signal]:
        """
        전략 실행

        Args:
            market_data: 시장 데이터

        Returns:
            Signal or None
        """
        if not self._strategy or not self._strategy.is_active:
            return None

        try:
            signal = self._strategy.analyze_signal(market_data)

            if signal and self._strategy.is_valid_signal(signal):
                self.logger.info(f"신호 생성: {signal.signal_type.value} - {signal.reason}")
                return signal

            return None

        except Exception as e:
            self.logger.error(f"전략 실행 오류 [{self._strategy.name}]: {e}")
            return None

    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 조회"""
        if self._strategy:
            return self._strategy.get_strategy_info()
        return {}

    def get_status(self) -> Dict[str, Any]:
        """컨텍스트 상태 조회"""
        if self._strategy:
            return self._strategy.get_status()
        return {
            'name': 'None',
            'is_active': False,
            'config': {},
            'last_signal_time': None,
            'signal_count': 0
        }