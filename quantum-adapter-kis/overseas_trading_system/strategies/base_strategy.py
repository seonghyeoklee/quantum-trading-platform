"""
해외주식 거래 전략 기본 클래스
전략 패턴을 구현하여 런타임에 전략 변경 가능
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from collections import deque

from overseas_trading_system.core.overseas_data_types import (
    OverseasMarketData, OverseasTradingSignal, SignalType, ExchangeType, TradingSession
)


class BaseOverseasStrategy(ABC):
    """해외주식 거래 전략 기본 클래스"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__

        # 데이터 히스토리
        self.price_history: deque = deque(maxlen=100)
        self.volume_history: deque = deque(maxlen=100)

        # 전략 상태
        self.last_signal: Optional[OverseasTradingSignal] = None
        self.signal_count = 0

    @abstractmethod
    def analyze_signal(self, market_data: OverseasMarketData) -> Optional[OverseasTradingSignal]:
        """
        시장 데이터를 분석하여 매매 신호 생성

        Args:
            market_data: 해외주식 시장 데이터

        Returns:
            OverseasTradingSignal: 매매 신호 (None이면 신호 없음)
        """
        pass

    def add_market_data(self, market_data: OverseasMarketData):
        """시장 데이터 히스토리에 추가"""
        self.price_history.append(market_data.current_price)
        self.volume_history.append(market_data.volume)

    def get_average_price(self, period: int = 20) -> float:
        """이동평균 계산"""
        if len(self.price_history) < period:
            return 0.0

        recent_prices = list(self.price_history)[-period:]
        return sum(recent_prices) / len(recent_prices)

    def get_average_volume(self, period: int = 20) -> float:
        """평균 거래량 계산"""
        if len(self.volume_history) < period:
            return 0.0

        recent_volumes = list(self.volume_history)[-period:]
        return sum(recent_volumes) / len(recent_volumes)

    def calculate_rsi(self, period: int = 14) -> float:
        """RSI 계산"""
        if len(self.price_history) < period + 1:
            return 50.0

        prices = list(self.price_history)[-period-1:]
        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if len(gains) == 0:
            return 50.0

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def is_volume_spike(self, threshold: float = 2.0) -> bool:
        """거래량 급증 확인"""
        if len(self.volume_history) < 2:
            return False

        current_volume = self.volume_history[-1]
        avg_volume = self.get_average_volume(20)

        return current_volume > avg_volume * threshold

    def is_pre_market_active(self, market_data: OverseasMarketData) -> bool:
        """프리마켓 활성 시간 확인"""
        return market_data.trading_session == TradingSession.PRE_MARKET

    def is_regular_hours(self, market_data: OverseasMarketData) -> bool:
        """정규장 시간 확인"""
        return market_data.trading_session == TradingSession.REGULAR

    def is_after_hours(self, market_data: OverseasMarketData) -> bool:
        """애프터아워스 시간 확인"""
        return market_data.trading_session == TradingSession.AFTER_HOURS

    def get_volatility(self, period: int = 20) -> float:
        """변동성 계산 (표준편차)"""
        if len(self.price_history) < period:
            return 0.0

        prices = list(self.price_history)[-period:]
        mean_price = sum(prices) / len(prices)

        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        return variance ** 0.5

    def create_signal(
        self,
        market_data: OverseasMarketData,
        signal_type: SignalType,
        confidence: float,
        reason: str,
        quantity: int = 1
    ) -> OverseasTradingSignal:
        """매매 신호 생성"""
        signal = OverseasTradingSignal(
            symbol=market_data.symbol,
            exchange=market_data.exchange,
            signal_type=signal_type,
            confidence=confidence,
            price=market_data.current_price,
            quantity=quantity,
            reason=reason,
            session=market_data.trading_session
        )

        self.last_signal = signal
        self.signal_count += 1

        return signal

    def get_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            'name': self.name,
            'signal_count': self.signal_count,
            'last_signal_type': self.last_signal.signal_type.value if self.last_signal else 'NONE',
            'data_points': len(self.price_history),
            'config': self.config
        }

    def reset(self):
        """전략 상태 초기화"""
        self.price_history.clear()
        self.volume_history.clear()
        self.last_signal = None
        self.signal_count = 0