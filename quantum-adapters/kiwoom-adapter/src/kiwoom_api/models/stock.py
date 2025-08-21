"""
종목정보 관련 데이터 모델 (ka10001, ka10099 API)
키움 API 스펙에 완전히 맞춰진 최소한의 모델
"""
from typing import Optional
from pydantic import BaseModel, Field


class StockInfoRequest(BaseModel):
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