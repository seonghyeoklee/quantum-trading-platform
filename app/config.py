import os
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings


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

    # 감시 종목 (기본: 삼성전자, SK하이닉스)
    watch_symbols: list[str] = ["005930", "000660"]

    # 매매 금액 (종목당)
    order_amount: int = 500_000

    # 손절/익절 비율 (미사용 - MVP에서는 전략 시그널로만 매매)
    stop_loss_pct: float = -3.0
    take_profit_pct: float = 5.0

    # 전략 파라미터
    short_ma_period: int = 5
    long_ma_period: int = 20

    # 매매 주기 (초)
    trading_interval: int = 60

    # 연속 에러 허용 횟수 (초과 시 엔진 정지)
    max_consecutive_errors: int = 5


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
