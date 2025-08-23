"""
키움 API 계좌 관련 함수들

키움 API 스펙에 완전히 맞춰진 계좌 API 함수 구현
fn_{api_id} 형태로 명명하여 키움 문서와 1:1 매핑

지원하는 API:
- 손익 관련: ka10072~ka10077, ka10085, ka10170
- 주문/체결 관련: ka10075, ka10076, ka10088  
- 계좌 현황 관련: kt00001~kt00018
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

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


# ============== 손익 관련 API 함수 ==============

async def fn_ka10072(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 일자별종목별실현손익요청_일자 (ka10072)

    키움 API 스펙 완전 준수 함수
    사용자 제공 코드와 동일한 방식으로 구현

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stk_cd: 종목코드 (6자리)
              - strt_dt: 시작일자 (YYYYMMDD)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디
            - dt_stk_div_rlzt_pl: 일자별종목별실현손익 리스트

    Example:
        >>> result = await fn_ka10072(data={"stk_cd": "005930", "strt_dt": "20241128"})
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['dt_stk_div_rlzt_pl']}")
    """
    logger.info("💰 키움 일자별종목별실현손익요청_일자 시작 (ka10072)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None or not data.get('stk_cd') or not data.get('strt_dt'):
            raise ValueError("종목코드(stk_cd)와 시작일자(strt_dt)가 필요합니다")

        stk_cd = data['stk_cd']
        strt_dt = data['strt_dt']
        logger.info(f"📊 종목코드: {stk_cd}, 시작일자: {strt_dt}")

        # 3. 요청할 API URL 구성
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/acnt'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10072',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비
        request_data = {
            'stk_cd': stk_cd,
            'strt_dt': strt_dt
        }

        logger.info(f"📤 요청 데이터: {json.dumps(request_data, ensure_ascii=False)}")

        # 6. HTTP POST 요청
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 응답 처리
        logger.info(f"📥 응답 상태: {response.status_code}")
        
        # 응답 헤더 처리
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10072')
        }
        
        # 응답 바디 처리
        if response.status_code == 200:
            response_body = response.json()
            logger.info("✅ ka10072 요청 성공")
            
            # 손익 데이터가 있는지 확인
            if 'dt_stk_div_rlzt_pl' in response_body:
                profit_list = response_body['dt_stk_div_rlzt_pl']
                logger.info(f"📈 실현손익 데이터: {len(profit_list) if isinstance(profit_list, list) else 0}건")
        else:
            response_body = response.json() if response.content else {}
            logger.error(f"❌ ka10072 요청 실패: {response.status_code}")

        # 8. 키움 API 표준 응답 형태로 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

        logger.info(f"🔄 ka10072 응답 완료: {response.status_code}")
        return result

    except httpx.TimeoutException:
        logger.error("⏰ ka10072 요청 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"🔥 ka10072 HTTP 오류: {e.response.status_code}")
        return {
            'Code': e.response.status_code,
            'Header': {},
            'Body': {'error': f'HTTP {e.response.status_code}'}
        }
    except Exception as e:
        logger.error(f"💥 ka10072 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10073(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 일자별종목별실현손익요청_기간 (ka10073) - 정확한 키움 스펙 구현

    키움 공식 API 스펙:
    - Request: stk_cd(종목코드), strt_dt(시작일자), end_dt(종료일자)
    - Response: dt_stk_rlzt_pl 리스트 (14개 필드)

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stk_cd: 종목코드 (String, Required, 6자리)
              - strt_dt: 시작일자 (String, Required, 8자리 YYYYMMDD)
              - end_dt: 종료일자 (String, Required, 8자리 YYYYMMDD)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (cont-yn, next-key, api-id)
        - Body: 키움 API 응답 바디
            - dt_stk_rlzt_pl: 일자별종목별실현손익 리스트
              각 항목은 14개 필드 포함 (dt, tdy_htssel_cmsn, stk_nm, cntr_qty, 
              buy_uv, cntr_pric, tdy_sel_pl, pl_rt, stk_cd, tdy_trde_cmsn, 
              tdy_trde_tax, wthd_alowa, loan_dt, crd_tp)

    Example:
        >>> data = {"stk_cd": "005930", "strt_dt": "20241128", "end_dt": "20241128"}
        >>> result = await fn_ka10073(data=data)
        >>> print(f"Code: {result['Code']}")
        >>> print(f"Body: {result['Body']['dt_stk_rlzt_pl']}")
    """
    logger.info("💰 키움 일자별종목별실현손익요청_기간 시작 (ka10073)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        required_fields = ['stk_cd', 'strt_dt', 'end_dt']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"{field}가 필요합니다")

        stk_cd = data['stk_cd']
        strt_dt = data['strt_dt']
        end_dt = data['end_dt']
        
        logger.info(f"📊 종목코드: {stk_cd}, 기간: {strt_dt}~{end_dt}")

        # 3. 요청할 API URL 구성 (키움 스펙)
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/acnt'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙 완전 준수)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10073',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비 (키움 스펙)
        request_data = {
            'stk_cd': stk_cd,    # 종목코드 
            'strt_dt': strt_dt,  # 시작일자 YYYYMMDD
            'end_dt': end_dt     # 종료일자 YYYYMMDD
        }

        logger.info(f"📤 요청 데이터: {json.dumps(request_data, ensure_ascii=False)}")

        # 6. HTTP POST 요청
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 응답 처리
        logger.info(f"📥 응답 상태: {response.status_code}")
        
        # 응답 헤더 처리 (키움 스펙)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),      # 연속조회키
            'cont-yn': response.headers.get('cont-yn', 'N'),       # 연속조회여부
            'api-id': response.headers.get('api-id', 'ka10073')    # TR명
        }
        
        # 응답 바디 처리
        if response.status_code == 200:
            response_body = response.json()
            logger.info("✅ ka10073 요청 성공")
            
            # 키움 스펙: dt_stk_rlzt_pl 손익 데이터가 있는지 확인
            if 'dt_stk_rlzt_pl' in response_body:
                profit_list = response_body['dt_stk_rlzt_pl']
                logger.info(f"📈 일자별종목별실현손익 데이터: {len(profit_list) if isinstance(profit_list, list) else 0}건")
                
                # 첫 번째 항목 필드 확인 (디버깅용)
                if profit_list and isinstance(profit_list, list) and len(profit_list) > 0:
                    first_item = profit_list[0]
                    logger.info(f"📋 첫 번째 손익 항목 필드: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
        else:
            response_body = response.json() if response.content else {}
            logger.error(f"❌ ka10073 요청 실패: {response.status_code}")

        # 8. 키움 API 표준 응답 형태로 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

        logger.info(f"🔄 ka10073 응답 완료: {response.status_code}")
        return result

    except httpx.TimeoutException:
        logger.error("⏰ ka10073 요청 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"🔥 ka10073 HTTP 오류: {e.response.status_code}")
        return {
            'Code': e.response.status_code,
            'Header': {},
            'Body': {'error': f'HTTP {e.response.status_code}'}
        }
    except Exception as e:
        logger.error(f"💥 ka10073 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10074(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 일자별실현손익요청 (ka10074) - 정확한 키움 스펙 구현

    키움 공식 API 스펙:
    - Request: strt_dt(시작일자), end_dt(종료일자) - 둘 다 Required
    - Response: 총매수/매도금액, 실현손익, 수수료/세금, dt_rlzt_pl 리스트

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - strt_dt: 시작일자 (String, Required, 8자리 YYYYMMDD)
              - end_dt: 종료일자 (String, Required, 8자리 YYYYMMDD)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (cont-yn, next-key, api-id)
        - Body: 키움 API 응답 바디
            - tot_buy_amt: 총매수금액 (String)
            - tot_sell_amt: 총매도금액 (String)
            - rlzt_pl: 실현손익 (String)
            - trde_cmsn: 매매수수료 (String)
            - trde_tax: 매매세금 (String)
            - dt_rlzt_pl: 일자별실현손익 리스트
              각 항목: dt(일자), buy_amt(매수금액), sell_amt(매도금액),
              tdy_sel_pl(당일매도손익), tdy_trde_cmsn(당일매매수수료), tdy_trde_tax(당일매매세금)

    Example:
        >>> data = {"strt_dt": "20241128", "end_dt": "20241128"}
        >>> result = await fn_ka10074(data=data)
        >>> print(f"Code: {result['Code']}")
        >>> print(f"총 실현손익: {result['Body']['rlzt_pl']}")
        >>> print(f"일자별 손익: {result['Body']['dt_rlzt_pl']}")
    """
    logger.info("💰 키움 일자별실현손익요청 시작 (ka10074)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증 (키움 스펙: 둘 다 Required)
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        required_fields = ['strt_dt', 'end_dt']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"{field}가 필요합니다")

        strt_dt = data['strt_dt']
        end_dt = data['end_dt']
        
        logger.info(f"📊 일자별실현손익 조회기간: {strt_dt} ~ {end_dt}")

        # 3. 요청할 API URL 구성 (키움 스펙)
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/acnt'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙 완전 준수)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10074',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비 (키움 스펙)
        request_data = {
            'strt_dt': strt_dt,  # 시작일자
            'end_dt': end_dt     # 종료일자
        }

        logger.info(f"📤 요청 데이터: {json.dumps(request_data, ensure_ascii=False)}")

        # 6. HTTP POST 요청
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 응답 처리
        logger.info(f"📥 응답 상태: {response.status_code}")
        
        # 응답 헤더 처리 (키움 스펙)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),      # 연속조회키
            'cont-yn': response.headers.get('cont-yn', 'N'),       # 연속조회여부
            'api-id': response.headers.get('api-id', 'ka10074')    # TR명
        }
        
        # 응답 바디 처리
        if response.status_code == 200:
            response_body = response.json()
            logger.info("✅ ka10074 요청 성공")
            
            # 키움 스펙: 응답 필드 확인
            if response_body:
                logger.info(f"📈 총매수금액: {response_body.get('tot_buy_amt', 'N/A')}")
                logger.info(f"📈 총매도금액: {response_body.get('tot_sell_amt', 'N/A')}")
                logger.info(f"💰 실현손익: {response_body.get('rlzt_pl', 'N/A')}")
                
                # 일자별실현손익 리스트 확인
                if 'dt_rlzt_pl' in response_body:
                    daily_list = response_body['dt_rlzt_pl']
                    logger.info(f"📅 일자별실현손익 데이터: {len(daily_list) if isinstance(daily_list, list) else 0}건")
        else:
            response_body = response.json() if response.content else {}
            logger.error(f"❌ ka10074 요청 실패: {response.status_code}")

        # 8. 키움 API 표준 응답 형태로 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

        logger.info(f"🔄 ka10074 응답 완료: {response.status_code}")
        return result

    except httpx.TimeoutException:
        logger.error("⏰ ka10074 요청 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"🔥 ka10074 HTTP 오류: {e.response.status_code}")
        return {
            'Code': e.response.status_code,
            'Header': {},
            'Body': {'error': f'HTTP {e.response.status_code}'}
        }
    except Exception as e:
        logger.error(f"💥 ka10074 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10075(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 미체결요청 (ka10075) - 정확한 키움 스펙 구현

    키움 공식 API 스펙:
    - Request: all_stk_tp(전체종목구분), trde_tp(매매구분), stk_cd(종목코드), stex_tp(거래소구분)
    - Response: oso 리스트 (미체결 정보 31개 필드)

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - all_stk_tp: 전체종목구분 (String, Required, 0:전체, 1:종목)
              - trde_tp: 매매구분 (String, Required, 0:전체, 1:매도, 2:매수)
              - stk_cd: 종목코드 (String, Optional, 6자리)
              - stex_tp: 거래소구분 (String, Required, 0:통합, 1:KRX, 2:NXT)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (cont-yn, next-key, api-id)
        - Body: 키움 API 응답 바디
            - oso: 미체결 리스트
              각 항목: acnt_no(계좌번호), ord_no(주문번호), stk_cd(종목코드),
              ord_stt(주문상태), stk_nm(종목명), ord_qty(주문수량), ord_pric(주문가격),
              oso_qty(미체결수량), cntr_tot_amt(체결누계금액), trde_tp(매매구분) 등 31개 필드

    Example:
        >>> data = {"all_stk_tp": "1", "trde_tp": "0", "stk_cd": "005930", "stex_tp": "0"}
        >>> result = await fn_ka10075(data=data)
        >>> print(f"Code: {result['Code']}")
        >>> print(f"미체결 리스트: {result['Body']['oso']}")
    """
    logger.info("📋 키움 미체결요청 시작 (ka10075)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증 (키움 스펙: all_stk_tp, trde_tp, stex_tp 필수)
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        required_fields = ['all_stk_tp', 'trde_tp', 'stex_tp']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"{field}가 필요합니다")

        all_stk_tp = data['all_stk_tp']
        trde_tp = data['trde_tp']
        stk_cd = data.get('stk_cd', '')  # 선택사항
        stex_tp = data['stex_tp']
        
        logger.info(f"📊 미체결요청 - 전체종목구분: {all_stk_tp}, 매매구분: {trde_tp}, 종목코드: {stk_cd or 'N/A'}, 거래소구분: {stex_tp}")

        # 3. 요청할 API URL 구성 (키움 스펙)
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/acnt'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙 완전 준수)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10075',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비 (키움 스펙)
        request_data = {
            'all_stk_tp': all_stk_tp,  # 전체종목구분
            'trde_tp': trde_tp,        # 매매구분
            'stex_tp': stex_tp         # 거래소구분
        }
        
        # 종목코드는 선택사항 (stk_cd가 있을 때만 포함)
        if stk_cd:
            request_data['stk_cd'] = stk_cd

        logger.info(f"📤 요청 데이터: {json.dumps(request_data, ensure_ascii=False)}")

        # 6. HTTP POST 요청
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 응답 처리
        logger.info(f"📥 응답 상태: {response.status_code}")
        
        # 응답 헤더 처리 (키움 스펙)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),      # 연속조회키
            'cont-yn': response.headers.get('cont-yn', 'N'),       # 연속조회여부
            'api-id': response.headers.get('api-id', 'ka10075')    # TR명
        }
        
        # 응답 바디 처리
        if response.status_code == 200:
            response_body = response.json()
            logger.info("✅ ka10075 요청 성공")
            
            # 키움 스펙: oso(미체결) 리스트 확인
            if response_body and 'oso' in response_body:
                oso_list = response_body['oso']
                logger.info(f"📋 미체결 데이터: {len(oso_list) if isinstance(oso_list, list) else 0}건")
                
                # 첫 번째 미체결 항목 필드 확인 (디버깅용)
                if oso_list and isinstance(oso_list, list) and len(oso_list) > 0:
                    first_item = oso_list[0]
                    logger.info(f"📊 첫 번째 미체결 항목 필드: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
        else:
            response_body = response.json() if response.content else {}
            logger.error(f"❌ ka10075 요청 실패: {response.status_code}")

        # 8. 키움 API 표준 응답 형태로 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

        logger.info(f"🔄 ka10075 응답 완료: {response.status_code}")
        return result

    except httpx.TimeoutException:
        logger.error("⏰ ka10075 요청 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"🔥 ka10075 HTTP 오류: {e.response.status_code}")
        return {
            'Code': e.response.status_code,
            'Header': {},
            'Body': {'error': f'HTTP {e.response.status_code}'}
        }
    except Exception as e:
        logger.error(f"💥 ka10075 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10076(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 체결요청 (ka10076) - 정확한 키움 스펙 구현

    키움 공식 API 스펙:
    - Request: stk_cd(종목코드), qry_tp(조회구분), sell_tp(매도수구분), ord_no(주문번호), stex_tp(거래소구분)
    - Response: cntr 리스트 (체결정보 19개 필드)

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stk_cd: 종목코드 (String, Optional, 6자리)
              - qry_tp: 조회구분 (String, Required, 0:전체, 1:종목)
              - sell_tp: 매도수구분 (String, Required, 0:전체, 1:매도, 2:매수)
              - ord_no: 주문번호 (String, Optional, 검색 기준 값)
              - stex_tp: 거래소구분 (String, Required, 0:통합, 1:KRX, 2:NXT)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (cont-yn, next-key, api-id)
        - Body: 키움 API 응답 바디
            - cntr: 체결 리스트
              각 항목: ord_no(주문번호), stk_nm(종목명), io_tp_nm(주문구분),
              ord_pric(주문가격), ord_qty(주문수량), cntr_pric(체결가), cntr_qty(체결량),
              oso_qty(미체결수량), ord_stt(주문상태), trde_tp(매매구분) 등 19개 필드

    Example:
        >>> data = {"stk_cd": "005930", "qry_tp": "1", "sell_tp": "0", "ord_no": "", "stex_tp": "0"}
        >>> result = await fn_ka10076(data=data)
        >>> print(f"Code: {result['Code']}")
        >>> print(f"체결 리스트: {result['Body']['cntr']}")
    """
    logger.info("✅ 키움 체결요청 시작 (ka10076)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증 (키움 스펙: qry_tp, sell_tp, stex_tp 필수)
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        required_fields = ['qry_tp', 'sell_tp', 'stex_tp']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"{field}가 필요합니다")

        stk_cd = data.get('stk_cd', '')  # 선택사항
        qry_tp = data['qry_tp']
        sell_tp = data['sell_tp']
        ord_no = data.get('ord_no', '')  # 선택사항
        stex_tp = data['stex_tp']
        
        logger.info(f"📊 체결요청 - 종목코드: {stk_cd or 'N/A'}, 조회구분: {qry_tp}, 매도수구분: {sell_tp}, 주문번호: {ord_no or 'N/A'}, 거래소구분: {stex_tp}")

        # 3. 요청할 API URL 구성 (키움 스펙)
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/acnt'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙 완전 준수)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10076',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비 (키움 스펙)
        request_data = {
            'qry_tp': qry_tp,      # 조회구분
            'sell_tp': sell_tp,    # 매도수구분
            'stex_tp': stex_tp     # 거래소구분
        }
        
        # 종목코드는 선택사항 (stk_cd가 있을 때만 포함)
        if stk_cd:
            request_data['stk_cd'] = stk_cd
            
        # 주문번호는 선택사항 (ord_no가 있을 때만 포함)
        if ord_no:
            request_data['ord_no'] = ord_no

        logger.info(f"📤 요청 데이터: {json.dumps(request_data, ensure_ascii=False)}")

        # 6. HTTP POST 요청
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 응답 처리
        logger.info(f"📥 응답 상태: {response.status_code}")
        
        # 응답 헤더 처리 (키움 스펙)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),      # 연속조회키
            'cont-yn': response.headers.get('cont-yn', 'N'),       # 연속조회여부
            'api-id': response.headers.get('api-id', 'ka10076')    # TR명
        }
        
        # 응답 바디 처리
        if response.status_code == 200:
            response_body = response.json()
            logger.info("✅ ka10076 요청 성공")
            
            # 키움 스펙: cntr(체결) 리스트 확인
            if response_body and 'cntr' in response_body:
                cntr_list = response_body['cntr']
                logger.info(f"✅ 체결 데이터: {len(cntr_list) if isinstance(cntr_list, list) else 0}건")
                
                # 첫 번째 체결 항목 필드 확인 (디버깅용)
                if cntr_list and isinstance(cntr_list, list) and len(cntr_list) > 0:
                    first_item = cntr_list[0]
                    logger.info(f"📊 첫 번째 체결 항목 필드: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
        else:
            response_body = response.json() if response.content else {}
            logger.error(f"❌ ka10076 요청 실패: {response.status_code}")

        # 8. 키움 API 표준 응답 형태로 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

        logger.info(f"🔄 ka10076 응답 완료: {response.status_code}")
        return result

    except httpx.TimeoutException:
        logger.error("⏰ ka10076 요청 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"🔥 ka10076 HTTP 오류: {e.response.status_code}")
        return {
            'Code': e.response.status_code,
            'Header': {},
            'Body': {'error': f'HTTP {e.response.status_code}'}
        }
    except Exception as e:
        logger.error(f"💥 ka10076 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10077(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 당일실현손익상세요청 (ka10077) - 정확한 키움 스펙 구현

    키움 공식 API 스펙:
    - Request: stk_cd(종목코드) - Required
    - Response: tdy_rlzt_pl(당일실현손익), tdy_rlzt_pl_dtl 리스트 (당일실현손익상세 9개 필드)

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stk_cd: 종목코드 (String, Required, 6자리)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (cont-yn, next-key, api-id)
        - Body: 키움 API 응답 바디
            - tdy_rlzt_pl: 당일실현손익 (String)
            - tdy_rlzt_pl_dtl: 당일실현손익상세 리스트
              각 항목: stk_nm(종목명), cntr_qty(체결량), buy_uv(매입단가),
              cntr_pric(체결가), tdy_sel_pl(당일매도손익), pl_rt(손익율),
              tdy_trde_cmsn(당일매매수수료), tdy_trde_tax(당일매매세금), stk_cd(종목코드)

    Example:
        >>> data = {"stk_cd": "005930"}
        >>> result = await fn_ka10077(data=data)
        >>> print(f"Code: {result['Code']}")
        >>> print(f"당일실현손익: {result['Body']['tdy_rlzt_pl']}")
        >>> print(f"상세내역: {result['Body']['tdy_rlzt_pl_dtl']}")
    """
    logger.info("💰 키움 당일실현손익상세요청 시작 (ka10077)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증 (키움 스펙: stk_cd 필수)
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        if not data.get('stk_cd'):
            raise ValueError("종목코드(stk_cd)가 필요합니다")

        stk_cd = data['stk_cd']
        
        logger.info(f"📊 당일실현손익상세 조회 종목코드: {stk_cd}")

        # 3. 요청할 API URL 구성 (키움 스펙)
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/acnt'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙 완전 준수)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10077',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비 (키움 스펙)
        request_data = {
            'stk_cd': stk_cd  # 종목코드 (필수)
        }

        logger.info(f"📤 요청 데이터: {json.dumps(request_data, ensure_ascii=False)}")

        # 6. HTTP POST 요청
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 응답 처리
        logger.info(f"📥 응답 상태: {response.status_code}")
        
        # 응답 헤더 처리 (키움 스펙)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),      # 연속조회키
            'cont-yn': response.headers.get('cont-yn', 'N'),       # 연속조회여부
            'api-id': response.headers.get('api-id', 'ka10077')    # TR명
        }
        
        # 응답 바디 처리
        if response.status_code == 200:
            response_body = response.json()
            logger.info("✅ ka10077 요청 성공")
            
            # 키움 스펙: 응답 필드 확인
            if response_body:
                # 당일실현손익 전체 금액
                tdy_rlzt_pl = response_body.get('tdy_rlzt_pl', 'N/A')
                logger.info(f"💰 당일실현손익: {tdy_rlzt_pl}")
                
                # 당일실현손익상세 리스트 확인
                if 'tdy_rlzt_pl_dtl' in response_body:
                    detail_list = response_body['tdy_rlzt_pl_dtl']
                    logger.info(f"📊 당일실현손익상세 데이터: {len(detail_list) if isinstance(detail_list, list) else 0}건")
                    
                    # 첫 번째 상세 항목 필드 확인 (디버깅용)
                    if detail_list and isinstance(detail_list, list) and len(detail_list) > 0:
                        first_item = detail_list[0]
                        logger.info(f"📋 첫 번째 상세 항목 필드: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
        else:
            response_body = response.json() if response.content else {}
            logger.error(f"❌ ka10077 요청 실패: {response.status_code}")

        # 8. 키움 API 표준 응답 형태로 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

        logger.info(f"🔄 ka10077 응답 완료: {response.status_code}")
        return result

    except httpx.TimeoutException:
        logger.error("⏰ ka10077 요청 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"🔥 ka10077 HTTP 오류: {e.response.status_code}")
        return {
            'Code': e.response.status_code,
            'Header': {},
            'Body': {'error': f'HTTP {e.response.status_code}'}
        }
    except Exception as e:
        logger.error(f"💥 ka10077 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10085(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 계좌수익률요청 (ka10085) - 정확한 키움 스펙 구현

    키움 공식 API 스펙:
    - Request: stex_tp(거래소구분) - Required
    - Response: acnt_prft_rt 리스트 (계좌수익률 정보 17개 필드)

    Args:
        token: 접근토큰 (없으면 자동 발급)
        data: 요청 데이터
              - stex_tp: 거래소구분 (String, Required, 0:통합, 1:KRX, 2:NXT)
        cont_yn: 연속조회여부 (N: 최초, Y: 연속)
        next_key: 연속조회키

    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더 (cont-yn, next-key, api-id)
        - Body: 키움 API 응답 바디
            - acnt_prft_rt: 계좌수익률 리스트
              각 항목: dt(일자), stk_cd(종목코드), stk_nm(종목명), cur_prc(현재가),
              pur_pric(매입가), pur_amt(매입금액), rmnd_qty(보유수량), tdy_sel_pl(당일매도손익),
              tdy_trde_cmsn(당일매매수수료), tdy_trde_tax(당일매매세금), crd_tp(신용구분),
              loan_dt(대출일), setl_remn(결제잔고), clrn_alow_qty(청산가능수량),
              crd_amt(신용금액), crd_int(신용이자), expr_dt(만기일)

    Example:
        >>> data = {"stex_tp": "0"}
        >>> result = await fn_ka10085(data=data)
        >>> print(f"Code: {result['Code']}")
        >>> print(f"계좌수익률 리스트: {result['Body']['acnt_prft_rt']}")
    """
    logger.info("📈 키움 계좌수익률요청 시작 (ka10085)")

    try:
        # 1. 토큰 준비
        if token is None:
            token = await get_valid_access_token()
        
        # 2. 요청 데이터 검증 (키움 스펙: stex_tp 필수)
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        if not data.get('stex_tp'):
            raise ValueError("거래소구분(stex_tp)가 필요합니다")

        stex_tp = data['stex_tp']
        
        logger.info(f"📈 계좌수익률 조회 거래소구분: {stex_tp} ({'통합' if stex_tp == '0' else 'KRX' if stex_tp == '1' else 'NXT' if stex_tp == '2' else 'Unknown'})")

        # 3. 요청할 API URL 구성 (키움 스펙)
        host = settings.kiwoom_base_url
        endpoint = '/api/dostk/acnt'
        url = host + endpoint

        logger.info(f"📡 요청 URL: {url}")
        logger.info(f"📊 모드: {settings.kiwoom_mode_description}")

        # 4. header 데이터 (키움 API 스펙 완전 준수)
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',  # 컨텐츠타입
            'authorization': f'Bearer {token}',  # 접근토큰
            'cont-yn': cont_yn,  # 연속조회여부
            'next-key': next_key,  # 연속조회키
            'api-id': 'ka10085',  # TR명
        }

        logger.info(f"🔑 토큰: {token[:20]}...")
        logger.info(f"📋 연속조회: {cont_yn}")
        if next_key:
            logger.info(f"🔗 연속키: {next_key[:20]}...")

        # 5. 요청 데이터 준비 (키움 스펙)
        request_data = {
            'stex_tp': stex_tp  # 거래소구분 (필수)
        }

        logger.info(f"📤 요청 데이터: {json.dumps(request_data, ensure_ascii=False)}")

        # 6. HTTP POST 요청
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 7. 응답 처리
        logger.info(f"📥 응답 상태: {response.status_code}")
        
        # 응답 헤더 처리 (키움 스펙)
        response_headers = {
            'next-key': response.headers.get('next-key', ''),      # 연속조회키
            'cont-yn': response.headers.get('cont-yn', 'N'),       # 연속조회여부
            'api-id': response.headers.get('api-id', 'ka10085')    # TR명
        }
        
        # 응답 바디 처리
        if response.status_code == 200:
            response_body = response.json()
            logger.info("✅ ka10085 요청 성공")
            
            # 키움 스펙: acnt_prft_rt(계좌수익률) 리스트 확인
            if response_body and 'acnt_prft_rt' in response_body:
                profit_rt_list = response_body['acnt_prft_rt']
                logger.info(f"📈 계좌수익률 데이터: {len(profit_rt_list) if isinstance(profit_rt_list, list) else 0}건")
                
                # 첫 번째 수익률 항목 필드 확인 (디버깅용)
                if profit_rt_list and isinstance(profit_rt_list, list) and len(profit_rt_list) > 0:
                    first_item = profit_rt_list[0]
                    logger.info(f"📊 첫 번째 수익률 항목 필드: {list(first_item.keys()) if isinstance(first_item, dict) else 'N/A'}")
        else:
            response_body = response.json() if response.content else {}
            logger.error(f"❌ ka10085 요청 실패: {response.status_code}")

        # 8. 키움 API 표준 응답 형태로 반환
        result = {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

        logger.info(f"🔄 ka10085 응답 완료: {response.status_code}")
        return result

    except httpx.TimeoutException:
        logger.error("⏰ ka10085 요청 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"🔥 ka10085 HTTP 오류: {e.response.status_code}")
        return {
            'Code': e.response.status_code,
            'Header': {},
            'Body': {'error': f'HTTP {e.response.status_code}'}
        }
    except Exception as e:
        logger.error(f"💥 ka10085 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10088(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 미체결 분할주문 상세 (ka10088)
    
    Args:
        token: 인증 토큰
        data: 요청 데이터
              - ord_no: 주문번호 (String, Required, 20자)
        cont_yn: 연속조회여부 ('N': 최초조회, 'Y': 연속조회)
        next_key: 연속조회 키
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 응답 헤더 정보
        - Body: 응답 데이터
          - osop: 미체결분할주문리스트 (LIST)
            각 항목은 다음 필드 포함:
            - stk_cd: 종목코드
            - stk_nm: 종목명  
            - ord_no: 주문번호
            - ord_qty: 주문수량
            - ord_pric: 주문가격
            - osop_qty: 미체결수량
            - io_tp_nm: 매매구분명
            - trde_tp: 거래구분
            - sell_tp: 매도구분
            - cntr_qty: 체결수량
            - ord_stt: 주문상태
            - cur_prc: 현재가
            - stex_tp: 거래소구분
            - stex_tp_txt: 거래소구분명
    
    Example:
        >>> data = {"ord_no": "20241128001"}
        >>> result = await fn_ka10088(token="your_token", data=data)
    """
    logger.info("📋 ka10088 미체결 분할주문 상세 요청 시작")
    
    try:
        # 토큰 검증
        if token is None:
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None or not data.get('ord_no'):
            raise ValueError("주문번호(ord_no)가 필요합니다")
            
        # API 요청 URL
        url = f"{settings.kiwoom_base_url}/api/dostk/acnt"
        
        # 요청 헤더 구성
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10088'
        }
        
        # 요청 본문 구성
        request_body = {
            'ord_no': data['ord_no']
        }
        
        logger.info(f"📊 주문번호: {data['ord_no']}")
        
        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_body)
        
        # 응답 헤더 처리
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10088'),
            'response-time': response.headers.get('response-time', ''),
            'request-time': response.headers.get('request-time', '')
        }
        
        # 응답 본문 처리
        try:
            response_body = response.json() if response.content else {}
        except:
            response_body = {}
        
        # 로그 출력
        if response.status_code == 200:
            osop_count = len(response_body.get('osop', [])) if isinstance(response_body.get('osop'), list) else 0
            logger.info(f"✅ ka10088 요청 성공 - 미체결분할주문 {osop_count}건 조회")
        else:
            logger.error(f"❌ ka10088 요청 실패 - 상태코드: {response.status_code}")
            
        # 표준 응답 형식 반환
        return {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
    except Exception as e:
        logger.error(f"💥 ka10088 처리 중 예외 발생: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_ka10170(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 당일매매일지요청 (ka10170)
    
    Args:
        token: 인증 토큰
        data: 요청 데이터
              - base_dt: 기준일자 YYYYMMDD (Optional, 공백시 금일데이터, 최근 2개월까지 제공)
              - ottks_tp: 단주구분 (Required, 1:당일매수에 대한 당일매도, 2:당일매도 전체)
              - ch_crd_tp: 현금신용구분 (Required, 0:전체, 1:현금매매만, 2:신용매매만)
        cont_yn: 연속조회여부 ('N': 최초조회, 'Y': 연속조회)
        next_key: 연속조회 키
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 응답 헤더 정보
        - Body: 응답 데이터
          - tot_sell_amt: 총매도금액
          - tot_buy_amt: 총매수금액
          - tot_cmsn_tax: 총수수료_세금
          - tot_exct_amt: 총정산금액
          - tot_pl_amt: 총손익금액
          - tot_prft_rt: 총수익률
          - tdy_trde_diary: 당일매매일지 (LIST)
            각 항목은 다음 필드 포함:
            - stk_nm: 종목명
            - buy_avg_pric: 매수평균가
            - buy_qty: 매수수량
            - sel_avg_pric: 매도평균가
            - sell_qty: 매도수량
            - cmsn_alm_tax: 수수료_제세금
            - pl_amt: 손익금액
            - sell_amt: 매도금액
            - buy_amt: 매수금액
            - prft_rt: 수익률
            - stk_cd: 종목코드
    
    Example:
        >>> data = {
        ...     "base_dt": "20241120",
        ...     "ottks_tp": "1", 
        ...     "ch_crd_tp": "0"
        ... }
        >>> result = await fn_ka10170(token="your_token", data=data)
    """
    logger.info("📔 ka10170 당일매매일지요청 시작")
    
    try:
        # 토큰 검증
        if token is None:
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None or not data.get('ottks_tp') or not data.get('ch_crd_tp'):
            raise ValueError("단주구분(ottks_tp), 현금신용구분(ch_crd_tp)이 필요합니다")
            
        # API 요청 URL
        url = f"{settings.kiwoom_base_url}/api/dostk/acnt"
        
        # 요청 헤더 구성
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'ka10170'
        }
        
        # 요청 본문 구성
        request_body = {
            'ottks_tp': data['ottks_tp'],
            'ch_crd_tp': data['ch_crd_tp']
        }
        
        # base_dt가 있을 경우에만 추가 (optional)
        if data.get('base_dt'):
            request_body['base_dt'] = data['base_dt']
        
        logger.info(f"📊 기준일자: {data.get('base_dt', '금일')}, 단주구분: {data['ottks_tp']}, 현금신용구분: {data['ch_crd_tp']}")
        
        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_body)
        
        # 응답 헤더 처리
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'ka10170'),
            'response-time': response.headers.get('response-time', ''),
            'request-time': response.headers.get('request-time', '')
        }
        
        # 응답 본문 처리
        try:
            response_body = response.json() if response.content else {}
        except:
            response_body = {}
        
        # 로그 출력
        if response.status_code == 200:
            diary_count = len(response_body.get('tdy_trde_diary', [])) if isinstance(response_body.get('tdy_trde_diary'), list) else 0
            logger.info(f"✅ ka10170 요청 성공 - 당일매매일지 {diary_count}건 조회")
        else:
            logger.error(f"❌ ka10170 요청 실패 - 상태코드: {response.status_code}")
            
        # 표준 응답 형식 반환
        return {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
    except Exception as e:
        logger.error(f"💥 ka10170 처리 중 예외 발생: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


# ============== 계좌 현황 관련 API 함수 (kt00001~kt00018) ==============

async def fn_kt00001(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 예수금상세현황요청 (kt00001)
    
    Args:
        token: 인증 토큰
        data: 요청 데이터
              - qry_tp: 조회구분 (Required, 3:추정조회, 2:일반조회)
        cont_yn: 연속조회여부 ('N': 최초조회, 'Y': 연속조회)
        next_key: 연속조회 키
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 응답 헤더 정보
        - Body: 응답 데이터
          - entr: 예수금
          - profa_ch: 주식증거금현금
          - bncr_profa_ch: 수익증권증거금현금
          - nxdy_bncr_sell_exct: 익일수익증권매도정산대금
          - fc_stk_krw_repl_set_amt: 해외주식원화대용설정금
          - crd_grnta_ch: 신용보증금현금
          - crd_grnt_ch: 신용담보금현금
          - add_grnt_ch: 추가담보금현금
          - etc_profa: 기타증거금
          - uncl_stk_amt: 미수확보금
          - shrts_prica: 공매도대금
          - crd_set_grnta: 신용설정평가금
          - chck_ina_amt: 수표입금액
          - etc_chck_ina_amt: 기타수표입금액
          - crd_grnt_ruse: 신용담보재사용
          - knx_asset_evltv: 코넥스기본예탁금
          - elwdpst_evlta: ELW예탁평가금
          - crd_ls_rght_frcs_amt: 신용대주권리예정금액
          - lvlh_join_amt: 생계형가입금액
          - lvlh_trns_alowa: 생계형입금가능금액
          - repl_amt: 대용금평가금액(합계)
          - remn_repl_evlta: 잔고대용평가금액
          - trst_remn_repl_evlta: 위탁대용잔고평가금액
          - bncr_remn_repl_evlta: 수익증권대용평가금액
          - profa_repl: 위탁증거금대용
          - crd_grnta_repl: 신용보증금대용
          - crd_grnt_repl: 신용담보금대용
          - add_grnt_repl: 추가담보금대용
          - rght_repl_amt: 권리대용금
          - pymn_alow_amt: 출금가능금액
          - wrap_pymn_alow_amt: 랩출금가능금액
          - ord_alow_amt: 주문가능금액
          - bncr_buy_alowa: 수익증권매수가능금액
          - 20stk_ord_alow_amt: 20%종목주문가능금액
          - 30stk_ord_alow_amt: 30%종목주문가능금액
          - 40stk_ord_alow_amt: 40%종목주문가능금액
          - 100stk_ord_alow_amt: 100%종목주문가능금액
          - ch_uncla: 현금미수금
          - ch_uncla_dlfe: 현금미수연체료
          - ch_uncla_tot: 현금미수금합계
          - crd_int_npay: 신용이자미납
          - int_npay_amt_dlfe: 신용이자미납연체료
          - int_npay_amt_tot: 신용이자미납합계
          - etc_loana: 기타대여금
          - etc_loana_dlfe: 기타대여금연체료
          - etc_loan_tot: 기타대여금합계
          - nrpy_loan: 미상환융자금
          - loan_sum: 융자금합계
          - ls_sum: 대주금합계
          - crd_grnt_rt: 신용담보비율
          - mdstrm_usfe: 중도이용료
          - min_ord_alow_yn: 최소주문가능금액
          - loan_remn_evlt_amt: 대출총평가금액
          - dpst_grntl_remn: 예탁담보대출잔고
          - sell_grntl_remn: 매도담보대출잔고
          - d1_entra: d+1추정예수금
          - d1_slby_exct_amt: d+1매도매수정산금
          - d1_buy_exct_amt: d+1매수정산금
          - d1_out_rep_mor: d+1미수변제소요금
          - d1_sel_exct_amt: d+1매도정산금
          - d1_pymn_alow_amt: d+1출금가능금액
          - d2_entra: d+2추정예수금
          - d2_slby_exct_amt: d+2매도매수정산금
          - d2_buy_exct_amt: d+2매수정산금
          - d2_out_rep_mor: d+2미수변제소요금
          - d2_sel_exct_amt: d+2매도정산금
          - d2_pymn_alow_amt: d+2출금가능금액
          - 50stk_ord_alow_amt: 50%종목주문가능금액
          - 60stk_ord_alow_amt: 60%종목주문가능금액
          - stk_entr_prst: 종목별예수금 (LIST)
            각 항목은 다음 필드 포함:
            - crnc_cd: 통화코드
            - fx_entr: 외화예수금
            - fc_krw_repl_evlta: 원화대용평가금
            - fc_trst_profa: 해외주식증거금
            - pymn_alow_amt: 출금가능금액
            - pymn_alow_amt_entr: 출금가능금액(예수금)
            - ord_alow_amt_entr: 주문가능금액(예수금)
            - fc_uncla: 외화미수(합계)
            - fc_ch_uncla: 외화현금미수금
            - dly_amt: 연체료
            - d1_fx_entr: d+1외화예수금
            - d2_fx_entr: d+2외화예수금
            - d3_fx_entr: d+3외화예수금
            - d4_fx_entr: d+4외화예수금
    
    Example:
        >>> data = {"qry_tp": "3"}
        >>> result = await fn_kt00001(token="your_token", data=data)
    """
    logger.info("💳 kt00001 예수금상세현황요청 시작")
    
    try:
        # 토큰 검증
        if token is None:
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None or not data.get('qry_tp'):
            raise ValueError("조회구분(qry_tp)이 필요합니다")
            
        # API 요청 URL
        url = f"{settings.kiwoom_base_url}/api/dostk/acnt"
        
        # 요청 헤더 구성
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00001'
        }
        
        # 요청 본문 구성
        request_body = {
            'qry_tp': data['qry_tp']
        }
        
        logger.info(f"💳 조회구분: {data['qry_tp']} ({'추정조회' if data['qry_tp'] == '3' else '일반조회'})")
        
        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_body)
        
        # 응답 헤더 처리
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00001'),
            'response-time': response.headers.get('response-time', ''),
            'request-time': response.headers.get('request-time', '')
        }
        
        # 응답 본문 처리
        try:
            response_body = response.json() if response.content else {}
        except:
            response_body = {}
        
        # 로그 출력
        if response.status_code == 200:
            stk_count = len(response_body.get('stk_entr_prst', [])) if isinstance(response_body.get('stk_entr_prst'), list) else 0
            logger.info(f"✅ kt00001 요청 성공 - 종목별예수금 {stk_count}건 조회")
        else:
            logger.error(f"❌ kt00001 요청 실패 - 상태코드: {response.status_code}")
            
        # 표준 응답 형식 반환
        return {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
    except Exception as e:
        logger.error(f"💥 kt00001 처리 중 예외 발생: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


async def fn_kt00002(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 일별추정예탁자산현황요청 (kt00002)
    
    Args:
        token: 인증 토큰
        data: 요청 데이터
              - start_dt: 시작조회기간 (Required, YYYYMMDD)
              - end_dt: 종료조회기간 (Required, YYYYMMDD)
        cont_yn: 연속조회여부 ('N': 최초조회, 'Y': 연속조회)
        next_key: 연속조회 키
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 응답 헤더 정보
        - Body: 응답 데이터
          - daly_prsm_dpst_aset_amt_prst: 일별추정예탁자산현황 (LIST)
            각 항목은 다음 필드 포함:
            - dt: 일자
            - entr: 예수금
            - grnt_use_amt: 담보대출금
            - crd_loan: 신용융자금
            - ls_grnt: 대주담보금
            - repl_amt: 대용금
            - prsm_dpst_aset_amt: 추정예탁자산
            - prsm_dpst_aset_amt_bncr_skip: 추정예탁자산수익증권제외
    
    Example:
        >>> data = {"start_dt": "20241111", "end_dt": "20241125"}
        >>> result = await fn_kt00002(token="your_token", data=data)
    """
    logger.info("📊 kt00002 일별추정예탁자산현황요청 시작")
    
    try:
        # 토큰 검증
        if token is None:
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None or not data.get('start_dt') or not data.get('end_dt'):
            raise ValueError("시작조회기간(start_dt), 종료조회기간(end_dt)이 필요합니다")
            
        # API 요청 URL
        url = f"{settings.kiwoom_base_url}/api/dostk/acnt"
        
        # 요청 헤더 구성
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00002'
        }
        
        # 요청 본문 구성
        request_body = {
            'start_dt': data['start_dt'],
            'end_dt': data['end_dt']
        }
        
        logger.info(f"📊 조회기간: {data['start_dt']} ~ {data['end_dt']}")
        
        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_body)
        
        # 응답 헤더 처리
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00002'),
            'response-time': response.headers.get('response-time', ''),
            'request-time': response.headers.get('request-time', '')
        }
        
        # 응답 본문 처리
        try:
            response_body = response.json() if response.content else {}
        except:
            response_body = {}
        
        # 로그 출력
        if response.status_code == 200:
            asset_count = len(response_body.get('daly_prsm_dpst_aset_amt_prst', [])) if isinstance(response_body.get('daly_prsm_dpst_aset_amt_prst'), list) else 0
            logger.info(f"✅ kt00002 요청 성공 - 일별추정예탁자산현황 {asset_count}건 조회")
        else:
            logger.error(f"❌ kt00002 요청 실패 - 상태코드: {response.status_code}")
            
        # 표준 응답 형식 반환
        return {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
    except Exception as e:
        logger.error(f"💥 kt00002 처리 중 예외 발생: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


# 나머지 kt00003~kt00018 함수들을 간단한 형태로 구현 (패턴 동일)

async def fn_kt00003(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 추정자산조회요청 (kt00003)
    
    Args:
        token: 인증 토큰
        data: 요청 데이터
              - qry_tp: 상장폐지조회구분 (Required, 0:전체, 1:상장폐지종목제외)
        cont_yn: 연속조회여부 ('N': 최초조회, 'Y': 연속조회)
        next_key: 연속조회 키
    
    Returns:
        Dict containing:
        - Code: HTTP 상태 코드
        - Header: 응답 헤더 정보
        - Body: 응답 데이터
          - prsm_dpst_aset_amt: 추정예탁자산
    
    Example:
        >>> data = {"qry_tp": "0"}
        >>> result = await fn_kt00003(token="your_token", data=data)
    """
    logger.info("💰 kt00003 추정자산조회요청 시작")
    
    try:
        # 토큰 검증
        if token is None:
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None or not data.get('qry_tp'):
            raise ValueError("상장폐지조회구분(qry_tp)이 필요합니다")
            
        # API 요청 URL
        url = f"{settings.kiwoom_base_url}/api/dostk/acnt"
        
        # 요청 헤더 구성
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00003'
        }
        
        # 요청 본문 구성
        request_body = {
            'qry_tp': data['qry_tp']
        }
        
        logger.info(f"💰 상장폐지조회구분: {data['qry_tp']} ({'전체' if data['qry_tp'] == '0' else '상장폐지종목제외'})")
        
        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_body)
        
        # 응답 헤더 처리
        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00003'),
            'response-time': response.headers.get('response-time', ''),
            'request-time': response.headers.get('request-time', '')
        }
        
        # 응답 본문 처리
        try:
            response_body = response.json() if response.content else {}
        except:
            response_body = {}
        
        # 로그 출력
        if response.status_code == 200:
            asset_amount = response_body.get('prsm_dpst_aset_amt', 'N/A')
            logger.info(f"✅ kt00003 요청 성공 - 추정예탁자산: {asset_amount}")
        else:
            logger.error(f"❌ kt00003 요청 실패 - 상태코드: {response.status_code}")
            
        # 표준 응답 형식 반환
        return {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }
        
    except Exception as e:
        logger.error(f"💥 kt00003 처리 중 예외 발생: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00004(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 계좌평가현황요청 (kt00004)
    
    계좌평가현황요청 - 전체 계좌의 평가 현황과 보유종목별 평가정보 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - qry_tp (str): 상장폐지조회구분 (0:전체, 1:상장폐지종목제외)
            - dmst_stex_tp (str): 국내거래소구분 (KRX:한국거래소, NXT:넥스트트레이드)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보
            - Body: 계좌평가현황 데이터
                - Main 필드 (19개):
                  - acnt_no: 계좌번호 (String, 10)
                  - evlt_amt: 평가금액 (String, 15)
                  - bfdy_buy_amt: 전일매수금액 (String, 15)
                  - tot_stck_evlt_amt: 총주식평가금액 (String, 15)
                  - bfdy_evlt_amt: 전일평가금액 (String, 15)
                  - d2_bfdy_evlt_amt: 전전일평가금액 (String, 15)
                  - tot_evlu_pfls_amt: 총평가손익금액 (String, 15)
                  - tot_pftrt: 총수익률 (String, 12)
                  - bfdy_tot_asst_evlt_amt: 전일총자산평가금액 (String, 15)
                  - asst_icdc_amt: 자산증감액 (String, 15)
                  - asst_icdc_erng_rt: 자산증감수익률 (String, 12)
                  - ord_psbl_tot_amt: 주문가능총금액 (String, 15)
                  - mnrg_tot_amt: 증거금총액 (String, 15)
                  - ssts_dvd_amt: 신주인수권배당금액 (String, 15)
                  - tot_loan_amt: 총대출금액 (String, 15)
                  - spsn_stck_evlt_amt: 신용주식평가금액 (String, 15)
                  - d1_ovrd_amt: 1일연체금액 (String, 15)
                  - d2_ovrd_amt: 2일연체금액 (String, 15)
                  - d3_ovrd_amt: 3일이상연체금액 (String, 15)
                - stk_acnt_evlt_prst: 종목별계좌평가현황 리스트
                  각 항목 필드 (15개):
                  - stk_cd: 종목코드 (String, 9)
                  - stk_nm: 종목명 (String, 40)
                  - hldg_qty: 보유수량 (String, 10)
                  - ord_psbl_qty: 주문가능수량 (String, 10)  
                  - pchs_avg_prc: 매입평균가격 (String, 10)
                  - evlt_prc: 평가가격 (String, 8)
                  - evlt_amt: 평가금액 (String, 15)
                  - evlu_pfls_amt: 평가손익금액 (String, 15)
                  - evlu_pfls_rt: 평가손익률 (String, 12)
                  - evlu_erng_rt: 평가수익률 (String, 10)
                  - loan_amt: 대출금액 (String, 15)
                  - stck_loan_amt: 주식대출금액 (String, 15)
                  - expd_dt: 만료일자 (String, 8)
                  - fltt_rt: 등락율 (String, 12)
                  - bfdy_cprs_icdc_amt: 전일대비증감금액 (String, 15)
                  
    Raises:
        Exception: API 호출 실패 시
        
    Example:
        >>> result = await fn_kt00004(
        ...     token="access_token_here",
        ...     data={
        ...         "qry_tp": "1",  # 상장폐지종목제외
        ...         "dmst_stex_tp": "KRX"  # 한국거래소
        ...     }
        ... )
        >>> print(f"계좌번호: {result['Body']['acnt_no']}")
        >>> print(f"평가금액: {result['Body']['evlt_amt']}")
    """
    logger.info("🏁 키움증권 계좌평가현황요청 (kt00004) 시작")
    
    if not token:
        token = await get_valid_access_token()
        logger.info(f"🔑 토큰 자동 획득: {token[:10]}...")
        
    if not data:
        logger.error("❌ data 매개변수가 필요합니다")
        return {
            'Code': 400,
            'Header': {},
            'Body': {'error': 'data 매개변수가 필요합니다'}
        }

    # 필수 필드 검증
    required_fields = ['qry_tp', 'dmst_stex_tp']
    for field in required_fields:
        if field not in data:
            logger.error(f"❌ 필수 필드 누락: {field}")
            return {
                'Code': 400,
                'Header': {},
                'Body': {'error': f'필수 필드 누락: {field}'}
            }

    logger.info(f"📊 요청 데이터: qry_tp={data['qry_tp']}, dmst_stex_tp={data['dmst_stex_tp']}")
    logger.info(f"🔄 연속조회: cont_yn={cont_yn}, next_key={next_key}")

    try:
        # 키움 API 호출
        url = f"{settings.get_base_url()}/api/kt00004"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "api-id": settings.get_app_key(),
            "Content-Type": "application/json",
        }

        # 요청 본문 구성
        request_body = {
            **data,
            "cont-yn": cont_yn,
            "next-key": next_key
        }

        logger.info(f"🌐 API 호출: {url}")
        logger.info(f"📤 요청 본문: {json.dumps(request_body, ensure_ascii=False)}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=request_body, headers=headers)
            
            logger.info(f"📡 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 응답 데이터 로깅
                if 'Body' in result and result['Body']:
                    body = result['Body']
                    logger.info(f"✅ 계좌번호: {body.get('acnt_no', 'N/A')}")
                    logger.info(f"✅ 평가금액: {body.get('evlt_amt', 'N/A')}")
                    logger.info(f"✅ 총수익률: {body.get('tot_pftrt', 'N/A')}")
                    logger.info(f"✅ 주문가능총금액: {body.get('ord_psbl_tot_amt', 'N/A')}")
                    
                    # 보유종목 개수 로깅
                    if 'stk_acnt_evlt_prst' in body and isinstance(body['stk_acnt_evlt_prst'], list):
                        stock_count = len(body['stk_acnt_evlt_prst'])
                        logger.info(f"✅ 보유종목 개수: {stock_count}개")
                        
                        # 각 종목 정보 로깅 (최대 5개까지만)
                        for idx, stock in enumerate(body['stk_acnt_evlt_prst'][:5]):
                            logger.info(f"  📈 종목 {idx+1}: {stock.get('stk_nm', 'N/A')}({stock.get('stk_cd', 'N/A')}) - "
                                      f"평가금액: {stock.get('evlt_amt', 'N/A')}, "
                                      f"수익률: {stock.get('evlu_pfls_rt', 'N/A')}")
                        
                        if stock_count > 5:
                            logger.info(f"  📊 외 {stock_count - 5}개 종목...")
                
                logger.info("🎉 키움증권 계좌평가현황요청 (kt00004) 성공")
                return {
                    'Code': 200,
                    'Header': result.get('Header', {}),
                    'Body': result.get('Body', {})
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00005(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 체결잔고요청 (kt00005)
    
    체결잔고요청 - 계좌의 예수금 정보와 보유종목별 체결잔고 정보 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - dmst_stex_tp (str): 국내거래소구분 (KRX:한국거래소, NXT:넥스트트레이드)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보
            - Body: 체결잔고 데이터
                - Main 필드 (25개):
                  - entr: 예수금 (String, 12)
                  - entr_d1: 예수금D+1 (String, 12)
                  - entr_d2: 예수금D+2 (String, 12)
                  - pymn_alow_amt: 출금가능금액 (String, 12)
                  - uncl_stk_amt: 미수확보금 (String, 12)
                  - repl_amt: 대용금 (String, 12)
                  - rght_repl_amt: 권리대용금 (String, 12)
                  - ord_alowa: 주문가능현금 (String, 12)
                  - ch_uncla: 현금미수금 (String, 12)
                  - crd_int_npay_gold: 신용이자미납금 (String, 12)
                  - etc_loana: 기타대여금 (String, 12)
                  - nrpy_loan: 미상환융자금 (String, 12)
                  - profa_ch: 증거금현금 (String, 12)
                  - repl_profa: 증거금대용 (String, 12)
                  - stk_buy_tot_amt: 주식매수총액 (String, 12)
                  - evlt_amt_tot: 평가금액합계 (String, 12)
                  - tot_pl_tot: 총손익합계 (String, 12)
                  - tot_pl_rt: 총손익률 (String, 12)
                  - tot_re_buy_alowa: 총재매수가능금액 (String, 12)
                  - 20ord_alow_amt: 20%주문가능금액 (String, 12)
                  - 30ord_alow_amt: 30%주문가능금액 (String, 12)
                  - 40ord_alow_amt: 40%주문가능금액 (String, 12)
                  - 50ord_alow_amt: 50%주문가능금액 (String, 12)
                  - 60ord_alow_amt: 60%주문가능금액 (String, 12)
                  - 100ord_alow_amt: 100%주문가능금액 (String, 12)
                  - crd_loan_tot: 신용융자합계 (String, 12)
                  - crd_loan_ls_tot: 신용융자대주합계 (String, 12)
                  - crd_grnt_rt: 신용담보비율 (String, 12)
                  - dpst_grnt_use_amt_amt: 예탁담보대출금액 (String, 12)
                  - grnt_loan_amt: 매도담보대출금액 (String, 12)
                - stk_cntr_remn: 종목별체결잔고 리스트
                  각 항목 필드 (13개):
                  - crd_tp: 신용구분 (String, 2)
                  - loan_dt: 대출일 (String, 8)
                  - expr_dt: 만기일 (String, 8)
                  - stk_cd: 종목번호 (String, 12)
                  - stk_nm: 종목명 (String, 30)
                  - setl_remn: 결제잔고 (String, 12)
                  - cur_qty: 현재잔고 (String, 12)
                  - cur_prc: 현재가 (String, 12)
                  - buy_uv: 매입단가 (String, 12)
                  - pur_amt: 매입금액 (String, 12)
                  - evlt_amt: 평가금액 (String, 12)
                  - evltv_prft: 평가손익 (String, 12)
                  - pl_rt: 손익률 (String, 12)
                  
    Raises:
        Exception: API 호출 실패 시
        
    Example:
        >>> result = await fn_kt00005(
        ...     token="access_token_here",
        ...     data={
        ...         "dmst_stex_tp": "KRX"  # 한국거래소
        ...     }
        ... )
        >>> print(f"예수금: {result['Body']['entr']}")
        >>> print(f"평가금액합계: {result['Body']['evlt_amt_tot']}")
    """
    logger.info("🏁 키움증권 체결잔고요청 (kt00005) 시작")
    
    if not token:
        token = await get_valid_access_token()
        logger.info(f"🔑 토큰 자동 획득: {token[:10]}...")
        
    if not data:
        logger.error("❌ data 매개변수가 필요합니다")
        return {
            'Code': 400,
            'Header': {},
            'Body': {'error': 'data 매개변수가 필요합니다'}
        }

    # 필수 필드 검증
    required_fields = ['dmst_stex_tp']
    for field in required_fields:
        if field not in data:
            logger.error(f"❌ 필수 필드 누락: {field}")
            return {
                'Code': 400,
                'Header': {},
                'Body': {'error': f'필수 필드 누락: {field}'}
            }

    logger.info(f"📊 요청 데이터: dmst_stex_tp={data['dmst_stex_tp']}")
    logger.info(f"🔄 연속조회: cont_yn={cont_yn}, next_key={next_key}")

    try:
        # 키움 API 호출
        url = f"{settings.get_base_url()}/api/dostk/acnt"
        
        headers = {
            "authorization": f"Bearer {token}",
            "api-id": "kt00005",
            "Content-Type": "application/json;charset=UTF-8",
            "cont-yn": cont_yn,
            "next-key": next_key
        }

        logger.info(f"🌐 API 호출: {url}")
        logger.info(f"📤 요청 본문: {json.dumps(data, ensure_ascii=False)}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 헤더 정보 추출
                response_header = {
                    'next-key': response.headers.get('next-key', ''),
                    'cont-yn': response.headers.get('cont-yn', 'N'),
                    'api-id': response.headers.get('api-id', 'kt00005')
                }
                
                # 응답 데이터 로깅
                if result:
                    body = result
                    logger.info(f"✅ 예수금: {body.get('entr', 'N/A')}")
                    logger.info(f"✅ 출금가능금액: {body.get('pymn_alow_amt', 'N/A')}")
                    logger.info(f"✅ 주문가능현금: {body.get('ord_alowa', 'N/A')}")
                    logger.info(f"✅ 평가금액합계: {body.get('evlt_amt_tot', 'N/A')}")
                    logger.info(f"✅ 총손익합계: {body.get('tot_pl_tot', 'N/A')}")
                    logger.info(f"✅ 총손익률: {body.get('tot_pl_rt', 'N/A')}")
                    
                    # 보유종목 개수 로깅
                    if 'stk_cntr_remn' in body and isinstance(body['stk_cntr_remn'], list):
                        stock_count = len(body['stk_cntr_remn'])
                        logger.info(f"✅ 보유종목 개수: {stock_count}개")
                        
                        # 각 종목 정보 로깅 (최대 5개까지만)
                        for idx, stock in enumerate(body['stk_cntr_remn'][:5]):
                            logger.info(f"  📈 종목 {idx+1}: {stock.get('stk_nm', 'N/A')}({stock.get('stk_cd', 'N/A')}) - "
                                      f"현재잔고: {stock.get('cur_qty', 'N/A')}, "
                                      f"평가손익: {stock.get('evltv_prft', 'N/A')}, "
                                      f"손익률: {stock.get('pl_rt', 'N/A')}")
                        
                        if stock_count > 5:
                            logger.info(f"  📊 외 {stock_count - 5}개 종목...")
                
                logger.info("🎉 키움증권 체결잔고요청 (kt00005) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00007(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 계좌별주문체결내역상세요청 (kt00007)
    
    계좌별주문체결내역상세요청 - 계좌의 주문 및 체결 내역 상세 정보 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - ord_dt (Optional[str]): 주문일자 YYYYMMDD (선택사항)
            - qry_tp (str): 조회구분 (1:주문순, 2:역순, 3:미체결, 4:체결내역만)
            - stk_bond_tp (str): 주식채권구분 (0:전체, 1:주식, 2:채권)
            - sell_tp (str): 매도수구분 (0:전체, 1:매도, 2:매수)
            - stk_cd (Optional[str]): 종목코드 (선택사항, 공백일때 전체종목)
            - fr_ord_no (Optional[str]): 시작주문번호 (선택사항, 공백일때 전체주문)
            - dmst_stex_tp (str): 국내거래소구분 (%:전체, KRX:한국거래소, NXT:넥스트트레이드, SOR:최선주문집행)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보 
            - Body: 주문체결내역 데이터
                - acnt_ord_cntr_prps_dtl: 계좌별주문체결내역상세 리스트
                  각 항목 필드 (22개):
                  - ord_no: 주문번호 (String, 7)
                  - stk_cd: 종목번호 (String, 12)
                  - trde_tp: 매매구분 (String, 20)
                  - crd_tp: 신용구분 (String, 20)
                  - ord_qty: 주문수량 (String, 10)
                  - ord_uv: 주문단가 (String, 10)
                  - cnfm_qty: 확인수량 (String, 10)
                  - acpt_tp: 접수구분 (String, 20)
                  - rsrv_tp: 반대여부 (String, 20)
                  - ord_tm: 주문시간 (String, 8)
                  - ori_ord: 원주문 (String, 7)
                  - stk_nm: 종목명 (String, 40)
                  - io_tp_nm: 주문구분 (String, 20)
                  - loan_dt: 대출일 (String, 8)
                  - cntr_qty: 체결수량 (String, 10)
                  - cntr_uv: 체결단가 (String, 10)
                  - ord_remnq: 주문잔량 (String, 10)
                  - comm_ord_tp: 통신구분 (String, 20)
                  - mdfy_cncl: 정정취소 (String, 20)
                  - cnfm_tm: 확인시간 (String, 8)
                  - dmst_stex_tp: 국내거래소구분 (String, 8)
                  - cond_uv: 스톱가 (String, 10)
                  
    Raises:
        Exception: API 호출 실패 시
        
    Example:
        >>> result = await fn_kt00007(
        ...     token="access_token_here",
        ...     data={
        ...         "ord_dt": "",  # 전체 주문일자
        ...         "qry_tp": "1",  # 주문순
        ...         "stk_bond_tp": "0",  # 전체
        ...         "sell_tp": "0",  # 전체
        ...         "stk_cd": "005930",  # 삼성전자
        ...         "fr_ord_no": "",  # 전체 주문
        ...         "dmst_stex_tp": "KRX"  # 한국거래소
        ...     }
        ... )
        >>> print(f"주문내역 개수: {len(result['Body']['acnt_ord_cntr_prps_dtl'])}")
    """
    logger.info("🏁 키움증권 계좌별주문체결내역상세요청 (kt00007) 시작")
    
    if not token:
        token = await get_valid_access_token()
        logger.info(f"🔑 토큰 자동 획득: {token[:10]}...")
        
    if not data:
        logger.error("❌ data 매개변수가 필요합니다")
        return {
            'Code': 400,
            'Header': {},
            'Body': {'error': 'data 매개변수가 필요합니다'}
        }

    # 필수 필드 검증
    required_fields = ['qry_tp', 'stk_bond_tp', 'sell_tp', 'dmst_stex_tp']
    for field in required_fields:
        if field not in data:
            logger.error(f"❌ 필수 필드 누락: {field}")
            return {
                'Code': 400,
                'Header': {},
                'Body': {'error': f'필수 필드 누락: {field}'}
            }

    logger.info(f"📊 요청 데이터: qry_tp={data['qry_tp']}, stk_bond_tp={data['stk_bond_tp']}, sell_tp={data['sell_tp']}, dmst_stex_tp={data['dmst_stex_tp']}")
    logger.info(f"📊 선택 필드: ord_dt={data.get('ord_dt', '')}, stk_cd={data.get('stk_cd', '')}, fr_ord_no={data.get('fr_ord_no', '')}")
    logger.info(f"🔄 연속조회: cont_yn={cont_yn}, next_key={next_key}")

    try:
        # 키움 API 호출
        url = f"{settings.get_base_url()}/api/dostk/acnt"
        
        headers = {
            "authorization": f"Bearer {token}",
            "api-id": "kt00007",
            "Content-Type": "application/json;charset=UTF-8",
            "cont-yn": cont_yn,
            "next-key": next_key
        }

        logger.info(f"🌐 API 호출: {url}")
        logger.info(f"📤 요청 본문: {json.dumps(data, ensure_ascii=False)}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 헤더 정보 추출
                response_header = {
                    'next-key': response.headers.get('next-key', ''),
                    'cont-yn': response.headers.get('cont-yn', 'N'),
                    'api-id': response.headers.get('api-id', 'kt00007')
                }
                
                # 응답 데이터 로깅
                if result and 'acnt_ord_cntr_prps_dtl' in result:
                    orders_list = result['acnt_ord_cntr_prps_dtl']
                    if isinstance(orders_list, list):
                        orders_count = len(orders_list)
                        logger.info(f"✅ 주문체결내역 개수: {orders_count}개")
                        
                        # 각 주문 정보 로깅 (최대 5개까지만)
                        for idx, order in enumerate(orders_list[:5]):
                            logger.info(f"  📈 주문 {idx+1}: {order.get('stk_nm', 'N/A')}({order.get('stk_cd', 'N/A')}) - "
                                      f"주문번호: {order.get('ord_no', 'N/A')}, "
                                      f"매매구분: {order.get('trde_tp', 'N/A')}, "
                                      f"주문수량: {order.get('ord_qty', 'N/A')}, "
                                      f"체결수량: {order.get('cntr_qty', 'N/A')}")
                        
                        if orders_count > 5:
                            logger.info(f"  📊 외 {orders_count - 5}개 주문...")
                    else:
                        logger.info("✅ 주문체결내역: 데이터 없음")
                
                logger.info("🎉 키움증권 계좌별주문체결내역상세요청 (kt00007) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00008(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 계좌별익일결제예정내역요청 (kt00008)
    
    계좌별익일결제예정내역요청 - 계좌의 익일 결제 예정 내역 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - strt_dcd_seq (Optional[str]): 시작결제번호 (선택사항, 7자리)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보
            - Body: 익일결제예정내역 데이터
                - Main 필드 (4개):
                  - trde_dt: 매매일자 (String, 8)
                  - setl_dt: 결제일자 (String, 8) 
                  - sell_amt_sum: 매도정산합 (String, 12)
                  - buy_amt_sum: 매수정산합 (String, 12)
                - acnt_nxdy_setl_frcs_prps_array: 계좌별익일결제예정내역배열 리스트
                  각 항목 필드 (15개):
                  - seq: 일련번호 (String, 7)
                  - stk_cd: 종목번호 (String, 12)
                  - loan_dt: 대출일 (String, 8)
                  - qty: 수량 (String, 12)
                  - engg_amt: 약정금액 (String, 12)
                  - cmsn: 수수료 (String, 12)
                  - incm_tax: 소득세 (String, 12)
                  - rstx: 농특세 (String, 12)
                  - stk_nm: 종목명 (String, 40)
                  - sell_tp: 매도수구분 (String, 10)
                  - unp: 단가 (String, 12)
                  - exct_amt: 정산금액 (String, 12)
                  - trde_tax: 거래세 (String, 12)
                  - resi_tax: 주민세 (String, 12)
                  - crd_tp: 신용구분 (String, 20)
                  
    Raises:
        Exception: API 호출 실패 시
        
    Example:
        >>> result = await fn_kt00008(
        ...     token="access_token_here",
        ...     data={
        ...         "strt_dcd_seq": ""  # 전체 결제내역
        ...     }
        ... )
        >>> print(f"매매일자: {result['Body']['trde_dt']}")
        >>> print(f"결제일자: {result['Body']['setl_dt']}")
    """
    logger.info("🏁 키움증권 계좌별익일결제예정내역요청 (kt00008) 시작")
    
    if not token:
        token = await get_valid_access_token()
        logger.info(f"🔑 토큰 자동 획득: {token[:10]}...")
        
    if not data:
        data = {}
        logger.info("📊 data가 없어서 빈 데이터로 요청")

    logger.info(f"📊 요청 데이터: strt_dcd_seq={data.get('strt_dcd_seq', '')}")
    logger.info(f"🔄 연속조회: cont_yn={cont_yn}, next_key={next_key}")

    try:
        # 키움 API 호출
        url = f"{settings.get_base_url()}/api/dostk/acnt"
        
        headers = {
            "authorization": f"Bearer {token}",
            "api-id": "kt00008",
            "Content-Type": "application/json;charset=UTF-8",
            "cont-yn": cont_yn,
            "next-key": next_key
        }

        logger.info(f"🌐 API 호출: {url}")
        logger.info(f"📤 요청 본문: {json.dumps(data, ensure_ascii=False)}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data, headers=headers)
            
            logger.info(f"📡 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 헤더 정보 추출
                response_header = {
                    'next-key': response.headers.get('next-key', ''),
                    'cont-yn': response.headers.get('cont-yn', 'N'),
                    'api-id': response.headers.get('api-id', 'kt00008')
                }
                
                # 응답 데이터 로깅
                if result:
                    body = result
                    logger.info(f"✅ 매매일자: {body.get('trde_dt', 'N/A')}")
                    logger.info(f"✅ 결제일자: {body.get('setl_dt', 'N/A')}")
                    logger.info(f"✅ 매도정산합: {body.get('sell_amt_sum', 'N/A')}")
                    logger.info(f"✅ 매수정산합: {body.get('buy_amt_sum', 'N/A')}")
                    
                    # 결제예정내역 개수 로깅
                    if 'acnt_nxdy_setl_frcs_prps_array' in body and isinstance(body['acnt_nxdy_setl_frcs_prps_array'], list):
                        settlement_count = len(body['acnt_nxdy_setl_frcs_prps_array'])
                        logger.info(f"✅ 결제예정내역 개수: {settlement_count}개")
                        
                        # 각 결제예정 정보 로깅 (최대 5개까지만)
                        for idx, settlement in enumerate(body['acnt_nxdy_setl_frcs_prps_array'][:5]):
                            logger.info(f"  📈 결제 {idx+1}: {settlement.get('stk_nm', 'N/A')}({settlement.get('stk_cd', 'N/A')}) - "
                                      f"일련번호: {settlement.get('seq', 'N/A')}, "
                                      f"수량: {settlement.get('qty', 'N/A')}, "
                                      f"정산금액: {settlement.get('exct_amt', 'N/A')}, "
                                      f"매도수구분: {settlement.get('sell_tp', 'N/A')}")
                        
                        if settlement_count > 5:
                            logger.info(f"  📊 외 {settlement_count - 5}개 결제예정...")
                    else:
                        logger.info("✅ 결제예정내역: 데이터 없음")
                
                logger.info("🎉 키움증권 계좌별익일결제예정내역요청 (kt00008) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00009(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 계좌별주문체결현황요청 (kt00009)
    
    계좌별주문체결현황요청 - 계좌별 주문 및 체결 현황 정보 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - ord_dt (Optional[str]): 주문일자 YYYYMMDD (선택사항)
            - stk_bond_tp (str): 주식채권구분 (0:전체, 1:주식, 2:채권)
            - mrkt_tp (str): 시장구분 (0:전체, 1:코스피, 2:코스닥, 3:OTCBB, 4:ECN)
            - sell_tp (str): 매도수구분 (0:전체, 1:매도, 2:매수)
            - qry_tp (str): 조회구분 (0:전체, 1:체결)
            - stk_cd (Optional[str]): 종목코드 (선택사항, 전문 조회할 종목코드)
            - fr_ord_no (Optional[str]): 시작주문번호 (선택사항)
            - dmst_stex_tp (str): 국내거래소구분 (%:전체, KRX:한국거래소, NXT:넥스트트레이드, SOR:최선주문집행)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보 
            - Body: 주문체결현황 데이터
                - tot_ord_cnt: 전체주문건수 (String, 5)
                - tot_cntr_cnt: 전체체결건수 (String, 5)
                - tot_unsett_cnt: 전체미체결건수 (String, 5)
                - acnt_ord_cntr_prst_array: 계좌별주문체결현황 리스트
                  각 항목 필드 (22개):
                  - ord_no: 주문번호 (String, 7)
                  - stk_cd: 종목코드 (String, 12)
                  - stk_nm: 종목명 (String, 40)
                  - trde_tp: 매매구분 (String, 20)
                  - crd_tp: 신용구분 (String, 20)
                  - ord_qty: 주문수량 (String, 10)
                  - ord_prc: 주문가격 (String, 10)
                  - cnfm_qty: 확인수량 (String, 10)
                  - cntr_qty: 체결수량 (String, 10)
                  - cntr_prc: 체결가격 (String, 10)
                  - acpt_dt: 접수일자 (String, 8)
                  - acpt_tm: 접수시간 (String, 6)
                  - ord_stcd: 주문상태코드 (String, 2)
                  - ord_stnm: 주문상태명 (String, 10)
                  - cmpr_prc: 대비가격 (String, 10)
                  - cmpr_pl_rt: 손익률 (String, 9)
                  - ord_dt: 주문일자 (String, 8)
                  - ord_tm: 주문시간 (String, 6)
                  - ord_remnq: 주문잔량 (String, 10)
                  - comm_ord_tp: 통신구분 (String, 20)
                  - ori_ord_no: 원주문번호 (String, 7)
                  - loan_dt: 대출일자 (String, 8)
                  
    Raises:
        ValueError: 필수 파라미터가 없거나 잘못된 값인 경우
        httpx.RequestError: 네트워크 요청 실패
        Exception: 기타 예상치 못한 오류
    """
    logger.info("📊 키움증권 계좌별주문체결현황요청 (kt00009) 시작")

    try:
        # 토큰 검증 및 획득
        if token is None:
            logger.info("🔑 OAuth 토큰 자동 획득 중...")
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        # 필수 필드 검증
        required_fields = {
            'stk_bond_tp': '주식채권구분',
            'mrkt_tp': '시장구분', 
            'sell_tp': '매도수구분',
            'qry_tp': '조회구분',
            'dmst_stex_tp': '국내거래소구분'
        }
        
        missing_fields = []
        for field, field_name in required_fields.items():
            if not data.get(field):
                missing_fields.append(f"{field}({field_name})")
        
        if missing_fields:
            raise ValueError(f"다음 필수 필드들이 누락되었습니다: {', '.join(missing_fields)}")

        # API 엔드포인트 및 헤더 설정
        url = settings.kiwoom_base_url + '/api/dostk/acnt'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00009',
        }

        # 요청 데이터 준비
        request_data = {}
        
        # 필수 필드
        request_data['stk_bond_tp'] = data['stk_bond_tp']
        request_data['mrkt_tp'] = data['mrkt_tp']
        request_data['sell_tp'] = data['sell_tp']
        request_data['qry_tp'] = data['qry_tp']
        request_data['dmst_stex_tp'] = data['dmst_stex_tp']
        
        # 선택 필드
        if data.get('ord_dt'):
            request_data['ord_dt'] = data['ord_dt']
        if data.get('stk_cd'):
            request_data['stk_cd'] = data['stk_cd']
        if data.get('fr_ord_no'):
            request_data['fr_ord_no'] = data['fr_ord_no']

        logger.info(f"📊 요청 파라미터:")
        logger.info(f"  - 주식채권구분 (stk_bond_tp): {request_data['stk_bond_tp']}")
        logger.info(f"  - 시장구분 (mrkt_tp): {request_data['mrkt_tp']}")
        logger.info(f"  - 매도수구분 (sell_tp): {request_data['sell_tp']}")
        logger.info(f"  - 조회구분 (qry_tp): {request_data['qry_tp']}")
        logger.info(f"  - 국내거래소구분 (dmst_stex_tp): {request_data['dmst_stex_tp']}")
        
        if data.get('ord_dt'):
            logger.info(f"  - 주문일자 (ord_dt): {request_data['ord_dt']}")
        if data.get('stk_cd'):
            logger.info(f"  - 종목코드 (stk_cd): {request_data['stk_cd']}")
        if data.get('fr_ord_no'):
            logger.info(f"  - 시작주문번호 (fr_ord_no): {request_data['fr_ord_no']}")
        
        logger.info(f"  - 연속조회여부: {cont_yn}")
        if next_key:
            logger.info(f"  - 연속조회키: {next_key}")

        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 응답 헤더 처리
        response_header = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00009')
        }
        
        logger.info(f"📡 응답 상태: {response.status_code}")
        logger.info(f"📋 응답 헤더: {response_header}")

        # 응답 처리
        if response.status_code == 200:
            result = response.json() if response.content else {}
            
            # 응답 데이터 로깅
            if result:
                body = result.get('Body', {})
                if body:
                    logger.info("✅ 주문체결현황 조회 완료:")
                    logger.info(f"✅ 전체주문건수: {body.get('tot_ord_cnt', 'N/A')}")
                    logger.info(f"✅ 전체체결건수: {body.get('tot_cntr_cnt', 'N/A')}")
                    logger.info(f"✅ 전체미체결건수: {body.get('tot_unsett_cnt', 'N/A')}")
                    
                    # 주문체결 내역 개수 로깅
                    if 'acnt_ord_cntr_prst_array' in body and isinstance(body['acnt_ord_cntr_prst_array'], list):
                        order_count = len(body['acnt_ord_cntr_prst_array'])
                        logger.info(f"✅ 주문체결 내역 개수: {order_count}개")
                        
                        # 각 주문 정보 로깅 (최대 5개까지만)
                        for idx, order in enumerate(body['acnt_ord_cntr_prst_array'][:5]):
                            logger.info(f"  📊 주문 {idx+1}: {order.get('stk_nm', 'N/A')}({order.get('stk_cd', 'N/A')}) - "
                                      f"주문번호: {order.get('ord_no', 'N/A')}, "
                                      f"매매구분: {order.get('trde_tp', 'N/A')}, "
                                      f"주문수량: {order.get('ord_qty', 'N/A')}, "
                                      f"체결수량: {order.get('cntr_qty', 'N/A')}, "
                                      f"주문상태: {order.get('ord_stnm', 'N/A')}")
                        
                        if order_count > 5:
                            logger.info(f"  📊 외 {order_count - 5}개 주문...")
                
                logger.info("🎉 키움증권 계좌별주문체결현황요청 (kt00009) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00010(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 주문인출가능금액요청 (kt00010)
    
    주문인출가능금액요청 - 종목별 주문가능금액 및 수량 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - io_amt (Optional[str]): 입출금액 (선택사항)
            - stk_cd (str): 종목번호 (12자리)
            - trde_tp (str): 매매구분 (1:매도, 2:매수)
            - trde_qty (Optional[str]): 매매수량 (선택사항)
            - uv (str): 매수가격 (10자리)
            - exp_buy_unp (Optional[str]): 예상매수단가 (선택사항)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보 
            - Body: 주문가능금액 데이터
                - profa_20ord_alow_amt: 증거금20%주문가능금액 (String, 12)
                - profa_20ord_alowq: 증거금20%주문가능수량 (String, 10)
                - profa_30ord_alow_amt: 증거금30%주문가능금액 (String, 12)
                - profa_30ord_alowq: 증거금30%주문가능수량 (String, 10)
                - profa_40ord_alow_amt: 증거금40%주문가능금액 (String, 12)
                - profa_40ord_alowq: 증거금40%주문가능수량 (String, 10)
                - profa_50ord_alow_amt: 증거금50%주문가능금액 (String, 12)
                - profa_50ord_alowq: 증거금50%주문가능수량 (String, 10)
                - profa_60ord_alow_amt: 증거금60%주문가능금액 (String, 12)
                - profa_60ord_alowq: 증거금60%주문가능수량 (String, 10)
                - profa_rdex_60ord_alow_amt: 증거금감면60%주문가능금 (String, 12)
                - profa_rdex_60ord_alowq: 증거금감면60%주문가능수 (String, 10)
                - profa_100ord_alow_amt: 증거금100%주문가능금액 (String, 12)
                - profa_100ord_alowq: 증거금100%주문가능수량 (String, 10)
                - pred_reu_alowa: 전일재사용가능금액 (String, 12)
                - tdy_reu_alowa: 금일재사용가능금액 (String, 12)
                - entr: 예수금 (String, 12)
                - repl_amt: 대용금 (String, 12)
                - uncla: 미수금 (String, 12)
                - ord_pos_repl: 주문가능대용 (String, 12)
                - ord_alowa: 주문가능현금 (String, 12)
                - wthd_alowa: 인출가능금액 (String, 12)
                - nxdy_wthd_alowa: 익일인출가능금액 (String, 12)
                - pur_amt: 매입금액 (String, 12)
                - cmsn: 수수료 (String, 12)
                - pur_exct_amt: 매입정산금 (String, 12)
                - d2entra: D2추정예수금 (String, 12)
                - profa_rdex_aplc_tp: 증거금감면적용구분 (String, 1) - 0:일반,1:60%감면
                  
    Raises:
        ValueError: 필수 파라미터가 없거나 잘못된 값인 경우
        httpx.RequestError: 네트워크 요청 실패
        Exception: 기타 예상치 못한 오류
    """
    logger.info("💳 키움증권 주문인출가능금액요청 (kt00010) 시작")

    try:
        # 토큰 검증 및 획득
        if token is None:
            logger.info("🔑 OAuth 토큰 자동 획득 중...")
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        # 필수 필드 검증
        required_fields = {
            'stk_cd': '종목번호',
            'trde_tp': '매매구분', 
            'uv': '매수가격'
        }
        
        missing_fields = []
        for field, field_name in required_fields.items():
            if not data.get(field):
                missing_fields.append(f"{field}({field_name})")
        
        if missing_fields:
            raise ValueError(f"다음 필수 필드들이 누락되었습니다: {', '.join(missing_fields)}")

        # API 엔드포인트 및 헤더 설정
        url = settings.kiwoom_base_url + '/api/dostk/acnt'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00010',
        }

        # 요청 데이터 준비
        request_data = {}
        
        # 필수 필드
        request_data['stk_cd'] = data['stk_cd']
        request_data['trde_tp'] = data['trde_tp']
        request_data['uv'] = data['uv']
        
        # 선택 필드
        if data.get('io_amt'):
            request_data['io_amt'] = data['io_amt']
        if data.get('trde_qty'):
            request_data['trde_qty'] = data['trde_qty']
        if data.get('exp_buy_unp'):
            request_data['exp_buy_unp'] = data['exp_buy_unp']

        logger.info(f"💳 요청 파라미터:")
        logger.info(f"  - 종목번호 (stk_cd): {request_data['stk_cd']}")
        logger.info(f"  - 매매구분 (trde_tp): {request_data['trde_tp']} ({'매도' if request_data['trde_tp'] == '1' else '매수'})")
        logger.info(f"  - 매수가격 (uv): {request_data['uv']}")
        
        if data.get('io_amt'):
            logger.info(f"  - 입출금액 (io_amt): {request_data['io_amt']}")
        if data.get('trde_qty'):
            logger.info(f"  - 매매수량 (trde_qty): {request_data['trde_qty']}")
        if data.get('exp_buy_unp'):
            logger.info(f"  - 예상매수단가 (exp_buy_unp): {request_data['exp_buy_unp']}")
        
        logger.info(f"  - 연속조회여부: {cont_yn}")
        if next_key:
            logger.info(f"  - 연속조회키: {next_key}")

        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 응답 헤더 처리
        response_header = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00010')
        }
        
        logger.info(f"📡 응답 상태: {response.status_code}")
        logger.info(f"📋 응답 헤더: {response_header}")

        # 응답 처리
        if response.status_code == 200:
            result = response.json() if response.content else {}
            
            # 응답 데이터 로깅
            if result:
                body = result.get('Body', {})
                if body:
                    logger.info("✅ 주문가능금액 조회 완료:")
                    logger.info(f"✅ 증거금20%주문가능금액: {body.get('profa_20ord_alow_amt', 'N/A')}")
                    logger.info(f"✅ 증거금20%주문가능수량: {body.get('profa_20ord_alowq', 'N/A')}")
                    logger.info(f"✅ 증거금30%주문가능금액: {body.get('profa_30ord_alow_amt', 'N/A')}")
                    logger.info(f"✅ 증거금30%주문가능수량: {body.get('profa_30ord_alowq', 'N/A')}")
                    logger.info(f"✅ 증거금40%주문가능금액: {body.get('profa_40ord_alow_amt', 'N/A')}")
                    logger.info(f"✅ 증거금40%주문가능수량: {body.get('profa_40ord_alowq', 'N/A')}")
                    logger.info(f"✅ 증거금50%주문가능금액: {body.get('profa_50ord_alow_amt', 'N/A')}")
                    logger.info(f"✅ 증거금50%주문가능수량: {body.get('profa_50ord_alowq', 'N/A')}")
                    logger.info(f"✅ 증거금60%주문가능금액: {body.get('profa_60ord_alow_amt', 'N/A')}")
                    logger.info(f"✅ 증거금60%주문가능수량: {body.get('profa_60ord_alowq', 'N/A')}")
                    logger.info(f"✅ 증거금100%주문가능금액: {body.get('profa_100ord_alow_amt', 'N/A')}")
                    logger.info(f"✅ 증거금100%주문가능수량: {body.get('profa_100ord_alowq', 'N/A')}")
                    logger.info(f"✅ 주문가능현금: {body.get('ord_alowa', 'N/A')}")
                    logger.info(f"✅ 인출가능금액: {body.get('wthd_alowa', 'N/A')}")
                    logger.info(f"✅ 예수금: {body.get('entr', 'N/A')}")
                    logger.info(f"✅ 증거금감면적용구분: {body.get('profa_rdex_aplc_tp', 'N/A')} ({'일반' if body.get('profa_rdex_aplc_tp') == '0' else '60%감면' if body.get('profa_rdex_aplc_tp') == '1' else 'N/A'})")
                
                logger.info("🎉 키움증권 주문인출가능금액요청 (kt00010) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00011(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 증거금율별주문가능수량조회요청 (kt00011)
    
    증거금율별주문가능수량조회요청 - 종목별 증거금율에 따른 주문가능수량 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - stk_cd (str): 종목번호 (12자리)
            - uv (Optional[str]): 매수가격 (선택사항, 10자리)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보 
            - Body: 증거금율별 주문가능수량 데이터
                - stk_profa_rt: 종목증거금율 (String, 15)
                - profa_rt: 계좌증거금율 (String, 15)
                - aplc_rt: 적용증거금율 (String, 15)
                - profa_20ord_alow_amt: 증거금20%주문가능금액 (String, 12)
                - profa_20ord_alowq: 증거금20%주문가능수량 (String, 12)
                - profa_20pred_reu_amt: 증거금20%전일재사용금액 (String, 12)
                - profa_20tdy_reu_amt: 증거금20%금일재사용금액 (String, 12)
                - profa_30ord_alow_amt: 증거금30%주문가능금액 (String, 12)
                - profa_30ord_alowq: 증거금30%주문가능수량 (String, 12)
                - profa_30pred_reu_amt: 증거금30%전일재사용금액 (String, 12)
                - profa_30tdy_reu_amt: 증거금30%금일재사용금액 (String, 12)
                - profa_40ord_alow_amt: 증거금40%주문가능금액 (String, 12)
                - profa_40ord_alowq: 증거금40%주문가능수량 (String, 12)
                - profa_40pred_reu_amt: 증거금40전일재사용금액 (String, 12)
                - profa_40tdy_reu_amt: 증거금40%금일재사용금액 (String, 12)
                - profa_50ord_alow_amt: 증거금50%주문가능금액 (String, 12)
                - profa_50ord_alowq: 증거금50%주문가능수량 (String, 12)
                - profa_50pred_reu_amt: 증거금50%전일재사용금액 (String, 12)
                - profa_50tdy_reu_amt: 증거금50%금일재사용금액 (String, 12)
                - profa_60ord_alow_amt: 증거금60%주문가능금액 (String, 12)
                - profa_60ord_alowq: 증거금60%주문가능수량 (String, 12)
                - profa_60pred_reu_amt: 증거금60%전일재사용금액 (String, 12)
                - profa_60tdy_reu_amt: 증거금60%금일재사용금액 (String, 12)
                - profa_100ord_alow_amt: 증거금100%주문가능금액 (String, 12)
                - profa_100ord_alowq: 증거금100%주문가능수량 (String, 12)
                - profa_100pred_reu_amt: 증거금100%전일재사용금액 (String, 12)
                - profa_100tdy_reu_amt: 증거금100%금일재사용금액 (String, 12)
                - min_ord_alow_amt: 미수불가주문가능금액 (String, 12)
                - min_ord_alowq: 미수불가주문가능수량 (String, 12)
                - min_pred_reu_amt: 미수불가전일재사용금액 (String, 12)
                - min_tdy_reu_amt: 미수불가금일재사용금액 (String, 12)
                - entr: 예수금 (String, 12)
                - repl_amt: 대용금 (String, 12)
                - uncla: 미수금 (String, 12)
                - ord_pos_repl: 주문가능대용 (String, 12)
                - ord_alowa: 주문가능현금 (String, 12)
                  
    Raises:
        ValueError: 필수 파라미터가 없거나 잘못된 값인 경우
        httpx.RequestError: 네트워크 요청 실패
        Exception: 기타 예상치 못한 오류
    """
    logger.info("📊 키움증권 증거금율별주문가능수량조회요청 (kt00011) 시작")

    try:
        # 토큰 검증 및 획득
        if token is None:
            logger.info("🔑 OAuth 토큰 자동 획득 중...")
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        # 필수 필드 검증
        required_fields = {
            'stk_cd': '종목번호'
        }
        
        missing_fields = []
        for field, field_name in required_fields.items():
            if not data.get(field):
                missing_fields.append(f"{field}({field_name})")
        
        if missing_fields:
            raise ValueError(f"다음 필수 필드들이 누락되었습니다: {', '.join(missing_fields)}")

        # API 엔드포인트 및 헤더 설정
        url = settings.kiwoom_base_url + '/api/dostk/acnt'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00011',
        }

        # 요청 데이터 준비
        request_data = {}
        
        # 필수 필드
        request_data['stk_cd'] = data['stk_cd']
        
        # 선택 필드
        if data.get('uv'):
            request_data['uv'] = data['uv']

        logger.info(f"📊 요청 파라미터:")
        logger.info(f"  - 종목번호 (stk_cd): {request_data['stk_cd']}")
        
        if data.get('uv'):
            logger.info(f"  - 매수가격 (uv): {request_data['uv']}")
        
        logger.info(f"  - 연속조회여부: {cont_yn}")
        if next_key:
            logger.info(f"  - 연속조회키: {next_key}")

        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 응답 헤더 처리
        response_header = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00011')
        }
        
        logger.info(f"📡 응답 상태: {response.status_code}")
        logger.info(f"📋 응답 헤더: {response_header}")

        # 응답 처리
        if response.status_code == 200:
            result = response.json() if response.content else {}
            
            # 응답 데이터 로깅
            if result:
                body = result.get('Body', {})
                if body:
                    logger.info("✅ 증거금율별 주문가능수량 조회 완료:")
                    logger.info(f"✅ 종목증거금율: {body.get('stk_profa_rt', 'N/A')}%")
                    logger.info(f"✅ 계좌증거금율: {body.get('profa_rt', 'N/A')}%")
                    logger.info(f"✅ 적용증거금율: {body.get('aplc_rt', 'N/A')}%")
                    
                    logger.info("📊 증거금율별 주문가능수량:")
                    logger.info(f"  - 증거금20%: 금액={body.get('profa_20ord_alow_amt', 'N/A')}, 수량={body.get('profa_20ord_alowq', 'N/A')}")
                    logger.info(f"  - 증거금30%: 금액={body.get('profa_30ord_alow_amt', 'N/A')}, 수량={body.get('profa_30ord_alowq', 'N/A')}")
                    logger.info(f"  - 증거금40%: 금액={body.get('profa_40ord_alow_amt', 'N/A')}, 수량={body.get('profa_40ord_alowq', 'N/A')}")
                    logger.info(f"  - 증거금50%: 금액={body.get('profa_50ord_alow_amt', 'N/A')}, 수량={body.get('profa_50ord_alowq', 'N/A')}")
                    logger.info(f"  - 증거금60%: 금액={body.get('profa_60ord_alow_amt', 'N/A')}, 수량={body.get('profa_60ord_alowq', 'N/A')}")
                    logger.info(f"  - 증거금100%: 금액={body.get('profa_100ord_alow_amt', 'N/A')}, 수량={body.get('profa_100ord_alowq', 'N/A')}")
                    logger.info(f"  - 미수불가: 금액={body.get('min_ord_alow_amt', 'N/A')}, 수량={body.get('min_ord_alowq', 'N/A')}")
                    
                    logger.info(f"✅ 주문가능현금: {body.get('ord_alowa', 'N/A')}")
                    logger.info(f"✅ 예수금: {body.get('entr', 'N/A')}")
                    logger.info(f"✅ 대용금: {body.get('repl_amt', 'N/A')}")
                    logger.info(f"✅ 미수금: {body.get('uncla', 'N/A')}")
                
                logger.info("🎉 키움증권 증거금율별주문가능수량조회요청 (kt00011) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00012(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 신용보증금율별주문가능수량조회요청 (kt00012)
    
    신용보증금율별주문가능수량조회요청 - 종목별 신용보증금율에 따른 주문가능수량 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터
            - stk_cd (str): 종목번호 (12자리)
            - uv (Optional[str]): 매수가격 (선택사항, 10자리)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보 
            - Body: 신용보증금율별 주문가능수량 데이터
                - stk_assr_rt: 종목보증금율 (String, 1)
                - stk_assr_rt_nm: 종목보증금율명 (String, 4)
                - assr_30ord_alow_amt: 보증금30%주문가능금액 (String, 12)
                - assr_30ord_alowq: 보증금30%주문가능수량 (String, 12)
                - assr_30pred_reu_amt: 보증금30%전일재사용금액 (String, 12)
                - assr_30tdy_reu_amt: 보증금30%금일재사용금액 (String, 12)
                - assr_40ord_alow_amt: 보증금40%주문가능금액 (String, 12)
                - assr_40ord_alowq: 보증금40%주문가능수량 (String, 12)
                - assr_40pred_reu_amt: 보증금40%전일재사용금액 (String, 12)
                - assr_40tdy_reu_amt: 보증금40%금일재사용금액 (String, 12)
                - assr_50ord_alow_amt: 보증금50%주문가능금액 (String, 12)
                - assr_50ord_alowq: 보증금50%주문가능수량 (String, 12)
                - assr_50pred_reu_amt: 보증금50%전일재사용금액 (String, 12)
                - assr_50tdy_reu_amt: 보증금50%금일재사용금액 (String, 12)
                - assr_60ord_alow_amt: 보증금60%주문가능금액 (String, 12)
                - assr_60ord_alowq: 보증금60%주문가능수량 (String, 12)
                - assr_60pred_reu_amt: 보증금60%전일재사용금액 (String, 12)
                - assr_60tdy_reu_amt: 보증금60%금일재사용금액 (String, 12)
                - entr: 예수금 (String, 12)
                - repl_amt: 대용금 (String, 12)
                - uncla: 미수금 (String, 12)
                - ord_pos_repl: 주문가능대용 (String, 12)
                - ord_alowa: 주문가능현금 (String, 12)
                - out_alowa: 미수가능금액 (String, 12)
                - out_pos_qty: 미수가능수량 (String, 12)
                - min_amt: 미수불가금액 (String, 12)
                - min_qty: 미수불가수량 (String, 12)
                  
    Raises:
        ValueError: 필수 파라미터가 없거나 잘못된 값인 경우
        httpx.RequestError: 네트워크 요청 실패
        Exception: 기타 예상치 못한 오류
    """
    logger.info("📊 키움증권 신용보증금율별주문가능수량조회요청 (kt00012) 시작")

    try:
        # 토큰 검증 및 획득
        if token is None:
            logger.info("🔑 OAuth 토큰 자동 획득 중...")
            token = await get_valid_access_token()
        
        # 데이터 검증
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        # 필수 필드 검증
        required_fields = {
            'stk_cd': '종목번호'
        }
        
        missing_fields = []
        for field, field_name in required_fields.items():
            if not data.get(field):
                missing_fields.append(f"{field}({field_name})")
        
        if missing_fields:
            raise ValueError(f"다음 필수 필드들이 누락되었습니다: {', '.join(missing_fields)}")

        # API 엔드포인트 및 헤더 설정
        url = settings.kiwoom_base_url + '/api/dostk/acnt'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00012',
        }

        # 요청 데이터 준비
        request_data = {}
        
        # 필수 필드
        request_data['stk_cd'] = data['stk_cd']
        
        # 선택 필드
        if data.get('uv'):
            request_data['uv'] = data['uv']

        logger.info(f"📊 요청 파라미터:")
        logger.info(f"  - 종목번호 (stk_cd): {request_data['stk_cd']}")
        
        if data.get('uv'):
            logger.info(f"  - 매수가격 (uv): {request_data['uv']}")
        
        logger.info(f"  - 연속조회여부: {cont_yn}")
        if next_key:
            logger.info(f"  - 연속조회키: {next_key}")

        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 응답 헤더 처리
        response_header = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00012')
        }
        
        logger.info(f"📡 응답 상태: {response.status_code}")
        logger.info(f"📋 응답 헤더: {response_header}")

        # 응답 처리
        if response.status_code == 200:
            result = response.json() if response.content else {}
            
            # 응답 데이터 로깅
            if result:
                body = result.get('Body', {})
                if body:
                    logger.info("✅ 신용보증금율별 주문가능수량 조회 완료:")
                    logger.info(f"✅ 종목보증금율: {body.get('stk_assr_rt', 'N/A')}% ({body.get('stk_assr_rt_nm', 'N/A')})")
                    
                    logger.info("📊 보증금율별 주문가능수량:")
                    logger.info(f"  - 보증금30%: 금액={body.get('assr_30ord_alow_amt', 'N/A')}, 수량={body.get('assr_30ord_alowq', 'N/A')}")
                    logger.info(f"  - 보증금40%: 금액={body.get('assr_40ord_alow_amt', 'N/A')}, 수량={body.get('assr_40ord_alowq', 'N/A')}")
                    logger.info(f"  - 보증금50%: 금액={body.get('assr_50ord_alow_amt', 'N/A')}, 수량={body.get('assr_50ord_alowq', 'N/A')}")
                    logger.info(f"  - 보증금60%: 금액={body.get('assr_60ord_alow_amt', 'N/A')}, 수량={body.get('assr_60ord_alowq', 'N/A')}")
                    
                    logger.info("💰 미수 관련:")
                    logger.info(f"  - 미수가능금액: {body.get('out_alowa', 'N/A')}")
                    logger.info(f"  - 미수가능수량: {body.get('out_pos_qty', 'N/A')}")
                    logger.info(f"  - 미수불가금액: {body.get('min_amt', 'N/A')}")
                    logger.info(f"  - 미수불가수량: {body.get('min_qty', 'N/A')}")
                    
                    logger.info(f"✅ 주문가능현금: {body.get('ord_alowa', 'N/A')}")
                    logger.info(f"✅ 예수금: {body.get('entr', 'N/A')}")
                    logger.info(f"✅ 대용금: {body.get('repl_amt', 'N/A')}")
                    logger.info(f"✅ 미수금: {body.get('uncla', 'N/A')}")
                
                logger.info("🎉 키움증권 신용보증금율별주문가능수량조회요청 (kt00012) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00013(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """
    키움증권 증거금세부내역조회요청 (kt00013)
    
    증거금세부내역조회요청 - 계좌의 증거금 세부 내역 정보 조회
    
    Args:
        token (Optional[str]): OAuth 토큰. None시 자동 획득
        data (Optional[Dict[str, Any]]): 요청 데이터 (이 API는 Body 파라미터 없음)
        cont_yn (str): 연속조회여부 (N: 최초, Y: 연속)
        next_key (str): 연속조회키 (연속조회시 필요)
        
    Returns:
        Dict[str, Any]: 키움 API 응답
            - Code: 응답코드
            - Header: 헤더 정보 
            - Body: 증거금 세부내역 데이터 (46개 필드)
                - tdy_reu_objt_amt: 금일재사용대상금액 (String, 15)
                - tdy_reu_use_amt: 금일재사용사용금액 (String, 15)
                - tdy_reu_alowa: 금일재사용가능금액 (String, 15)
                - tdy_reu_lmtt_amt: 금일재사용제한금액 (String, 15)
                - tdy_reu_alowa_fin: 금일재사용가능금액최종 (String, 15)
                - pred_reu_objt_amt: 전일재사용대상금액 (String, 15)
                - pred_reu_use_amt: 전일재사용사용금액 (String, 15)
                - pred_reu_alowa: 전일재사용가능금액 (String, 15)
                - pred_reu_lmtt_amt: 전일재사용제한금액 (String, 15)
                - pred_reu_alowa_fin: 전일재사용가능금액최종 (String, 15)
                - ch_amt: 현금금액 (String, 15)
                - ch_profa: 현금증거금 (String, 15)
                - use_pos_ch: 사용가능현금 (String, 15)
                - ch_use_lmtt_amt: 현금사용제한금액 (String, 15)
                - use_pos_ch_fin: 사용가능현금최종 (String, 15)
                - repl_amt_amt: 대용금액 (String, 15)
                - repl_profa: 대용증거금 (String, 15)
                - use_pos_repl: 사용가능대용 (String, 15)
                - repl_use_lmtt_amt: 대용사용제한금액 (String, 15)
                - use_pos_repl_fin: 사용가능대용최종 (String, 15)
                - crd_grnta_ch: 신용보증금현금 (String, 15)
                - crd_grnta_repl: 신용보증금대용 (String, 15)
                - crd_grnt_ch: 신용담보금현금 (String, 15)
                - crd_grnt_repl: 신용담보금대용 (String, 15)
                - uncla: 미수금 (String, 12)
                - ls_grnt_reu_gold: 대주담보금재사용금 (String, 15)
                - 20ord_alow_amt: 20%주문가능금액 (String, 15)
                - 30ord_alow_amt: 30%주문가능금액 (String, 15)
                - 40ord_alow_amt: 40%주문가능금액 (String, 15)
                - 50ord_alow_amt: 50%주문가능금액 (String, 15)
                - 60ord_alow_amt: 60%주문가능금액 (String, 15)
                - 100ord_alow_amt: 100%주문가능금액 (String, 15)
                - tdy_crd_rpya_loss_amt: 금일신용상환손실금액 (String, 15)
                - pred_crd_rpya_loss_amt: 전일신용상환손실금액 (String, 15)
                - tdy_ls_rpya_loss_repl_profa: 금일대주상환손실대용증거금 (String, 15)
                - pred_ls_rpya_loss_repl_profa: 전일대주상환손실대용증거금 (String, 15)
                - evlt_repl_amt_spg_use_skip: 평가대용금(현물사용제외) (String, 15)
                - evlt_repl_rt: 평가대용비율 (String, 15)
                - crd_repl_profa: 신용대용증거금 (String, 15)
                - ch_ord_repl_profa: 현금주문대용증거금 (String, 15)
                - crd_ord_repl_profa: 신용주문대용증거금 (String, 15)
                - crd_repl_conv_gold: 신용대용환산금 (String, 15)
                - repl_alowa: 대용가능금액(현금제한) (String, 15)
                - repl_alowa_2: 대용가능금액2(신용제한) (String, 15)
                - ch_repl_lck_gold: 현금대용부족금 (String, 15)
                - crd_repl_lck_gold: 신용대용부족금 (String, 15)
                - ch_ord_alow_repla: 현금주문가능대용금 (String, 15)
                - crd_ord_alow_repla: 신용주문가능대용금 (String, 15)
                - d2vexct_entr: D2가정산예수금 (String, 15)
                - d2ch_ord_alow_amt: D2현금주문가능금액 (String, 15)
                  
    Raises:
        ValueError: 필수 파라미터가 없거나 잘못된 값인 경우
        httpx.RequestError: 네트워크 요청 실패
        Exception: 기타 예상치 못한 오류
    """
    logger.info("📋 키움증권 증거금세부내역조회요청 (kt00013) 시작")

    try:
        # 토큰 검증 및 획득
        if token is None:
            logger.info("🔑 OAuth 토큰 자동 획득 중...")
            token = await get_valid_access_token()

        # API 엔드포인트 및 헤더 설정
        url = settings.kiwoom_base_url + '/api/dostk/acnt'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00013',
        }

        # 요청 데이터 준비 (이 API는 Body 파라미터 없음)
        request_data = {}

        logger.info(f"📋 요청 파라미터: (Body 파라미터 없음)")
        logger.info(f"  - 연속조회여부: {cont_yn}")
        if next_key:
            logger.info(f"  - 연속조회키: {next_key}")

        # HTTP 요청 실행
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        # 응답 헤더 처리
        response_header = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', 'kt00013')
        }
        
        logger.info(f"📡 응답 상태: {response.status_code}")
        logger.info(f"📋 응답 헤더: {response_header}")

        # 응답 처리
        if response.status_code == 200:
            result = response.json() if response.content else {}
            
            # 응답 데이터 로깅
            if result:
                body = result.get('Body', {})
                if body:
                    logger.info("✅ 증거금 세부내역 조회 완료:")
                    
                    # 재사용 관련 정보
                    logger.info("🔄 재사용 관련:")
                    logger.info(f"  - 금일재사용가능금액: {body.get('tdy_reu_alowa', 'N/A')}")
                    logger.info(f"  - 금일재사용사용금액: {body.get('tdy_reu_use_amt', 'N/A')}")
                    logger.info(f"  - 전일재사용가능금액: {body.get('pred_reu_alowa', 'N/A')}")
                    logger.info(f"  - 전일재사용사용금액: {body.get('pred_reu_use_amt', 'N/A')}")
                    
                    # 현금 관련 정보
                    logger.info("💰 현금 관련:")
                    logger.info(f"  - 현금금액: {body.get('ch_amt', 'N/A')}")
                    logger.info(f"  - 사용가능현금: {body.get('use_pos_ch', 'N/A')}")
                    logger.info(f"  - 사용가능현금최종: {body.get('use_pos_ch_fin', 'N/A')}")
                    
                    # 대용 관련 정보
                    logger.info("💎 대용 관련:")
                    logger.info(f"  - 대용금액: {body.get('repl_amt_amt', 'N/A')}")
                    logger.info(f"  - 사용가능대용: {body.get('use_pos_repl', 'N/A')}")
                    logger.info(f"  - 사용가능대용최종: {body.get('use_pos_repl_fin', 'N/A')}")
                    
                    # 주문가능금액 (증거금율별)
                    logger.info("📊 증거금율별 주문가능금액:")
                    logger.info(f"  - 20%: {body.get('20ord_alow_amt', 'N/A')}")
                    logger.info(f"  - 30%: {body.get('30ord_alow_amt', 'N/A')}")
                    logger.info(f"  - 40%: {body.get('40ord_alow_amt', 'N/A')}")
                    logger.info(f"  - 50%: {body.get('50ord_alow_amt', 'N/A')}")
                    logger.info(f"  - 60%: {body.get('60ord_alow_amt', 'N/A')}")
                    logger.info(f"  - 100%: {body.get('100ord_alow_amt', 'N/A')}")
                    
                    # 신용 관련 정보
                    logger.info("🏦 신용 관련:")
                    logger.info(f"  - 신용보증금현금: {body.get('crd_grnta_ch', 'N/A')}")
                    logger.info(f"  - 신용보증금대용: {body.get('crd_grnta_repl', 'N/A')}")
                    logger.info(f"  - 미수금: {body.get('uncla', 'N/A')}")
                    
                    logger.info(f"✅ 평가대용비율: {body.get('evlt_repl_rt', 'N/A')}%")
                
                logger.info("🎉 키움증권 증거금세부내역조회요청 (kt00013) 성공")
                return {
                    'Code': 200,
                    'Header': response_header,
                    'Body': result
                }
            else:
                error_text = response.text
                logger.error(f"❌ API 호출 실패: {response.status_code} - {error_text}")
                return {
                    'Code': response.status_code,
                    'Header': {},
                    'Body': {'error': error_text}
                }
                
    except httpx.RequestError as e:
        logger.error(f"❌ 네트워크 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': f'네트워크 오류: {str(e)}'}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00015(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 위탁종합거래내역요청 (kt00015)
    
    Args:
        token: OAuth Bearer 토큰
        data: 요청 데이터
            - strt_dt (str): 시작일자 (YYYYMMDD)
            - end_dt (str): 종료일자 (YYYYMMDD)
            - tp (str): 구분 (0:전체,1:입출금,2:입출고,3:매매,4:매수,5:매도,6:입금,7:출금,A:예탁담보대출입금,B:매도담보대출입금,C:현금상환,F:환전,M:입출금+환전,G:외화매수,H:외화매도,I:환전정산입금,J:환전정산출금)
            - stk_cd (str, optional): 종목코드
            - crnc_cd (str, optional): 통화코드
            - gds_tp (str): 상품구분 (0:전체, 1:국내주식, 2:수익증권, 3:해외주식, 4:금융상품)
            - frgn_stex_code (str, optional): 해외거래소코드
            - dmst_stex_tp (str): 국내거래소구분 (%:(전체),KRX:한국거래소,NXT:넥스트트레이드)
        cont_yn: 연속조회여부 ('N': 최초, 'Y': 연속)
        next_key: 연속조회키
        
    Returns:
        Dict containing:
        - Code: 응답코드
        - Header: 응답헤더 (next-key, cont-yn 포함)
        - Body: 응답본문 (위탁종합거래내역 배열)
    """
    if not token:
        logger.error("❌ 토큰이 제공되지 않았습니다")
        return {
            'Code': 401,
            'Header': {},
            'Body': {'error': '인증 토큰이 필요합니다'}
        }
    
    # 요청 데이터 준비
    if not data:
        data = {}
        
    request_data = {
        'strt_dt': data.get('strt_dt', ''),
        'end_dt': data.get('end_dt', ''), 
        'tp': data.get('tp', '0'),
        'stk_cd': data.get('stk_cd', ''),
        'crnc_cd': data.get('crnc_cd', ''),
        'gds_tp': data.get('gds_tp', '0'),
        'frgn_stex_code': data.get('frgn_stex_code', ''),
        'dmst_stex_tp': data.get('dmst_stex_tp', '%')
    }
    
    logger.info(f"📊 요청 파라미터:")
    logger.info(f"  - 시작일자: {request_data['strt_dt']}")
    logger.info(f"  - 종료일자: {request_data['end_dt']}")
    logger.info(f"  - 구분: {request_data['tp']}")
    logger.info(f"  - 종목코드: {request_data['stk_cd'] or '(전체)'}")
    logger.info(f"  - 통화코드: {request_data['crnc_cd'] or '(전체)'}")
    logger.info(f"  - 상품구분: {request_data['gds_tp']}")
    logger.info(f"  - 해외거래소코드: {request_data['frgn_stex_code'] or '(해당없음)'}")
    logger.info(f"  - 국내거래소구분: {request_data['dmst_stex_tp']}")
    logger.info(f"  - 연속조회여부: {cont_yn}")
    logger.info(f"  - 연속조회키: {next_key}")
    
    try:
        # API 엔드포인트 설정
        host = settings.get_api_host()
        endpoint = '/api/dostk/acnt'
        url = host + endpoint
        
        # HTTP 헤더 설정
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00015'
        }
        
        # API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=request_data,
                timeout=30.0
            )
            
            # 응답 헤더 정보
            response_headers = {
                'next-key': response.headers.get('next-key', ''),
                'cont-yn': response.headers.get('cont-yn', ''),
                'api-id': response.headers.get('api-id', '')
            }
            
            # 응답 데이터
            response_data = response.json()
            
            logger.info(f"📈 응답 상태 코드: {response.status_code}")
            logger.info(f"📤 응답 헤더: {response_headers}")
            
            if response.status_code == 200:
                body = response_data.get('Body', {})
                
                if 'trst_ovrl_trde_prps_array' in body:
                    transactions = body['trst_ovrl_trde_prps_array']
                    logger.info(f"📊 거래내역 건수: {len(transactions) if transactions else 0}건")
                    
                    # 거래내역 로깅 (처음 3건만)
                    if transactions and len(transactions) > 0:
                        logger.info(f"📋 거래내역 샘플:")
                        for i, transaction in enumerate(transactions[:3]):
                            logger.info(f"  [{i+1}] 거래일자: {transaction.get('trde_dt', '')}")
                            logger.info(f"      거래번호: {transaction.get('trde_no', '')}")
                            logger.info(f"      적요명: {transaction.get('rmrk_nm', '')}")
                            logger.info(f"      종목명: {transaction.get('stk_nm', '')}")
                            logger.info(f"      거래금액: {transaction.get('trde_amt', '')} 원")
                            logger.info(f"      거래구분: {transaction.get('io_tp_nm', '')}")
                            logger.info(f"      정산금액: {transaction.get('exct_amt', '')} 원")
                            logger.info(f"      통화코드: {transaction.get('crnc_cd', '')}")
                            logger.info(f"      처리시간: {transaction.get('proc_tm', '')}")
                            if i < len(transactions[:3]) - 1:
                                logger.info(f"      ---")
                else:
                    logger.info(f"📊 거래내역이 없습니다")
                    
            return {
                'Code': response.status_code,
                'Header': response_headers,
                'Body': response_data.get('Body', {})
            }
            
    except httpx.TimeoutException:
        logger.error("❌ API 호출 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.RequestError as e:
        logger.error(f"❌ API 호출 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00016(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 일별계좌수익률상세현황요청 (kt00016)
    
    Args:
        token: OAuth Bearer 토큰
        data: 요청 데이터
            - fr_dt (str): 평가시작일 (YYYYMMDD)
            - to_dt (str): 평가종료일 (YYYYMMDD)
        cont_yn: 연속조회여부 ('N': 최초, 'Y': 연속)
        next_key: 연속조회키
        
    Returns:
        Dict containing:
        - Code: 응답코드
        - Header: 응답헤더 (next-key, cont-yn 포함)
        - Body: 응답본문 (일별계좌수익률상세현황)
    """
    if not token:
        logger.error("❌ 토큰이 제공되지 않았습니다")
        return {
            'Code': 401,
            'Header': {},
            'Body': {'error': '인증 토큰이 필요합니다'}
        }
    
    # 요청 데이터 준비
    if not data:
        data = {}
        
    request_data = {
        'fr_dt': data.get('fr_dt', ''),
        'to_dt': data.get('to_dt', '')
    }
    
    logger.info(f"📈 요청 파라미터:")
    logger.info(f"  - 평가시작일: {request_data['fr_dt']}")
    logger.info(f"  - 평가종료일: {request_data['to_dt']}")
    logger.info(f"  - 연속조회여부: {cont_yn}")
    logger.info(f"  - 연속조회키: {next_key}")
    
    try:
        # API 엔드포인트 설정
        host = settings.get_api_host()
        endpoint = '/api/dostk/acnt'
        url = host + endpoint
        
        # HTTP 헤더 설정
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00016'
        }
        
        # API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=request_data,
                timeout=30.0
            )
            
            # 응답 헤더 정보
            response_headers = {
                'next-key': response.headers.get('next-key', ''),
                'cont-yn': response.headers.get('cont-yn', ''),
                'api-id': response.headers.get('api-id', '')
            }
            
            # 응답 데이터
            response_data = response.json()
            
            logger.info(f"📈 응답 상태 코드: {response.status_code}")
            logger.info(f"📤 응답 헤더: {response_headers}")
            
            if response.status_code == 200:
                body = response_data.get('Body', {})
                
                # 관리 정보
                logger.info(f"📋 관리정보:")
                logger.info(f"  - 관리사원번호: {body.get('mang_empno', '')}")
                logger.info(f"  - 관리자명: {body.get('mngr_nm', '')}")
                logger.info(f"  - 관리자지점: {body.get('dept_nm', '')}")
                
                # 예수금 정보
                logger.info(f"💰 예수금 정보:")
                logger.info(f"  - 예수금_초: {body.get('entr_fr', '')} 원")
                logger.info(f"  - 예수금_말: {body.get('entr_to', '')} 원")
                
                # 유가증권 정보
                logger.info(f"📊 유가증권 정보:")
                logger.info(f"  - 유가증권평가금액_초: {body.get('scrt_evlt_amt_fr', '')} 원")
                logger.info(f"  - 유가증권평가금액_말: {body.get('scrt_evlt_amt_to', '')} 원")
                
                # 대출 관련 정보
                logger.info(f"🏦 대출 관련:")
                logger.info(f"  - 신용융자금_초: {body.get('crd_loan_fr', '')} 원")
                logger.info(f"  - 신용융자금_말: {body.get('crd_loan_to', '')} 원")
                logger.info(f"  - 대출금_초: {body.get('loan_amt_fr', '')} 원")
                logger.info(f"  - 대출금_말: {body.get('loan_amt_to', '')} 원")
                
                # 수익률 정보
                logger.info(f"📈 수익률 정보:")
                logger.info(f"  - 순자산액계_초: {body.get('tot_amt_fr', '')} 원")
                logger.info(f"  - 순자산액계_말: {body.get('tot_amt_to', '')} 원")
                logger.info(f"  - 투자원금평잔: {body.get('invt_bsamt', '')} 원")
                logger.info(f"  - 평가손익: {body.get('evltv_prft', '')} 원")
                logger.info(f"  - 수익률: {body.get('prft_rt', '')}%")
                logger.info(f"  - 회전율: {body.get('tern_rt', '')}%")
                
                # 거래 정보
                logger.info(f"💸 거래 정보:")
                logger.info(f"  - 기간내총입금: {body.get('termin_tot_trns', '')} 원")
                logger.info(f"  - 기간내총출금: {body.get('termin_tot_pymn', '')} 원")
                logger.info(f"  - 기간내총입고: {body.get('termin_tot_inq', '')} 원")
                logger.info(f"  - 기간내총출고: {body.get('termin_tot_outq', '')} 원")
                    
            return {
                'Code': response.status_code,
                'Header': response_headers,
                'Body': response_data.get('Body', {})
            }
            
    except httpx.TimeoutException:
        logger.error("❌ API 호출 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.RequestError as e:
        logger.error(f"❌ API 호출 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00017(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 계좌별당일현황요청 (kt00017)
    
    Args:
        token: OAuth Bearer 토큰
        data: 요청 데이터 (이 API는 Body 파라미터가 없음)
        cont_yn: 연속조회여부 ('N': 최초, 'Y': 연속)
        next_key: 연속조회키
        
    Returns:
        Dict containing:
        - Code: 응답코드
        - Header: 응답헤더 (next-key, cont-yn 포함)
        - Body: 응답본문 (계좌별당일현황)
    """
    if not token:
        logger.error("❌ 토큰이 제공되지 않았습니다")
        return {
            'Code': 401,
            'Header': {},
            'Body': {'error': '인증 토큰이 필요합니다'}
        }
    
    # 요청 데이터 준비 (이 API는 Body 파라미터 없음)
    request_data = {}
    
    logger.info(f"📊 요청 파라미터: (Body 파라미터 없음)")
    logger.info(f"  - 연속조회여부: {cont_yn}")
    logger.info(f"  - 연속조회키: {next_key}")
    
    try:
        # API 엔드포인트 설정
        host = settings.get_api_host()
        endpoint = '/api/dostk/acnt'
        url = host + endpoint
        
        # HTTP 헤더 설정
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00017'
        }
        
        # API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=request_data,
                timeout=30.0
            )
            
            # 응답 헤더 정보
            response_headers = {
                'next-key': response.headers.get('next-key', ''),
                'cont-yn': response.headers.get('cont-yn', ''),
                'api-id': response.headers.get('api-id', '')
            }
            
            # 응답 데이터
            response_data = response.json()
            
            logger.info(f"📊 응답 상태 코드: {response.status_code}")
            logger.info(f"📤 응답 헤더: {response_headers}")
            
            if response.status_code == 200:
                body = response_data.get('Body', {})
                
                # D+2 관련 정보
                logger.info(f"📅 D+2 관련 정보:")
                logger.info(f"  - D+2추정예수금: {body.get('d2_entra', '')} 원")
                logger.info(f"  - 일반주식평가금액D+2: {body.get('gnrl_stk_evlt_amt_d2', '')} 원")
                logger.info(f"  - 예탁담보대출금D+2: {body.get('dpst_grnt_use_amt_d2', '')} 원")
                logger.info(f"  - 예탁담보주식평가금액D+2: {body.get('crd_stk_evlt_amt_d2', '')} 원")
                
                # 신용 관련 정보
                logger.info(f"🏦 신용 관련 정보:")
                logger.info(f"  - 신용이자미납금: {body.get('crd_int_npay_gold', '')} 원")
                logger.info(f"  - 신용융자금D+2: {body.get('crd_loan_d2', '')} 원")
                logger.info(f"  - 신용융자평가금D+2: {body.get('crd_loan_evlta_d2', '')} 원")
                logger.info(f"  - 신용대주담보금D+2: {body.get('crd_ls_grnt_d2', '')} 원")
                logger.info(f"  - 신용대주평가금D+2: {body.get('crd_ls_evlta_d2', '')} 원")
                logger.info(f"  - 신용이자금액: {body.get('crd_int_amt', '')} 원")
                
                # 입출금/입출고 정보
                logger.info(f"💰 입출금/입출고 정보:")
                logger.info(f"  - 입금금액: {body.get('ina_amt', '')} 원")
                logger.info(f"  - 출금금액: {body.get('outa', '')} 원")
                logger.info(f"  - 입고금액: {body.get('inq_amt', '')} 원")
                logger.info(f"  - 출고금액: {body.get('outq_amt', '')} 원")
                
                # 매매 관련 정보
                logger.info(f"📈 매매 관련 정보:")
                logger.info(f"  - 매도금액: {body.get('sell_amt', '')} 원")
                logger.info(f"  - 매수금액: {body.get('buy_amt', '')} 원")
                logger.info(f"  - 수수료: {body.get('cmsn', '')} 원")
                logger.info(f"  - 세금: {body.get('tax', '')} 원")
                
                # 대출 및 평가 정보
                logger.info(f"🏛️ 대출 및 평가 정보:")
                logger.info(f"  - 기타대여금: {body.get('etc_loana', '')} 원")
                logger.info(f"  - 주식매입자금대출금: {body.get('stk_pur_cptal_loan_amt', '')} 원")
                logger.info(f"  - RP평가금액: {body.get('rp_evlt_amt', '')} 원")
                logger.info(f"  - 채권평가금액: {body.get('bd_evlt_amt', '')} 원")
                logger.info(f"  - ELS평가금액: {body.get('elsevlt_amt', '')} 원")
                
                # 기타 정보
                logger.info(f"💸 기타 정보:")
                logger.info(f"  - 매도대금담보대출이자금액: {body.get('sel_prica_grnt_loan_int_amt_amt', '')} 원")
                logger.info(f"  - 배당금액: {body.get('dvida_amt', '')} 원")
                    
            return {
                'Code': response.status_code,
                'Header': response_headers,
                'Body': response_data.get('Body', {})
            }
            
    except httpx.TimeoutException:
        logger.error("❌ API 호출 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.RequestError as e:
        logger.error(f"❌ API 호출 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }

async def fn_kt00018(
    token: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    cont_yn: str = 'N',
    next_key: str = ''
) -> Dict[str, Any]:
    """키움증권 계좌평가잔고내역요청 (kt00018)
    
    Args:
        token: OAuth Bearer 토큰
        data: 요청 데이터
            - qry_tp (str): 조회구분 (1:합산, 2:개별)
            - dmst_stex_tp (str): 국내거래소구분 (KRX:한국거래소, NXT:넥스트트레이드)
        cont_yn: 연속조회여부 ('N': 최초, 'Y': 연속)
        next_key: 연속조회키
        
    Returns:
        Dict containing:
        - Code: 응답코드
        - Header: 응답헤더 (next-key, cont-yn 포함)
        - Body: 응답본문 (계좌평가잔고내역)
    """
    if not token:
        logger.error("❌ 토큰이 제공되지 않았습니다")
        return {
            'Code': 401,
            'Header': {},
            'Body': {'error': '인증 토큰이 필요합니다'}
        }
    
    # 요청 데이터 준비
    if not data:
        data = {}
        
    request_data = {
        'qry_tp': data.get('qry_tp', '1'),
        'dmst_stex_tp': data.get('dmst_stex_tp', 'KRX')
    }
    
    logger.info(f"📋 요청 파라미터:")
    logger.info(f"  - 조회구분: {request_data['qry_tp']} ({'합산' if request_data['qry_tp'] == '1' else '개별'})")
    logger.info(f"  - 국내거래소구분: {request_data['dmst_stex_tp']}")
    logger.info(f"  - 연속조회여부: {cont_yn}")
    logger.info(f"  - 연속조회키: {next_key}")
    
    try:
        # API 엔드포인트 설정
        host = settings.get_api_host()
        endpoint = '/api/dostk/acnt'
        url = host + endpoint
        
        # HTTP 헤더 설정
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': 'kt00018'
        }
        
        # API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=request_data,
                timeout=30.0
            )
            
            # 응답 헤더 정보
            response_headers = {
                'next-key': response.headers.get('next-key', ''),
                'cont-yn': response.headers.get('cont-yn', ''),
                'api-id': response.headers.get('api-id', '')
            }
            
            # 응답 데이터
            response_data = response.json()
            
            logger.info(f"📋 응답 상태 코드: {response.status_code}")
            logger.info(f"📤 응답 헤더: {response_headers}")
            
            if response.status_code == 200:
                body = response_data.get('Body', {})
                
                # 포트폴리오 요약 정보
                logger.info(f"💼 포트폴리오 요약:")
                logger.info(f"  - 총매입금액: {body.get('tot_pur_amt', '')} 원")
                logger.info(f"  - 총평가금액: {body.get('tot_evlt_amt', '')} 원")
                logger.info(f"  - 총평가손익금액: {body.get('tot_evlt_pl', '')} 원")
                logger.info(f"  - 총수익률: {body.get('tot_prft_rt', '')}%")
                logger.info(f"  - 추정예탁자산: {body.get('prsm_dpst_aset_amt', '')} 원")
                
                # 대출 관련 정보
                logger.info(f"🏦 대출 관련:")
                logger.info(f"  - 총대출금: {body.get('tot_loan_amt', '')} 원")
                logger.info(f"  - 총융자금액: {body.get('tot_crd_loan_amt', '')} 원")
                logger.info(f"  - 총대주금액: {body.get('tot_crd_ls_amt', '')} 원")
                
                # 계좌평가잔고 상세 정보
                if 'acnt_evlt_remn_indv_tot' in body:
                    holdings = body['acnt_evlt_remn_indv_tot']
                    logger.info(f"📊 보유종목 수: {len(holdings) if holdings else 0}개")
                    
                    # 보유종목 로깅 (처음 5개만)
                    if holdings and len(holdings) > 0:
                        logger.info(f"📈 보유종목 상세 (상위 5개):")
                        for i, holding in enumerate(holdings[:5]):
                            logger.info(f"  [{i+1}] {holding.get('stk_nm', '')} ({holding.get('stk_cd', '')})")
                            logger.info(f"      현재가: {holding.get('cur_prc', '')} 원")
                            logger.info(f"      매입가: {holding.get('pur_pric', '')} 원")
                            logger.info(f"      보유수량: {holding.get('rmnd_qty', '')} 주")
                            logger.info(f"      평가금액: {holding.get('evlt_amt', '')} 원")
                            logger.info(f"      평가손익: {holding.get('evltv_prft', '')} 원")
                            logger.info(f"      수익률: {holding.get('prft_rt', '')}%")
                            logger.info(f"      보유비중: {holding.get('poss_rt', '')}%")
                            logger.info(f"      신용구분: {holding.get('crd_tp_nm', '')}")
                            if i < len(holdings[:5]) - 1:
                                logger.info(f"      ---")
                else:
                    logger.info(f"📊 보유종목이 없습니다")
                    
            return {
                'Code': response.status_code,
                'Header': response_headers,
                'Body': response_data.get('Body', {})
            }
            
    except httpx.TimeoutException:
        logger.error("❌ API 호출 타임아웃")
        return {
            'Code': 408,
            'Header': {},
            'Body': {'error': 'Request timeout'}
        }
    except httpx.RequestError as e:
        logger.error(f"❌ API 호출 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }


# ============== 공통 유틸리티 함수 ==============

async def _execute_kt_api(
    api_id: str,
    log_message: str,
    token: Optional[str],
    data: Optional[Dict[str, Any]],
    cont_yn: str,
    next_key: str,
    required_fields: List[str]
) -> Dict[str, Any]:
    """
    kt00xxx API 공통 실행 함수
    
    Args:
        api_id: API ID (예: kt00007)
        log_message: 로그 메시지
        token: 접근토큰
        data: 요청 데이터
        cont_yn: 연속조회여부
        next_key: 연속조회키
        required_fields: 필수 필드 리스트
    """
    logger.info(f"{log_message} 시작 ({api_id})")

    try:
        if token is None:
            token = await get_valid_access_token()
        
        if data is None:
            raise ValueError("요청 데이터가 필요합니다")
        
        # 필수 필드 검증
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValueError(f"다음 필드들이 필요합니다: {', '.join(missing_fields)}")

        url = settings.kiwoom_base_url + '/api/dostk/acnt'
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'cont-yn': cont_yn,
            'next-key': next_key,
            'api-id': api_id,
        }

        # 요청 데이터는 필수 필드만 포함
        request_data = {field: data[field] for field in required_fields}
        
        logger.info(f"📊 요청 데이터: {request_data}")

        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=request_data)

        response_headers = {
            'next-key': response.headers.get('next-key', ''),
            'cont-yn': response.headers.get('cont-yn', 'N'),
            'api-id': response.headers.get('api-id', api_id)
        }
        
        response_body = response.json() if response.content else {}
        
        if response.status_code == 200:
            logger.info(f"✅ {api_id} 요청 성공")
        else:
            logger.error(f"❌ {api_id} 요청 실패: {response.status_code}")

        return {
            'Code': response.status_code,
            'Header': response_headers,
            'Body': response_body
        }

    except Exception as e:
        logger.error(f"💥 {api_id} 처리 실패: {str(e)}")
        return {
            'Code': 500,
            'Header': {},
            'Body': {'error': str(e)}
        }