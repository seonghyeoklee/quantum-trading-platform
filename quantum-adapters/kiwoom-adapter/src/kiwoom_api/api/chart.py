"""키움 API 차트 라우터

키움 API 차트 관련 fn_ka**** 함수 직접 호출 엔드포인트
"""

import logging
import sys
from pathlib import Path

from fastapi import APIRouter

# Handle both relative and absolute imports for different execution contexts
try:
    from ..models.kiwoom_request import (
        KiwoomStockChartApiRequest, 
        KiwoomStockMinuteChartApiRequest, 
        KiwoomStockWeeklyChartApiRequest, 
        KiwoomStockYearlyChartApiRequest, 
        KiwoomStockTickChartApiRequest, 
        KiwoomSectorTickChartApiRequest, 
        KiwoomInvestorInstitutionChartApiRequest, 
        KiwoomIntradayInvestorTradeChartApiRequest, 
        KiwoomSectorMinuteChartApiRequest, 
        KiwoomSectorDailyChartApiRequest, 
        KiwoomApiResponse
    )
    from ..functions.chart import (
        fn_ka10081, fn_ka10080, fn_ka10082, fn_ka10094, fn_ka10079, 
        fn_ka20004, fn_ka10060, fn_ka10064, fn_ka20005, fn_ka20006, 
        fn_ka20007, fn_ka20008, fn_ka20019, fn_ka10083
    )
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from kiwoom_api.models.kiwoom_request import (
        KiwoomStockChartApiRequest, 
        KiwoomStockMinuteChartApiRequest, 
        KiwoomStockWeeklyChartApiRequest, 
        KiwoomStockYearlyChartApiRequest, 
        KiwoomStockTickChartApiRequest, 
        KiwoomSectorTickChartApiRequest, 
        KiwoomInvestorInstitutionChartApiRequest, 
        KiwoomIntradayInvestorTradeChartApiRequest, 
        KiwoomSectorMinuteChartApiRequest, 
        KiwoomSectorDailyChartApiRequest, 
        KiwoomApiResponse
    )
    from kiwoom_api.functions.chart import (
        fn_ka10081, fn_ka10080, fn_ka10082, fn_ka10094, fn_ka10079, 
        fn_ka20004, fn_ka10060, fn_ka10064, fn_ka20005, fn_ka20006, 
        fn_ka20007, fn_ka20008, fn_ka20019, fn_ka10083
    )

logger = logging.getLogger(__name__)

router = APIRouter(tags=["차트 API"])


@router.post(
    "/api/fn_ka10081",
    response_model=KiwoomApiResponse,
    summary="키움증권 주식일봉차트조회 (ka10081)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10081 함수 직접 호출"
)
async def api_fn_ka10081(request: KiwoomStockChartApiRequest) -> KiwoomApiResponse:
    """키움증권 주식일봉차트조회 (ka10081)

    키움 API 스펙에 완전히 맞춘 fn_ka10081 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환

    Args:
        request: 차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - stk_cd: 종목코드 (예: '{종목코드}')
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                  - upd_stkpc_tp: 수정주가구분 ('0' or '1')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')

    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디 (차트 데이터)
    """
    # fn_ka10081 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10081(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )

    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka10080",
    response_model=KiwoomApiResponse,
    summary="키움증권 주식분봉차트조회 (ka10080)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10080 함수 직접 호출"
)
async def api_fn_ka10080(request: KiwoomStockMinuteChartApiRequest) -> KiwoomApiResponse:
    """키움증권 주식분봉차트조회 (ka10080)

    키움 API 스펙에 완전히 맞춘 fn_ka10080 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환

    Args:
        request: 분봉차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - stk_cd: 종목코드 (예: '{종목코드}')
                  - tic_scope: 틱범위 ('1':1분, '3':3분, '5':5분, '10':10분, '15':15분, '30':30분, '45':45분, '60':60분)
                  - upd_stkpc_tp: 수정주가구분 ('0' or '1')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')

    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더
        - Body: 키움 API 응답 바디 (분봉차트 데이터)
    """
    # fn_ka10080 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10080(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )

    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka10082",
    response_model=KiwoomApiResponse,
    summary="키움증권 주식주봉차트조회 (ka10082)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10082 함수 직접 호출"
)
async def api_fn_ka10082(request: KiwoomStockWeeklyChartApiRequest) -> KiwoomApiResponse:
    """키움증권 주식주봉차트조회 (ka10082)
    
    키움 API 스펙에 완전히 맞춘 fn_ka10082 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 주봉차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - stk_cd: 종목코드 (예: '{종목코드}')
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                  - upd_stkpc_tp: 수정주가구분 ('0' or '1')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (주봉차트 데이터)
    """
    # fn_ka10082 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10082(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka10094",
    response_model=KiwoomApiResponse,
    summary="키움증권 주식년봉차트조회 (ka10094)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10094 함수 직접 호출"
)
async def api_fn_ka10094(request: KiwoomStockYearlyChartApiRequest) -> KiwoomApiResponse:
    """키움증권 주식년봉차트조회 (ka10094)
    
    키움 API 스펙에 완전히 맞춘 fn_ka10094 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 년봉차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - stk_cd: 종목코드 (예: '{종목코드}')
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                  - upd_stkpc_tp: 수정주가구분 ('0' or '1')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (년봉차트 데이터)
    """
    # fn_ka10094 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10094(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka10079",
    response_model=KiwoomApiResponse,
    summary="키움증권 주식틱차트조회 (ka10079)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10079 함수 직접 호출"
)
async def api_fn_ka10079(request: KiwoomStockTickChartApiRequest) -> KiwoomApiResponse:
    """키움증권 주식틱차트조회 (ka10079)
    
    키움 API 스펙에 완전히 맞춘 fn_ka10079 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 틱차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - stk_cd: 종목코드 (예: '{종목코드}')
                  - tic_scope: 틱범위 ('1':1틱, '3':3틱, '5':5틱, '10':10틱, '30':30틱)
                  - upd_stkpc_tp: 수정주가구분 ('0' or '1')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (틱차트 데이터)
    """
    # fn_ka10079 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10079(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka20004",
    response_model=KiwoomApiResponse,
    summary="키움증권 업종틱차트조회 (ka20004)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka20004 함수 직접 호출"
)
async def api_fn_ka20004(request: KiwoomSectorTickChartApiRequest) -> KiwoomApiResponse:
    """키움증권 업종틱차트조회 (ka20004)
    
    키움 API 스펙에 완전히 맞춘 fn_ka20004 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 업종틱차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                     101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
                  - tic_scope: 틱범위 ('1':1틱, '3':3틱, '5':5틱, '10':10틱, '30':30틱)
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (업종틱차트 데이터)
    """
    # fn_ka20004 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka20004(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka10060",
    response_model=KiwoomApiResponse,
    summary="키움증권 종목별투자자기관별차트조회 (ka10060)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10060 함수 직접 호출"
)
async def api_fn_ka10060(request: KiwoomInvestorInstitutionChartApiRequest) -> KiwoomApiResponse:
    """키움증권 종목별투자자기관별차트조회 (ka10060)
    
    키움 API 스펙에 완전히 맞춘 fn_ka10060 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 투자자기관별차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - dt: 일자 YYYYMMDD (예: '{날짜}')
                  - stk_cd: 종목코드 (거래소별 종목코드: KRX:{종목코드}, NXT:{종목코드}_NX, SOR:{종목코드}_AL)
                  - amt_qty_tp: 금액수량구분 ('1':금액, '2':수량)
                  - trde_tp: 매매구분 ('0':순매수, '1':매수, '2':매도)
                  - unit_tp: 단위구분 ('1000':천주, '1':단주)
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (투자자기관별차트 데이터)
    """
    # fn_ka10060 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10060(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka10064",
    response_model=KiwoomApiResponse,
    summary="키움증권 장중투자자별매매차트조회 (ka10064)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10064 함수 직접 호출"
)
async def api_fn_ka10064(request: KiwoomIntradayInvestorTradeChartApiRequest) -> KiwoomApiResponse:
    """키움증권 장중투자자별매매차트조회 (ka10064)
    
    키움 API 스펙에 완전히 맞춘 fn_ka10064 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 장중투자자별매매차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - mrkt_tp: 시장구분 ('000':전체, '001':코스피, '101':코스닥)
                  - amt_qty_tp: 금액수량구분 ('1':금액, '2':수량)
                  - trde_tp: 매매구분 ('0':순매수, '1':매수, '2':매도)
                  - stk_cd: 종목코드 (거래소별 종목코드: KRX:{종목코드}, NXT:{종목코드}_NX, SOR:{종목코드}_AL)
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (장중투자자별매매차트 데이터)
    """
    # fn_ka10064 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10064(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka20005",
    response_model=KiwoomApiResponse,
    summary="키움증권 업종분봉조회 (ka20005)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka20005 함수 직접 호출"
)
async def api_fn_ka20005(request: KiwoomSectorMinuteChartApiRequest) -> KiwoomApiResponse:
    """키움증권 업종분봉조회 (ka20005)
    
    키움 API 스펙에 완전히 맞춘 fn_ka20005 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 업종분봉조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                     101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
                  - tic_scope: 틱범위 ('1':1분, '3':3분, '5':5분, '10':10분, '30':30분)
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (업종분봉차트 데이터)
    """
    # fn_ka20005 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka20005(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka20006",
    response_model=KiwoomApiResponse,
    summary="키움증권 업종일봉조회 (ka20006)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka20006 함수 직접 호출"
)
async def api_fn_ka20006(request: KiwoomSectorDailyChartApiRequest) -> KiwoomApiResponse:
    """키움증권 업종일봉조회 (ka20006)
    
    키움 API 스펙에 완전히 맞춘 fn_ka20006 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 업종일봉조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                     101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (업종일봉차트 데이터)
    """
    # fn_ka20006 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka20006(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka20007",
    response_model=KiwoomApiResponse,
    summary="키움증권 업종주봉조회 (ka20007)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka20007 함수 직접 호출"
)
async def api_fn_ka20007(request: KiwoomSectorDailyChartApiRequest) -> KiwoomApiResponse:
    """키움증권 업종주봉조회 (ka20007)
    
    키움 API 스펙에 완전히 맞춘 fn_ka20007 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 업종주봉조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                     101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (업종주봉차트 데이터)
    """
    # fn_ka20007 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka20007(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka20008",
    response_model=KiwoomApiResponse,
    summary="키움증권 업종월봉조회 (ka20008)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka20008 함수 직접 호출"
)
async def api_fn_ka20008(request: KiwoomSectorDailyChartApiRequest) -> KiwoomApiResponse:
    """키움증권 업종월봉조회 (ka20008)
    
    키움 API 스펙에 완전히 맞춘 fn_ka20008 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 업종월봉조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                     101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (업종월봉차트 데이터)
    """
    # fn_ka20008 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka20008(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka20019",
    response_model=KiwoomApiResponse,
    summary="키움증권 업종년봉조회 (ka20019)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka20019 함수 직접 호출"
)
async def api_fn_ka20019(request: KiwoomSectorDailyChartApiRequest) -> KiwoomApiResponse:
    """키움증권 업종년봉조회 (ka20019)
    
    키움 API 스펙에 완전히 맞춘 fn_ka20019 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 업종년봉조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - inds_cd: 업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 
                                     101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (업종년봉차트 데이터)
    """
    # fn_ka20019 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka20019(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)


@router.post(
    "/api/fn_ka10083",
    response_model=KiwoomApiResponse,
    summary="키움증권 주식월봉차트조회 (ka10083)",
    description="키움 API 스펙에 완전히 맞춘 fn_ka10083 함수 직접 호출"
)
async def api_fn_ka10083(request: KiwoomStockChartApiRequest) -> KiwoomApiResponse:
    """키움증권 주식월봉차트조회 (ka10083)
    
    키움 API 스펙에 완전히 맞춘 fn_ka10083 함수 직접 호출
    사용자 제공 코드와 동일한 응답 형식으로 반환
    
    Args:
        request: 주식월봉차트조회 요청 데이터 (토큰 자동 관리)
                - data: 차트조회 파라미터
                  - stk_cd: 종목코드 (거래소별 종목코드: KRX:{종목코드}, NXT:{종목코드}_NX, SOR:{종목코드}_AL)
                  - base_dt: 기준일자 YYYYMMDD (예: '{날짜}')
                  - upd_stkpc_tp: 수정주가구분 ('0' or '1')
                - cont_yn: 연속조회여부 ('Y' or 'N', 기본값: 'N')
                - next_key: 연속조회키 (기본값: '')
    
    Returns:
        KiwoomApiResponse containing:
        - Code: HTTP 상태 코드
        - Header: 키움 API 응답 헤더  
        - Body: 키움 API 응답 바디 (주식월봉차트 데이터)
    """
    # fn_ka10083 함수 직접 호출 (키움 스타일, 토큰 자동 관리)
    result = await fn_ka10083(
        data=request.data.model_dump(),
        cont_yn=request.cont_yn,
        next_key=request.next_key
    )
    
    # KiwoomApiResponse 모델로 반환
    return KiwoomApiResponse(**result)