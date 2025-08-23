"""
기본 실시간 데이터 모델
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class BaseRealtimeModel(BaseModel, ABC):
    """실시간 데이터 기본 모델"""
    
    class Config:
        """Pydantic 설정"""
        extra = "allow"  # 알려지지 않은 필드 허용
        validate_assignment = True
        
    @abstractmethod
    def parse_values(self, values: Dict[str, str]) -> Dict[str, Any]:
        """타입별 values 파싱 로직"""
        pass
        
    @classmethod
    def from_realtime_data(cls, data: Dict[str, Any]) -> 'BaseRealtimeModel':
        """실시간 데이터에서 모델 인스턴스 생성"""
        return cls(**data)