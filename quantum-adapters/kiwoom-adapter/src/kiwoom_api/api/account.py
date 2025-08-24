"""
키움 API 계좌정보 REST API 엔드포인트
함수명 기준으로 API 경로 매핑: /api/fn_ka10072
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

try:
    from ..models.account import (
        DailyStockProfitLossRequest, DailyStockProfitLossPeriodRequest, DailyProfitLossRequest,
        UnfilledOrderRequest, FilledOrderRequest, TodayProfitLossDetailRequest,
        AccountReturnRateRequest, UnfilledSplitOrderDetailRequest, DailyTradingLogRequest,
        DepositDetailStatusRequest, DailyEstimatedAssetStatusRequest, EstimatedAssetInquiryRequest,
        AccountEvaluationStatusRequest, FilledBalanceRequest, AccountOrderFilledDetailRequest,
        AccountNextDaySettlementRequest, AccountOrderFilledStatusRequest, OrderWithdrawalAmountRequest,
        MarginRateOrderQuantityRequest, CreditMarginRateOrderQuantityRequest, MarginDetailInquiryRequest,
        TrustComprehensiveTransactionRequest, DailyAccountReturnDetailRequest, AccountDailyStatusRequest,
        AccountEvaluationBalanceDetailRequest
    )
    from ..functions.account import (
        fn_ka10072, fn_ka10073, fn_ka10074, fn_ka10075, fn_ka10076, fn_ka10077, fn_ka10085,
        fn_ka10088, fn_ka10170, fn_kt00001, fn_kt00002, fn_kt00003, fn_kt00004, fn_kt00005,
        fn_kt00007, fn_kt00008, fn_kt00009, fn_kt00010, fn_kt00011,
        fn_kt00012, fn_kt00013, fn_kt00015, fn_kt00016, fn_kt00017, fn_kt00018
    )
    from ..functions.auth import get_valid_access_token
except ImportError:
    from kiwoom_api.models.account import (
        DailyStockProfitLossRequest, DailyStockProfitLossPeriodRequest, DailyProfitLossRequest,
        UnfilledOrderRequest, FilledOrderRequest, TodayProfitLossDetailRequest,
        AccountReturnRateRequest, UnfilledSplitOrderDetailRequest, DailyTradingLogRequest,
        DepositDetailStatusRequest, DailyEstimatedAssetStatusRequest, EstimatedAssetInquiryRequest,
        AccountEvaluationStatusRequest, FilledBalanceRequest, AccountOrderFilledDetailRequest,
        AccountNextDaySettlementRequest, AccountOrderFilledStatusRequest, OrderWithdrawalAmountRequest,
        MarginRateOrderQuantityRequest, CreditMarginRateOrderQuantityRequest, MarginDetailInquiryRequest,
        TrustComprehensiveTransactionRequest, DailyAccountReturnDetailRequest, AccountDailyStatusRequest,
        AccountEvaluationBalanceDetailRequest
    )
    from kiwoom_api.functions.account import (
        fn_ka10072, fn_ka10073, fn_ka10074, fn_ka10075, fn_ka10076, fn_ka10077, fn_ka10085,
        fn_ka10088, fn_ka10170, fn_kt00001, fn_kt00002, fn_kt00003, fn_kt00004, fn_kt00005,
        fn_kt00007, fn_kt00008, fn_kt00009, fn_kt00010, fn_kt00011,
        fn_kt00012, fn_kt00013, fn_kt00015, fn_kt00016, fn_kt00017, fn_kt00018
    )
    from kiwoom_api.functions.auth import get_valid_access_token


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["키움 계좌 API"])


# 손익 관련 API (ka10072 ~ ka10077)

@router.post("/fn_ka10072", summary="키움 일자별종목별실현손익요청_일자 (ka10072)")
async def api_fn_ka10072(
    request: DailyStockProfitLossRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 일자별종목별실현손익요청_일자 (ka10072)
    
    - **stk_cd**: 종목코드 (6자리)
    - **strt_dt**: 시작일자 (YYYYMMDD)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - 일자별 종목별 실현손익 상세 내역
    - 매수/매도 정보
    - 손익금액 및 수익률
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"💰 fn_ka10072 요청: {request.stk_cd} ({request.strt_dt})")
        
        result = await fn_ka10072(
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
        logger.error(f"❌ fn_ka10072 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10072 실패: {str(e)}")


@router.post("/fn_ka10073", summary="키움 주별종목별실현손익요청 (ka10073)")
async def api_fn_ka10073(
    request: DailyStockProfitLossPeriodRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 일자별종목별실현손익요청_기간 (ka10073) - 정확한 키움 스펙
    
    - **stk_cd**: 종목코드 (String, Required, 6자리)
    - **strt_dt**: 시작일자 (String, Required, 8자리 YYYYMMDD)
    - **end_dt**: 종료일자 (String, Required, 8자리 YYYYMMDD)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **dt_stk_rlzt_pl**: 일자별종목별실현손익 리스트
      - dt: 일자 (String, 20자리)
      - tdy_htssel_cmsn: 당일hts매도수수료 (String, 20자리)  
      - stk_nm: 종목명 (String, 40자리)
      - cntr_qty: 체결량 (String, 20자리)
      - buy_uv: 매입단가 (String, 20자리)
      - cntr_pric: 체결가 (String, 20자리)
      - tdy_sel_pl: 당일매도손익 (String, 20자리)
      - pl_rt: 손익율 (String, 20자리)
      - stk_cd: 종목코드 (String, 20자리)
      - tdy_trde_cmsn: 당일매매수수료 (String, 20자리)
      - tdy_trde_tax: 당일매매세금 (String, 20자리)
      - wthd_alowa: 인출가능금액 (String, 20자리)
      - loan_dt: 대출일 (String, 20자리)
      - crd_tp: 신용구분 (String, 20자리)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"💰 fn_ka10073 요청: {request.stk_cd}")
        
        result = await fn_ka10073(
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
        logger.error(f"❌ fn_ka10073 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10073 실패: {str(e)}")


@router.post("/fn_ka10074", summary="키움 월별종목별실현손익요청 (ka10074)")
async def api_fn_ka10074(
    request: DailyProfitLossRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 일자별실현손익요청 (ka10074) - 정확한 키움 스펙
    
    - **strt_dt**: 시작일자 (String, Required, 8자리 YYYYMMDD)
    - **end_dt**: 종료일자 (String, Required, 8자리 YYYYMMDD)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **tot_buy_amt**: 총매수금액 (String)
    - **tot_sell_amt**: 총매도금액 (String)
    - **rlzt_pl**: 실현손익 (String)
    - **trde_cmsn**: 매매수수료 (String)
    - **trde_tax**: 매매세금 (String)
    - **dt_rlzt_pl**: 일자별실현손익 리스트 (LIST)
      - dt: 일자 (String, 20자리)
      - buy_amt: 매수금액 (String, 20자리)
      - sell_amt: 매도금액 (String, 20자리)
      - tdy_sel_pl: 당일매도손익 (String, 20자리)
      - tdy_trde_cmsn: 당일매매수수료 (String, 20자리)
      - tdy_trde_tax: 당일매매세금 (String, 20자리)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"💰 fn_ka10074 요청: {request.strt_dt}~{request.end_dt}")
        
        result = await fn_ka10074(
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
        logger.error(f"❌ fn_ka10074 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10074 실패: {str(e)}")


@router.post("/fn_ka10075", summary="키움 미체결요청 (ka10075)")
async def api_fn_ka10075(
    request: UnfilledOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 미체결요청 (ka10075)
    
    - **all_stk_tp**: 전체종목구분 (0:전체, 1:종목)
    - **trde_tp**: 매매구분 (0:전체, 1:매도, 2:매수)
    - **stk_cd**: 종목코드 (선택, 6자리)
    - **stex_tp**: 거래소구분 (0:통합, 1:KRX, 2:NXT)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **oso**: 미체결 리스트
      - acnt_no: 계좌번호
      - ord_no: 주문번호
      - stk_cd: 종목코드
      - ord_stt: 주문상태
      - stk_nm: 종목명
      - ord_qty: 주문수량
      - ord_pric: 주문가격
      - oso_qty: 미체결수량
      - cntr_tot_amt: 체결누계금액
      - trde_tp: 매매구분
      - cur_prc: 현재가
      - sel_bid: 매도호가
      - buy_bid: 매수호가
      - 기타 31개 필드 (스톱가, 시간, 체결정보 등)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📋 fn_ka10075 요청: 전체종목구분={request.all_stk_tp}, 매매구분={request.trde_tp}, 종목코드={request.stk_cd or 'N/A'}, 거래소구분={request.stex_tp}")
        
        result = await fn_ka10075(
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
        logger.error(f"❌ fn_ka10075 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10075 실패: {str(e)}")


@router.post("/fn_ka10076", summary="키움 체결요청 (ka10076)")
async def api_fn_ka10076(
    request: FilledOrderRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 체결요청 (ka10076)
    
    - **stk_cd**: 종목코드 (선택, 6자리)
    - **qry_tp**: 조회구분 (0:전체, 1:종목)
    - **sell_tp**: 매도수구분 (0:전체, 1:매도, 2:매수)
    - **ord_no**: 주문번호 (선택, 검색 기준 값)
    - **stex_tp**: 거래소구분 (0:통합, 1:KRX, 2:NXT)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **cntr**: 체결 리스트
      - ord_no: 주문번호
      - stk_nm: 종목명
      - io_tp_nm: 주문구분
      - ord_pric: 주문가격
      - ord_qty: 주문수량
      - cntr_pric: 체결가
      - cntr_qty: 체결량
      - oso_qty: 미체결수량
      - ord_stt: 주문상태
      - trde_tp: 매매구분
      - orig_ord_no: 원주문번호
      - ord_tm: 주문시간
      - stk_cd: 종목코드
      - stex_tp: 거래소구분
      - stex_tp_txt: 거래소구분텍스트
      - sor_yn: SOR 여부값
      - stop_pric: 스톱가
      - 기타 체결 관련 정보 (수수료, 세금 등)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"✅ fn_ka10076 요청: 조회구분={request.qry_tp}, 매도수구분={request.sell_tp}, 종목코드={request.stk_cd or 'N/A'}, 거래소구분={request.stex_tp}")
        
        result = await fn_ka10076(
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
        logger.error(f"❌ fn_ka10076 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10076 실패: {str(e)}")


@router.post("/fn_ka10077", summary="키움 당일실현손익상세요청 (ka10077)")
async def api_fn_ka10077(
    request: TodayProfitLossDetailRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 당일실현손익상세요청 (ka10077)
    
    - **stk_cd**: 종목코드 (필수, 6자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **tdy_rlzt_pl**: 당일실현손익 (String)
    - **tdy_rlzt_pl_dtl**: 당일실현손익상세 리스트
      - stk_nm: 종목명
      - cntr_qty: 체결량
      - buy_uv: 매입단가
      - cntr_pric: 체결가
      - tdy_sel_pl: 당일매도손익
      - pl_rt: 손익율
      - tdy_trde_cmsn: 당일매매수수료
      - tdy_trde_tax: 당일매매세금
      - stk_cd: 종목코드
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"💰 fn_ka10077 요청: 종목코드={request.stk_cd}")
        
        result = await fn_ka10077(
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
        logger.error(f"❌ fn_ka10077 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10077 실패: {str(e)}")


@router.post("/fn_ka10085", summary="키움 계좌수익률요청 (ka10085)")
async def api_fn_ka10085(
    request: AccountReturnRateRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 계좌수익률요청 (ka10085)
    
    - **stex_tp**: 거래소구분 (필수, 0:통합, 1:KRX, 2:NXT)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **acnt_prft_rt**: 계좌수익률 리스트
      - dt: 일자
      - stk_cd: 종목코드
      - stk_nm: 종목명
      - cur_prc: 현재가
      - pur_pric: 매입가
      - pur_amt: 매입금액
      - rmnd_qty: 보유수량
      - tdy_sel_pl: 당일매도손익
      - tdy_trde_cmsn: 당일매매수수료
      - tdy_trde_tax: 당일매매세금
      - crd_tp: 신용구분
      - loan_dt: 대출일
      - setl_remn: 결제잔고
      - clrn_alow_qty: 청산가능수량
      - crd_amt: 신용금액
      - crd_int: 신용이자
      - expr_dt: 만기일
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📈 fn_ka10085 요청: 거래소구분={request.stex_tp}")
        
        result = await fn_ka10085(
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
        logger.error(f"❌ fn_ka10085 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10085 실패: {str(e)}")


# 주문/체결 관련 API

@router.post("/fn_ka10088", summary="키움 미체결 분할주문 상세 (ka10088)")
async def api_fn_ka10088(
    request: UnfilledSplitOrderDetailRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 미체결 분할주문 상세 (ka10088)
    
    - **ord_no**: 주문번호 (20자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - osop: 미체결분할주문리스트 (LIST)
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
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📋 fn_ka10088 요청: {request.ord_no}")
        
        result = await fn_ka10088(
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
        logger.error(f"❌ fn_ka10088 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10088 실패: {str(e)}")


# 계좌 현황 관련 API (kt00001 ~ kt00018)

@router.post("/fn_kt00001", summary="키움 예수금상세현황요청 (kt00001)")
async def api_fn_kt00001(
    request: DepositDetailStatusRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 예수금상세현황요청 (kt00001)
    
    - **qry_tp**: 조회구분 (Required, 3:추정조회, 2:일반조회)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
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
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"💳 fn_kt00001 요청: 조회구분={request.qry_tp}")
        
        result = await fn_kt00001(
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
        logger.error(f"❌ fn_kt00001 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00001 실패: {str(e)}")


@router.post("/fn_kt00002", summary="키움 일별추정예탁자산현황요청 (kt00002)")
async def api_fn_kt00002(
    request: DailyEstimatedAssetStatusRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 일별추정예탁자산현황요청 (kt00002)
    
    - **start_dt**: 시작조회기간 (Required, YYYYMMDD)
    - **end_dt**: 종료조회기간 (Required, YYYYMMDD)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - daly_prsm_dpst_aset_amt_prst: 일별추정예탁자산현황 (LIST)
      - dt: 일자
      - entr: 예수금
      - grnt_use_amt: 담보대출금
      - crd_loan: 신용융자금
      - ls_grnt: 대주담보금
      - repl_amt: 대용금
      - prsm_dpst_aset_amt: 추정예탁자산
      - prsm_dpst_aset_amt_bncr_skip: 추정예탁자산수익증권제외
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📊 fn_kt00002 요청: {request.start_dt} ~ {request.end_dt}")
        
        result = await fn_kt00002(
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
        logger.error(f"❌ fn_kt00002 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00002 실패: {str(e)}")


@router.post("/fn_kt00003", summary="키움 추정자산조회요청 (kt00003)")
async def api_fn_kt00003(
    request: EstimatedAssetInquiryRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 추정자산조회요청 (kt00003)
    
    - **qry_tp**: 상장폐지조회구분 (Required, 0:전체, 1:상장폐지종목제외)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - prsm_dpst_aset_amt: 추정예탁자산
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"💰 fn_kt00003 요청: 상장폐지조회구분={request.qry_tp}")
        
        result = await fn_kt00003(
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
        logger.error(f"❌ fn_kt00003 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00003 실패: {str(e)}")


@router.post("/fn_kt00004", summary="키움 계좌평가현황요청 (kt00004)")
async def api_fn_kt00004(
    request: AccountEvaluationStatusRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 계좌평가현황요청 (kt00004)
    
    계좌평가현황과 보유종목별 평가정보를 조회합니다
    
    **요청 파라미터:**
    - **qry_tp**: 상장폐지조회구분 (0:전체, 1:상장폐지종목제외)
    - **dmst_stex_tp**: 국내거래소구분 (KRX:한국거래소, NXT:넥스트트레이드)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드 (Main 19개):**
    - **acnt_no**: 계좌번호 (String, 10)
    - **evlt_amt**: 평가금액 (String, 15)
    - **bfdy_buy_amt**: 전일매수금액 (String, 15)
    - **tot_stck_evlt_amt**: 총주식평가금액 (String, 15)
    - **bfdy_evlt_amt**: 전일평가금액 (String, 15)
    - **d2_bfdy_evlt_amt**: 전전일평가금액 (String, 15)
    - **tot_evlu_pfls_amt**: 총평가손익금액 (String, 15)
    - **tot_pftrt**: 총수익률 (String, 12)
    - **bfdy_tot_asst_evlt_amt**: 전일총자산평가금액 (String, 15)
    - **asst_icdc_amt**: 자산증감액 (String, 15)
    - **asst_icdc_erng_rt**: 자산증감수익률 (String, 12)
    - **ord_psbl_tot_amt**: 주문가능총금액 (String, 15)
    - **mnrg_tot_amt**: 증거금총액 (String, 15)
    - **ssts_dvd_amt**: 신주인수권배당금액 (String, 15)
    - **tot_loan_amt**: 총대출금액 (String, 15)
    - **spsn_stck_evlt_amt**: 신용주식평가금액 (String, 15)
    - **d1_ovrd_amt**: 1일연체금액 (String, 15)
    - **d2_ovrd_amt**: 2일연체금액 (String, 15)
    - **d3_ovrd_amt**: 3일이상연체금액 (String, 15)
    
    **응답 필드 (stk_acnt_evlt_prst 리스트, 각 항목 15개 필드):**
    - **stk_cd**: 종목코드 (String, 9)
    - **stk_nm**: 종목명 (String, 40)
    - **hldg_qty**: 보유수량 (String, 10)
    - **ord_psbl_qty**: 주문가능수량 (String, 10)
    - **pchs_avg_prc**: 매입평균가격 (String, 10)
    - **evlt_prc**: 평가가격 (String, 8)
    - **evlt_amt**: 평가금액 (String, 15)
    - **evlu_pfls_amt**: 평가손익금액 (String, 15)
    - **evlu_pfls_rt**: 평가손익률 (String, 12)
    - **evlu_erng_rt**: 평가수익률 (String, 10)
    - **loan_amt**: 대출금액 (String, 15)
    - **stck_loan_amt**: 주식대출금액 (String, 15)
    - **expd_dt**: 만료일자 (String, 8)
    - **fltt_rt**: 등락율 (String, 12)
    - **bfdy_cprs_icdc_amt**: 전일대비증감금액 (String, 15)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📈 fn_kt00004 요청: qry_tp={request.qry_tp}, dmst_stex_tp={request.dmst_stex_tp}")
        
        result = await fn_kt00004(
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
        logger.error(f"❌ fn_kt00004 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00004 실패: {str(e)}")


@router.post("/fn_kt00005", summary="키움 체결잔고요청 (kt00005)")
async def api_fn_kt00005(
    request: FilledBalanceRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 체결잔고요청 (kt00005)
    
    계좌의 예수금 정보와 보유종목별 체결잔고 정보를 조회합니다
    
    **요청 파라미터:**
    - **dmst_stex_tp**: 국내거래소구분 (KRX:한국거래소, NXT:넥스트트레이드)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드 (Main 30개):**
    - **entr**: 예수금 (String, 12)
    - **entr_d1**: 예수금D+1 (String, 12)
    - **entr_d2**: 예수금D+2 (String, 12)
    - **pymn_alow_amt**: 출금가능금액 (String, 12)
    - **uncl_stk_amt**: 미수확보금 (String, 12)
    - **repl_amt**: 대용금 (String, 12)
    - **rght_repl_amt**: 권리대용금 (String, 12)
    - **ord_alowa**: 주문가능현금 (String, 12)
    - **ch_uncla**: 현금미수금 (String, 12)
    - **crd_int_npay_gold**: 신용이자미납금 (String, 12)
    - **etc_loana**: 기타대여금 (String, 12)
    - **nrpy_loan**: 미상환융자금 (String, 12)
    - **profa_ch**: 증거금현금 (String, 12)
    - **repl_profa**: 증거금대용 (String, 12)
    - **stk_buy_tot_amt**: 주식매수총액 (String, 12)
    - **evlt_amt_tot**: 평가금액합계 (String, 12)
    - **tot_pl_tot**: 총손익합계 (String, 12)
    - **tot_pl_rt**: 총손익률 (String, 12)
    - **tot_re_buy_alowa**: 총재매수가능금액 (String, 12)
    - **20ord_alow_amt**: 20%주문가능금액 (String, 12)
    - **30ord_alow_amt**: 30%주문가능금액 (String, 12)
    - **40ord_alow_amt**: 40%주문가능금액 (String, 12)
    - **50ord_alow_amt**: 50%주문가능금액 (String, 12)
    - **60ord_alow_amt**: 60%주문가능금액 (String, 12)
    - **100ord_alow_amt**: 100%주문가능금액 (String, 12)
    - **crd_loan_tot**: 신용융자합계 (String, 12)
    - **crd_loan_ls_tot**: 신용융자대주합계 (String, 12)
    - **crd_grnt_rt**: 신용담보비율 (String, 12)
    - **dpst_grnt_use_amt_amt**: 예탁담보대출금액 (String, 12)
    - **grnt_loan_amt**: 매도담보대출금액 (String, 12)
    
    **응답 필드 (stk_cntr_remn 리스트, 각 항목 13개 필드):**
    - **crd_tp**: 신용구분 (String, 2)
    - **loan_dt**: 대출일 (String, 8)
    - **expr_dt**: 만기일 (String, 8)
    - **stk_cd**: 종목번호 (String, 12)
    - **stk_nm**: 종목명 (String, 30)
    - **setl_remn**: 결제잔고 (String, 12)
    - **cur_qty**: 현재잔고 (String, 12)
    - **cur_prc**: 현재가 (String, 12)
    - **buy_uv**: 매입단가 (String, 12)
    - **pur_amt**: 매입금액 (String, 12)
    - **evlt_amt**: 평가금액 (String, 12)
    - **evltv_prft**: 평가손익 (String, 12)
    - **pl_rt**: 손익률 (String, 12)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📋 fn_kt00005 요청: dmst_stex_tp={request.dmst_stex_tp}")
        
        result = await fn_kt00005(
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
        logger.error(f"❌ fn_kt00005 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00005 실패: {str(e)}")


# @router.post("/fn_kt00006", summary="키움 선물옵션자산현황요청 (kt00006)")
# fn_kt00006 함수가 functions/account.py에 구현되지 않았으므로 일시적으로 비활성화


@router.post("/fn_kt00007", summary="키움 계좌별주문체결내역상세요청 (kt00007)")
async def api_fn_kt00007(
    request: AccountOrderFilledDetailRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 계좌별주문체결내역상세요청 (kt00007)
    
    계좌의 주문 및 체결 내역 상세 정보를 조회합니다
    
    **요청 파라미터:**
    - **ord_dt**: 주문일자 YYYYMMDD (선택사항)
    - **qry_tp**: 조회구분 (1:주문순, 2:역순, 3:미체결, 4:체결내역만)
    - **stk_bond_tp**: 주식채권구분 (0:전체, 1:주식, 2:채권)
    - **sell_tp**: 매도수구분 (0:전체, 1:매도, 2:매수)
    - **stk_cd**: 종목코드 (선택사항, 공백일때 전체종목)
    - **fr_ord_no**: 시작주문번호 (선택사항, 공백일때 전체주문)
    - **dmst_stex_tp**: 국내거래소구분 (%:전체, KRX:한국거래소, NXT:넥스트트레이드, SOR:최선주문집행)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드 (acnt_ord_cntr_prps_dtl 리스트, 각 항목 22개 필드):**
    - **ord_no**: 주문번호 (String, 7)
    - **stk_cd**: 종목번호 (String, 12)
    - **trde_tp**: 매매구분 (String, 20)
    - **crd_tp**: 신용구분 (String, 20)
    - **ord_qty**: 주문수량 (String, 10)
    - **ord_uv**: 주문단가 (String, 10)
    - **cnfm_qty**: 확인수량 (String, 10)
    - **acpt_tp**: 접수구분 (String, 20)
    - **rsrv_tp**: 반대여부 (String, 20)
    - **ord_tm**: 주문시간 (String, 8)
    - **ori_ord**: 원주문 (String, 7)
    - **stk_nm**: 종목명 (String, 40)
    - **io_tp_nm**: 주문구분 (String, 20)
    - **loan_dt**: 대출일 (String, 8)
    - **cntr_qty**: 체결수량 (String, 10)
    - **cntr_uv**: 체결단가 (String, 10)
    - **ord_remnq**: 주문잔량 (String, 10)
    - **comm_ord_tp**: 통신구분 (String, 20)
    - **mdfy_cncl**: 정정취소 (String, 20)
    - **cnfm_tm**: 확인시간 (String, 8)
    - **dmst_stex_tp**: 국내거래소구분 (String, 8)
    - **cond_uv**: 스톱가 (String, 10)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📊 fn_kt00007 요청: qry_tp={request.qry_tp}, stk_bond_tp={request.stk_bond_tp}, sell_tp={request.sell_tp}, dmst_stex_tp={request.dmst_stex_tp}")
        
        result = await fn_kt00007(
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
        logger.error(f"❌ fn_kt00007 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00007 실패: {str(e)}")


# 간소화된 계좌 현황 API들 (kt00008 ~ kt00018)

@router.post("/fn_kt00008", summary="키움 계좌별익일결제예정내역요청 (kt00008)")
async def api_fn_kt00008(
    request: AccountNextDaySettlementRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 계좌별익일결제예정내역요청 (kt00008)
    
    계좌의 익일 결제 예정 내역을 조회합니다
    
    **요청 파라미터:**
    - **strt_dcd_seq**: 시작결제번호 (선택사항, 7자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드 (Main 4개):**
    - **trde_dt**: 매매일자 (String, 8)
    - **setl_dt**: 결제일자 (String, 8)
    - **sell_amt_sum**: 매도정산합 (String, 12)
    - **buy_amt_sum**: 매수정산합 (String, 12)
    
    **응답 필드 (acnt_nxdy_setl_frcs_prps_array 리스트, 각 항목 15개 필드):**
    - **seq**: 일련번호 (String, 7)
    - **stk_cd**: 종목번호 (String, 12)
    - **loan_dt**: 대출일 (String, 8)
    - **qty**: 수량 (String, 12)
    - **engg_amt**: 약정금액 (String, 12)
    - **cmsn**: 수수료 (String, 12)
    - **incm_tax**: 소득세 (String, 12)
    - **rstx**: 농특세 (String, 12)
    - **stk_nm**: 종목명 (String, 40)
    - **sell_tp**: 매도수구분 (String, 10)
    - **unp**: 단가 (String, 12)
    - **exct_amt**: 정산금액 (String, 12)
    - **trde_tax**: 거래세 (String, 12)
    - **resi_tax**: 주민세 (String, 12)
    - **crd_tp**: 신용구분 (String, 20)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📋 fn_kt00008 요청: strt_dcd_seq={request.strt_dcd_seq or ''}")
        result = await fn_kt00008(token=access_token, data=request.dict(), cont_yn=cont_yn, next_key=next_key)
        return JSONResponse(status_code=result['Code'], content=result)
    except Exception as e:
        logger.error(f"❌ fn_kt00008 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00008 실패: {str(e)}")


@router.post("/fn_kt00009", summary="키움 계좌별주문체결현황요청 (kt00009)")
async def api_fn_kt00009(
    request: AccountOrderFilledStatusRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 계좌별주문체결현황요청 (kt00009)
    
    계좌별 주문 및 체결 현황 정보를 조회합니다.
    
    **요청 파라미터:**
    - **ord_dt** (Optional[str]): 주문일자 YYYYMMDD (선택사항)
    - **stk_bond_tp** (str): 주식채권구분 (0:전체, 1:주식, 2:채권)
    - **mrkt_tp** (str): 시장구분 (0:전체, 1:코스피, 2:코스닥, 3:OTCBB, 4:ECN)
    - **sell_tp** (str): 매도수구분 (0:전체, 1:매도, 2:매수)
    - **qry_tp** (str): 조회구분 (0:전체, 1:체결)
    - **stk_cd** (Optional[str]): 종목코드 (선택사항, 전문 조회할 종목코드)
    - **fr_ord_no** (Optional[str]): 시작주문번호 (선택사항)
    - **dmst_stex_tp** (str): 국내거래소구분 (%:전체, KRX:한국거래소, NXT:넥스트트레이드, SOR:최선주문집행)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **tot_ord_cnt**: 전체주문건수 (String, 5)
    - **tot_cntr_cnt**: 전체체결건수 (String, 5)
    - **tot_unsett_cnt**: 전체미체결건수 (String, 5)
    - **acnt_ord_cntr_prst_array**: 계좌별주문체결현황 리스트
      - **ord_no**: 주문번호 (String, 7)
      - **stk_cd**: 종목코드 (String, 12)
      - **stk_nm**: 종목명 (String, 40)
      - **trde_tp**: 매매구분 (String, 20)
      - **crd_tp**: 신용구분 (String, 20)
      - **ord_qty**: 주문수량 (String, 10)
      - **ord_prc**: 주문가격 (String, 10)
      - **cnfm_qty**: 확인수량 (String, 10)
      - **cntr_qty**: 체결수량 (String, 10)
      - **cntr_prc**: 체결가격 (String, 10)
      - **acpt_dt**: 접수일자 (String, 8)
      - **acpt_tm**: 접수시간 (String, 6)
      - **ord_stcd**: 주문상태코드 (String, 2)
      - **ord_stnm**: 주문상태명 (String, 10)
      - **cmpr_prc**: 대비가격 (String, 10)
      - **cmpr_pl_rt**: 손익률 (String, 9)
      - **ord_dt**: 주문일자 (String, 8)
      - **ord_tm**: 주문시간 (String, 6)
      - **ord_remnq**: 주문잔량 (String, 10)
      - **comm_ord_tp**: 통신구분 (String, 20)
      - **ori_ord_no**: 원주문번호 (String, 7)
      - **loan_dt**: 대출일자 (String, 8)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📊 fn_kt00009 요청: 주식채권구분={request.stk_bond_tp}, 시장구분={request.mrkt_tp}, 조회구분={request.qry_tp}")
        result = await fn_kt00009(token=access_token, data=request.dict(), cont_yn=cont_yn, next_key=next_key)
        return JSONResponse(status_code=result['Code'], content=result)
    except Exception as e:
        logger.error(f"❌ fn_kt00009 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00009 실패: {str(e)}")


@router.post("/fn_kt00010", summary="키움 주문인출가능금액요청 (kt00010)")
async def api_fn_kt00010(
    request: OrderWithdrawalAmountRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 주문인출가능금액요청 (kt00010)
    
    종목별 주문가능금액 및 수량 정보를 조회합니다.
    
    **요청 파라미터:**
    - **io_amt** (Optional[str]): 입출금액 (선택사항, 12자리)
    - **stk_cd** (str): 종목번호 (12자리)
    - **trde_tp** (str): 매매구분 (1:매도, 2:매수)
    - **trde_qty** (Optional[str]): 매매수량 (선택사항, 10자리)
    - **uv** (str): 매수가격 (10자리)
    - **exp_buy_unp** (Optional[str]): 예상매수단가 (선택사항, 10자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **profa_20ord_alow_amt**: 증거금20%주문가능금액 (String, 12)
    - **profa_20ord_alowq**: 증거금20%주문가능수량 (String, 10)
    - **profa_30ord_alow_amt**: 증거금30%주문가능금액 (String, 12)
    - **profa_30ord_alowq**: 증거금30%주문가능수량 (String, 10)
    - **profa_40ord_alow_amt**: 증거금40%주문가능금액 (String, 12)
    - **profa_40ord_alowq**: 증거금40%주문가능수량 (String, 10)
    - **profa_50ord_alow_amt**: 증거금50%주문가능금액 (String, 12)
    - **profa_50ord_alowq**: 증거금50%주문가능수량 (String, 10)
    - **profa_60ord_alow_amt**: 증거금60%주문가능금액 (String, 12)
    - **profa_60ord_alowq**: 증거금60%주문가능수량 (String, 10)
    - **profa_rdex_60ord_alow_amt**: 증거금감면60%주문가능금 (String, 12)
    - **profa_rdex_60ord_alowq**: 증거금감면60%주문가능수 (String, 10)
    - **profa_100ord_alow_amt**: 증거금100%주문가능금액 (String, 12)
    - **profa_100ord_alowq**: 증거금100%주문가능수량 (String, 10)
    - **pred_reu_alowa**: 전일재사용가능금액 (String, 12)
    - **tdy_reu_alowa**: 금일재사용가능금액 (String, 12)
    - **entr**: 예수금 (String, 12)
    - **repl_amt**: 대용금 (String, 12)
    - **uncla**: 미수금 (String, 12)
    - **ord_pos_repl**: 주문가능대용 (String, 12)
    - **ord_alowa**: 주문가능현금 (String, 12)
    - **wthd_alowa**: 인출가능금액 (String, 12)
    - **nxdy_wthd_alowa**: 익일인출가능금액 (String, 12)
    - **pur_amt**: 매입금액 (String, 12)
    - **cmsn**: 수수료 (String, 12)
    - **pur_exct_amt**: 매입정산금 (String, 12)
    - **d2entra**: D2추정예수금 (String, 12)
    - **profa_rdex_aplc_tp**: 증거금감면적용구분 (String, 1) - 0:일반, 1:60%감면
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"💳 fn_kt00010 요청: 종목번호={request.stk_cd}, 매매구분={request.trde_tp}, 매수가격={request.uv}")
        result = await fn_kt00010(token=access_token, data=request.dict(), cont_yn=cont_yn, next_key=next_key)
        return JSONResponse(status_code=result['Code'], content=result)
    except Exception as e:
        logger.error(f"❌ fn_kt00010 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00010 실패: {str(e)}")


@router.post("/fn_kt00011", summary="키움 증거금율별주문가능수량조회요청 (kt00011)")
async def api_fn_kt00011(
    request: MarginRateOrderQuantityRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 증거금율별주문가능수량조회요청 (kt00011)
    
    종목별 증거금율에 따른 주문가능수량 정보를 조회합니다.
    
    **요청 파라미터:**
    - **stk_cd** (str): 종목번호 (12자리)
    - **uv** (Optional[str]): 매수가격 (선택사항, 10자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **stk_profa_rt**: 종목증거금율 (String, 15)
    - **profa_rt**: 계좌증거금율 (String, 15)
    - **aplc_rt**: 적용증거금율 (String, 15)
    - **profa_20ord_alow_amt**: 증거금20%주문가능금액 (String, 12)
    - **profa_20ord_alowq**: 증거금20%주문가능수량 (String, 12)
    - **profa_20pred_reu_amt**: 증거금20%전일재사용금액 (String, 12)
    - **profa_20tdy_reu_amt**: 증거금20%금일재사용금액 (String, 12)
    - **profa_30ord_alow_amt**: 증거금30%주문가능금액 (String, 12)
    - **profa_30ord_alowq**: 증거금30%주문가능수량 (String, 12)
    - **profa_30pred_reu_amt**: 증거금30%전일재사용금액 (String, 12)
    - **profa_30tdy_reu_amt**: 증거금30%금일재사용금액 (String, 12)
    - **profa_40ord_alow_amt**: 증거금40%주문가능금액 (String, 12)
    - **profa_40ord_alowq**: 증거금40%주문가능수량 (String, 12)
    - **profa_40pred_reu_amt**: 증거금40전일재사용금액 (String, 12)
    - **profa_40tdy_reu_amt**: 증거금40%금일재사용금액 (String, 12)
    - **profa_50ord_alow_amt**: 증거금50%주문가능금액 (String, 12)
    - **profa_50ord_alowq**: 증거금50%주문가능수량 (String, 12)
    - **profa_50pred_reu_amt**: 증거금50%전일재사용금액 (String, 12)
    - **profa_50tdy_reu_amt**: 증거금50%금일재사용금액 (String, 12)
    - **profa_60ord_alow_amt**: 증거금60%주문가능금액 (String, 12)
    - **profa_60ord_alowq**: 증거금60%주문가능수량 (String, 12)
    - **profa_60pred_reu_amt**: 증거금60%전일재사용금액 (String, 12)
    - **profa_60tdy_reu_amt**: 증거금60%금일재사용금액 (String, 12)
    - **profa_100ord_alow_amt**: 증거금100%주문가능금액 (String, 12)
    - **profa_100ord_alowq**: 증거금100%주문가능수량 (String, 12)
    - **profa_100pred_reu_amt**: 증거금100%전일재사용금액 (String, 12)
    - **profa_100tdy_reu_amt**: 증거금100%금일재사용금액 (String, 12)
    - **min_ord_alow_amt**: 미수불가주문가능금액 (String, 12)
    - **min_ord_alowq**: 미수불가주문가능수량 (String, 12)
    - **min_pred_reu_amt**: 미수불가전일재사용금액 (String, 12)
    - **min_tdy_reu_amt**: 미수불가금일재사용금액 (String, 12)
    - **entr**: 예수금 (String, 12)
    - **repl_amt**: 대용금 (String, 12)
    - **uncla**: 미수금 (String, 12)
    - **ord_pos_repl**: 주문가능대용 (String, 12)
    - **ord_alowa**: 주문가능현금 (String, 12)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📊 fn_kt00011 요청: 종목번호={request.stk_cd}, 매수가격={getattr(request, 'uv', 'N/A')}")
        result = await fn_kt00011(token=access_token, data=request.dict(), cont_yn=cont_yn, next_key=next_key)
        return JSONResponse(status_code=result['Code'], content=result)
    except Exception as e:
        logger.error(f"❌ fn_kt00011 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00011 실패: {str(e)}")


@router.post("/fn_kt00012", summary="키움 신용보증금율별주문가능수량조회요청 (kt00012)")
async def api_fn_kt00012(
    request: CreditMarginRateOrderQuantityRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 신용보증금율별주문가능수량조회요청 (kt00012)
    
    종목별 신용보증금율에 따른 주문가능수량 정보를 조회합니다.
    
    **요청 파라미터:**
    - **stk_cd** (str): 종목번호 (12자리)
    - **uv** (Optional[str]): 매수가격 (선택사항, 10자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - **stk_assr_rt**: 종목보증금율 (String, 1)
    - **stk_assr_rt_nm**: 종목보증금율명 (String, 4)
    - **assr_30ord_alow_amt**: 보증금30%주문가능금액 (String, 12)
    - **assr_30ord_alowq**: 보증금30%주문가능수량 (String, 12)
    - **assr_30pred_reu_amt**: 보증금30%전일재사용금액 (String, 12)
    - **assr_30tdy_reu_amt**: 보증금30%금일재사용금액 (String, 12)
    - **assr_40ord_alow_amt**: 보증금40%주문가능금액 (String, 12)
    - **assr_40ord_alowq**: 보증금40%주문가능수량 (String, 12)
    - **assr_40pred_reu_amt**: 보증금40%전일재사용금액 (String, 12)
    - **assr_40tdy_reu_amt**: 보증금40%금일재사용금액 (String, 12)
    - **assr_50ord_alow_amt**: 보증금50%주문가능금액 (String, 12)
    - **assr_50ord_alowq**: 보증금50%주문가능수량 (String, 12)
    - **assr_50pred_reu_amt**: 보증금50%전일재사용금액 (String, 12)
    - **assr_50tdy_reu_amt**: 보증금50%금일재사용금액 (String, 12)
    - **assr_60ord_alow_amt**: 보증금60%주문가능금액 (String, 12)
    - **assr_60ord_alowq**: 보증금60%주문가능수량 (String, 12)
    - **assr_60pred_reu_amt**: 보증금60%전일재사용금액 (String, 12)
    - **assr_60tdy_reu_amt**: 보증금60%금일재사용금액 (String, 12)
    - **entr**: 예수금 (String, 12)
    - **repl_amt**: 대용금 (String, 12)
    - **uncla**: 미수금 (String, 12)
    - **ord_pos_repl**: 주문가능대용 (String, 12)
    - **ord_alowa**: 주문가능현금 (String, 12)
    - **out_alowa**: 미수가능금액 (String, 12)
    - **out_pos_qty**: 미수가능수량 (String, 12)
    - **min_amt**: 미수불가금액 (String, 12)
    - **min_qty**: 미수불가수량 (String, 12)
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📊 fn_kt00012 요청: 종목번호={request.stk_cd}, 매수가격={getattr(request, 'uv', 'N/A')}")
        result = await fn_kt00012(token=access_token, data=request.dict(), cont_yn=cont_yn, next_key=next_key)
        return JSONResponse(status_code=result['Code'], content=result)
    except Exception as e:
        logger.error(f"❌ fn_kt00012 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00012 실패: {str(e)}")


# 나머지 kt API들도 동일한 패턴으로 구현
@router.post("/fn_kt00013", summary="키움 증거금세부내역조회요청 (kt00013)")
async def api_fn_kt00013(
    request: MarginDetailInquiryRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 증거금세부내역조회요청 (kt00013)
    
    - **이 API는 요청 Body 파라미터가 없습니다 (빈 JSON 객체 전송)**
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    
    **재사용 관련:**
    - reuse_amt: 재사용금액
    - reuse_abl_amt: 재사용가능금액
    - reuse_mgn_rt: 재사용증거금율
    - tdy_ruse_cash_mgn_amt: 당일재사용현금증거금액
    - tdy_ruse_subst_mgn_amt: 당일재사용대용증거금액
    
    **현금 관련:**
    - cash_mgn_amt: 현금증거금액
    - cash_excs_amt: 현금초과액
    - cash_excs_abl_amt: 현금초과가능액
    - rqrd_cash_mgn_amt: 소요현금증거금액
    - avbl_cash_mgn_amt: 가용현금증거금액
    
    **대용 관련:**
    - subst_mgn_amt: 대용증거금액
    - subst_amt: 대용금액
    - subst_excs_amt: 대용초과액
    - subst_excs_abl_amt: 대용초과가능액
    - rqrd_subst_mgn_amt: 소요대용증거금액
    - avbl_subst_mgn_amt: 가용대용증거금액
    
    **증거금율별 주문가능금액:**
    - mgn_rt_20_ord_abl_amt: 증거금율20%주문가능금액
    - mgn_rt_30_ord_abl_amt: 증거금율30%주문가능금액
    - mgn_rt_40_ord_abl_amt: 증거금율40%주문가능금액
    - mgn_rt_50_ord_abl_amt: 증거금율50%주문가능금액
    - mgn_rt_60_ord_abl_amt: 증거금율60%주문가능금액
    - mgn_rt_100_ord_abl_amt: 증거금율100%주문가능금액
    
    **신용 관련:**
    - crdt_loan_amt: 신용대출금액
    - crdt_intst: 신용이자
    - crdt_mgn_amt: 신용증거금액
    - crdt_mgn_rt: 신용증거금율
    - crdt_rqrd_mgn_amt: 신용소요증거금액
    - crdt_avbl_mgn_amt: 신용가용증거금액
    - crdt_ruse_abl_amt: 신용재사용가능금액
    
    **기타:**
    - tot_mgn_amt: 총증거금액
    - mgn_excs_amt: 증거금초과액
    - mgn_excs_abl_amt: 증거금초과가능액
    - rqrd_mgn_amt: 소요증거금액
    - avbl_mgn_amt: 가용증거금액
    - mgn_lack_amt: 증거금부족금액
    - add_mgn_amt: 추가증거금액
    - addl_mgn_amt: 추가가능증거금액
    - nrcvb_buy_amt: 미수매수금액
    - tot_loan_amt: 총대출금액
    - loan_intst: 대출이자
    - prsm_tlex_amt: 추정세금액
    - rcvb_amt: 미수금액
    - mgn_dps_amt: 증거금예수금액
    - mgn_dps_mgn_rt: 증거금예수증거금율
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📋 fn_kt00013 요청: (Body 파라미터 없음)")
        
        # fn_kt00013 직접 호출
        result = await fn_kt00013(
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
        logger.error(f"❌ fn_kt00013 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00013 실패: {str(e)}")


@router.post("/fn_kt00015", summary="키움 위탁종합거래내역요청 (kt00015)")
async def api_fn_kt00015(
    request: TrustComprehensiveTransactionRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 위탁종합거래내역요청 (kt00015)
    
    - **strt_dt**: 시작일자 (YYYYMMDD 형식 8자리)
    - **end_dt**: 종료일자 (YYYYMMDD 형식 8자리)
    - **tp**: 구분
      - 0: 전체
      - 1: 입출금
      - 2: 입출고
      - 3: 매매
      - 4: 매수
      - 5: 매도
      - 6: 입금
      - 7: 출금
      - A: 예탁담보대출입금
      - B: 매도담보대출입금
      - C: 현금상환(융자,담보상환)
      - F: 환전
      - M: 입출금+환전
      - G: 외화매수
      - H: 외화매도
      - I: 환전정산입금
      - J: 환전정산출금
    - **stk_cd**: 종목코드 (선택사항, 12자리)
    - **crnc_cd**: 통화코드 (선택사항, 3자리)
    - **gds_tp**: 상품구분
      - 0: 전체
      - 1: 국내주식
      - 2: 수익증권
      - 3: 해외주식
      - 4: 금융상품
    - **frgn_stex_code**: 해외거래소코드 (선택사항, 10자리)
    - **dmst_stex_tp**: 국내거래소구분
      - %: 전체
      - KRX: 한국거래소
      - NXT: 넥스트트레이드
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    
    **위탁종합거래내역배열 (trst_ovrl_trde_prps_array):**
    - trde_dt: 거래일자
    - trde_no: 거래번호
    - rmrk_nm: 적요명
    - crd_deal_tp_nm: 신용거래구분명
    - exct_amt: 정산금액
    - loan_amt_rpya: 대출금상환
    - fc_trde_amt: 거래금액(외)
    - fc_exct_amt: 정산금액(외)
    - entra_remn: 예수금잔고
    - crnc_cd: 통화코드
    - trde_ocr_tp: 거래종류구분 (1:입출금, 2:펀드, 3:ELS, 4:채권, 5:해외채권, 6:외화RP, 7:외화발행어음)
    - trde_kind_nm: 거래종류명
    - stk_nm: 종목명
    - trde_amt: 거래금액
    - trde_agri_tax: 거래및농특세
    - rpy_diffa: 상환차금
    - fc_trde_tax: 거래세(외)
    - dly_sum: 연체합
    - fc_entra: 외화예수금잔고
    - mdia_tp_nm: 매체구분명
    - io_tp: 입출구분
    - io_tp_nm: 입출구분명
    - orig_deal_no: 원거래번호
    - stk_cd: 종목코드
    - trde_qty_jwa_cnt: 거래수량/좌수
    - cmsn: 수수료
    - int_ls_usfe: 이자/대주이용
    - fc_cmsn: 수수료(외)
    - fc_dly_sum: 연체합(외)
    - vlbl_nowrm: 유가금잔
    - proc_tm: 처리시간
    - isin_cd: ISIN코드
    - stex_cd: 거래소코드
    - stex_nm: 거래소명
    - trde_unit: 거래단가/환율
    - incm_resi_tax: 소득/주민세
    - loan_dt: 대출일
    - uncl_ocr: 미수(원/주)
    - rpym_sum: 변제합
    - cntr_dt: 체결일
    - rcpy_no: 출납번호
    - prcsr: 처리자
    - proc_brch: 처리점
    - trde_stle: 매매형태
    - txon_base_pric: 과세기준가
    - tax_sum_cmsn: 세금수수료합
    - frgn_pay_txam: 외국납부세액(외)
    - fc_uncl_ocr: 미수(외)
    - rpym_sum_fr: 변제합(외)
    - rcpmnyer: 입금자
    - trde_prtc_tp: 거래내역구분
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📊 fn_kt00015 요청: {request.strt_dt} ~ {request.end_dt} (구분: {request.tp})")
        
        # fn_kt00015 직접 호출
        result = await fn_kt00015(
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
        logger.error(f"❌ fn_kt00015 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00015 실패: {str(e)}")


@router.post("/fn_kt00016", summary="키움 일별계좌수익률상세현황요청 (kt00016)")
async def api_fn_kt00016(
    request: DailyAccountReturnDetailRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 일별계좌수익률상세현황요청 (kt00016)
    
    - **fr_dt**: 평가시작일 (YYYYMMDD 형식 8자리)
    - **to_dt**: 평가종료일 (YYYYMMDD 형식 8자리)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    
    **관리정보:**
    - mang_empno: 관리사원번호
    - mngr_nm: 관리자명
    - dept_nm: 관리자지점
    
    **예수금 정보:**
    - entr_fr: 예수금_초
    - entr_to: 예수금_말
    
    **유가증권 평가정보:**
    - scrt_evlt_amt_fr: 유가증권평가금액_초
    - scrt_evlt_amt_to: 유가증권평가금액_말
    
    **대주 관련:**
    - ls_grnt_fr: 대주담보금_초
    - ls_grnt_to: 대주담보금_말
    - ls_evlta_fr: 대주평가금_초
    - ls_evlta_to: 대주평가금_말
    
    **신용 관련:**
    - crd_loan_fr: 신용융자금_초
    - crd_loan_to: 신용융자금_말
    - crd_int_npay_gold_fr: 신용이자미납금_초
    - crd_int_npay_gold_to: 신용이자미납금_말
    - crd_int_fr: 신용이자_초
    - crd_int_to: 신용이자_말
    
    **미수금 관련:**
    - ch_uncla_fr: 현금미수금_초
    - ch_uncla_to: 현금미수금_말
    
    **대용금 관련:**
    - krw_asgna_fr: 원화대용금_초
    - krw_asgna_to: 원화대용금_말
    
    **권리 관련:**
    - rght_evlta_fr: 권리평가금_초
    - rght_evlta_to: 권리평가금_말
    
    **대출 관련:**
    - loan_amt_fr: 대출금_초
    - loan_amt_to: 대출금_말
    - etc_loana_fr: 기타대여금_초
    - etc_loana_to: 기타대여금_말
    
    **순자산 및 수익률:**
    - tot_amt_fr: 순자산액계_초
    - tot_amt_to: 순자산액계_말
    - invt_bsamt: 투자원금평잔
    - evltv_prft: 평가손익
    - prft_rt: 수익률
    - tern_rt: 회전율
    
    **기간내 거래정보:**
    - termin_tot_trns: 기간내총입금
    - termin_tot_pymn: 기간내총출금
    - termin_tot_inq: 기간내총입고
    - termin_tot_outq: 기간내총출고
    
    **대용매도 관련:**
    - futr_repl_sella: 선물대용매도금액
    - trst_repl_sella: 위탁대용매도금액
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📈 fn_kt00016 요청: {request.fr_dt} ~ {request.to_dt}")
        
        # fn_kt00016 직접 호출
        result = await fn_kt00016(
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
        logger.error(f"❌ fn_kt00016 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00016 실패: {str(e)}")


@router.post("/fn_kt00017", summary="키움 계좌별당일현황요청 (kt00017)")
async def api_fn_kt00017(
    request: AccountDailyStatusRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 계좌별당일현황요청 (kt00017)
    
    - **이 API는 요청 Body 파라미터가 없습니다 (빈 JSON 객체 전송)**
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    
    **D+2 관련 정보:**
    - d2_entra: D+2추정예수금
    - gnrl_stk_evlt_amt_d2: 일반주식평가금액D+2
    - dpst_grnt_use_amt_d2: 예탁담보대출금D+2
    - crd_stk_evlt_amt_d2: 예탁담보주식평가금액D+2
    - crd_loan_d2: 신용융자금D+2
    - crd_loan_evlta_d2: 신용융자평가금D+2
    - crd_ls_grnt_d2: 신용대주담보금D+2
    - crd_ls_evlta_d2: 신용대주평가금D+2
    
    **신용 관련 정보:**
    - crd_int_npay_gold: 신용이자미납금
    - crd_int_amt: 신용이자금액
    
    **입출금/입출고 정보:**
    - ina_amt: 입금금액
    - outa: 출금금액
    - inq_amt: 입고금액
    - outq_amt: 출고금액
    
    **매매 관련 정보:**
    - sell_amt: 매도금액
    - buy_amt: 매수금액
    - cmsn: 수수료
    - tax: 세금
    
    **대출 관련 정보:**
    - etc_loana: 기타대여금
    - stk_pur_cptal_loan_amt: 주식매입자금대출금
    - sel_prica_grnt_loan_int_amt_amt: 매도대금담보대출이자금액
    
    **평가금액 정보:**
    - rp_evlt_amt: RP평가금액
    - bd_evlt_amt: 채권평가금액
    - elsevlt_amt: ELS평가금액
    
    **기타 정보:**
    - dvida_amt: 배당금액
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📊 fn_kt00017 요청: (Body 파라미터 없음)")
        
        # fn_kt00017 직접 호출
        result = await fn_kt00017(
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
        logger.error(f"❌ fn_kt00017 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00017 실패: {str(e)}")


@router.post("/fn_kt00018", summary="키움 계좌평가잔고내역요청 (kt00018)")
async def api_fn_kt00018(
    request: AccountEvaluationBalanceDetailRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 계좌평가잔고내역요청 (kt00018)
    
    - **qry_tp**: 조회구분
      - 1: 합산
      - 2: 개별
    - **dmst_stex_tp**: 국내거래소구분
      - KRX: 한국거래소
      - NXT: 넥스트트레이드
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    
    **포트폴리오 요약 정보:**
    - tot_pur_amt: 총매입금액
    - tot_evlt_amt: 총평가금액
    - tot_evlt_pl: 총평가손익금액
    - tot_prft_rt: 총수익률(%)
    - prsm_dpst_aset_amt: 추정예탁자산
    
    **대출 관련 정보:**
    - tot_loan_amt: 총대출금
    - tot_crd_loan_amt: 총융자금액
    - tot_crd_ls_amt: 총대주금액
    
    **계좌평가잔고개별합산 (acnt_evlt_remn_indv_tot) - 배열:**
    
    **종목 기본정보:**
    - stk_cd: 종목번호
    - stk_nm: 종목명
    - cur_prc: 현재가
    - pred_close_pric: 전일종가
    
    **매입 정보:**
    - pur_pric: 매입가
    - pur_amt: 매입금액
    - pur_cmsn: 매입수수료
    
    **보유 정보:**
    - rmnd_qty: 보유수량
    - trde_able_qty: 매매가능수량
    - poss_rt: 보유비중(%)
    
    **거래 정보:**
    - pred_buyq: 전일매수수량
    - pred_sellq: 전일매도수량
    - tdy_buyq: 금일매수수량
    - tdy_sellq: 금일매도수량
    
    **평가 정보:**
    - evlt_amt: 평가금액
    - evltv_prft: 평가손익
    - prft_rt: 수익률(%)
    
    **수수료 및 세금:**
    - sell_cmsn: 평가수수료
    - tax: 세금
    - sum_cmsn: 수수료합 (매입수수료 + 평가수수료)
    
    **신용 관련:**
    - crd_tp: 신용구분
    - crd_tp_nm: 신용구분명
    - crd_loan_dt: 대출일
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📋 fn_kt00018 요청: 조회구분={request.qry_tp}, 거래소={request.dmst_stex_tp}")
        
        # fn_kt00018 직접 호출
        result = await fn_kt00018(
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
        logger.error(f"❌ fn_kt00018 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_kt00018 실패: {str(e)}")


# 매매일지 관련 API

@router.post("/fn_ka10170", summary="키움 당일매매일지요청 (ka10170)")
async def api_fn_ka10170(
    request: DailyTradingLogRequest,
    cont_yn: str = Query("N", description="연속조회여부 (N: 최초, Y: 연속)"),
    next_key: str = Query("", description="연속조회키"),
    access_token: str = Depends(get_valid_access_token)
) -> JSONResponse:
    """
    키움증권 당일매매일지요청 (ka10170)
    
    - **base_dt**: 기준일자 YYYYMMDD (Optional, 공백시 금일데이터, 최근 2개월까지 제공)
    - **ottks_tp**: 단주구분 (Required, 1:당일매수에 대한 당일매도, 2:당일매도 전체)
    - **ch_crd_tp**: 현금신용구분 (Required, 0:전체, 1:현금매매만, 2:신용매매만)
    - **cont_yn**: 연속조회여부 (N: 최초, Y: 연속)
    - **next_key**: 연속조회키 (연속조회시 필요)
    
    **응답 필드:**
    - tot_sell_amt: 총매도금액
    - tot_buy_amt: 총매수금액
    - tot_cmsn_tax: 총수수료_세금
    - tot_exct_amt: 총정산금액
    - tot_pl_amt: 총손익금액
    - tot_prft_rt: 총수익률
    - tdy_trde_diary: 당일매매일지 (LIST)
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
    
    **키움 API 원본 응답을 그대로 반환합니다**
    """
    try:
        logger.info(f"📔 fn_ka10170 요청: 기준일자={request.base_dt}, 단주구분={request.ottks_tp}, 현금신용구분={request.ch_crd_tp}")
        
        result = await fn_ka10170(
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
        logger.error(f"❌ fn_ka10170 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"fn_ka10170 실패: {str(e)}")