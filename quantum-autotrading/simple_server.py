"""
간단한 테스트 서버

시나리오 테스트를 위한 기본 API 서버입니다.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime
import random

app = FastAPI(
    title="국내주식 단타 자동매매 시스템",
    description="5분봉 기반 단타 자동매매 시스템 API",
    version="1.0.0"
)

# 전역 상태 관리
system_state = {
    "is_running": False,
    "positions": {},
    "orders": [],
    "balance": 10000000,  # 1천만원
    "order_counter": 1
}

# 요청 모델
class OrderRequest(BaseModel):
    symbol: str
    side: str  # buy, sell
    order_type: str  # market, limit
    quantity: int
    price: Optional[float] = None

class SystemStatus(BaseModel):
    is_running: bool
    uptime: str
    active_positions: int
    total_orders: int

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "국내주식 단타 자동매매 시스템",
        "version": "1.0.0",
        "status": "running" if system_state["is_running"] else "stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_running": system_state["is_running"]
    }

@app.get("/system/status")
async def get_system_status():
    """시스템 상태 조회"""
    return {
        "is_running": system_state["is_running"],
        "uptime": "00:05:23",
        "active_positions": len(system_state["positions"]),
        "total_orders": len(system_state["orders"]),
        "balance": system_state["balance"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/balance")
async def get_balance():
    """계좌 잔고 조회"""
    return {
        "total_balance": system_state["balance"],
        "available_balance": system_state["balance"] * 0.8,
        "used_balance": system_state["balance"] * 0.2,
        "positions_value": sum(pos.get("market_value", 0) for pos in system_state["positions"].values()),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/market-data/stocks/{symbol}/price")
async def get_stock_price(symbol: str):
    """현재가 조회"""
    # 삼성전자 기준 모의 데이터
    base_prices = {
        "005930": 75000,  # 삼성전자
        "000660": 45000,  # SK하이닉스
        "035420": 350000, # NAVER
        "051910": 850000, # LG화학
        "006400": 25000   # 삼성SDI
    }
    
    base_price = base_prices.get(symbol, 50000)
    current_price = base_price + random.randint(-1000, 1000)
    
    return {
        "symbol": symbol,
        "current_price": current_price,
        "change": random.randint(-500, 500),
        "change_percent": random.uniform(-2.0, 2.0),
        "volume": random.randint(1000000, 5000000),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/market-data/stocks/{symbol}/orderbook")
async def get_orderbook(symbol: str):
    """호가창 조회"""
    base_price = 75000 if symbol == "005930" else 50000
    
    bids = []
    asks = []
    
    for i in range(5):
        bid_price = base_price - (i + 1) * 100
        ask_price = base_price + (i + 1) * 100
        
        bids.append({
            "price": bid_price,
            "quantity": random.randint(100, 2000)
        })
        
        asks.append({
            "price": ask_price,
            "quantity": random.randint(100, 2000)
        })
    
    return {
        "symbol": symbol,
        "bids": bids,
        "asks": asks,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/market-data/stocks/{symbol}/indicators")
async def get_indicators(symbol: str):
    """기술적 지표 조회"""
    return {
        "symbol": symbol,
        "rsi": random.uniform(30, 70),
        "macd": random.uniform(-100, 100),
        "ema_5": random.uniform(74000, 76000),
        "ema_20": random.uniform(73000, 77000),
        "bollinger_upper": random.uniform(76000, 78000),
        "bollinger_lower": random.uniform(72000, 74000),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/trading/start")
async def start_trading():
    """자동매매 시작"""
    system_state["is_running"] = True
    return {
        "message": "자동매매가 시작되었습니다",
        "status": "started",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/trading/stop")
async def stop_trading():
    """자동매매 중지"""
    system_state["is_running"] = False
    return {
        "message": "자동매매가 중지되었습니다",
        "status": "stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trading/status")
async def get_trading_status():
    """거래 상태 조회"""
    return {
        "is_running": system_state["is_running"],
        "active_positions": len(system_state["positions"]),
        "pending_orders": len([o for o in system_state["orders"] if o["status"] == "pending"]),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trading/signals")
async def get_signals(symbol: Optional[str] = None, limit: int = 10):
    """매매 신호 조회"""
    signals = []
    
    symbols = [symbol] if symbol else ["005930", "000660", "035420"]
    
    for sym in symbols:
        for i in range(min(limit, 3)):
            signal_type = random.choice(["buy", "sell"])
            signals.append({
                "symbol": sym,
                "signal_type": signal_type,
                "strength": random.uniform(0.6, 0.9),
                "confidence": random.uniform(0.7, 0.95),
                "technical_score": random.uniform(0.5, 0.8),
                "microstructure_score": random.uniform(0.6, 0.9),
                "sentiment_score": random.uniform(0.4, 0.7),
                "current_price": random.randint(74000, 76000),
                "reasoning": f"{signal_type.upper()} 신호 - RSI 과매수/과매도, EMA 골든크로스",
                "timestamp": datetime.now().isoformat()
            })
    
    return signals[:limit]

@app.post("/trading/order")
async def place_order(order: OrderRequest):
    """주문 실행"""
    
    # 최대 포지션 수 체크 (3개 제한)
    if order.side == "buy" and len(system_state["positions"]) >= 3:
        raise HTTPException(status_code=400, detail="최대 포지션 수(3개)를 초과했습니다")
    
    order_id = f"ORD{system_state['order_counter']:06d}"
    system_state["order_counter"] += 1
    
    # 주문 생성
    new_order = {
        "order_id": order_id,
        "symbol": order.symbol,
        "side": order.side,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "price": order.price,
        "status": "filled",  # 즉시 체결로 시뮬레이션
        "filled_quantity": order.quantity,
        "avg_fill_price": order.price or 75000,
        "created_at": datetime.now().isoformat(),
        "filled_at": datetime.now().isoformat()
    }
    
    system_state["orders"].append(new_order)
    
    # 포지션 업데이트
    if order.side == "buy":
        if order.symbol in system_state["positions"]:
            pos = system_state["positions"][order.symbol]
            total_quantity = pos["quantity"] + order.quantity
            total_cost = pos["avg_price"] * pos["quantity"] + (order.price or 75000) * order.quantity
            pos["avg_price"] = total_cost / total_quantity
            pos["quantity"] = total_quantity
        else:
            system_state["positions"][order.symbol] = {
                "symbol": order.symbol,
                "quantity": order.quantity,
                "avg_price": order.price or 75000,
                "current_price": order.price or 75000,
                "unrealized_pnl": 0,
                "unrealized_pnl_percent": 0,
                "opened_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
    else:  # sell
        if order.symbol in system_state["positions"]:
            pos = system_state["positions"][order.symbol]
            pos["quantity"] -= order.quantity
            if pos["quantity"] <= 0:
                del system_state["positions"][order.symbol]
    
    return {
        "order_id": order_id,
        "status": "filled",
        "message": f"{order.side.upper()} 주문이 체결되었습니다",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trading/orders")
async def get_orders(symbol: Optional[str] = None):
    """주문 내역 조회"""
    orders = system_state["orders"]
    if symbol:
        orders = [o for o in orders if o["symbol"] == symbol]
    return orders[-10:]  # 최근 10개

@app.get("/trading/positions")
async def get_positions():
    """현재 포지션 조회"""
    positions = []
    for symbol, pos in system_state["positions"].items():
        # 현재가 업데이트 (시뮬레이션)
        current_price = pos["avg_price"] + random.randint(-500, 500)
        unrealized_pnl = (current_price - pos["avg_price"]) * pos["quantity"]
        unrealized_pnl_percent = (current_price - pos["avg_price"]) / pos["avg_price"] * 100
        
        pos.update({
            "current_price": current_price,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percent,
            "market_value": current_price * pos["quantity"]
        })
        
        positions.append(pos)
    
    return positions

@app.post("/trading/emergency-stop")
async def emergency_stop():
    """긴급 정지"""
    system_state["is_running"] = False
    return {
        "message": "긴급 정지가 실행되었습니다",
        "status": "emergency_stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/trading/history")
async def get_trade_history(limit: int = 10):
    """거래 히스토리"""
    return system_state["orders"][-limit:]

@app.get("/system/performance/daily")
async def get_daily_performance():
    """일일 성과"""
    return {
        "date": datetime.now().date().isoformat(),
        "total_trades": len(system_state["orders"]),
        "winning_trades": random.randint(5, 8),
        "losing_trades": random.randint(2, 5),
        "win_rate": random.uniform(60, 80),
        "total_pnl": random.randint(-50000, 150000),
        "total_pnl_percent": random.uniform(-2, 5),
        "best_trade": random.randint(10000, 50000),
        "worst_trade": random.randint(-30000, -5000)
    }

@app.get("/system/performance/weekly")
async def get_weekly_performance():
    """주간 성과"""
    return {
        "week": "2024-W42",
        "total_trades": random.randint(50, 100),
        "win_rate": random.uniform(65, 75),
        "total_pnl": random.randint(100000, 500000),
        "sharpe_ratio": random.uniform(1.2, 2.5),
        "max_drawdown": random.uniform(-5, -15)
    }

@app.get("/system/risk-status")
async def get_risk_status():
    """리스크 상태"""
    return {
        "max_positions": 3,
        "current_positions": len(system_state["positions"]),
        "position_utilization": len(system_state["positions"]) / 3 * 100,
        "balance_utilization": 20.0,
        "risk_level": "LOW",
        "alerts": []
    }

@app.post("/trading/test-stop-loss")
async def test_stop_loss(data: Dict[str, Any]):
    """손절 테스트"""
    return {
        "message": f"{data['symbol']} 손절 시나리오 테스트 완료",
        "loss_percent": data["loss_percent"],
        "action": "stop_loss_triggered",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 자동매매 시스템 테스트 서버 시작")
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
