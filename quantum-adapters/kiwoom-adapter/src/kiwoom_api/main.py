"""키움 API FastAPI 메인 애플리케이션

키움증권 REST API를 위한 FastAPI 서비스
Java kiwoom-service와 동일한 API 스펙 제공
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# Handle both relative and absolute imports for different execution contexts
try:
    from .api import auth, chart, websocket, websocket_rest, stock
    from .config.settings import settings
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.api import auth, chart, websocket, websocket_rest, stock
    from kiwoom_api.config.settings import settings

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 애플리케이션 생명주기 관리"""
    # 애플리케이션 시작시
    logger.info("🚀 키움 API 서비스 시작")
    logger.info(f"📊 모드: {settings.kiwoom_mode_description}")
    logger.info(f"🔑 앱키: {settings.get_app_key()}")
    logger.info(f"🌐 서버: {settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}")
    logger.info(f"📚 API 문서: http://{settings.FASTAPI_HOST}:{settings.FASTAPI_PORT}/docs")

    yield

    # 애플리케이션 종료시
    logger.info("🛑 키움 API 서비스 종료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="REST API 서비스",
    description="""
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(auth.router, prefix="")
app.include_router(chart.router, prefix="")
app.include_router(websocket.router, prefix="")
app.include_router(websocket_rest.router, prefix="")
app.include_router(stock.router, prefix="")


@app.get("/", include_in_schema=False)
async def root():
    """루트 경로에서 Swagger UI로 리다이렉트"""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "kiwoom-api-python",
        "version": "0.1.0",
        "mode": settings.kiwoom_mode_description
    }


if __name__ == "__main__":
    import uvicorn

    # 개발 서버 실행
    uvicorn.run(
        "kiwoom_api.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
