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
from fastapi.staticfiles import StaticFiles

# Distributed Tracing
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Structured Logging
import structlog

# Handle both relative and absolute imports for different execution contexts
try:
    from .api import auth, chart, stock, account
    from .config.settings import settings
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.api import auth, chart, stock, account
    from kiwoom_api.config.settings import settings

# OpenTelemetry 설정
def setup_tracing():
    """분산 추적 설정 (Zipkin 서버가 없으면 비활성화)"""
    try:
        # Zipkin 서버 연결 테스트
        import requests
        zipkin_endpoint = "http://quantum-zipkin:9411/api/v2/spans"
        requests.get("http://quantum-zipkin:9411/health", timeout=1)
        
        # Tracer Provider 설정
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Zipkin Exporter 설정
        zipkin_exporter = ZipkinExporter(
            endpoint=zipkin_endpoint,
            local_node_ipv4="127.0.0.1",
            local_node_port=8100,
        )
        
        # Span Processor 추가
        span_processor = BatchSpanProcessor(zipkin_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        return tracer
    except:
        # Zipkin 서버가 없으면 기본 tracer 반환 (트레이싱 비활성화)
        trace.set_tracer_provider(TracerProvider())
        return trace.get_tracer(__name__)

# Structured Logging 설정
def setup_logging():
    """구조화된 로깅 설정"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# 추적 및 로깅 초기화
tracer = setup_tracing()
setup_logging()
logger = structlog.get_logger(__name__)


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

# FastAPI 자동 계측 설정
FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())

# API 라우터 등록
app.include_router(auth.router, prefix="")
app.include_router(chart.router, prefix="")
app.include_router(stock.router, prefix="")
app.include_router(account.router, prefix="")

# 정적 파일 서빙 (대시보드용)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """루트 경로에서 Swagger UI로 리다이렉트"""
    return RedirectResponse(url="/docs")


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """실시간 WebSocket 대시보드로 리다이렉트"""
    return RedirectResponse(url="/static/kiwoom_realtime_dashboard.html")


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
