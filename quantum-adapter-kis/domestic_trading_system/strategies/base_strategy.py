"""
국내주식 거래 전략 기본 클래스
모든 거래 전략의 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from domestic_trading_system.core.domestic_data_types import DomesticMarketData


class BaseDomesticStrategy(ABC):
    """국내주식 거래 전략 기본 클래스"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__

        # 기본 설정
        self.min_data_points = config.get('min_data_points', 20)
        self.max_position_size = config.get('max_position_size', 1)

        # 전략 상태
        self.last_signal_time = None
        self.signal_cooldown = config.get('signal_cooldown', 60)  # 초

    @abstractmethod
    async def generate_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData) -> Optional[Dict[str, Any]]:
        """
        매매 신호 생성

        Args:
            history: 과거 시장 데이터 리스트
            current_data: 현재 시장 데이터

        Returns:
            신호 딕셔너리 또는 None
            {
                'type': 'BUY' 또는 'SELL',
                'confidence': 0.0 ~ 1.0,
                'reason': '신호 발생 이유',
                'quantity': 주문 수량
            }
        """
        pass

    def can_generate_signal(self) -> bool:
        """신호 생성 가능 여부 확인 (쿨다운 체크)"""
        if self.last_signal_time is None:
            return True

        time_diff = (datetime.now() - self.last_signal_time).total_seconds()
        return time_diff >= self.signal_cooldown

    def update_signal_time(self):
        """마지막 신호 생성 시간 업데이트"""
        self.last_signal_time = datetime.now()

    def get_price_change_percent(self, history: List[DomesticMarketData], periods: int = 1) -> float:
        """가격 변화율 계산"""
        if len(history) < periods + 1:
            return 0.0

        current_price = history[-1].current_price
        past_price = history[-(periods + 1)].current_price

        if past_price == 0:
            return 0.0

        return ((current_price - past_price) / past_price) * 100

    def get_simple_moving_average(self, history: List[DomesticMarketData], periods: int) -> float:
        """단순 이동평균 계산"""
        if len(history) < periods:
            return 0.0

        prices = [data.current_price for data in history[-periods:]]
        return sum(prices) / len(prices)

    def get_volume_average(self, history: List[DomesticMarketData], periods: int) -> float:
        """거래량 평균 계산"""
        if len(history) < periods:
            return 0.0

        volumes = [data.volume for data in history[-periods:]]
        return sum(volumes) / len(volumes)

    def is_price_breakout(self, history: List[DomesticMarketData], periods: int = 20) -> bool:
        """가격 돌파 여부 확인"""
        if len(history) < periods + 1:
            return False

        current_price = history[-1].current_price
        recent_high = max([data.high_price for data in history[-periods:-1]])

        return current_price > recent_high

    def is_volume_surge(self, history: List[DomesticMarketData], threshold: float = 2.0, periods: int = 20) -> bool:
        """거래량 급증 여부 확인"""
        if len(history) < periods + 1:
            return False

        current_volume = history[-1].volume
        avg_volume = self.get_volume_average(history[:-1], periods)

        if avg_volume == 0:
            return False

        return current_volume > (avg_volume * threshold)

    def calculate_rsi(self, history: List[DomesticMarketData], periods: int = 14) -> float:
        """RSI 계산"""
        if len(history) < periods + 1:
            return 50.0

        prices = [data.current_price for data in history]
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        gains = [delta if delta > 0 else 0 for delta in deltas[-periods:]]
        losses = [-delta if delta < 0 else 0 for delta in deltas[-periods:]]

        avg_gain = sum(gains) / periods if gains else 0
        avg_loss = sum(losses) / periods if losses else 0

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def get_bollinger_bands(self, history: List[DomesticMarketData], periods: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """볼린저 밴드 계산"""
        if len(history) < periods:
            return {'upper': 0, 'middle': 0, 'lower': 0}

        prices = [data.current_price for data in history[-periods:]]
        sma = sum(prices) / len(prices)

        # 표준편차 계산
        variance = sum([(price - sma) ** 2 for price in prices]) / len(prices)
        std = variance ** 0.5

        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }

    def get_current_analysis(self) -> Dict[str, Any]:
        """현재 전략 분석 정보 반환 (기본 구현)"""
        return {
            'strategy': self.name,
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'can_generate_signal': self.can_generate_signal(),
            'config': self.config
        }