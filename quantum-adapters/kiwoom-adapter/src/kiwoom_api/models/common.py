"""공통 응답 모델"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class KiwoomApiResponse(BaseModel):
    """키움 API 공통 응답 모델"""
    
    return_code: int
    return_msg: str
    
    def is_success(self) -> bool:
        """성공 여부 확인"""
        return self.return_code == 0


class KiwoomApiHeaders(BaseModel):
    """키움 API 공통 헤더 모델"""
    
    api_id: str
    cont_yn: str = "N"  
    next_key: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """딕셔너리로 변환"""
        return {
            "api-id": self.api_id,
            "cont-yn": self.cont_yn,
            "next-key": self.next_key
        }