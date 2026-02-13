"""API 엔드포인트"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.trading.engine import TradingEngine

router = APIRouter()


def get_engine(request: Request) -> TradingEngine:
    """FastAPI 의존성 주입으로 엔진 인스턴스 획득"""
    engine: TradingEngine | None = getattr(request.app.state, "engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="엔진이 초기화되지 않았습니다.")
    return engine


# --- 요청/응답 모델 ---


class StartRequest(BaseModel):
    symbols: list[str] | None = None


# --- 엔드포인트 ---


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/market/price/{symbol}")
async def get_price(symbol: str, engine: TradingEngine = Depends(get_engine)):
    try:
        price = await engine.market.get_current_price(symbol)
        return price.model_dump()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/trading/start")
async def start_trading(req: StartRequest, engine: TradingEngine = Depends(get_engine)):
    status = engine.get_status()
    if status.status.value == "RUNNING":
        raise HTTPException(status_code=409, detail="이미 실행 중입니다.")
    await engine.start(req.symbols)
    status = engine.get_status()
    return {"message": "자동매매 시작", "symbols": status.watch_symbols}


@router.post("/trading/stop")
async def stop_trading(engine: TradingEngine = Depends(get_engine)):
    await engine.stop()
    return {"message": "자동매매 중지"}


@router.get("/trading/status")
async def trading_status(engine: TradingEngine = Depends(get_engine)):
    status = engine.get_status()
    return status.model_dump(mode="json")


@router.get("/trading/positions")
async def get_positions(engine: TradingEngine = Depends(get_engine)):
    try:
        positions, summary = await engine.order.get_balance()
        return {
            "positions": [p.model_dump() for p in positions],
            "summary": summary.model_dump(),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


