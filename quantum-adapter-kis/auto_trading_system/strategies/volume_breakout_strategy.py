"""
거래량 돌파 전략
평균 거래량 대비 급증한 거래량과 함께 가격이 저항선을 돌파할 때 매수
평균 거래량 대비 급증한 거래량과 함께 가격이 지지선을 하향 돌파할 때 매도
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base_strategy import BaseStrategy
from ..core.data_types import MarketData, Signal, SignalType


class VolumeBreakoutStrategy(BaseStrategy):
    """거래량 돌파 전략"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("VolumeBreakout", config)

        # 전략 특정 설정
        self.volume_period = self.config.get('volume_period', 20)  # 평균 거래량 계산 기간
        self.volume_threshold = self.config.get('volume_threshold', 2.0)  # 거래량 임계값
        self.price_breakout_period = self.config.get('price_breakout_period', 20)  # 저항/지지선 계산 기간
        self.breakout_margin = self.config.get('breakout_margin', 0.5)  # 돌파 마진 (%)

        # 내부 상태
        self.price_history: List[float] = []
        self.volume_history: List[int] = []
        self.high_history: List[float] = []
        self.low_history: List[float] = []

    def analyze_signal(self, market_data: MarketData) -> Optional[Signal]:
        """거래량 돌파 신호 분석"""

        # 히스토리 업데이트
        self.price_history.append(market_data.current_price)
        self.volume_history.append(market_data.volume)
        self.high_history.append(market_data.high_price)
        self.low_history.append(market_data.low_price)

        # 히스토리 크기 제한
        max_history = max(self.volume_period, self.price_breakout_period) + 10
        if len(self.price_history) > max_history:
            self.price_history = self.price_history[-max_history:]
            self.volume_history = self.volume_history[-max_history:]
            self.high_history = self.high_history[-max_history:]
            self.low_history = self.low_history[-max_history:]

        # 데이터 충분성 확인
        if len(self.price_history) < max(self.volume_period, self.price_breakout_period):
            return None

        # 거래량 급증 확인
        if not self._is_volume_surge():
            return None

        # 가격 돌파 확인
        return self._check_price_breakout(market_data)

    def _is_volume_surge(self) -> bool:
        """거래량 급증 확인"""
        if len(self.volume_history) < self.volume_period + 1:
            return False

        current_volume = self.volume_history[-1]
        avg_volume = sum(self.volume_history[-self.volume_period-1:-1]) / self.volume_period

        if avg_volume == 0:
            return False

        volume_ratio = current_volume / avg_volume
        return volume_ratio >= self.volume_threshold

    def _check_price_breakout(self, market_data: MarketData) -> Optional[Signal]:
        """가격 돌파 확인"""

        # 저항선과 지지선 계산
        resistance_level = self._calculate_resistance_level()
        support_level = self._calculate_support_level()

        if resistance_level is None or support_level is None:
            return None

        current_price = market_data.current_price

        # 상향 돌파 (매수 신호)
        if self._is_upward_breakout(current_price, resistance_level):
            return self._generate_breakout_buy_signal(market_data, resistance_level)

        # 하향 돌파 (매도 신호)
        elif self._is_downward_breakout(current_price, support_level):
            return self._generate_breakout_sell_signal(market_data, support_level)

        return None

    def _calculate_resistance_level(self) -> Optional[float]:
        """저항선 계산"""
        if len(self.high_history) < self.price_breakout_period:
            return None

        # 최근 N일간 최고가들의 평균
        recent_highs = self.high_history[-self.price_breakout_period:]

        # 상위 30% 고점들의 평균을 저항선으로 설정
        sorted_highs = sorted(recent_highs, reverse=True)
        top_30_percent = int(len(sorted_highs) * 0.3)
        if top_30_percent == 0:
            top_30_percent = 1

        resistance = sum(sorted_highs[:top_30_percent]) / top_30_percent
        return resistance

    def _calculate_support_level(self) -> Optional[float]:
        """지지선 계산"""
        if len(self.low_history) < self.price_breakout_period:
            return None

        # 최근 N일간 최저가들의 평균
        recent_lows = self.low_history[-self.price_breakout_period:]

        # 하위 30% 저점들의 평균을 지지선으로 설정
        sorted_lows = sorted(recent_lows)
        bottom_30_percent = int(len(sorted_lows) * 0.3)
        if bottom_30_percent == 0:
            bottom_30_percent = 1

        support = sum(sorted_lows[:bottom_30_percent]) / bottom_30_percent
        return support

    def _is_upward_breakout(self, current_price: float, resistance_level: float) -> bool:
        """상향 돌파 확인"""
        breakout_price = resistance_level * (1 + self.breakout_margin / 100)
        return current_price > breakout_price

    def _is_downward_breakout(self, current_price: float, support_level: float) -> bool:
        """하향 돌파 확인"""
        breakout_price = support_level * (1 - self.breakout_margin / 100)
        return current_price < breakout_price

    def _generate_breakout_buy_signal(self, market_data: MarketData, resistance_level: float) -> Signal:
        """상향 돌파 매수 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_breakout_buy_confidence(market_data, resistance_level)

        volume_ratio = self._get_current_volume_ratio()
        reason = f"상향 돌파 (저항선: {resistance_level:.0f}, 거래량: {volume_ratio:.1f}배)"

        # 추가 신뢰도 요소들
        if self._is_strong_momentum():
            confidence += 0.1
            reason += " + 강한 모멘텀"

        if self._is_consecutive_green_candles():
            confidence += 0.05
            reason += " + 연속 양봉"

        signal = self.create_signal(
            signal_type=SignalType.BUY,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"거래량 돌파 매수 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _generate_breakout_sell_signal(self, market_data: MarketData, support_level: float) -> Signal:
        """하향 돌파 매도 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_breakout_sell_confidence(market_data, support_level)

        volume_ratio = self._get_current_volume_ratio()
        reason = f"하향 돌파 (지지선: {support_level:.0f}, 거래량: {volume_ratio:.1f}배)"

        # 추가 신뢰도 요소들
        if self._is_strong_bearish_momentum():
            confidence += 0.1
            reason += " + 강한 하락 모멘텀"

        if self._is_consecutive_red_candles():
            confidence += 0.05
            reason += " + 연속 음봉"

        signal = self.create_signal(
            signal_type=SignalType.SELL,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"거래량 돌파 매도 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _calculate_breakout_buy_confidence(self, market_data: MarketData, resistance_level: float) -> float:
        """상향 돌파 매수 신뢰도 계산"""
        confidence = 0.7  # 기본 신뢰도

        # 돌파 강도
        breakout_strength = (market_data.current_price - resistance_level) / resistance_level * 100
        if breakout_strength > 3.0:
            confidence += 0.15
        elif breakout_strength > 1.5:
            confidence += 0.1

        # 거래량 강도
        volume_ratio = self._get_current_volume_ratio()
        if volume_ratio > 3.0:
            confidence += 0.15
        elif volume_ratio > 2.5:
            confidence += 0.1

        return confidence

    def _calculate_breakout_sell_confidence(self, market_data: MarketData, support_level: float) -> float:
        """하향 돌파 매도 신뢰도 계산"""
        confidence = 0.7  # 기본 신뢰도

        # 돌파 강도
        breakout_strength = (support_level - market_data.current_price) / support_level * 100
        if breakout_strength > 3.0:
            confidence += 0.15
        elif breakout_strength > 1.5:
            confidence += 0.1

        # 거래량 강도
        volume_ratio = self._get_current_volume_ratio()
        if volume_ratio > 3.0:
            confidence += 0.15
        elif volume_ratio > 2.5:
            confidence += 0.1

        return confidence

    def _get_current_volume_ratio(self) -> float:
        """현재 거래량 비율 계산"""
        if len(self.volume_history) < self.volume_period + 1:
            return 0.0

        current_volume = self.volume_history[-1]
        avg_volume = sum(self.volume_history[-self.volume_period-1:-1]) / self.volume_period

        if avg_volume == 0:
            return 0.0

        return current_volume / avg_volume

    def _is_strong_momentum(self) -> bool:
        """강한 상승 모멘텀 확인"""
        if len(self.price_history) < 3:
            return False

        # 최근 3일간 지속적인 상승
        return all(self.price_history[i] < self.price_history[i+1]
                  for i in range(-3, -1))

    def _is_strong_bearish_momentum(self) -> bool:
        """강한 하락 모멘텀 확인"""
        if len(self.price_history) < 3:
            return False

        # 최근 3일간 지속적인 하락
        return all(self.price_history[i] > self.price_history[i+1]
                  for i in range(-3, -1))

    def _is_consecutive_green_candles(self) -> bool:
        """연속 양봉 확인"""
        if len(self.price_history) < 3:
            return False

        # 최근 2일간 양봉
        recent_opens = self.price_history[-3:-1]  # 전일, 전전일 종가가 다음날 시가로 근사
        recent_closes = self.price_history[-2:]   # 전일, 당일 종가

        return all(recent_closes[i] > recent_opens[i] for i in range(len(recent_opens)))

    def _is_consecutive_red_candles(self) -> bool:
        """연속 음봉 확인"""
        if len(self.price_history) < 3:
            return False

        # 최근 2일간 음봉
        recent_opens = self.price_history[-3:-1]  # 전일, 전전일 종가가 다음날 시가로 근사
        recent_closes = self.price_history[-2:]   # 전일, 당일 종가

        return all(recent_closes[i] < recent_opens[i] for i in range(len(recent_opens)))

    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            'name': self.name,
            'description': '거래량 급증을 동반한 가격 돌파 전략',
            'parameters': {
                'volume_period': self.volume_period,
                'volume_threshold': self.volume_threshold,
                'price_breakout_period': self.price_breakout_period,
                'breakout_margin': self.breakout_margin,
                'min_confidence': self.min_confidence
            },
            'signals': {
                'buy': f'저항선 상향 돌파 + 거래량 {self.volume_threshold}배 이상',
                'sell': f'지지선 하향 돌파 + 거래량 {self.volume_threshold}배 이상'
            },
            'current_state': {
                'price_data_count': len(self.price_history),
                'volume_data_count': len(self.volume_history),
                'current_volume_ratio': self._get_current_volume_ratio(),
                'resistance_level': self._calculate_resistance_level(),
                'support_level': self._calculate_support_level()
            }
        }