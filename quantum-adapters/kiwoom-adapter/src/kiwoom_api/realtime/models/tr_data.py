"""
키움증권 조건검색 TR 데이터 모델

TR 요청/응답을 위한 Pydantic 모델 정의:
- 조건검색 목록조회 (CNSRLST)
- 조건검색 실행 (CNSRREQ)  
- 조건검색 해제 (CNSRCLR)
- 실시간 알림 데이터
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

# BaseModel을 직접 사용 (BaseRealtimeModel 불필요)


class TRRequest(BaseModel):
    """TR 요청 기본 모델"""
    trnm: str = Field(..., description="TR명")
    
    class Config:
        extra = "allow"  # 추가 필드 허용


class TRResponse(BaseModel):
    """TR 응답 기본 모델"""
    trnm: str = Field(..., description="TR명")
    return_code: int = Field(0, description="결과코드 (0:정상)")
    return_msg: str = Field("", description="결과메시지")
    
    class Config:
        extra = "allow"  # 추가 필드 허용


# ========== 조건검색 목록조회 (CNSRLST) ==========

class ScreenerListRequest(TRRequest):
    """조건검색 목록조회 요청"""
    trnm: str = Field("CNSRLST", description="TR명 고정값")


class ScreenerCondition(BaseModel):
    """조건검색식 정보"""
    seq: str = Field(..., description="조건검색식 일련번호")
    name: str = Field(..., description="조건검색식 명")
    description: Optional[str] = Field(None, description="조건식 설명")


class ScreenerListResponse(TRResponse):
    """조건검색 목록조회 응답"""
    trnm: str = Field("CNSRLST", description="TR명 고정값")
    data: List[List[str]] = Field([], description="조건검색식 목록 (이중 배열)")
    
    def get_conditions(self) -> List[ScreenerCondition]:
        """조건검색식 객체 목록으로 변환"""
        conditions = []
        for condition_data in self.data:
            if len(condition_data) >= 2:
                conditions.append(ScreenerCondition(
                    seq=condition_data[0],
                    name=condition_data[1],
                    description=f"조건식 {condition_data[0]}: {condition_data[1]}"
                ))
        return conditions


# ========== 조건검색 실행 (CNSRREQ) ==========

class ScreenerSearchRequest(TRRequest):
    """조건검색 실행 요청"""
    trnm: str = Field("CNSRREQ", description="TR명 고정값")
    seq: str = Field(..., description="조건검색식 일련번호")
    search_type: str = Field("0", description="조회타입 (0:일반, 1:실시간포함)")
    stex_tp: str = Field("K", description="거래소구분 (K:KRX)")
    cont_yn: str = Field("N", description="연속조회여부")
    next_key: str = Field("", description="연속조회키")
    
    @validator('search_type')
    def validate_search_type(cls, v):
        if v not in ['0', '1']:
            raise ValueError('search_type은 0(일반) 또는 1(실시간포함)이어야 합니다')
        return v


class ScreenerSearchResult(BaseModel):
    """조건검색 결과 종목"""
    jmcode: str = Field(..., description="종목코드", alias="jmcode")
    stock_code: str = Field("", description="종목코드 (정규화)")
    detected_time: Optional[str] = Field(None, description="발견 시간")
    
    def __init__(self, **data):
        super().__init__(**data)
        # jmcode를 stock_code로도 설정
        if not self.stock_code and self.jmcode:
            self.stock_code = self.jmcode


class ScreenerSearchResponse(TRResponse):
    """조건검색 실행 응답 (일반 검색)"""
    trnm: str = Field("CNSRREQ", description="TR명 고정값")
    seq: str = Field("", description="조건검색식 일련번호")
    cont_yn: str = Field("N", description="연속조회여부")
    next_key: str = Field("", description="연속조회키")
    data: List[Dict[str, Any]] = Field([], description="검색결과 데이터")
    
    def get_search_results(self) -> List[ScreenerSearchResult]:
        """검색 결과를 객체 목록으로 변환"""
        results = []
        for result_data in self.data:
            if isinstance(result_data, dict) and 'jmcode' in result_data:
                results.append(ScreenerSearchResult(**result_data))
        return results


class ScreenerRealtimeSearchResponse(TRResponse):
    """조건검색 실행 응답 (실시간 포함)"""
    trnm: str = Field("CNSRREQ", description="TR명 고정값")
    seq: str = Field("", description="조건검색식 일련번호")
    data: List[Dict[str, str]] = Field([], description="검색결과 데이터")
    
    def get_initial_results(self) -> List[str]:
        """초기 검색 결과 종목코드 목록"""
        results = []
        for result_data in self.data:
            if isinstance(result_data, dict) and 'jmcode' in result_data:
                results.append(result_data['jmcode'])
        return results


# ========== 조건검색 해제 (CNSRCLR) ==========

class ScreenerClearRequest(TRRequest):
    """조건검색 실시간 해제 요청"""
    trnm: str = Field("CNSRCLR", description="TR명 고정값")
    seq: str = Field(..., description="조건검색식 일련번호")


class ScreenerClearResponse(TRResponse):
    """조건검색 실시간 해제 응답"""
    trnm: str = Field("CNSRCLR", description="TR명 고정값")
    seq: str = Field("", description="조건검색식 일련번호")


# ========== 조건검색 실시간 알림 ==========

class ScreenerRealtimeAlert(BaseModel):
    """조건검색 실시간 알림 데이터"""
    condition_seq: str = Field(..., description="조건식 일련번호 (841)")
    stock_code: str = Field(..., description="종목코드 (9001)")
    action: str = Field(..., description="삽입/삭제 구분 (843) - I:삽입, D:삭제")
    trade_time: Optional[str] = Field(None, description="체결시간 (20)")
    trade_side: Optional[str] = Field(None, description="매도/수 구분 (907)")
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['I', 'D']:
            raise ValueError('action은 I(삽입) 또는 D(삭제)여야 합니다')
        return v
    
    def get_action_description(self) -> str:
        """액션 설명 반환"""
        return "조건만족" if self.action == 'I' else "조건이탈"
    
    def get_status(self) -> str:
        """상태 설명 반환"""
        return "종목추가" if self.action == 'I' else "종목제거"


# ========== 통합 데이터 모델 ==========

class ScreenerState(BaseModel):
    """조건검색 상태 관리"""
    seq: str = Field(..., description="조건식 일련번호")
    name: str = Field("", description="조건식 명")
    is_active: bool = Field(False, description="실시간 활성 여부")
    search_type: str = Field("0", description="검색 타입")
    monitored_stocks: List[str] = Field([], description="감시 중인 종목 목록")
    last_search_time: Optional[datetime] = Field(None, description="마지막 검색 시간")
    alert_count: int = Field(0, description="알림 발생 횟수")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ScreenerManager(BaseModel):
    """조건검색 매니저"""
    active_conditions: Dict[str, ScreenerState] = Field({}, description="활성 조건식 상태")
    total_alerts: int = Field(0, description="전체 알림 발생 횟수")
    last_update: Optional[datetime] = Field(None, description="마지막 업데이트 시간")
    
    def add_condition(self, condition: ScreenerCondition, search_type: str = "0"):
        """조건식 추가"""
        state = ScreenerState(
            seq=condition.seq,
            name=condition.name,
            search_type=search_type,
            is_active=(search_type == "1")
        )
        self.active_conditions[condition.seq] = state
        self.last_update = datetime.now()
    
    def remove_condition(self, seq: str):
        """조건식 제거"""
        self.active_conditions.pop(seq, None)
        self.last_update = datetime.now()
    
    def update_condition_stocks(self, seq: str, stock_code: str, action: str):
        """조건식 감시 종목 업데이트"""
        if seq in self.active_conditions:
            condition = self.active_conditions[seq]
            if action == 'I' and stock_code not in condition.monitored_stocks:
                condition.monitored_stocks.append(stock_code)
            elif action == 'D' and stock_code in condition.monitored_stocks:
                condition.monitored_stocks.remove(stock_code)
            
            condition.alert_count += 1
            self.total_alerts += 1
            self.last_update = datetime.now()
    
    def get_active_condition_count(self) -> int:
        """활성 조건식 수 반환"""
        return len([c for c in self.active_conditions.values() if c.is_active])
    
    def get_total_monitored_stocks(self) -> int:
        """전체 감시 종목 수 반환"""
        total = 0
        for condition in self.active_conditions.values():
            total += len(condition.monitored_stocks)
        return total
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# ========== TR 처리 결과 모델 ==========

class TRProcessResult(BaseModel):
    """TR 처리 결과"""
    tr_name: str = Field(..., description="TR명")
    success: bool = Field(True, description="처리 성공 여부")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="처리 결과 데이터")
    timestamp: str = Field(..., description="처리 시간")
    analysis: Optional[Dict[str, Any]] = Field(None, description="분석 정보")
    
    class Config:
        extra = "allow"