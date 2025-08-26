"""
키움 API 종목정보 및 주식 거래주문 REST API 엔드포인트
함수명 기준으로 API 경로 매핑: /api/fn_ka10001, /api/fn_kt10000
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header, Query
from fastapi.responses import JSONResponse

try:
    # Stock models
    from ..models.stock import (
        StockInfoRequest, StockListRequest, IndustryCodeRequest, 
        WatchlistRequest, ProgramTradeRequest, StockBuyOrderRequest,
        StockSellOrderRequest, StockModifyOrderRequest, StockCancelOrderRequest
    )
    # Kiwoom request models
    from ..models.kiwoom_request import (
        KiwoomStockOrderbookRequest, KiwoomStockHistoricalRequest,
        KiwoomStockMinuteRequest, KiwoomStockMarketInfoRequest,
        KiwoomNewStockRightsRequest, KiwoomDailyInstitutionalTradeRequest,
        KiwoomStockInstitutionalTrendRequest
    )
    # Response models
    from ..models.orderbook import OrderbookApiResponse, OrderbookResponse, OrderbookData
    from ..models.chart import (
        ChartApiResponse, ChartResponse, MinuteChartApiResponse, MinuteChartResponse,
        MarketInfoApiResponse, MarketInfoResponse, NewStockRightsApiResponse,
        NewStockRightsResponse, DailyInstitutionalTradeApiResponse,
        DailyInstitutionalTradeResponse, StockInstitutionalTrendApiResponse,
        StockInstitutionalTrendResponse
    )
    # Stock business functions
    from ..functions.stock import (
        fn_ka10001, fn_ka10099, fn_ka10100, fn_ka10101, fn_ka10095, fn_ka90003,
        fn_kt10000, fn_kt10001, fn_kt10002, fn_kt10003
    )
    # Specialized data functions
    from ..functions.orderbook import fn_ka10004, convert_orderbook_data
    from ..functions.historical import fn_ka10005, convert_chart_data
    from ..functions.minute_chart import fn_ka10006, convert_minute_data, get_stock_name_from_code
    from ..functions.market_info import fn_ka10007, convert_market_info_data
    from ..functions.new_stock_rights import (
        fn_ka10011, convert_new_stock_rights_data, get_rights_type_name
    )
    from ..functions.daily_institutional_trade import (
        fn_ka10044, convert_daily_institutional_trade_data,
        get_trade_type_name, get_market_type_name, get_exchange_type_name
    )
    from ..functions.stock_institutional_trend import (
        fn_ka10045, convert_stock_institutional_trend_data, get_change_sign_name
    )
    # Authentication
    from ..auth.token_validator import extract_bearer_token
except ImportError:
    # Stock models
    from kiwoom_api.models.stock import (
        StockInfoRequest, StockListRequest, IndustryCodeRequest, 
        WatchlistRequest, ProgramTradeRequest, StockBuyOrderRequest,
        StockSellOrderRequest, StockModifyOrderRequest, StockCancelOrderRequest
    )
    # Kiwoom request models
    from kiwoom_api.models.kiwoom_request import (
        KiwoomStockOrderbookRequest, KiwoomStockHistoricalRequest,
        KiwoomStockMinuteRequest, KiwoomStockMarketInfoRequest,
        KiwoomNewStockRightsRequest, KiwoomDailyInstitutionalTradeRequest,
        KiwoomStockInstitutionalTrendRequest
    )
    # Response models
    from kiwoom_api.models.orderbook import OrderbookApiResponse, OrderbookResponse, OrderbookData
    from kiwoom_api.models.chart import (
        ChartApiResponse, ChartResponse, MinuteChartApiResponse, MinuteChartResponse,
        MarketInfoApiResponse, MarketInfoResponse, NewStockRightsApiResponse,
        NewStockRightsResponse, DailyInstitutionalTradeApiResponse,
        DailyInstitutionalTradeResponse, StockInstitutionalTrendApiResponse,
        StockInstitutionalTrendResponse
    )
    # Stock business functions
    from kiwoom_api.functions.stock import (
        fn_ka10001, fn_ka10099, fn_ka10100, fn_ka10101, fn_ka10095, fn_ka90003,
        fn_kt10000, fn_kt10001, fn_kt10002, fn_kt10003
    )
    # Specialized data functions
    from kiwoom_api.functions.orderbook import fn_ka10004, convert_orderbook_data
    from kiwoom_api.functions.historical import fn_ka10005, convert_chart_data
    from kiwoom_api.functions.minute_chart import fn_ka10006, convert_minute_data, get_stock_name_from_code
    from kiwoom_api.functions.market_info import fn_ka10007, convert_market_info_data
    from kiwoom_api.functions.new_stock_rights import (
        fn_ka10011, convert_new_stock_rights_data, get_rights_type_name
    )
    from kiwoom_api.functions.daily_institutional_trade import (
        fn_ka10044, convert_daily_institutional_trade_data,
        get_trade_type_name, get_market_type_name, get_exchange_type_name
    )
    from kiwoom_api.functions.stock_institutional_trend import (
        fn_ka10045, convert_stock_institutional_trend_data, get_change_sign_name
    )
    # Authentication
    from kiwoom_api.auth.token_validator import extract_bearer_token


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


@router.post("/fn_ka10001", summary="키움 종목기본정보요청 (ka10001)", tags=["종목정보 API"])
async def api_fn_ka10001(
    request: StockInfoRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 주식기본정보요청 (ka10001)

    - **stk_cd**: 종목코드 (거래소별 종목코드)
      - KRX: 039490
      - NXT: 039490_NX
      - SOR: 039490_AL
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📊 fn_ka10001 요청: {request.stk_cd}")

        # fn_ka10001 직접 호출
        result = await fn_ka10001(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_ka10001 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10001 실패: {str(e)}")


@router.post("/fn_ka10099", summary="키움 종목정보 리스트 (ka10099)", tags=["종목정보 API"])
async def api_fn_ka10099(
    request: StockListRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 종목정보 리스트 (ka10099)

    - **mrkt_tp**: 시장구분
      - 0: 코스피
      - 10: 코스닥
      - 3: ELW
      - 8: ETF
      - 30: K-OTC
      - 50: 코넥스
      - 5: 신주인수권
      - 4: 뮤추얼펀드
      - 6: 리츠
      - 9: 하이일드
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📊 fn_ka10099 요청: {request.mrkt_tp}")

        # fn_ka10099 직접 호출
        result = await fn_ka10099(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_ka10099 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10099 실패: {str(e)}")


@router.post("/fn_ka10100", summary="키움 종목정보 조회 (ka10100)", tags=["종목정보 API"])
async def api_fn_ka10100(
    request: StockInfoRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 종목정보 조회 (ka10100)

    - **stk_cd**: 종목코드 (6자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - code: 종목코드
    - name: 종목명
    - listCount: 상장주식수
    - auditInfo: 감리구분
    - regDay: 상장일
    - lastPrice: 전일종가
    - state: 종목상태
    - marketCode: 시장구분코드
    - marketName: 시장명
    - upName: 업종명
    - upSizeName: 회사크기분류
    - companyClassName: 회사분류 (코스닥만)
    - orderWarning: 투자유의종목여부
    - nxtEnable: NXT가능여부

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📊 fn_ka10100 요청: {request.stk_cd}")

        # fn_ka10100 직접 호출
        result = await fn_ka10100(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_ka10100 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10100 실패: {str(e)}")


@router.post("/fn_ka10101", summary="키움 업종코드 리스트 (ka10101)", tags=["종목정보 API"])
async def api_fn_ka10101(
    request: IndustryCodeRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 업종코드 리스트 (ka10101)

    - **mrkt_tp**: 시장구분
      - 0: 코스피(거래소)
      - 1: 코스닥
      - 2: KOSPI200
      - 4: KOSPI100
      - 7: KRX100(통합지수)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - list: 업종코드리스트
      - marketCode: 시장구분코드
      - code: 코드
      - name: 업종명
      - group: 그룹

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📊 fn_ka10101 요청: {request.mrkt_tp}")

        # fn_ka10101 직접 호출
        result = await fn_ka10101(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_ka10101 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10101 실패: {str(e)}")


@router.post("/fn_ka10095", summary="키움 관심종목정보요청 (ka10095)", tags=["종목정보 API"])
async def api_fn_ka10095(
    request: WatchlistRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 관심종목정보요청 (ka10095)

    - **stk_cd**: 종목코드 (거래소별 종목코드, 여러 종목시 | 로 구분)
      - 단일 종목: "005930"
      - 다중 종목: "005930|000660|035420"
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - list: 종목정보 리스트
      - code: 종목코드
      - name: 종목명
      - price: 현재가
      - change: 전일대비
      - rate: 등락율
      - volume: 거래량
      - amount: 거래대금
      - high: 고가
      - low: 저가
      - open: 시가
      - prevClose: 전일종가
      - marketCap: 시가총액
      - shares: 상장주식수
      - per: PER
      - pbr: PBR
      - eps: EPS
      - bps: BPS
      - roe: ROE
      - 매수호가/매도호가 정보
      - 기술적 지표 등

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📊 fn_ka10095 요청: {request.stk_cd}")

        # fn_ka10095 직접 호출
        result = await fn_ka10095(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_ka10095 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10095 실패: {str(e)}")


@router.post("/fn_ka90003", summary="키움 프로그램순매수상위50요청 (ka90003)", tags=["종목정보 API"])
async def api_fn_ka90003(
    request: ProgramTradeRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 프로그램순매수상위50요청 (ka90003)

    - **trde_upper_tp**: 매매상위구분
      - 1: 순매도상위
      - 2: 순매수상위
    - **amt_qty_tp**: 금액수량구분
      - 1: 금액
      - 2: 수량
    - **mrkt_tp**: 시장구분
      - P00101: 코스피
      - P10102: 코스닥
    - **stex_tp**: 거래소구분
      - 1: KRX
      - 2: NXT
      - 3: 통합
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - prm_netprps_upper_50: 프로그램순매수상위50 리스트
      - rank: 순위
      - stk_cd: 종목코드
      - stk_nm: 종목명
      - cur_prc: 현재가
      - flu_sig: 등락기호
      - pred_pre: 전일대비
      - flu_rt: 등락율
      - acc_trde_qty: 누적거래량
      - prm_sell_amt: 프로그램매도금액
      - prm_buy_amt: 프로그램매수금액
      - prm_netprps_amt: 프로그램순매수금액

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📊 fn_ka90003 요청: {request.trde_upper_tp}/{request.amt_qty_tp}/{request.mrkt_tp}/{request.stex_tp}")

        # fn_ka90003 직접 호출
        result = await fn_ka90003(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_ka90003 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka90003 실패: {str(e)}")


# ============== 시세 정보 관련 API 엔드포인트 ==============

@router.post("/fn_ka10004", summary="키움 주식호가요청 (ka10004)", tags=["시세 API"])
async def api_fn_ka10004(
    request: KiwoomStockOrderbookRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> OrderbookApiResponse:
    """
    키움증권 주식호가요청 (ka10004) - 실시간 호가 스냅샷 조회

    - **stk_cd**: 종목코드 (6자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - **stock_code**: 종목코드
    - **stock_name**: 종목명
    - **raw_data**: 키움 원본 응답 데이터
    - **orderbook_data**: 구조화된 호가 데이터
      - **timestamp**: 호가 기준시간
      - **ask_prices**: 매도호가 리스트 (1-10호가)
      - **ask_volumes**: 매도잔량 리스트 (1-10호가)
      - **ask_changes**: 매도잔량대비 리스트 (1-10호가)
      - **bid_prices**: 매수호가 리스트 (1-10호가)
      - **bid_volumes**: 매수잔량 리스트 (1-10호가)
      - **bid_changes**: 매수잔량대비 리스트 (1-10호가)
      - **total_ask_volume**: 총매도잔량
      - **total_bid_volume**: 총매수잔량
      - **total_ask_change**: 총매도잔량대비
      - **total_bid_change**: 총매수잔량대비
      - **after_hours_ask_volume**: 시간외매도잔량
      - **after_hours_bid_volume**: 시간외매수잔량
    - **request_time**: 요청 시간
    - **response_time**: 응답 시간

    **실시간 vs REST API:**
    - REST API: 호출 시점의 호가 스냅샷 데이터 (일반적으로 1초 이내)
    - WebSocket: 실시간 스트리밍 데이터 (밀리초 단위 업데이트)
    """
    try:
        # Note: fn_ka10004 uses internal token management, no explicit token required
        request_time = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info(f"📊 fn_ka10004 요청: {request.stk_cd} (호가 스냅샷)")

        # fn_ka10004 호출
        result = await fn_ka10004(
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        response_time = datetime.now().strftime('%Y%m%d%H%M%S')

        if result['Code'] == 200:
            # 응답 데이터 처리
            body = result.get('Body', {})

            # 원본 데이터를 OrderbookResponse 모델로 변환
            raw_data = OrderbookResponse(**body)

            # 구조화된 데이터로 변환
            orderbook_data = convert_orderbook_data(body)

            # 종목명 가져오기
            stock_name = get_stock_name_from_code(request.stk_cd)

            # 최종 응답 구성
            response = OrderbookApiResponse(
                stock_code=request.stk_cd,
                stock_name=stock_name,
                raw_data=raw_data,
                orderbook_data=orderbook_data,
                request_time=request_time,
                response_time=response_time
            )

            logger.info(f"✅ fn_ka10004 완료: {request.stk_cd} - 매도최우선: {orderbook_data.ask_prices[0]}, 매수최우선: {orderbook_data.bid_prices[0]}")
            return response

        else:
            # 오류 응답
            error_msg = result.get('Error', 'Unknown error')
            logger.error(f"❌ fn_ka10004 API 오류: {error_msg}")
            raise HTTPException(status_code=result['Code'], detail=error_msg)

    except Exception as e:
        logger.error(f"❌ fn_ka10004 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10004 실패: {str(e)}")


@router.post("/fn_ka10005", summary="키움 주식일주월시분요청 (ka10005)", tags=["시세 API"])
async def api_fn_ka10005(
    request: KiwoomStockHistoricalRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> ChartApiResponse:
    """
    키움증권 주식일주월시분요청 (ka10005) - 차트 데이터 조회

    - **stk_cd**: 종목코드 (거래소별 종목코드)
      - KRX: 039490
      - NXT: 039490_NX
      - SOR: 039490_AL
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - **stock_code**: 종목코드
    - **stock_name**: 종목명
    - **raw_data**: 키움 원본 응답 데이터
    - **chart_data**: 구조화된 차트 데이터
      - **timestamp**: 날짜/시간
      - **ohlcv**: OHLCV 데이터 (시가, 고가, 저가, 종가, 거래량, 대비, 등락률)
      - **trading_info**: 거래 정보 (거래량, 거래대금, 신용잔고율)
      - **institutional_data**: 기관/외인 데이터 (외인보유, 외인비중, 순매수)
    - **data_count**: 데이터 개수
    - **request_time**: 요청 시간
    - **response_time**: 응답 시간

    **차트 데이터 활용:**
    - 일/주/월/시/분 단위 차트 분석
    - 외국인/기관/개인 투자자별 매매 동향 분석
    - 기술적 분석 지표 계산 기초 데이터
    """
    try:
        # Note: fn_ka10005 uses internal token management, no explicit token required
        request_time = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info(f"📈 fn_ka10005 요청: {request.stk_cd} (차트 데이터)")

        # fn_ka10005 호출
        result = await fn_ka10005(
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        response_time = datetime.now().strftime('%Y%m%d%H%M%S')

        if result['Code'] == 200:
            # 응답 데이터 처리
            body = result.get('Body', {})

            # 원본 데이터를 ChartResponse 모델로 변환
            raw_data = ChartResponse(**body)

            # 구조화된 데이터로 변환
            chart_data = convert_chart_data(body)

            # 종목명 가져오기
            from ..functions.orderbook import get_stock_name_from_code
            stock_name = get_stock_name_from_code(request.stk_cd.split('_')[0])  # 거래소 코드 제거

            # 최종 응답 구성
            response = ChartApiResponse(
                stock_code=request.stk_cd,
                stock_name=stock_name,
                raw_data=raw_data,
                chart_data=chart_data,
                data_count=len(chart_data),
                request_time=request_time,
                response_time=response_time
            )

            logger.info(f"✅ fn_ka10005 완료: {request.stk_cd} - {len(chart_data)}건 데이터")
            return response

        else:
            # 오류 응답
            error_msg = result.get('Error', 'Unknown error')
            logger.error(f"❌ fn_ka10005 API 오류: {error_msg}")
            raise HTTPException(status_code=result['Code'], detail=error_msg)

    except Exception as e:
        logger.error(f"❌ fn_ka10005 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10005 실패: {str(e)}")


@router.post("/fn_ka10006", summary="키움 주식시분요청 (ka10006)", tags=["시세 API"])
async def api_fn_ka10006(
    request: KiwoomStockMinuteRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> MinuteChartApiResponse:
    """
    키움증권 주식시분요청 (ka10006) - 실시간 시분 데이터 조회

    - **stk_cd**: 종목코드 (거래소별 종목코드)
      - KRX: 039490
      - NXT: 039490_NX
      - SOR: 039490_AL
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - **stock_code**: 종목코드
    - **stock_name**: 종목명
    - **raw_data**: 키움 원본 응답 데이터
    - **minute_data**: 구조화된 시분 데이터
      - **timestamp**: 시간 정보
      - **price_data**: 가격 정보 (시가, 고가, 저가, 종가, 대비, 등락률)
      - **volume_data**: 거래량/거래대금 정보
      - **strength**: 체결강도
    - **data_count**: 데이터 개수
    - **request_time**: 요청 시간
    - **response_time**: 응답 시간

    **시분 데이터 활용:**
    - 실시간 가격 모니터링
    - 단기 매매 신호 분석
    - 체결강도를 통한 매매 심리 파악
    - 분봉 차트 데이터 기초
    """
    try:
        # Note: fn_ka10006 uses internal token management, no explicit token required
        request_time = datetime.now().strftime('%Y%m%d%H%M%S')
        logger.info(f"⏰ fn_ka10006 요청: {request.stk_cd} (시분 데이터)")

        # fn_ka10006 호출
        result = await fn_ka10006(
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        response_time = datetime.now().strftime('%Y%m%d%H%M%S')

        if result['Code'] == 200:
            # 응답 데이터 처리
            body = result.get('Body', {})

            # ka10006은 단일 데이터 응답이므로 minute_data 리스트로 래핑
            minute_data_list = [body] if body else []
            raw_data = MinuteChartResponse(minute_data=minute_data_list)

            # 구조화된 데이터로 변환
            minute_data = convert_minute_data(body)

            # 종목명 가져오기
            from ..functions.orderbook import get_stock_name_from_code
            stock_name = get_stock_name_from_code(request.stk_cd.split('_')[0])  # 거래소 코드 제거

            # 최종 응답 구성
            response = MinuteChartApiResponse(
                stock_code=request.stk_cd,
                stock_name=stock_name,
                raw_data=raw_data,
                minute_data=minute_data,
                data_count=len(minute_data),
                request_time=request_time,
                response_time=response_time
            )

            logger.info(f"✅ fn_ka10006 완료: {request.stk_cd} - 종가: {body.get('close_pric')}, 체결강도: {body.get('cntr_str')}")
            return response

        else:
            # 오류 응답
            error_msg = result.get('Error', 'Unknown error')
            logger.error(f"❌ fn_ka10006 API 오류: {error_msg}")
            raise HTTPException(status_code=result['Code'], detail=error_msg)

    except Exception as e:
        logger.error(f"❌ fn_ka10006 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10006 실패: {str(e)}")


@router.post("/fn_ka10007", summary="키움 시세표성정보요청 (ka10007)", tags=["시세 API"])
async def api_fn_ka10007(
    request: KiwoomStockMarketInfoRequest,
    authorization: str = Header(..., description="Bearer {access_token}")
) -> MarketInfoApiResponse:
    """
    키움증권 시세표성정보요청 (ka10007) - 포괄적인 시세표 정보

    **시세표성정보 포함 내용:**
    - 기본 시세정보: OHLCV, 대비, 등락률
    - 매도/매수 호가: 1-10호가 가격 및 잔량
    - LP(유동성 공급자) 정보: LP 매도/매수 5단계 호가
    - 시장 데이터: 시가총액, 외국인비율, 공매도비율, 체결강도

    **요청 파라미터:**
    - **stk_cd**: 종목코드 (거래소별 종목코드)
      - 예시: "005930" (삼성전자)
      - KRX: 039490
      - NXT: 039490_NX
      - SOR: 039490_AL

    **응답 데이터:**
    - **raw_data**: 키움 API 원본 응답 (전체 필드 포함)
    - **market_info**: 구조화된 시세표성정보
      - **basic_info**: OHLCV 기본 시세
      - **orderbook**: 매도/매수 호가 배열
      - **lp_info**: LP 매도/매수 호가
      - **market_data**: 시총, 외국인비율, 공매도비율, 체결강도

    **실시간 시세표성정보를 제공하는 핵심 API입니다**
    """
    try:
        # Note: fn_ka10007 uses internal token management, no explicit token required
        request_time = datetime.now().strftime("%Y%m%d%H%M%S")
        logger.info(f"📊 fn_ka10007 요청: {request.stk_cd}")

        # fn_ka10007 호출
        result = await fn_ka10007(data=request.model_dump())

        if result.get('Code') == 200:
            # 응답 처리 시간
            response_time = datetime.now().strftime("%Y%m%d%H%M%S")

            body = result.get('Body', {})
            stock_name = get_stock_name_from_code(request.stk_cd)

            # 원본 데이터 구조화
            raw_data = MarketInfoResponse(market_info=body)

            # 구조화된 데이터 변환
            market_info = convert_market_info_data(body)

            response = MarketInfoApiResponse(
                stock_code=request.stk_cd,
                stock_name=stock_name,
                raw_data=raw_data,
                market_info=market_info,
                request_time=request_time,
                response_time=response_time
            )

            # 로그에 주요 정보만 출력
            basic_info = market_info.basic_info
            orderbook_info = market_info.orderbook
            ask_count = len(orderbook_info.get('ask', []))
            bid_count = len(orderbook_info.get('bid', []))

            logger.info(f"✅ fn_ka10007 완료: {request.stk_cd} - 종가: {basic_info.get('close')}, "
                       f"매도호가: {ask_count}단계, 매수호가: {bid_count}단계, "
                       f"체결강도: {market_info.market_data.get('strength')}")
            return response

        else:
            # 오류 응답
            error_msg = result.get('Error', 'Unknown error')
            logger.error(f"❌ fn_ka10007 API 오류: {error_msg}")
            raise HTTPException(status_code=result['Code'], detail=error_msg)

    except Exception as e:
        logger.error(f"❌ fn_ka10007 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10007 실패: {str(e)}")


@router.post("/fn_ka10011", summary="키움 신주인수권전체시세요청 (ka10011)", tags=["시세 API"])
async def api_fn_ka10011(
    request: KiwoomNewStockRightsRequest,
    authorization: str = Header(..., description="Bearer {access_token}")
) -> NewStockRightsApiResponse:
    """
    키움증권 신주인수권전체시세요청 (ka10011) - 신주인수권 전체 시세 정보

    **신주인수권 시세정보 포함 내용:**
    - 종목기본정보: 종목코드, 종목명
    - 가격정보: 현재가, OHLC, 전일대비, 등락률
    - 호가정보: 최우선매도호가, 최우선매수호가
    - 거래정보: 누적거래량

    **요청 파라미터:**
    - **newstk_recvrht_tp**: 신주인수권구분
      - "00": 전체 (모든 신주인수권 종목)
      - "05": 신주인수권증권 (신주인수권증권만)
      - "07": 신주인수권증서 (신주인수권증서만)

    **응답 데이터:**
    - **raw_data**: 키움 API 원본 응답 (전체 필드 포함)
    - **rights_data**: 구조화된 신주인수권 시세 데이터 배열
      - **code**: 종목코드
      - **name**: 종목명
      - **price_info**: 가격정보 (현재가, OHLC, 대비, 등락률)
      - **bid_info**: 호가정보 (최우선매도/매수호가)
      - **volume_info**: 거래량정보

    **신주인수권 시장 전체 현황을 제공하는 종합 API입니다**
    """
    try:
        # Note: fn_ka10011 uses internal token management, no explicit token required
        request_time = datetime.now().strftime("%Y%m%d%H%M%S")
        logger.info(f"📋 fn_ka10011 요청: {request.newstk_recvrht_tp}")

        # fn_ka10011 호출
        result = await fn_ka10011(data=request.model_dump())

        if result.get('Code') == 200:
            # 응답 처리 시간
            response_time = datetime.now().strftime("%Y%m%d%H%M%S")

            body = result.get('Body', {})
            rights_type_name = get_rights_type_name(request.newstk_recvrht_tp)

            # 원본 데이터 구조화
            raw_data = NewStockRightsResponse(newstk_recvrht_mrpr=body.get('newstk_recvrht_mrpr', []))

            # 구조화된 데이터 변환
            rights_data = convert_new_stock_rights_data(body)

            response = NewStockRightsApiResponse(
                rights_type=request.newstk_recvrht_tp,
                rights_type_name=rights_type_name,
                raw_data=raw_data,
                rights_data=rights_data,
                data_count=len(rights_data),
                request_time=request_time,
                response_time=response_time
            )

            # 로그에 주요 정보만 출력
            logger.info(f"✅ fn_ka10011 완료: {request.newstk_recvrht_tp} ({rights_type_name}) - "
                       f"종목수: {len(rights_data)}개")

            # 첫 번째 종목 정보 출력 (있는 경우)
            if rights_data:
                first_item = rights_data[0]
                current_price = first_item.price_info.get('current', '0')
                volume = first_item.volume_info.get('volume', '0')
                logger.info(f"   대표종목: {first_item.name}({first_item.code}) - "
                           f"현재가: {current_price}, 거래량: {volume}")

            return response

        else:
            # 오류 응답
            error_msg = result.get('Error', 'Unknown error')
            logger.error(f"❌ fn_ka10011 API 오류: {error_msg}")
            raise HTTPException(status_code=result['Code'], detail=error_msg)

    except Exception as e:
        logger.error(f"❌ fn_ka10011 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10011 실패: {str(e)}")


@router.post("/fn_ka10044", summary="키움 일별기관매매종목요청 (ka10044)", tags=["시세 API"])
async def api_fn_ka10044(
    request: KiwoomDailyInstitutionalTradeRequest,
    authorization: str = Header(..., description="Bearer {access_token}")
) -> DailyInstitutionalTradeApiResponse:
    """
    키움증권 일별기관매매종목요청 (ka10044) - 기관 투자자 일별 매매 종목 현황

    **일별기관매매종목정보 포함 내용:**
    - 종목기본정보: 종목코드, 종목명
    - 매매정보: 순매수수량, 순매수금액
    - 기간/시장별 필터링 지원

    **요청 파라미터:**
    - **strt_dt**: 시작일자 (YYYYMMDD 형식)
    - **end_dt**: 종료일자 (YYYYMMDD 형식)
    - **trde_tp**: 매매구분
      - "1": 순매도 (기관이 순매도한 종목들)
      - "2": 순매수 (기관이 순매수한 종목들)
    - **mrkt_tp**: 시장구분
      - "001": 코스피 (KOSPI)
      - "101": 코스닥 (KOSDAQ)
    - **stex_tp**: 거래소구분
      - "1": KRX (한국거래소)
      - "2": NXT (넥스트트레이드)
      - "3": 통합 (전체 거래소)

    **응답 데이터:**
    - **raw_data**: 키움 API 원본 응답 (전체 필드 포함)
    - **trade_data**: 구조화된 일별기관매매종목 데이터 배열
      - **code**: 종목코드
      - **name**: 종목명
      - **trade_info**: 매매정보 (순매수수량, 순매수금액)

    **기관 투자자의 매매 동향 분석에 필수적인 API입니다**
    """
    try:
        # Note: fn_ka10044 uses internal token management, no explicit token required
        request_time = datetime.now().strftime("%Y%m%d%H%M%S")
        logger.info(f"📊 fn_ka10044 요청: {request.strt_dt}-{request.end_dt}, {get_trade_type_name(request.trde_tp)}")

        # fn_ka10044 호출
        result = await fn_ka10044(data=request.model_dump())

        if result.get('Code') == 200:
            # 응답 처리 시간
            response_time = datetime.now().strftime("%Y%m%d%H%M%S")

            body = result.get('Body', {})

            # 파라미터별 한글명 변환
            trade_type_name = get_trade_type_name(request.trde_tp)
            market_type_name = get_market_type_name(request.mrkt_tp)
            exchange_type_name = get_exchange_type_name(request.stex_tp)

            # 원본 데이터 구조화
            raw_data = DailyInstitutionalTradeResponse(daly_orgn_trde_stk=body.get('daly_orgn_trde_stk', []))

            # 구조화된 데이터 변환
            trade_data = convert_daily_institutional_trade_data(body)

            response = DailyInstitutionalTradeApiResponse(
                start_date=request.strt_dt,
                end_date=request.end_dt,
                trade_type=request.trde_tp,
                trade_type_name=trade_type_name,
                market_type=request.mrkt_tp,
                market_type_name=market_type_name,
                exchange_type=request.stex_tp,
                exchange_type_name=exchange_type_name,
                raw_data=raw_data,
                trade_data=trade_data,
                data_count=len(trade_data),
                request_time=request_time,
                response_time=response_time
            )

            # 로그에 주요 정보만 출력
            logger.info(f"✅ fn_ka10044 완료: {request.strt_dt}-{request.end_dt} "
                       f"{trade_type_name}/{market_type_name}/{exchange_type_name} - "
                       f"종목수: {len(trade_data)}개")

            # 대표 종목 정보 출력 (있는 경우)
            if trade_data:
                first_item = trade_data[0]
                net_qty = first_item.trade_info.get('net_quantity', '0')
                net_amt = first_item.trade_info.get('net_amount', '0')
                logger.info(f"   대표종목: {first_item.name}({first_item.code}) - "
                           f"순매수: {net_qty}주, {net_amt}원")

            return response

        else:
            # 오류 응답
            error_msg = result.get('Error', 'Unknown error')
            logger.error(f"❌ fn_ka10044 API 오류: {error_msg}")
            raise HTTPException(status_code=result['Code'], detail=error_msg)

    except Exception as e:
        logger.error(f"❌ fn_ka10044 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10044 실패: {str(e)}")


# ============== 주식 거래주문 관련 API 엔드포인트 ==============

@router.post("/fn_kt10000", summary="키움 주식 매수주문 (kt10000)", tags=["주문 API"])
async def api_fn_kt10000(
    request: StockBuyOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 주식 매수주문 (kt10000)

    - **dmst_stex_tp**: 국내거래소구분
      - KRX: 한국거래소
      - NXT: 넥스트트레이드
      - SOR: 스마트오더라우팅
    - **stk_cd**: 종목코드 (6자리)
    - **ord_qty**: 주문수량
    - **ord_uv**: 주문단가 (시장가일 때는 공백)
    - **trde_tp**: 매매구분
      - 0: 보통
      - 3: 시장가
      - 5: 조건부지정가
      - 81: 장마감후시간외
      - 61: 장시작전시간외
      - 62: 시간외단일가
      - 6: 최유리지정가
      - 7: 최우선지정가
      - 10: 보통(IOC)
      - 13: 시장가(IOC)
      - 16: 최유리(IOC)
      - 20: 보통(FOK)
      - 23: 시장가(FOK)
      - 26: 최유리(FOK)
      - 28: 스톱지정가
      - 29: 중간가
      - 30: 중간가(IOC)
      - 31: 중간가(FOK)
    - **cond_uv**: 조건단가 (optional)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - **ord_no**: 주문번호 (주문 성공시 반환)
    - **dmst_stex_tp**: 국내거래소구분 (응답)

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📈 fn_kt10000 요청: {request.stk_cd} {request.ord_qty}주 매수주문")

        # fn_kt10000 직접 호출
        result = await fn_kt10000(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_kt10000 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt10000 실패: {str(e)}")


@router.post("/fn_kt10001", summary="키움 주식 매도주문 (kt10001)", tags=["주문 API"])
async def api_fn_kt10001(
    request: StockSellOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 주식 매도주문 (kt10001)

    - **dmst_stex_tp**: 국내거래소구분
      - KRX: 한국거래소
      - NXT: 넥스트트레이드
      - SOR: 스마트오더라우팅
    - **stk_cd**: 종목코드 (6자리)
    - **ord_qty**: 주문수량
    - **ord_uv**: 주문단가 (시장가일 때는 공백)
    - **trde_tp**: 매매구분
      - 0: 보통
      - 3: 시장가
      - 5: 조건부지정가
      - 81: 장마감후시간외
      - 61: 장시작전시간외
      - 62: 시간외단일가
      - 6: 최유리지정가
      - 7: 최우선지정가
      - 10: 보통(IOC)
      - 13: 시장가(IOC)
      - 16: 최유리(IOC)
      - 20: 보통(FOK)
      - 23: 시장가(FOK)
      - 26: 최유리(FOK)
      - 28: 스톱지정가
      - 29: 중간가
      - 30: 중간가(IOC)
      - 31: 중간가(FOK)
    - **cond_uv**: 조건단가 (optional)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - **ord_no**: 주문번호 (주문 성공시 반환)
    - **dmst_stex_tp**: 국내거래소구분 (응답)

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"📉 fn_kt10001 요청: {request.stk_cd} {request.ord_qty}주 매도주문")

        # fn_kt10001 직접 호출
        result = await fn_kt10001(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_kt10001 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt10001 실패: {str(e)}")


@router.post("/fn_kt10002", summary="키움 주식 정정주문 (kt10002)", tags=["주문 API"])
async def api_fn_kt10002(
    request: StockModifyOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 주식 정정주문 (kt10002)

    - **dmst_stex_tp**: 국내거래소구분
      - KRX: 한국거래소
      - NXT: 넥스트트레이드
      - SOR: 스마트오더라우팅
    - **orig_ord_no**: 원주문번호 (7자리, 필수)
    - **stk_cd**: 종목코드 (6자리)
    - **mdfy_qty**: 정정수량 (필수)
    - **mdfy_uv**: 정정단가 (필수)
    - **mdfy_cond_uv**: 정정조건단가 (optional)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - **ord_no**: 주문번호 (주문 성공시 반환)
    - **base_orig_ord_no**: 모주문번호
    - **mdfy_qty**: 정정수량 (응답)
    - **dmst_stex_tp**: 국내거래소구분 (응답)

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        logger.info(f"🔄 fn_kt10002 요청: {request.orig_ord_no} 주문 {request.mdfy_qty}주 → {request.mdfy_uv}원으로 정정")

        # fn_kt10002 직접 호출
        result = await fn_kt10002(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_kt10002 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt10002 실패: {str(e)}")


@router.post("/fn_kt10003", summary="키움 주식 취소주문 (kt10003)", tags=["주문 API"])
async def api_fn_kt10003(
    request: StockCancelOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    authorization: str = Header(..., description="Bearer {access_token}")
) -> JSONResponse:
    """
    키움증권 주식 취소주문 (kt10003)

    - **dmst_stex_tp**: 국내거래소구분
      - KRX: 한국거래소
      - NXT: 넥스트트레이드
      - SOR: 스마트오더라우팅
    - **orig_ord_no**: 원주문번호 (7자리, 필수)
    - **stk_cd**: 종목코드 (6자리)
    - **cncl_qty**: 취소수량 (필수)
      - 숫자: 해당 수량만큼 취소
      - "0": 잔량 전부 취소
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)

    **응답 필드:**
    - **ord_no**: 주문번호 (주문 성공시 반환)
    - **base_orig_ord_no**: 모주문번호
    - **cncl_qty**: 취소수량 (응답)

    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        # Java Backend에서 전달받은 토큰 추출
        access_token = extract_bearer_token(authorization)
        cncl_desc = "잔량 전부 취소" if request.cncl_qty == "0" else f"{request.cncl_qty}주 취소"
        logger.info(f"❌ fn_kt10003 요청: {request.orig_ord_no} 주문 {cncl_desc}")

        # fn_kt10003 직접 호출
        result = await fn_kt10003(
            token=access_token,
            data=request.model_dump(),
            cont_yn=cont_yn,
            next_key=next_key
        )

        return JSONResponse(
            status_code=result['Code'],
            content=result
        )

    except Exception as e:
        logger.error(f"❌ fn_kt10003 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt10003 실패: {str(e)}")


@router.post("/fn_ka10045", summary="키움 종목별기관매매추이요청 (ka10045)", tags=["시세 API"])
async def api_fn_ka10045(
    request: KiwoomStockInstitutionalTrendRequest,
    authorization: str = Header(..., description="Bearer {access_token}")
) -> StockInstitutionalTrendApiResponse:
    """
    키움증권 종목별기관매매추이요청 (ka10045) - 특정 종목의 기관/외국인 매매 추이 정보

    **종목별 기관매매추이 포함 내용:**
    - 종목기본정보: 종목코드, 종목명, 거래일자
    - 기관정보: 보유수량, 비중, 추정평균가, 순매수수량/금액, 매수/매도수량
    - 외국인정보: 보유수량, 비중, 추정평균가, 순매수수량/금액, 매수/매도수량
    - 개인정보: 순매수수량/금액, 매수/매도수량
    - 주가정보: 현재가, 전일대비, 전일대비부호, 전일대비거래량비율

    **요청 파라미터:**
    - **stk_cd**: 종목코드 (6자리)
      - 예: "005930" (삼성전자), "000660" (SK하이닉스)
    - **strt_dt**: 시작일자 (YYYYMMDD 형식)
      - 예: "20241201"
    - **end_dt**: 종료일자 (YYYYMMDD 형식)
      - 예: "20241225"
      - 권장: 최대 1개월 범위

    **응답 데이터:**
    - **raw_data**: 키움 원본 응답 데이터
    - **trend_data**: 구조화된 매매추이 데이터 (일별)
    - **data_count**: 조회된 데이터 건수

    키움 원본 데이터와 가공된 구조화 데이터를 함께 제공합니다.
    """
    try:
        # Note: fn_ka10045 uses internal token management, no explicit token required
        logger.info(f"📊 fn_ka10045 요청: {request.data.stk_cd} ({request.data.strt_dt}-{request.data.end_dt})")

        # fn_ka10045 호출
        result = await fn_ka10045(
            data=request.data.model_dump(),
            cont_yn=request.cont_yn,
            next_key=request.next_key
        )

        if result.get('Code') == 200:
            # 성공 응답 처리
            logger.info(f"✅ fn_ka10045 성공: {request.data.stk_cd}")

            # 원본 응답 데이터
            raw_response = StockInstitutionalTrendResponse(**result['Body'])

            # 구조화된 데이터 변환
            trend_data = convert_stock_institutional_trend_data(result['Body'])

            # API 응답 구성
            response = StockInstitutionalTrendApiResponse(
                stock_code=request.stk_cd,
                start_date=request.strt_dt,
                end_date=request.end_dt,
                raw_data=raw_response,
                trend_data=trend_data,
                data_count=len(trend_data),
                request_time=datetime.now().strftime("%Y%m%d%H%M%S"),
                response_time=datetime.now().strftime("%Y%m%d%H%M%S")
            )

            logger.info(f"✅ fn_ka10045 완료: {request.stk_cd} - {len(trend_data)}건")
            return response

        else:
            # 오류 응답
            error_msg = result.get('Error', 'Unknown error')
            logger.error(f"❌ fn_ka10045 API 오류: {error_msg}")
            raise HTTPException(status_code=result['Code'], detail=error_msg)

    except Exception as e:
        logger.error(f"❌ fn_ka10045 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10045 실패: {str(e)}")

