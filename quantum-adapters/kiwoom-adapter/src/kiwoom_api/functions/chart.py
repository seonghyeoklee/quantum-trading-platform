"""
키움 API 차트 관련 함수들

키움 API 스펙에 완전히 맞춰진 차트 함수 구현
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
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.config.settings import settings

logger = logging.getLogger(__name__)


async def fn_ka10081(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """
    키움증권 주식일봉차트조회 (ka10081)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        data: 차트조회 요청 데이터
              - stk_cd: 종목코드 (예: '005930')
              - base_dt: 기준일자 YYYYMMDD (예: '20250820')
              - upd_stkpc_tp: 수정주가구분 ('0' or '1')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: 접근토큰 (선택적, 없으면 자동 관리)

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> params = {
        ...     'stk_cd': '005930',
        ...     'base_dt': '20250820',
        ...     'upd_stkpc_tp': '1'
        ... }
        >>> result = await fn_ka10081(data=params)
        >>> print(f"Code: {result['Code']}")
    """
    logger.info("📈 키움 주식일봉차트조회 시작 (ka10081)")

    try:
        # 0. 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager

        # 유효한 토큰 자동 획득
        valid_token = await token_manager.ensure_token_valid(token)
        logger.info(f"🔑 사용할 토큰: {valid_token[:20]}...")
        # 1. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 2. 요청 데이터 검증
        required_fields = ['stk_cd', 'base_dt', 'upd_stkpc_tp']
        for field in required_fields:
            if not data.get(field):
                error_msg = f"필수 파라미터 누락: {field}"
                logger.error(error_msg)
                return {
                    'Code': 400,
                    'Header': {'api-id': 'ka10081', 'cont-yn': 'N', 'next-key': ''},
                    'Body': {'error': error_msg}
                }

        logger.info(f"📊 종목코드: {data['stk_cd']}")
        logger.info(f"📅 기준일자: {data['base_dt']}")
        logger.info(f"🔧 수정주가구분: {data['upd_stkpc_tp']}")
        logger.info(f"🔄 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔑 연속조회키: {next_key[:20]}...")

        # 3. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {valid_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10081',
        }

        # 4. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=data)

        # 5. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10081')
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

        return result

    except Exception as e:
        error_msg = f"키움 주식일봉차트조회 실패 (ka10081): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10081', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10080(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """
    키움증권 주식분봉차트조회 (ka10080)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        data: 차트조회 요청 데이터
              - stk_cd: 종목코드 (예: '005930')
              - tic_scope: 틱범위 ('1':1분, '3':3분, '5':5분, '10':10분, '15':15분, '30':30분, '45':45분, '60':60분)
              - upd_stkpc_tp: 수정주가구분 ('0' or '1')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: 접근토큰 (선택적, 없으면 자동 관리)

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> params = {
        ...     'stk_cd': '005930',
        ...     'tic_scope': '1',
        ...     'upd_stkpc_tp': '1'
        ... }
        >>> result = await fn_ka10080(data=params)
        >>> print(f"Code: {result['Code']}")
    """
    logger.info("📊 키움 주식분봉차트조회 시작 (ka10080)")

    try:
        # 0. 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager

        # 유효한 토큰 자동 획득
        valid_token = await token_manager.ensure_token_valid(token)
        logger.info(f"🔑 사용할 토큰: {valid_token[:20]}...")

        # 1. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 2. 요청 데이터 검증
        required_fields = ['stk_cd', 'tic_scope', 'upd_stkpc_tp']
        for field in required_fields:
            if not data.get(field):
                error_msg = f"필수 파라미터 누락: {field}"
                logger.error(error_msg)
                return {
                    'Code': 400,
                    'Header': {'api-id': 'ka10080', 'cont-yn': 'N', 'next-key': ''},
                    'Body': {'error': error_msg}
                }

        logger.info(f"📊 종목코드: {data['stk_cd']}")
        logger.info(f"⏱️ 틱범위: {data['tic_scope']}분")
        logger.info(f"🔧 수정주가구분: {data['upd_stkpc_tp']}")
        logger.info(f"🔄 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔑 연속조회키: {next_key[:20]}...")

        # 3. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {valid_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10080',
        }

        # 4. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=data)

        # 5. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10080')
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

        return result

    except Exception as e:
        error_msg = f"키움 주식분봉차트조회 실패 (ka10080): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10080', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10082(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """
    키움증권 주식주봉차트조회 (ka10082)
    
    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현
    
    Args:
        data: 차트조회 요청 데이터
              - stk_cd: 종목코드 (예: '005930')
              - base_dt: 기준일자 YYYYMMDD (예: '20241108')
              - upd_stkpc_tp: 수정주가구분 ('0' or '1')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: 접근토큰 (선택적, 없으면 자동 관리)
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디
    
    Example:
        >>> params = {
        ...     'stk_cd': '005930',
        ...     'base_dt': '20241108',
        ...     'upd_stkpc_tp': '1'
        ... }
        >>> result = await fn_ka10082(data=params)
        >>> print(f"Code: {result['Code']}")
    """
    logger.info("📊 키움 주식주봉차트조회 시작 (ka10082)")
    
    try:
        # 0. 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        # 유효한 토큰 자동 획득
        valid_token = await token_manager.ensure_token_valid(token)
        logger.info(f"🔑 사용할 토큰: {valid_token[:20]}...")
        
        # 1. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")
        
        # 2. 요청 데이터 검증
        required_fields = ['stk_cd', 'base_dt', 'upd_stkpc_tp']
        for field in required_fields:
            if not data.get(field):
                error_msg = f"필수 파라미터 누락: {field}"
                logger.error(error_msg)
                return {
                    'Code': 400,
                    'Header': {'api-id': 'ka10082', 'cont-yn': 'N', 'next-key': ''},
                    'Body': {'error': error_msg}
                }
        
        logger.info(f"📊 종목코드: {data['stk_cd']}")
        logger.info(f"📅 기준일자: {data['base_dt']}")
        logger.info(f"🔧 수정주가구분: {data['upd_stkpc_tp']}")
        logger.info(f"🔄 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔑 연속조회키: {next_key[:20]}...")
        
        # 3. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {valid_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10082',
        }
        
        # 4. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 5. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10082')
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
        
        return result
        
    except Exception as e:
        error_msg = f"키움 주식주봉차트조회 실패 (ka10082): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10082', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10094(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """
    키움증권 주식년봉차트조회 (ka10094)
    
    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현
    
    Args:
        data: 차트조회 요청 데이터
              - stk_cd: 종목코드 (예: '005930')
              - base_dt: 기준일자 YYYYMMDD (예: '20241212')
              - upd_stkpc_tp: 수정주가구분 ('0' or '1')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: 접근토큰 (선택적, 없으면 자동 관리)
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디
    
    Example:
        >>> params = {
        ...     'stk_cd': '005930',
        ...     'base_dt': '20241212',
        ...     'upd_stkpc_tp': '1'
        ... }
        >>> result = await fn_ka10094(data=params)
        >>> print(f"Code: {result['Code']}")
    """
    logger.info("📊 키움 주식년봉차트조회 시작 (ka10094)")
    
    try:
        # 0. 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        # 유효한 토큰 자동 획득
        valid_token = await token_manager.ensure_token_valid(token)
        logger.info(f"🔑 사용할 토큰: {valid_token[:20]}...")
        
        # 1. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")
        
        # 2. 요청 데이터 검증
        required_fields = ['stk_cd', 'base_dt', 'upd_stkpc_tp']
        for field in required_fields:
            if not data.get(field):
                error_msg = f"필수 파라미터 누락: {field}"
                logger.error(error_msg)
                return {
                    'Code': 400,
                    'Header': {'api-id': 'ka10094', 'cont-yn': 'N', 'next-key': ''},
                    'Body': {'error': error_msg}
                }
        
        logger.info(f"📊 종목코드: {data['stk_cd']}")
        logger.info(f"📅 기준일자: {data['base_dt']}")
        logger.info(f"🔧 수정주가구분: {data['upd_stkpc_tp']}")
        logger.info(f"🔄 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔑 연속조회키: {next_key[:20]}...")
        
        # 3. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {valid_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10094',
        }
        
        # 4. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 5. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10094')
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
        
        return result
        
    except Exception as e:
        error_msg = f"키움 주식년봉차트조회 실패 (ka10094): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10094', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10079(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """
    키움증권 주식틱차트조회 (ka10079)
    
    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현
    
    Args:
        data: 차트조회 요청 데이터
              - stk_cd: 종목코드 (예: '005930')
              - tic_scope: 틱범위 ('1':1틱, '3':3틱, '5':5틱, '10':10틱, '30':30틱)
              - upd_stkpc_tp: 수정주가구분 ('0' or '1')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: 접근토큰 (선택적, 없으면 자동 관리)
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디
    
    Example:
        >>> params = {
        ...     'stk_cd': '005930',
        ...     'tic_scope': '1',
        ...     'upd_stkpc_tp': '1'
        ... }
        >>> result = await fn_ka10079(data=params)
        >>> print(f"Code: {result['Code']}")
    """
    logger.info("📊 키움 주식틱차트조회 시작 (ka10079)")
    
    try:
        # 0. 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        # 유효한 토큰 자동 획득
        valid_token = await token_manager.ensure_token_valid(token)
        logger.info(f"🔑 사용할 토큰: {valid_token[:20]}...")
        
        # 1. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")
        
        # 2. 요청 데이터 검증
        required_fields = ['stk_cd', 'tic_scope', 'upd_stkpc_tp']
        for field in required_fields:
            if not data.get(field):
                error_msg = f"필수 파라미터 누락: {field}"
                logger.error(error_msg)
                return {
                    'Code': 400,
                    'Header': {'api-id': 'ka10079', 'cont-yn': 'N', 'next-key': ''},
                    'Body': {'error': error_msg}
                }
        
        logger.info(f"📊 종목코드: {data['stk_cd']}")
        logger.info(f"⚡ 틱범위: {data['tic_scope']}틱")
        logger.info(f"🔧 수정주가구분: {data['upd_stkpc_tp']}")
        logger.info(f"🔄 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔑 연속조회키: {next_key[:20]}...")
        
        # 3. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {valid_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10079',
        }
        
        # 4. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 5. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10079')
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
        
        return result
        
    except Exception as e:
        error_msg = f"키움 주식틱차트조회 실패 (ka10079): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10079', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka20004(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 업종틱차트조회 (ka20004)
    
    키움 API 스펙에 완전히 맞춘 업종틱차트조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
              - tic_scope: 틱범위 ('1':1틱, '3':3틱, '5':5틱, '10':10틱, '30':30틱)
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (업종틱차트 데이터)
    """
    logger.info(f"🚀 키움 업종틱차트조회 시작 - ka20004")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka20004',
        }
        
        logger.info(f"📡 키움 API 호출 - ka20004: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka20004')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 업종틱차트조회 실패 (ka20004): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka20004', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10060(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 종목별투자자기관별차트조회 (ka10060)
    
    키움 API 스펙에 완전히 맞춘 종목별투자자기관별차트조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - dt: 일자 YYYYMMDD (예: '20241107')
              - stk_cd: 종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)
              - amt_qty_tp: 금액수량구분 ('1':금액, '2':수량)
              - trde_tp: 매매구분 ('0':순매수, '1':매수, '2':매도)
              - unit_tp: 단위구분 ('1000':천주, '1':단주)
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (투자자기관별차트 데이터)
    """
    logger.info(f"🚀 키움 종목별투자자기관별차트조회 시작 - ka10060")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10060',
        }
        
        logger.info(f"📡 키움 API 호출 - ka10060: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10060')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 종목별투자자기관별차트조회 실패 (ka10060): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10060', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10064(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 장중투자자별매매차트조회 (ka10064)
    
    키움 API 스펙에 완전히 맞춘 장중투자자별매매차트조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - mrkt_tp: 시장구분 ('000':전체, '001':코스피, '101':코스닥)
              - amt_qty_tp: 금액수량구분 ('1':금액, '2':수량)
              - trde_tp: 매매구분 ('0':순매수, '1':매수, '2':매도)
              - stk_cd: 종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (장중투자자별매매차트 데이터)
    """
    logger.info(f"🚀 키움 장중투자자별매매차트조회 시작 - ka10064")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10064',
        }
        
        logger.info(f"📡 키움 API 호출 - ka10064: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10064')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 장중투자자별매매차트조회 실패 (ka10064): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10064', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka20005(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 업종분봉조회 (ka20005)
    
    키움 API 스펙에 완전히 맞춘 업종분봉조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
              - tic_scope: 틱범위 ('1':1분, '3':3분, '5':5분, '10':10분, '30':30분)
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (업종분봉차트 데이터)
    """
    logger.info(f"🚀 키움 업종분봉조회 시작 - ka20005")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka20005',
        }
        
        logger.info(f"📡 키움 API 호출 - ka20005: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka20005')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 업종분봉조회 실패 (ka20005): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka20005', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka20006(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 업종일봉조회 (ka20006)
    
    키움 API 스펙에 완전히 맞춘 업종일봉조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
              - base_dt: 기준일자 YYYYMMDD (예: '20241122')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (업종일봉차트 데이터)
    """
    logger.info(f"🚀 키움 업종일봉조회 시작 - ka20006")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka20006',
        }
        
        logger.info(f"📡 키움 API 호출 - ka20006: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka20006')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 업종일봉조회 실패 (ka20006): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka20006', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka20007(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 업종주봉조회 (ka20007)
    
    키움 API 스펙에 완전히 맞춘 업종주봉조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
              - base_dt: 기준일자 YYYYMMDD (예: '20241122')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (업종주봉차트 데이터)
    """
    logger.info(f"🚀 키움 업종주봉조회 시작 - ka20007")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka20007',
        }
        
        logger.info(f"📡 키움 API 호출 - ka20007: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka20007')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 업종주봉조회 실패 (ka20007): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka20007', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka20008(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 업종월봉조회 (ka20008)
    
    키움 API 스펙에 완전히 맞춘 업종월봉조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
              - base_dt: 기준일자 YYYYMMDD (예: '20241122')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (업종월봉차트 데이터)
    """
    logger.info(f"🚀 키움 업종월봉조회 시작 - ka20008")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka20008',
        }
        
        logger.info(f"📡 키움 API 호출 - ka20008: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka20008')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 업종월봉조회 실패 (ka20008): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka20008', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka20019(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 업종년봉조회 (ka20019)
    
    키움 API 스펙에 완전히 맞춘 업종년봉조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
              - base_dt: 기준일자 YYYYMMDD (예: '20241122')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (업종년봉차트 데이터)
    """
    logger.info(f"🚀 키움 업종년봉조회 시작 - ka20019")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka20019',
        }
        
        logger.info(f"📡 키움 API 호출 - ka20019: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka20019')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 업종년봉조회 실패 (ka20019): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka20019', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10083(data: Dict[str, Any], cont_yn: str = 'N', next_key: str = '', token: Optional[str] = None) -> Dict[str, Any]:
    """키움증권 주식월봉차트조회 (ka10083)
    
    키움 API 스펙에 완전히 맞춘 주식월봉차트조회 함수
    토큰을 자동으로 관리하고 응답 형식을 원본과 동일하게 유지
    
    Args:
        data: 차트조회 파라미터 딕셔너리
              - stk_cd: 종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)
              - base_dt: 기준일자 YYYYMMDD (예: '20241108')
              - upd_stkpc_tp: 수정주가구분 ('0' or '1')
        cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
        next_key: 연속조회키 (기본값: '')
        token: Bearer 토큰 (None일 경우 자동 관리)
        
    Returns:
        Dict[str, Any]: 키움 API 응답과 동일한 형식
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (next-key, cont-yn, api-id)
        - Body: 키움 API 응답 바디 (주식월봉차트 데이터)
    """
    logger.info(f"🚀 키움 주식월봉차트조회 시작 - ka10083")
    
    try:
        # 토큰 자동 관리
        try:
            from ..auth.token_manager import token_manager
        except ImportError:
            from kiwoom_api.auth.token_manager import token_manager
        
        access_token = await token_manager.ensure_token_valid(token)
        
        # API 요청 설정
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/chart'
        url = host + endpoint
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {access_token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10083',
        }
        
        logger.info(f"📡 키움 API 호출 - ka10083: {data}")
        
        # HTTP POST 요청
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(url, headers=headers, json=data)
        
        # 응답 헤더 추출 (키움 스타일)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10083')
        }
        
        # 응답 데이터 파싱
        try:
            response_body = response.json()
        except ValueError:
            response_body = {"error": "Invalid JSON response", "raw": response.text}
        
        # 원본과 동일한 응답 형식 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
        # 디버깅용 로그 출력 (사용자 코드 스타일)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        error_msg = f"키움 주식월봉차트조회 실패 (ka10083): {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10083', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }