"""
이동평균 기반 국내주식 거래 전략
골든크로스/데드크로스 및 이동평균 지지/저항 활용
"""

from typing import List, Dict, Any, Optional
from domestic_trading_system.core.domestic_data_types import DomesticMarketData
from domestic_trading_system.strategies.base_strategy import BaseDomesticStrategy


class DomesticMovingAverageStrategy(BaseDomesticStrategy):
    """이동평균 기반 국내주식 거래 전략"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # 이동평균선 설정
        self.short_ma_period = config.get('short_ma_period', 5)
        self.long_ma_period = config.get('long_ma_period', 20)

        # 신호 생성 설정
        self.cross_threshold = config.get('cross_threshold', 0.005)  # 0.5% 이상 교차
        self.trend_confirmation = config.get('trend_confirmation', True)

        # 신뢰도 설정
        self.base_confidence = config.get('base_confidence', 0.8)
        self.volume_boost = config.get('volume_boost', 0.1)

        # 추가 필터
        self.use_volume_filter = config.get('use_volume_filter', True)
        self.volume_threshold = config.get('volume_threshold', 1.3)

        # 현재 분석 상태
        self.short_ma = 0.0
        self.long_ma = 0.0
        self.cross_direction = "NONE"  # GOLDEN, DEAD, NONE
        self.trend_direction = "NEUTRAL"  # UP, DOWN, NEUTRAL
        self.price_vs_ma = "NEUTRAL"  # ABOVE, BELOW, NEUTRAL

    async def generate_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData) -> Optional[Dict[str, Any]]:
        """이동평균 기반 매매 신호 생성"""
        try:
            # 최소 데이터 확인
            if len(history) < self.long_ma_period + 5:
                return None

            # 신호 쿨다운 확인
            if not self.can_generate_signal():
                return None

            # 이동평균 계산
            self.short_ma = self.get_simple_moving_average(history, self.short_ma_period)
            self.long_ma = self.get_simple_moving_average(history, self.long_ma_period)

            # 교차 신호 분석
            self._analyze_ma_cross(history)

            # 트렌드 분석
            self._analyze_trend(history)

            # 가격 vs 이동평균 위치 분석
            self._analyze_price_position(current_data.current_price)

            # 거래량 분석
            volume_surge = self.is_volume_surge(history, self.volume_threshold) if self.use_volume_filter else True

            # 매수 신호 확인 (골든크로스 또는 지지선 반등)
            if self._check_buy_signal(history, current_data, volume_surge):
                confidence = self._calculate_buy_confidence(history, current_data, volume_surge)

                if confidence >= self.base_confidence:
                    self.update_signal_time()
                    return {
                        'type': 'BUY',
                        'confidence': confidence,
                        'reason': self._get_buy_reason(),
                        'quantity': self.max_position_size
                    }

            # 매도 신호 확인 (데드크로스 또는 저항선 도달)
            elif self._check_sell_signal(history, current_data, volume_surge):
                confidence = self._calculate_sell_confidence(history, current_data, volume_surge)

                if confidence >= self.base_confidence:
                    self.update_signal_time()
                    return {
                        'type': 'SELL',
                        'confidence': confidence,
                        'reason': self._get_sell_reason(),
                        'quantity': self.max_position_size
                    }

            return None

        except Exception as e:
            return None

    def _analyze_ma_cross(self, history: List[DomesticMarketData]):
        """이동평균 교차 분석"""
        if len(history) < self.long_ma_period + 2:
            self.cross_direction = "NONE"
            return

        # 이전 이동평균 계산
        prev_short_ma = self.get_simple_moving_average(history[:-1], self.short_ma_period)
        prev_long_ma = self.get_simple_moving_average(history[:-1], self.long_ma_period)

        # 교차 여부 확인
        current_diff = (self.short_ma - self.long_ma) / self.long_ma if self.long_ma > 0 else 0
        prev_diff = (prev_short_ma - prev_long_ma) / prev_long_ma if prev_long_ma > 0 else 0

        # 골든크로스 (단기 > 장기로 교차)
        if prev_diff <= 0 and current_diff > self.cross_threshold:
            self.cross_direction = "GOLDEN"
        # 데드크로스 (단기 < 장기로 교차)
        elif prev_diff >= 0 and current_diff < -self.cross_threshold:
            self.cross_direction = "DEAD"
        else:
            self.cross_direction = "NONE"

    def _analyze_trend(self, history: List[DomesticMarketData]):
        """트렌드 분석"""
        if len(history) < self.long_ma_period + 5:
            self.trend_direction = "NEUTRAL"
            return

        # 장기 이동평균의 기울기로 트렌드 판단
        current_long_ma = self.long_ma
        prev_long_ma = self.get_simple_moving_average(history[:-3], self.long_ma_period)

        if prev_long_ma > 0:
            trend_change = (current_long_ma - prev_long_ma) / prev_long_ma

            if trend_change > 0.01:  # 1% 이상 상승
                self.trend_direction = "UP"
            elif trend_change < -0.01:  # 1% 이상 하락
                self.trend_direction = "DOWN"
            else:
                self.trend_direction = "NEUTRAL"

    def _analyze_price_position(self, current_price: float):
        """가격과 이동평균 위치 관계 분석"""
        if current_price > self.short_ma and current_price > self.long_ma:
            self.price_vs_ma = "ABOVE_BOTH"
        elif current_price < self.short_ma and current_price < self.long_ma:
            self.price_vs_ma = "BELOW_BOTH"
        elif current_price > self.short_ma > self.long_ma:
            self.price_vs_ma = "ABOVE_SHORT"
        elif current_price < self.short_ma < self.long_ma:
            self.price_vs_ma = "BELOW_SHORT"
        else:
            self.price_vs_ma = "BETWEEN"

    def _check_buy_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> bool:
        """매수 신호 확인"""
        # 케이스 1: 골든크로스
        if self.cross_direction == "GOLDEN":
            # 상승 트렌드에서 더 강한 신호
            if not self.trend_confirmation or self.trend_direction in ["UP", "NEUTRAL"]:
                return volume_surge if self.use_volume_filter else True

        # 케이스 2: 단기 이동평균 지지선 반등
        if self.price_vs_ma in ["ABOVE_SHORT", "ABOVE_BOTH"]:
            # 단기 이동평균 근처에서 반등
            current_price = current_data.current_price
            if abs(current_price - self.short_ma) / self.short_ma < 0.02:  # 2% 이내
                price_rising = self.get_price_change_percent(history, 1) > 0
                if price_rising and self.trend_direction != "DOWN":
                    return volume_surge if self.use_volume_filter else True

        return False

    def _check_sell_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> bool:
        """매도 신호 확인"""
        # 케이스 1: 데드크로스
        if self.cross_direction == "DEAD":
            # 하락 트렌드에서 더 강한 신호
            if not self.trend_confirmation or self.trend_direction in ["DOWN", "NEUTRAL"]:
                return volume_surge if self.use_volume_filter else True

        # 케이스 2: 단기 이동평균 저항선 도달
        if self.price_vs_ma in ["BELOW_SHORT", "BELOW_BOTH"]:
            # 단기 이동평균 근처에서 저항
            current_price = current_data.current_price
            if abs(current_price - self.short_ma) / self.short_ma < 0.02:  # 2% 이내
                price_falling = self.get_price_change_percent(history, 1) < 0
                if price_falling and self.trend_direction != "UP":
                    return volume_surge if self.use_volume_filter else True

        return False

    def _calculate_buy_confidence(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> float:
        """매수 신뢰도 계산"""
        confidence = self.base_confidence

        # 골든크로스시 높은 신뢰도
        if self.cross_direction == "GOLDEN":
            confidence += 0.1

        # 상승 트렌드에서 추가 신뢰도
        if self.trend_direction == "UP":
            confidence += 0.05

        # 이동평균 간격이 좁을 때 (수렴) 신뢰도 증가
        if self.long_ma > 0:
            ma_gap = abs(self.short_ma - self.long_ma) / self.long_ma
            if ma_gap < 0.02:  # 2% 이내
                confidence += 0.05

        # 거래량 급증시 추가 신뢰도
        if volume_surge:
            confidence += self.volume_boost

        # 가격 모멘텀
        price_change = self.get_price_change_percent(history, 2)
        if price_change > 1.0:
            confidence += 0.05

        return min(confidence, 0.95)

    def _calculate_sell_confidence(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> float:
        """매도 신뢰도 계산"""
        confidence = self.base_confidence

        # 데드크로스시 높은 신뢰도
        if self.cross_direction == "DEAD":
            confidence += 0.1

        # 하락 트렌드에서 추가 신뢰도
        if self.trend_direction == "DOWN":
            confidence += 0.05

        # 이동평균 간격이 좁을 때 (수렴) 신뢰도 증가
        if self.long_ma > 0:
            ma_gap = abs(self.short_ma - self.long_ma) / self.long_ma
            if ma_gap < 0.02:  # 2% 이내
                confidence += 0.05

        # 거래량 급증시 추가 신뢰도
        if volume_surge:
            confidence += self.volume_boost

        # 가격 모멘텀
        price_change = self.get_price_change_percent(history, 2)
        if price_change < -1.0:
            confidence += 0.05

        return min(confidence, 0.95)

    def _get_buy_reason(self) -> str:
        """매수 사유 생성"""
        if self.cross_direction == "GOLDEN":
            return f"골든크로스 (단기MA: {self.short_ma:,.0f} > 장기MA: {self.long_ma:,.0f})"
        else:
            return f"이동평균 지지선 반등 (단기MA: {self.short_ma:,.0f}원)"

    def _get_sell_reason(self) -> str:
        """매도 사유 생성"""
        if self.cross_direction == "DEAD":
            return f"데드크로스 (단기MA: {self.short_ma:,.0f} < 장기MA: {self.long_ma:,.0f})"
        else:
            return f"이동평균 저항선 도달 (단기MA: {self.short_ma:,.0f}원)"

    def get_current_analysis(self) -> Dict[str, Any]:
        """현재 전략 분석 정보 반환"""
        base_analysis = super().get_current_analysis()

        # 이동평균 특화 분석 추가
        ma_analysis = {
            'moving_averages': {
                'short_ma': round(self.short_ma, 2),
                'long_ma': round(self.long_ma, 2),
                'short_period': self.short_ma_period,
                'long_period': self.long_ma_period
            },
            'cross_direction': self.cross_direction,
            'trend_direction': self.trend_direction,
            'price_vs_ma': self.price_vs_ma,
            'ma_gap_percent': round(abs(self.short_ma - self.long_ma) / self.long_ma * 100, 2) if self.long_ma > 0 else 0
        }

        base_analysis.update(ma_analysis)
        return base_analysis