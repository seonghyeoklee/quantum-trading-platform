"""API 엔드포인트"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.trading.engine import TradingEngine

router = APIRouter()

# 엔진 인스턴스는 main.py에서 주입
_engine: TradingEngine | None = None


def set_engine(engine: TradingEngine) -> None:
    global _engine
    _engine = engine


def get_engine() -> TradingEngine:
    if _engine is None:
        raise HTTPException(status_code=503, detail="엔진이 초기화되지 않았습니다.")
    return _engine


# --- 요청/응답 모델 ---


class StartRequest(BaseModel):
    symbols: list[str] | None = None


# --- 엔드포인트 ---


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/market/price/{symbol}")
async def get_price(symbol: str):
    engine = get_engine()
    try:
        price = await engine.market.get_current_price(symbol)
        return price.model_dump()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/trading/start")
async def start_trading(req: StartRequest):
    engine = get_engine()
    status = engine.get_status()
    if status.status.value == "RUNNING":
        raise HTTPException(status_code=409, detail="이미 실행 중입니다.")
    await engine.start(req.symbols)
    status = engine.get_status()
    return {"message": "자동매매 시작", "symbols": status.watch_symbols}


@router.post("/trading/stop")
async def stop_trading():
    engine = get_engine()
    await engine.stop()
    return {"message": "자동매매 중지"}


@router.get("/trading/status")
async def trading_status():
    engine = get_engine()
    status = engine.get_status()
    return status.model_dump(mode="json")


@router.get("/trading/positions")
async def get_positions():
    engine = get_engine()
    try:
        positions = await engine.order.get_balance()
        return [p.model_dump() for p in positions]
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
