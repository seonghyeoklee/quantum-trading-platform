"""
키움 API 종목정보 및 주식 거래주문 REST API 엔드포인트
함수명 기준으로 API 경로 매핑: /api/fn_ka10001, /api/fn_kt10000
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

try:
    from ..models.stock import StockInfoRequest, StockListRequest, IndustryCodeRequest, WatchlistRequest, ProgramTradeRequest, StockBuyOrderRequest, StockSellOrderRequest, StockModifyOrderRequest, StockCancelOrderRequest
    from ..functions.stock import fn_ka10001, fn_ka10099, fn_ka10100, fn_ka10101, fn_ka10095, fn_ka90003, fn_kt10000, fn_kt10001, fn_kt10002, fn_kt10003
    from ..functions.auth import get_valid_access_token
except ImportError:
    from kiwoom_api.models.stock import StockInfoRequest, StockListRequest, IndustryCodeRequest, WatchlistRequest, ProgramTradeRequest, StockBuyOrderRequest, StockSellOrderRequest, StockModifyOrderRequest, StockCancelOrderRequest
    from kiwoom_api.functions.stock import fn_ka10001, fn_ka10099, fn_ka10100, fn_ka10101, fn_ka10095, fn_ka90003, fn_kt10000, fn_kt10001, fn_kt10002, fn_kt10003
    from kiwoom_api.functions.auth import get_valid_access_token


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["키움 API"])


@router.post("/fn_ka10001", summary="키움 종목기본정보요청 (ka10001)")
async def api_fn_ka10001(
    request: StockInfoRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📊 fn_ka10001 요청: {request.stk_cd}")
        
        # fn_ka10001 직접 호출
        result = await fn_ka10001(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_ka10099", summary="키움 종목정보 리스트 (ka10099)")
async def api_fn_ka10099(
    request: StockListRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📊 fn_ka10099 요청: {request.mrkt_tp}")
        
        # fn_ka10099 직접 호출
        result = await fn_ka10099(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_ka10100", summary="키움 종목정보 조회 (ka10100)")
async def api_fn_ka10100(
    request: StockInfoRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📊 fn_ka10100 요청: {request.stk_cd}")
        
        # fn_ka10100 직접 호출
        result = await fn_ka10100(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_ka10101", summary="키움 업종코드 리스트 (ka10101)")
async def api_fn_ka10101(
    request: IndustryCodeRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📊 fn_ka10101 요청: {request.mrkt_tp}")
        
        # fn_ka10101 직접 호출
        result = await fn_ka10101(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_ka10095", summary="키움 관심종목정보요청 (ka10095)")
async def api_fn_ka10095(
    request: WatchlistRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📊 fn_ka10095 요청: {request.stk_cd}")
        
        # fn_ka10095 직접 호출
        result = await fn_ka10095(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_ka90003", summary="키움 프로그램순매수상위50요청 (ka90003)")
async def api_fn_ka90003(
    request: ProgramTradeRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📊 fn_ka90003 요청: {request.trde_upper_tp}/{request.amt_qty_tp}/{request.mrkt_tp}/{request.stex_tp}")
        
        # fn_ka90003 직접 호출
        result = await fn_ka90003(
            token=access_token,
            data=request.dict(),
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


# ============== 주식 거래주문 관련 API 엔드포인트 ==============

@router.post("/fn_kt10000", summary="키움 주식 매수주문 (kt10000)")
async def api_fn_kt10000(
    request: StockBuyOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📈 fn_kt10000 요청: {request.stk_cd} {request.ord_qty}주 매수주문")
        
        # fn_kt10000 직접 호출
        result = await fn_kt10000(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_kt10001", summary="키움 주식 매도주문 (kt10001)")
async def api_fn_kt10001(
    request: StockSellOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"📉 fn_kt10001 요청: {request.stk_cd} {request.ord_qty}주 매도주문")
        
        # fn_kt10001 직접 호출
        result = await fn_kt10001(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_kt10002", summary="키움 주식 정정주문 (kt10002)")
async def api_fn_kt10002(
    request: StockModifyOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        logger.info(f"🔄 fn_kt10002 요청: {request.orig_ord_no} 주문 {request.mdfy_qty}주 → {request.mdfy_uv}원으로 정정")
        
        # fn_kt10002 직접 호출
        result = await fn_kt10002(
            token=access_token,
            data=request.dict(),
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


@router.post("/fn_kt10003", summary="키움 주식 취소주문 (kt10003)")
async def api_fn_kt10003(
    request: StockCancelOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
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
        cncl_desc = "잔량 전부 취소" if request.cncl_qty == "0" else f"{request.cncl_qty}주 취소"
        logger.info(f"❌ fn_kt10003 요청: {request.orig_ord_no} 주문 {cncl_desc}")
        
        # fn_kt10003 직접 호출
        result = await fn_kt10003(
            token=access_token,
            data=request.dict(),
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