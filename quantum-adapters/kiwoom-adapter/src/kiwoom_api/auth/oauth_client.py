"""키움 OAuth 2.0 클라이언트

키움 API au10001 토큰 발급 기능 구현
사용자 제공 코드를 기반으로 한 키움 API 스펙 완전 준수
"""

import json
import logging
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import httpx

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..models.auth import TokenRequest, TokenResponse
    from ..models.common import KiwoomApiHeaders
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    from kiwoom_api.config.settings import settings
    from kiwoom_api.models.auth import TokenRequest, TokenResponse
    from kiwoom_api.models.common import KiwoomApiHeaders

logger = logging.getLogger(__name__)


class KiwoomOAuthClient:
    """키움증권 OAuth 2.0 클라이언트
    
    키움 API au10001 스펙에 완전히 맞춰진 토큰 발급 클라이언트
    """
    
    def __init__(self, app_key: str, app_secret: str, sandbox_mode: bool = True):
        self.app_key = app_key
        self.app_secret = app_secret
        self.sandbox_mode = sandbox_mode
        self.base_url = settings.kiwoom_base_url
        self.timeout = 30.0
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(
            f"키움 OAuth 클라이언트 초기화 - 모드: {settings.kiwoom_mode_description}, "
            f"앱키: {app_key}"
        )
    
    async def _get_client(self) -> httpx.AsyncClient:
        """AsyncClient 인스턴스 반환 (재사용)"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def _close_client(self) -> None:
        """AsyncClient 종료"""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        """async context manager 진입"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """async context manager 종료"""
        await self._close_client()
    
    async def request_token(self) -> TokenResponse:
        """키움 OAuth 2.0 토큰 발급 (au10001)
        
        사용자 제공 fn_au10001 함수를 기반으로 한 완전한 키움 API 스펙 구현
        
        Returns:
            TokenResponse: 키움 API 응답 (expires_dt, token_type, token, return_code, return_msg)
        """
        logger.info("키움 OAuth 토큰 발급 요청 시작")
        
        # 실제 키움 API 호출 (Mock 모드 제거)
        return await self._call_kiwoom_api()
    
    async def _call_kiwoom_api(self) -> TokenResponse:
        """실제 키움 API 호출 (사용자 제공 코드 기반)"""
        # 1. 요청할 API URL (사용자 코드와 동일)
        endpoint = "/oauth2/token"
        url = self.base_url + endpoint
        
        # 2. header 데이터 (사용자 코드와 동일)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
        }
        
        # 3. 요청 데이터 (사용자 코드와 동일)
        data = {
            'grant_type': 'client_credentials',
            'appkey': self.app_key,
            'secretkey': self.app_secret,
        }
        
        logger.info(f"키움 API 호출 - URL: {url}, 앱키: {self.app_key}")
        
        try:
            # 4. HTTP POST 요청 (AsyncClient 재사용)
            client = await self._get_client()
            response = await client.post(url, headers=headers, json=data)
            
            # 5. 응답 상태 코드와 데이터 출력 (사용자 코드 스타일 유지)
            logger.info(f"Code: {response.status_code}")
            
            # 응답 헤더 확인 (키움 API 스펙)
            response_headers = {
                key: response.headers.get(key) 
                for key in ['next-key', 'cont-yn', 'api-id']
            }
            logger.info(f"Header: {json.dumps(response_headers, indent=4, ensure_ascii=False)}")
            
            # 응답 처리
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Body: {json.dumps(response_data, indent=4, ensure_ascii=False)}")
                
                return TokenResponse(**response_data)
            else:
                error_msg = f"키움 API 호출 실패 - Status: {response.status_code}"
                logger.error(error_msg)
                return TokenResponse.create_error_response(
                    response.status_code,
                    f"키움 API 호출 실패: {error_msg}"
                )
                    
        except httpx.TimeoutException:
            error_msg = f"키움 API 호출 타임아웃 - {self.timeout}초"
            logger.error(error_msg)
            return TokenResponse.create_error_response(408, error_msg)
            
        except Exception as e:
            error_msg = f"키움 API 호출 중 오류 발생: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return TokenResponse.create_error_response(500, error_msg)
    


# 전역 OAuth 클라이언트 인스턴스 생성 함수
def create_oauth_client() -> KiwoomOAuthClient:
    """OAuth 클라이언트 생성"""
    return KiwoomOAuthClient(
        app_key=settings.KIWOOM_APP_KEY,
        app_secret=settings.KIWOOM_APP_SECRET,
        sandbox_mode=settings.KIWOOM_SANDBOX_MODE
    )