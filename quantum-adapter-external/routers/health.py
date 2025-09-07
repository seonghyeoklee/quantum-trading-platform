"""
Health check endpoints for Quantum Adapter External.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime
from config.settings import settings
import platform
import sys

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    service: str = "quantum-adapter-external"
    environment: dict


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check if the service is running and configured properly"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns basic service information and configuration status.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        environment={
            "python_version": sys.version,
            "platform": platform.platform(),
            "debug": settings.debug,
            "server_port": settings.server_port,
            "naver_api_configured": bool(settings.naver_client_id and settings.naver_client_secret),
            "dart_api_configured": bool(settings.dart_api_key)
        }
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check", 
    description="Check if the service is ready to handle requests"
)
async def readiness_check():
    """
    Readiness check endpoint.
    
    Verifies that all required configurations are in place.
    """
    # Check if essential configurations are present
    missing_configs = []
    
    if not settings.naver_client_id or not settings.naver_client_secret:
        missing_configs.append("Naver API credentials")
    
    if not settings.dart_api_key:
        missing_configs.append("DART API key")
    
    if missing_configs:
        return {
            "status": "not_ready",
            "message": f"Missing configurations: {', '.join(missing_configs)}",
            "timestamp": datetime.utcnow()
        }, status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "status": "ready",
        "message": "Service is ready to handle requests",
        "timestamp": datetime.utcnow()
    }