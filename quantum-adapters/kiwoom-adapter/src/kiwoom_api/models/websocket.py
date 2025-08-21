"""키움 WebSocket API 요청/응답 모델"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WebSocketLoginRequest(BaseModel):
    """WebSocket 로그인 요청 모델"""
    
    trnm: str = Field(default="LOGIN", description="서비스명")
    token: str = Field(description="Access Token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trnm": "LOGIN",
                "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
            }
        }


class WebSocketRealtimeItem(BaseModel):
    """실시간 등록 아이템 모델"""
    
    item: List[str] = Field(description="실시간 등록 요소 (종목코드 등)")
    type: List[str] = Field(description="실시간 항목 (TR명: 00, 0A, 0B...)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item": ["005930", "000660"],
                "type": ["00", "0A"]
            }
        }


class WebSocketRegisterRequest(BaseModel):
    """실시간 데이터 등록 요청 모델 (REG)"""
    
    trnm: str = Field(default="REG", description="서비스명")
    grp_no: str = Field(default="1", description="그룹번호")
    refresh: str = Field(default="1", description="기존등록유지여부 (0:기존유지안함, 1:기존유지)")
    data: List[WebSocketRealtimeItem] = Field(description="실시간 등록 리스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trnm": "REG",
                "grp_no": "1",
                "refresh": "1",
                "data": [{
                    "item": ["005930"],
                    "type": ["00"]
                }]
            }
        }


class WebSocketRemoveRequest(BaseModel):
    """실시간 데이터 해지 요청 모델 (REMOVE)"""
    
    trnm: str = Field(default="REMOVE", description="서비스명")
    grp_no: str = Field(description="그룹번호")
    data: List[WebSocketRealtimeItem] = Field(description="해지할 실시간 리스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trnm": "REMOVE",
                "grp_no": "1",
                "data": [{
                    "item": ["005930"],
                    "type": ["00"]
                }]
            }
        }


class WebSocketRealtimeValues(BaseModel):
    """실시간 데이터 값 모델"""
    
    # API 스펙에 따른 실시간 데이터 필드들 (0B 타입 기준)
    execution_time: Optional[str] = Field(None, alias="20", description="체결시간")
    current_price: Optional[str] = Field(None, alias="10", description="현재가")
    change: Optional[str] = Field(None, alias="11", description="전일대비")
    change_rate: Optional[str] = Field(None, alias="12", description="등락율")
    ask_price: Optional[str] = Field(None, alias="27", description="(최우선)매도호가")
    bid_price: Optional[str] = Field(None, alias="28", description="(최우선)매수호가")
    volume: Optional[str] = Field(None, alias="15", description="거래량 (+는 매수체결, -는 매도체결)")
    acc_volume: Optional[str] = Field(None, alias="13", description="누적거래량")
    acc_trade_value: Optional[str] = Field(None, alias="14", description="누적거래대금")
    open_price: Optional[str] = Field(None, alias="16", description="시가")
    high_price: Optional[str] = Field(None, alias="17", description="고가")
    low_price: Optional[str] = Field(None, alias="18", description="저가")
    change_sign: Optional[str] = Field(None, alias="25", description="전일대비기호")
    volume_change: Optional[str] = Field(None, alias="26", description="전일거래량대비(계약,주)")
    trade_value_change: Optional[str] = Field(None, alias="29", description="거래대금증감")
    volume_change_rate: Optional[str] = Field(None, alias="30", description="전일거래량대비(비율)")
    turnover_rate: Optional[str] = Field(None, alias="31", description="거래회전율")
    trade_cost: Optional[str] = Field(None, alias="32", description="거래비용")
    strength: Optional[str] = Field(None, alias="228", description="체결강도")
    market_cap: Optional[str] = Field(None, alias="311", description="시가총액(억)")
    market_state: Optional[str] = Field(None, alias="290", description="장구분 (1:장전, 2:장중, 3:장후)")
    ko_approach: Optional[str] = Field(None, alias="691", description="K.O 접근도")
    upper_limit_time: Optional[str] = Field(None, alias="567", description="상한가발생시간")
    lower_limit_time: Optional[str] = Field(None, alias="568", description="하한가발생시간")
    prev_same_time_vol_rate: Optional[str] = Field(None, alias="851", description="전일 동시간 거래량 비율")
    open_time: Optional[str] = Field(None, alias="1890", description="시가시간")
    high_time: Optional[str] = Field(None, alias="1891", description="고가시간")
    low_time: Optional[str] = Field(None, alias="1892", description="저가시간")
    sell_volume: Optional[str] = Field(None, alias="1030", description="매도체결량")
    buy_volume: Optional[str] = Field(None, alias="1031", description="매수체결량")
    buy_rate: Optional[str] = Field(None, alias="1032", description="매수비율")
    sell_count: Optional[str] = Field(None, alias="1071", description="매도체결건수")
    buy_count: Optional[str] = Field(None, alias="1072", description="매수체결건수")
    instant_trade_value: Optional[str] = Field(None, alias="1313", description="순간거래대금")
    sell_volume_single: Optional[str] = Field(None, alias="1315", description="매도체결량_단건")
    buy_volume_single: Optional[str] = Field(None, alias="1316", description="매수체결량_단건")
    net_buy_volume: Optional[str] = Field(None, alias="1314", description="순매수체결량")
    cfd_margin: Optional[str] = Field(None, alias="1497", description="CFD증거금")
    maintenance_margin: Optional[str] = Field(None, alias="1498", description="유지증거금")
    daily_avg_price: Optional[str] = Field(None, alias="620", description="당일거래평균가")
    cfd_trade_cost: Optional[str] = Field(None, alias="732", description="CFD거래비용")
    stock_lending_cost: Optional[str] = Field(None, alias="852", description="대주거래비용")
    exchange_type: Optional[str] = Field(None, alias="9081", description="거래소구분")
    
    # 계좌 관련 (기존 필드 유지)
    account_no: Optional[str] = Field(None, alias="9201", description="계좌번호")
    order_no: Optional[str] = Field(None, alias="9203", description="주문번호")
    manager_id: Optional[str] = Field(None, alias="9205", description="관리자사번")
    symbol_code: Optional[str] = Field(None, alias="9001", description="종목코드/업종코드")
    symbol_name: Optional[str] = Field(None, alias="302", description="종목명")
    
    # 주문 관련
    order_business_type: Optional[str] = Field(None, alias="912", description="주문업무분류")
    order_status: Optional[str] = Field(None, alias="913", description="주문상태")
    order_quantity: Optional[str] = Field(None, alias="900", description="주문수량")
    order_price: Optional[str] = Field(None, alias="901", description="주문가격")
    unfilled_quantity: Optional[str] = Field(None, alias="902", description="미체결수량")
    filled_amount: Optional[str] = Field(None, alias="903", description="체결누계금액")
    original_order_no: Optional[str] = Field(None, alias="904", description="원주문번호")
    order_type: Optional[str] = Field(None, alias="905", description="주문구분")
    trade_type: Optional[str] = Field(None, alias="906", description="매매구분")
    buy_sell_type: Optional[str] = Field(None, alias="907", description="매도수구분")
    order_time: Optional[str] = Field(None, alias="908", description="주문/체결시간")
    
    # 체결 관련
    execution_no: Optional[str] = Field(None, alias="909", description="체결번호")
    execution_price: Optional[str] = Field(None, alias="910", description="체결가")
    execution_quantity: Optional[str] = Field(None, alias="911", description="체결량")
    unit_execution_price: Optional[str] = Field(None, alias="914", description="단위체결가")
    unit_execution_quantity: Optional[str] = Field(None, alias="915", description="단위체결량")
    
    # 수수료/세금
    daily_commission: Optional[str] = Field(None, alias="938", description="당일매매수수료")
    daily_tax: Optional[str] = Field(None, alias="939", description="당일매매세금")
    
    # 기타
    reject_reason: Optional[str] = Field(None, alias="919", description="거부사유")
    screen_no: Optional[str] = Field(None, alias="920", description="화면번호")
    terminal_no: Optional[str] = Field(None, alias="921", description="터미널번호")
    credit_type: Optional[str] = Field(None, alias="922", description="신용구분")
    loan_date: Optional[str] = Field(None, alias="923", description="대출일")
    after_hours_price: Optional[str] = Field(None, alias="10010", description="시간외단일가_현재가")
    
    # 거래소 구분
    exchange_code: Optional[str] = Field(None, alias="2134", description="거래소구분 (0:통합,1:KRX,2:NXT)")
    exchange_name: Optional[str] = Field(None, alias="2135", description="거래소구분명")
    sor_flag: Optional[str] = Field(None, alias="2136", description="SOR여부 (Y,N)")
    
    class Config:
        allow_population_by_field_name = True
        json_schema_extra = {
            "example": {
                "9001": "005930",
                "302": "삼성전자",
                "10": "75000",
                "27": "75100",
                "28": "74900"
            }
        }


class WebSocketRealtimeDataItem(BaseModel):
    """실시간 데이터 아이템 모델"""
    
    type: Optional[str] = Field(None, description="실시간항목 (TR명)")
    name: Optional[str] = Field(None, description="실시간 항목명")
    item: Optional[str] = Field(None, description="실시간 등록 요소 (종목코드)")
    values: Optional[Dict[str, str]] = Field(None, description="실시간 값 리스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "00",
                "name": "주식호가잔량",
                "item": "005930",
                "values": {
                    "9001": "005930",
                    "302": "삼성전자",
                    "10": "75000"
                }
            }
        }


class WebSocketResponse(BaseModel):
    """WebSocket 응답 모델"""
    
    return_code: Optional[int] = Field(None, description="결과코드 (0:정상, 1:오류)")
    return_msg: Optional[str] = Field(None, description="결과메시지")
    trnm: Optional[str] = Field(None, description="서비스명")
    data: Optional[List[WebSocketRealtimeDataItem]] = Field(None, description="실시간 데이터 리스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "return_code": 0,
                "return_msg": "정상처리",
                "trnm": "REG",
                "data": [{
                    "type": "00",
                    "name": "주식호가잔량", 
                    "item": "005930",
                    "values": {
                        "9001": "005930",
                        "302": "삼성전자",
                        "10": "75000"
                    }
                }]
            }
        }


# 실시간 데이터 타입 코드 매핑
REALTIME_TYPE_CODES = {
    "00": "주식호가잔량",
    "0A": "주식체결처리",
    "0B": "주식우선호가",
    "0C": "주식예상체결가",
    "0D": "주식ETF_NAV",
    "0E": "주식거래원",
    "0F": "주식VI발동해제",
    "0G": "주식투자자", 
    "0H": "주식투자자별매매거래량",
    "0I": "장시작시간",
    "0J": "ETF추적오차율",
    "0K": "신고대량매매체결",
    "0L": "상품별투자자별매매거래대금"
}


# 실시간 값 필드 매핑
REALTIME_VALUE_FIELDS = {
    "9201": "계좌번호",
    "9203": "주문번호", 
    "9205": "관리자사번",
    "9001": "종목코드",
    "912": "주문업무분류",
    "913": "주문상태",
    "302": "종목명",
    "900": "주문수량",
    "901": "주문가격",
    "902": "미체결수량",
    "903": "체결누계금액",
    "904": "원주문번호",
    "905": "주문구분",
    "906": "매매구분",
    "907": "매도수구분",
    "908": "주문체결시간",
    "909": "체결번호",
    "910": "체결가",
    "911": "체결량",
    "10": "현재가",
    "27": "매도호가",
    "28": "매수호가",
    "914": "단위체결가",
    "915": "단위체결량",
    "938": "당일매매수수료",
    "939": "당일매매세금",
    "919": "거부사유",
    "920": "화면번호",
    "921": "터미널번호",
    "922": "신용구분",
    "923": "대출일",
    "10010": "시간외단일가현재가",
    "2134": "거래소구분",
    "2135": "거래소구분명",
    "2136": "SOR여부"
}