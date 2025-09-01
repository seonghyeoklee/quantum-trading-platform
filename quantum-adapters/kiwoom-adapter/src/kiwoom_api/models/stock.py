"""
종목정보 관련 데이터 모델 (ka10001, ka10099 API)
주식 거래주문 관련 데이터 모델 (kt10000~kt10003 API)
키움 API 스펙에 완전히 맞춰진 최소한의 모델
Java 인증 정보 전달 지원
"""
from typing import Optional
from pydantic import BaseModel, Field, validator


class BaseKiwoomRequest(BaseModel):
    """키움 API 요청 기본 모델 (Java 인증 정보 전달 지원)"""
    
    # Java에서 전달되는 키움 인증 정보 (선택적)
    kiwoom_access_token: Optional[str] = Field(None, description="Java에서 전달된 키움 액세스 토큰")
    kiwoom_app_key: Optional[str] = Field(None, description="Java에서 전달된 키움 API 키")
    kiwoom_app_secret: Optional[str] = Field(None, description="Java에서 전달된 키움 API 시크릿")
    kiwoom_base_url: Optional[str] = Field(None, description="Java에서 전달된 키움 베이스 URL")
    dry_run: Optional[bool] = Field(None, description="모드 지정 (true: 모의투자, false: 실전투자)")


class StockInfoRequest(BaseKiwoomRequest):
    """종목 기본정보 요청 모델 (ka10001)"""
    
    stk_cd: str = Field(..., max_length=20, description="종목코드 (거래소별 종목코드)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930"  # 삼성전자
            }
        }


class StockListRequest(BaseModel):
    """종목정보 리스트 요청 모델 (ka10099)"""
    
    mrkt_tp: str = Field(..., max_length=2, description="시장구분 (0:코스피,10:코스닥,3:ELW,8:ETF,30:K-OTC,50:코넥스,5:신주인수권,4:뮤추얼펀드,6:리츠,9:하이일드)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mrkt_tp": "0"  # 코스피
            }
        }


class IndustryCodeRequest(BaseModel):
    """업종코드 리스트 요청 모델 (ka10101)"""
    
    mrkt_tp: str = Field(..., max_length=1, description="시장구분 (0:코스피(거래소),1:코스닥,2:KOSPI200,4:KOSPI100,7:KRX100(통합지수))")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mrkt_tp": "0"  # 코스피(거래소)
            }
        }


class WatchlistRequest(BaseModel):
    """관심종목정보 요청 모델 (ka10095)"""
    
    stk_cd: str = Field(..., max_length=200, description="종목코드 (거래소별 종목코드, 여러 종목시 | 로 구분)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930|000660|035420"  # 삼성전자|SK하이닉스|NAVER
            }
        }


class ProgramTradeRequest(BaseModel):
    """프로그램순매수상위50 요청 모델 (ka90003)"""
    
    trde_upper_tp: str = Field(..., max_length=1, description="매매상위구분 (1:순매도상위, 2:순매수상위)")
    amt_qty_tp: str = Field(..., max_length=2, description="금액수량구분 (1:금액, 2:수량)")
    mrkt_tp: str = Field(..., max_length=10, description="시장구분 (P00101:코스피, P10102:코스닥)")
    stex_tp: str = Field(..., max_length=1, description="거래소구분 (1:KRX, 2:NXT, 3:통합)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trde_upper_tp": "2",  # 순매수상위
                "amt_qty_tp": "1",     # 금액
                "mrkt_tp": "P00101",   # 코스피
                "stex_tp": "1"         # KRX
            }
        }


# ============== 주식 거래주문 관련 API 모델 ==============

class StockBuyOrderRequest(BaseKiwoomRequest):
    """주식 매수주문 요청 모델 (kt10000)"""
    
    dmst_stex_tp: str = Field(..., max_length=3, description="국내거래소구분 (KRX, NXT, SOR)")
    stk_cd: str = Field(..., max_length=12, description="종목코드")
    ord_qty: str = Field(..., max_length=12, description="주문수량")
    ord_uv: Optional[str] = Field("", max_length=12, description="주문단가 (시장가일 때는 공백)")
    trde_tp: str = Field(..., max_length=2, description="매매구분")
    cond_uv: Optional[str] = Field("", max_length=12, description="조건단가")
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        valid_values = ['KRX', 'NXT', 'SOR']
        if v not in valid_values:
            raise ValueError(f'국내거래소구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    @validator('trde_tp')
    def validate_trde_tp(cls, v):
        valid_values = ['0', '3', '5', '81', '61', '62', '6', '7', '10', '13', '16', '20', '23', '26', '28', '29', '30', '31']
        if v not in valid_values:
            raise ValueError(f'매매구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "dmst_stex_tp": "KRX",
                "stk_cd": "005930", 
                "ord_qty": "1",
                "ord_uv": "",  # 시장가일 때 공백
                "trde_tp": "3",  # 시장가
                "cond_uv": ""
            }
        }


class StockSellOrderRequest(BaseKiwoomRequest):
    """주식 매도주문 요청 모델 (kt10001)"""
    
    dmst_stex_tp: str = Field(..., max_length=3, description="국내거래소구분 (KRX, NXT, SOR)")
    stk_cd: str = Field(..., max_length=12, description="종목코드")
    ord_qty: str = Field(..., max_length=12, description="주문수량")
    ord_uv: Optional[str] = Field("", max_length=12, description="주문단가 (시장가일 때는 공백)")
    trde_tp: str = Field(..., max_length=2, description="매매구분")
    cond_uv: Optional[str] = Field("", max_length=12, description="조건단가")
    
    @validator('dmst_stex_tp')
    def validate_dmst_stex_tp(cls, v):
        valid_values = ['KRX', 'NXT', 'SOR']
        if v not in valid_values:
            raise ValueError(f'국내거래소구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    @validator('trde_tp')
    def validate_trde_tp(cls, v):
        valid_values = ['0', '3', '5', '81', '61', '62', '6', '7', '10', '13', '16', '20', '23', '26', '28', '29', '30', '31']
        if v not in valid_values:
            raise ValueError(f'매매구분은 다음 값 중 하나여야 합니다: {", ".join(valid_values)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "dmst_stex_tp": "KRX",
                "stk_cd": "005930", 
                "ord_qty": "1",
                "ord_uv": "",  # 시장가일 때 공백
                "trde_tp": "3",  # 시장가
                "cond_uv": ""
            }
        }


class StockModifyOrderRequest(BaseModel):
    """주식 정정주문 요청 모델 (kt10002)"""
    
    dmst_stex_tp: str = Field(..., max_length=3, description="국내거래소구분 (KRX, NXT, SOR)")
    orig_ord_no: str = Field(..., max_length=7, description="원주문번호")
    stk_cd: str = Field(..., max_length=12, description="종목코드")
    mdfy_qty: str = Field(..., max_length=12, description="정정수량")
    mdfy_uv: str = Field(..., max_length=12, description="정정단가")
    mdfy_cond_uv: Optional[str] = Field("", max_length=12, description="정정조건단가")
    
    @validator("dmst_stex_tp")
    def validate_dmst_stex_tp(cls, v):
        valid_values = ["KRX", "NXT", "SOR"]
        if v not in valid_values:
            raise ValueError(f"국내거래소구분은 다음 값 중 하나여야 합니다: {', '.join(valid_values)}")
        return v
    
    @validator("orig_ord_no")
    def validate_orig_ord_no(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("원주문번호는 필수입니다")
        return v
    
    @validator("mdfy_qty")
    def validate_mdfy_qty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("정정수량은 필수입니다")
        return v
        
    @validator("mdfy_uv")
    def validate_mdfy_uv(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("정정단가는 필수입니다")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "dmst_stex_tp": "KRX",
                "orig_ord_no": "0000139",  # 원주문번호
                "stk_cd": "005930",
                "mdfy_qty": "1",           # 정정수량  
                "mdfy_uv": "199700",       # 정정단가
                "mdfy_cond_uv": ""         # 정정조건단가
            }
        }




class StockCancelOrderRequest(BaseModel):
    """주식 취소주문 요청 모델 (kt10003)"""
    
    dmst_stex_tp: str = Field(..., max_length=3, description="국내거래소구분 (KRX, NXT, SOR)")
    orig_ord_no: str = Field(..., max_length=7, description="원주문번호")
    stk_cd: str = Field(..., max_length=12, description="종목코드")
    cncl_qty: str = Field(..., max_length=12, description="취소수량 (0 입력시 잔량 전부 취소)")
    
    @validator("dmst_stex_tp")
    def validate_dmst_stex_tp(cls, v):
        valid_values = ["KRX", "NXT", "SOR"]
        if v not in valid_values:
            raise ValueError(f"국내거래소구분은 다음 값 중 하나여야 합니다: {', '.join(valid_values)}")
        return v
    
    @validator("orig_ord_no")
    def validate_orig_ord_no(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("원주문번호는 필수입니다")
        return v
    
    @validator("cncl_qty")
    def validate_cncl_qty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("취소수량은 필수입니다")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "dmst_stex_tp": "KRX",
                "orig_ord_no": "0000140",  # 원주문번호
                "stk_cd": "005930",
                "cncl_qty": "1"            # 취소수량 (0=잔량전부취소)
            }
        }

