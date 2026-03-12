import os
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class StrategyType(str, Enum):
    SMA_CROSSOVER = "sma_crossover"  # 기존 SMA 크로스오버
    BOLLINGER = "bollinger"  # 볼린저밴드 반전
    KAMA = "kama"  # Kaufman Adaptive MA 크로스오버
    BREAKOUT = "breakout"  # 도치안 채널 브레이크아웃


class AllocationMode(str, Enum):
    EQUAL = "equal"                      # 기존: 종목당 고정 금액
    VOLUME_WEIGHTED = "volume_weighted"  # 거래량 비례 배분


class StrategyConfig(BaseModel):
    """런타임 전략 전환용 설정 모델"""

    strategy_type: StrategyType = StrategyType.BOLLINGER

    # SMA 크로스오버 파라미터
    short_ma_period: int = 7
    long_ma_period: int = 20
    use_advanced_strategy: bool = True
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_ma_period: int = 15
    obv_ma_period: int = 20
    stop_loss_pct: float = 3.0
    max_holding_days: int = 20

    # 매도 최소 수익률 게이트 (전략 공통, 0=비활성)
    # 시그널 매도 시 수익률 < 기준이면 보류 (손실 중이면 매도 허용)
    min_profit_pct: float = 0.3

    # 볼린저밴드 파라미터
    bollinger_period: int = 20
    bollinger_num_std: float = 2.0
    bollinger_volume_filter: bool = True
    bollinger_min_bandwidth: float = 1.0  # 밴드 폭 최소 % (좁은 밴드 매매 차단)
    bollinger_min_profit_pct: float = 0.3  # 최소 수익률 게이트 (볼린저 매도 시, 0=비활성)
    bollinger_min_sell_bandwidth: float = 0.0  # 매도 전용 밴드폭 필터 (0=비활성)
    bollinger_use_middle_exit: bool = True  # 중간밴드 이탈 매도 (보유 시 중간선 아래면 익절)
    bollinger_obv_filter: bool = True   # 볼린저 OBV 필터
    bollinger_obv_ma_period: int = 10   # 볼린저 OBV SMA 기간 (분봉용)

    # SMA 크로스 최소 갭 % (0=비활성, 두 MA 간 갭이 기준 미만이면 HOLD)
    min_sma_gap_pct: float = 0.1
    # 매도 후 재매수 금지 시간 (분, 0=비활성)
    sell_cooldown_minutes: int = 30

    # 분봉 설정
    use_minute_chart: bool = True
    minute_short_period: int = 7
    minute_long_period: int = 20

    # 트레일링 스탑 (고점 대비 하락률, 0=비활성)
    trailing_stop_pct: float = 2.0
    trailing_stop_grace_minutes: int = 15  # 매수 후 N분간 트레일링 스탑 비활성 (0=즉시 적용)

    # 목표 수익률 자동 매도 (0=비활성, 예: 3.0 → 매수가 대비 +3% 도달 시 자동 매도)
    take_profit_pct: float = 0.0

    # 분할 매수 (1=일반 전량 매수, 2+=BUY 시그널마다 분할 매수)
    split_buy_count: int = 1

    # 자본 활용 비율 (현금 대비 투자 비율, 0=target_order_amount 사용)
    capital_ratio: float = 0.3

    # RSI 다이버전스 필터 (SMA 크로스오버 복합 전략용)
    use_rsi_divergence: bool = False

    # MACD 확인 필터 (SMA 크로스오버 복합 전략용)
    use_macd_filter: bool = False
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # 볼린저 캔들 패턴 필터 (로스 카메론 방식)
    bollinger_use_engulfing: bool = False       # 장악형 캔들 확인
    bollinger_use_double_pattern: bool = False   # 이중바닥/천장 패턴
    bollinger_rsi_period: int = 14               # 볼린저용 RSI 기간
    bollinger_rsi_overbought: float = 70.0
    bollinger_rsi_oversold: float = 30.0

    # 자동 국면 전환
    auto_regime: bool = False

    # 섹터 모멘텀 스캐너
    scanner_enabled: bool = False           # 기본 비활성 (하위호환)
    scanner_interval_minutes: int = 10      # 스캔 주기
    scanner_top_sectors: int = 3            # 상위 N개 섹터
    scanner_max_picks: int = 5              # 최대 선정 종목
    scanner_min_price: float = 1000.0       # 최소 주가 (동전주 제외)
    scanner_min_volume: int = 100_000       # 최소 거래량
    scanner_min_change_rate: float = -30.0  # 최소 등락률 (하락종목도 포함)

    # 주문금액 배분 모드
    allocation_mode: AllocationMode = AllocationMode.EQUAL
    total_order_budget: int = 11_000_000       # 국내 총 예산 (KRW)
    us_total_order_budget: float = 6000.0      # 해외 총 예산 (USD)

    # ATR 기반 동적 손절/트레일링 (0=고정 % 사용)
    atr_stop_multiplier: float = 0.0      # ATR * N 으로 손절
    atr_trailing_multiplier: float = 0.0  # ATR * N 으로 트레일링
    atr_period: int = 14

    # 적응형 밴드폭 (볼린저, 0=고정 min_bandwidth 사용)
    bandwidth_percentile: float = 0.0
    bandwidth_lookback: int = 100

    # KAMA 파라미터
    kama_er_period: int = 10
    kama_fast_period: int = 2
    kama_slow_period: int = 30
    kama_signal_period: int = 10
    kama_volume_filter: bool = False

    # 브레이크아웃 파라미터
    breakout_upper_period: int = 20
    breakout_lower_period: int = 10
    breakout_atr_filter: float = 0.0
    breakout_volume_filter: bool = True

    # 멀티 타임프레임 확인 (분봉 전략 시 일봉 추세 필터)
    use_daily_trend_filter: bool = False
    daily_trend_sma_period: int = 20


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
    short_ma_period: int = 7
    long_ma_period: int = 20

    # 분봉 전략 파라미터
    use_minute_chart: bool = True          # 분봉 모드 활성화
    minute_short_period: int = 7           # 7분 SMA
    minute_long_period: int = 20           # 20분 SMA
    minute_chart_lookback: int = 120       # 분봉 조회 범위 (분)

    # SMA 크로스 최소 갭 % (0=비활성, 두 MA 간 갭이 기준 미만이면 HOLD)
    min_sma_gap_pct: float = 0.1
    # 매도 후 재매수 금지 시간 (분, 0=비활성)
    sell_cooldown_minutes: int = 30

    # 동적 주문수량
    target_order_amount: int = 10_000_000  # 목표 주문금액
    min_quantity: int = 1                  # 최소 주문수량
    max_quantity: int = 50                 # 최대 주문수량

    # 전략 선택
    strategy_type: StrategyType = StrategyType.BOLLINGER

    # 볼린저밴드 파라미터
    bollinger_period: int = 20  # SMA 기간 (20분)
    bollinger_num_std: float = 2.0  # 표준편차 배수
    bollinger_volume_filter: bool = True  # 볼린저 매수 시 거래량 필터 적용
    bollinger_volume_ma_period: int = 20  # 거래량 SMA 기간
    bollinger_min_bandwidth: float = 1.0  # 밴드 폭 최소 % (좁은 밴드 매매 차단)
    bollinger_min_profit_pct: float = 0.3  # 최소 수익률 게이트 (볼린저 매도 시, 0=비활성)
    bollinger_min_sell_bandwidth: float = 0.0  # 매도 전용 밴드폭 필터 (0=비활성)
    bollinger_use_middle_exit: bool = True  # 중간밴드 이탈 매도 (보유 시 중간선 아래면 익절)
    bollinger_obv_filter: bool = True   # 볼린저 OBV 필터
    bollinger_obv_ma_period: int = 10   # 볼린저 OBV SMA 기간 (분봉용)

    # 단타 제한
    max_daily_trades: int = 5  # 종목당 하루 최대 매수 횟수

    # 장 마감 청산 (0=비활성)
    force_close_minute: int = 0  # HHMM 이후 강제 매도 (0=비활성)
    no_new_buy_minute: int = 0  # HHMM 이후 신규 매수 금지 (0=비활성)

    # 활성 매매 시간대 (HHMM 튜플 리스트). 빈 리스트면 전 구간 매매.
    active_trading_windows: list[tuple[int, int]] = []  # 전 구간 매매

    # 복합 전략 (RSI + 거래량 + OBV 필터) — SMA_CROSSOVER 전략용
    use_advanced_strategy: bool = True
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_ma_period: int = 15
    obv_ma_period: int = 20

    # 리스크 관리 (전략 무관)
    stop_loss_pct: float = 3.0       # 매수가 대비 N% 하락 시 손절 (0=비활성)
    max_holding_days: int = 20       # 최대 보유 거래일 (0=비활성)

    # 매도 최소 수익률 게이트 (전략 공통, 0=비활성)
    min_profit_pct: float = 0.3

    # 트레일링 스탑 (고점 대비 하락률, 0=비활성)
    trailing_stop_pct: float = 2.0
    trailing_stop_grace_minutes: int = 15  # 매수 후 N분간 트레일링 스탑 비활성 (0=즉시 적용)

    # 목표 수익률 자동 매도 (0=비활성, 예: 3.0 → 매수가 대비 +3% 도달 시 자동 매도)
    take_profit_pct: float = 0.0

    # 분할 매수 (1=일반 전량 매수, 2+=BUY 시그널마다 분할 매수)
    split_buy_count: int = 1

    # 자본 활용 비율 (현금 대비 투자 비율, 0=target_order_amount 사용)
    capital_ratio: float = 0.3

    # RSI 다이버전스 필터 (SMA 크로스오버 복합 전략용)
    use_rsi_divergence: bool = False

    # MACD 확인 필터 (SMA 크로스오버 복합 전략용)
    use_macd_filter: bool = False
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # 볼린저 캔들 패턴 필터 (로스 카메론 방식)
    bollinger_use_engulfing: bool = False       # 장악형 캔들 확인
    bollinger_use_double_pattern: bool = False   # 이중바닥/천장 패턴
    bollinger_rsi_period: int = 14               # 볼린저용 RSI 기간
    bollinger_rsi_overbought: float = 70.0
    bollinger_rsi_oversold: float = 30.0

    # 자동 국면 전환
    auto_regime: bool = False
    regime_reference_symbol: str = "005930"  # 국면 판별 기준 종목

    # 섹터 모멘텀 스캐너
    scanner_enabled: bool = True            # 거래량 스캐너 활성
    scanner_interval_minutes: int = 1       # 스캔 주기 (1분)
    scanner_top_sectors: int = 5            # 상위 5개 섹터
    scanner_max_picks: int = 7              # 최대 7종목 선정
    scanner_min_price: float = 1000.0       # 최소 주가 (동전주 제외)
    scanner_min_volume: int = 100_000       # 최소 거래량
    scanner_min_change_rate: float = -30.0  # 최소 등락률 (하락종목도 포함)

    # 주문금액 배분 모드
    allocation_mode: AllocationMode = AllocationMode.EQUAL
    total_order_budget: int = 11_000_000       # 국내 총 예산 (KRW)
    us_total_order_budget: float = 6000.0      # 해외 총 예산 (USD)

    # ATR 기반 동적 손절/트레일링 (0=고정 % 사용)
    atr_stop_multiplier: float = 0.0
    atr_trailing_multiplier: float = 0.0
    atr_period: int = 14

    # 적응형 밴드폭 (볼린저, 0=고정 min_bandwidth 사용)
    bandwidth_percentile: float = 0.0
    bandwidth_lookback: int = 100

    # KAMA 파라미터
    kama_er_period: int = 10
    kama_fast_period: int = 2
    kama_slow_period: int = 30
    kama_signal_period: int = 10
    kama_volume_filter: bool = False

    # 브레이크아웃 파라미터
    breakout_upper_period: int = 10
    breakout_lower_period: int = 20
    breakout_atr_filter: float = 0.0
    breakout_volume_filter: bool = True

    # 멀티 타임프레임 확인 (분봉 전략 시 일봉 추세 필터)
    use_daily_trend_filter: bool = False
    daily_trend_sma_period: int = 20

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
