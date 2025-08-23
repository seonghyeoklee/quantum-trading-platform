#!/usr/bin/env python3
"""
키움증권 실시간 데이터 핸들러 베이스 클래스

실시간 데이터와 TR 메시지 처리를 위한 기본 인터페이스 정의
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Handle both relative and absolute imports
try:
    from ..models.realtime_data import RealtimeData
except ImportError:
    from kiwoom_api.realtime.models.realtime_data import RealtimeData

logger = logging.getLogger(__name__)


class BaseRealtimeHandler(ABC):
    """실시간 데이터 핸들러 베이스 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.message_count = 0
        
    @abstractmethod
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """실시간 데이터 처리
        
        Args:
            data: RealtimeData 객체
            
        Returns:
            처리 결과 딕셔너리 또는 None (처리 불가 시)
        """
        pass
        
    def _safe_int(self, value: str) -> int:
        """안전한 정수 변환"""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value: str) -> float:
        """안전한 실수 변환"""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
            
    def _get_current_time(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def _format_price(self, value: str) -> str:
        """가격 포맷팅 (천 단위 콤마)"""
        try:
            price = int(value) if value else 0
            return f"{price:,}"
        except (ValueError, TypeError):
            return value
    
    def _format_volume(self, value: str) -> str:
        """거래량 포맷팅"""
        try:
            volume = int(value) if value else 0
            if volume >= 100000000:  # 1억 이상
                return f"{volume/100000000:.1f}억"
            elif volume >= 10000:  # 1만 이상
                return f"{volume/10000:.1f}만"
            else:
                return f"{volume:,}"
        except (ValueError, TypeError):
            return value
    
    def _get_change_sign(self, value: str) -> str:
        """등락 기호 반환"""
        try:
            change = int(value) if value else 0
            if change > 0:
                return "▲"
            elif change < 0:
                return "▼"
            else:
                return "="
        except (ValueError, TypeError):
            return "?"
    
    def increment_message_count(self):
        """메시지 처리 횟수 증가"""
        self.message_count += 1


class BaseMessageHandler(ABC):
    """일반 메시지 핸들러 베이스 클래스"""
    
    def __init__(self, message_type: str):
        self.message_type = message_type
        self.handled_count = 0
        
    @abstractmethod
    async def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """메시지 처리
        
        Args:
            message: 수신된 메시지 딕셔너리
            
        Returns:
            처리 결과 딕셔너리 또는 None
        """
        pass
        
    def increment_handled_count(self):
        """처리 횟수 증가"""
        self.handled_count += 1