"""
볼린저 밴드 기반 국내주식 거래 전략
밴드 돌파 및 회귀 패턴으로 매매 신호 생성
"""

from typing import List, Dict, Any, Optional
from domestic_trading_system.core.domestic_data_types import DomesticMarketData
from domestic_trading_system.strategies.base_strategy import BaseDomesticStrategy


class DomesticBollingerStrategy(BaseDomesticStrategy):
    """볼린저 밴드 기반 국내주식 거래 전략"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # 볼린저 밴드 설정
        self.bb_period = config.get('bb_period', 20)
        self.bb_std_dev = config.get('bb_std_dev', 2.0)

        # 신호 생성 설정
        self.squeeze_threshold = config.get('squeeze_threshold', 0.02)  # 밴드 폭 기준
        self.breakout_confirmation = config.get('breakout_confirmation', True)

        # 신뢰도 설정
        self.base_confidence = config.get('base_confidence', 0.75)
        self.volume_boost = config.get('volume_boost', 0.1)

        # 추가 필터
        self.use_volume_filter = config.get('use_volume_filter', True)
        self.volume_threshold = config.get('volume_threshold', 1.5)

        # 현재 분석 상태
        self.current_bands = {'upper': 0, 'middle': 0, 'lower': 0}
        self.band_position = "MIDDLE"  # UPPER, LOWER, MIDDLE
        self.band_width = 0.0
        self.is_squeeze = False

    async def generate_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData) -> Optional[Dict[str, Any]]:
        """볼린저 밴드 기반 매매 신호 생성"""
        try:
            # 최소 데이터 확인
            if len(history) < self.bb_period + 5:
                return None

            # 신호 쿨다운 확인
            if not self.can_generate_signal():
                return None

            # 볼린저 밴드 계산
            self.current_bands = self.get_bollinger_bands(history, self.bb_period, self.bb_std_dev)
            current_price = current_data.current_price

            # 밴드 위치 분석
            self._analyze_band_position(current_price)

            # 밴드 폭 및 압축 상태 분석
            self._analyze_band_width(history)

            # 거래량 분석
            volume_surge = self.is_volume_surge(history, self.volume_threshold) if self.use_volume_filter else True

            # 매수 신호 확인 (하단 밴드 반등 또는 돌파)
            if self._check_buy_signal(history, current_data, volume_surge):
                confidence = self._calculate_buy_confidence(history, current_data, volume_surge)

                if confidence >= self.base_confidence:
                    self.update_signal_time()
                    return {
                        'type': 'BUY',
                        'confidence': confidence,
                        'reason': self._get_buy_reason(current_price),
                        'quantity': self.max_position_size
                    }

            # 매도 신호 확인 (상단 밴드 도달 또는 돌파)
            elif self._check_sell_signal(history, current_data, volume_surge):
                confidence = self._calculate_sell_confidence(history, current_data, volume_surge)

                if confidence >= self.base_confidence:
                    self.update_signal_time()
                    return {
                        'type': 'SELL',
                        'confidence': confidence,
                        'reason': self._get_sell_reason(current_price),
                        'quantity': self.max_position_size
                    }

            return None

        except Exception as e:
            return None

    def _analyze_band_position(self, current_price: float):
        """밴드 내 가격 위치 분석"""
        upper = self.current_bands['upper']
        lower = self.current_bands['lower']
        middle = self.current_bands['middle']

        if current_price > upper:
            self.band_position = "ABOVE_UPPER"
        elif current_price < lower:
            self.band_position = "BELOW_LOWER"
        elif current_price > middle:
            self.band_position = "UPPER_HALF"
        else:
            self.band_position = "LOWER_HALF"

    def _analyze_band_width(self, history: List[DomesticMarketData]):
        """밴드 폭 및 압축 상태 분석"""
        upper = self.current_bands['upper']
        lower = self.current_bands['lower']
        middle = self.current_bands['middle']

        if middle > 0:
            self.band_width = (upper - lower) / middle
            self.is_squeeze = self.band_width < self.squeeze_threshold
        else:
            self.band_width = 0.0
            self.is_squeeze = False

    def _check_buy_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> bool:
        """매수 신호 확인"""
        current_price = current_data.current_price
        lower_band = self.current_bands['lower']

        # 케이스 1: 하단 밴드 터치 후 반등
        if self.band_position == "BELOW_LOWER" or (current_price <= lower_band * 1.01):
            # 가격이 상승 중인지 확인
            price_rising = self.get_price_change_percent(history, 1) > 0
            if price_rising:
                return volume_surge if self.use_volume_filter else True

        # 케이스 2: 밴드 압축 후 상향 돌파
        if self.is_squeeze and self.band_position in ["UPPER_HALF", "ABOVE_UPPER"]:
            # 강한 상승 모멘텀 확인
            strong_momentum = self.get_price_change_percent(history, 2) > 1.0
            if strong_momentum:
                return volume_surge if self.use_volume_filter else True

        return False

    def _check_sell_signal(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> bool:
        """매도 신호 확인"""
        current_price = current_data.current_price
        upper_band = self.current_bands['upper']

        # 케이스 1: 상단 밴드 터치 후 하락
        if self.band_position == "ABOVE_UPPER" or (current_price >= upper_band * 0.99):
            # 가격이 하락 중인지 확인
            price_falling = self.get_price_change_percent(history, 1) < 0
            if price_falling:
                return volume_surge if self.use_volume_filter else True

        # 케이스 2: 밴드 압축 후 하향 돌파
        if self.is_squeeze and self.band_position in ["LOWER_HALF", "BELOW_LOWER"]:
            # 강한 하락 모멘텀 확인
            strong_momentum = self.get_price_change_percent(history, 2) < -1.0
            if strong_momentum:
                return volume_surge if self.use_volume_filter else True

        return False

    def _calculate_buy_confidence(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> float:
        """매수 신뢰도 계산"""
        confidence = self.base_confidence
        current_price = current_data.current_price
        lower_band = self.current_bands['lower']

        # 하단 밴드 근접도에 따른 신뢰도 증가
        if lower_band > 0:
            distance_ratio = abs(current_price - lower_band) / lower_band
            if distance_ratio < 0.02:  # 2% 이내
                confidence += 0.1
            elif distance_ratio < 0.01:  # 1% 이내
                confidence += 0.15

        # 밴드 압축 상태에서 추가 신뢰도
        if self.is_squeeze:
            confidence += 0.1

        # 거래량 급증시 추가 신뢰도
        if volume_surge:
            confidence += self.volume_boost

        # 가격 상승 모멘텀
        price_change = self.get_price_change_percent(history, 1)
        if price_change > 0.5:
            confidence += 0.05

        return min(confidence, 0.95)

    def _calculate_sell_confidence(self, history: List[DomesticMarketData], current_data: DomesticMarketData, volume_surge: bool) -> float:
        """매도 신뢰도 계산"""
        confidence = self.base_confidence
        current_price = current_data.current_price
        upper_band = self.current_bands['upper']

        # 상단 밴드 근접도에 따른 신뢰도 증가
        if upper_band > 0:
            distance_ratio = abs(current_price - upper_band) / upper_band
            if distance_ratio < 0.02:  # 2% 이내
                confidence += 0.1
            elif distance_ratio < 0.01:  # 1% 이내
                confidence += 0.15

        # 밴드 압축 상태에서 추가 신뢰도
        if self.is_squeeze:
            confidence += 0.1

        # 거래량 급증시 추가 신뢰도
        if volume_surge:
            confidence += self.volume_boost

        # 가격 하락 모멘텀
        price_change = self.get_price_change_percent(history, 1)
        if price_change < -0.5:
            confidence += 0.05

        return min(confidence, 0.95)

    def _get_buy_reason(self, current_price: float) -> str:
        """매수 사유 생성"""
        if self.is_squeeze:
            return f"밴드 압축 후 상향 돌파 (폭: {self.band_width:.3f})"
        else:
            return f"하단밴드 반등 ({current_price:,.0f}원 vs {self.current_bands['lower']:,.0f}원)"

    def _get_sell_reason(self, current_price: float) -> str:
        """매도 사유 생성"""
        if self.is_squeeze:
            return f"밴드 압축 후 하향 돌파 (폭: {self.band_width:.3f})"
        else:
            return f"상단밴드 도달 ({current_price:,.0f}원 vs {self.current_bands['upper']:,.0f}원)"

    def get_current_analysis(self) -> Dict[str, Any]:
        """현재 전략 분석 정보 반환"""
        base_analysis = super().get_current_analysis()

        # 볼린저 밴드 특화 분석 추가
        bollinger_analysis = {
            'bollinger_bands': {
                'upper': round(self.current_bands['upper'], 2),
                'middle': round(self.current_bands['middle'], 2),
                'lower': round(self.current_bands['lower'], 2)
            },
            'band_position': self.band_position,
            'band_width': round(self.band_width, 4),
            'is_squeeze': self.is_squeeze,
            'squeeze_threshold': self.squeeze_threshold
        }

        base_analysis.update(bollinger_analysis)
        return base_analysis