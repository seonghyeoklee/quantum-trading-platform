"""
키움증권 계좌 관련 데이터 모델

계좌 API 전용 Pydantic 모델 정의:
- 손익 관련: ka10072~ka10077, ka10085, ka10170
- 주문/체결 관련: ka10075, ka10076, ka10088  
- 계좌 현황 관련: kt00001~kt00018

기존 패턴 완전 준수하여 키움 API 스펙과 1:1 매핑
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator


# ============== 손익 관련 API 모델 ==============

class DailyStockProfitLossRequest(BaseModel):
    """일자별종목별실현손익요청_일자 (ka10072)"""
    
    stk_cd: str = Field(..., max_length=6, description="종목코드")
    strt_dt: str = Field(..., max_length=8, description="시작일자 (YYYYMMDD)")
    
    @validator('strt_dt')
    def validate_date_format(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('날짜는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "strt_dt": "20241128"
            }
        }


class DailyStockProfitLossPeriodRequest(BaseModel):
    """일자별종목별실현손익요청_기간 (ka10073) - 정확한 키움 스펙"""
    
    stk_cd: str = Field(..., max_length=6, description="종목코드")
    strt_dt: str = Field(..., max_length=8, description="시작일자 (YYYYMMDD)")
    end_dt: str = Field(..., max_length=8, description="종료일자 (YYYYMMDD)")
    
    @validator('strt_dt', 'end_dt')
    def validate_date_format(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('날짜는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "strt_dt": "20241128", 
                "end_dt": "20241128"
            }
        }


class DailyProfitLossRequest(BaseModel):
    """일자별실현손익요청 (ka10074) - 정확한 키움 스펙"""
    
    strt_dt: str = Field(..., max_length=8, description="시작일자 (String, Required, 8자리 YYYYMMDD)")
    end_dt: str = Field(..., max_length=8, description="종료일자 (String, Required, 8자리 YYYYMMDD)")
    
    @validator('strt_dt', 'end_dt')
    def validate_date_format(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('날짜는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "strt_dt": "20241128",
                "end_dt": "20241128"
            }
        }


class UnfilledOrderRequest(BaseModel):
    """미체결요청 (ka10075) - 정확한 키움 스펙"""
    
    all_stk_tp: str = Field(..., max_length=1, description="전체종목구분 (String, Required, 0:전체, 1:종목)")
    trde_tp: str = Field(..., max_length=1, description="매매구분 (String, Required, 0:전체, 1:매도, 2:매수)")
    stk_cd: Optional[str] = Field(None, max_length=6, description="종목코드 (String, Optional, 6자리)")
    stex_tp: str = Field(..., max_length=1, description="거래소구분 (String, Required, 0:통합, 1:KRX, 2:NXT)")
    
    @validator('all_stk_tp')
    def validate_all_stk_tp(cls, v):
        if v not in ['0', '1']:
            raise ValueError('전체종목구분은 0(전체) 또는 1(종목)이어야 합니다')
        return v
    
    @validator('trde_tp')
    def validate_trde_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('매매구분은 0(전체), 1(매도), 2(매수) 중 하나여야 합니다')
        return v
    
    @validator('stex_tp')
    def validate_stex_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('거래소구분은 0(통합), 1(KRX), 2(NXT) 중 하나여야 합니다')
        return v
    
    @validator('stk_cd')
    def validate_stk_cd(cls, v):
        if v and (len(v) != 6 or not v.isdigit()):
            raise ValueError('종목코드는 6자리 숫자여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "all_stk_tp": "1",
                "trde_tp": "0", 
                "stk_cd": "005930",
                "stex_tp": "0"
            }
        }


class FilledOrderRequest(BaseModel):
    """체결요청 (ka10076) - 정확한 키움 스펙"""
    
    stk_cd: Optional[str] = Field(None, max_length=6, description="종목코드 (String, Optional, 6자리)")
    qry_tp: str = Field(..., max_length=1, description="조회구분 (String, Required, 0:전체, 1:종목)")
    sell_tp: str = Field(..., max_length=1, description="매도수구분 (String, Required, 0:전체, 1:매도, 2:매수)")
    ord_no: Optional[str] = Field(None, max_length=10, description="주문번호 (String, Optional, 검색 기준 값으로 입력한 주문번호보다 과거 체결내역 조회)")
    stex_tp: str = Field(..., max_length=1, description="거래소구분 (String, Required, 0:통합, 1:KRX, 2:NXT)")
    
    @validator('qry_tp')
    def validate_qry_tp(cls, v):
        if v not in ['0', '1']:
            raise ValueError('조회구분은 0(전체) 또는 1(종목)이어야 합니다')
        return v
    
    @validator('sell_tp')
    def validate_sell_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('매도수구분은 0(전체), 1(매도), 2(매수) 중 하나여야 합니다')
        return v
    
    @validator('stex_tp')
    def validate_stex_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('거래소구분은 0(통합), 1(KRX), 2(NXT) 중 하나여야 합니다')
        return v
    
    @validator('stk_cd')
    def validate_stk_cd(cls, v):
        if v and (len(v) != 6 or not v.isdigit()):
            raise ValueError('종목코드는 6자리 숫자여야 합니다')
        return v
    
    @validator('ord_no')
    def validate_ord_no(cls, v):
        if v and len(v) > 10:
            raise ValueError('주문번호는 최대 10자리여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "qry_tp": "1",
                "sell_tp": "0",
                "ord_no": "",
                "stex_tp": "0"
            }
        }


class TodayProfitLossDetailRequest(BaseModel):
    """당일실현손익상세요청 (ka10077) - 정확한 키움 스펙"""
    
    stk_cd: str = Field(..., max_length=6, description="종목코드 (String, Required, 6자리)")
    
    @validator('stk_cd')
    def validate_stk_cd(cls, v):
        if len(v) != 6 or not v.isdigit():
            raise ValueError('종목코드는 6자리 숫자여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930"
            }
        }


class AccountReturnRateRequest(BaseModel):
    """계좌수익률요청 (ka10085) - 정확한 키움 스펙"""
    
    stex_tp: str = Field(..., max_length=1, description="거래소구분 (String, Required, 0:통합, 1:KRX, 2:NXT)")
    
    @validator('stex_tp')
    def validate_stex_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('거래소구분은 0(통합), 1(KRX), 2(NXT) 중 하나여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "stex_tp": "0"
            }
        }


class UnfilledSplitOrderDetailRequest(BaseModel):
    """미체결 분할주문 상세 (ka10088)"""
    
    ord_no: str = Field(..., max_length=20, description="주문번호")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ord_no": "20241128001"
            }
        }


class DailyTradingLogRequest(BaseModel):
    """당일매매일지요청 (ka10170)"""
    
    base_dt: Optional[str] = Field(None, max_length=8, description="기준일자 YYYYMMDD(공백입력시 금일데이터,최근 2개월까지 제공)")
    ottks_tp: str = Field(..., max_length=1, description="단주구분 1:당일매수에 대한 당일매도,2:당일매도 전체")
    ch_crd_tp: str = Field(..., max_length=1, description="현금신용구분 0:전체, 1:현금매매만, 2:신용매매만")
    
    @validator('base_dt')
    def validate_base_dt(cls, v):
        if v is not None and (len(v) != 8 or not v.isdigit()):
            raise ValueError('기준일자는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
        
    @validator('ottks_tp')
    def validate_ottks_tp(cls, v):
        if v not in ['1', '2']:
            raise ValueError('단주구분은 1 또는 2만 가능합니다')
        return v
        
    @validator('ch_crd_tp') 
    def validate_ch_crd_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('현금신용구분은 0, 1, 2만 가능합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "base_dt": "20241120",
                "ottks_tp": "1",
                "ch_crd_tp": "0"
            }
        }


# ============== 계좌 현황 관련 API 모델 (kt00001~kt00018) ==============

class DepositDetailStatusRequest(BaseModel):
    """예수금상세현황요청 (kt00001)"""
    
    qry_tp: str = Field(..., max_length=1, description="조회구분 3:추정조회, 2:일반조회")
    
    @validator('qry_tp')
    def validate_qry_tp(cls, v):
        if v not in ['2', '3']:
            raise ValueError('조회구분은 2(일반조회) 또는 3(추정조회)만 가능합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "qry_tp": "3"
            }
        }


class DailyEstimatedAssetStatusRequest(BaseModel):
    """일별추정예탁자산현황요청 (kt00002)"""
    
    start_dt: str = Field(..., max_length=8, description="시작조회기간 YYYYMMDD")
    end_dt: str = Field(..., max_length=8, description="종료조회기간 YYYYMMDD")
    
    @validator('start_dt', 'end_dt')
    def validate_date_format(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('날짜는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_dt": "20241111",
                "end_dt": "20241125"
            }
        }


class EstimatedAssetInquiryRequest(BaseModel):
    """추정자산조회요청 (kt00003)"""
    
    qry_tp: str = Field(..., max_length=1, description="상장폐지조회구분 0:전체, 1:상장폐지종목제외")
    
    @validator('qry_tp')
    def validate_qry_tp(cls, v):
        if v not in ['0', '1']:
            raise ValueError('상장폐지조회구분은 0(전체) 또는 1(상장폐지종목제외)만 가능합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "qry_tp": "0"
            }
        }


class AccountEvaluationStatusRequest(BaseModel):
    """계좌평가현황요청 (kt00004)"""
    
    qry_tp: str = Field(..., pattern="^[01]$", description="상장폐지조회구분 (0:전체, 1:상장폐지종목제외)")
    dmst_stex_tp: str = Field(..., pattern="^(KRX|NXT)$", description="국내거래소구분 (KRX:한국거래소, NXT:넥스트트레이드)")
    
    @validator('qry_tp')
    def validate_qry_tp(cls, v):
        if v not in ['0', '1']:
            raise ValueError('상장폐지조회구분은 0(전체) 또는 1(상장폐지종목제외)만 가능합니다')
        return v
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        if v not in ['KRX', 'NXT']:
            raise ValueError('국내거래소구분은 KRX(한국거래소) 또는 NXT(넥스트트레이드)만 가능합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "qry_tp": "1",
                "dmst_stex_tp": "KRX"
            }
        }


class FilledBalanceRequest(BaseModel):
    """체결잔고요청 (kt00005)"""
    
    dmst_stex_tp: str = Field(..., pattern="^(KRX|NXT)$", description="국내거래소구분 (KRX:한국거래소, NXT:넥스트트레이드)")
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        if v not in ['KRX', 'NXT']:
            raise ValueError('국내거래소구분은 KRX(한국거래소) 또는 NXT(넥스트트레이드)만 가능합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "dmst_stex_tp": "KRX"
            }
        }


class AccountOrderFilledDetailRequest(BaseModel):
    """계좌별주문체결내역상세요청 (kt00007)"""
    
    ord_dt: Optional[str] = Field(None, max_length=8, description="주문일자 YYYYMMDD (선택사항)")
    qry_tp: str = Field(..., pattern="^[1-4]$", description="조회구분 (1:주문순, 2:역순, 3:미체결, 4:체결내역만)")
    stk_bond_tp: str = Field(..., pattern="^[0-2]$", description="주식채권구분 (0:전체, 1:주식, 2:채권)")
    sell_tp: str = Field(..., pattern="^[0-2]$", description="매도수구분 (0:전체, 1:매도, 2:매수)")
    stk_cd: Optional[str] = Field(None, max_length=12, description="종목코드 (선택사항, 공백일때 전체종목)")
    fr_ord_no: Optional[str] = Field(None, max_length=7, description="시작주문번호 (선택사항, 공백일때 전체주문)")
    dmst_stex_tp: str = Field(..., max_length=6, description="국내거래소구분 (%:전체, KRX:한국거래소, NXT:넥스트트레이드, SOR:최선주문집행)")
    
    @validator('ord_dt')
    def validate_ord_dt(cls, v):
        if v is not None and v != '' and (len(v) != 8 or not v.isdigit()):
            raise ValueError('주문일자는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    @validator('qry_tp')
    def validate_qry_tp(cls, v):
        if v not in ['1', '2', '3', '4']:
            raise ValueError('조회구분은 1(주문순), 2(역순), 3(미체결), 4(체결내역만) 중 하나여야 합니다')
        return v
    
    @validator('stk_bond_tp')
    def validate_stk_bond_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('주식채권구분은 0(전체), 1(주식), 2(채권) 중 하나여야 합니다')
        return v
    
    @validator('sell_tp')
    def validate_sell_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('매도수구분은 0(전체), 1(매도), 2(매수) 중 하나여야 합니다')
        return v
    
    @validator('stk_cd')
    def validate_stk_cd(cls, v):
        if v is not None and v != '' and len(v) > 12:
            raise ValueError('종목코드는 최대 12자리여야 합니다')
        return v
    
    @validator('fr_ord_no')
    def validate_fr_ord_no(cls, v):
        if v is not None and v != '' and len(v) > 7:
            raise ValueError('시작주문번호는 최대 7자리여야 합니다')
        return v
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        if v not in ['%', 'KRX', 'NXT', 'SOR']:
            raise ValueError('국내거래소구분은 %(전체), KRX(한국거래소), NXT(넥스트트레이드), SOR(최선주문집행) 중 하나여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "ord_dt": "",
                "qry_tp": "1",
                "stk_bond_tp": "0",
                "sell_tp": "0", 
                "stk_cd": "005930",
                "fr_ord_no": "",
                "dmst_stex_tp": "%"
            }
        }


class AccountNextDaySettlementRequest(BaseModel):
    """계좌별익일결제예정내역요청 (kt00008)"""
    
    strt_dcd_seq: Optional[str] = Field(None, max_length=7, description="시작결제번호 (선택사항)")
    
    @validator('strt_dcd_seq')
    def validate_strt_dcd_seq(cls, v):
        if v is not None and v != '' and len(v) > 7:
            raise ValueError('시작결제번호는 최대 7자리여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "strt_dcd_seq": ""
            }
        }


class AccountOrderFilledStatusRequest(BaseModel):
    """계좌별주문체결현황요청 (kt00009)"""
    
    ord_dt: Optional[str] = Field(None, max_length=8, description="주문일자 YYYYMMDD (선택사항)")
    stk_bond_tp: str = Field(..., pattern="^[0-2]$", description="주식채권구분 (0:전체, 1:주식, 2:채권)")
    mrkt_tp: str = Field(..., pattern="^[0-4]$", description="시장구분 (0:전체, 1:코스피, 2:코스닥, 3:OTCBB, 4:ECN)")
    sell_tp: str = Field(..., pattern="^[0-2]$", description="매도수구분 (0:전체, 1:매도, 2:매수)")
    qry_tp: str = Field(..., pattern="^[0-1]$", description="조회구분 (0:전체, 1:체결)")
    stk_cd: Optional[str] = Field(None, max_length=12, description="종목코드 (선택사항, 전문 조회할 종목코드)")
    fr_ord_no: Optional[str] = Field(None, max_length=7, description="시작주문번호 (선택사항)")
    dmst_stex_tp: str = Field(..., max_length=6, description="국내거래소구분 (%:전체, KRX:한국거래소, NXT:넥스트트레이드, SOR:최선주문집행)")
    
    @validator('ord_dt')
    def validate_ord_dt(cls, v):
        if v is not None and v != '' and (len(v) != 8 or not v.isdigit()):
            raise ValueError('주문일자는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    @validator('stk_bond_tp')
    def validate_stk_bond_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('주식채권구분은 0(전체), 1(주식), 2(채권) 중 하나여야 합니다')
        return v
    
    @validator('mrkt_tp')
    def validate_mrkt_tp(cls, v):
        if v not in ['0', '1', '2', '3', '4']:
            raise ValueError('시장구분은 0(전체), 1(코스피), 2(코스닥), 3(OTCBB), 4(ECN) 중 하나여야 합니다')
        return v
    
    @validator('sell_tp')
    def validate_sell_tp(cls, v):
        if v not in ['0', '1', '2']:
            raise ValueError('매도수구분은 0(전체), 1(매도), 2(매수) 중 하나여야 합니다')
        return v
    
    @validator('qry_tp')
    def validate_qry_tp(cls, v):
        if v not in ['0', '1']:
            raise ValueError('조회구분은 0(전체) 또는 1(체결)이어야 합니다')
        return v
    
    @validator('stk_cd')
    def validate_stk_cd(cls, v):
        if v is not None and v != '' and len(v) > 12:
            raise ValueError('종목코드는 최대 12자리여야 합니다')
        return v
    
    @validator('fr_ord_no')
    def validate_fr_ord_no(cls, v):
        if v is not None and v != '' and len(v) > 7:
            raise ValueError('시작주문번호는 최대 7자리여야 합니다')
        return v
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        if v not in ['%', 'KRX', 'NXT', 'SOR']:
            raise ValueError('국내거래소구분은 %(전체), KRX(한국거래소), NXT(넥스트트레이드), SOR(최선주문집행) 중 하나여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "ord_dt": "",
                "stk_bond_tp": "0",
                "mrkt_tp": "0",
                "sell_tp": "0",
                "qry_tp": "0",
                "stk_cd": "",
                "fr_ord_no": "",
                "dmst_stex_tp": "KRX"
            }
        }


class OrderWithdrawalAmountRequest(BaseModel):
    """주문인출가능금액요청 (kt00010)"""
    
    io_amt: Optional[str] = Field(None, max_length=12, description="입출금액 (선택사항)")
    stk_cd: str = Field(..., max_length=12, description="종목번호")
    trde_tp: str = Field(..., pattern="^[12]$", description="매매구분 (1:매도, 2:매수)")
    trde_qty: Optional[str] = Field(None, max_length=10, description="매매수량 (선택사항)")
    uv: str = Field(..., max_length=10, description="매수가격")
    exp_buy_unp: Optional[str] = Field(None, max_length=10, description="예상매수단가 (선택사항)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "io_amt": "",
                "stk_cd": "005930",
                "trde_tp": "2",
                "trde_qty": "",
                "uv": "267000",
                "exp_buy_unp": ""
            }
        }


class MarginRateOrderQuantityRequest(BaseModel):
    """증거금율별주문가능수량조회요청 (kt00011)"""
    
    stk_cd: str = Field(..., max_length=12, description="종목번호")
    uv: Optional[str] = Field(None, max_length=10, description="매수가격 (선택사항)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "uv": ""
            }
        }


class CreditMarginRateOrderQuantityRequest(BaseModel):
    """신용보증금율별주문가능수량조회요청 (kt00012)"""
    
    stk_cd: str = Field(..., max_length=12, description="종목번호")
    uv: Optional[str] = Field(None, max_length=10, description="매수가격 (선택사항)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "uv": ""
            }
        }


class MarginDetailInquiryRequest(BaseModel):
    """증거금세부내역조회요청 (kt00013)"""
    
    # 이 API는 Body 파라미터가 없습니다 (요청 본문이 비어있음)
    
    class Config:
        json_schema_extra = {
            "example": {}
        }


class TrustComprehensiveTransactionRequest(BaseModel):
    """위탁종합거래내역요청 (kt00015)"""
    
    strt_dt: str = Field(..., max_length=8, description="시작일자 (YYYYMMDD)")
    end_dt: str = Field(..., max_length=8, description="종료일자 (YYYYMMDD)") 
    tp: str = Field(..., max_length=1, description="구분 0:전체,1:입출금,2:입출고,3:매매,4:매수,5:매도,6:입금,7:출금,A:예탁담보대출입금,B:매도담보대출입금,C:현금상환,F:환전,M:입출금+환전,G:외화매수,H:외화매도,I:환전정산입금,J:환전정산출금")
    stk_cd: Optional[str] = Field("", max_length=12, description="종목코드 (선택사항)")
    crnc_cd: Optional[str] = Field("", max_length=3, description="통화코드 (선택사항)")
    gds_tp: str = Field(..., max_length=1, description="상품구분 0:전체, 1:국내주식, 2:수익증권, 3:해외주식, 4:금융상품")
    frgn_stex_code: Optional[str] = Field("", max_length=10, description="해외거래소코드 (선택사항)")
    dmst_stex_tp: str = Field(..., max_length=6, description="국내거래소구분 %:(전체),KRX:한국거래소,NXT:넥스트트레이드")
    
    @validator('strt_dt', 'end_dt')
    def validate_date_format(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('날짜는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    @validator('tp')
    def validate_tp(cls, v):
        valid_values = ['0', '1', '2', '3', '4', '5', '6', '7', 'A', 'B', 'C', 'F', 'M', 'G', 'H', 'I', 'J']
        if v not in valid_values:
            raise ValueError(f'구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    @validator('gds_tp')
    def validate_gds_tp(cls, v):
        valid_values = ['0', '1', '2', '3', '4']
        if v not in valid_values:
            raise ValueError(f'상품구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        valid_values = ['%', 'KRX', 'NXT']
        if v not in valid_values:
            raise ValueError(f'국내거래소구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "strt_dt": "20241121",
                "end_dt": "20241125", 
                "tp": "0",
                "stk_cd": "",
                "crnc_cd": "",
                "gds_tp": "0",
                "frgn_stex_code": "",
                "dmst_stex_tp": "%"
            }
        }


class DailyAccountReturnDetailRequest(BaseModel):
    """일별계좌수익률상세현황요청 (kt00016)"""
    
    fr_dt: str = Field(..., max_length=8, description="평가시작일 (YYYYMMDD)")
    to_dt: str = Field(..., max_length=8, description="평가종료일 (YYYYMMDD)")
    
    @validator('fr_dt', 'to_dt')
    def validate_date_format(cls, v):
        if len(v) != 8 or not v.isdigit():
            raise ValueError('날짜는 YYYYMMDD 형식 8자리 숫자여야 합니다')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "fr_dt": "20241111",
                "to_dt": "20241125"
            }
        }


class AccountDailyStatusRequest(BaseModel):
    """계좌별당일현황요청 (kt00017)"""
    
    # 이 API는 Body 파라미터가 없습니다 (요청 본문이 비어있음)
    
    class Config:
        json_schema_extra = {
            "example": {}
        }


class AccountEvaluationBalanceDetailRequest(BaseModel):
    """계좌평가잔고내역요청 (kt00018)"""
    
    qry_tp: str = Field(..., max_length=1, description="조회구분 1:합산, 2:개별")
    dmst_stex_tp: str = Field(..., max_length=6, description="국내거래소구분 KRX:한국거래소,NXT:넥스트트레이드")
    
    @validator('qry_tp')
    def validate_qry_tp(cls, v):
        valid_values = ['1', '2']
        if v not in valid_values:
            raise ValueError(f'조회구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        valid_values = ['KRX', 'NXT']
        if v not in valid_values:
            raise ValueError(f'국내거래소구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "qry_tp": "1",
                "dmst_stex_tp": "KRX"
            }
        }