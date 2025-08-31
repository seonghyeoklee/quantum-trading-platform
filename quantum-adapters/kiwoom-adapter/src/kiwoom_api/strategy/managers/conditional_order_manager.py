"""
조건부 매매 주문 관리자

사용자가 설정한 조건부 매매 주문들을 모니터링하고 실행하는 시스템
"""

import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from decimal import Decimal

# Handle both relative and absolute imports for different execution contexts
try:
    from ..models.conditional_order import (
        ConditionalOrder, ConditionalOrderRequest, OrderStatus, 
        ConditionType, OrderAction
    )
    from ..engines.base_strategy import BaseStrategy
    from ...analysis.indicators.technical import calculate_rsi, calculate_sma
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.models.conditional_order import (
        ConditionalOrder, ConditionalOrderRequest, OrderStatus, 
        ConditionType, OrderAction
    )
    from kiwoom_api.strategy.engines.base_strategy import BaseStrategy
    from kiwoom_api.analysis.indicators.technical import calculate_rsi, calculate_sma


class ConditionalOrderManager:
    """조건부 매매 주문 관리자"""
    
    def __init__(self):
        self.orders: Dict[str, ConditionalOrder] = {}  # order_id -> ConditionalOrder
        self.user_orders: Dict[str, List[str]] = {}    # user_id -> [order_ids]
        self.symbol_orders: Dict[str, List[str]] = {}  # symbol -> [order_ids]
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        print("🔄 조건부 매매 주문 관리자 초기화됨")
    
    async def create_order(self, request: ConditionalOrderRequest) -> ConditionalOrder:
        """조건부 매매 주문 생성"""
        order_id = str(uuid.uuid4())
        
        # 유효 기간 설정
        valid_until = None
        if request.valid_hours and request.valid_hours > 0:
            valid_until = datetime.now() + timedelta(hours=request.valid_hours)
        
        # 조건부 주문 생성
        order = ConditionalOrder(
            order_id=order_id,
            user_id=request.user_id,
            symbol=request.symbol,
            condition_type=request.condition_type,
            condition_value=request.condition_value,
            condition_value2=request.condition_value2,
            action=request.action,
            quantity=request.quantity,
            amount=request.amount,
            percentage=request.percentage,
            valid_until=valid_until,
            dry_run=request.dry_run,
            memo=request.memo
        )
        
        # 주문 등록
        self.orders[order_id] = order
        
        # 사용자별 주문 목록에 추가
        if request.user_id not in self.user_orders:
            self.user_orders[request.user_id] = []
        self.user_orders[request.user_id].append(order_id)
        
        # 종목별 주문 목록에 추가
        if request.symbol not in self.symbol_orders:
            self.symbol_orders[request.symbol] = []
        self.symbol_orders[request.symbol].append(order_id)
        
        print(f"✅ 조건부 주문 생성: {order_id} - {order.get_condition_description()} → {order.get_action_description()}")
        
        # 모니터링 시작 (아직 시작되지 않은 경우)
        if not self.monitoring_active:
            await self.start_monitoring()
        
        return order
    
    async def cancel_order(self, order_id: str, user_id: str) -> bool:
        """조건부 매매 주문 취소"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.user_id != user_id:
            return False  # 본인 주문만 취소 가능
        
        if order.status not in [OrderStatus.ACTIVE]:
            return False  # 활성 주문만 취소 가능
        
        order.status = OrderStatus.CANCELLED
        print(f"❌ 조건부 주문 취소: {order_id}")
        
        return True
    
    def get_user_orders(self, user_id: str) -> List[ConditionalOrder]:
        """사용자의 조건부 매매 주문 목록 조회"""
        order_ids = self.user_orders.get(user_id, [])
        return [self.orders[order_id] for order_id in order_ids if order_id in self.orders]
    
    def get_active_orders(self) -> List[ConditionalOrder]:
        """활성 조건부 매매 주문 목록 조회"""
        return [order for order in self.orders.values() if order.status == OrderStatus.ACTIVE]
    
    def get_order_by_id(self, order_id: str) -> Optional[ConditionalOrder]:
        """주문 ID로 조건부 매매 주문 조회"""
        return self.orders.get(order_id)
    
    async def start_monitoring(self):
        """조건부 매매 모니터링 시작"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        print("🚀 조건부 매매 모니터링 시작됨")
    
    async def stop_monitoring(self):
        """조건부 매매 모니터링 중지"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        print("🛑 조건부 매매 모니터링 중지됨")
    
    async def _monitoring_loop(self):
        """조건부 매매 모니터링 루프"""
        print("🔍 조건부 매매 모니터링 루프 시작")
        
        while self.monitoring_active:
            try:
                active_orders = self.get_active_orders()
                if not active_orders:
                    await asyncio.sleep(30)  # 활성 주문이 없으면 30초 대기
                    continue
                
                # 종목별로 그룹화하여 효율적으로 데이터 조회
                symbols = list(set(order.symbol for order in active_orders))
                
                for symbol in symbols:
                    symbol_orders = [order for order in active_orders if order.symbol == symbol]
                    if not symbol_orders:
                        continue
                    
                    # 해당 종목의 현재 데이터 수집
                    current_data = await self._get_symbol_data(symbol)
                    if not current_data:
                        continue
                    
                    # 각 주문의 조건 확인
                    for order in symbol_orders:
                        if not order.is_valid():
                            # 유효하지 않은 주문 처리
                            if order.valid_until and datetime.now() > order.valid_until:
                                order.status = OrderStatus.CANCELLED
                                print(f"⏰ 조건부 주문 만료: {order.order_id}")
                            continue
                        
                        # 조건 확인
                        if order.check_condition(current_data):
                            await self._execute_order(order, current_data)
                
                # 모니터링 간격 (10초)
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"❌ 조건부 매매 모니터링 오류: {e}")
                await asyncio.sleep(30)  # 오류 발생 시 30초 대기
    
    async def _get_symbol_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """종목의 현재 데이터 수집"""
        try:
            # BaseStrategy를 이용해서 차트 데이터 가져오기
            # 임시 설정으로 BaseStrategy 생성
            from ...strategy.models.strategy_config import StrategyConfig, StrategyType, RiskLevel
            
            temp_config = StrategyConfig(
                strategy_name="temp_conditional_order",
                strategy_type=StrategyType.RSI_MEAN_REVERSION,
                target_symbols=[symbol],
                risk_level=RiskLevel.MODERATE,
                max_position_size=Decimal("1000000"),
                execution_interval=60
            )
            
            base_strategy = BaseStrategy(temp_config)
            chart_data = await base_strategy.get_chart_data(symbol, days=30)
            
            if not chart_data or not chart_data.get("prices"):
                return None
            
            prices = chart_data["prices"]
            volumes = chart_data.get("volumes", [])
            
            # 현재가
            current_price = prices[-1]
            
            # RSI 계산 (14일)
            rsi = None
            if len(prices) >= 15:
                try:
                    rsi = calculate_rsi(prices, period=14)
                except:
                    pass
            
            # 이동평균 계산 (단기 5일, 장기 20일)
            short_ma = None
            long_ma = None
            prev_short_ma = None
            prev_long_ma = None
            
            if len(prices) >= 20:
                try:
                    short_ma = calculate_sma(prices, period=5)
                    long_ma = calculate_sma(prices, period=20)
                    
                    # 이전 시점의 이동평균 (교차 확인용)
                    if len(prices) >= 21:
                        prev_short_ma = calculate_sma(prices[:-1], period=5)
                        prev_long_ma = calculate_sma(prices[:-1], period=20)
                except:
                    pass
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "rsi": rsi,
                "short_ma": short_ma,
                "long_ma": long_ma,
                "prev_short_ma": prev_short_ma,
                "prev_long_ma": prev_long_ma,
                "prices": prices,
                "volumes": volumes,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            print(f"❌ {symbol} 데이터 수집 실패: {e}")
            return None
    
    async def _execute_order(self, order: ConditionalOrder, current_data: Dict[str, Any]):
        """조건 만족 시 주문 실행"""
        try:
            current_price = current_data["current_price"]
            
            # 주문 상태 업데이트
            order.status = OrderStatus.TRIGGERED
            order.triggered_at = datetime.now()
            
            print(f"🎯 조건 만족! 주문 실행: {order.order_id}")
            print(f"   조건: {order.get_condition_description()}")
            print(f"   실행: {order.get_action_description()}")
            print(f"   현재가: {current_price:,}원")
            
            # 실제 주문 실행 (현재는 모의투자로 시뮬레이션)
            execution_result = await self._simulate_order_execution(order, current_price)
            
            # 실행 결과 저장
            order.executed_price = Decimal(str(current_price))
            order.executed_quantity = execution_result.get("quantity", 0)
            order.execution_details = execution_result
            order.status = OrderStatus.COMPLETED
            order.completed_at = datetime.now()
            
            print(f"✅ 주문 실행 완료: {order.order_id}")
            print(f"   체결가: {order.executed_price:,}원")
            print(f"   체결수량: {order.executed_quantity:,}주")
            
        except Exception as e:
            print(f"❌ 주문 실행 실패: {order.order_id}, 오류: {e}")
            order.status = OrderStatus.ERROR
            order.execution_details = {"error": str(e)}
    
    async def _simulate_order_execution(self, order: ConditionalOrder, current_price: float) -> Dict[str, Any]:
        """주문 실행 시뮬레이션 (모의투자)"""
        # 실제 키움증권 API 호출은 여기서 구현
        # 현재는 모의투자 시뮬레이션만 구현
        
        if order.action in [OrderAction.BUY, OrderAction.SELL]:
            if order.quantity:
                # 수량 지정 주문
                quantity = order.quantity
                total_amount = quantity * current_price
            elif order.amount:
                # 금액 지정 주문
                quantity = int(order.amount / current_price)
                total_amount = order.amount
            else:
                # 기본값 설정
                quantity = 1
                total_amount = current_price
            
            return {
                "order_type": order.action.value,
                "symbol": order.symbol,
                "quantity": quantity,
                "price": current_price,
                "total_amount": total_amount,
                "execution_time": datetime.now(),
                "simulated": order.dry_run
            }
        
        elif order.action in [OrderAction.BUY_PERCENT, OrderAction.SELL_PERCENT]:
            # 퍼센트 주문은 실제 계좌 잔고 정보가 필요
            # 현재는 임시로 시뮬레이션
            percentage = order.percentage or 10.0
            
            return {
                "order_type": order.action.value,
                "symbol": order.symbol,
                "percentage": percentage,
                "price": current_price,
                "execution_time": datetime.now(),
                "simulated": order.dry_run
            }
        
        return {"error": "Unknown order action"}
    
    def get_statistics(self) -> Dict[str, Any]:
        """조건부 매매 통계 정보"""
        total_orders = len(self.orders)
        active_orders = len([o for o in self.orders.values() if o.status == OrderStatus.ACTIVE])
        completed_orders = len([o for o in self.orders.values() if o.status == OrderStatus.COMPLETED])
        cancelled_orders = len([o for o in self.orders.values() if o.status == OrderStatus.CANCELLED])
        error_orders = len([o for o in self.orders.values() if o.status == OrderStatus.ERROR])
        
        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "error_orders": error_orders,
            "monitoring_active": self.monitoring_active,
            "unique_symbols": len(self.symbol_orders),
            "unique_users": len(self.user_orders)
        }


# 전역 조건부 매매 관리자 인스턴스
conditional_order_manager = ConditionalOrderManager()