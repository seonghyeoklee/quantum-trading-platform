"""
백엔드 API와 통신하기 위한 HTTP 클라이언트 모듈
KIS 토큰 관리를 위해 백엔드의 JWT 기반 API를 호출합니다.
"""

import httpx
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendClient:
    """백엔드 API 클라이언트"""
    
    def __init__(self, base_url: str = None):
        """
        BackendClient 초기화
        
        Args:
            base_url: 백엔드 API 기본 URL (기본값: http://api.quantum-trading.com:8080)
        """
        self.base_url = base_url or os.getenv("BACKEND_API_URL", "http://api.quantum-trading.com:8080")
        self.timeout = 30.0  # 30초 타임아웃
        
    async def get_kis_token(self, authorization: str, environment: str = "LIVE") -> Optional[Dict[str, Any]]:
        """
        사용자의 현재 활성 KIS 토큰을 조회합니다.
        
        Args:
            authorization: JWT 토큰 ("Bearer <token>" 형식)
            environment: KIS 환경 ("LIVE" 또는 "SANDBOX")
            
        Returns:
            토큰 정보 딕셔너리 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": authorization,
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}/api/v1/kis/token/current"
                params = {"environment": environment}
                
                logger.info(f"Requesting KIS token from backend: {url}?environment={environment}")
                
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info(f"Successfully retrieved KIS token for environment: {environment}")
                    return token_data
                elif response.status_code == 404:
                    logger.warning(f"No KIS token found for environment: {environment}")
                    return None
                else:
                    logger.error(f"Failed to get KIS token: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Timeout while requesting KIS token from backend")
            return None
        except Exception as e:
            logger.error(f"Error getting KIS token: {str(e)}")
            return None
    
    async def get_token_status(self, authorization: str, environment: str = "LIVE") -> Optional[Dict[str, Any]]:
        """
        KIS 토큰의 상태를 확인합니다.
        
        Args:
            authorization: JWT 토큰 ("Bearer <token>" 형식)
            environment: KIS 환경 ("LIVE" 또는 "SANDBOX")
            
        Returns:
            토큰 상태 정보 딕셔너리 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": authorization,
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}/api/v1/kis/token/status"
                params = {"environment": environment}
                
                logger.info(f"Checking KIS token status: {url}?environment={environment}")
                
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    status_data = response.json()
                    logger.info(f"Successfully retrieved KIS token status for environment: {environment}")
                    return status_data
                else:
                    logger.error(f"Failed to get KIS token status: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Timeout while checking KIS token status")
            return None
        except Exception as e:
            logger.error(f"Error checking KIS token status: {str(e)}")
            return None
    
    async def refresh_kis_token(self, authorization: str, environment: str = "LIVE") -> Optional[Dict[str, Any]]:
        """
        KIS 토큰을 갱신합니다.
        
        Args:
            authorization: JWT 토큰 ("Bearer <token>" 형식)
            environment: KIS 환경 ("LIVE" 또는 "SANDBOX")
            
        Returns:
            갱신된 토큰 정보 딕셔너리 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "Authorization": authorization,
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}/api/v1/kis/token/refresh"
                data = {"environment": environment}
                
                logger.info(f"Refreshing KIS token: {url} for environment: {environment}")
                
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info(f"Successfully refreshed KIS token for environment: {environment}")
                    return token_data
                else:
                    logger.error(f"Failed to refresh KIS token: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Timeout while refreshing KIS token")
            return None
        except Exception as e:
            logger.error(f"Error refreshing KIS token: {str(e)}")
            return None

    def is_backend_available(self) -> bool:
        """
        백엔드 서버가 사용 가능한지 확인합니다.
        
        Returns:
            백엔드 서버 사용 가능 여부
        """
        try:
            import requests
            response = requests.get(f"{self.base_url}/actuator/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Backend server not available: {str(e)}")
            return False

# 전역 백엔드 클라이언트 인스턴스
backend_client = BackendClient()

def map_environment(svr: str) -> str:
    """
    KIS auth 환경 매개변수를 백엔드 API 환경으로 매핑합니다.
    
    Args:
        svr: KIS auth 환경 ("prod" 또는 "vps")
        
    Returns:
        백엔드 API 환경 ("LIVE" 또는 "SANDBOX")
    """
    if svr == "prod":
        return "LIVE"
    elif svr == "vps":
        return "SANDBOX"
    else:
        logger.warning(f"Unknown environment: {svr}, defaulting to LIVE")
        return "LIVE"

def get_authorization_header() -> str:
    """
    현재 요청의 Authorization 헤더를 가져옵니다.
    이 함수는 나중에 FastAPI의 request context에서 헤더를 추출하도록 수정될 예정입니다.
    
    Returns:
        Authorization 헤더 문자열
    """
    # TODO: FastAPI request context에서 실제 헤더 추출하도록 구현
    # 현재는 환경 변수나 기본값 사용
    return os.getenv("DEFAULT_JWT_TOKEN", "Bearer dummy-token")

async def get_kis_token_for_environment(svr: str, authorization: str = None) -> Optional[str]:
    """
    지정된 환경의 KIS 토큰을 가져옵니다.
    
    Args:
        svr: KIS auth 환경 ("prod" 또는 "vps")
        authorization: JWT 토큰 (옵션)
        
    Returns:
        KIS 액세스 토큰 또는 None
    """
    if authorization is None:
        authorization = get_authorization_header()
        
    environment = map_environment(svr)
    
    # 먼저 토큰 상태 확인
    status = await backend_client.get_token_status(authorization, environment)
    if status and status.get("hasToken") and status.get("isValid"):
        # 유효한 토큰이 있으면 조회
        token_data = await backend_client.get_kis_token(authorization, environment)
        if token_data:
            return token_data.get("token")
    
    # 토큰이 없거나 유효하지 않으면 갱신 시도
    logger.info(f"Attempting to refresh KIS token for environment: {environment}")
    token_data = await backend_client.refresh_kis_token(authorization, environment)
    if token_data:
        return token_data.get("token")
    
    return None