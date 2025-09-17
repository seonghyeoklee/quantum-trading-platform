"""
평균회귀 전략
볼린저 밴드를 이용한 평균회귀 매매 전략
가격이 하단 밴드 근처에서 매수, 상단 밴드 근처에서 매도
"""

from typing import Dict, Any, Optional, List
import math
import logging

from .base_strategy import BaseStrategy
from ..core.data_types import MarketData, Signal, SignalType


class MeanReversionStrategy(BaseStrategy):
    """평균회귀 전략"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("MeanReversion", config)

        # 전략 특정 설정
        self.bb_period = self.config.get('bb_period', 20)  # 볼린저 밴드 기간
        self.bb_std_dev = self.config.get('bb_std_dev', 2.0)  # 표준편차 배수
        self.reversion_threshold = self.config.get('reversion_threshold', 0.1)  # 회귀 임계값
        self.oversold_ratio = self.config.get('oversold_ratio', 0.05)  # 과매도 비율
        self.overbought_ratio = self.config.get('overbought_ratio', 0.95)  # 과매수 비율

        # 내부 상태
        self.price_history: List[float] = []
        self.bb_upper_history: List[float] = []
        self.bb_lower_history: List[float] = []
        self.bb_middle_history: List[float] = []

    def analyze_signal(self, market_data: MarketData) -> Optional[Signal]:
        """평균회귀 신호 분석"""

        # 가격 히스토리 업데이트
        self.price_history.append(market_data.current_price)

        # 히스토리 크기 제한
        if len(self.price_history) > self.bb_period + 50:
            self.price_history = self.price_history[-(self.bb_period + 50):]

        # 볼린저 밴드 계산
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands()

        if bb_upper is None or bb_middle is None or bb_lower is None:
            return None

        # MarketData에 볼린저 밴드 설정
        market_data.bb_upper = bb_upper
        market_data.bb_lower = bb_lower

        # 볼린저 밴드 히스토리 업데이트
        self.bb_upper_history.append(bb_upper)
        self.bb_middle_history.append(bb_middle)
        self.bb_lower_history.append(bb_lower)

        # 히스토리 크기 제한
        if len(self.bb_upper_history) > 50:
            self.bb_upper_history = self.bb_upper_history[-50:]
            self.bb_middle_history = self.bb_middle_history[-50:]
            self.bb_lower_history = self.bb_lower_history[-50:]

        # 평균회귀 신호 분석
        return self._analyze_mean_reversion_signal(market_data, bb_upper, bb_middle, bb_lower)

    def _calculate_bollinger_bands(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """볼린저 밴드 계산"""
        if len(self.price_history) < self.bb_period:
            return None, None, None

        # 최근 N일 가격 데이터
        recent_prices = self.price_history[-self.bb_period:]

        # 중간선 (이동평균)
        middle = sum(recent_prices) / len(recent_prices)

        # 표준편차 계산
        variance = sum((price - middle) ** 2 for price in recent_prices) / len(recent_prices)
        std_dev = math.sqrt(variance)

        # 상단/하단 밴드
        upper = middle + (std_dev * self.bb_std_dev)
        lower = middle - (std_dev * self.bb_std_dev)

        return upper, middle, lower

    def _analyze_mean_reversion_signal(
        self,
        market_data: MarketData,
        bb_upper: float,
        bb_middle: float,
        bb_lower: float
    ) -> Optional[Signal]:
        """평균회귀 신호 분석"""

        current_price = market_data.current_price

        # 밴드 내 위치 계산 (0: 하단, 1: 상단)
        band_position = (current_price - bb_lower) / (bb_upper - bb_lower)

        # 과매도 영역 (매수 신호)
        if band_position <= self.oversold_ratio:
            return self._generate_mean_reversion_buy_signal(
                market_data, bb_upper, bb_middle, bb_lower, band_position
            )

        # 과매수 영역 (매도 신호)
        elif band_position >= self.overbought_ratio:
            return self._generate_mean_reversion_sell_signal(
                market_data, bb_upper, bb_middle, bb_lower, band_position
            )

        # 중간선 회귀 신호
        reversion_signal = self._check_middle_line_reversion(
            market_data, bb_middle, band_position
        )
        if reversion_signal:
            return reversion_signal

        return None

    def _generate_mean_reversion_buy_signal(
        self,
        market_data: MarketData,
        bb_upper: float,
        bb_middle: float,
        bb_lower: float,
        band_position: float
    ) -> Signal:
        """평균회귀 매수 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_buy_confidence(band_position, bb_lower)

        reason = f"볼린저 밴드 과매도 (위치: {band_position:.2f}, 하단: {bb_lower:.0f})"

        # 밴드 폭 확인
        if self._is_band_expanding():
            confidence += 0.05
            reason += " + 밴드 확장"

        # 가격 반등 신호
        if self._is_price_bouncing_from_lower():
            confidence += 0.1
            reason += " + 반등 신호"

        signal = self.create_signal(
            signal_type=SignalType.BUY,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"평균회귀 매수 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _generate_mean_reversion_sell_signal(
        self,
        market_data: MarketData,
        bb_upper: float,
        bb_middle: float,
        bb_lower: float,
        band_position: float
    ) -> Signal:
        """평균회귀 매도 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_sell_confidence(band_position, bb_upper)

        reason = f"볼린저 밴드 과매수 (위치: {band_position:.2f}, 상단: {bb_upper:.0f})"

        # 밴드 폭 확인
        if self._is_band_expanding():
            confidence += 0.05
            reason += " + 밴드 확장"

        # 가격 하락 신호
        if self._is_price_falling_from_upper():
            confidence += 0.1
            reason += " + 하락 신호"

        signal = self.create_signal(
            signal_type=SignalType.SELL,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"평균회귀 매도 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _check_middle_line_reversion(
        self,
        market_data: MarketData,
        bb_middle: float,
        band_position: float
    ) -> Optional[Signal]:
        """중간선 회귀 신호 확인"""

        current_price = market_data.current_price

        # 중간선과의 거리가 임계값 이내일 때만 확인
        distance_from_middle = abs(current_price - bb_middle) / bb_middle
        if distance_from_middle > self.reversion_threshold:
            return None

        # 중간선 접근 패턴 확인
        if self._is_approaching_middle_from_above(bb_middle):
            confidence = 0.5
            reason = f"중간선 하향 접근 (중간선: {bb_middle:.0f})"

            return self.create_signal(
                signal_type=SignalType.SELL,
                market_data=market_data,
                confidence=confidence,
                reason=reason,
                quantity=int(self.position_size * 0.5)  # 절반 수량
            )

        elif self._is_approaching_middle_from_below(bb_middle):
            confidence = 0.5
            reason = f"중간선 상향 접근 (중간선: {bb_middle:.0f})"

            return self.create_signal(
                signal_type=SignalType.BUY,
                market_data=market_data,
                confidence=confidence,
                reason=reason,
                quantity=int(self.position_size * 0.5)  # 절반 수량
            )

        return None

    def _calculate_buy_confidence(self, band_position: float, bb_lower: float) -> float:
        """매수 신호 신뢰도 계산"""
        confidence = 0.6  # 기본 신뢰도

        # 밴드 하단에 가까울수록 신뢰도 증가
        if band_position <= 0.02:  # 하단 2% 이내
            confidence += 0.3
        elif band_position <= 0.05:  # 하단 5% 이내
            confidence += 0.2
        elif band_position <= 0.1:  # 하단 10% 이내
            confidence += 0.1

        return confidence

    def _calculate_sell_confidence(self, band_position: float, bb_upper: float) -> float:
        """매도 신호 신뢰도 계산"""
        confidence = 0.6  # 기본 신뢰도

        # 밴드 상단에 가까울수록 신뢰도 증가
        if band_position >= 0.98:  # 상단 2% 이내
            confidence += 0.3
        elif band_position >= 0.95:  # 상단 5% 이내
            confidence += 0.2
        elif band_position >= 0.9:  # 상단 10% 이내
            confidence += 0.1

        return confidence

    def _is_band_expanding(self) -> bool:
        """밴드 확장 확인"""
        if len(self.bb_upper_history) < 3 or len(self.bb_lower_history) < 3:
            return False

        # 최근 밴드 폭 증가 확인
        recent_width = self.bb_upper_history[-1] - self.bb_lower_history[-1]
        prev_width = self.bb_upper_history[-2] - self.bb_lower_history[-2]

        return recent_width > prev_width

    def _is_price_bouncing_from_lower(self) -> bool:
        """하단에서 반등 확인"""
        if len(self.price_history) < 3 or len(self.bb_lower_history) < 3:
            return False

        # 이전에 하단 밴드 근처였다가 상승하는 패턴
        prev_price = self.price_history[-2]
        current_price = self.price_history[-1]
        bb_lower = self.bb_lower_history[-1]

        was_near_lower = abs(prev_price - bb_lower) / bb_lower < 0.02
        is_rising = current_price > prev_price

        return was_near_lower and is_rising

    def _is_price_falling_from_upper(self) -> bool:
        """상단에서 하락 확인"""
        if len(self.price_history) < 3 or len(self.bb_upper_history) < 3:
            return False

        # 이전에 상단 밴드 근처였다가 하락하는 패턴
        prev_price = self.price_history[-2]
        current_price = self.price_history[-1]
        bb_upper = self.bb_upper_history[-1]

        was_near_upper = abs(prev_price - bb_upper) / bb_upper < 0.02
        is_falling = current_price < prev_price

        return was_near_upper and is_falling

    def _is_approaching_middle_from_above(self, bb_middle: float) -> bool:
        """위에서 중간선 접근 확인"""
        if len(self.price_history) < 3:
            return False

        # 중간선 위에서 하향 접근
        current_price = self.price_history[-1]
        prev_price = self.price_history[-2]

        is_above_middle = current_price > bb_middle
        is_descending = current_price < prev_price

        return is_above_middle and is_descending

    def _is_approaching_middle_from_below(self, bb_middle: float) -> bool:
        """아래서 중간선 접근 확인"""
        if len(self.price_history) < 3:
            return False

        # 중간선 아래에서 상향 접근
        current_price = self.price_history[-1]
        prev_price = self.price_history[-2]

        is_below_middle = current_price < bb_middle
        is_ascending = current_price > prev_price

        return is_below_middle and is_ascending

    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            'name': self.name,
            'description': '볼린저 밴드 기반 평균회귀 전략',
            'parameters': {
                'bb_period': self.bb_period,
                'bb_std_dev': self.bb_std_dev,
                'reversion_threshold': self.reversion_threshold,
                'oversold_ratio': self.oversold_ratio,
                'overbought_ratio': self.overbought_ratio,
                'min_confidence': self.min_confidence
            },
            'signals': {
                'buy': f'밴드 위치 ≤ {self.oversold_ratio} (과매도)',
                'sell': f'밴드 위치 ≥ {self.overbought_ratio} (과매수)',
                'middle_reversion': '중간선 회귀 신호'
            },
            'current_state': {
                'price_data_count': len(self.price_history),
                'bb_data_count': len(self.bb_upper_history),
                'current_bb_upper': self.bb_upper_history[-1] if self.bb_upper_history else None,
                'current_bb_middle': self.bb_middle_history[-1] if self.bb_middle_history else None,
                'current_bb_lower': self.bb_lower_history[-1] if self.bb_lower_history else None
            }
        }