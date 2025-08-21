"""
키움 API 종목정보 관련 함수들

키움 API 스펙에 완전히 맞춰진 종목정보 함수 구현
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
    from ..functions.auth import get_valid_access_token
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.config.settings import settings
    from kiwoom_api.functions.auth import get_valid_access_token

logger = logging.getLogger(__name__)


async def fn_ka10001(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 주식기본정보요청 (ka10001)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stk_cd: 종목코드 (거래소별 종목코드)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> result = await fn_ka10001(data={"stk_cd": "005930"})
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['stk_nm']}")
    """
    logger.info("🏢 키움 종목기본정보 요청 시작 (ka10001)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None or not data.get('stk_cd'):
            raise ValueError("종목코드(stk_cd)가 필요합니다")

        stk_cd = data['stk_cd']
        logger.info(f"📊 종목코드: {stk_cd}")

        # 3. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/stkinfo'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10001',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비
        request_data = {
            'stk_cd': stk_cd
        }

        # 6. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10001')
        }

        # 8. 응답 데이터 구성 (사용자 코드와 동일한 형태)
        result = {
            'Code': response.status_code,
            'Header': api_headers,
            'Body': response.json() if response.content else {}
        }

        # 9. 로깅 (사용자 코드와 동일한 형태)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")

        return result

    except Exception as e:
        error_msg = f"키움 종목기본정보 요청 실패 (ka10001): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10001', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10099(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 종목정보 리스트 (ka10099)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - mrkt_tp: 시장구분 (0:코스피,10:코스닥,3:ELW,8:ETF,30:K-OTC,50:코넥스,5:신주인수권,4:뮤추얼펀드,6:리츠,9:하이일드)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> result = await fn_ka10099(data={"mrkt_tp": "0"})
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['list']}")
    """
    logger.info("🏢 키움 종목정보 리스트 요청 시작 (ka10099)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None or not data.get('mrkt_tp'):
            raise ValueError("시장구분(mrkt_tp)이 필요합니다")

        mrkt_tp = data['mrkt_tp']
        logger.info(f"📊 시장구분: {mrkt_tp}")

        # 3. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/stkinfo'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10099',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비
        request_data = {
            'mrkt_tp': mrkt_tp
        }

        # 6. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10099')
        }

        # 8. 응답 데이터 구성 (사용자 코드와 동일한 형태)
        result = {
            'Code': response.status_code,
            'Header': api_headers,
            'Body': response.json() if response.content else {}
        }

        # 9. 로깅 (사용자 코드와 동일한 형태)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")

        return result

    except Exception as e:
        error_msg = f"키움 종목정보 리스트 요청 실패 (ka10099): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10099', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10100(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 종목정보 조회 (ka10100)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stk_cd: 종목코드 (6자리)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> result = await fn_ka10100(data={"stk_cd": "005930"})
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['name']}")
    """
    logger.info("🏢 키움 종목정보 조회 시작 (ka10100)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None or not data.get('stk_cd'):
            raise ValueError("종목코드(stk_cd)가 필요합니다")

        stk_cd = data['stk_cd']
        logger.info(f"📊 종목코드: {stk_cd}")

        # 3. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/stkinfo'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10100',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비
        request_data = {
            'stk_cd': stk_cd
        }

        # 6. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10100')
        }

        # 8. 응답 데이터 구성 (사용자 코드와 동일한 형태)
        result = {
            'Code': response.status_code,
            'Header': api_headers,
            'Body': response.json() if response.content else {}
        }

        # 9. 로깅 (사용자 코드와 동일한 형태)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")

        return result

    except Exception as e:
        error_msg = f"키움 종목정보 조회 실패 (ka10100): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10100', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10101(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 업종코드 리스트 (ka10101)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - mrkt_tp: 시장구분 (0:코스피(거래소),1:코스닥,2:KOSPI200,4:KOSPI100,7:KRX100(통합지수))
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> result = await fn_ka10101(data={"mrkt_tp": "0"})
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['list']}")
    """
    logger.info("🏢 키움 업종코드 리스트 요청 시작 (ka10101)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None or not data.get('mrkt_tp'):
            raise ValueError("시장구분(mrkt_tp)이 필요합니다")

        mrkt_tp = data['mrkt_tp']
        logger.info(f"📊 시장구분: {mrkt_tp}")

        # 3. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/stkinfo'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10101',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비
        request_data = {
            'mrkt_tp': mrkt_tp
        }

        # 6. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10101')
        }

        # 8. 응답 데이터 구성 (사용자 코드와 동일한 형태)
        result = {
            'Code': response.status_code,
            'Header': api_headers,
            'Body': response.json() if response.content else {}
        }

        # 9. 로깅 (사용자 코드와 동일한 형태)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")

        return result

    except Exception as e:
        error_msg = f"키움 업종코드 리스트 요청 실패 (ka10101): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10101', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka10095(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 관심종목정보요청 (ka10095)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stk_cd: 종목코드 (거래소별 종목코드, 여러 종목시 | 로 구분)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> result = await fn_ka10095(data={"stk_cd": "005930|000660|035420"})
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['list']}")
    """
    logger.info("🏢 키움 관심종목정보 요청 시작 (ka10095)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None or not data.get('stk_cd'):
            raise ValueError("종목코드(stk_cd)가 필요합니다")

        stk_cd = data['stk_cd']
        logger.info(f"📊 종목코드: {stk_cd}")

        # 3. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/stkinfo'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10095',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비
        request_data = {
            'stk_cd': stk_cd
        }

        # 6. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10095')
        }

        # 8. 응답 데이터 구성 (사용자 코드와 동일한 형태)
        result = {
            'Code': response.status_code,
            'Header': api_headers,
            'Body': response.json() if response.content else {}
        }

        # 9. 로깅 (사용자 코드와 동일한 형태)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")

        return result

    except Exception as e:
        error_msg = f"키움 관심종목정보 요청 실패 (ka10095): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka10095', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }


async def fn_ka90003(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 프로그램순매수상위50요청 (ka90003)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - trde_upper_tp: 매매상위구분 (1:순매도상위, 2:순매수상위)
              - amt_qty_tp: 금액수량구분 (1:금액, 2:수량)
              - mrkt_tp: 시장구분 (P00101:코스피, P10102:코스닥)
              - stex_tp: 거래소구분 (1:KRX, 2:NXT, 3:통합)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디

    Example:
        >>> data = {"trde_upper_tp": "2", "amt_qty_tp": "1", "mrkt_tp": "P00101", "stex_tp": "1"}
        >>> result = await fn_ka90003(data=data)
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['prm_netprps_upper_50']}")
    """
    logger.info("🏢 키움 프로그램순매수상위50 요청 시작 (ka90003)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        required_fields = ['trde_upper_tp', 'amt_qty_tp', 'mrkt_tp', 'stex_tp']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"{field}가 필요합니다")

        logger.info(f"📊 매매상위구분: {data['trde_upper_tp']}")
        logger.info(f"📊 금액수량구분: {data['amt_qty_tp']}")
        logger.info(f"📊 시장구분: {data['mrkt_tp']}")
        logger.info(f"📊 거래소구분: {data['stex_tp']}")

        # 3. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/stkinfo'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka90003',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비
        request_data = {
            'trde_upper_tp': data['trde_upper_tp'],
            'amt_qty_tp': data['amt_qty_tp'],
            'mrkt_tp': data['mrkt_tp'],
            'stex_tp': data['stex_tp']
        }

        # 6. HTTP POST 요청
        timeout = 30.0
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 키움 API 응답 헤더 추출
        api_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka90003')
        }

        # 8. 응답 데이터 구성 (사용자 코드와 동일한 형태)
        result = {
            'Code': response.status_code,
            'Header': api_headers,
            'Body': response.json() if response.content else {}
        }

        # 9. 로깅 (사용자 코드와 동일한 형태)
        logger.info(f"Code: {result['Code']}")
        logger.info(f"Header: {json.dumps(result['Header'], indent=4, ensure_ascii=False)}")
        logger.info(f"Body: {json.dumps(result['Body'], indent=4, ensure_ascii=False)}")

        return result

    except Exception as e:
        error_msg = f"키움 프로그램순매수상위50 요청 실패 (ka90003): {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 에러 응답도 사용자 코드와 동일한 형태로 반환
        return {
            'Code': 500,
            'Header': {'api-id': 'ka90003', 'cont-yn': 'N', 'next-key': ''},
            'Body': {'error': error_msg}
        }