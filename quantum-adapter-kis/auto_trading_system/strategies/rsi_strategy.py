"""
RSI 전략
RSI(Relative Strength Index) 지표를 사용한 과매수/과매도 매매 전략
RSI 30 이하일 때 매수, RSI 70 이상일 때 매도
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base_strategy import BaseStrategy
from ..core.data_types import MarketData, Signal, SignalType


class RSIStrategy(BaseStrategy):
    """RSI 전략"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("RSI", config)

        # 전략 특정 설정
        self.rsi_period = self.config.get('rsi_period', 14)
        self.oversold_threshold = self.config.get('oversold_threshold', 30)
        self.overbought_threshold = self.config.get('overbought_threshold', 70)
        self.extreme_oversold = self.config.get('extreme_oversold', 20)
        self.extreme_overbought = self.config.get('extreme_overbought', 80)

        # 내부 상태
        self.price_history: List[float] = []
        self.rsi_history: List[float] = []
        self.gains: List[float] = []
        self.losses: List[float] = []

    def analyze_signal(self, market_data: MarketData) -> Optional[Signal]:
        """RSI 기반 신호 분석"""

        # 가격 히스토리 업데이트
        self.price_history.append(market_data.current_price)

        # 히스토리 크기 제한
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]

        # RSI 계산
        rsi = self._calculate_rsi()
        if rsi is None:
            return None

        # MarketData에 RSI 설정
        market_data.rsi = rsi

        # RSI 히스토리 업데이트
        self.rsi_history.append(rsi)
        if len(self.rsi_history) > 50:
            self.rsi_history = self.rsi_history[-50:]

        # 신호 분석
        return self._analyze_rsi_signal(market_data, rsi)

    def _calculate_rsi(self) -> Optional[float]:
        """RSI 계산"""
        if len(self.price_history) < self.rsi_period + 1:
            return None

        # 가격 변화량 계산
        if len(self.gains) == 0:
            # 초기 계산
            for i in range(1, len(self.price_history)):
                change = self.price_history[i] - self.price_history[i-1]
                if change > 0:
                    self.gains.append(change)
                    self.losses.append(0)
                else:
                    self.gains.append(0)
                    self.losses.append(abs(change))
        else:
            # 증분 계산
            change = self.price_history[-1] - self.price_history[-2]
            if change > 0:
                self.gains.append(change)
                self.losses.append(0)
            else:
                self.gains.append(0)
                self.losses.append(abs(change))

        # 히스토리 크기 제한
        if len(self.gains) > 100:
            self.gains = self.gains[-100:]
            self.losses = self.losses[-100:]

        if len(self.gains) < self.rsi_period:
            return None

        # RSI 계산
        avg_gain = sum(self.gains[-self.rsi_period:]) / self.rsi_period
        avg_loss = sum(self.losses[-self.rsi_period:]) / self.rsi_period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _analyze_rsi_signal(self, market_data: MarketData, rsi: float) -> Optional[Signal]:
        """RSI 신호 분석"""

        # 과매도 영역 (매수 신호)
        if rsi <= self.oversold_threshold:
            return self._generate_buy_signal(market_data, rsi)

        # 과매수 영역 (매도 신호)
        elif rsi >= self.overbought_threshold:
            return self._generate_sell_signal(market_data, rsi)

        # 다이버전스 확인
        divergence_signal = self._check_divergence(market_data, rsi)
        if divergence_signal:
            return divergence_signal

        return None

    def _generate_buy_signal(self, market_data: MarketData, rsi: float) -> Signal:
        """과매도 매수 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_buy_confidence(rsi)

        reason = f"RSI 과매도 ({rsi:.1f} ≤ {self.oversold_threshold})"

        # 극도 과매도 상태
        if rsi <= self.extreme_oversold:
            confidence += 0.15
            reason += " - 극도 과매도"

        # 연속 하락 확인
        if self._is_continuous_decline():
            confidence += 0.1
            reason += " + 연속 하락"

        signal = self.create_signal(
            signal_type=SignalType.BUY,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"RSI 매수 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _generate_sell_signal(self, market_data: MarketData, rsi: float) -> Signal:
        """과매수 매도 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_sell_confidence(rsi)

        reason = f"RSI 과매수 ({rsi:.1f} ≥ {self.overbought_threshold})"

        # 극도 과매수 상태
        if rsi >= self.extreme_overbought:
            confidence += 0.15
            reason += " - 극도 과매수"

        # 연속 상승 확인
        if self._is_continuous_rise():
            confidence += 0.1
            reason += " + 연속 상승"

        signal = self.create_signal(
            signal_type=SignalType.SELL,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"RSI 매도 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _calculate_buy_confidence(self, rsi: float) -> float:
        """매수 신호 신뢰도 계산"""
        confidence = 0.6  # 기본 신뢰도

        # RSI가 낮을수록 신뢰도 증가
        if rsi <= 20:
            confidence += 0.3
        elif rsi <= 25:
            confidence += 0.2
        elif rsi <= 30:
            confidence += 0.1

        return confidence

    def _calculate_sell_confidence(self, rsi: float) -> float:
        """매도 신호 신뢰도 계산"""
        confidence = 0.6  # 기본 신뢰도

        # RSI가 높을수록 신뢰도 증가
        if rsi >= 80:
            confidence += 0.3
        elif rsi >= 75:
            confidence += 0.2
        elif rsi >= 70:
            confidence += 0.1

        return confidence

    def _is_continuous_decline(self) -> bool:
        """연속 하락 확인"""
        if len(self.price_history) < 3:
            return False

        # 최근 3일간 하락
        return all(self.price_history[i] > self.price_history[i+1]
                  for i in range(-3, -1))

    def _is_continuous_rise(self) -> bool:
        """연속 상승 확인"""
        if len(self.price_history) < 3:
            return False

        # 최근 3일간 상승
        return all(self.price_history[i] < self.price_history[i+1]
                  for i in range(-3, -1))

    def _check_divergence(self, market_data: MarketData, rsi: float) -> Optional[Signal]:
        """다이버전스 확인"""
        if len(self.price_history) < 10 or len(self.rsi_history) < 10:
            return None

        # 불리쉬 다이버전스 (가격 하락, RSI 상승)
        bullish_div = self._check_bullish_divergence()
        if bullish_div:
            confidence = 0.7
            reason = "불리쉬 다이버전스 (가격↓, RSI↑)"

            return self.create_signal(
                signal_type=SignalType.BUY,
                market_data=market_data,
                confidence=confidence,
                reason=reason
            )

        # 베어리쉬 다이버전스 (가격 상승, RSI 하락)
        bearish_div = self._check_bearish_divergence()
        if bearish_div:
            confidence = 0.7
            reason = "베어리쉬 다이버전스 (가격↑, RSI↓)"

            return self.create_signal(
                signal_type=SignalType.SELL,
                market_data=market_data,
                confidence=confidence,
                reason=reason
            )

        return None

    def _check_bullish_divergence(self) -> bool:
        """불리쉬 다이버전스 확인"""
        if len(self.price_history) < 20 or len(self.rsi_history) < 20:
            return False

        # 최근 10일과 그 이전 10일 비교
        recent_prices = self.price_history[-10:]
        past_prices = self.price_history[-20:-10]
        recent_rsi = self.rsi_history[-10:]
        past_rsi = self.rsi_history[-20:-10]

        # 가격 저점 하락
        min_recent_price = min(recent_prices)
        min_past_price = min(past_prices)
        price_declining = min_recent_price < min_past_price

        # RSI 저점 상승
        min_recent_rsi = min(recent_rsi)
        min_past_rsi = min(past_rsi)
        rsi_rising = min_recent_rsi > min_past_rsi

        return price_declining and rsi_rising

    def _check_bearish_divergence(self) -> bool:
        """베어리쉬 다이버전스 확인"""
        if len(self.price_history) < 20 or len(self.rsi_history) < 20:
            return False

        # 최근 10일과 그 이전 10일 비교
        recent_prices = self.price_history[-10:]
        past_prices = self.price_history[-20:-10]
        recent_rsi = self.rsi_history[-10:]
        past_rsi = self.rsi_history[-20:-10]

        # 가격 고점 상승
        max_recent_price = max(recent_prices)
        max_past_price = max(past_prices)
        price_rising = max_recent_price > max_past_price

        # RSI 고점 하락
        max_recent_rsi = max(recent_rsi)
        max_past_rsi = max(past_rsi)
        rsi_declining = max_recent_rsi < max_past_rsi

        return price_rising and rsi_declining

    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            'name': self.name,
            'description': 'RSI 과매수/과매도 기반 매매 전략',
            'parameters': {
                'rsi_period': self.rsi_period,
                'oversold_threshold': self.oversold_threshold,
                'overbought_threshold': self.overbought_threshold,
                'extreme_oversold': self.extreme_oversold,
                'extreme_overbought': self.extreme_overbought,
                'min_confidence': self.min_confidence
            },
            'signals': {
                'buy': f'RSI ≤ {self.oversold_threshold} (과매도)',
                'sell': f'RSI ≥ {self.overbought_threshold} (과매수)',
                'bullish_divergence': '가격 하락 + RSI 상승',
                'bearish_divergence': '가격 상승 + RSI 하락'
            },
            'current_state': {
                'price_data_count': len(self.price_history),
                'rsi_data_count': len(self.rsi_history),
                'current_rsi': self.rsi_history[-1] if self.rsi_history else None,
                'gains_count': len(self.gains),
                'losses_count': len(self.losses)
            }
        }