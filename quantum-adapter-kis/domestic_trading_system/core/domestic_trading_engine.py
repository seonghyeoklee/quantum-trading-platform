"""
국내주식 거래 엔진
실시간 데이터 기반 자동매매 엔진
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from threading import Lock

from domestic_trading_system.core.domestic_data_types import (
    DomesticMarketData, TradingSignal, MarketType, TradingSession
)


class DomesticTradingEngine:
    """국내주식 자동매매 엔진"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("domestic_trading_engine")

        # 설정
        self.config = config
        self.max_positions = config.get('max_positions', 5)
        self.default_quantity = config.get('default_quantity', 1)
        self.min_confidence = config.get('min_confidence', 0.7)

        # 거래 상태
        self.is_trading_enabled = False
        self.positions = {}  # symbol -> position info
        self.strategies = {}  # symbol -> strategy instance
        self.market_data_history = {}  # symbol -> list of market data
        self.data_lock = Lock()

        # 주문 실행기
        self.order_executor = None

        # 통계
        self.total_signals = 0
        self.total_orders = 0
        self.successful_orders = 0

    def set_order_executor(self, executor: Callable):
        """주문 실행기 설정"""
        self.order_executor = executor
        self.logger.info("주문 실행기 설정 완료")

    def add_stock(self, symbol: str, strategy):
        """종목 및 전략 추가"""
        self.strategies[symbol] = strategy
        self.market_data_history[symbol] = []
        self.logger.info(f"종목 추가: {symbol} - {strategy.__class__.__name__}")

    def remove_stock(self, symbol: str):
        """종목 제거"""
        if symbol in self.strategies:
            del self.strategies[symbol]
        if symbol in self.market_data_history:
            del self.market_data_history[symbol]
        if symbol in self.positions:
            del self.positions[symbol]
        self.logger.info(f"종목 제거: {symbol}")

    def enable_trading(self):
        """거래 활성화"""
        self.is_trading_enabled = True
        self.logger.info("🟢 자동매매 활성화")

    def disable_trading(self):
        """거래 비활성화"""
        self.is_trading_enabled = False
        self.logger.info("🔴 자동매매 비활성화")

    async def update_market_data(self, symbol: str, market_data: DomesticMarketData) -> Optional[TradingSignal]:
        """시장 데이터 업데이트 및 신호 생성"""
        try:
            # 데이터 히스토리 업데이트
            with self.data_lock:
                if symbol not in self.market_data_history:
                    self.market_data_history[symbol] = []

                self.market_data_history[symbol].append(market_data)

                # 최대 1000개 데이터만 유지 (메모리 관리)
                if len(self.market_data_history[symbol]) > 1000:
                    self.market_data_history[symbol] = self.market_data_history[symbol][-1000:]

            # 거래 가능 시간 확인
            if market_data.trading_session == TradingSession.CLOSED:
                return None

            # 전략 신호 생성
            if symbol in self.strategies:
                strategy = self.strategies[symbol]
                signal = await self._generate_signal(symbol, market_data, strategy)

                if signal:
                    self.total_signals += 1

                    # 거래 활성화 상태에서만 주문 실행
                    if self.is_trading_enabled and signal.confidence >= self.min_confidence:
                        await self._execute_signal(signal)

                    return signal

        except Exception as e:
            self.logger.error(f"시장 데이터 업데이트 오류 [{symbol}]: {e}")

        return None

    async def _generate_signal(self, symbol: str, market_data: DomesticMarketData, strategy) -> Optional[TradingSignal]:
        """전략 기반 신호 생성"""
        try:
            # 최근 데이터 가져오기
            with self.data_lock:
                history = self.market_data_history.get(symbol, [])

            # 최소 데이터 요구사항 확인
            if len(history) < 20:  # 최소 20개 데이터 필요
                return None

            # 전략별 신호 생성
            if hasattr(strategy, 'generate_signal'):
                signal_data = await strategy.generate_signal(history, market_data)

                if signal_data:
                    signal = TradingSignal(
                        symbol=symbol,
                        signal_type=signal_data['type'],
                        confidence=signal_data['confidence'],
                        reason=signal_data['reason'],
                        price=market_data.current_price,
                        timestamp=datetime.now(),
                        strategy_name=strategy.__class__.__name__,
                        target_quantity=signal_data.get('quantity', self.default_quantity)
                    )

                    self.logger.info(f"신호 생성: {symbol} {signal.signal_type} (신뢰도: {signal.confidence:.2f})")
                    return signal

        except Exception as e:
            self.logger.error(f"신호 생성 오류 [{symbol}]: {e}")

        return None

    async def _execute_signal(self, signal: TradingSignal):
        """신호 실행"""
        try:
            # 포지션 확인
            current_position = self.positions.get(signal.symbol, 0)

            # 매수 신호 처리
            if signal.signal_type == "BUY":
                if current_position >= 0:  # 롱 포지션이 아니거나 중립
                    if len(self.positions) >= self.max_positions:
                        self.logger.warning(f"최대 포지션 수 초과: {signal.symbol}")
                        return

                    # 주문 실행
                    if self.order_executor:
                        success = await self._execute_order(signal)
                        if success:
                            self.positions[signal.symbol] = current_position + signal.target_quantity
                            self.successful_orders += 1

            # 매도 신호 처리
            elif signal.signal_type == "SELL":
                if current_position > 0:  # 매도할 포지션이 있을 때만
                    # 주문 실행
                    if self.order_executor:
                        success = await self._execute_order(signal)
                        if success:
                            self.positions[signal.symbol] = max(0, current_position - signal.target_quantity)
                            self.successful_orders += 1

            self.total_orders += 1

        except Exception as e:
            self.logger.error(f"신호 실행 오류: {e}")

    async def _execute_order(self, signal: TradingSignal) -> bool:
        """실제 주문 실행"""
        try:
            if self.order_executor:
                order_result = await self.order_executor(signal)

                if order_result.get('success', False):
                    self.logger.info(f"✅ 주문 성공: {signal.symbol} {signal.signal_type} {signal.target_quantity}주")
                    return True
                else:
                    self.logger.error(f"❌ 주문 실패: {signal.symbol} - {order_result.get('error', 'Unknown error')}")
                    return False
            else:
                self.logger.warning("주문 실행기가 설정되지 않음")
                return False

        except Exception as e:
            self.logger.error(f"주문 실행 오류: {e}")
            return False

    def get_position(self, symbol: str) -> int:
        """포지션 조회"""
        return self.positions.get(symbol, 0)

    def get_all_positions(self) -> Dict[str, int]:
        """모든 포지션 조회"""
        return self.positions.copy()

    def get_strategy_analysis(self, symbol: str) -> Optional[Dict]:
        """전략 분석 정보 조회"""
        try:
            if symbol in self.strategies:
                strategy = self.strategies[symbol]
                if hasattr(strategy, 'get_current_analysis'):
                    return strategy.get_current_analysis()
        except Exception as e:
            self.logger.error(f"전략 분석 조회 오류 [{symbol}]: {e}")
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """거래 통계 조회"""
        success_rate = 0.0
        if self.total_orders > 0:
            success_rate = self.successful_orders / self.total_orders

        return {
            'total_signals': self.total_signals,
            'total_orders': self.total_orders,
            'successful_orders': self.successful_orders,
            'success_rate': success_rate,
            'active_positions': len([p for p in self.positions.values() if p > 0]),
            'total_symbols': len(self.strategies),
            'trading_enabled': self.is_trading_enabled
        }

    def get_market_data_summary(self, symbol: str, limit: int = 50) -> List[Dict]:
        """시장 데이터 요약 조회"""
        try:
            with self.data_lock:
                history = self.market_data_history.get(symbol, [])

            if not history:
                return []

            # 최근 데이터만 반환
            recent_data = history[-limit:]

            summary = []
            for data in recent_data:
                summary.append({
                    'timestamp': data.timestamp.isoformat(),
                    'price': data.current_price,
                    'change_percent': data.change_percent,
                    'volume': data.volume,
                    'trading_session': data.trading_session.value
                })

            return summary

        except Exception as e:
            self.logger.error(f"시장 데이터 요약 조회 오류 [{symbol}]: {e}")
            return []

    async def cleanup(self):
        """정리 작업"""
        try:
            # 모든 포지션 정리 (실제 운영에서는 신중하게 처리)
            self.logger.info("거래 엔진 정리 시작")

            # 통계 로그
            stats = self.get_statistics()
            self.logger.info(f"최종 통계: {stats}")

            # 메모리 정리
            self.market_data_history.clear()
            self.strategies.clear()

            self.logger.info("거래 엔진 정리 완료")

        except Exception as e:
            self.logger.error(f"정리 작업 오류: {e}")


# 테스트 함수
async def test_domestic_trading_engine():
    """국내주식 거래 엔진 테스트"""
    print("=== 국내주식 거래 엔진 테스트 ===")

    # 테스트 설정
    config = {
        'max_positions': 3,
        'default_quantity': 1,
        'min_confidence': 0.8
    }

    # 거래 엔진 초기화
    engine = DomesticTradingEngine(config)

    # 테스트 주문 실행기
    async def test_order_executor(signal):
        print(f"📋 테스트 주문: {signal.symbol} {signal.signal_type} {signal.target_quantity}주")
        return {'success': True, 'order_id': f'TEST_{signal.symbol}_{datetime.now().strftime("%H%M%S")}'}

    engine.set_order_executor(test_order_executor)

    # 테스트 전략 (단순한 예시)
    class TestStrategy:
        async def generate_signal(self, history, current_data):
            # 단순한 테스트 신호 (5% 이상 상승시 매도, 5% 이상 하락시 매수)
            if current_data.change_percent > 5:
                return {
                    'type': 'SELL',
                    'confidence': 0.9,
                    'reason': '5% 이상 상승으로 매도 신호',
                    'quantity': 1
                }
            elif current_data.change_percent < -5:
                return {
                    'type': 'BUY',
                    'confidence': 0.9,
                    'reason': '5% 이상 하락으로 매수 신호',
                    'quantity': 1
                }
            return None

    # 테스트 종목 추가
    engine.add_stock("005930", TestStrategy())  # 삼성전자
    engine.enable_trading()

    print("✅ 거래 엔진 테스트 설정 완료")
    print("거래 엔진이 정상적으로 초기화되었습니다.")

    # 통계 출력
    stats = engine.get_statistics()
    print(f"📊 초기 통계: {stats}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(test_domestic_trading_engine())