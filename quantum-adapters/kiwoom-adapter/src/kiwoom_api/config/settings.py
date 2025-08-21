"""키움 API 환경설정 모듈

환경변수 기반 설정 관리
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class KiwoomSettings(BaseSettings):
    """키움 API 설정"""
    
    # 키움 모드 설정
    KIWOOM_SANDBOX_MODE: bool = Field(True, description="키움 샌드박스 모드 (실전투자 vs 모의투자)")
    
    # 샌드박스 모드용 키 (모의투자)
    KIWOOM_SANDBOX_APP_KEY: str = Field(..., description="키움 샌드박스 API 앱키")
    KIWOOM_SANDBOX_APP_SECRET: str = Field(..., description="키움 샌드박스 API 시크릿키")
    
    # 실전 모드용 키 (실제투자)
    KIWOOM_PRODUCTION_APP_KEY: str = Field("", description="키움 실전 API 앱키")
    KIWOOM_PRODUCTION_APP_SECRET: str = Field("", description="키움 실전 API 시크릿키")
    
    # FastAPI 서버 설정
    FASTAPI_HOST: str = Field("0.0.0.0", description="FastAPI 호스트")
    FASTAPI_PORT: int = Field(8100, description="FastAPI 포트")
    
    # 로깅 설정
    LOG_LEVEL: str = Field("INFO", description="로깅 레벨")
    
    # WebSocket 설정
    WEBSOCKET_PING_INTERVAL: int = Field(60, description="WebSocket Ping 간격 (초)")
    WEBSOCKET_PING_TIMEOUT: int = Field(10, description="WebSocket Ping 타임아웃 (초)")
    WEBSOCKET_CLOSE_TIMEOUT: int = Field(10, description="WebSocket 종료 타임아웃 (초)")
    WEBSOCKET_MAX_CONNECTIONS: int = Field(100, description="최대 WebSocket 연결 수")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def kiwoom_base_url(self) -> str:
        """키움 API 베이스 URL"""
        if self.KIWOOM_SANDBOX_MODE:
            return "https://mockapi.kiwoom.com"  # 키움 샌드박스 환경
        return "https://api.kiwoom.com"  # 키움 실전 환경
    
    @property
    def kiwoom_websocket_url(self) -> str:
        """키움 WebSocket URL"""
        if self.KIWOOM_SANDBOX_MODE:
            return "wss://mockapi.kiwoom.com:10000/api/dostk/websocket"  # 샌드박스
        return "wss://api.kiwoom.com:10000/api/dostk/websocket"  # 실전
    
    @property
    def KIWOOM_APP_KEY(self) -> str:
        """현재 모드에 따른 앱키 자동 선택"""
        if self.KIWOOM_SANDBOX_MODE:
            return self.KIWOOM_SANDBOX_APP_KEY
        return self.KIWOOM_PRODUCTION_APP_KEY
    
    @property
    def KIWOOM_APP_SECRET(self) -> str:
        """현재 모드에 따른 시크릿키 자동 선택"""
        if self.KIWOOM_SANDBOX_MODE:
            return self.KIWOOM_SANDBOX_APP_SECRET
        return self.KIWOOM_PRODUCTION_APP_SECRET
    
    @property
    def kiwoom_mode_description(self) -> str:
        """현재 모드 설명"""
        return "샌드박스 (모의투자)" if self.KIWOOM_SANDBOX_MODE else "실전투자"
    
    def get_app_key(self, app_key: Optional[str] = None) -> str:
        """앱키 반환 (마스킹 없이)"""
        return app_key or self.KIWOOM_APP_KEY
    
    def validate_keys(self) -> bool:
        """현재 모드에 맞는 키가 설정되어 있는지 검증"""
        if self.KIWOOM_SANDBOX_MODE:
            return bool(self.KIWOOM_SANDBOX_APP_KEY and self.KIWOOM_SANDBOX_APP_SECRET)
        return bool(self.KIWOOM_PRODUCTION_APP_KEY and self.KIWOOM_PRODUCTION_APP_SECRET)


# 전역 설정 인스턴스
settings = KiwoomSettings()