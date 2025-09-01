"""
키움 API 인증 관련 함수들

키움 API 스펙에 완전히 맞춰진 인증 함수 구현
fn_{api_id} 형태로 명명하여 키움 문서와 1:1 매핑
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import httpx

# Handle both relative and absolute imports for different execution contexts
try:
    from ..config.settings import settings
    from ..auth.token_cache import token_cache
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.config.settings import settings
    from kiwoom_api.auth.token_cache import token_cache

logger = logging.getLogger(__name__)

# Global client instance for reuse
_client: Optional[httpx.AsyncClient] = None


async def _get_client() -> httpx.AsyncClient:
    """AsyncClient 인스턴스 반환 (재사용)"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def _close_client() -> None:
    """AsyncClient 종료"""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def fn_au10001(
    app_key: str,
    app_secret: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    키움증권 접근토큰 발급 (au10001)
    환경변수 의존성 제거 - Java에서 키 전달받음

    Args:
        app_key: 키움 앱키 (Java에서 모드별로 선택해서 전달)
        app_secret: 키움 앱시크릿 (Java에서 모드별로 선택해서 전달)
        data: 토큰 발급 요청 데이터 (선택적)
              - grant_type: client_credentials (기본값)

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디 (access_token 포함)

    Example:
        >>> result = await fn_au10001("sandbox_key", "sandbox_secret")
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['access_token']}")
    """
    logger.info("🔑 키움 접근토큰 발급 시작 (au10001)")

    try:
        # 1. 모드 판단 (전달받은 키로부터)
        is_sandbox = "sandbox" in app_key.lower() or "mock" in app_key.lower()
        mode_desc = "모의투자 (Sandbox)" if is_sandbox else "실전투자 (Real)"
        
        # 2. 요청할 API URL 구성 (키 기반 자동 결정)
        host = "https://mockapi.kiwoom.com" if is_sandbox else "https://api.kiwoom.com"
        endpoint = '/oauth2/token'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {mode_desc}")

        # 3. 요청 데이터 준비 (Java에서 전달받은 키 사용)
        if data is None:
            data = {}

        # Java에서 전달받은 키 사용 (환경변수 의존성 완전 제거)
        params = {
            'grant_type': data.get('grant_type', 'client_credentials'),
            'appkey': app_key,      # Java에서 전달받은 키
            'secretkey': app_secret  # Java에서 전달받은 시크릿
        }

        logger.info(f"🔑 앱키: {app_key[:20]}*** (Java에서 전달)")
        logger.info(f"📋 grant_type: {params['grant_type']}")

        # 3. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
        }

        # 4. HTTP POST 요청 (AsyncClient 재사용)
        client = await _get_client()
        response = await client.post(url, headers=headers, json=params)

        # 5. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'au10001')
        }

        # 6. 응답 데이터 구성 (사용자 코드와 동일한 형태)
        result = {
            'Code': response.status_code,
            'Header': api_headers,
            'Body': response.json() if response.content else {}
        }

        # 7. 로깅 (사용자 코드와 동일한 형태)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")

        # 8. 성공한 경우 토큰 캐싱
        if result['Code'] == 200 and result['Body'].get('token'):
            await _cache_token_from_au10001_response(result['Body'])

        return result

    except Exception as e:
        error_msg = f"키움 접근토큰 발급 실패 (au10001): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'au10001', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }



async def get_access_token() -> Dict[str, Any]:
    """
    키움 OAuth2 토큰 발급 (호환성을 위한 래퍼 함수)
    
    Returns:
        Dict: 토큰 정보가 담긴 딕셔너리
    """
    result = await fn_au10001()
    if result['Code'] == 200:
        return result['Body']
    else:
        raise Exception(f"토큰 발급 실패: {result}")


async def _cache_token_from_au10001_response(body: Dict[str, Any]) -> None:
    """fn_au10001 응답에서 토큰을 캐시에 저장"""
    try:
        if not body.get('token'):
            return

        from datetime import datetime, timedelta

        try:
            from ..models.auth import CachedTokenInfo
        except ImportError:
            from kiwoom_api.models.auth import CachedTokenInfo

        # 만료시간 파싱 (키움 API 형식: YYYYMMDDHHMMSS)
        expires_dt = body.get('expires_dt', '')
        try:
            if expires_dt and len(expires_dt) == 14:
                expires_at = datetime.strptime(expires_dt, "%Y%m%d%H%M%S")
            else:
                expires_at = datetime.now() + timedelta(hours=24)  # 기본값
        except:
            expires_at = datetime.now() + timedelta(hours=24)  # 기본값

        # 캐시 정보 생성
        cached_token = CachedTokenInfo(
            app_key=settings.KIWOOM_APP_KEY,
            token=body['token'],
            expires_dt=expires_dt,
            issued_at=datetime.now(),
            expires_at=expires_at
        )

        # 캐시 저장
        await token_cache.cache_token(cached_token)
        logger.info(f"✅ fn_au10001 토큰 캐싱 완료 - 만료시간: {expires_at}")

    except Exception as e:
        logger.warning(f"⚠️ fn_au10001 토큰 캐싱 실패 (계속 진행): {str(e)}")