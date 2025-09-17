"""
자동매매 엔진
종목별 전략 실행, 포지션 관리, 주문 실행을 담당하는 핵심 엔진
"""

from typing import Dict, List, Optional, Callable, Any
import asyncio
import logging
from datetime import datetime, timedelta
from threading import Lock
import uuid

from ..core.data_types import (
    MarketData, Signal, Position, Order, TradingStats,
    SignalType, PositionType, OrderType, OrderStatus
)
from ..strategies.base_strategy import BaseStrategy, StrategyContext
from .position_manager import PositionManager
from .risk_manager import RiskManager


class AutoTradingEngine:
    """자동매매 엔진"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: 엔진 설정
        """
        self.config = config or {}

        # 기본 설정
        self.max_positions = self.config.get('max_positions', 10)  # 최대 동시 포지션
        self.default_quantity = self.config.get('default_quantity', 100)  # 기본 주문 수량
        self.execution_delay = self.config.get('execution_delay', 0.1)  # 주문 실행 지연 (초)

        # 핵심 컴포넌트
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager(self.config.get('risk_config', {}))

        # 종목별 상태 관리
        self.strategies: Dict[str, StrategyContext] = {}  # symbol -> StrategyContext
        self.market_data: Dict[str, MarketData] = {}  # symbol -> latest MarketData
        self.trading_stats: Dict[str, TradingStats] = {}  # symbol -> TradingStats

        # 주문 관리
        self.pending_orders: Dict[str, Order] = {}  # order_id -> Order
        self.order_history: List[Order] = []

        # 이벤트 콜백
        self.order_executor: Optional[Callable] = None  # 주문 실행 콜백
        self.event_callbacks: Dict[str, List[Callable]] = {
            'signal_generated': [],
            'order_placed': [],
            'order_filled': [],
            'position_opened': [],
            'position_closed': []
        }

        # 엔진 상태
        self.is_running = False
        self.is_trading_enabled = True
        self.data_lock = Lock()

        self.logger = logging.getLogger("trading_engine")

    def add_stock(self, symbol: str, strategy: BaseStrategy):
        """
        종목 추가

        Args:
            symbol: 종목 코드
            strategy: 매매 전략
        """
        with self.data_lock:
            self.strategies[symbol] = StrategyContext(strategy)
            self.trading_stats[symbol] = TradingStats()

        self.logger.info(f"종목 추가: {symbol} - {strategy.name} 전략")

    def remove_stock(self, symbol: str):
        """종목 제거"""
        with self.data_lock:
            # 기존 포지션 정리
            position = self.position_manager.get_position(symbol)
            if position:
                self.logger.warning(f"포지션이 있는 종목 제거: {symbol}")

            # 상태 제거
            self.strategies.pop(symbol, None)
            self.market_data.pop(symbol, None)
            self.trading_stats.pop(symbol, None)

        self.logger.info(f"종목 제거: {symbol}")

    def change_strategy(self, symbol: str, strategy: BaseStrategy):
        """전략 변경"""
        if symbol not in self.strategies:
            self.logger.error(f"존재하지 않는 종목: {symbol}")
            return

        with self.data_lock:
            self.strategies[symbol].set_strategy(strategy)

        self.logger.info(f"전략 변경 [{symbol}]: {strategy.name}")

    def set_order_executor(self, executor: Callable):
        """
        주문 실행기 설정

        Args:
            executor: 주문 실행 함수 (symbol, signal) -> order_id
        """
        self.order_executor = executor
        self.logger.info("주문 실행기 설정 완료")

    def add_event_callback(self, event_type: str, callback: Callable):
        """이벤트 콜백 추가"""
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)

    def enable_trading(self):
        """매매 활성화"""
        self.is_trading_enabled = True
        self.logger.info("매매 활성화")

    def disable_trading(self):
        """매매 비활성화"""
        self.is_trading_enabled = False
        self.logger.info("매매 비활성화")

    async def update_market_data(self, symbol: str, market_data: MarketData) -> Optional[Signal]:
        """
        시장 데이터 업데이트 및 신호 생성

        Args:
            symbol: 종목 코드
            market_data: 시장 데이터

        Returns:
            생성된 신호 (있는 경우)
        """
        if symbol not in self.strategies:
            return None

        with self.data_lock:
            # 데이터 저장
            self.market_data[symbol] = market_data

            # 포지션 업데이트 (현재가 반영)
            self.position_manager.update_position_price(symbol, market_data.current_price)

            # 전략 실행
            signal = self.strategies[symbol].execute_strategy(market_data)

        if signal:
            await self._process_signal(symbol, signal)

        return signal

    async def _process_signal(self, symbol: str, signal: Signal):
        """신호 처리"""
        try:
            # 이벤트 발생
            await self._emit_event('signal_generated', symbol=symbol, signal=signal)

            # 매매 비활성화 상태 확인
            if not self.is_trading_enabled:
                self.logger.info(f"매매 비활성화 상태 - 신호 무시: {symbol} {signal.signal_type.value}")
                return

            # 리스크 검증
            if not self.risk_manager.validate_signal(symbol, signal, self.market_data.get(symbol)):
                self.logger.warning(f"리스크 검증 실패 - 신호 거부: {symbol} {signal.signal_type.value}")
                return

            # 주문 실행
            await self._execute_signal(symbol, signal)

        except Exception as e:
            self.logger.error(f"신호 처리 오류 [{symbol}]: {e}")

    async def _execute_signal(self, symbol: str, signal: Signal):
        """신호 실행"""
        current_position = self.position_manager.get_position(symbol)

        if signal.signal_type == SignalType.BUY:
            await self._handle_buy_signal(symbol, signal, current_position)
        elif signal.signal_type == SignalType.SELL:
            await self._handle_sell_signal(symbol, signal, current_position)

    async def _handle_buy_signal(self, symbol: str, signal: Signal, current_position: Optional[Position]):
        """매수 신호 처리"""
        # 이미 롱 포지션이 있는 경우 스킵
        if current_position and current_position.position_type == PositionType.LONG:
            self.logger.info(f"이미 롱 포지션 보유 - 매수 신호 무시: {symbol}")
            return

        # 최대 포지션 수 확인
        if len(self.position_manager.get_all_positions()) >= self.max_positions:
            self.logger.warning(f"최대 포지션 수 초과 - 매수 신호 무시: {symbol}")
            return

        # 기존 숏 포지션이 있으면 청산
        if current_position and current_position.position_type == PositionType.SHORT:
            await self._close_position(symbol, "롱 진입을 위한 숏 청산")

        # 매수 주문 생성
        order = self._create_order(symbol, signal, OrderType.MARKET)
        await self._place_order(order)

    async def _handle_sell_signal(self, symbol: str, signal: Signal, current_position: Optional[Position]):
        """매도 신호 처리"""
        # 롱 포지션이 있으면 청산
        if current_position and current_position.position_type == PositionType.LONG:
            await self._close_position(symbol, signal.reason)
            return

        # 포지션이 없고 숏 가능한 경우 숏 진입 (일단 생략)
        self.logger.info(f"포지션 없음 - 매도 신호 무시: {symbol}")

    def _create_order(self, symbol: str, signal: Signal, order_type: OrderType) -> Order:
        """주문 생성"""
        order_id = str(uuid.uuid4())

        order = Order(
            order_id=order_id,
            symbol=symbol,
            order_type=order_type,
            signal_type=signal.signal_type,
            quantity=signal.quantity,
            price=signal.price,
            status=OrderStatus.PENDING,
            created_time=datetime.now()
        )

        return order

    async def _place_order(self, order: Order):
        """주문 실행"""
        try:
            # 주문 등록
            self.pending_orders[order.order_id] = order

            # 이벤트 발생
            await self._emit_event('order_placed', order=order)

            # 실제 주문 실행 (외부 실행기 사용)
            if self.order_executor:
                # 실행 지연
                if self.execution_delay > 0:
                    await asyncio.sleep(self.execution_delay)

                # 주문 실행
                success = await self.order_executor(order.symbol, order)

                if success:
                    await self._on_order_filled(order.order_id, order.price, order.quantity)
                else:
                    await self._on_order_rejected(order.order_id, "주문 실행 실패")
            else:
                # 실행기가 없으면 즉시 체결로 시뮬레이션
                await self._on_order_filled(order.order_id, order.price, order.quantity)

        except Exception as e:
            self.logger.error(f"주문 실행 오류: {e}")
            await self._on_order_rejected(order.order_id, str(e))

    async def _on_order_filled(self, order_id: str, filled_price: float, filled_quantity: int):
        """주문 체결 처리"""
        if order_id not in self.pending_orders:
            return

        order = self.pending_orders[order_id]

        # 주문 상태 업데이트
        order.status = OrderStatus.FILLED
        order.filled_time = datetime.now()
        order.filled_price = filled_price
        order.filled_quantity = filled_quantity

        # 주문 기록
        self.order_history.append(order)
        del self.pending_orders[order_id]

        # 포지션 업데이트
        if order.signal_type == SignalType.BUY:
            self.position_manager.open_position(
                order.symbol,
                PositionType.LONG,
                filled_quantity,
                filled_price,
                order.filled_time
            )
            await self._emit_event('position_opened', symbol=order.symbol, position_type='LONG')

        # 이벤트 발생
        await self._emit_event('order_filled', order=order)

        self.logger.info(f"주문 체결: {order.symbol} {order.signal_type.value} {filled_quantity}주 @ {filled_price:,}원")

    async def _on_order_rejected(self, order_id: str, reason: str):
        """주문 거부 처리"""
        if order_id not in self.pending_orders:
            return

        order = self.pending_orders[order_id]
        order.status = OrderStatus.REJECTED

        # 주문 기록
        self.order_history.append(order)
        del self.pending_orders[order_id]

        self.logger.warning(f"주문 거부: {order.symbol} {order.signal_type.value} - {reason}")

    async def _close_position(self, symbol: str, reason: str):
        """포지션 청산"""
        position = self.position_manager.get_position(symbol)
        if not position:
            return

        # 청산 주문 생성
        market_data = self.market_data.get(symbol)
        current_price = market_data.current_price if market_data else position.current_price

        # 매도 주문 (롱 포지션 청산)
        signal_type = SignalType.SELL
        order = Order(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            order_type=OrderType.MARKET,
            signal_type=signal_type,
            quantity=abs(position.quantity),
            price=current_price,
            status=OrderStatus.PENDING,
            created_time=datetime.now()
        )

        # 주문 실행
        await self._place_order(order)

        # 포지션 청산
        closed_position = self.position_manager.close_position(symbol)
        if closed_position:
            # 손익 계산
            pnl = closed_position.get_unrealized_pnl()

            # 통계 업데이트
            if symbol in self.trading_stats:
                self.trading_stats[symbol].update_stats(pnl)

            await self._emit_event('position_closed', symbol=symbol, pnl=pnl, reason=reason)

            self.logger.info(f"포지션 청산: {symbol} - 손익: {pnl:,.0f}원 ({reason})")

    async def _emit_event(self, event_type: str, **kwargs):
        """이벤트 발생"""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(**kwargs)
                    else:
                        callback(**kwargs)
                except Exception as e:
                    self.logger.error(f"이벤트 콜백 오류 [{event_type}]: {e}")

    def get_positions(self) -> Dict[str, Position]:
        """모든 포지션 조회"""
        return self.position_manager.get_all_positions()

    def get_position(self, symbol: str) -> Optional[Position]:
        """특정 종목 포지션 조회"""
        return self.position_manager.get_position(symbol)

    def get_trading_stats(self, symbol: str = None) -> Dict[str, TradingStats]:
        """거래 통계 조회"""
        if symbol:
            return {symbol: self.trading_stats.get(symbol, TradingStats())}
        return self.trading_stats.copy()

    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Order]:
        """주문 기록 조회"""
        orders = self.order_history[-limit:] if limit else self.order_history

        if symbol:
            orders = [order for order in orders if order.symbol == symbol]

        return orders

    def get_status(self) -> Dict[str, Any]:
        """엔진 상태 조회"""
        return {
            'is_running': self.is_running,
            'is_trading_enabled': self.is_trading_enabled,
            'stock_count': len(self.strategies),
            'position_count': len(self.position_manager.get_all_positions()),
            'pending_orders': len(self.pending_orders),
            'total_orders': len(self.order_history),
            'strategies': {
                symbol: strategy.get_status()
                for symbol, strategy in self.strategies.items()
            }
        }