"""키움 API 요청 모델"""

from pydantic import BaseModel, Field



class KiwoomStockChartRequest(BaseModel):
    """키움 주식일봉차트조회 요청 모델 (ka10081)"""

    stk_cd: str = Field(
        description="종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)",
        example="005930"
    )
    base_dt: str = Field(
        description="기준일자 YYYYMMDD",
        example="20250820"
    )
    upd_stkpc_tp: str = Field(
        description="수정주가구분 (0 or 1)",
        example="1"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "base_dt": "20250820",
                "upd_stkpc_tp": "1"
            }
        }


class KiwoomStockChartApiRequest(BaseModel):
    """키움 주식일봉차트조회 요청 모델 (토큰 자동 관리)"""

    data: KiwoomStockChartRequest = Field(
        description="차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "stk_cd": "005930",
                    "base_dt": "20250820",
                    "upd_stkpc_tp": "1"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomStockMinuteChartRequest(BaseModel):
    """키움 주식분봉차트조회 요청 모델 (ka10080)"""

    stk_cd: str = Field(
        description="종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)",
        example="005930"
    )
    tic_scope: str = Field(
        description="틱범위 ('1':1분, '3':3분, '5':5분, '10':10분, '15':15분, '30':30분, '45':45분, '60':60분)",
        example="1"
    )
    upd_stkpc_tp: str = Field(
        description="수정주가구분 ('0' or '1')",
        example="1"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "tic_scope": "1",
                "upd_stkpc_tp": "1"
            }
        }


class KiwoomStockMinuteChartApiRequest(BaseModel):
    """키움 주식분봉차트조회 요청 모델 (토큰 자동 관리)"""

    data: KiwoomStockMinuteChartRequest = Field(
        description="분봉차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "stk_cd": "005930",
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomStockWeeklyChartRequest(BaseModel):
    """키움 주식주봉차트조회 요청 모델 (ka10082)"""
    
    stk_cd: str = Field(
        description="종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)",
        example="005930"
    )
    base_dt: str = Field(
        description="기준일자 YYYYMMDD",
        example="20241108"
    )
    upd_stkpc_tp: str = Field(
        description="수정주가구분 ('0' or '1')",
        example="1"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "base_dt": "20241108",
                "upd_stkpc_tp": "1"
            }
        }


class KiwoomStockWeeklyChartApiRequest(BaseModel):
    """키움 주식주봉차트조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomStockWeeklyChartRequest = Field(
        description="주봉차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "stk_cd": "005930",
                    "base_dt": "20241108",
                    "upd_stkpc_tp": "1"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomStockYearlyChartRequest(BaseModel):
    """키움 주식년봉차트조회 요청 모델 (ka10094)"""
    
    stk_cd: str = Field(
        description="종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)",
        example="005930"
    )
    base_dt: str = Field(
        description="기준일자 YYYYMMDD",
        example="20241212"
    )
    upd_stkpc_tp: str = Field(
        description="수정주가구분 ('0' or '1')",
        example="1"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "base_dt": "20241212",
                "upd_stkpc_tp": "1"
            }
        }


class KiwoomStockYearlyChartApiRequest(BaseModel):
    """키움 주식년봉차트조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomStockYearlyChartRequest = Field(
        description="년봉차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "stk_cd": "005930",
                    "base_dt": "20241212",
                    "upd_stkpc_tp": "1"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomStockTickChartRequest(BaseModel):
    """키움 주식틱차트조회 요청 모델 (ka10079)"""
    
    stk_cd: str = Field(
        description="종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)",
        example="005930"
    )
    tic_scope: str = Field(
        description="틱범위 ('1':1틱, '3':3틱, '5':5틱, '10':10틱, '30':30틱)",
        example="1"
    )
    upd_stkpc_tp: str = Field(
        description="수정주가구분 ('0' or '1')",
        example="1"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stk_cd": "005930",
                "tic_scope": "1",
                "upd_stkpc_tp": "1"
            }
        }


class KiwoomStockTickChartApiRequest(BaseModel):
    """키움 주식틱차트조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomStockTickChartRequest = Field(
        description="틱차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "stk_cd": "005930",
                    "tic_scope": "1",
                    "upd_stkpc_tp": "1"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomSectorTickChartRequest(BaseModel):
    """키움 업종틱차트조회 요청 모델 (ka20004)"""
    
    inds_cd: str = Field(
        description="업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)",
        example="001"
    )
    tic_scope: str = Field(
        description="틱범위 ('1':1틱, '3':3틱, '5':5틱, '10':10틱, '30':30틱)",
        example="1"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "inds_cd": "001",
                "tic_scope": "1"
            }
        }


class KiwoomSectorTickChartApiRequest(BaseModel):
    """키움 업종틱차트조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomSectorTickChartRequest = Field(
        description="업종틱차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "inds_cd": "001",
                    "tic_scope": "1"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomInvestorInstitutionChartRequest(BaseModel):
    """키움 종목별투자자기관별차트조회 요청 모델 (ka10060)"""
    
    dt: str = Field(
        description="일자 YYYYMMDD",
        example="20241107"
    )
    stk_cd: str = Field(
        description="종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)",
        example="005930"
    )
    amt_qty_tp: str = Field(
        description="금액수량구분 ('1':금액, '2':수량)",
        example="1"
    )
    trde_tp: str = Field(
        description="매매구분 ('0':순매수, '1':매수, '2':매도)",
        example="0"
    )
    unit_tp: str = Field(
        description="단위구분 ('1000':천주, '1':단주)",
        example="1000"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "dt": "20241107",
                "stk_cd": "005930",
                "amt_qty_tp": "1",
                "trde_tp": "0",
                "unit_tp": "1000"
            }
        }


class KiwoomInvestorInstitutionChartApiRequest(BaseModel):
    """키움 종목별투자자기관별차트조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomInvestorInstitutionChartRequest = Field(
        description="투자자기관별차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "dt": "20241107",
                    "stk_cd": "005930",
                    "amt_qty_tp": "1",
                    "trde_tp": "0",
                    "unit_tp": "1000"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomIntradayInvestorTradeChartRequest(BaseModel):
    """키움 장중투자자별매매차트조회 요청 모델 (ka10064)"""
    
    mrkt_tp: str = Field(
        description="시장구분 ('000':전체, '001':코스피, '101':코스닥)",
        example="000"
    )
    amt_qty_tp: str = Field(
        description="금액수량구분 ('1':금액, '2':수량)",
        example="1"
    )
    trde_tp: str = Field(
        description="매매구분 ('0':순매수, '1':매수, '2':매도)",
        example="0"
    )
    stk_cd: str = Field(
        description="종목코드 (거래소별 종목코드: KRX:039490, NXT:039490_NX, SOR:039490_AL)",
        example="005930"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "mrkt_tp": "000",
                "amt_qty_tp": "1",
                "trde_tp": "0",
                "stk_cd": "005930"
            }
        }


class KiwoomIntradayInvestorTradeChartApiRequest(BaseModel):
    """키움 장중투자자별매매차트조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomIntradayInvestorTradeChartRequest = Field(
        description="장중투자자별매매차트조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "mrkt_tp": "000",
                    "amt_qty_tp": "1",
                    "trde_tp": "0",
                    "stk_cd": "005930"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomSectorMinuteChartRequest(BaseModel):
    """키움 업종분봉조회 요청 모델 (ka20005)"""
    
    inds_cd: str = Field(
        description="업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)",
        example="001"
    )
    tic_scope: str = Field(
        description="틱범위 ('1':1분, '3':3분, '5':5분, '10':10분, '30':30분)",
        example="5"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "inds_cd": "001",
                "tic_scope": "5"
            }
        }


class KiwoomSectorMinuteChartApiRequest(BaseModel):
    """키움 업종분봉조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomSectorMinuteChartRequest = Field(
        description="업종분봉조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "inds_cd": "001",
                    "tic_scope": "5"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomSectorDailyChartRequest(BaseModel):
    """키움 업종일봉조회 요청 모델 (ka20006)"""

    inds_cd: str = Field(
        description="업종코드 (001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주, 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701:KRX100)",
        example="001"
    )
    base_dt: str = Field(
        description="기준일자 YYYYMMDD",
        example="20241122"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "inds_cd": "001",
                "base_dt": "20241122"
            }
        }


class KiwoomSectorDailyChartApiRequest(BaseModel):
    """키움 업종일봉조회 요청 모델 (토큰 자동 관리)"""
    
    data: KiwoomSectorDailyChartRequest = Field(
        description="업종일봉조회 요청 데이터"
    )
    cont_yn: str = Field(
        default="N",
        description="연속조회여부 ('Y' or 'N')",
        example="N"
    )
    next_key: str = Field(
        default="",
        description="연속조회키",
        example=""
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "inds_cd": "001",
                    "base_dt": "20241122"
                },
                "cont_yn": "N",
                "next_key": ""
            }
        }


class KiwoomApiResponse(BaseModel):
    """키움 API 응답 모델"""

    Code: int = Field(description="HTTP 상태 코드", example=200)
    Header: dict = Field(
        description="키움 API 응답 헤더",
        example={
            "next-key": "",
            "cont-yn": "N",
            "api-id": "au10001"
        }
    )
    Body: dict = Field(
        description="키움 API 응답 바디",
        example={
            "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "expires_dt": "20250821235959",
            "return_code": 0,
            "return_msg": "정상적으로 처리되었습니다"
        }
    )
