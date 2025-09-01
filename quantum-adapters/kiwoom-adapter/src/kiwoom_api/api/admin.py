"""
관리자 API 엔드포인트

Java 백엔드에서 호출하는 관리자 전용 API들을 제공합니다.
사용자별 트레이딩 모드 변경, 시스템 설정 관리 등의 기능을 포함합니다.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import logging

# 이중 import 전략 적용
try:
    from ..config.runtime_settings import (
        user_trading_settings_manager, 
        set_user_trading_mode,
        get_trading_statistics,
        UserTradingConfig
    )
    from ..auth.token_cache import token_cache
    from ..config.settings import settings
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.config.runtime_settings import (
        user_trading_settings_manager, 
        set_user_trading_mode,
        get_trading_statistics,
        UserTradingConfig
    )
    from kiwoom_api.auth.token_cache import token_cache
    from kiwoom_api.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# === 요청/응답 모델들 ===

class UserTradingModeRequest(BaseModel):
    """사용자 트레이딩 모드 변경 요청"""
    user_id: str = Field(..., description="사용자 ID")
    sandbox_mode: bool = Field(..., description="샌드박스 모드 여부 (true: 모의투자, false: 실전투자)")
    kiwoom_account_id: Optional[str] = Field(None, description="키움 계좌 ID")
    max_daily_amount: Optional[float] = Field(None, description="일일 최대 투자금액")
    risk_level: str = Field("MEDIUM", description="리스크 레벨 (LOW/MEDIUM/HIGH)")
    auto_trading_enabled: bool = Field(False, description="자동매매 활성화 여부")
    notifications_enabled: bool = Field(True, description="알림 활성화 여부")
    ttl_hours: int = Field(24, description="설정 유효시간 (시간)")
    timestamp: Optional[datetime] = Field(None, description="요청 시간")


class AdminResponse(BaseModel):
    """관리자 API 응답"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SystemStatusResponse(BaseModel):
    """시스템 상태 응답"""
    system_mode: str  # sandbox/production
    python_adapter_version: str
    active_users: int
    sandbox_mode_users: int
    production_mode_users: int
    default_mode: str
    uptime_seconds: int
    last_cleanup: Optional[datetime]
    kiwoom_connection_status: bool


class UserConfigResponse(BaseModel):
    """사용자 설정 응답"""
    user_id: str
    sandbox_mode: bool
    kiwoom_account_id: Optional[str]
    max_daily_amount: Optional[float]
    risk_level: str
    auto_trading_enabled: bool
    notifications_enabled: bool
    updated_at: datetime
    expires_at: Optional[datetime]
    is_expired: bool


# === 보안 의존성 ===

def verify_admin_access(authorization: str = Header(None)):
    """관리자 접근 권한 확인"""
    # 간단한 API 키 기반 인증 (실제로는 JWT 토큰이나 더 강력한 인증 사용)
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    # 실제 구현에서는 더 복잡한 인증 로직 필요
    # 예: JWT 토큰 검증, 데이터베이스에서 권한 확인 등
    return True


# === API 엔드포인트들 ===

@router.post("/user-trading-mode", response_model=AdminResponse)
async def update_user_trading_mode(
    request: UserTradingModeRequest,
    _: bool = Depends(verify_admin_access)
):
    """
    사용자별 트레이딩 모드 업데이트
    
    Java 백엔드에서 호출되는 주요 엔드포인트입니다.
    사용자가 웹 UI에서 모드를 변경하면 이 API를 통해 Python 어댑터에 반영됩니다.
    """
    try:
        logger.info("사용자 트레이딩 모드 업데이트 요청: user_id=%s, sandbox_mode=%s", 
                   request.user_id, request.sandbox_mode)
        
        # 기존 설정 조회 (로깅용)
        old_config = user_trading_settings_manager.get_user_config(request.user_id)
        old_mode = old_config.sandbox_mode if old_config else None
        
        # 사용자별 트레이딩 모드 설정
        set_user_trading_mode(
            user_id=request.user_id,
            sandbox_mode=request.sandbox_mode,
            kiwoom_account_id=request.kiwoom_account_id,
            max_daily_amount=request.max_daily_amount,
            risk_level=request.risk_level,
            auto_trading_enabled=request.auto_trading_enabled,
            notifications_enabled=request.notifications_enabled,
            ttl_hours=request.ttl_hours
        )
        
        # 모드 변경 시 사용자별 토큰 캐시 무효화
        if old_mode != request.sandbox_mode:
            await token_cache.invalidate_user_tokens(request.user_id)
            logger.info("사용자 토큰 캐시 무효화: user_id=%s", request.user_id)
        
        mode_description = "모의투자" if request.sandbox_mode else "실전투자"
        
        return AdminResponse(
            success=True,
            message=f"사용자 {request.user_id}의 트레이딩 모드가 {mode_description}(으)로 변경되었습니다",
            data={
                "user_id": request.user_id,
                "previous_mode": "모의투자" if old_mode else "실전투자" if old_mode is not None else None,
                "new_mode": mode_description,
                "kiwoom_account_id": request.kiwoom_account_id,
                "ttl_hours": request.ttl_hours
            }
        )
        
    except Exception as e:
        logger.error("사용자 트레이딩 모드 업데이트 실패: user_id=%s, error=%s", 
                    request.user_id, str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"트레이딩 모드 업데이트 실패: {str(e)}"
        )


@router.get("/user-trading-mode/{user_id}", response_model=AdminResponse)
async def get_user_trading_mode(
    user_id: str,
    _: bool = Depends(verify_admin_access)
):
    """특정 사용자의 트레이딩 모드 조회"""
    try:
        user_config = user_trading_settings_manager.get_user_config(user_id)
        
        if not user_config:
            return AdminResponse(
                success=True,
                message=f"사용자 {user_id}는 기본 설정을 사용 중입니다",
                data={
                    "user_id": user_id,
                    "sandbox_mode": settings.KIWOOM_SANDBOX_MODE,
                    "is_default": True
                }
            )
        
        return AdminResponse(
            success=True,
            message="사용자 트레이딩 모드 조회 성공",
            data=UserConfigResponse(
                user_id=user_config.user_id,
                sandbox_mode=user_config.sandbox_mode,
                kiwoom_account_id=user_config.kiwoom_account_id,
                max_daily_amount=user_config.max_daily_amount,
                risk_level=user_config.risk_level,
                auto_trading_enabled=user_config.auto_trading_enabled,
                notifications_enabled=user_config.notifications_enabled,
                updated_at=user_config.updated_at,
                expires_at=user_config.expires_at,
                is_expired=user_config.is_expired()
            ).dict()
        )
        
    except Exception as e:
        logger.error("사용자 트레이딩 모드 조회 실패: user_id=%s, error=%s", user_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"트레이딩 모드 조회 실패: {str(e)}"
        )


@router.delete("/user-trading-mode/{user_id}", response_model=AdminResponse)
async def remove_user_trading_mode(
    user_id: str,
    _: bool = Depends(verify_admin_access)
):
    """사용자별 트레이딩 모드 설정 제거 (기본값으로 복원)"""
    try:
        removed = user_trading_settings_manager.remove_user_config(user_id)
        
        if removed:
            # 사용자 토큰 캐시도 무효화
            await token_cache.invalidate_user_tokens(user_id)
            
            return AdminResponse(
                success=True,
                message=f"사용자 {user_id}의 개별 설정이 제거되어 기본 설정으로 복원되었습니다",
                data={
                    "user_id": user_id,
                    "reverted_to_default": True,
                    "default_sandbox_mode": settings.KIWOOM_SANDBOX_MODE
                }
            )
        else:
            return AdminResponse(
                success=True,
                message=f"사용자 {user_id}는 이미 기본 설정을 사용 중입니다",
                data={
                    "user_id": user_id,
                    "was_using_default": True
                }
            )
            
    except Exception as e:
        logger.error("사용자 트레이딩 모드 제거 실패: user_id=%s, error=%s", user_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"트레이딩 모드 제거 실패: {str(e)}"
        )


@router.get("/system/status", response_model=AdminResponse)
async def get_system_status(_: bool = Depends(verify_admin_access)):
    """시스템 상태 조회"""
    try:
        stats = get_trading_statistics()
        
        # 키움 연결 상태 확인 (간단한 예시)
        kiwoom_connected = True  # 실제로는 연결 상태 확인 로직 필요
        
        system_status = SystemStatusResponse(
            system_mode="sandbox" if settings.KIWOOM_SANDBOX_MODE else "production",
            python_adapter_version="1.0.0",  # 실제 버전 정보
            active_users=stats['total_users'],
            sandbox_mode_users=stats['sandbox_mode_users'],
            production_mode_users=stats['production_mode_users'],
            default_mode=stats['default_mode'],
            uptime_seconds=0,  # 실제 업타임 계산 필요
            last_cleanup=None,  # 마지막 정리 시간
            kiwoom_connection_status=kiwoom_connected
        )
        
        return AdminResponse(
            success=True,
            message="시스템 상태 조회 성공",
            data=system_status.dict()
        )
        
    except Exception as e:
        logger.error("시스템 상태 조회 실패: error=%s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"시스템 상태 조회 실패: {str(e)}"
        )


@router.get("/users/configurations", response_model=AdminResponse)
async def get_all_user_configurations(_: bool = Depends(verify_admin_access)):
    """모든 사용자 설정 조회"""
    try:
        all_configs = user_trading_settings_manager.get_all_user_configs()
        
        config_list = []
        for user_id, config in all_configs.items():
            config_list.append(UserConfigResponse(
                user_id=config.user_id,
                sandbox_mode=config.sandbox_mode,
                kiwoom_account_id=config.kiwoom_account_id,
                max_daily_amount=config.max_daily_amount,
                risk_level=config.risk_level,
                auto_trading_enabled=config.auto_trading_enabled,
                notifications_enabled=config.notifications_enabled,
                updated_at=config.updated_at,
                expires_at=config.expires_at,
                is_expired=config.is_expired()
            ).dict())
        
        return AdminResponse(
            success=True,
            message=f"사용자 설정 {len(config_list)}개 조회 성공",
            data={
                "total_users": len(config_list),
                "configurations": config_list
            }
        )
        
    except Exception as e:
        logger.error("사용자 설정 목록 조회 실패: error=%s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"사용자 설정 조회 실패: {str(e)}"
        )


@router.post("/system/cleanup", response_model=AdminResponse)
async def cleanup_expired_configurations(_: bool = Depends(verify_admin_access)):
    """만료된 설정들 수동 정리"""
    try:
        cleaned_count = user_trading_settings_manager.cleanup_expired_configs()
        
        return AdminResponse(
            success=True,
            message=f"만료된 설정 {cleaned_count}개가 정리되었습니다",
            data={
                "cleaned_configurations": cleaned_count,
                "cleanup_time": datetime.now()
            }
        )
        
    except Exception as e:
        logger.error("설정 정리 실패: error=%s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"설정 정리 실패: {str(e)}"
        )


@router.post("/token-cache/invalidate/{user_id}", response_model=AdminResponse)
async def invalidate_user_token_cache(
    user_id: str,
    _: bool = Depends(verify_admin_access)
):
    """특정 사용자의 토큰 캐시 무효화"""
    try:
        await token_cache.invalidate_user_tokens(user_id)
        
        return AdminResponse(
            success=True,
            message=f"사용자 {user_id}의 토큰 캐시가 무효화되었습니다",
            data={
                "user_id": user_id,
                "invalidated_at": datetime.now()
            }
        )
        
    except Exception as e:
        logger.error("토큰 캐시 무효화 실패: user_id=%s, error=%s", user_id, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"토큰 캐시 무효화 실패: {str(e)}"
        )


@router.get("/health", response_model=AdminResponse)
async def admin_health_check():
    """관리자 API 헬스체크 (인증 불필요)"""
    return AdminResponse(
        success=True,
        message="관리자 API가 정상 동작 중입니다",
        data={
            "service": "kiwoom-adapter-admin",
            "version": "1.0.0",
            "timestamp": datetime.now()
        }
    )