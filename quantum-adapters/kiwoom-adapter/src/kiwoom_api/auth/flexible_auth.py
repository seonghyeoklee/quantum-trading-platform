"""
유연한 인증 시스템

조회성 API vs 주문성 API를 구분하여 다른 인증 전략 적용:
- 조회성: 고정 키 사용 (환경변수 기반)
- 주문성: 개별 토큰 인증 (Bearer Token 필수)
"""

import logging
from typing import Optional
from fastapi import Header, HTTPException, Depends
from enum import Enum

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from .token_validator import extract_bearer_token
except ImportError:
    import sys
    from pathlib import Path
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_validator import extract_bearer_token

logger = logging.getLogger(__name__)


class APIType(Enum):
    """API 유형 분류"""
    READ_ONLY = "read_only"      # 조회성 API (시세, 차트, 뉴스 등)
    TRADING = "trading"          # 주문성 API (주문, 계좌조회, 잔고 등)


class AuthenticationStrategy:
    """인증 전략 클래스"""
    
    @staticmethod
    def for_read_only_api() -> str:
        """
        조회성 API용 인증 - 고정 키 사용
        
        Returns:
            str: 환경변수에서 가져온 고정 키
            
        Raises:
            HTTPException: 키가 설정되지 않은 경우
        """
        if not settings.validate_keys():
            logger.error("키움 API 키가 설정되지 않았습니다")
            raise HTTPException(
                status_code=500,
                detail="서버 설정 오류: API 키가 구성되지 않았습니다"
            )
        
        # 현재 모드에 맞는 고정 키 반환
        app_key = settings.KIWOOM_APP_KEY
        logger.debug(f"조회성 API 인증 - 고정 키 사용: {app_key[:10]}***")
        return app_key
    
    @staticmethod
    def for_trading_api(authorization: str = Header(..., description="Bearer {access_token}")) -> str:
        """
        주문성 API용 인증 - 개별 토큰 필수
        
        Args:
            authorization: Authorization 헤더 (Bearer Token)
            
        Returns:
            str: 검증된 토큰
            
        Raises:
            HTTPException: 토큰이 유효하지 않은 경우
        """
        token = extract_bearer_token(authorization)
        logger.debug(f"주문성 API 인증 - 개별 토큰 사용: {token[:10]}***")
        return token


class FlexibleAuth:
    """유연한 인증 미들웨어"""
    
    @staticmethod
    def read_only_auth() -> str:
        """조회성 API 인증 의존성"""
        return AuthenticationStrategy.for_read_only_api()
    
    @staticmethod  
    def trading_auth(authorization: str = Header(...)) -> str:
        """주문성 API 인증 의존성"""
        return AuthenticationStrategy.for_trading_api(authorization)
    
    @staticmethod
    def optional_auth(authorization: Optional[str] = Header(None)) -> tuple[str, APIType]:
        """
        선택적 인증 - 토큰이 있으면 주문용, 없으면 조회용
        
        Args:
            authorization: 선택적 Authorization 헤더
            
        Returns:
            tuple: (인증키/토큰, API타입)
        """
        if authorization and authorization.startswith("Bearer "):
            # 토큰이 있으면 주문용 API로 처리
            try:
                token = extract_bearer_token(authorization)
                logger.info("선택적 인증: 주문용 토큰 사용")
                return token, APIType.TRADING
            except HTTPException:
                # 토큰이 잘못되었으면 에러
                logger.warning("잘못된 토큰으로 인한 인증 실패")
                raise
        else:
            # 토큰이 없으면 조회용 API로 처리  
            logger.info("선택적 인증: 조회용 고정키 사용")
            key = AuthenticationStrategy.for_read_only_api()
            return key, APIType.READ_ONLY


# 편의용 의존성 주입 함수들
def get_read_only_auth() -> str:
    """조회성 API 인증 (FastAPI Dependency)"""
    return FlexibleAuth.read_only_auth()


def get_trading_auth(authorization: str = Header(...)) -> str:
    """주문성 API 인증 (FastAPI Dependency)"""
    return FlexibleAuth.trading_auth(authorization)


def get_optional_auth(authorization: Optional[str] = Header(None)) -> tuple[str, APIType]:
    """선택적 인증 (FastAPI Dependency)"""
    return FlexibleAuth.optional_auth(authorization)