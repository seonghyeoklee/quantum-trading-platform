"""
거래 모드 관리 API 엔드포인트

키움증권 API 키 패턴 분석을 통한 자동 거래 모드 탐지 및 Java 백엔드와의 동기화 기능을 제공합니다.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

try:
    from ..functions.trading_mode_sync import (
        trading_mode_sync, 
        detect_trading_mode, 
        sync_trading_mode_with_backend,
        validate_keys_for_mode,
        TradingMode,
        TradingModeInfo,
        KeyPatternAnalysis
    )
    from ..models.common import APIResponse
    from ..utils.rate_limiter import get_rate_limiter
    from ..auth.token_cache import get_valid_token
except ImportError:
    from kiwoom_api.functions.trading_mode_sync import (
        trading_mode_sync, 
        detect_trading_mode, 
        sync_trading_mode_with_backend,
        validate_keys_for_mode,
        TradingMode,
        TradingModeInfo,
        KeyPatternAnalysis
    )
    from kiwoom_api.models.common import APIResponse
    from kiwoom_api.utils.rate_limiter import get_rate_limiter
    from kiwoom_api.auth.token_cache import get_valid_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trading-mode", tags=["trading-mode"])

# Request Models
class TradingModeDetectionRequest(BaseModel):
    """거래 모드 탐지 요청"""
    app_key: str = Field(..., description="키움증권 App Key")
    secret_key: str = Field(..., description="키움증권 Secret Key") 
    user_id: Optional[str] = Field(None, description="사용자 ID (옵션)")

class TradingModeSyncRequest(BaseModel):
    """거래 모드 동기화 요청"""
    user_id: str = Field(..., description="사용자 ID")
    app_key: str = Field(..., description="키움증권 App Key")
    secret_key: str = Field(..., description="키움증권 Secret Key")

class KeyValidationRequest(BaseModel):
    """API 키 유효성 검증 요청"""
    app_key: str = Field(..., description="키움증권 App Key")
    secret_key: str = Field(..., description="키움증권 Secret Key")

# Response Models
class TradingModeDetectionResponse(BaseModel):
    """거래 모드 탐지 응답"""
    user_id: str
    trading_mode: str
    detection_status: str
    message: str
    confidence_score: float
    detected_at: str

class TradingModeSyncResponse(BaseModel):
    """거래 모드 동기화 응답"""
    user_id: str
    detected_mode: str
    confidence_score: float
    sync_status: str
    sync_message: str
    synced_at: str

class KeyValidationResponse(BaseModel):
    """API 키 유효성 검증 응답"""
    trading_mode: str
    confidence_score: float
    app_key_pattern: str
    secret_key_pattern: str
    detection_reasons: list[str]

@router.post("/detect", response_model=APIResponse[TradingModeDetectionResponse])
async def detect_trading_mode_endpoint(request: TradingModeDetectionRequest):
    """
    API 키 패턴 분석을 통한 거래 모드 자동 탐지
    
    키움증권 App Key와 Secret Key의 패턴을 분석하여 
    실전투자/모의투자 모드를 자동으로 판단합니다.
    """
    try:
        logger.info(f"거래 모드 탐지 요청: user_id={request.user_id}")
        
        # Rate limiting 적용
        rate_limiter = await get_rate_limiter()
        
        async def _detect_mode():
            return await detect_trading_mode(
                app_key=request.app_key,
                secret_key=request.secret_key, 
                user_id=request.user_id
            )
        
        mode_info = await rate_limiter.execute_with_retry('trading_mode_detect', _detect_mode)
        
        response_data = TradingModeDetectionResponse(
            user_id=mode_info.user_id,
            trading_mode=mode_info.trading_mode.value,
            detection_status=mode_info.detection_status,
            message=mode_info.message,
            confidence_score=mode_info.confidence_score,
            detected_at=mode_info.detected_at or ""
        )
        
        logger.info(f"거래 모드 탐지 완료: {response_data.trading_mode} (신뢰도: {response_data.confidence_score})")
        
        return APIResponse(
            Code=200,
            Body=response_data,
            message="거래 모드 탐지가 완료되었습니다"
        )
        
    except Exception as e:
        logger.error(f"거래 모드 탐지 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래 모드 탐지에 실패했습니다: {str(e)}"
        )

@router.post("/sync", response_model=APIResponse[TradingModeSyncResponse])
async def sync_trading_mode_endpoint(request: TradingModeSyncRequest):
    """
    Java 백엔드와 거래 모드 동기화
    
    Python 어댑터에서 탐지한 거래 모드 정보를 
    Java 백엔드와 동기화합니다.
    """
    try:
        logger.info(f"거래 모드 동기화 요청: user_id={request.user_id}")
        
        # Rate limiting 적용
        rate_limiter = await get_rate_limiter()
        
        async def _sync_mode():
            return await sync_trading_mode_with_backend(
                user_id=request.user_id,
                app_key=request.app_key,
                secret_key=request.secret_key
            )
        
        sync_result = await rate_limiter.execute_with_retry('trading_mode_sync', _sync_mode)
        
        response_data = TradingModeSyncResponse(
            user_id=sync_result["user_id"],
            detected_mode=sync_result["detected_mode"],
            confidence_score=sync_result["confidence_score"],
            sync_status=sync_result["sync_status"],
            sync_message=sync_result["sync_message"],
            synced_at=sync_result["synced_at"]
        )
        
        logger.info(f"거래 모드 동기화 완료: {response_data.sync_status}")
        
        return APIResponse(
            Code=200,
            Body=response_data,
            message="거래 모드 동기화가 완료되었습니다"
        )
        
    except Exception as e:
        logger.error(f"거래 모드 동기화 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"거래 모드 동기화에 실패했습니다: {str(e)}"
        )

@router.post("/validate-keys", response_model=APIResponse[KeyValidationResponse])
async def validate_api_keys_endpoint(request: KeyValidationRequest):
    """
    API 키 패턴 유효성 검증
    
    키움증권 App Key와 Secret Key의 패턴을 검증하고
    어떤 거래 모드에 해당하는지 상세 분석 결과를 제공합니다.
    """
    try:
        logger.info("API 키 패턴 유효성 검증 요청")
        
        # Rate limiting 적용
        rate_limiter = await get_rate_limiter()
        
        async def _validate_keys():
            return await validate_keys_for_mode(
                app_key=request.app_key,
                secret_key=request.secret_key
            )
        
        analysis = await rate_limiter.execute_with_retry('key_validation', _validate_keys)
        
        response_data = KeyValidationResponse(
            trading_mode=analysis.trading_mode.value,
            confidence_score=analysis.confidence_score,
            app_key_pattern=analysis.app_key_pattern,
            secret_key_pattern=analysis.secret_key_pattern,
            detection_reasons=analysis.detection_reasons
        )
        
        logger.info(f"API 키 검증 완료: {response_data.trading_mode} (신뢰도: {response_data.confidence_score})")
        
        return APIResponse(
            Code=200,
            Body=response_data,
            message="API 키 패턴 검증이 완료되었습니다"
        )
        
    except Exception as e:
        logger.error(f"API 키 검증 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"API 키 검증에 실패했습니다: {str(e)}"
        )

@router.get("/status", response_model=APIResponse[Dict[str, Any]])
async def get_trading_mode_status():
    """
    거래 모드 시스템 상태 조회
    
    거래 모드 탐지 시스템의 현재 상태와 통계 정보를 제공합니다.
    """
    try:
        logger.debug("거래 모드 시스템 상태 조회")
        
        # 시스템 상태 정보
        status_info = {
            "service_name": "Kiwoom Trading Mode Detection Service",
            "version": "1.0.0",
            "status": "ACTIVE",
            "supported_modes": [mode.value for mode in TradingMode],
            "detection_patterns": {
                "production_indicators": ["길이 >= 32자", "표준 키움증권 형식"],
                "sandbox_indicators": ["_TEST", "_SB", "_DEMO", "TEST_", "DEMO_"]
            },
            "system_time": trading_mode_sync._get_current_timestamp()
        }
        
        return APIResponse(
            Code=200,
            Body=status_info,
            message="거래 모드 시스템 상태 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"시스템 상태 조회에 실패했습니다: {str(e)}"
        )

@router.get("/patterns", response_model=APIResponse[Dict[str, Any]])
async def get_supported_patterns():
    """
    지원하는 API 키 패턴 정보
    
    키움증권 API 키 패턴 인식 규칙과 
    각 거래 모드별 특징을 제공합니다.
    """
    try:
        logger.debug("지원 패턴 정보 조회")
        
        patterns_info = {
            "production_patterns": {
                "app_key": {
                    "format": "PS[A-Z0-9]{32}",
                    "min_length": 32,
                    "characteristics": ["실전투자 전용", "영숫자 조합", "고정 접두사"]
                },
                "secret_key": {
                    "format": "[A-Za-z0-9+/]{64}={0,2}",
                    "min_length": 32,
                    "characteristics": ["Base64 형식", "실전 거래용", "높은 보안"]
                }
            },
            "sandbox_patterns": {
                "app_key": {
                    "indicators": ["_TEST", "_SB", "_DEMO", "TEST_", "DEMO_"],
                    "characteristics": ["모의투자 전용", "테스트 표시자 포함"]
                },
                "secret_key": {
                    "indicators": ["_TEST", "_DEMO", "_SB"],
                    "characteristics": ["테스트용 접미사", "안전한 연습 환경"]
                }
            },
            "detection_confidence": {
                "high": "0.9+",
                "medium": "0.7-0.9", 
                "low": "0.0-0.7"
            }
        }
        
        return APIResponse(
            Code=200,
            Body=patterns_info,
            message="지원 패턴 정보 조회 완료"
        )
        
    except Exception as e:
        logger.error(f"패턴 정보 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"패턴 정보 조회에 실패했습니다: {str(e)}"
        )