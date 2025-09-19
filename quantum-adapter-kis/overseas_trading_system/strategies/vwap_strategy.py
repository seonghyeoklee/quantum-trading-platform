"""
VWAP (Volume Weighted Average Price) 전략
기관 투자자들이 가장 많이 사용하는 벤치마크 전략

주요 특징:
- Intraday VWAP 계산 (매일 9:30 AM EST 리셋)
- 표준편차 밴드 (Upper/Lower Band)
- 거래량 가중 매매 신호
- 세션별 가중치 조정
"""

from typing import Optional, Dict, Any
from datetime import datetime, time
from collections import deque
import statistics

from overseas_trading_system.core.overseas_data_types import (
    OverseasMarketData, OverseasTradingSignal, SignalType, TradingSession
)
from .base_strategy import BaseOverseasStrategy


class VWAPStrategy(BaseOverseasStrategy):
    """VWAP 기반 매매 전략"""

    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'std_multiplier': 2.0,           # 표준편차 배수 (밴드 폭)
            'volume_threshold': 1.5,         # 거래량 임계값 (평균의 1.5배)
            'min_confidence': 0.7,           # 최소 신뢰도
            'vwap_period': 'intraday',       # VWAP 기간 (intraday 또는 anchored)
            'session_start_hour': 9,         # 세션 시작 시간 (EST)
            'session_start_minute': 30,      # 세션 시작 분
            'price_deviation_threshold': 0.5, # 가격 이탈 임계값 (%)
            'min_data_points': 20            # 최소 데이터 포인트
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)
        self.name = "VWAP Strategy"

        # VWAP 계산용 데이터
        self.cumulative_volume = 0
        self.cumulative_volume_price = 0
        self.vwap_data_points = deque(maxlen=500)  # 가격과 VWAP 차이 저장
        self.current_vwap = 0
        self.session_start_time = None

        # 밴드 계산용
        self.upper_band = 0
        self.lower_band = 0
        self.std_deviation = 0

    def analyze_signal(self, market_data: OverseasMarketData) -> Optional[OverseasTradingSignal]:
        """VWAP 분석 및 신호 생성"""
        # 데이터 히스토리에 추가
        self.add_market_data(market_data)

        # 새로운 세션 확인 (9:30 AM EST 리셋)
        if self._is_new_session(market_data):
            self._reset_vwap()

        # VWAP 계산 및 업데이트
        self._update_vwap(market_data)

        # 최소 데이터 확인
        if len(self.vwap_data_points) < self.config['min_data_points']:
            return None

        # 밴드 계산
        self._calculate_bands()

        # 매매 신호 생성
        signal_type, confidence, reason = self._generate_vwap_signal(market_data)

        if signal_type == SignalType.NONE:
            return None

        # 최소 신뢰도 확인
        if confidence < self.config['min_confidence']:
            return None

        # 포지션 크기 계산
        quantity = self._calculate_position_size(confidence, market_data)

        return self.create_signal(
            market_data=market_data,
            signal_type=signal_type,
            confidence=confidence,
            reason=reason,
            quantity=quantity
        )

    def _is_new_session(self, market_data: OverseasMarketData) -> bool:
        """새로운 거래 세션 확인 (9:30 AM EST)"""
        current_time = datetime.now().time()
        session_start = time(
            self.config['session_start_hour'],
            self.config['session_start_minute']
        )

        # 첫 실행이거나 9:30 AM 이후 첫 데이터인 경우
        if self.session_start_time is None:
            if current_time >= session_start:
                self.session_start_time = datetime.now()
                return True
        else:
            # 전날 세션에서 오늘 세션으로 넘어간 경우
            today = datetime.now().date()
            if self.session_start_time.date() < today and current_time >= session_start:
                self.session_start_time = datetime.now()
                return True

        return False

    def _reset_vwap(self):
        """VWAP 데이터 리셋"""
        self.cumulative_volume = 0
        self.cumulative_volume_price = 0
        self.vwap_data_points.clear()
        self.current_vwap = 0
        self.upper_band = 0
        self.lower_band = 0
        self.std_deviation = 0

    def _update_vwap(self, market_data: OverseasMarketData):
        """VWAP 업데이트"""
        price = market_data.current_price
        volume = market_data.volume

        # 거래량이 0이거나 음수인 경우 기본값 사용
        if volume <= 0:
            volume = 1000  # 기본 거래량

        # 누적 계산
        self.cumulative_volume_price += (price * volume)
        self.cumulative_volume += volume

        # VWAP 계산
        if self.cumulative_volume > 0:
            self.current_vwap = self.cumulative_volume_price / self.cumulative_volume

            # 가격과 VWAP 차이 저장 (표준편차 계산용)
            price_deviation = price - self.current_vwap
            self.vwap_data_points.append(price_deviation)

    def _calculate_bands(self):
        """Upper/Lower Band 계산"""
        if len(self.vwap_data_points) < 2:
            return

        # 표준편차 계산
        deviations = list(self.vwap_data_points)
        self.std_deviation = statistics.stdev(deviations)

        # 밴드 계산
        multiplier = self.config['std_multiplier']
        self.upper_band = self.current_vwap + (multiplier * self.std_deviation)
        self.lower_band = self.current_vwap - (multiplier * self.std_deviation)

    def _generate_vwap_signal(
        self,
        market_data: OverseasMarketData
    ) -> tuple[SignalType, float, str]:
        """VWAP 기반 매매 신호 생성"""

        current_price = market_data.current_price
        reasons = []
        buy_score = 0.0
        sell_score = 0.0

        # 1. VWAP 대비 위치 분석
        vwap_distance_pct = ((current_price - self.current_vwap) / self.current_vwap) * 100

        # 2. 밴드 위치 분석
        if current_price <= self.lower_band:
            # Lower Band 근처 - 매수 신호
            band_distance = abs(current_price - self.lower_band) / self.current_vwap * 100
            buy_score += 0.4
            reasons.append(f"Lower Band 터치 (VWAP 대비 {vwap_distance_pct:.1f}%)")

            # 밴드에 가까울수록 강한 신호
            if band_distance < 0.2:  # 0.2% 이내
                buy_score += 0.2
                reasons.append("밴드 정확히 터치")

        elif current_price >= self.upper_band:
            # Upper Band 근처 - 매도 신호
            band_distance = abs(current_price - self.upper_band) / self.current_vwap * 100
            sell_score += 0.4
            reasons.append(f"Upper Band 터치 (VWAP 대비 {vwap_distance_pct:.1f}%)")

            if band_distance < 0.2:
                sell_score += 0.2
                reasons.append("밴드 정확히 터치")

        # 3. VWAP 회귀 경향 분석
        if len(self.price_history) >= 3:
            recent_prices = list(self.price_history)[-3:]

            # 가격이 VWAP 방향으로 움직이는지 확인
            if current_price < self.current_vwap:
                # VWAP 아래에서 VWAP 방향으로 움직이는지 확인
                if recent_prices[-1] > recent_prices[-2] > recent_prices[-3]:
                    buy_score += 0.15
                    reasons.append("VWAP 회귀 움직임")
            else:
                # VWAP 위에서 VWAP 방향으로 움직이는지 확인
                if recent_prices[-1] < recent_prices[-2] < recent_prices[-3]:
                    sell_score += 0.15
                    reasons.append("VWAP 회귀 움직임")

        # 4. 거래량 분석
        avg_volume = self.get_average_volume(20)
        if market_data.volume > avg_volume * self.config['volume_threshold']:
            volume_multiplier = min(market_data.volume / avg_volume, 3.0) / 3.0
            buy_score += 0.1 * volume_multiplier
            sell_score += 0.1 * volume_multiplier
            reasons.append(f"거래량 급증 ({market_data.volume/avg_volume:.1f}x)")

        # 5. RSI 보조 확인
        rsi = self.calculate_rsi()
        if rsi < 35 and current_price < self.current_vwap:
            buy_score += 0.1
            reasons.append(f"RSI 과매도 ({rsi:.0f})")
        elif rsi > 65 and current_price > self.current_vwap:
            sell_score += 0.1
            reasons.append(f"RSI 과매수 ({rsi:.0f})")

        # 6. 세션별 가중치 적용
        session_weight = self._get_session_weight(market_data.trading_session)
        buy_score *= session_weight
        sell_score *= session_weight

        if session_weight < 1.0:
            reasons.append(f"세션 가중치 ({session_weight:.1f}x)")

        # 7. 최종 신호 결정
        if buy_score > sell_score and buy_score > 0.5:
            confidence = min(buy_score, 1.0)
            return SignalType.BUY, confidence, " | ".join(reasons)
        elif sell_score > buy_score and sell_score > 0.5:
            confidence = min(sell_score, 1.0)
            return SignalType.SELL, confidence, " | ".join(reasons)
        else:
            return SignalType.NONE, 0.0, "신호 강도 부족"

    def _get_session_weight(self, session: TradingSession) -> float:
        """거래시간별 가중치"""
        weights = {
            TradingSession.PRE_MARKET: 0.6,    # 프리마켓은 낮은 가중치
            TradingSession.REGULAR: 1.0,       # 정규장은 정상 가중치
            TradingSession.AFTER_HOURS: 0.4,   # 애프터아워스는 매우 낮은 가중치
            TradingSession.CLOSED: 0.1
        }
        return weights.get(session, 1.0)

    def _calculate_position_size(self, confidence: float, market_data: OverseasMarketData) -> int:
        """포지션 크기 계산"""
        base_quantity = 1

        # 신뢰도 기반 조정
        confidence_multiplier = confidence

        # 변동성 기반 조정 (높은 변동성에서는 포지션 축소)
        volatility = self.get_volatility()
        if volatility > 0:
            volatility_ratio = min(volatility / market_data.current_price * 100, 10.0)
            volatility_multiplier = max(0.5, 1 - (volatility_ratio / 20.0))
        else:
            volatility_multiplier = 1.0

        # 거래량 기반 조정
        avg_volume = self.get_average_volume()
        if avg_volume > 0:
            volume_ratio = market_data.volume / avg_volume
            volume_multiplier = min(1.5, max(0.5, volume_ratio / 2.0))
        else:
            volume_multiplier = 1.0

        final_quantity = int(base_quantity * confidence_multiplier * volatility_multiplier * volume_multiplier)
        return max(1, final_quantity)

    def get_current_analysis(self) -> Dict[str, Any]:
        """현재 전략 분석 상태 반환 (로그용)"""
        if self.current_vwap == 0:
            return {
                'vwap': 0,
                'upper_band': 0,
                'lower_band': 0,
                'std_deviation': 0,
                'position': 'INIT'
            }

        # 현재 가격 위치 판단
        if len(self.price_history) > 0:
            current_price = self.price_history[-1]
            if current_price >= self.upper_band:
                position = 'UPPER'
            elif current_price <= self.lower_band:
                position = 'LOWER'
            else:
                position = 'MID'
        else:
            position = 'UNKNOWN'

        return {
            'vwap': self.current_vwap,
            'upper_band': self.upper_band,
            'lower_band': self.lower_band,
            'std_deviation': self.std_deviation,
            'position': position,
            'data_points': len(self.vwap_data_points)
        }

    def get_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        base_info = super().get_info()

        additional_info = {
            'vwap_current': self.current_vwap,
            'upper_band': self.upper_band,
            'lower_band': self.lower_band,
            'std_deviation': self.std_deviation,
            'cumulative_volume': self.cumulative_volume,
            'data_points': len(self.vwap_data_points),
            'session_start': self.session_start_time.isoformat() if self.session_start_time else None
        }

        base_info.update(additional_info)
        return base_info

    def reset(self):
        """전략 상태 초기화"""
        super().reset()
        self._reset_vwap()
        self.session_start_time = None