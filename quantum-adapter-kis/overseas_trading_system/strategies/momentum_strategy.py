"""
모멘텀 추종 전략 (해외시장 특화)
Pre-market 데이터, 볼륨 급증, 기술적 지표를 종합한 모멘텀 전략
"""

from typing import Optional, Dict, Any
from datetime import datetime

from overseas_trading_system.core.overseas_data_types import (
    OverseasMarketData, OverseasTradingSignal, SignalType, TradingSession
)
from .base_strategy import BaseOverseasStrategy


class MomentumStrategy(BaseOverseasStrategy):
    """모멘텀 추종 전략"""

    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'rsi_oversold': 30,          # RSI 과매도 기준
            'rsi_overbought': 70,        # RSI 과매수 기준
            'volume_spike_threshold': 2.0,  # 거래량 급증 기준 (평균의 2배)
            'price_change_threshold': 0.02,  # 가격 변동 기준 (2%)
            'min_confidence': 0.6,       # 최소 신뢰도
            'ma_short': 5,               # 단기 이동평균
            'ma_long': 20,               # 장기 이동평균
            'pre_market_weight': 1.5,    # 프리마켓 가중치
            'regular_hours_weight': 1.0,  # 정규장 가중치
            'after_hours_weight': 0.8    # 애프터아워스 가중치
        }

        if config:
            default_config.update(config)

        super().__init__(default_config)
        self.name = "Momentum Following Strategy"

        # 추가 히스토리
        self.pre_market_prices = []
        self.gap_history = []

    def analyze_signal(self, market_data: OverseasMarketData) -> Optional[OverseasTradingSignal]:
        """모멘텀 분석 및 신호 생성"""
        # 데이터 히스토리에 추가
        self.add_market_data(market_data)

        # 최소 데이터 확인
        if len(self.price_history) < self.config['ma_long']:
            return None

        # 1. 기본 기술적 분석
        rsi = self.calculate_rsi()
        ma_short = self.get_average_price(self.config['ma_short'])
        ma_long = self.get_average_price(self.config['ma_long'])
        volatility = self.get_volatility()

        # 2. 거래량 분석
        volume_spike = self.is_volume_spike(self.config['volume_spike_threshold'])
        volume_ratio = market_data.volume / self.get_average_volume() if self.get_average_volume() > 0 else 1.0

        # 3. 가격 변동 분석
        price_change_pct = abs(market_data.change_percent)
        significant_move = price_change_pct >= self.config['price_change_threshold'] * 100

        # 4. 거래시간 가중치
        session_weight = self._get_session_weight(market_data.trading_session)

        # 5. 프리마켓 갭 분석
        gap_strength = self._analyze_gap(market_data)

        # 6. 모멘텀 신호 생성
        signal_type, confidence, reason = self._generate_momentum_signal(
            market_data, rsi, ma_short, ma_long, volume_spike, volume_ratio,
            significant_move, session_weight, gap_strength, volatility
        )

        if signal_type == SignalType.NONE:
            return None

        # 최소 신뢰도 확인
        if confidence < self.config['min_confidence']:
            return None

        # 포지션 크기 계산
        quantity = self._calculate_position_size(confidence, volatility, volume_ratio)

        # 리스크 기반 포지션 크기 조절 (BaseOverseasStrategy 공통 방어 로직)
        risk_score = self._calculate_risk_score(market_data)
        quantity = self._adjust_position_size_for_risk(quantity, risk_score)

        return self.create_signal(
            market_data=market_data,
            signal_type=signal_type,
            confidence=confidence,
            reason=reason,
            quantity=quantity
        )

    def _get_session_weight(self, session: TradingSession) -> float:
        """거래시간별 가중치"""
        weights = {
            TradingSession.PRE_MARKET: self.config['pre_market_weight'],
            TradingSession.REGULAR: self.config['regular_hours_weight'],
            TradingSession.AFTER_HOURS: self.config['after_hours_weight'],
            TradingSession.CLOSED: 0.1
        }
        return weights.get(session, 1.0)

    def _analyze_gap(self, market_data: OverseasMarketData) -> float:
        """갭 분석 (전일 종가 대비 시가 갭)"""
        if market_data.previous_close == 0 or market_data.open_price == 0:
            return 0.0

        gap_percent = ((market_data.open_price - market_data.previous_close) / market_data.previous_close) * 100
        self.gap_history.append(gap_percent)

        # 갭의 강도 계산 (절댓값)
        gap_strength = min(abs(gap_percent) / 5.0, 1.0)  # 5% 갭을 최대로 정규화

        return gap_strength

    def _generate_momentum_signal(
        self,
        market_data: OverseasMarketData,
        rsi: float,
        ma_short: float,
        ma_long: float,
        volume_spike: bool,
        volume_ratio: float,
        significant_move: bool,
        session_weight: float,
        gap_strength: float,
        volatility: float
    ) -> tuple[SignalType, float, str]:
        """모멘텀 신호 생성"""

        reasons = []
        buy_score = 0.0
        sell_score = 0.0

        # 1. 이동평균 분석
        if ma_short > ma_long:
            buy_score += 0.2
            reasons.append("단기MA > 장기MA")
        else:
            sell_score += 0.1
            reasons.append("단기MA < 장기MA")

        # 2. RSI 분석
        if rsi < self.config['rsi_oversold']:
            buy_score += 0.3
            reasons.append(f"RSI 과매도({rsi:.1f})")
        elif rsi > self.config['rsi_overbought']:
            sell_score += 0.3
            reasons.append(f"RSI 과매수({rsi:.1f})")

        # 3. 거래량 분석
        if volume_spike:
            buy_score += 0.2
            reasons.append(f"거래량 급증({volume_ratio:.1f}x)")

        # 4. 가격 모멘텀 분석
        if significant_move:
            if market_data.change > 0:
                buy_score += 0.15
                reasons.append(f"상승모멘텀({market_data.change_percent:+.1f}%)")
            else:
                sell_score += 0.15
                reasons.append(f"하락모멘텀({market_data.change_percent:+.1f}%)")

        # 5. 갭 분석
        if gap_strength > 0.3:  # 1.5% 이상 갭
            if market_data.open_price > market_data.previous_close:
                buy_score += gap_strength * 0.2
                reasons.append(f"상승갭({gap_strength*5:.1f}%)")
            else:
                sell_score += gap_strength * 0.1
                reasons.append(f"하락갭({gap_strength*5:.1f}%)")

        # 6. 변동성 조정
        volatility_factor = min(volatility / market_data.current_price * 100, 0.1)
        if volatility_factor > 0.03:  # 3% 이상 변동성
            buy_score *= (1 - volatility_factor)
            sell_score *= (1 - volatility_factor)
            reasons.append(f"고변동성({volatility_factor*100:.1f}%)")

        # 7. 거래시간 가중치 적용
        buy_score *= session_weight
        sell_score *= session_weight

        # 8. 급락 방어 리스크 필터 적용 (BaseOverseasStrategy 공통 방어 로직)
        buy_score, sell_score, reasons = self._apply_risk_filter(buy_score, sell_score, reasons, market_data)

        # 9. 최종 신호 결정
        if buy_score > sell_score and buy_score > 0.4:
            confidence = min(buy_score, 1.0)
            return SignalType.BUY, confidence, " | ".join(reasons)
        elif sell_score > buy_score and sell_score > 0.3:
            confidence = min(sell_score, 1.0)
            return SignalType.SELL, confidence, " | ".join(reasons)
        else:
            return SignalType.NONE, 0.0, "신호 강도 부족"

    def _calculate_position_size(self, confidence: float, volatility: float, volume_ratio: float) -> int:
        """포지션 크기 계산"""
        base_quantity = 1

        # 신뢰도 기반 조정
        confidence_multiplier = confidence

        # 변동성 기반 조정 (변동성이 높으면 포지션 축소)
        volatility_ratio = volatility / 100  # 변동성을 비율로 변환
        volatility_multiplier = max(0.5, 1 - volatility_ratio)

        # 거래량 기반 조정
        volume_multiplier = min(2.0, volume_ratio)

        final_quantity = int(base_quantity * confidence_multiplier * volatility_multiplier * volume_multiplier)

        return max(1, final_quantity)

    def get_info(self) -> Dict[str, Any]:
        """전략 정보 반환"""
        base_info = super().get_info()

        additional_info = {
            'rsi_current': self.calculate_rsi() if len(self.price_history) >= 14 else 0,
            'ma_short': self.get_average_price(self.config['ma_short']),
            'ma_long': self.get_average_price(self.config['ma_long']),
            'volume_spike': self.is_volume_spike(),
            'volatility': self.get_volatility(),
            'gap_count': len(self.gap_history),
            'avg_gap': sum(self.gap_history) / len(self.gap_history) if self.gap_history else 0
        }

        base_info.update(additional_info)
        return base_info