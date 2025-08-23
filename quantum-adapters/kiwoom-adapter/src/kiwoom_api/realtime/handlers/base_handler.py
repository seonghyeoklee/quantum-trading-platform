"""
실시간 데이터 핸들러 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from ..models.realtime_data import RealtimeData, RealtimeResponse


class BaseRealtimeHandler(ABC):
    """실시간 데이터 핸들러 기본 클래스"""
    
    def __init__(self, type_code: str):
        self.type_code = type_code
        self.callbacks: list[Callable[[RealtimeData], None]] = []
        
    @abstractmethod
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """실시간 데이터 처리"""
        pass
        
    def add_callback(self, callback: Callable[[RealtimeData], None]) -> None:
        """콜백 함수 추가"""
        self.callbacks.append(callback)
        
    def remove_callback(self, callback: Callable[[RealtimeData], None]) -> None:
        """콜백 함수 제거"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    async def execute_callbacks(self, data: RealtimeData) -> None:
        """등록된 콜백 함수들 실행"""
        for callback in self.callbacks:
            try:
                if callable(callback):
                    callback(data)
            except Exception as e:
                print(f"❌ 콜백 실행 오류 ({self.type_code}): {e}")
                
    def get_type_code(self) -> str:
        """타입 코드 반환"""
        return self.type_code