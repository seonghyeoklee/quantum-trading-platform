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


async def fn_au10001(data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    키움증권 접근토큰 발급 (au10001)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        data: 토큰 발급 요청 데이터 (선택적)
              - grant_type: client_credentials (기본값)
              - appkey: 앱키 (환경변수에서 자동 설정)
              - secretkey: 시크릿키 (환경변수에서 자동 설정)

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> result = await fn_au10001()
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['token']}")
    """
    logger.info("🔑 키움 접근토큰 발급 시작 (au10001)")

    try:
        # 1. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/oauth2/token'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 2. 요청 데이터 준비 (환경변수 기반 자동 설정)
        if data is None:
            data = {}

        # 기본값 설정 (키움 API 스펙)
        params = {
            'grant_type': data.get('grant_type', 'client_credentials'),
            'appkey': data.get('appkey', settings.KIWOOM_APP_KEY),
            'secretkey': data.get('secretkey', settings.KIWOOM_APP_SECRET),
        }

        logger.info(f"🔑 앱키: {params['appkey']}")
        logger.info(f"📋 grant_type: {params['grant_type']}")

        # 3. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
        }

        # 4. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
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


async def get_valid_access_token() -> str:
    """
    유효한 Access Token을 반환하는 의존성 함수
    
    캐시된 토큰이 있고 유효하면 반환, 없으면 새로 발급
    
    Returns:
        str: 유효한 access token
        
    Raises:
        HTTPException: 토큰 발급 실패 시
    """
    try:
        # 1. 캐시된 토큰 확인
        cached_token = await token_cache.get_cached_token(settings.KIWOOM_APP_KEY)
        if cached_token and cached_token.is_valid():
            logger.info(f"✅ 캐시된 토큰 사용: {cached_token.token[:20]}...")
            return cached_token.token
        
        # 2. 새 토큰 발급
        logger.info("🔄 새 토큰 발급 중...")
        result = await fn_au10001()
        
        if result['Code'] != 200:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401, 
                detail=f"토큰 발급 실패: {result.get('Body', {}).get('error', '알 수 없는 오류')}"
            )
        
        token = result['Body'].get('token')
        if not token:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="토큰이 응답에 없습니다")
        
        logger.info(f"✅ 새 토큰 발급 성공: {token[:20]}...")
        return token
        
    except Exception as e:
        logger.error(f"❌ 토큰 발급 실패: {str(e)}")
        from fastapi import HTTPException
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"토큰 발급 중 오류: {str(e)}")


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