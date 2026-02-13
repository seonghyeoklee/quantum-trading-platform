"""FastAPI 진입점"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router, set_engine
from app.config import load_settings
from app.trading.engine import TradingEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    engine = TradingEngine(settings)
    set_engine(engine)
    logger.info("자동매매 엔진 초기화 완료")
    yield
    await engine.stop()
    logger.info("자동매매 엔진 종료")


app = FastAPI(
    title="Quantum Trading Platform",
    description="국내주식 모의투자 자동매매 시스템",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
