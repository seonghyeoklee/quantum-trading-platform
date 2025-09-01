"""
동적 모드 전환을 위한 설정 관리 모듈

요청별로 dry_run 파라미터에 따라 모의/실전 모드 설정을 동적으로 생성
환경변수 고정 의존성을 제거하고 유연한 모드 전환 지원
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class DynamicKiwoomConfig:
    """요청별 동적 키움 설정"""
    base_url: str
    app_key: str
    app_secret: str
    mode_description: str
    is_sandbox_mode: bool
    access_token: Optional[str] = None  # Java에서 전달된 액세스 토큰


class DynamicSettingsManager:
    """동적 모드 전환 설정 관리자"""
    
    @classmethod
    def get_config_from_dry_run(cls, dry_run: Optional[bool] = None) -> DynamicKiwoomConfig:
        """
        dry_run 파라미터에 따른 동적 키움 설정 생성
        
        Args:
            dry_run: True면 모의투자 모드, False면 실전투자 모드, None이면 환경변수 기본값 사용
            
        Returns:
            DynamicKiwoomConfig: 모드별 설정 객체
        """
        # dry_run 파라미터가 None이면 환경변수 기본값 사용
        if dry_run is None:
            is_sandbox = settings.KIWOOM_SANDBOX_MODE
            logger.info("🔧 dry_run 파라미터 없음 - 환경변수 기본값 사용")
        else:
            # dry_run=True면 모의투자(sandbox), dry_run=False면 실전투자
            is_sandbox = dry_run
            mode_text = "모의투자" if dry_run else "실전투자"
            logger.info(f"🎯 요청별 모드 전환: dry_run={dry_run} → {mode_text}")
        
        # 모드별 설정 생성
        if is_sandbox:
            # 모의투자 모드 설정
            base_url = "https://mockapi.kiwoom.com"
            app_key = settings.KIWOOM_SANDBOX_APP_KEY
            app_secret = settings.KIWOOM_SANDBOX_APP_SECRET
            mode_description = "샌드박스 (모의투자)"
        else:
            # 실전투자 모드 설정
            base_url = "https://api.kiwoom.com"
            app_key = settings.KIWOOM_PRODUCTION_APP_KEY
            app_secret = settings.KIWOOM_PRODUCTION_APP_SECRET
            mode_description = "실전투자"
        
        # 키 검증
        if not app_key or not app_secret:
            mode_name = "sandbox" if is_sandbox else "production"
            raise ValueError(f"{mode_name} 모드 API 키가 설정되지 않았습니다")
        
        config = DynamicKiwoomConfig(
            base_url=base_url,
            app_key=app_key,
            app_secret=app_secret,
            mode_description=mode_description,
            is_sandbox_mode=is_sandbox
        )
        
        logger.info(f"✅ 동적 설정 생성: {config.mode_description}")
        logger.info(f"📡 API URL: {config.base_url}")
        logger.info(f"🔑 API Key: {config.app_key[:20]}...")
        
        return config
    
    @classmethod
    def get_websocket_url(cls, is_sandbox_mode: bool) -> str:
        """모드별 WebSocket URL 반환"""
        if is_sandbox_mode:
            return "wss://mockapi.kiwoom.com:10000/api/dostk/websocket"
        return "wss://api.kiwoom.com:10000/api/dostk/websocket"
    
    @classmethod
    def extract_dry_run_from_request(cls, request_data: Dict[str, Any]) -> Optional[bool]:
        """
        요청 데이터에서 dry_run 파라미터 추출
        
        Args:
            request_data: API 요청 데이터
            
        Returns:
            Optional[bool]: dry_run 값 또는 None
        """
        # 다양한 형태의 dry_run 파라미터 지원
        dry_run_keys = ['dry_run', 'dryRun', 'dry-run', 'mock_mode']
        
        for key in dry_run_keys:
            if key in request_data:
                value = request_data[key]
                # boolean 타입 직접 사용
                if isinstance(value, bool):
                    return value
                # 문자열에서 boolean 변환
                elif isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                # 숫자에서 boolean 변환
                elif isinstance(value, (int, float)):
                    return bool(value)
        
        return None
    
    @classmethod
    def get_token_cache_key(cls, base_key: str, is_sandbox_mode: bool) -> str:
        """모드별 토큰 캐시 키 생성"""
        mode_suffix = "sandbox" if is_sandbox_mode else "production"
        return f"{base_key}_{mode_suffix}"
    
    @classmethod
    def extract_auth_info_from_request(cls, request_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Java에서 전달된 키움 인증 정보 추출
        
        Args:
            request_data: API 요청 데이터
            
        Returns:
            Tuple[access_token, app_key, app_secret, base_url]: 인증 정보 또는 None
        """
        access_token = request_data.get('kiwoom_access_token')
        app_key = request_data.get('kiwoom_app_key')
        app_secret = request_data.get('kiwoom_app_secret')
        base_url = request_data.get('kiwoom_base_url')
        
        # 로깅 (보안을 위해 키는 마스킹)
        if access_token or app_key:
            logger.info(f"🔑 Java에서 전달된 인증 정보 감지")
            if access_token:
                logger.debug(f"   액세스 토큰: {access_token[:10]}***")
            if app_key:
                logger.debug(f"   API 키: {app_key[:10]}***")
            if base_url:
                logger.debug(f"   베이스 URL: {base_url}")
        
        return access_token, app_key, app_secret, base_url
    
    @classmethod
    def get_config_from_request(cls, request_data: Dict[str, Any]) -> DynamicKiwoomConfig:
        """
        요청 데이터에서 완전한 동적 설정 생성 (Java 인증 정보 우선)
        
        Args:
            request_data: API 요청 데이터
            
        Returns:
            DynamicKiwoomConfig: 완전한 설정 객체
        """
        # 1. dry_run 추출
        dry_run = cls.extract_dry_run_from_request(request_data)
        
        # 2. Java 인증 정보 추출
        access_token, java_app_key, java_app_secret, java_base_url = cls.extract_auth_info_from_request(request_data)
        
        # 3. Java 인증 정보가 있으면 우선 사용, 없으면 환경변수 기반 설정 사용
        if java_app_key and java_app_secret and java_base_url:
            logger.info("✅ Java 전달 인증 정보 사용 - 환경변수 의존성 제거됨")
            
            # 모드 판단 (base_url로부터)
            is_sandbox_mode = "mock" in java_base_url.lower()
            mode_description = "모의투자 (Java 전달)" if is_sandbox_mode else "실전투자 (Java 전달)"
            
            config = DynamicKiwoomConfig(
                base_url=java_base_url,
                app_key=java_app_key,
                app_secret=java_app_secret,
                mode_description=mode_description,
                is_sandbox_mode=is_sandbox_mode,
                access_token=access_token
            )
            
            logger.info(f"🚀 Java 통합 모드: {config.mode_description}")
            logger.info(f"📡 Base URL: {config.base_url}")
            
        else:
            logger.info("⚠️ Java 인증 정보 없음 - 환경변수 기반 설정 사용 (Fallback)")
            # 기존 환경변수 기반 설정 사용
            config = cls.get_config_from_dry_run(dry_run)
            if access_token:
                config.access_token = access_token
        
        return config


# 전역 함수로 편의성 제공
def get_dynamic_config(dry_run: Optional[bool] = None) -> DynamicKiwoomConfig:
    """dry_run 파라미터에 따른 동적 설정 생성"""
    return DynamicSettingsManager.get_config_from_dry_run(dry_run)


def get_config_from_request(request_data: Dict[str, Any]) -> DynamicKiwoomConfig:
    """요청 데이터에서 완전한 동적 설정 생성 (Java 인증 정보 우선)"""
    return DynamicSettingsManager.get_config_from_request(request_data)


def extract_dry_run(request_data: Dict[str, Any]) -> Optional[bool]:
    """요청 데이터에서 dry_run 추출"""
    return DynamicSettingsManager.extract_dry_run_from_request(request_data)


def get_mode_description(dry_run: Optional[bool]) -> str:
    """모드 설명 반환"""
    if dry_run is None:
        return "환경변수 기본값"
    return "모의투자" if dry_run else "실전투자"