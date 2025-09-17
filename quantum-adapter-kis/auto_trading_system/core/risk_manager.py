"""
리스크 관리자
매매 신호의 리스크를 평가하고 제한하는 시스템
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .data_types import Signal, MarketData, SignalType


class RiskManager:
    """리스크 관리자"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: 리스크 관리 설정
        """
        self.config = config or {}

        # 기본 리스크 설정
        self.max_daily_trades = self.config.get('max_daily_trades', 10)  # 일일 최대 거래 수
        self.max_position_size = self.config.get('max_position_size', 1000000)  # 최대 포지션 크기 (원)
        self.max_loss_per_trade = self.config.get('max_loss_per_trade', 50000)  # 거래당 최대 손실 (원)
        self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.6)  # 최소 신뢰도
        self.max_correlation_exposure = self.config.get('max_correlation_exposure', 0.3)  # 최대 상관관계 노출

        # 시간 기반 제한
        self.trading_start_time = self.config.get('trading_start_time', '09:00')  # 거래 시작 시간
        self.trading_end_time = self.config.get('trading_end_time', '15:30')  # 거래 종료 시간
        self.avoid_market_open_minutes = self.config.get('avoid_market_open_minutes', 10)  # 시장 개장 후 회피 시간
        self.avoid_market_close_minutes = self.config.get('avoid_market_close_minutes', 10)  # 시장 마감 전 회피 시간

        # 변동성 기반 제한
        self.max_volatility_threshold = self.config.get('max_volatility_threshold', 0.05)  # 최대 허용 변동성 (5%)
        self.min_volume_threshold = self.config.get('min_volume_threshold', 1000)  # 최소 거래량

        # 내부 상태
        self.daily_trade_count: Dict[str, int] = {}  # symbol -> count
        self.last_reset_date: Optional[datetime] = None
        self.risk_violations: List[Dict[str, Any]] = []

        self.logger = logging.getLogger("risk_manager")

    def validate_signal(self, symbol: str, signal: Signal, market_data: Optional[MarketData] = None) -> bool:
        """
        신호 리스크 검증

        Args:
            symbol: 종목 코드
            signal: 매매 신호
            market_data: 시장 데이터

        Returns:
            검증 통과 여부
        """
        try:
            # 일일 거래 횟수 초기화
            self._reset_daily_counters_if_needed()

            # 각종 리스크 검증
            validations = [
                ('신뢰도', self._validate_confidence(signal)),
                ('거래 시간', self._validate_trading_time()),
                ('일일 거래 한도', self._validate_daily_trade_limit(symbol)),
                ('포지션 크기', self._validate_position_size(signal)),
                ('시장 데이터', self._validate_market_conditions(market_data) if market_data else True),
                ('변동성', self._validate_volatility(market_data) if market_data else True),
                ('거래량', self._validate_volume(market_data) if market_data else True)
            ]

            # 검증 실행
            for validation_name, is_valid in validations:
                if not is_valid:
                    self._record_risk_violation(symbol, signal, validation_name)
                    return False

            # 모든 검증 통과
            self._increment_daily_trade_count(symbol)
            return True

        except Exception as e:
            self.logger.error(f"리스크 검증 오류 [{symbol}]: {e}")
            return False

    def _validate_confidence(self, signal: Signal) -> bool:
        """신뢰도 검증"""
        return signal.confidence >= self.min_confidence_threshold

    def _validate_trading_time(self) -> bool:
        """거래 시간 검증"""
        now = datetime.now()
        current_time = now.time()

        # 거래 시간 파싱
        start_time = datetime.strptime(self.trading_start_time, '%H:%M').time()
        end_time = datetime.strptime(self.trading_end_time, '%H:%M').time()

        # 기본 거래 시간 확인
        if not (start_time <= current_time <= end_time):
            return False

        # 시장 개장 직후 회피
        market_open = datetime.combine(now.date(), start_time)
        avoid_until = market_open + timedelta(minutes=self.avoid_market_open_minutes)
        if now <= avoid_until:
            return False

        # 시장 마감 직전 회피
        market_close = datetime.combine(now.date(), end_time)
        avoid_from = market_close - timedelta(minutes=self.avoid_market_close_minutes)
        if now >= avoid_from:
            return False

        return True

    def _validate_daily_trade_limit(self, symbol: str) -> bool:
        """일일 거래 한도 검증"""
        current_count = self.daily_trade_count.get(symbol, 0)
        return current_count < self.max_daily_trades

    def _validate_position_size(self, signal: Signal) -> bool:
        """포지션 크기 검증"""
        position_value = signal.price * signal.quantity
        return position_value <= self.max_position_size

    def _validate_market_conditions(self, market_data: MarketData) -> bool:
        """시장 상황 검증"""
        # 기본적인 시장 데이터 유효성 확인
        if market_data.current_price <= 0:
            return False

        if market_data.high_price < market_data.low_price:
            return False

        if market_data.volume < 0:
            return False

        return True

    def _validate_volatility(self, market_data: MarketData) -> bool:
        """변동성 검증"""
        if market_data.high_price == market_data.low_price:
            return True  # 변동성 0

        # 일일 변동성 계산
        daily_volatility = (market_data.high_price - market_data.low_price) / market_data.current_price

        return daily_volatility <= self.max_volatility_threshold

    def _validate_volume(self, market_data: MarketData) -> bool:
        """거래량 검증"""
        return market_data.volume >= self.min_volume_threshold

    def _reset_daily_counters_if_needed(self):
        """일일 카운터 초기화 (필요시)"""
        today = datetime.now().date()

        if self.last_reset_date != today:
            self.daily_trade_count.clear()
            self.last_reset_date = today
            self.logger.info(f"일일 카운터 초기화: {today}")

    def _increment_daily_trade_count(self, symbol: str):
        """일일 거래 횟수 증가"""
        self.daily_trade_count[symbol] = self.daily_trade_count.get(symbol, 0) + 1

    def _record_risk_violation(self, symbol: str, signal: Signal, violation_type: str):
        """리스크 위반 기록"""
        violation = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'signal_type': signal.signal_type.value,
            'violation_type': violation_type,
            'signal_confidence': signal.confidence,
            'signal_reason': signal.reason
        }

        self.risk_violations.append(violation)

        # 위반 기록 크기 제한 (최근 100개)
        if len(self.risk_violations) > 100:
            self.risk_violations = self.risk_violations[-100:]

        self.logger.warning(
            f"리스크 위반 [{symbol}]: {violation_type} - "
            f"{signal.signal_type.value} (신뢰도: {signal.confidence:.2f})"
        )

    def get_daily_trade_count(self, symbol: str = None) -> Dict[str, int]:
        """일일 거래 횟수 조회"""
        self._reset_daily_counters_if_needed()

        if symbol:
            return {symbol: self.daily_trade_count.get(symbol, 0)}
        return self.daily_trade_count.copy()

    def get_risk_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """리스크 위반 기록 조회"""
        return self.risk_violations[-limit:] if limit else self.risk_violations

    def is_trading_allowed(self) -> bool:
        """현재 거래 허용 여부"""
        return self._validate_trading_time()

    def get_risk_metrics(self) -> Dict[str, Any]:
        """리스크 지표 조회"""
        self._reset_daily_counters_if_needed()

        total_daily_trades = sum(self.daily_trade_count.values())
        violation_count_by_type = {}

        # 위반 유형별 집계
        for violation in self.risk_violations:
            violation_type = violation['violation_type']
            violation_count_by_type[violation_type] = violation_count_by_type.get(violation_type, 0) + 1

        return {
            'is_trading_allowed': self.is_trading_allowed(),
            'daily_trade_count': total_daily_trades,
            'max_daily_trades': self.max_daily_trades,
            'daily_trade_usage': (total_daily_trades / self.max_daily_trades) * 100 if self.max_daily_trades > 0 else 0,
            'total_violations': len(self.risk_violations),
            'violations_by_type': violation_count_by_type,
            'last_reset_date': self.last_reset_date.isoformat() if self.last_reset_date else None,
            'config': {
                'max_daily_trades': self.max_daily_trades,
                'max_position_size': self.max_position_size,
                'min_confidence_threshold': self.min_confidence_threshold,
                'max_volatility_threshold': self.max_volatility_threshold,
                'trading_hours': f"{self.trading_start_time} - {self.trading_end_time}"
            }
        }

    def update_config(self, new_config: Dict[str, Any]):
        """리스크 설정 업데이트"""
        self.config.update(new_config)

        # 설정 재로드
        self.max_daily_trades = self.config.get('max_daily_trades', self.max_daily_trades)
        self.max_position_size = self.config.get('max_position_size', self.max_position_size)
        self.max_loss_per_trade = self.config.get('max_loss_per_trade', self.max_loss_per_trade)
        self.min_confidence_threshold = self.config.get('min_confidence_threshold', self.min_confidence_threshold)

        self.logger.info(f"리스크 설정 업데이트: {new_config}")

    def reset_violations(self):
        """위반 기록 초기화"""
        violation_count = len(self.risk_violations)
        self.risk_violations.clear()
        self.logger.info(f"위반 기록 초기화: {violation_count}건 삭제")

    def emergency_stop(self):
        """긴급 정지 (모든 거래 차단)"""
        # 일일 거래 한도를 0으로 설정하여 모든 거래 차단
        for symbol in self.daily_trade_count.keys():
            self.daily_trade_count[symbol] = self.max_daily_trades

        self.logger.critical("긴급 정지 활성화 - 모든 거래 차단")