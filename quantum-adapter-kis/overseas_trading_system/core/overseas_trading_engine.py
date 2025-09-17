"""
해외주식 거래 엔진
환율 관리, 세금 계산, 포지션 관리를 포함한 해외시장 특화 거래 엔진
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict

from overseas_trading_system.core.overseas_data_types import (
    OverseasMarketData, OverseasPosition, OverseasTradingSignal, OverseasOrder,
    ExchangeType, SignalType, PositionType, OrderStatus, TaxInfo, ExchangeRate
)


class OverseasTradingEngine:
    """해외주식 거래 엔진"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger("overseas_trading_engine")

        # 설정값
        self.max_positions = self.config.get('max_positions', 10)
        self.default_quantity = self.config.get('default_quantity', 1)
        self.execution_delay = self.config.get('execution_delay', 0.1)

        # 상태 관리
        self.is_trading_enabled = True
        self.positions: Dict[str, OverseasPosition] = {}
        self.pending_orders: Dict[str, OverseasOrder] = {}
        self.order_history: List[OverseasOrder] = []
        self.strategies: Dict[str, Any] = {}

        # 세금 관리
        self.tax_info = TaxInfo()

        # 이벤트 콜백
        self.event_callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # 통계
        self.trading_stats = {
            'total_orders': 0,
            'successful_orders': 0,
            'failed_orders': 0,
            'total_realized_pnl_usd': 0.0,
            'total_realized_pnl_krw': 0.0,
            'total_tax_paid': 0.0
        }

        # 주문 실행기 (외부에서 설정)
        self.order_executor: Optional[Callable] = None

    def set_order_executor(self, executor: Callable):
        """주문 실행기 설정"""
        self.order_executor = executor

    def add_event_callback(self, event_name: str, callback: Callable):
        """이벤트 콜백 추가"""
        self.event_callbacks[event_name].append(callback)

    async def _emit_event(self, event_name: str, *args, **kwargs):
        """이벤트 발생"""
        for callback in self.event_callbacks[event_name]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"이벤트 콜백 오류 [{event_name}]: {e}")

    def add_stock(self, symbol: str, strategy: Any):
        """종목 및 전략 추가"""
        self.strategies[symbol] = strategy
        self.logger.info(f"종목 추가: {symbol} - {strategy.name}")

    def change_strategy(self, symbol: str, strategy: Any):
        """전략 변경"""
        self.strategies[symbol] = strategy
        self.logger.info(f"전략 변경: {symbol} -> {strategy.name}")

    async def update_market_data(self, symbol: str, market_data: OverseasMarketData) -> Optional[OverseasTradingSignal]:
        """시장 데이터 업데이트 및 신호 생성"""
        try:
            # 포지션 업데이트
            if symbol in self.positions:
                position = self.positions[symbol]
                position.current_price = market_data.current_price
                if market_data.exchange_rate:
                    position.current_rate = market_data.exchange_rate.rate

            # 전략이 등록된 경우 신호 생성
            if symbol in self.strategies:
                strategy = self.strategies[symbol]
                signal = strategy.analyze_signal(market_data)

                if signal and signal.signal_type != SignalType.NONE:
                    self.logger.info(f"신호 생성: {symbol} {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")

                    # 신호 생성 이벤트 발생
                    await self._emit_event('signal_generated', symbol, signal)

                    # 매매 실행 여부 확인
                    if self.is_trading_enabled and self._should_execute_signal(signal):
                        await self._execute_signal(symbol, signal, market_data)

                    return signal

            return None

        except Exception as e:
            self.logger.error(f"시장 데이터 업데이트 오류 [{symbol}]: {e}")
            return None

    def _should_execute_signal(self, signal: OverseasTradingSignal) -> bool:
        """신호 실행 여부 판단"""
        # 신뢰도 체크
        min_confidence = self.config.get('min_confidence', 0.6)
        if signal.confidence < min_confidence:
            return False

        # 포지션 한도 체크
        if signal.signal_type == SignalType.BUY:
            if len(self.positions) >= self.max_positions:
                self.logger.warning(f"최대 포지션 한도 초과: {len(self.positions)}/{self.max_positions}")
                return False

        # 기존 포지션 체크
        if signal.symbol in self.positions:
            position = self.positions[signal.symbol]
            if signal.signal_type == SignalType.BUY and position.position_type == PositionType.LONG:
                return False  # 이미 매수 포지션 보유
            if signal.signal_type == SignalType.SELL and position.position_type != PositionType.LONG:
                return False  # 매도할 포지션 없음

        return True

    async def _execute_signal(self, symbol: str, signal: OverseasTradingSignal, market_data: OverseasMarketData):
        """신호 실행"""
        try:
            # 주문 생성
            order_id = f"ORD_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            order = OverseasOrder(
                order_id=order_id,
                symbol=symbol,
                exchange=signal.exchange,
                signal_type=signal.signal_type,
                quantity=signal.quantity,
                price=signal.price,
                order_rate=market_data.exchange_rate.rate if market_data.exchange_rate else 1300.0
            )

            self.pending_orders[order_id] = order
            self.trading_stats['total_orders'] += 1

            # 주문 생성 이벤트 발생
            await self._emit_event('order_placed', order)

            # 주문 실행기 호출
            if self.order_executor:
                success = await self.order_executor(symbol, order)

                if success:
                    # 주문 체결 처리
                    await self._handle_order_filled(order)
                else:
                    # 주문 실패 처리
                    await self._handle_order_failed(order)
            else:
                self.logger.warning(f"주문 실행기가 설정되지 않음: {order_id}")

        except Exception as e:
            self.logger.error(f"신호 실행 오류 [{symbol}]: {e}")

    async def _handle_order_filled(self, order: OverseasOrder):
        """주문 체결 처리"""
        try:
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.filled_price = order.price
            order.filled_rate = order.order_rate
            order.filled_time = datetime.now()

            # 통계 업데이트
            self.trading_stats['successful_orders'] += 1

            # 포지션 업데이트
            if order.signal_type == SignalType.BUY:
                await self._open_position(order)
            elif order.signal_type == SignalType.SELL:
                await self._close_position(order)

            # 주문 이력에 추가
            self.order_history.append(order)
            del self.pending_orders[order.order_id]

            # 주문 체결 이벤트 발생
            await self._emit_event('order_filled', order)

            self.logger.info(f"주문 체결: {order.symbol} {order.signal_type.value} {order.filled_quantity}주 @ ${order.filled_price:.2f}")

        except Exception as e:
            self.logger.error(f"주문 체결 처리 오류: {e}")

    async def _handle_order_failed(self, order: OverseasOrder):
        """주문 실패 처리"""
        order.status = OrderStatus.REJECTED
        self.trading_stats['failed_orders'] += 1

        # 주문 이력에 추가
        self.order_history.append(order)
        del self.pending_orders[order.order_id]

        self.logger.warning(f"주문 실패: {order.symbol} {order.signal_type.value}")

    async def _open_position(self, order: OverseasOrder):
        """포지션 오픈"""
        try:
            position = OverseasPosition(
                symbol=order.symbol,
                exchange=order.exchange,
                position_type=PositionType.LONG,
                quantity=order.filled_quantity,
                entry_price=order.filled_price,
                entry_rate=order.filled_rate,
                current_price=order.filled_price,
                current_rate=order.filled_rate
            )

            self.positions[order.symbol] = position

            # 포지션 오픈 이벤트 발생
            await self._emit_event('position_opened', order.symbol, position.position_type.value)

            self.logger.info(f"포지션 오픈: {order.symbol} LONG {order.filled_quantity}주 @ ${order.filled_price:.2f}")

        except Exception as e:
            self.logger.error(f"포지션 오픈 오류: {e}")

    async def _close_position(self, order: OverseasOrder):
        """포지션 클로즈"""
        try:
            if order.symbol not in self.positions:
                self.logger.warning(f"클로즈할 포지션 없음: {order.symbol}")
                return

            position = self.positions[order.symbol]

            # 손익 계산
            realized_pnl_usd = position.get_unrealized_pnl_usd()
            realized_pnl_krw = realized_pnl_usd * order.filled_rate

            # 세금 계산
            if realized_pnl_krw > 0:
                tax_calc = self.tax_info.calculate_tax(realized_pnl_krw)
                tax_amount = tax_calc['total_tax']
                self.trading_stats['total_tax_paid'] += tax_amount
                net_pnl_krw = realized_pnl_krw - tax_amount
            else:
                tax_amount = 0.0
                net_pnl_krw = realized_pnl_krw

            # 통계 업데이트
            self.trading_stats['total_realized_pnl_usd'] += realized_pnl_usd
            self.trading_stats['total_realized_pnl_krw'] += net_pnl_krw

            # 포지션 제거
            del self.positions[order.symbol]

            # 포지션 클로즈 이벤트 발생
            reason = f"신호에 의한 매도 (세전 손익: ₩{realized_pnl_krw:+,.0f}, 세금: ₩{tax_amount:,.0f})"
            await self._emit_event('position_closed', order.symbol, net_pnl_krw, reason)

            self.logger.info(f"포지션 클로즈: {order.symbol} 손익: ${realized_pnl_usd:+.2f} (₩{net_pnl_krw:+,.0f})")

        except Exception as e:
            self.logger.error(f"포지션 클로즈 오류: {e}")

    def get_position(self, symbol: str) -> Optional[OverseasPosition]:
        """포지션 조회"""
        return self.positions.get(symbol)

    def get_positions(self) -> Dict[str, OverseasPosition]:
        """전체 포지션 조회"""
        return self.positions.copy()

    def get_total_portfolio_value_usd(self) -> float:
        """전체 포트폴리오 가치 (USD)"""
        return sum(pos.get_market_value_usd() for pos in self.positions.values())

    def get_total_portfolio_value_krw(self) -> float:
        """전체 포트폴리오 가치 (KRW)"""
        return sum(pos.get_market_value_krw() for pos in self.positions.values())

    def get_total_unrealized_pnl_usd(self) -> float:
        """전체 미실현 손익 (USD)"""
        return sum(pos.get_unrealized_pnl_usd() for pos in self.positions.values())

    def get_total_unrealized_pnl_krw(self) -> float:
        """전체 미실현 손익 (KRW)"""
        return sum(pos.get_unrealized_pnl_krw() for pos in self.positions.values())

    def get_currency_impact(self) -> float:
        """환율 변동 영향 (KRW)"""
        return sum(pos.get_currency_impact() for pos in self.positions.values())

    def enable_trading(self):
        """매매 활성화"""
        self.is_trading_enabled = True
        self.logger.info("매매 활성화")

    def disable_trading(self):
        """매매 비활성화"""
        self.is_trading_enabled = False
        self.logger.info("매매 비활성화")

    def get_status(self) -> Dict[str, Any]:
        """엔진 상태 조회"""
        return {
            'is_trading_enabled': self.is_trading_enabled,
            'stock_count': len(self.strategies),
            'position_count': len(self.positions),
            'pending_orders': len(self.pending_orders),
            'total_orders': self.trading_stats['total_orders'],
            'portfolio_value_usd': self.get_total_portfolio_value_usd(),
            'portfolio_value_krw': self.get_total_portfolio_value_krw(),
            'unrealized_pnl_usd': self.get_total_unrealized_pnl_usd(),
            'unrealized_pnl_krw': self.get_total_unrealized_pnl_krw(),
            'currency_impact': self.get_currency_impact(),
            'realized_pnl_usd': self.trading_stats['total_realized_pnl_usd'],
            'realized_pnl_krw': self.trading_stats['total_realized_pnl_krw'],
            'total_tax_paid': self.trading_stats['total_tax_paid']
        }

    def get_trading_stats(self) -> Dict[str, Any]:
        """거래 통계 조회"""
        total_orders = self.trading_stats['total_orders']
        success_rate = (self.trading_stats['successful_orders'] / total_orders * 100) if total_orders > 0 else 0

        return {
            'total_orders': total_orders,
            'successful_orders': self.trading_stats['successful_orders'],
            'failed_orders': self.trading_stats['failed_orders'],
            'success_rate': success_rate,
            'total_realized_pnl_usd': self.trading_stats['total_realized_pnl_usd'],
            'total_realized_pnl_krw': self.trading_stats['total_realized_pnl_krw'],
            'total_tax_paid': self.trading_stats['total_tax_paid'],
            'net_realized_pnl_krw': self.trading_stats['total_realized_pnl_krw']
        }

    def calculate_position_sizing(self, signal: OverseasTradingSignal, available_cash_usd: float) -> int:
        """포지션 크기 계산"""
        try:
            # 기본 수량
            base_quantity = self.default_quantity

            # 신뢰도 기반 조정
            confidence_multiplier = min(2.0, signal.confidence * 2)
            adjusted_quantity = int(base_quantity * confidence_multiplier)

            # 사용 가능 현금 기반 제한
            max_affordable = int(available_cash_usd / signal.price) if signal.price > 0 else 0
            final_quantity = min(adjusted_quantity, max_affordable)

            return max(1, final_quantity)  # 최소 1주

        except Exception as e:
            self.logger.error(f"포지션 크기 계산 오류: {e}")
            return 1