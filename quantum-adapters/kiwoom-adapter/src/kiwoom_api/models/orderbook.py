"""키움 주식호가요청(ka10004) 응답 모델"""

from typing import Optional
from pydantic import BaseModel, Field


class OrderbookResponse(BaseModel):
    """키움 주식호가요청 응답 모델"""

    # 기준시간
    bid_req_base_tm: Optional[str] = Field(None, description="호가잔량기준시간")

    # 매도호가 1-10차 (가격)
    sel_fpr_bid: Optional[str] = Field(None, description="매도최우선호가 (매도호가1)")
    sel_2th_pre_bid: Optional[str] = Field(None, description="매도2차선호가")
    sel_3th_pre_bid: Optional[str] = Field(None, description="매도3차선호가")
    sel_4th_pre_bid: Optional[str] = Field(None, description="매도4차선호가")
    sel_5th_pre_bid: Optional[str] = Field(None, description="매도5차선호가")
    sel_6th_pre_bid: Optional[str] = Field(None, description="매도6차선호가")
    sel_7th_pre_bid: Optional[str] = Field(None, description="매도7차선호가")
    sel_8th_pre_bid: Optional[str] = Field(None, description="매도8차선호가")
    sel_9th_pre_bid: Optional[str] = Field(None, description="매도9차선호가")
    sel_10th_pre_bid: Optional[str] = Field(None, description="매도10차선호가")

    # 매도호가 1-10차 (잔량)
    sel_fpr_req: Optional[str] = Field(None, description="매도최우선잔량 (매도호가수량1)")
    sel_2th_pre_req: Optional[str] = Field(None, description="매도2차선잔량")
    sel_3th_pre_req: Optional[str] = Field(None, description="매도3차선잔량")
    sel_4th_pre_req: Optional[str] = Field(None, description="매도4차선잔량")
    sel_5th_pre_req: Optional[str] = Field(None, description="매도5차선잔량")
    sel_6th_pre_req: Optional[str] = Field(None, description="매도6차선잔량")
    sel_7th_pre_req: Optional[str] = Field(None, description="매도7차선잔량")
    sel_8th_pre_req: Optional[str] = Field(None, description="매도8차선잔량")
    sel_9th_pre_req: Optional[str] = Field(None, description="매도9차선잔량")
    sel_10th_pre_req: Optional[str] = Field(None, description="매도10차선잔량")

    # 매도호가 1-10차 (직전대비)
    sel_1th_pre_req_pre: Optional[str] = Field(None, description="매도1차선잔량대비")
    sel_2th_pre_req_pre: Optional[str] = Field(None, description="매도2차선잔량대비")
    sel_3th_pre_req_pre: Optional[str] = Field(None, description="매도3차선잔량대비")
    sel_4th_pre_req_pre: Optional[str] = Field(None, description="매도4차선잔량대비")
    sel_5th_pre_req_pre: Optional[str] = Field(None, description="매도5차선잔량대비")
    sel_6th_pre_req_pre: Optional[str] = Field(None, description="매도6차선잔량대비")
    sel_7th_pre_req_pre: Optional[str] = Field(None, description="매도7차선잔량대비")
    sel_8th_pre_req_pre: Optional[str] = Field(None, description="매도8차선잔량대비")
    sel_9th_pre_req_pre: Optional[str] = Field(None, description="매도9차선잔량대비")
    sel_10th_pre_req_pre: Optional[str] = Field(None, description="매도10차선잔량대비")

    # 매수호가 1-10차 (가격)
    buy_fpr_bid: Optional[str] = Field(None, description="매수최우선호가 (매수호가1)")
    buy_2th_pre_bid: Optional[str] = Field(None, description="매수2차선호가")
    buy_3th_pre_bid: Optional[str] = Field(None, description="매수3차선호가")
    buy_4th_pre_bid: Optional[str] = Field(None, description="매수4차선호가")
    buy_5th_pre_bid: Optional[str] = Field(None, description="매수5차선호가")
    buy_6th_pre_bid: Optional[str] = Field(None, description="매수6차선호가")
    buy_7th_pre_bid: Optional[str] = Field(None, description="매수7차선호가")
    buy_8th_pre_bid: Optional[str] = Field(None, description="매수8차선호가")
    buy_9th_pre_bid: Optional[str] = Field(None, description="매수9차선호가")
    buy_10th_pre_bid: Optional[str] = Field(None, description="매수10차선호가")

    # 매수호가 1-10차 (잔량)
    buy_fpr_req: Optional[str] = Field(None, description="매수최우선잔량 (매수호가수량1)")
    buy_2th_pre_req: Optional[str] = Field(None, description="매수2차선잔량")
    buy_3th_pre_req: Optional[str] = Field(None, description="매수3차선잔량")
    buy_4th_pre_req: Optional[str] = Field(None, description="매수4차선잔량")
    buy_5th_pre_req: Optional[str] = Field(None, description="매수5차선잔량")
    buy_6th_pre_req: Optional[str] = Field(None, description="매수6차선잔량")
    buy_7th_pre_req: Optional[str] = Field(None, description="매수7차선잔량")
    buy_8th_pre_req: Optional[str] = Field(None, description="매수8차선잔량")
    buy_9th_pre_req: Optional[str] = Field(None, description="매수9차선잔량")
    buy_10th_pre_req: Optional[str] = Field(None, description="매수10차선잔량")

    # 매수호가 1-10차 (직전대비)
    buy_1th_pre_req_pre: Optional[str] = Field(None, description="매수1차선잔량대비")
    buy_2th_pre_req_pre: Optional[str] = Field(None, description="매수2차선잔량대비")
    buy_3th_pre_req_pre: Optional[str] = Field(None, description="매수3차선잔량대비")
    buy_4th_pre_req_pre: Optional[str] = Field(None, description="매수4차선잔량대비")
    buy_5th_pre_req_pre: Optional[str] = Field(None, description="매수5차선잔량대비")
    buy_6th_pre_req_pre: Optional[str] = Field(None, description="매수6차선잔량대비")
    buy_7th_pre_req_pre: Optional[str] = Field(None, description="매수7차선잔량대비")
    buy_8th_pre_req_pre: Optional[str] = Field(None, description="매수8차선잔량대비")
    buy_9th_pre_req_pre: Optional[str] = Field(None, description="매수9차선잔량대비")
    buy_10th_pre_req_pre: Optional[str] = Field(None, description="매수10차선잔량대비")

    # 총 잔량 정보
    tot_sel_req: Optional[str] = Field(None, description="총매도잔량 (매도호가총잔량)")
    tot_sel_req_jub_pre: Optional[str] = Field(None, description="총매도잔량직전대비")
    tot_buy_req: Optional[str] = Field(None, description="총매수잔량 (매수호가총잔량)")
    tot_buy_req_jub_pre: Optional[str] = Field(None, description="총매수잔량직전대비")

    # 시간외 잔량 정보
    ovt_sel_req: Optional[str] = Field(None, description="시간외매도잔량")
    ovt_sel_req_pre: Optional[str] = Field(None, description="시간외매도잔량대비")
    ovt_buy_req: Optional[str] = Field(None, description="시간외매수잔량")
    ovt_buy_req_pre: Optional[str] = Field(None, description="시간외매수잔량대비")

    class Config:
        json_schema_extra = {
            "example": {
                "bid_req_base_tm": "093000",
                "sel_fpr_bid": "{매도최우선호가}",
                "sel_fpr_req": "{매도최우선잔량}",
                "buy_fpr_bid": "{매수최우선호가}",
                "buy_fpr_req": "{매수최우선잔량}",
                "tot_sel_req": "{총매도잔량}",
                "tot_buy_req": "{총매수잔량}"
            }
        }


class OrderbookData(BaseModel):
    """호가 데이터 (구조화된 형태)"""

    timestamp: str = Field(description="호가 기준시간")
    
    # 매도호가 리스트 (1-10호가)
    ask_prices: list[str] = Field(description="매도호가 리스트 (1-10)")
    ask_volumes: list[str] = Field(description="매도잔량 리스트 (1-10)")
    ask_changes: list[str] = Field(description="매도잔량대비 리스트 (1-10)")
    
    # 매수호가 리스트 (1-10호가)
    bid_prices: list[str] = Field(description="매수호가 리스트 (1-10)")
    bid_volumes: list[str] = Field(description="매수잔량 리스트 (1-10)")
    bid_changes: list[str] = Field(description="매수잔량대비 리스트 (1-10)")
    
    # 총 잔량
    total_ask_volume: str = Field(description="총매도잔량")
    total_bid_volume: str = Field(description="총매수잔량")
    total_ask_change: str = Field(description="총매도잔량대비")
    total_bid_change: str = Field(description="총매수잔량대비")
    
    # 시간외 잔량
    after_hours_ask_volume: str = Field(description="시간외매도잔량")
    after_hours_bid_volume: str = Field(description="시간외매수잔량")


class OrderbookApiResponse(BaseModel):
    """키움 주식호가요청 API 응답"""
    
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    
    # 원본 데이터
    raw_data: OrderbookResponse = Field(description="키움 원본 응답 데이터")
    
    # 구조화된 데이터
    orderbook_data: OrderbookData = Field(description="구조화된 호가 데이터")
    
    # 메타 정보
    request_time: str = Field(description="요청 시간")
    response_time: str = Field(description="응답 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "{종목코드}",
                "stock_name": "{종목명}",
                "raw_data": {
                    "sel_fpr_bid": "{매도최우선호가}",
                    "sel_fpr_req": "{매도최우선잔량}",
                    "buy_fpr_bid": "{매수최우선호가}",
                    "buy_fpr_req": "{매수최우선잔량}"
                },
                "orderbook_data": {
                    "timestamp": "093000",
                    "ask_prices": ["{매도호가1}", "{매도호가2}", "{매도호가3}"],
                    "ask_volumes": ["{매도잔량1}", "{매도잔량2}", "{매도잔량3}"],
                    "bid_prices": ["{매수호가1}", "{매수호가2}", "{매수호가3}"],
                    "bid_volumes": ["{매수잔량1}", "{매수잔량2}", "{매수잔량3}"]
                }
            }
        }