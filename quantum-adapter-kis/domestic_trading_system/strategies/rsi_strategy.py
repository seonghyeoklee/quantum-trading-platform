"""
RSI 기반 국내주식 거래 전략
과매수/과매도 구간에서 매매 신호 생성
"""

from typing import List, Dict, Any, Optional
from domestic_trading_system.core.domestic_data_types import DomesticMarketData
from domestic_trading_system.strategies.base_strategy import BaseDomesticStrategy


class DomesticRSIStrategy(BaseDomesticStrategy):
    """RSI 기반 국내주식 거래 전략"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # RSI 설정
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)

        # 신뢰도 설정
        self.base_confidence = config.get('base_confidence', 0.7)
        self.volume_boost = config.get('volume_boost', 0.1)

        # 추가 필터
        self.use_volume_filter = config.get('use_volume_filter', True)
        self.volume_threshold = config.get('volume_threshold', 1.5)

        # 현재 분석 상태
        self.current_rsi = 50.0
        self.rsi_trend = "NEUTRAL"  # UP, DOWN, NEUTRAL

    async def generate_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData) -> Optional[Dict[str, Any]]:
        """RSI 기반 매매 신호 생성"""
        try:
            # 최소 데이터 확인
            if len(history) < self.rsi_period + 5:
                return None

            # 신호 쿨다운 확인
            if not self.can_generate_signal():
                return None

            # RSI 계산
            self.current_rsi = self.calculate_rsi(history, self.rsi_period)

            # RSI 트렌드 분석
            self._analyze_rsi_trend(history)

            # 거래량 분석
            volume_surge = self.is_volume_surge(history, self.volume_threshold) if self.use_volume_filter else True

            # 매수 신호 확인 (과매도 + 반등)
            if self._check_buy_signal(history, current_data, volume_surge):
                confidence = self._calculate_buy_confidence(history, current_data, volume_surge)

                if confidence >= self.base_confidence:
                    self.update_signal_time()
                    return {
                        'type': 'BUY',
                        'confidence': confidence,
                        'reason': f'RSI 과매도 반등 (RSI: {self.current_rsi:.1f})',
                        'quantity': self.max_position_size
                    }

            # 매도 신호 확인 (과매수 + 하락)
            elif self._check_sell_signal(history, current_data, volume_surge):
                confidence = self._calculate_sell_confidence(history, current_data, volume_surge)

                if confidence >= self.base_confidence:
                    self.update_signal_time()
                    return {
                        'type': 'SELL',
                        'confidence': confidence,
                        'reason': f'RSI 과매수 하락 (RSI: {self.current_rsi:.1f})',
                        'quantity': self.max_position_size
                    }

            return None

        except Exception as e:
            return None

    def _analyze_rsi_trend(self, history: List[DomesticMarketData]):
        """RSI 트렌드 분석"""
        if len(history) < self.rsi_period + 3:
            self.rsi_trend = "NEUTRAL"
            return

        # 최근 3개 RSI 값 계산
        rsi_values = []
        for i in range(3):
            slice_end = len(history) - i
            slice_data = history[:slice_end]
            if len(slice_data) >= self.rsi_period:
                rsi = self.calculate_rsi(slice_data, self.rsi_period)
                rsi_values.append(rsi)

        if len(rsi_values) >= 3:
            # RSI 상승 트렌드
            if rsi_values[0] > rsi_values[1] > rsi_values[2]:
                self.rsi_trend = "UP"
            # RSI 하락 트렌드
            elif rsi_values[0] < rsi_values[1] < rsi_values[2]:
                self.rsi_trend = "DOWN"
            else:
                self.rsi_trend = "NEUTRAL"

    def _check_buy_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> bool:
        """매수 신호 확인"""
        # 기본 RSI 과매도 조건
        if self.current_rsi > self.rsi_oversold:
            return False

        # RSI 상승 트렌드 (바닥에서 반등)
        if self.rsi_trend != "UP":
            return False

        # 가격이 상승 중
        price_rising = self.get_price_change_percent(history, 1) > 0

        # 거래량 조건 (선택적)
        volume_condition = volume_surge if self.use_volume_filter else True

        return price_rising and volume_condition

    def _check_sell_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> bool:
        """매도 신호 확인"""
        # 기본 RSI 과매수 조건
        if self.current_rsi < self.rsi_overbought:
            return False

        # RSI 하락 트렌드 (고점에서 하락)
        if self.rsi_trend != "DOWN":
            return False

        # 가격이 하락 중
        price_falling = self.get_price_change_percent(history, 1) < 0

        # 거래량 조건 (선택적)
        volume_condition = volume_surge if self.use_volume_filter else True

        return price_falling and volume_condition

    def _calculate_buy_confidence(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> float:
        """매수 신뢰도 계산"""
        confidence = self.base_confidence

        # RSI가 더 낮을수록 신뢰도 증가
        rsi_factor = (self.rsi_oversold - self.current_rsi) / self.rsi_oversold
        confidence += rsi_factor * 0.1

        # 거래량 급증시 추가 신뢰도
        if volume_surge:
            confidence += self.volume_boost

        # 가격 상승폭에 따른 조정
        price_change = self.get_price_change_percent(history, 1)
        if price_change > 1.0:  # 1% 이상 상승
            confidence += 0.05
        elif price_change > 2.0:  # 2% 이상 상승
            confidence += 0.1

        # 최대 0.95로 제한
        return min(confidence, 0.95)

    def _calculate_sell_confidence(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> float:
        """매도 신뢰도 계산"""
        confidence = self.base_confidence

        # RSI가 더 높을수록 신뢰도 증가
        rsi_factor = (self.current_rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
        confidence += rsi_factor * 0.1

        # 거래량 급증시 추가 신뢰도
        if volume_surge:
            confidence += self.volume_boost

        # 가격 하락폭에 따른 조정
        price_change = self.get_price_change_percent(history, 1)
        if price_change < -1.0:  # 1% 이상 하락
            confidence += 0.05
        elif price_change < -2.0:  # 2% 이상 하락
            confidence += 0.1

        # 최대 0.95로 제한
        return min(confidence, 0.95)

    def get_current_analysis(self) -> Dict[str, Any]:
        """현재 전략 분석 정보 반환"""
        base_analysis = super().get_current_analysis()

        # RSI 특화 분석 추가
        rsi_analysis = {
            'rsi_value': round(self.current_rsi, 2),
            'rsi_trend': self.rsi_trend,
            'rsi_level': self._get_rsi_level(),
            'oversold_threshold': self.rsi_oversold,
            'overbought_threshold': self.rsi_overbought
        }

        base_analysis.update(rsi_analysis)
        return base_analysis

    def _get_rsi_level(self) -> str:
        """RSI 수준 분류"""
        if self.current_rsi <= self.rsi_oversold:
            return "과매도"
        elif self.current_rsi >= self.rsi_overbought:
            return "과매수"
        elif self.current_rsi < 45:
            return "약세"
        elif self.current_rsi > 55:
            return "강세"
        else:
            return "중립"