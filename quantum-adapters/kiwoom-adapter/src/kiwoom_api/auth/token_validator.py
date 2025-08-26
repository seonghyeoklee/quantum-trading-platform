"""
토큰 검증 유틸리티

Java Backend로부터 전달받은 Bearer 토큰을 검증하는 함수들
기존 OAuth 자체 발급 방식에서 토큰 전달받는 방식으로 변경
"""

import logging
from typing import Optional
from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


def extract_bearer_token(authorization: str = Header(..., description="Bearer {access_token}")) -> str:
    """
    Authorization 헤더에서 Bearer 토큰을 추출하고 기본 검증 수행
    
    Args:
        authorization: Authorization 헤더 값 ("Bearer {token}" 형식)
        
    Returns:
        str: 추출된 access token
        
    Raises:
        HTTPException: 토큰이 유효하지 않을 때
    """
    try:
        # 1. Bearer 접두사 확인
        if not authorization.startswith("Bearer "):
            logger.warning(f"Invalid authorization header format: {authorization[:20]}...")
            raise HTTPException(
                status_code=401, 
                detail="Authorization header must start with 'Bearer '"
            )
        
        # 2. 토큰 추출
        token = authorization.split("Bearer ")[1].strip()
        
        # 3. 기본 토큰 검증
        if not token:
            logger.warning("Empty token in authorization header")
            raise HTTPException(
                status_code=401, 
                detail="Token is required"
            )
        
        # 4. 토큰 길이 검증 (기본적인 형식 체크)
        if len(token) < 10:
            logger.warning(f"Token too short: {len(token)} characters")
            raise HTTPException(
                status_code=401, 
                detail="Invalid token format"
            )
        
        logger.debug(f"✅ Valid token extracted: {token[:20]}...")
        return token
        
    except HTTPException:
        # HTTPException은 그대로 전파
        raise
    except Exception as e:
        logger.error(f"Unexpected error in token extraction: {str(e)}")
        raise HTTPException(
            status_code=401, 
            detail="Invalid authorization header"
        )


def validate_token_format(token: str) -> bool:
    """
    토큰 형식에 대한 추가 검증
    
    Args:
        token: 검증할 access token
        
    Returns:
        bool: 토큰이 유효한 형식이면 True
    """
    try:
        # 기본 길이 검증
        if len(token) < 10:
            return False
        
        # 특수문자 허용 (키움 토큰 특성)
        # 일반적으로 JWT나 OAuth 토큰은 영문, 숫자, 특수문자 조합
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~:/?#[]@!$&\'()*+,;=')
        if not all(c in allowed_chars for c in token):
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error validating token format: {str(e)}")
        return False


class TokenValidator:
    """
    토큰 검증을 위한 클래스 (고급 검증이 필요할 경우 사용)
    """
    
    @staticmethod
    def extract_and_validate(authorization: str = Header(...)) -> str:
        """
        토큰 추출과 형식 검증을 모두 수행
        
        Args:
            authorization: Authorization 헤더
            
        Returns:
            str: 검증된 토큰
        """
        token = extract_bearer_token(authorization)
        
        if not validate_token_format(token):
            logger.warning(f"Token format validation failed: {token[:20]}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid token format"
            )
        
        return token
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """
        토큰 만료 여부 확인 (필요시 구현)
        현재는 기본 구현으로 False 반환
        
        Args:
            token: 확인할 토큰
            
        Returns:
            bool: 만료되었으면 True (현재는 항상 False)
        """
        # NOTE: 키움 API는 JWT가 아닌 OAuth2 토큰을 사용하므로
        # 실제 토큰 만료 검증은 키움 API 호출 시 401 응답으로 판단
        # 현재는 기본값으로 False 반환 (만료되지 않음으로 가정)
        return False