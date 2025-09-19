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

    # =================== 공통 급락 방어 로직 ===================

    def _should_apply_risk_filter(self) -> bool:
        """방어 로직 적용 여부 확인

        Returns:
            bool: 리스크 필터 적용 여부
        """
        return self.config.get('enable_crash_protection', True)

    def _detect_crash_momentum(self) -> tuple[bool, float]:
        """급락 모멘텀 감지 (모든 전략 공통 사용)

        Returns:
            tuple[bool, float]: (is_crashing, momentum_percent)
        """
        if len(self.price_history) < 10:
            return False, 0.0

        current_price = self.price_history[-1]

        # 5분간 가격 변화 (약 5개 데이터 포인트 = 5분)
        price_5min_ago = self.price_history[-5] if len(self.price_history) >= 5 else current_price
        momentum_5min = (current_price - price_5min_ago) / price_5min_ago if price_5min_ago > 0 else 0

        # 10분간 가격 변화 (약 10개 데이터 포인트 = 10분)
        price_10min_ago = self.price_history[-10] if len(self.price_history) >= 10 else current_price
        momentum_10min = (current_price - price_10min_ago) / price_10min_ago if price_10min_ago > 0 else 0

        # 급락 기준: 설정에서 읽거나 기본값 사용
        crash_5min_threshold = self.config.get('crash_5min_threshold', -0.02)  # -2%
        crash_10min_threshold = self.config.get('crash_10min_threshold', -0.03)  # -3%

        # 급락 감지
        is_crashing = momentum_5min < crash_5min_threshold or momentum_10min < crash_10min_threshold

        # 더 심각한 모멘텀 반환
        worst_momentum = min(momentum_5min, momentum_10min)

        return is_crashing, worst_momentum

    def _count_consecutive_drops(self) -> int:
        """연속 하락 봉 개수 계산 (모든 전략 공통 사용)

        Returns:
            int: 연속 하락 개수 (최대 10개까지)
        """
        if len(self.price_history) < 2:
            return 0

        consecutive_drops = 0
        for i in range(1, min(11, len(self.price_history))):
            current_idx = len(self.price_history) - i
            prev_idx = current_idx - 1

            if prev_idx < 0:
                break

            # 현재 가격이 이전 가격보다 낮으면 하락
            if self.price_history[current_idx] < self.price_history[prev_idx]:
                consecutive_drops += 1
            else:
                break

        return consecutive_drops

    def _calculate_risk_score(self, market_data: OverseasMarketData) -> int:
        """종합 리스크 점수 계산 (모든 전략 공통 사용)

        Args:
            market_data: 현재 시장 데이터

        Returns:
            int: 리스크 점수 (0=안전, 100=극위험)
        """
        risk_score = 0

        # 1. 급락 모멘텀 (30점)
        is_crashing, momentum = self._detect_crash_momentum()
        if is_crashing:
            if momentum < -0.05:  # -5% 이상 급락
                risk_score += 30
            elif momentum < -0.03:  # -3% 이상 급락
                risk_score += 25
            else:  # -2% 이상 급락
                risk_score += 20
        elif momentum < -0.01:  # -1% 하락
            risk_score += 10

        # 2. 연속 하락 카운터 (20점)
        consecutive_drops = self._count_consecutive_drops()
        if consecutive_drops >= 5:
            risk_score += 20
        elif consecutive_drops >= 3:
            risk_score += 15
        elif consecutive_drops >= 2:
            risk_score += 10
        elif consecutive_drops >= 1:
            risk_score += 5

        # 3. RSI 극단값 (15점)
        rsi = self.calculate_rsi()
        if rsi < 15:  # 극단적 과매도
            risk_score += 5  # 역설적으로 낮은 리스크 (반등 가능성)
        elif rsi < 25:
            risk_score += 8
        elif rsi > 85:  # 극단적 과매수
            risk_score += 15
        elif rsi > 75:
            risk_score += 10

        # 4. 거래량 이상 스파이크 (15점)
        avg_volume = self.get_average_volume()
        if avg_volume > 0:
            volume_ratio = market_data.volume / avg_volume
            if volume_ratio > 5:  # 5배 이상 거래량 급증
                risk_score += 15
            elif volume_ratio > 3:  # 3배 이상 거래량 급증
                risk_score += 10
            elif volume_ratio > 2:  # 2배 이상 거래량 급증
                risk_score += 5

        # 5. 변동성 (20점)
        volatility = self.get_volatility()
        if volatility > 0 and market_data.current_price > 0:
            volatility_percent = volatility / market_data.current_price
            volatility_threshold = self.config.get('volatility_threshold', 0.02)  # 기본 2%

            if volatility_percent > volatility_threshold * 2:  # 4% 이상 변동성
                risk_score += 20
            elif volatility_percent > volatility_threshold * 1.5:  # 3% 이상 변동성
                risk_score += 15
            elif volatility_percent > volatility_threshold:  # 2% 이상 변동성
                risk_score += 10
            elif volatility_percent > volatility_threshold * 0.75:  # 1.5% 이상 변동성
                risk_score += 5

        return min(risk_score, 100)

    def _apply_risk_filter(self, buy_score: float, sell_score: float, reasons: list, market_data: OverseasMarketData) -> tuple[float, float, list]:
        """리스크 필터 적용 (모든 전략 공통 사용)

        Args:
            buy_score: 원래 매수 점수
            sell_score: 원래 매도 점수
            reasons: 신호 이유 리스트
            market_data: 현재 시장 데이터

        Returns:
            tuple[float, float, list]: (조정된 매수 점수, 조정된 매도 점수, 업데이트된 이유)
        """
        # 방어 로직 비활성화 시 원본 반환
        if not self._should_apply_risk_filter():
            return buy_score, sell_score, reasons

        # 리스크 체크
        risk_score = self._calculate_risk_score(market_data)
        is_crashing, momentum = self._detect_crash_momentum()
        consecutive_drops = self._count_consecutive_drops()

        # 설정에서 리스크 임계값 읽기
        risk_threshold_critical = self.config.get('risk_threshold_critical', 70)
        risk_threshold_high = self.config.get('risk_threshold_high', 50)
        risk_threshold_medium = self.config.get('risk_threshold_medium', 30)
        risk_threshold_low = self.config.get('risk_threshold_low', 15)

        # 급락 모멘텀 체크 (최우선)
        if is_crashing:
            crash_reduction = self.config.get('crash_signal_reduction', 0.1)  # 기본 90% 약화
            reasons.append(f"🚨 급락 감지 ({momentum*100:.1f}%)")
            buy_score *= crash_reduction

        # 연속 하락 체크
        consecutive_threshold = self.config.get('consecutive_drops_threshold', 3)
        if consecutive_drops >= consecutive_threshold:
            consecutive_reduction = self.config.get('consecutive_signal_reduction', 0.5)  # 기본 50% 약화
            reasons.append(f"⚠️ 연속 {consecutive_drops}회 하락")
            buy_score *= consecutive_reduction

        # 종합 리스크 점수 적용
        if risk_score > risk_threshold_critical:
            reasons.append(f"🚨 극고위험 (리스크: {risk_score})")
            buy_score *= 0.1  # 매수 신호 90% 약화
        elif risk_score > risk_threshold_high:
            reasons.append(f"⚠️ 고위험 (리스크: {risk_score})")
            buy_score *= 0.3  # 매수 신호 70% 약화
        elif risk_score > risk_threshold_medium:
            reasons.append(f"⚠️ 주의 (리스크: {risk_score})")
            buy_score *= 0.7  # 매수 신호 30% 약화
        elif risk_score > risk_threshold_low:
            reasons.append(f"ℹ️ 경미한 리스크 ({risk_score})")
            buy_score *= 0.9  # 매수 신호 10% 약화

        return buy_score, sell_score, reasons

    def _adjust_position_size_for_risk(self, quantity: int, risk_score: int) -> int:
        """리스크에 따른 포지션 크기 조절 (모든 전략 공통 사용)

        Args:
            quantity: 원래 포지션 크기
            risk_score: 리스크 점수 (0-100)

        Returns:
            int: 조정된 포지션 크기
        """
        # 방어 로직 비활성화 시 원본 반환
        if not self._should_apply_risk_filter():
            return quantity

        # 설정에서 임계값 읽기
        risk_threshold_critical = self.config.get('risk_threshold_critical', 70)
        risk_threshold_high = self.config.get('risk_threshold_high', 50)
        risk_threshold_medium = self.config.get('risk_threshold_medium', 30)
        risk_threshold_low = self.config.get('risk_threshold_low', 15)

        # 설정에서 축소 비율 읽기
        reduction_critical = self.config.get('position_reduction_critical', 0.1)  # 90% 축소
        reduction_high = self.config.get('position_reduction_high', 0.33)  # 67% 축소
        reduction_medium = self.config.get('position_reduction_medium', 0.5)  # 50% 축소
        reduction_low = self.config.get('position_reduction_low', 0.8)  # 20% 축소

        if risk_score > risk_threshold_critical:
            return max(1, int(quantity * reduction_critical))
        elif risk_score > risk_threshold_high:
            return max(1, int(quantity * reduction_high))
        elif risk_score > risk_threshold_medium:
            return max(1, int(quantity * reduction_medium))
        elif risk_score > risk_threshold_low:
            return max(1, int(quantity * reduction_low))
        else:
            return quantity

    def get_risk_analysis(self, market_data: OverseasMarketData) -> Dict[str, Any]:
        """현재 리스크 분석 정보 반환 (로깅 및 모니터링용)

        Args:
            market_data: 현재 시장 데이터

        Returns:
            Dict[str, Any]: 리스크 분석 결과
        """
        if not self._should_apply_risk_filter():
            return {
                'risk_protection_enabled': False,
                'risk_score': 0,
                'is_crashing': False,
                'momentum_5min': 0.0,
                'consecutive_drops': 0,
                'volatility_percent': 0.0
            }

        risk_score = self._calculate_risk_score(market_data)
        is_crashing, momentum = self._detect_crash_momentum()
        consecutive_drops = self._count_consecutive_drops()

        # 변동성 계산
        volatility = self.get_volatility()
        volatility_percent = (volatility / market_data.current_price * 100) if volatility > 0 and market_data.current_price > 0 else 0.0

        return {
            'risk_protection_enabled': True,
            'risk_score': risk_score,
            'is_crashing': is_crashing,
            'momentum_5min': round(momentum * 100, 2),  # 퍼센트로 변환
            'consecutive_drops': consecutive_drops,
            'volatility_percent': round(volatility_percent, 2)
        }