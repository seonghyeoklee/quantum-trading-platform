"""
주문 실행 서비스

KIS API를 통한 실제 주문 실행, 주문 상태 관리, 포지션 관리를 담당합니다.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..models import (
    TradingSignal, Order, Position, OrderRequest, OrderSide, 
    OrderType, OrderStatus, SignalType
)
from ..config import settings
# from ..utils.kis_client import KISClient

@dataclass
class OrderExecution:
    """주문 실행 결과"""
    success: bool
    order_id: Optional[str]
    error_message: Optional[str]
    executed_price: Optional[float]
    executed_quantity: Optional[int]

class OrderExecutor:
    """주문 실행 메인 클래스"""
    
    def __init__(self):
        self.active_orders = {}  # 활성 주문 관리
        self.positions = {}  # 포지션 관리
        self.order_history = []  # 주문 히스토리
        
        # TODO: KIS API 클라이언트 초기화
        # self.kis_client = KISClient()
        
        # 주문 모니터링 상태
        self.is_monitoring = False
        
    async def start_order_monitoring(self):
        """주문 모니터링 시작"""
        
        if self.is_monitoring:
            return
            
        print("📋 주문 모니터링 시작...")
        self.is_monitoring = True
        
        try:
            # 주문 상태 모니터링 태스크 시작
            asyncio.create_task(self._order_status_monitoring_loop())
            asyncio.create_task(self._position_monitoring_loop())
            
            print("✅ 주문 모니터링 시작 완료")
            
        except Exception as e:
            print(f"❌ 주문 모니터링 시작 실패: {e}")
            self.is_monitoring = False
            raise
    
    async def stop_order_monitoring(self):
        """주문 모니터링 중지"""
        
        print("🛑 주문 모니터링 중지...")
        self.is_monitoring = False
        print("✅ 주문 모니터링 중지 완료")
    
    async def process_signal(self, signal: TradingSignal, quantity: int) -> Optional[OrderExecution]:
        """매매 신호 처리 및 주문 실행"""
        
        try:
            print(f"🎯 매매 신호 처리 시작: {signal.symbol} {signal.signal_type} {quantity}주")
            
            # 신호 유형에 따른 주문 생성
            if signal.signal_type == SignalType.BUY:
                order_request = OrderRequest(
                    symbol=signal.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,  # 시장가 주문
                    quantity=quantity
                )
            elif signal.signal_type == SignalType.SELL:
                order_request = OrderRequest(
                    symbol=signal.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=quantity
                )
            else:
                print(f"⚠️ HOLD 신호는 주문 실행하지 않음: {signal.symbol}")
                return None
            
            # 주문 실행
            execution_result = await self.execute_order(order_request)
            
            # 성공 시 손절/익절 주문 설정
            if execution_result.success and signal.signal_type == SignalType.BUY:
                await self._setup_stop_loss_take_profit(
                    signal.symbol, 
                    quantity, 
                    signal.stop_loss_price, 
                    signal.target_price
                )
            
            return execution_result
            
        except Exception as e:
            print(f"❌ 매매 신호 처리 실패: {e}")
            return OrderExecution(
                success=False,
                order_id=None,
                error_message=str(e),
                executed_price=None,
                executed_quantity=None
            )
    
    async def execute_order(self, order_request: OrderRequest) -> OrderExecution:
        """주문 실행"""
        
        try:
            print(f"📤 주문 실행: {order_request.symbol} {order_request.side} {order_request.quantity}주")
            
            # 주문 ID 생성
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 주문 객체 생성
            order = Order(
                order_id=order_id,
                symbol=order_request.symbol,
                side=order_request.side,
                order_type=order_request.order_type,
                quantity=order_request.quantity,
                price=order_request.price,
                status=OrderStatus.PENDING,
                filled_quantity=0,
                remaining_quantity=order_request.quantity,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # TODO: KIS API로 실제 주문 전송
            # kis_order_result = await self.kis_client.place_order(order_request)
            # if not kis_order_result.success:
            #     return OrderExecution(
            #         success=False,
            #         order_id=order_id,
            #         error_message=kis_order_result.error_message,
            #         executed_price=None,
            #         executed_quantity=None
            #     )
            
            # 임시로 성공 처리 (실제로는 KIS API 응답 처리)
            await asyncio.sleep(0.1)  # API 호출 시뮬레이션
            
            # 시장가 주문이므로 즉시 체결 시뮬레이션
            executed_price = 75000.0  # 임시 체결가
            executed_quantity = order_request.quantity
            
            # 주문 상태 업데이트
            order.status = OrderStatus.FILLED
            order.filled_quantity = executed_quantity
            order.remaining_quantity = 0
            order.avg_fill_price = executed_price
            order.filled_at = datetime.now()
            order.updated_at = datetime.now()
            
            # 활성 주문에 추가 (체결되었지만 기록용)
            self.active_orders[order_id] = order
            self.order_history.append(order)
            
            # 포지션 업데이트
            await self._update_position(order)
            
            print(f"✅ 주문 체결 완료: {order_id} {executed_quantity}주 @ {executed_price:,.0f}원")
            
            return OrderExecution(
                success=True,
                order_id=order_id,
                error_message=None,
                executed_price=executed_price,
                executed_quantity=executed_quantity
            )
            
        except Exception as e:
            print(f"❌ 주문 실행 실패: {e}")
            return OrderExecution(
                success=False,
                order_id=None,
                error_message=str(e),
                executed_price=None,
                executed_quantity=None
            )
    
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        
        try:
            if order_id not in self.active_orders:
                print(f"⚠️ 주문을 찾을 수 없음: {order_id}")
                return False
            
            order = self.active_orders[order_id]
            
            if order.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
                print(f"⚠️ 취소할 수 없는 주문 상태: {order.status}")
                return False
            
            # TODO: KIS API로 주문 취소 요청
            # cancel_result = await self.kis_client.cancel_order(order_id)
            # if not cancel_result.success:
            #     return False
            
            # 주문 상태 업데이트
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            
            print(f"✅ 주문 취소 완료: {order_id}")
            return True
            
        except Exception as e:
            print(f"❌ 주문 취소 실패: {e}")
            return False
    
    async def _update_position(self, order: Order):
        """포지션 업데이트"""
        
        try:
            symbol = order.symbol
            
            if symbol not in self.positions:
                # 새 포지션 생성
                if order.side == OrderSide.BUY:
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=order.filled_quantity,
                        avg_price=order.avg_fill_price,
                        current_price=order.avg_fill_price,
                        unrealized_pnl=0.0,
                        unrealized_pnl_percent=0.0,
                        opened_at=order.filled_at,
                        updated_at=datetime.now()
                    )
                    print(f"📈 새 포지션 생성: {symbol} {order.filled_quantity}주 @ {order.avg_fill_price:,.0f}원")
            else:
                # 기존 포지션 업데이트
                position = self.positions[symbol]
                
                if order.side == OrderSide.BUY:
                    # 매수 - 포지션 증가
                    total_cost = (position.quantity * position.avg_price) + (order.filled_quantity * order.avg_fill_price)
                    total_quantity = position.quantity + order.filled_quantity
                    
                    position.avg_price = total_cost / total_quantity
                    position.quantity = total_quantity
                    
                elif order.side == OrderSide.SELL:
                    # 매도 - 포지션 감소
                    position.quantity -= order.filled_quantity
                    
                    # 포지션이 0이 되면 제거
                    if position.quantity <= 0:
                        del self.positions[symbol]
                        print(f"📉 포지션 청산 완료: {symbol}")
                        return
                
                position.updated_at = datetime.now()
                print(f"🔄 포지션 업데이트: {symbol} {position.quantity}주 @ {position.avg_price:,.0f}원")
            
        except Exception as e:
            print(f"❌ 포지션 업데이트 실패: {e}")
    
    async def _setup_stop_loss_take_profit(self, symbol: str, quantity: int, 
                                         stop_loss_price: Optional[float], 
                                         take_profit_price: Optional[float]):
        """손절/익절 주문 설정"""
        
        try:
            if stop_loss_price:
                # 손절 주문 생성
                stop_loss_request = OrderRequest(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.STOP_LOSS,
                    quantity=quantity,
                    price=stop_loss_price
                )
                
                # TODO: 실제로는 조건부 주문으로 등록
                print(f"🛡️ 손절 주문 설정: {symbol} {quantity}주 @ {stop_loss_price:,.0f}원")
            
            if take_profit_price:
                # 익절 주문 생성
                take_profit_request = OrderRequest(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.TAKE_PROFIT,
                    quantity=quantity,
                    price=take_profit_price
                )
                
                # TODO: 실제로는 조건부 주문으로 등록
                print(f"🎯 익절 주문 설정: {symbol} {quantity}주 @ {take_profit_price:,.0f}원")
                
        except Exception as e:
            print(f"❌ 손절/익절 주문 설정 실패: {e}")
    
    async def _order_status_monitoring_loop(self):
        """주문 상태 모니터링 루프"""
        
        while self.is_monitoring:
            try:
                # 대기 중인 주문들의 상태 확인
                pending_orders = [
                    order for order in self.active_orders.values() 
                    if order.status == OrderStatus.PENDING
                ]
                
                for order in pending_orders:
                    # TODO: KIS API에서 주문 상태 조회
                    # order_status = await self.kis_client.get_order_status(order.order_id)
                    # await self._update_order_status(order, order_status)
                    pass
                
                await asyncio.sleep(5)  # 5초마다 체크
                
            except Exception as e:
                print(f"❌ 주문 상태 모니터링 오류: {e}")
                await asyncio.sleep(10)
    
    async def _position_monitoring_loop(self):
        """포지션 모니터링 루프"""
        
        while self.is_monitoring:
            try:
                # 포지션별 현재가 업데이트 및 손익 계산
                for symbol, position in self.positions.items():
                    # TODO: 현재가 조회
                    # current_price = await self.get_current_price(symbol)
                    current_price = 75500.0  # 임시값
                    
                    # 손익 계산
                    position.current_price = current_price
                    position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
                    position.unrealized_pnl_percent = (current_price - position.avg_price) / position.avg_price * 100
                    position.updated_at = datetime.now()
                    
                    # 손절/익절 조건 체크
                    await self._check_stop_loss_take_profit(position)
                
                await asyncio.sleep(10)  # 10초마다 체크
                
            except Exception as e:
                print(f"❌ 포지션 모니터링 오류: {e}")
                await asyncio.sleep(30)
    
    async def _check_stop_loss_take_profit(self, position: Position):
        """손절/익절 조건 체크"""
        
        try:
            # 손절 체크 (2% 손실)
            loss_percent = (position.current_price - position.avg_price) / position.avg_price * 100
            if loss_percent <= -settings.stop_loss_percent:
                print(f"🛡️ 손절 조건 도달: {position.symbol} {loss_percent:.2f}%")
                await self._execute_stop_loss(position)
                return
            
            # 익절 체크 (4% 수익)
            if loss_percent >= settings.take_profit_percent:
                print(f"🎯 익절 조건 도달: {position.symbol} {loss_percent:.2f}%")
                await self._execute_take_profit(position)
                return
                
        except Exception as e:
            print(f"❌ 손절/익절 조건 체크 실패: {e}")
    
    async def _execute_stop_loss(self, position: Position):
        """손절 실행"""
        
        try:
            stop_loss_request = OrderRequest(
                symbol=position.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=position.quantity
            )
            
            result = await self.execute_order(stop_loss_request)
            if result.success:
                print(f"🛡️ 손절 실행 완료: {position.symbol}")
            
        except Exception as e:
            print(f"❌ 손절 실행 실패: {e}")
    
    async def _execute_take_profit(self, position: Position):
        """익절 실행"""
        
        try:
            take_profit_request = OrderRequest(
                symbol=position.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=position.quantity
            )
            
            result = await self.execute_order(take_profit_request)
            if result.success:
                print(f"🎯 익절 실행 완료: {position.symbol}")
            
        except Exception as e:
            print(f"❌ 익절 실행 실패: {e}")
    
    async def get_active_orders(self) -> List[Order]:
        """활성 주문 조회"""
        
        return list(self.active_orders.values())
    
    async def get_positions(self) -> List[Position]:
        """현재 포지션 조회"""
        
        return list(self.positions.values())
    
    async def get_order_history(self, limit: int = 100) -> List[Order]:
        """주문 히스토리 조회"""
        
        return self.order_history[-limit:]
    
    async def close_position(self, symbol: str) -> bool:
        """포지션 강제 청산"""
        
        try:
            if symbol not in self.positions:
                print(f"⚠️ 포지션을 찾을 수 없음: {symbol}")
                return False
            
            position = self.positions[symbol]
            
            close_request = OrderRequest(
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=position.quantity
            )
            
            result = await self.execute_order(close_request)
            
            if result.success:
                print(f"📉 포지션 강제 청산 완료: {symbol}")
                return True
            else:
                print(f"❌ 포지션 청산 실패: {symbol}")
                return False
                
        except Exception as e:
            print(f"❌ 포지션 청산 실패: {e}")
            return False
    
    async def cancel_all_orders(self) -> int:
        """모든 대기 주문 취소"""
        
        cancelled_count = 0
        
        try:
            pending_orders = [
                order for order in self.active_orders.values() 
                if order.status == OrderStatus.PENDING
            ]
            
            for order in pending_orders:
                if await self.cancel_order(order.order_id):
                    cancelled_count += 1
            
            print(f"📋 전체 주문 취소 완료: {cancelled_count}개")
            return cancelled_count
            
        except Exception as e:
            print(f"❌ 전체 주문 취소 실패: {e}")
            return cancelled_count
    
    async def health_check(self) -> bool:
        """주문 실행기 상태 확인"""
        
        try:
            # 모니터링 상태 확인
            if not self.is_monitoring:
                return False
            
            # TODO: KIS API 연결 상태 확인
            # kis_connection = await self.kis_client.check_connection()
            # if not kis_connection:
            #     return False
            
            # 최근 주문 처리 확인 (선택적)
            recent_orders = [
                order for order in self.order_history 
                if (datetime.now() - order.created_at).seconds < 3600  # 1시간 내
            ]
            
            # 정상 동작 중이면 True (주문이 없어도 정상)
            return True
            
        except Exception as e:
            print(f"❌ 주문 실행기 헬스체크 실패: {e}")
            return False
