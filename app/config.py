import os
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class StrategyType(str, Enum):
    SMA_CROSSOVER = "sma_crossover"  # 기존 SMA 크로스오버
    BOLLINGER = "bollinger"  # 볼린저밴드 반전


class StrategyConfig(BaseModel):
    """런타임 전략 전환용 설정 모델"""

    strategy_type: StrategyType = StrategyType.BOLLINGER

    # SMA 크로스오버 파라미터
    short_ma_period: int = 10
    long_ma_period: int = 40
    use_advanced_strategy: bool = True
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_ma_period: int = 15
    obv_ma_period: int = 20
    stop_loss_pct: float = 5.0
    max_holding_days: int = 20

    # 볼린저밴드 파라미터
    bollinger_period: int = 20
    bollinger_num_std: float = 2.0
    bollinger_volume_filter: bool = True

    # 분봉 설정
    use_minute_chart: bool = True
    minute_short_period: int = 5
    minute_long_period: int = 20

    # 트레일링 스탑 (고점 대비 하락률, 0=비활성)
    trailing_stop_pct: float = 0.0

    # 자본 활용 비율 (현금 대비 투자 비율, 0=target_order_amount 사용)
    capital_ratio: float = 0.0

    # 자동 국면 전환
    auto_regime: bool = False


class KISConfig(BaseSettings):
    """KIS API 설정"""

    # 모의투자 기본 URL
    base_url: str = "https://openapivts.koreainvestment.com:29443"

    # API 키 (환경변수 또는 yaml에서 로드)
    app_key: str = ""
    app_secret: str = ""

    # 계좌 정보
    account_no: str = ""  # 8자리 종합계좌번호
    account_product_code: str = "01"  # 계좌상품코드
    hts_id: str = ""

    # HTTP 클라이언트 설정
    timeout: float = 10.0  # 요청 타임아웃 (초)


class TradingConfig(BaseSettings):
    """매매 설정"""

    # 감시 종목 (백테스트 최적화 기반 포트폴리오)
    watch_symbols: list[str] = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "005380",  # 현대차
        "035420",  # NAVER
        "005490",  # POSCO홀딩스
        "105560",  # KB금융
        "009540",  # HD한국조선해양
        "034020",  # 두산에너빌리티
        "298040",  # 효성중공업
        "064350",  # 현대로템
        "010120",  # LS일렉트릭
    ]

    # 매매 금액 (백테스트용 종목당 주문금액)
    order_amount: int = 1_800_000

    # 전략 파라미터 (백테스트 최적화 결과 — 일봉용)
    short_ma_period: int = 10
    long_ma_period: int = 40

    # 분봉 전략 파라미터
    use_minute_chart: bool = True          # 분봉 모드 활성화
    minute_short_period: int = 5           # 5분 SMA
    minute_long_period: int = 20           # 20분 SMA
    minute_chart_lookback: int = 120       # 분봉 조회 범위 (분)

    # 동적 주문수량
    target_order_amount: int = 1_000_000   # 목표 주문금액
    min_quantity: int = 1                  # 최소 주문수량
    max_quantity: int = 50                 # 최대 주문수량

    # 전략 선택
    strategy_type: StrategyType = StrategyType.BOLLINGER

    # 볼린저밴드 파라미터
    bollinger_period: int = 20  # SMA 기간 (20분)
    bollinger_num_std: float = 2.0  # 표준편차 배수
    bollinger_volume_filter: bool = True  # 볼린저 매수 시 거래량 필터 적용
    bollinger_volume_ma_period: int = 20  # 거래량 SMA 기간

    # 단타 제한
    max_daily_trades: int = 5  # 종목당 하루 최대 매수 횟수

    # 장 마감 청산
    force_close_minute: int = 1510  # 15:10 이후 강제 매도 (HHMM)
    no_new_buy_minute: int = 1450  # 14:50 이후 신규 매수 금지

    # 활성 매매 시간대 (HHMM 튜플 리스트). 빈 리스트면 전 구간 매매.
    active_trading_windows: list[tuple[int, int]] = [
        (930, 1100),   # 오전 골든타임
        (1400, 1450),  # 오후 골든타임 (14:50 매수 마감)
    ]

    # 복합 전략 (RSI + 거래량 + OBV 필터) — SMA_CROSSOVER 전략용
    use_advanced_strategy: bool = True
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_ma_period: int = 15
    obv_ma_period: int = 20

    # 리스크 관리 (SMA 크로스오버 전략용)
    stop_loss_pct: float = 5.0       # 매수가 대비 N% 하락 시 손절 (0=비활성)
    max_holding_days: int = 20       # 최대 보유 거래일 (0=비활성)

    # 트레일링 스탑 (고점 대비 하락률, 0=비활성)
    trailing_stop_pct: float = 0.0

    # 자본 활용 비율 (현금 대비 투자 비율, 0=target_order_amount 사용)
    capital_ratio: float = 0.10  # 예수금의 10%씩 종목당 투자

    # 자동 국면 전환
    auto_regime: bool = False
    regime_reference_symbol: str = "005930"  # 국면 판별 기준 종목

    # 저널 저장 경로 (빈 문자열이면 기본 경로 data/journal/logs)
    journal_dir: str = ""

    # 매매 주기 (초)
    trading_interval: int = 60

    # 연속 에러 허용 횟수 (초과 시 엔진 정지)
    max_consecutive_errors: int = 5

    # --- 해외주식(US) 설정 ---
    us_watch_symbols: list[str] = ["AAPL", "NVDA", "MSFT", "GOOGL", "META", "TSLA"]
    us_target_order_amount: float = 1000.0  # USD 기준
    us_min_quantity: int = 1
    us_max_quantity: int = 100
    # 심볼별 거래소 코드 (기본: NAS). 예: {"IBM": "NYS", "F": "AMS"}
    us_symbol_exchanges: dict[str, str] = {"GOOGL": "NAS", "META": "NAS"}


class Settings(BaseSettings):
    kis: KISConfig = KISConfig()
    trading: TradingConfig = TradingConfig()


def load_settings() -> Settings:
    """kis_devlp.yaml에서 설정을 로드하여 Settings 생성"""
    settings = Settings()

    # yaml 파일 경로: ~/KIS/config/kis_devlp.yaml
    yaml_path = Path.home() / "KIS" / "config" / "kis_devlp.yaml"
    if yaml_path.exists():
        with open(yaml_path, encoding="UTF-8") as f:
            cfg = yaml.safe_load(f)
        if cfg:
            settings.kis.app_key = cfg.get("paper_app", "")
            settings.kis.app_secret = cfg.get("paper_sec", "")
            settings.kis.account_no = cfg.get("my_paper_stock", "")
            settings.kis.account_product_code = cfg.get("my_prod", "01")
            settings.kis.hts_id = cfg.get("my_htsid", "")

    # 환경변수 오버라이드
    if os.getenv("KIS_APP_KEY"):
        settings.kis.app_key = os.getenv("KIS_APP_KEY", "")
    if os.getenv("KIS_APP_SECRET"):
        settings.kis.app_secret = os.getenv("KIS_APP_SECRET", "")
    if os.getenv("KIS_ACCOUNT_NO"):
        settings.kis.account_no = os.getenv("KIS_ACCOUNT_NO", "")

    return settings
