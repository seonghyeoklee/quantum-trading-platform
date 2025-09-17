"""
골든크로스 전략
5일 이동평균선이 20일 이동평균선을 상향 돌파할 때 매수
5일 이동평균선이 20일 이동평균선을 하향 돌파할 때 매도
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base_strategy import BaseStrategy
from ..core.data_types import MarketData, Signal, SignalType


class GoldenCrossStrategy(BaseStrategy):
    """골든크로스 전략"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("GoldenCross", config)

        # 전략 특정 설정
        self.fast_period = self.config.get('fast_period', 5)   # 단기 이평선
        self.slow_period = self.config.get('slow_period', 20)  # 장기 이평선
        self.volume_threshold = self.config.get('volume_threshold', 1.2)  # 거래량 임계값

        # 내부 상태
        self.price_history: List[float] = []
        self.volume_history: List[int] = []
        self.ma_history: List[Dict[str, float]] = []  # {ma5, ma20}

    def analyze_signal(self, market_data: MarketData) -> Optional[Signal]:
        """골든크로스/데드크로스 신호 분석"""

        # 가격 히스토리 업데이트
        self.price_history.append(market_data.current_price)
        self.volume_history.append(market_data.volume)

        # 히스토리 크기 제한 (최근 50개)
        if len(self.price_history) > 50:
            self.price_history = self.price_history[-50:]
            self.volume_history = self.volume_history[-50:]

        # 이동평균선 계산
        ma5 = self._calculate_ma(self.fast_period)
        ma20 = self._calculate_ma(self.slow_period)

        if ma5 is None or ma20 is None:
            return None

        # 이동평균 히스토리 업데이트
        self.ma_history.append({'ma5': ma5, 'ma20': ma20})
        if len(self.ma_history) > 50:
            self.ma_history = self.ma_history[-50:]

        # MarketData에 이동평균 설정
        market_data.ma5 = ma5
        market_data.ma20 = ma20

        # 크로스 패턴 감지
        signal = self._detect_cross_pattern(market_data)
        return signal

    def _calculate_ma(self, period: int) -> Optional[float]:
        """이동평균 계산"""
        if len(self.price_history) < period:
            return None

        return sum(self.price_history[-period:]) / period

    def _detect_cross_pattern(self, market_data: MarketData) -> Optional[Signal]:
        """크로스 패턴 감지"""

        if len(self.ma_history) < 2:
            return None

        current_ma = self.ma_history[-1]
        prev_ma = self.ma_history[-2]

        ma5_current = current_ma['ma5']
        ma20_current = current_ma['ma20']
        ma5_prev = prev_ma['ma5']
        ma20_prev = prev_ma['ma20']

        # 골든크로스 (매수 신호)
        if ma5_prev <= ma20_prev and ma5_current > ma20_current:
            return self._generate_buy_signal(market_data, ma5_current, ma20_current)

        # 데드크로스 (매도 신호)
        elif ma5_prev >= ma20_prev and ma5_current < ma20_current:
            return self._generate_sell_signal(market_data, ma5_current, ma20_current)

        # 추가 매수 조건: 골든크로스 후 상승 지속
        elif ma5_current > ma20_current and self._is_strong_uptrend():
            signal = self._check_additional_buy_conditions(market_data, ma5_current, ma20_current)
            if signal:
                return signal

        return None

    def _generate_buy_signal(self, market_data: MarketData, ma5: float, ma20: float) -> Signal:
        """골든크로스 매수 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_buy_confidence(market_data, ma5, ma20)

        reason = f"골든크로스 감지 (MA5: {ma5:.0f} > MA20: {ma20:.0f})"

        # 거래량 확인
        if self._is_volume_surge():
            confidence += 0.1
            reason += " + 거래량 급증"

        signal = self.create_signal(
            signal_type=SignalType.BUY,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"골든크로스 매수 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _generate_sell_signal(self, market_data: MarketData, ma5: float, ma20: float) -> Signal:
        """데드크로스 매도 신호 생성"""

        # 신뢰도 계산
        confidence = self._calculate_sell_confidence(market_data, ma5, ma20)

        reason = f"데드크로스 감지 (MA5: {ma5:.0f} < MA20: {ma20:.0f})"

        signal = self.create_signal(
            signal_type=SignalType.SELL,
            market_data=market_data,
            confidence=min(confidence, 1.0),
            reason=reason
        )

        self.logger.info(f"데드크로스 매도 신호: {reason} (신뢰도: {confidence:.2f})")
        return signal

    def _calculate_buy_confidence(self, market_data: MarketData, ma5: float, ma20: float) -> float:
        """매수 신호 신뢰도 계산"""
        confidence = 0.7  # 기본 신뢰도

        # 이동평균선 간격이 클수록 신뢰도 증가
        spread_percent = ((ma5 - ma20) / ma20) * 100
        if spread_percent > 2.0:
            confidence += 0.15
        elif spread_percent > 1.0:
            confidence += 0.1

        # 현재가가 이동평균선들보다 높으면 신뢰도 증가
        if market_data.current_price > ma5 > ma20:
            confidence += 0.1

        # RSI 확인 (과매수 상태 아닐 때 신뢰도 증가)
        if market_data.rsi and market_data.rsi < 70:
            confidence += 0.05

        return confidence

    def _calculate_sell_confidence(self, market_data: MarketData, ma5: float, ma20: float) -> float:
        """매도 신호 신뢰도 계산"""
        confidence = 0.7  # 기본 신뢰도

        # 이동평균선 간격이 클수록 신뢰도 증가
        spread_percent = ((ma20 - ma5) / ma20) * 100
        if spread_percent > 2.0:
            confidence += 0.15
        elif spread_percent > 1.0:
            confidence += 0.1

        # 현재가가 이동평균선들보다 낮으면 신뢰도 증가
        if market_data.current_price < ma5 < ma20:
            confidence += 0.1

        # RSI 확인 (과매도 상태 아닐 때 신뢰도 증가)
        if market_data.rsi and market_data.rsi > 30:
            confidence += 0.05

        return confidence

    def _is_volume_surge(self) -> bool:
        """거래량 급증 확인"""
        if len(self.volume_history) < 10:
            return False

        current_volume = self.volume_history[-1]
        avg_volume = sum(self.volume_history[-10:-1]) / 9  # 최근 9일 평균

        return current_volume > avg_volume * self.volume_threshold

    def _is_strong_uptrend(self) -> bool:
        """강한 상승 추세 확인"""
        if len(self.ma_history) < 5:
            return False

        # 최근 5일간 MA5가 지속적으로 상승
        recent_ma5 = [ma['ma5'] for ma in self.ma_history[-5:]]
        return all(recent_ma5[i] < recent_ma5[i+1] for i in range(len(recent_ma5)-1))

    def _check_additional_buy_conditions(self, market_data: MarketData, ma5: float, ma20: float) -> Optional[Signal]:
        """추가 매수 조건 확인"""

        # 이미 골든크로스 상태에서 추가 매수 조건
        if not self._is_strong_uptrend():
            return None

        # 거래량 급증 시에만 추가 매수
        if not self._is_volume_surge():
            return None

        # 최근 3일 이내에 동일한 신호가 있었다면 제외
        recent_signals = self.get_recent_signals(count=5)
        for signal in recent_signals:
            if signal.signal_type == SignalType.BUY:
                time_diff = market_data.timestamp - signal.timestamp
                if time_diff < timedelta(days=3):
                    return None

        confidence = 0.6  # 추가 매수는 낮은 신뢰도
        reason = f"상승 추세 지속 + 거래량 급증 (MA5: {ma5:.0f} > MA20: {ma20:.0f})"

        return self.create_signal(
            signal_type=SignalType.BUY,
            market_data=market_data,
            confidence=confidence,
            reason=reason,
            quantity=int(self.position_size * 0.5)  # 추가 매수는 절반 수량
        )

    def get_strategy_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        return {
            'name': self.name,
            'description': '골든크로스/데드크로스 기반 매매 전략',
            'parameters': {
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'volume_threshold': self.volume_threshold,
                'min_confidence': self.min_confidence
            },
            'signals': {
                'buy': '5일 이평선이 20일 이평선 상향 돌파',
                'sell': '5일 이평선이 20일 이평선 하향 돌파',
                'additional_buy': '상승 추세 지속 + 거래량 급증'
            },
            'current_state': {
                'price_data_count': len(self.price_history),
                'ma_data_count': len(self.ma_history),
                'last_ma5': self.ma_history[-1]['ma5'] if self.ma_history else None,
                'last_ma20': self.ma_history[-1]['ma20'] if self.ma_history else None
            }
        }