"""인증 관련 데이터 모델"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from .common import KiwoomApiResponse


class TokenRequest(BaseModel):
    """토큰 요청 모델 (키움 API au10001 스펙)"""
    
    grant_type: str = Field("client_credentials", description="인증 타입")
    appkey: str = Field(..., description="키움 앱키")
    secretkey: str = Field(..., description="키움 시크릿키")
    
    @field_validator("grant_type")
    @classmethod
    def validate_grant_type(cls, v):
        if v != "client_credentials":
            raise ValueError("grant_type은 'client_credentials'이어야 합니다")
        return v


class TokenResponse(KiwoomApiResponse):
    """토큰 응답 모델 (키움 API au10001 스펙 완전 준수)"""
    
    expires_dt: Optional[str] = Field(None, description="토큰 만료일시 (yyyyMMddHHmmss)")
    token_type: Optional[str] = Field(None, description="토큰 타입")
    token: Optional[str] = Field(None, description="접근 토큰")
    
    @classmethod
    def create_error_response(cls, return_code: int, return_msg: str) -> "TokenResponse":
        """에러 응답 생성"""
        return cls(
            return_code=return_code,
            return_msg=return_msg,
            expires_dt=None,
            token_type=None,
            token=None
        )
    
    @classmethod
    def create_success_response(
        cls, 
        token: str, 
        expires_dt: str, 
        token_type: str = "bearer",
        return_msg: str = "정상적으로 처리되었습니다"
    ) -> "TokenResponse":
        """성공 응답 생성"""
        return cls(
            return_code=0,
            return_msg=return_msg,
            expires_dt=expires_dt,
            token_type=token_type,
            token=token
        )


class CachedTokenInfo(BaseModel):
    """캐시된 토큰 정보"""
    
    app_key: str = Field(..., description="앱키")
    token: str = Field(..., description="토큰")
    expires_dt: str = Field(..., description="만료일시")
    issued_at: datetime = Field(..., description="발급시간")
    expires_at: datetime = Field(..., description="만료시간")
    
    def is_expired(self, buffer_minutes: int = 5) -> bool:
        """토큰 만료 여부 확인 (버퍼 시간 포함)"""
        buffer_time = datetime.now() + timedelta(minutes=buffer_minutes)
        return self.expires_at <= buffer_time
    
    def is_valid(self, buffer_minutes: int = 5) -> bool:
        """토큰 유효성 확인 (만료되지 않았으면 유효)"""
        return not self.is_expired(buffer_minutes)
    
    def get_token(self) -> str:
        """토큰 반환 (마스킹 없이)"""
        return self.token or ""