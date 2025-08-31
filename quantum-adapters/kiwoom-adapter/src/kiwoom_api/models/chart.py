"""키움 주식시장정보 및 차트요청 응답 모델"""

from typing import Optional, List
from pydantic import BaseModel, Field


class StockChartData(BaseModel):
    """주식 차트 데이터 (단일 항목)"""
    
    date: Optional[str] = Field(None, description="날짜")
    open_pric: Optional[str] = Field(None, description="시가")
    high_pric: Optional[str] = Field(None, description="고가")
    low_pric: Optional[str] = Field(None, description="저가")
    close_pric: Optional[str] = Field(None, description="종가")
    pre: Optional[str] = Field(None, description="대비")
    flu_rt: Optional[str] = Field(None, description="등락률")
    trde_qty: Optional[str] = Field(None, description="거래량")
    trde_prica: Optional[str] = Field(None, description="거래대금")
    for_poss: Optional[str] = Field(None, description="외인보유")
    for_wght: Optional[str] = Field(None, description="외인비중")
    for_netprps: Optional[str] = Field(None, description="외인순매수")
    orgn_netprps: Optional[str] = Field(None, description="기관순매수")
    ind_netprps: Optional[str] = Field(None, description="개인순매수")
    crd_remn_rt: Optional[str] = Field(None, description="신용잔고율")
    frgn: Optional[str] = Field(None, description="외국계")
    prm: Optional[str] = Field(None, description="프로그램")


class ChartResponse(BaseModel):
    """키움 주식일주월시분요청 응답 모델"""
    
    stk_ddwkmm: Optional[List[StockChartData]] = Field(None, description="주식일주월시분 데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_ddwkmm": [
                    {
                        "date": "{날짜}",
                        "open_pric": "{시가}",
                        "high_pric": "{고가}",
                        "low_pric": "{저가}",
                        "close_pric": "{종가}",
                        "pre": "{대비}",
                        "flu_rt": "{등락률}",
                        "trde_qty": "{거래량}",
                        "trde_prica": "{거래대금}",
                        "for_poss": "{외인보유}",
                        "for_wght": "{외인비중}",
                        "for_netprps": "{외인순매수}",
                        "orgn_netprps": "{기관순매수}",
                        "ind_netprps": "{개인순매수}",
                        "crd_remn_rt": "{신용잔고율}",
                        "frgn": "{외국계}",
                        "prm": "{프로그램}"
                    }
                ]
            }
        }


class StructuredChartData(BaseModel):
    """구조화된 차트 데이터"""
    
    timestamp: str = Field(description="데이터 날짜/시간")
    ohlcv: dict = Field(description="OHLCV 데이터")
    trading_info: dict = Field(description="거래 정보")
    institutional_data: dict = Field(description="기관/외인 데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "{날짜시간}",
                "ohlcv": {
                    "open": "{시가}",
                    "high": "{고가}", 
                    "low": "{저가}",
                    "close": "{종가}",
                    "volume": "{거래량}",
                    "change": "{대비}",
                    "change_rate": "{등락률}"
                },
                "trading_info": {
                    "volume": "{거래량}",
                    "value": "{거래대금}",
                    "credit_balance_rate": "{신용잔고율}"
                },
                "institutional_data": {
                    "foreign_holding": "{외인보유}",
                    "foreign_weight": "{외인비중}",
                    "foreign_net": "{외인순매수}",
                    "institution_net": "{기관순매수}",
                    "individual_net": "{개인순매수}",
                    "foreign_system": "{외국계}",
                    "program": "{프로그램}"
                }
            }
        }


class ChartApiResponse(BaseModel):
    """키움 주식일주월시분요청 API 응답"""
    
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    
    # 원본 데이터
    raw_data: ChartResponse = Field(description="키움 원본 응답 데이터")
    
    # 구조화된 데이터
    chart_data: List[StructuredChartData] = Field(description="구조화된 차트 데이터")
    
    # 메타 정보
    data_count: int = Field(description="데이터 개수")
    request_time: str = Field(description="요청 시간")
    response_time: str = Field(description="응답 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "{종목코드}",
                "stock_name": "{종목명}",
                "raw_data": {
                    "stk_ddwkmm": []
                },
                "chart_data": [],
                "data_count": 0,
                "request_time": "{요청시간}",
                "response_time": "{응답시간}"
            }
        }


class MinuteChartData(BaseModel):
    """주식 시분 데이터 (단일 항목)"""
    
    date: Optional[str] = Field(None, description="날짜")
    open_pric: Optional[str] = Field(None, description="시가")
    high_pric: Optional[str] = Field(None, description="고가")
    low_pric: Optional[str] = Field(None, description="저가")
    close_pric: Optional[str] = Field(None, description="종가")
    pre: Optional[str] = Field(None, description="대비")
    flu_rt: Optional[str] = Field(None, description="등락률")
    trde_qty: Optional[str] = Field(None, description="거래량")
    trde_prica: Optional[str] = Field(None, description="거래대금")
    cntr_str: Optional[str] = Field(None, description="체결강도")


class MinuteChartResponse(BaseModel):
    """키움 주식시분요청 응답 모델"""
    
    minute_data: Optional[List[MinuteChartData]] = Field(None, description="주식시분 데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "minute_data": [
                    {
                        "date": "{날짜시간}",
                        "open_pric": "{시가}",
                        "high_pric": "{고가}",
                        "low_pric": "{저가}",
                        "close_pric": "{종가}",
                        "pre": "{대비}",
                        "flu_rt": "{등락률}",
                        "trde_qty": "{거래량}",
                        "trde_prica": "{거래대금}",
                        "cntr_str": "{체결강도}"
                    }
                ]
            }
        }


class StructuredMinuteData(BaseModel):
    """구조화된 시분 데이터"""
    
    timestamp: str = Field(description="시간")
    price_data: dict = Field(description="가격 데이터")
    volume_data: dict = Field(description="거래량/거래대금 데이터")
    strength: str = Field(description="체결강도")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "{날짜시간}",
                "price_data": {
                    "open": "{시가}",
                    "high": "{고가}",
                    "low": "{저가}", 
                    "close": "{종가}",
                    "change": "{대비}",
                    "change_rate": "{등락률}"
                },
                "volume_data": {
                    "volume": "{거래량}",
                    "value": "{거래대금}"
                },
                "strength": "{체결강도}"
            }
        }


class MinuteChartApiResponse(BaseModel):
    """키움 주식시분요청 API 응답"""
    
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    
    # 원본 데이터
    raw_data: MinuteChartResponse = Field(description="키움 원본 응답 데이터")
    
    # 구조화된 데이터
    minute_data: List[StructuredMinuteData] = Field(description="구조화된 시분 데이터")
    
    # 메타 정보
    data_count: int = Field(description="데이터 개수")
    request_time: str = Field(description="요청 시간")
    response_time: str = Field(description="응답 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "{종목코드}",
                "stock_name": "{종목명}",
                "raw_data": {
                    "minute_data": []
                },
                "minute_data": [],
                "data_count": 0,
                "request_time": "{요청시간}",
                "response_time": "{응답시간}"
            }
        }


class MarketInfoData(BaseModel):
    """시세표성정보 데이터 (단일 항목)"""
    
    date: Optional[str] = Field(None, description="날짜")
    time: Optional[str] = Field(None, description="시간")
    open_pric: Optional[str] = Field(None, description="시가")
    high_pric: Optional[str] = Field(None, description="고가")
    low_pric: Optional[str] = Field(None, description="저가")
    close_pric: Optional[str] = Field(None, description="종가")
    pre: Optional[str] = Field(None, description="대비")
    flu_rt: Optional[str] = Field(None, description="등락률")
    trde_qty: Optional[str] = Field(None, description="거래량")
    trde_prica: Optional[str] = Field(None, description="거래대금")
    
    # 호가 정보 (매도 1-10호가)
    sale_pric1: Optional[str] = Field(None, description="매도1호가")
    sale_qty1: Optional[str] = Field(None, description="매도1잔량")
    sale_pric2: Optional[str] = Field(None, description="매도2호가")
    sale_qty2: Optional[str] = Field(None, description="매도2잔량")
    sale_pric3: Optional[str] = Field(None, description="매도3호가")
    sale_qty3: Optional[str] = Field(None, description="매도3잔량")
    sale_pric4: Optional[str] = Field(None, description="매도4호가")
    sale_qty4: Optional[str] = Field(None, description="매도4잔량")
    sale_pric5: Optional[str] = Field(None, description="매도5호가")
    sale_qty5: Optional[str] = Field(None, description="매도5잔량")
    sale_pric6: Optional[str] = Field(None, description="매도6호가")
    sale_qty6: Optional[str] = Field(None, description="매도6잔량")
    sale_pric7: Optional[str] = Field(None, description="매도7호가")
    sale_qty7: Optional[str] = Field(None, description="매도7잔량")
    sale_pric8: Optional[str] = Field(None, description="매도8호가")
    sale_qty8: Optional[str] = Field(None, description="매도8잔량")
    sale_pric9: Optional[str] = Field(None, description="매도9호가")
    sale_qty9: Optional[str] = Field(None, description="매도9잔량")
    sale_pric10: Optional[str] = Field(None, description="매도10호가")
    sale_qty10: Optional[str] = Field(None, description="매도10잔량")
    
    # 호가 정보 (매수 1-10호가)
    buy_pric1: Optional[str] = Field(None, description="매수1호가")
    buy_qty1: Optional[str] = Field(None, description="매수1잔량")
    buy_pric2: Optional[str] = Field(None, description="매수2호가")
    buy_qty2: Optional[str] = Field(None, description="매수2잔량")
    buy_pric3: Optional[str] = Field(None, description="매수3호가")
    buy_qty3: Optional[str] = Field(None, description="매수3잔량")
    buy_pric4: Optional[str] = Field(None, description="매수4호가")
    buy_qty4: Optional[str] = Field(None, description="매수4잔량")
    buy_pric5: Optional[str] = Field(None, description="매수5호가")
    buy_qty5: Optional[str] = Field(None, description="매수5잔량")
    buy_pric6: Optional[str] = Field(None, description="매수6호가")
    buy_qty6: Optional[str] = Field(None, description="매수6잔량")
    buy_pric7: Optional[str] = Field(None, description="매수7호가")
    buy_qty7: Optional[str] = Field(None, description="매수7잔량")
    buy_pric8: Optional[str] = Field(None, description="매수8호가")
    buy_qty8: Optional[str] = Field(None, description="매수8잔량")
    buy_pric9: Optional[str] = Field(None, description="매수9호가")
    buy_qty9: Optional[str] = Field(None, description="매수9잔량")
    buy_pric10: Optional[str] = Field(None, description="매수10호가")
    buy_qty10: Optional[str] = Field(None, description="매수10잔량")
    
    # LP 정보
    lp_sale_pric1: Optional[str] = Field(None, description="LP매도1호가")
    lp_sale_qty1: Optional[str] = Field(None, description="LP매도1잔량")
    lp_sale_pric2: Optional[str] = Field(None, description="LP매도2호가")
    lp_sale_qty2: Optional[str] = Field(None, description="LP매도2잔량")
    lp_sale_pric3: Optional[str] = Field(None, description="LP매도3호가")
    lp_sale_qty3: Optional[str] = Field(None, description="LP매도3잔량")
    lp_sale_pric4: Optional[str] = Field(None, description="LP매도4호가")
    lp_sale_qty4: Optional[str] = Field(None, description="LP매도4잔량")
    lp_sale_pric5: Optional[str] = Field(None, description="LP매도5호가")
    lp_sale_qty5: Optional[str] = Field(None, description="LP매도5잔량")
    
    lp_buy_pric1: Optional[str] = Field(None, description="LP매수1호가")
    lp_buy_qty1: Optional[str] = Field(None, description="LP매수1잔량")
    lp_buy_pric2: Optional[str] = Field(None, description="LP매수2호가")
    lp_buy_qty2: Optional[str] = Field(None, description="LP매수2잔량")
    lp_buy_pric3: Optional[str] = Field(None, description="LP매수3호가")
    lp_buy_qty3: Optional[str] = Field(None, description="LP매수3잔량")
    lp_buy_pric4: Optional[str] = Field(None, description="LP매수4호가")
    lp_buy_qty4: Optional[str] = Field(None, description="LP매수4잔량")
    lp_buy_pric5: Optional[str] = Field(None, description="LP매수5호가")
    lp_buy_qty5: Optional[str] = Field(None, description="LP매수5잔량")
    
    # 기타 시세 정보
    mrkt_cap: Optional[str] = Field(None, description="시가총액")
    for_rate: Optional[str] = Field(None, description="외국인비율")
    ssts_rt: Optional[str] = Field(None, description="공매도비율")
    cntr_str: Optional[str] = Field(None, description="체결강도")


class MarketInfoResponse(BaseModel):
    """키움 시세표성정보요청 응답 모델"""
    
    market_info: Optional[MarketInfoData] = Field(None, description="시세표성정보 데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "market_info": {
                    "date": "{날짜}",
                    "time": "{시간}",
                    "open_pric": "{시가}",
                    "high_pric": "{고가}",
                    "low_pric": "{저가}",
                    "close_pric": "{종가}",
                    "pre": "{대비}",
                    "flu_rt": "{등락률}",
                    "trde_qty": "{거래량}",
                    "trde_prica": "{거래대금}",
                    "sale_pric1": "{매도1호가}",
                    "sale_qty1": "{매도1잔량}",
                    "buy_pric1": "{매수1호가}",
                    "buy_qty1": "{매수1잔량}"
                }
            }
        }


class StructuredMarketInfo(BaseModel):
    """구조화된 시세표성정보 데이터"""
    
    timestamp: str = Field(description="데이터 날짜/시간")
    basic_info: dict = Field(description="기본 시세 정보 (OHLCV)")
    orderbook: dict = Field(description="호가 정보")
    lp_info: dict = Field(description="LP 정보")
    market_data: dict = Field(description="시장 데이터 (시총, 외국인비율 등)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "{날짜시간}",
                "basic_info": {
                    "open": "{시가}",
                    "high": "{고가}",
                    "low": "{저가}",
                    "close": "{종가}",
                    "change": "{대비}",
                    "change_rate": "{등락률}",
                    "volume": "{거래량}",
                    "value": "{거래대금}"
                },
                "orderbook": {
                    "ask": [
                        {"price": "{매도1호가}", "quantity": "{매도1잔량}"},
                        {"price": "{매도2호가}", "quantity": "{매도2잔량}"}
                    ],
                    "bid": [
                        {"price": "{매수1호가}", "quantity": "{매수1잔량}"},
                        {"price": "{매수2호가}", "quantity": "{매수2잔량}"}
                    ]
                },
                "lp_info": {
                    "lp_ask": [{"price": "{LP매도호가}", "quantity": "{LP매도잔량}"}],
                    "lp_bid": [{"price": "{LP매수호가}", "quantity": "{LP매수잔량}"}]
                },
                "market_data": {
                    "market_cap": "{시가총액}",
                    "foreign_rate": "{외국인비율}",
                    "short_selling_rate": "{공매도비율}",
                    "strength": "{체결강도}"
                }
            }
        }


class MarketInfoApiResponse(BaseModel):
    """키움 시세표성정보요청 API 응답"""
    
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    
    # 원본 데이터
    raw_data: MarketInfoResponse = Field(description="키움 원본 응답 데이터")
    
    # 구조화된 데이터
    market_info: StructuredMarketInfo = Field(description="구조화된 시세표성정보")
    
    # 메타 정보
    request_time: str = Field(description="요청 시간")
    response_time: str = Field(description="응답 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "{종목코드}",
                "stock_name": "{종목명}",
                "raw_data": {
                    "market_info": {}
                },
                "market_info": {
                    "timestamp": "20241225153000",
                    "basic_info": {},
                    "orderbook": {},
                    "lp_info": {},
                    "market_data": {}
                },
                "request_time": "{요청시간}",
                "response_time": "{응답시간}"
            }
        }


class NewStockRightsData(BaseModel):
    """신주인수권 시세 데이터 (단일 종목)"""
    
    stk_cd: Optional[str] = Field(None, description="종목코드")
    stk_nm: Optional[str] = Field(None, description="종목명")
    cur_prc: Optional[str] = Field(None, description="현재가")
    pred_pre_sig: Optional[str] = Field(None, description="전일대비기호")
    pred_pre: Optional[str] = Field(None, description="전일대비")
    flu_rt: Optional[str] = Field(None, description="등락율")
    fpr_sel_bid: Optional[str] = Field(None, description="최우선매도호가")
    fpr_buy_bid: Optional[str] = Field(None, description="최우선매수호가")
    acc_trde_qty: Optional[str] = Field(None, description="누적거래량")
    open_pric: Optional[str] = Field(None, description="시가")
    high_pric: Optional[str] = Field(None, description="고가")
    low_pric: Optional[str] = Field(None, description="저가")


class NewStockRightsResponse(BaseModel):
    """키움 신주인수권전체시세요청 응답 모델"""
    
    newstk_recvrht_mrpr: Optional[List[NewStockRightsData]] = Field(None, description="신주인수권시세 리스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "newstk_recvrht_mrpr": [
                    {
                        "stk_cd": "{종목코드}",
                        "stk_nm": "{종목명}",
                        "cur_prc": "{현재가}",
                        "pred_pre_sig": "{대비부호}",
                        "pred_pre": "{전일대비}",
                        "flu_rt": "{등락률}",
                        "fpr_sel_bid": "{최우선매도호가}",
                        "fpr_buy_bid": "{최우선매수호가}",
                        "acc_trde_qty": "{누적거래량}",
                        "open_pric": "{시가}",
                        "high_pric": "{고가}",
                        "low_pric": "{저가}"
                    }
                ]
            }
        }


class StructuredNewStockRightsData(BaseModel):
    """구조화된 신주인수권 시세 데이터"""
    
    code: str = Field(description="종목코드")
    name: str = Field(description="종목명")
    price_info: dict = Field(description="가격 정보 (현재가, OHLC, 대비, 등락율)")
    bid_info: dict = Field(description="호가 정보 (최우선매도/매수호가)")
    volume_info: dict = Field(description="거래량 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "{종목코드}",
                "name": "{종목명}",
                "price_info": {
                    "current": "{현재가}",
                    "open": "{시가}",
                    "high": "{고가}",
                    "low": "{저가}",
                    "change": "{전일대비}",
                    "change_rate": "{등락률}",
                    "change_sign": "{대비부호}"
                },
                "bid_info": {
                    "best_ask": "{최우선매도호가}",
                    "best_bid": "{최우선매수호가}"
                },
                "volume_info": {
                    "volume": "{누적거래량}"
                }
            }
        }


class NewStockRightsApiResponse(BaseModel):
    """키움 신주인수권전체시세요청 API 응답"""
    
    rights_type: str = Field(description="신주인수권구분")
    rights_type_name: str = Field(description="신주인수권구분명")
    
    # 원본 데이터
    raw_data: NewStockRightsResponse = Field(description="키움 원본 응답 데이터")
    
    # 구조화된 데이터
    rights_data: List[StructuredNewStockRightsData] = Field(description="구조화된 신주인수권 시세 데이터")
    
    # 메타 정보
    data_count: int = Field(description="데이터 개수")
    request_time: str = Field(description="요청 시간")
    response_time: str = Field(description="응답 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "rights_type": "00",
                "rights_type_name": "전체",
                "raw_data": {
                    "newstk_recvrht_mrpr": []
                },
                "rights_data": [],
                "data_count": 0,
                "request_time": "{요청시간}",
                "response_time": "{응답시간}"
            }
        }


class DailyInstitutionalTradeData(BaseModel):
    """일별기관매매종목 데이터 (단일 종목)"""
    
    stk_cd: Optional[str] = Field(None, description="종목코드")
    stk_nm: Optional[str] = Field(None, description="종목명")
    netprps_qty: Optional[str] = Field(None, description="순매수수량")
    netprps_amt: Optional[str] = Field(None, description="순매수금액")


class DailyInstitutionalTradeResponse(BaseModel):
    """키움 일별기관매매종목요청 응답 모델"""
    
    daly_orgn_trde_stk: Optional[List[DailyInstitutionalTradeData]] = Field(None, description="일별기관매매종목 리스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "daly_orgn_trde_stk": [
                    {
                        "stk_cd": "{종목코드}",
                        "stk_nm": "{종목명}",
                        "netprps_qty": "{순매수수량}",
                        "netprps_amt": "{순매수금액}"
                    }
                ]
            }
        }


class StructuredDailyInstitutionalTradeData(BaseModel):
    """구조화된 일별기관매매종목 데이터"""
    
    code: str = Field(description="종목코드")
    name: str = Field(description="종목명")
    trade_info: dict = Field(description="매매정보 (순매수수량, 순매수금액)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "{종목코드}",
                "name": "{종목명}",
                "trade_info": {
                    "net_quantity": "{순매수수량}",
                    "net_amount": "{순매수금액}"
                }
            }
        }


class DailyInstitutionalTradeApiResponse(BaseModel):
    """키움 일별기관매매종목요청 API 응답"""
    
    start_date: str = Field(description="시작일자")
    end_date: str = Field(description="종료일자")
    trade_type: str = Field(description="매매구분")
    trade_type_name: str = Field(description="매매구분명")
    market_type: str = Field(description="시장구분")
    market_type_name: str = Field(description="시장구분명")
    exchange_type: str = Field(description="거래소구분")
    exchange_type_name: str = Field(description="거래소구분명")
    
    # 원본 데이터
    raw_data: DailyInstitutionalTradeResponse = Field(description="키움 원본 응답 데이터")
    
    # 구조화된 데이터
    trade_data: List[StructuredDailyInstitutionalTradeData] = Field(description="구조화된 일별기관매매종목 데이터")
    
    # 메타 정보
    data_count: int = Field(description="데이터 개수")
    request_time: str = Field(description="요청 시간")
    response_time: str = Field(description="응답 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "{시작일자}",
                "end_date": "{종료일자}",
                "trade_type": "{매매구분}",
                "trade_type_name": "{매매구분명}",
                "market_type": "{시장구분}",
                "market_type_name": "{시장구분명}",
                "exchange_type": "{거래소구분}",
                "exchange_type_name": "{거래소구분명}",
                "raw_data": {
                    "daly_orgn_trde_stk": []
                },
                "trade_data": [],
                "data_count": 0,
                "request_time": "{요청시간}",
                "response_time": "{응답시간}"
            }
        }


# 종목별기관매매추이요청 (ka10045) 모델
class StockInstitutionalTrendData(BaseModel):
    """종목별 기관매매 추이 데이터 (단일 항목)"""
    
    trd_dd: Optional[str] = Field(None, description="거래일자")
    stk_cd: Optional[str] = Field(None, description="종목코드")
    stk_nm: Optional[str] = Field(None, description="종목명")
    
    # 기관 관련 데이터
    orgn_whld_shqty: Optional[str] = Field(None, description="기관보유수량")
    orgn_wght: Optional[str] = Field(None, description="기관비중")
    orgn_esti_avrg_pric: Optional[str] = Field(None, description="기관추정평균가")
    orgn_netprps_qty: Optional[str] = Field(None, description="기관순매수수량")
    orgn_netprps_amt: Optional[str] = Field(None, description="기관순매수금액")
    orgn_buy_qty: Optional[str] = Field(None, description="기관매수수량")
    orgn_sel_qty: Optional[str] = Field(None, description="기관매도수량")
    
    # 외국인 관련 데이터
    for_whld_shqty: Optional[str] = Field(None, description="외국인보유수량")
    for_wght: Optional[str] = Field(None, description="외국인비중")
    for_esti_avrg_pric: Optional[str] = Field(None, description="외국인추정평균가")
    for_netprps_qty: Optional[str] = Field(None, description="외국인순매수수량")
    for_netprps_amt: Optional[str] = Field(None, description="외국인순매수금액")
    for_buy_qty: Optional[str] = Field(None, description="외국인매수수량")
    for_sel_qty: Optional[str] = Field(None, description="외국인매도수량")
    
    # 개인 관련 데이터
    ind_netprps_qty: Optional[str] = Field(None, description="개인순매수수량")
    ind_netprps_amt: Optional[str] = Field(None, description="개인순매수금액")
    ind_buy_qty: Optional[str] = Field(None, description="개인매수수량")
    ind_sel_qty: Optional[str] = Field(None, description="개인매도수량")
    
    # 기타 정보
    cur_pric: Optional[str] = Field(None, description="현재가")
    prdy_ctrt: Optional[str] = Field(None, description="전일대비")
    prdy_ctrt_sign: Optional[str] = Field(None, description="전일대비부호")
    prdy_vrss_vol_rt: Optional[str] = Field(None, description="전일대비거래량비율")


class StructuredStockInstitutionalTrendData(BaseModel):
    """구조화된 종목별 기관매매 추이 데이터"""
    
    trade_date: str = Field(description="거래일자")
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    
    # 기관 정보
    institutional_info: dict = Field(description="기관 매매 정보")
    
    # 외국인 정보  
    foreign_info: dict = Field(description="외국인 매매 정보")
    
    # 개인 정보
    individual_info: dict = Field(description="개인 매매 정보")
    
    # 주가 정보
    price_info: dict = Field(description="주가 정보")


class StockInstitutionalTrendResponse(BaseModel):
    """키움 종목별기관매매추이요청 응답 모델"""
    
    stk_orgn_trde_trd: Optional[List[StockInstitutionalTrendData]] = Field(None, description="종목별기관매매추이 데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stk_orgn_trde_trd": [
                    {
                        "trd_dd": "{거래일자}",
                        "stk_cd": "{종목코드}",
                        "stk_nm": "{종목명}",
                        "orgn_whld_shqty": "{기관보유수량}",
                        "orgn_wght": "{기관비중}",
                        "orgn_esti_avrg_pric": "{기관추정평균가}",
                        "orgn_netprps_qty": "{기관순매수수량}",
                        "orgn_netprps_amt": "{기관순매수금액}",
                        "orgn_buy_qty": "{기관매수수량}",
                        "orgn_sel_qty": "{기관매도수량}",
                        "for_whld_shqty": "{외국인보유수량}",
                        "for_wght": "{외국인비중}",
                        "for_esti_avrg_pric": "{외국인추정평균가}",
                        "for_netprps_qty": "{외국인순매수수량}",
                        "for_netprps_amt": "{외국인순매수금액}",
                        "for_buy_qty": "{외국인매수수량}",
                        "for_sel_qty": "{외국인매도수량}",
                        "ind_netprps_qty": "{개인순매수수량}",
                        "ind_netprps_amt": "{개인순매수금액}",
                        "ind_buy_qty": "{개인매수수량}",
                        "ind_sel_qty": "{개인매도수량}",
                        "cur_pric": "{현재가}",
                        "prdy_ctrt": "{전일대비}",
                        "prdy_ctrt_sign": "{전일대비부호}",
                        "prdy_vrss_vol_rt": "{전일대비거래량비율}"
                    }
                ]
            }
        }


class StockInstitutionalTrendApiResponse(BaseModel):
    """키움 종목별기관매매추이요청 API 응답"""
    
    stock_code: str = Field(description="종목코드")
    start_date: str = Field(description="시작일자")
    end_date: str = Field(description="종료일자")
    
    # 원본 데이터
    raw_data: StockInstitutionalTrendResponse = Field(description="키움 원본 응답 데이터")
    
    # 구조화된 데이터
    trend_data: List[StructuredStockInstitutionalTrendData] = Field(description="구조화된 종목별 기관매매 추이 데이터")
    
    # 메타 정보
    data_count: int = Field(description="데이터 개수")
    request_time: str = Field(description="요청 시간")
    response_time: str = Field(description="응답 시간")

    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "005930",
                "start_date": "{시작일자}",
                "end_date": "{종료일자}",
                "raw_data": {
                    "stk_orgn_trde_trd": []
                },
                "trend_data": [],
                "data_count": 0,
                "request_time": "{요청시간}",
                "response_time": "{응답시간}"
            }
        }