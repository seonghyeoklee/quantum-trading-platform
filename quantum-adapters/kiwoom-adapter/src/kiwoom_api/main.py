"""키움 API FastAPI 메인 애플리케이션

키움증권 REST API를 위한 FastAPI 서비스
Java kiwoom-service와 동일한 API 스펙 제공
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Distributed Tracing
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Structured Logging
import structlog

# Prometheus Metrics
from prometheus_fastapi_instrumentator import Instrumentator

# Handle both relative and absolute imports for different execution contexts
try:
    from .api import auth, chart, stock, account, websocket, news, strategy, conditional_trading
    from .analysis.api import analysis_router
    from .analysis.api.comprehensive_router import router as comprehensive_router
    from .config.settings import settings
    from .events.api_middleware import KafkaEventMiddleware
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.api import auth, chart, stock, account, websocket, news, strategy, conditional_trading
    from kiwoom_api.analysis.api import analysis_router
    from kiwoom_api.analysis.api.comprehensive_router import router as comprehensive_router
    from kiwoom_api.config.settings import settings
    from kiwoom_api.events.api_middleware import KafkaEventMiddleware

# OpenTelemetry 설정
def setup_tracing():
    """분산 추적 설정 (Tempo 서버로 OTLP 전송)"""
    try:
        # Tempo 서버 연결 테스트
        import requests
        tempo_endpoint = "http://quantum-tempo:4318/v1/traces"
        requests.get("http://quantum-tempo:3200/ready", timeout=1)

        # Tracer Provider 설정
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)

        # OTLP Exporter 설정 (Tempo용)
        otlp_exporter = OTLPSpanExporter(
            endpoint=tempo_endpoint,
            headers={}
        )

        # Span Processor 추가
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

        return tracer
    except (requests.exceptions.RequestException, requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError) as e:
        # Tempo 서버 연결 실패 시 기본 tracer 반환 (트레이싱 비활성화)
        print(f"⚠️ Tempo 서버 연결 실패 - 트레이싱 비활성화: {str(e)}")
        trace.set_tracer_provider(TracerProvider())
        return trace.get_tracer(__name__)
    except Exception as e:
        # 기타 예외 처리
        print(f"⚠️ 트레이싱 설정 실패: {str(e)}")
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

# Kafka 이벤트 미들웨어 추가 (임시 비활성화)
import os
enable_kafka = False  # 임시로 비활성화
# enable_kafka = os.getenv('ENABLE_KAFKA', 'true').lower() == 'true'
# app.add_middleware(KafkaEventMiddleware, enable_kafka=enable_kafka)

# FastAPI 자동 계측 설정 (OpenTelemetry)
FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())

# Prometheus 메트릭 계측 설정
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

# API 라우터 등록
app.include_router(auth.router, prefix="")
app.include_router(chart.router, prefix="")
app.include_router(stock.router, prefix="")
app.include_router(account.router, prefix="")
app.include_router(websocket.router, prefix="")
app.include_router(news.router, prefix="")  # 뉴스 API 추가
app.include_router(strategy.router, prefix="")  # 자동매매 전략 API 추가
app.include_router(conditional_trading.router, prefix="")  # 조건부 매매 API 추가
app.include_router(analysis_router.router, prefix="")
app.include_router(comprehensive_router, prefix="")


# ======== 글로벌 예외 처리기 ========

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 처리"""
    logger.error(
        "HTTP 예외 발생",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
        client=request.client.host if request.client else None
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
                "timestamp": datetime.now().isoformat()
            }
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """값 오류 처리"""
    logger.error(
        "값 오류 발생",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        client=request.client.host if request.client else None
    )
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": 400,
                "message": f"잘못된 요청 값: {str(exc)}",
                "path": str(request.url.path),
                "timestamp": datetime.now().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 처리"""
    logger.error(
        "예상치 못한 오류 발생",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        client=request.client.host if request.client else None,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "내부 서버 오류가 발생했습니다",
                "path": str(request.url.path),
                "timestamp": datetime.now().isoformat()
            }
        }
    )


# 정적 파일 서빙 (대시보드용) - static 디렉토리가 있을 때만
import os
from pathlib import Path

static_dir = Path("static")
if static_dir.exists() and static_dir.is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Static files mounted at /static")


@app.get("/", include_in_schema=False)
async def root():
    """루트 경로에서 Swagger UI로 리다이렉트"""
    return RedirectResponse(url="/docs")


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """실시간 WebSocket 대시보드로 리다이렉트 또는 메시지"""
    static_dir = Path("static")
    if static_dir.exists() and static_dir.is_dir():
        return RedirectResponse(url="/static/kiwoom_realtime_dashboard.html")
    else:
        return {"message": "Dashboard not available - static files not found"}


@app.get("/health")
async def health_check():
    """향상된 헬스 체크 엔드포인트 - 서비스 상태 진단"""
    try:
        # 기본 상태 정보
        health_data = {
            "status": "healthy",
            "service": "kiwoom-api-python",
            "version": "0.1.0",
            "mode": settings.kiwoom_mode_description,
            "timestamp": datetime.now().isoformat()
        }

        # 설정 검증
        config_status = "healthy"
        config_issues = []

        # API 키 검증
        if not settings.validate_keys():
            config_status = "warning"
            config_issues.append("API 키 설정 누락 또는 불완전")

        # 환경 변수 검증
        if not settings.DART_API_KEY:
            config_issues.append("DART API 키 설정 누락")

        health_data.update({
            "config": {
                "status": config_status,
                "app_key_configured": bool(settings.KIWOOM_APP_KEY),
                "app_secret_configured": bool(settings.KIWOOM_APP_SECRET),
                "dart_api_configured": bool(settings.DART_API_KEY),
                "issues": config_issues
            },
            "environment": {
                "sandbox_mode": settings.KIWOOM_SANDBOX_MODE,
                "kafka_enabled": settings.ENABLE_KAFKA,
                "log_level": settings.LOG_LEVEL,
                "host": settings.FASTAPI_HOST,
                "port": settings.FASTAPI_PORT
            }
        })

        # 전체 상태 결정
        if config_issues:
            health_data["status"] = "warning"

        return health_data

    except Exception as e:
        logger.error("헬스 체크 중 오류 발생", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "service": "kiwoom-api-python",
                "error": "헬스 체크 실패",
                "timestamp": datetime.now().isoformat()
            }
        )


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
