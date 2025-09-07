"""
Quantum Adapter External - Main FastAPI Application

External data adapter for Quantum Trading Platform providing integration with:
- Naver News API
- DART API (planned)
- Other external data sources

Port: 8001
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from config.settings import settings
from routers import health, news, disclosure
from src.common.exceptions import ExternalAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Quantum Adapter External")
    logger.info(f"📊 Debug mode: {settings.debug}")
    logger.info(f"🔧 Server port: {settings.server_port}")
    logger.info(f"📰 Naver API configured: {bool(settings.naver_client_id and settings.naver_client_secret)}")
    
    yield
    
    # Shutdown
    logger.info("⏹️ Shutting down Quantum Adapter External")


# Initialize FastAPI application
app = FastAPI(
    title="Quantum Adapter External",
    description="External data adapter for Quantum Trading Platform providing news, financial data, and regulatory information",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://quantum-trading.com:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all incoming requests with timing information."""
    start_time = time.time()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path} - {request.client.host}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"📤 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    
    return response


# Global exception handlers
@app.exception_handler(ExternalAPIError)
async def external_api_exception_handler(request: Request, exc: ExternalAPIError):
    """Handle external API errors gracefully."""
    logger.error(f"External API error: {exc.message} (Status: {exc.status_code})")
    
    return JSONResponse(
        status_code=exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "External API Error",
            "message": exc.message,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": time.time()
        }
    )


# Include routers
app.include_router(health.router)
app.include_router(news.router)
app.include_router(disclosure.router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing basic service information.
    """
    return {
        "service": "quantum-adapter-external",
        "version": "1.0.0",
        "status": "operational",
        "description": "External data adapter for Quantum Trading Platform",
        "endpoints": {
            "health": "/health",
            "news": "/news",
            "disclosure": "/disclosure",
            "documentation": "/docs" if settings.debug else "disabled"
        },
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🔧 Starting server with uvicorn")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.server_port,
        reload=settings.debug,
        log_level="info"
    )