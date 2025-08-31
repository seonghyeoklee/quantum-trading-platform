"""
조건부 매매 API 엔드포인트

사용자가 조건부 매매 주문을 생성, 관리할 수 있는 API
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Handle both relative and absolute imports for different execution contexts
try:
    from ..strategy.models.conditional_order import (
        ConditionalOrder, ConditionalOrderRequest, ConditionalOrderResponse,
        OrderStatus, ConditionType, OrderAction
    )
    from ..strategy.managers.conditional_order_manager import conditional_order_manager
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.strategy.models.conditional_order import (
        ConditionalOrder, ConditionalOrderRequest, ConditionalOrderResponse,
        OrderStatus, ConditionType, OrderAction
    )
    from kiwoom_api.strategy.managers.conditional_order_manager import conditional_order_manager

router = APIRouter(prefix="/api/v1/conditional", tags=["Conditional Trading"])


# === 요청/응답 모델들 ===

class QuickOrderRequest(BaseModel):
    """간단 조건부 주문 요청 (가격 조건만)"""
    user_id: str
    symbol: str
    buy_price: Optional[Decimal] = None    # 매수가
    sell_price: Optional[Decimal] = None   # 매도가
    quantity: Optional[int] = None         # 수량
    amount: Optional[Decimal] = None       # 금액
    valid_hours: int = 24                  # 유효 시간
    dry_run: bool = True                   # 모의투자


class OrderListResponse(BaseModel):
    """주문 목록 응답"""
    orders: List[ConditionalOrder]
    total_count: int
    active_count: int


class StatisticsResponse(BaseModel):
    """통계 응답"""
    total_orders: int
    active_orders: int
    completed_orders: int
    cancelled_orders: int
    error_orders: int
    monitoring_active: bool
    unique_symbols: int
    unique_users: int


# === API 엔드포인트들 ===

@router.post("/order", response_model=ConditionalOrderResponse)
async def create_conditional_order(request: ConditionalOrderRequest):
    """
    조건부 매매 주문 생성
    
    사용자가 설정한 조건에 따라 자동으로 매수/매도를 실행하는 주문을 생성합니다.
    """
    try:
        order = await conditional_order_manager.create_order(request)
        
        return ConditionalOrderResponse(
            order_id=order.order_id,
            message="조건부 주문이 생성되었습니다.",
            condition_description=order.get_condition_description(),
            action_description=order.get_action_description(),
            status=order.status,
            created_at=order.created_at,
            valid_until=order.valid_until
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"조건부 주문 생성 실패: {str(e)}")


@router.post("/quick-order", response_model=List[ConditionalOrderResponse])
async def create_quick_order(request: QuickOrderRequest):
    """
    간단 조건부 주문 생성 (가격 조건)
    
    매수가/매도가를 간단히 설정하여 조건부 주문을 생성합니다.
    """
    try:
        created_orders = []
        
        # 매수 조건 생성
        if request.buy_price:
            buy_request = ConditionalOrderRequest(
                user_id=request.user_id,
                symbol=request.symbol,
                condition_type=ConditionType.PRICE_BELOW,
                condition_value=request.buy_price,
                action=OrderAction.BUY,
                quantity=request.quantity,
                amount=request.amount,
                valid_hours=request.valid_hours,
                dry_run=request.dry_run,
                memo=f"간단 주문 - 매수가 {request.buy_price:,}원"
            )
            
            buy_order = await conditional_order_manager.create_order(buy_request)
            created_orders.append(ConditionalOrderResponse(
                order_id=buy_order.order_id,
                message="매수 조건부 주문이 생성되었습니다.",
                condition_description=buy_order.get_condition_description(),
                action_description=buy_order.get_action_description(),
                status=buy_order.status,
                created_at=buy_order.created_at,
                valid_until=buy_order.valid_until
            ))
        
        # 매도 조건 생성
        if request.sell_price:
            sell_request = ConditionalOrderRequest(
                user_id=request.user_id,
                symbol=request.symbol,
                condition_type=ConditionType.PRICE_ABOVE,
                condition_value=request.sell_price,
                action=OrderAction.SELL,
                quantity=request.quantity,
                amount=request.amount,
                valid_hours=request.valid_hours,
                dry_run=request.dry_run,
                memo=f"간단 주문 - 매도가 {request.sell_price:,}원"
            )
            
            sell_order = await conditional_order_manager.create_order(sell_request)
            created_orders.append(ConditionalOrderResponse(
                order_id=sell_order.order_id,
                message="매도 조건부 주문이 생성되었습니다.",
                condition_description=sell_order.get_condition_description(),
                action_description=sell_order.get_action_description(),
                status=sell_order.status,
                created_at=sell_order.created_at,
                valid_until=sell_order.valid_until
            ))
        
        if not created_orders:
            raise HTTPException(status_code=400, detail="매수가 또는 매도가 중 하나는 설정해야 합니다.")
        
        return created_orders
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"간단 조건부 주문 생성 실패: {str(e)}")


@router.get("/orders/{user_id}", response_model=OrderListResponse)
async def get_user_orders(user_id: str, status: Optional[OrderStatus] = None):
    """
    사용자의 조건부 매매 주문 목록 조회
    
    특정 사용자의 모든 조건부 주문을 조회합니다.
    """
    try:
        orders = conditional_order_manager.get_user_orders(user_id)
        
        # 상태 필터링
        if status:
            orders = [order for order in orders if order.status == status]
        
        active_count = len([order for order in orders if order.status == OrderStatus.ACTIVE])
        
        return OrderListResponse(
            orders=orders,
            total_count=len(orders),
            active_count=active_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주문 목록 조회 실패: {str(e)}")


@router.get("/order/{order_id}", response_model=ConditionalOrder)
async def get_order_detail(order_id: str):
    """조건부 매매 주문 상세 조회"""
    order = conditional_order_manager.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    
    return order


@router.post("/order/{order_id}/cancel")
async def cancel_order(order_id: str, user_id: str):
    """조건부 매매 주문 취소"""
    success = await conditional_order_manager.cancel_order(order_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="주문을 취소할 수 없습니다.")
    
    return {"message": "주문이 취소되었습니다.", "order_id": order_id}


@router.get("/active", response_model=OrderListResponse)
async def get_active_orders():
    """모든 활성 조건부 매매 주문 조회"""
    try:
        orders = conditional_order_manager.get_active_orders()
        
        return OrderListResponse(
            orders=orders,
            total_count=len(orders),
            active_count=len(orders)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"활성 주문 조회 실패: {str(e)}")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """조건부 매매 통계 정보"""
    try:
        stats = conditional_order_manager.get_statistics()
        
        return StatisticsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


@router.post("/start-monitoring")
async def start_monitoring():
    """조건부 매매 모니터링 시작"""
    await conditional_order_manager.start_monitoring()
    return {"message": "조건부 매매 모니터링이 시작되었습니다."}


@router.post("/stop-monitoring")
async def stop_monitoring():
    """조건부 매매 모니터링 중지"""
    await conditional_order_manager.stop_monitoring()
    return {"message": "조건부 매매 모니터링이 중지되었습니다."}


@router.get("/condition-types")
async def get_condition_types():
    """사용 가능한 조건 타입 목록"""
    return {
        "condition_types": [
            {"value": "price_above", "label": "가격 이상", "description": "현재가가 설정가 이상일 때"},
            {"value": "price_below", "label": "가격 이하", "description": "현재가가 설정가 이하일 때"},
            {"value": "price_between", "label": "가격 범위", "description": "현재가가 설정 범위 내일 때"},
            {"value": "rsi_above", "label": "RSI 이상", "description": "RSI가 설정값 이상일 때"},
            {"value": "rsi_below", "label": "RSI 이하", "description": "RSI가 설정값 이하일 때"},
            {"value": "ma_cross_up", "label": "골든크로스", "description": "단기이평선이 장기이평선 상향돌파"},
            {"value": "ma_cross_down", "label": "데드크로스", "description": "단기이평선이 장기이평선 하향돌파"}
        ],
        "action_types": [
            {"value": "buy", "label": "매수", "description": "지정 수량/금액 매수"},
            {"value": "sell", "label": "매도", "description": "지정 수량/금액 매도"},
            {"value": "buy_percent", "label": "비율 매수", "description": "보유 금액의 일정 비율 매수"},
            {"value": "sell_percent", "label": "비율 매도", "description": "보유 주식의 일정 비율 매도"}
        ]
    }


# === 테스트용 엔드포인트 ===

# Mock 데이터 제거: 테스트 샘플 주문 생성 비활성화
# @router.post("/test/create-sample")
# async def create_sample_orders():
#     """테스트용 샘플 주문 생성 - Mock 데이터 제거로 비활성화"""
#     raise HTTPException(status_code=501, detail="샘플 주문 생성이 비활성화되었습니다. 실제 조건을 설정하여 주문을 생성해주세요.")