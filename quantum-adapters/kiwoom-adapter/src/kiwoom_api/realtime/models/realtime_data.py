#!/usr/bin/env python3
"""
키움증권 실시간 데이터 모델

18가지 실시간 데이터 타입과 조건검색 실시간 알림을 위한 통합 모델
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class RealtimeData(BaseModel):
    """실시간 데이터 기본 모델"""
    symbol: str = Field(..., description="종목코드")
    type: str = Field(..., description="실시간 타입 (0A, 0B, 00 등)")
    values: Dict[str, str] = Field({}, description="실시간 데이터 값들 (필드코드: 값)")
    timestamp: Optional[datetime] = Field(None, description="수신 시간")
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)
    
    def get_field_value(self, field_code: str) -> Optional[str]:
        """특정 필드 값 반환"""
        return self.values.get(field_code)
    
    def is_screener_alert(self) -> bool:
        """조건검색 실시간 알림 여부 확인"""
        # 조건검색 관련 필드 존재 확인
        return bool(self.values.get("841") and self.values.get("9001") and self.values.get("843"))


class RealtimeResponse(BaseModel):
    """실시간 응답 모델"""
    trnm: str = Field("REAL", description="TR명 (실시간은 'REAL')")
    data: List[Dict[str, Any]] = Field([], description="실시간 데이터 배열")
    
    def to_realtime_data(self) -> List[RealtimeData]:
        """RealtimeData 객체 리스트로 변환"""
        results = []
        
        for item in self.data:
            if isinstance(item, dict):
                # 실시간 데이터 형태 분석
                symbol = item.get('symbol', '')
                rt_type = item.get('type', '')
                values = item.get('values', {})
                
                results.append(RealtimeData(
                    symbol=symbol,
                    type=rt_type,
                    values=values
                ))
        
        return results


class RealtimeSubscription(BaseModel):
    """실시간 구독 정보 모델"""
    symbol: str = Field(..., description="종목코드")
    types: List[str] = Field([], description="구독 중인 실시간 타입들")
    subscribed_at: datetime = Field(default_factory=datetime.now, description="구독 시작 시간")
    active: bool = Field(True, description="구독 활성 상태")


class RealtimeManager(BaseModel):
    """실시간 구독 관리자"""
    subscriptions: Dict[str, RealtimeSubscription] = Field({}, description="구독 정보 맵")
    total_messages: int = Field(0, description="총 수신 메시지 수")
    last_message_time: Optional[datetime] = Field(None, description="마지막 메시지 수신 시간")
    
    def add_subscription(self, symbol: str, types: List[str]):
        """구독 추가"""
        if symbol in self.subscriptions:
            # 기존 구독에 타입 추가
            existing_types = set(self.subscriptions[symbol].types)
            new_types = set(types)
            self.subscriptions[symbol].types = list(existing_types | new_types)
        else:
            # 새 구독 생성
            self.subscriptions[symbol] = RealtimeSubscription(
                symbol=symbol,
                types=types
            )
    
    def remove_subscription(self, symbol: str, types: Optional[List[str]] = None):
        """구독 제거"""
        if symbol not in self.subscriptions:
            return
        
        if types is None:
            # 전체 구독 제거
            del self.subscriptions[symbol]
        else:
            # 특정 타입만 제거
            existing_types = set(self.subscriptions[symbol].types)
            remove_types = set(types)
            remaining_types = list(existing_types - remove_types)
            
            if remaining_types:
                self.subscriptions[symbol].types = remaining_types
            else:
                del self.subscriptions[symbol]
    
    def update_message_stats(self):
        """메시지 수신 통계 업데이트"""
        self.total_messages += 1
        self.last_message_time = datetime.now()
    
    def get_subscribed_symbols(self) -> List[str]:
        """구독 중인 종목 목록 반환"""
        return list(self.subscriptions.keys())
    
    def get_subscription_count(self) -> int:
        """총 구독 수 반환"""
        return len(self.subscriptions)
    
    def get_total_types(self) -> int:
        """총 구독 타입 수 반환"""
        return sum(len(sub.types) for sub in self.subscriptions.values())


# 실시간 데이터 타입별 필드 정의 (참고용)
REALTIME_FIELD_DEFINITIONS = {
    "0A": {  # 체결처리
        "9001": "종목코드",
        "20": "체결시간",
        "10": "현재가",
        "11": "전일대비",
        "12": "등락율",
        "13": "누적거래량",
        "14": "누적거래대금"
    },
    "0B": {  # 체결
        "9001": "종목코드", 
        "20": "체결시간",
        "10": "현재가",
        "11": "전일대비",
        "12": "등락율",
        "13": "체결량",
        "907": "매도수구분"
    },
    "00": {  # 호가잔량
        "9001": "종목코드",
        "21": "호가시간", 
        "41": "매도호가1",
        "61": "매수호가1",
        "71": "매도호가잔량1",
        "81": "매수호가잔량1"
    }
    # ... 나머지 15개 타입 정의 가능
}

# 조건검색 실시간 알림 필드 정의
SCREENER_REALTIME_FIELDS = {
    "841": "조건식일련번호",
    "9001": "종목코드", 
    "843": "삽입삭제구분",  # I:삽입(조건만족), D:삭제(조건이탈)
    "20": "체결시간",
    "907": "매도수구분"
}