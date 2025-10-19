"""
설정 관리 모듈

환경변수 및 시스템 설정을 관리합니다.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # === 기본 설정 ===
    app_name: str = "국내주식 단타 자동매매 시스템"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # === KIS API 설정 ===
    # 한국투자증권 API 인증 정보
    KIS_APPKEY: str = os.getenv("KIS_APPKEY", "")
    KIS_APPSECRET: str = os.getenv("KIS_APPSECRET", "")
    KIS_CANO: str = os.getenv("KIS_CANO", "")
    KIS_ACNT_PRDT_CD: str = os.getenv("KIS_ACNT_PRDT_CD", "01")
    
    # 실전/모의투자 설정
    KIS_USE_MOCK: bool = os.getenv("KIS_USE_MOCK", "true").lower() == "true"
    KIS_REAL_URL: str = os.getenv("KIS_REAL_URL", "https://openapi.koreainvestment.com:9443")
    KIS_MOCK_URL: str = os.getenv("KIS_MOCK_URL", "https://openapivts.koreainvestment.com:29443")
    
    # WebSocket 설정
    KIS_WEBSOCKET_URL: str = os.getenv("KIS_WEBSOCKET_URL", "ws://ops.koreainvestment.com:21000")
    
    # TR_ID 설정
    TR_ID_BALANCE_MOCK: str = os.getenv("TR_ID_BALANCE_MOCK", "VTTC8434R")
    TR_ID_BALANCE_REAL: str = os.getenv("TR_ID_BALANCE_REAL", "TTTC8434R")
    
    # 환경에 따른 base_url 자동 설정
    @property
    def kis_base_url(self) -> str:
        return self.KIS_MOCK_URL if self.KIS_USE_MOCK else self.KIS_REAL_URL
    
    # 환경에 따른 TR_ID 자동 설정
    @property
    def get_balance_tr_id(self) -> str:
        return self.TR_ID_BALANCE_MOCK if self.KIS_USE_MOCK else self.TR_ID_BALANCE_REAL
    
    # === 데이터베이스 설정 ===
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # === Redis 설정 (캐싱 및 백그라운드 작업) ===
    redis_url: str = "redis://localhost:6379"
    
    # === 매매 전략 설정 ===
    # 관심 종목 리스트 (삼성전자, SK하이닉스, NAVER 등)
    watchlist: List[str] = ["005930", "000660", "035420", "051910", "006400"]
    
    # 시간 프레임 설정
    timeframe_minutes: int = 5  # 5분봉
    max_positions: int = 3  # 최대 동시 포지션 수
    
    # 리스크 관리 설정
    max_position_size_percent: float = 10.0  # 계좌 대비 최대 포지션 크기 (%)
    stop_loss_percent: float = 2.0  # 손절선 (%)
    take_profit_percent: float = 4.0  # 익절선 (%)
    
    # === 기술적 지표 설정 ===
    # RSI 설정
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    
    # 이동평균 설정
    ema_short_period: int = 5
    ema_long_period: int = 20
    
    # 볼린저 밴드 설정
    bb_period: int = 20
    bb_std_dev: float = 2.0
    
    # MACD 설정
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # === 시장 미시구조 분석 설정 ===
    # 호가창 분석
    order_book_imbalance_threshold: float = 0.3  # 호가 불균형 임계값
    large_order_threshold: int = 1000000  # 대량 거래 임계값 (원)
    
    # 체결강도 분석
    volume_spike_threshold: float = 2.0  # 거래량 급증 임계값 (배수)
    
    # === 거래 시간 설정 ===
    market_open_time: str = "09:00"
    market_close_time: str = "15:30"
    trading_start_time: str = "09:10"  # 시초가 이후 시작
    trading_end_time: str = "15:20"   # 장마감 전 종료
    
    # === 로깅 설정 ===
    log_level: str = "INFO"
    log_file_path: str = "logs/autotrading.log"
    
    # === 백테스팅 설정 ===
    backtest_start_date: str = "2024-01-01"
    backtest_initial_capital: float = 10000000.0  # 1천만원
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

class TradingConfig:
    """매매 전략별 세부 설정"""
    
    # === 진입 신호 가중치 ===
    SIGNAL_WEIGHTS = {
        "technical_indicators": 0.6,  # 기술적 지표 60%
        "market_microstructure": 0.3,  # 시장 미시구조 30%
        "sentiment": 0.1  # 센티먼트 10%
    }
    
    # === 기술적 지표 신호 조건 ===
    TECHNICAL_SIGNALS = {
        # RSI 조건
        "rsi_buy": {"condition": "oversold_bounce", "threshold": 35.0},
        "rsi_sell": {"condition": "overbought_decline", "threshold": 65.0},
        
        # 이동평균 조건
        "ema_buy": {"condition": "golden_cross", "confirmation_bars": 2},
        "ema_sell": {"condition": "death_cross", "confirmation_bars": 2},
        
        # 볼린저 밴드 조건
        "bb_buy": {"condition": "lower_band_bounce", "penetration_percent": 2.0},
        "bb_sell": {"condition": "upper_band_rejection", "penetration_percent": 2.0},
        
        # MACD 조건
        "macd_buy": {"condition": "bullish_crossover", "histogram_trend": "increasing"},
        "macd_sell": {"condition": "bearish_crossover", "histogram_trend": "decreasing"}
    }
    
    # === 시장 미시구조 신호 조건 ===
    MICROSTRUCTURE_SIGNALS = {
        # 호가창 불균형
        "order_book_imbalance": {
            "buy_threshold": 0.6,  # 매수 잔량 비율 60% 이상
            "sell_threshold": 0.4   # 매도 잔량 비율 40% 이하
        },
        
        # 체결강도
        "execution_strength": {
            "strong_buy": 150.0,   # 체결강도 150 이상
            "strong_sell": 50.0    # 체결강도 50 이하
        },
        
        # 대량 거래 감지
        "large_trades": {
            "volume_threshold": 5000000,  # 500만원 이상
            "frequency_threshold": 3      # 5분 내 3회 이상
        }
    }
    
    # === 리스크 관리 규칙 ===
    RISK_RULES = {
        # 일일 손실 한도
        "daily_loss_limit": 3.0,  # 계좌 대비 3%
        
        # 연속 손실 제한
        "max_consecutive_losses": 3,
        
        # 포지션별 리스크
        "max_position_risk": 1.0,  # 계좌 대비 1%
        
        # 상관관계 리스크
        "max_correlated_positions": 2,  # 동일 섹터 최대 2개
        
        # 시간대별 리스크
        "avoid_lunch_time": True,  # 점심시간 거래 제한 (12:00-13:00)
        "reduce_end_of_day": True  # 장마감 30분 전 포지션 축소
    }

# 설정 인스턴스 생성
settings = Settings()
trading_config = TradingConfig()

# TODO: 설정 검증 함수들
def validate_kis_credentials() -> bool:
    """KIS API 인증 정보 검증"""
    # return all([
    #     settings.kis_app_key,
    #     settings.kis_app_secret,
    #     settings.kis_account_number,
    #     settings.kis_account_product_code
    # ])
    pass

def validate_database_config() -> bool:
    """데이터베이스 설정 검증"""
    # return bool(settings.supabase_url and settings.supabase_key)
    pass

def get_trading_hours() -> dict:
    """거래 시간 정보 반환"""
    # from datetime import datetime, time
    # return {
    #     "market_open": time.fromisoformat(settings.market_open_time),
    #     "market_close": time.fromisoformat(settings.market_close_time),
    #     "trading_start": time.fromisoformat(settings.trading_start_time),
    #     "trading_end": time.fromisoformat(settings.trading_end_time)
    # }
    pass

def is_trading_time() -> bool:
    """현재 시간이 거래 시간인지 확인"""
    # from datetime import datetime
    # now = datetime.now().time()
    # trading_hours = get_trading_hours()
    # return trading_hours["trading_start"] <= now <= trading_hours["trading_end"]
    pass
