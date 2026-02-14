# CLAUDE.md

## Project Overview

**Quantum Trading Platform** — 국내주식 모의투자 자동매매 시스템 (MVP)

Python + FastAPI 기반. KIS Open API 모의투자 환경에서 분봉/일봉 SMA 크로스오버 + RSI/거래량/OBV 필터 전략으로 자동매매.

## Technology Stack

- **Python 3.13+**, FastAPI, Uvicorn
- **httpx**: KIS API 비동기 호출
- **Pydantic v2**: 데이터 모델 + 설정
- **pytest + pytest-asyncio**: 테스트
- **uv**: 패키지 관리
- **Docker**: 컨테이너 배포

## Project Structure

```
quantum-trading-platform/
├── app/
│   ├── main.py                # FastAPI 진입점 (lifespan으로 엔진 관리)
│   ├── config.py              # 설정 (KIS API, 매매 파라미터, StrategyConfig)
│   ├── models.py              # Pydantic 데이터 모델
│   ├── kis/                   # KIS API 클라이언트
│   │   ├── client.py          # HTTP 클라이언트 (재시도, rate limit, keep-alive 비활성화)
│   │   ├── auth.py            # 토큰 발급/관리 (파일 캐싱: ~/.cache/kis/token.json)
│   │   ├── market.py          # 현재가/일봉/분봉 차트 조회
│   │   └── order.py           # 매수/매도 주문, 잔고 조회 (OPSQ2000 재시도)
│   ├── trading/               # 자동매매 핵심
│   │   ├── engine.py          # 자동매매 루프 (분봉/일봉, 동적수량, 런타임 전략 전환)
│   │   ├── strategy.py        # SMA 크로스오버 + RSI/거래량/OBV 복합 전략
│   │   ├── regime.py          # 시장 국면 판별 (SMA 정배열/역배열 기반)
│   │   ├── journal.py         # 일일 매매 저널 (JSONL 로깅 + HTML 리포트)
│   │   ├── backtest.py        # 백테스트 엔진 (yfinance, 국면별 분할 백테스트)
│   │   └── calendar.py        # 매매일/장시간 판단
│   └── api/
│       └── routes.py          # API 엔드포인트 (매매 + 전략 전환 + 백테스트 + 저널)
├── scripts/                   # 분석 + 백테스트 스크립트
│   ├── generate_regime_report.py  # 국면 기반 전략 선택 통합 리포트
│   ├── generate_comparison_report.py  # 전략 비교 리포트
│   ├── generate_market_report.py      # 시장 분석 리포트
│   ├── generate_daily_report.py       # 일일 매매 저널 리포트
│   ├── optimize.sh            # 파라미터 탐색 실행
│   └── run_backtest.py        # 단일 백테스트 실행
├── tests/
│   ├── test_strategy.py       # 전략 로직 단위 테스트 (29개)
│   ├── test_engine.py         # 엔진 로직 + E2E 테스트 (23개)
│   ├── test_journal.py        # 매매 저널 단위 테스트 (12개)
│   ├── test_regime.py         # 국면 판별 단위 테스트 (19개)
│   ├── test_calendar.py       # 매매일/장시간 단위 테스트 (14개)
│   ├── test_backtest.py       # 백테스트 단위 테스트 (32개)
│   └── test_kis_client.py     # KIS API 통합 테스트 (6개)
├── kis-mcp/                   # KIS MCP Server (API 스펙 검색용)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── CLAUDE.md
```

## Development Commands

### Setup
```bash
uv sync --extra dev
```

### Run Server
```bash
uv run python -m app.main
# → http://localhost:8000
```

### Run Tests
```bash
uv run pytest tests/ -v
```

### Run Unit Tests Only (KIS API 키 불필요)
```bash
uv run pytest tests/test_strategy.py tests/test_engine.py tests/test_calendar.py tests/test_regime.py tests/test_journal.py -v
```

### Generate Regime Report (yfinance 필요)
```bash
uv run python scripts/generate_regime_report.py
# → regime_strategy_report.html 생성
```

### Generate Daily Journal Report
```bash
uv run python scripts/generate_daily_report.py              # 오늘
uv run python scripts/generate_daily_report.py 2026-02-14   # 특정 날짜
# → data/journal/reports/YYYY-MM-DD.html 생성
```

### Docker
```bash
docker compose up -d          # 서버 기동
docker compose logs -f        # 로그 확인
docker compose down           # 종료
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | 헬스체크 |
| GET | `/market/price/{symbol}` | 종목 현재가 |
| POST | `/trading/start` | 자동매매 시작 (body: `{"symbols": ["005930"]}`) |
| POST | `/trading/stop` | 자동매매 중지 |
| GET | `/trading/status` | 엔진 상태/시그널/주문 이력 |
| GET | `/trading/positions` | 보유 포지션 + 계좌 요약 |
| GET | `/trading/strategy` | 현재 전략 설정 조회 |
| POST | `/trading/strategy` | 전략 + 파라미터 런타임 변경 (body: `StrategyConfig`) |
| GET | `/trading/journal` | 저널 날짜 목록 |
| GET | `/trading/journal/{date}` | 특정 날짜 이벤트 조회 |
| GET | `/trading/journal/{date}/report` | 일일 리포트 HTML |
| POST | `/backtest` | 과거 데이터 백테스트 (yfinance) |

## KIS API Configuration

**모의투자 전용** (`openapivts.koreainvestment.com:29443`)

설정 방법 (택 1):
1. `~/KIS/config/kis_devlp.yaml` (기존 방식)
2. 환경변수: `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`

### kis_devlp.yaml 필수 키
```yaml
paper_app: "모의투자_앱키"
paper_sec: "모의투자_앱시크릿"
my_paper_stock: "모의투자_계좌번호_8자리"
my_prod: "01"
my_htsid: "HTS_ID"
```

### 토큰 캐싱

- 토큰은 `~/.cache/kis/token.json`에 파일 캐싱
- 서버 재시작 시 유효한 토큰을 파일에서 로드 → KIS 토큰 발급 rate limit (분당 1회) 방지
- 같은 앱키로 발급된 토큰만 재사용, 만료 1시간 전 자동 갱신

## Trading Strategy

**분봉 기반 당일매매 (기본 모드)**
- `use_minute_chart: true` — 1분봉 데이터로 장중 시그널 생성
- 단기: SMA(5분), 장기: SMA(20분), 조회범위: 120분
- 골든크로스 → **매수**, 데드크로스 → **매도**
- 장 시간: 09:00 ~ 15:20, 주기: 60초

**일봉 모드 (백테스트/장기매매)**
- `use_minute_chart: false` — 일봉 데이터 기반
- 단기: SMA(10), 장기: SMA(40) (백테스트 최적화 결과)

**복합 전략 필터 (RSI + 거래량 + OBV)**
- `use_advanced_strategy: true` — 크로스오버 시그널에 추가 필터 적용
- RSI 과매수(70)/과매도(30) 영역에서 역방향 시그널 차단
- 거래량 SMA(15) 대비 확인, OBV SMA(20) 추세 확인

**동적 주문수량**
- `target_order_amount` (기본 100만원) / 현재가로 수량 계산
- `min_quantity`(1) ~ `max_quantity`(50) 범위 제한
- `capital_ratio` (0=비활성): 예수금 대비 비율로 주문금액 산출 (target_order_amount 대체)

**리스크 관리**
- `stop_loss_pct`: 매수가 대비 N% 하락 시 손절 (0=비활성)
- `max_holding_days`: 최대 보유 거래일 초과 시 매도 (0=비활성)
- `trailing_stop_pct`: 고점 대비 N% 하락 시 트레일링 스탑 매도 (0=비활성, 전략 무관)

## Market Regime Strategy Selection (국면 기반 전략 선택)

### 배경

백테스트 결과, 코스피 강세장(+119% YoY)에서 모든 능동 전략이 Buy & Hold에 열위.
**시장 국면(강세/약세/횡보)에 따라 최적 전략이 다르다**는 관찰에서 출발.
사용자가 리포트를 보고 판단한 뒤, API로 전략을 전환하는 프로세스.

### 운용 프로세스

```
┌─────────────────────────────────────────────────────────┐
│  1. 리포트 생성                                          │
│     uv run python scripts/generate_regime_report.py     │
│     → regime_strategy_report.html                       │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  2. 현재 국면 확인                                       │
│     리포트 상단 배너: "강한 상승 / 상승 / 횡보 / 하락 / 강한 하락"│
│     SMA20/60/120 정배열 → 강세, 역배열 → 약세             │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  3. 히트맵 매트릭스 분석                                  │
│     국면별 × 전략별 평균 수익률 확인                       │
│                                                         │
│              강한상승  상승   횡보   하락   강한하락       │
│  SMA 기본     +8.2%  +3.1%  -2.4%  -5.1%  -8.3%        │
│  SMA+리스크   +6.5%  +2.8%  -1.2%  -2.3%  -4.1%        │
│  볼린저       +2.3%  +1.8%  +1.5%  +0.8%  -0.5%        │
│  Buy & Hold  +15.2%  +5.8%  -0.3%  -8.2%  -15.1%       │
│                                                         │
│  → 강세장: B&H 또는 SMA 기본 (추세 추종)                 │
│  → 약세장: 볼린저 또는 SMA+리스크 (손실 제한)             │
│  → 횡보장: 볼린저 (밴드 내 반복 매매)                     │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  4. 전략 전환 (API)                                      │
│                                                         │
│  현재 설정 조회:                                         │
│    GET /trading/strategy                                │
│                                                         │
│  전략 변경 (예: 횡보장 → 볼린저):                         │
│    POST /trading/strategy                               │
│    {                                                    │
│      "strategy_type": "bollinger",                      │
│      "bollinger_period": 20,                            │
│      "bollinger_num_std": 2.0,                          │
│      "bollinger_volume_filter": true,                   │
│      "use_minute_chart": true                           │
│    }                                                    │
│                                                         │
│  전략 변경 (예: 강세장 → SMA 기본):                       │
│    POST /trading/strategy                               │
│    {                                                    │
│      "strategy_type": "sma_crossover",                  │
│      "short_ma_period": 10,                             │
│      "long_ma_period": 40,                              │
│      "use_advanced_strategy": false,                    │
│      "stop_loss_pct": 7.0                               │
│    }                                                    │
│                                                         │
│  → 다음 tick부터 즉시 적용 (재시작 불필요)                │
│  → 전략 타입 변경 시 기존 매수 추적 정보 자동 초기화       │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  5. 모니터링                                             │
│     GET /trading/status  → 시그널/주문 확인               │
│     주기적으로 리포트 재생성 → 국면 전환 감지              │
└─────────────────────────────────────────────────────────┘
```

### 국면 판별 기준 (`regime.py`)

| 국면 | 조건 | 의미 |
|------|------|------|
| `strong_bull` | `last > SMA20 > SMA60 > SMA120` | 완전 정배열, 강한 상승 추세 |
| `bull` | `last > SMA60` AND `SMA20 > SMA60` | 상승 추세 |
| `sideways` | 위 4가지에 해당 없음 | SMA 엇갈림, 방향성 불명확 |
| `bear` | `last < SMA60` AND `SMA20 < SMA60` | 하락 추세 |
| `strong_bear` | `last < SMA20 < SMA60 < SMA120` | 완전 역배열, 강한 하락 추세 |

### 국면별 전략 가이드라인

| 국면 | 추천 전략 | 이유 |
|------|----------|------|
| 강한 상승 | B&H 또는 SMA 기본 (넓은 손절) | 추세를 최대한 타야 함. 잦은 매매 = 기회 비용 |
| 상승 | SMA 기본 | 골든크로스 추세 추종이 유효 |
| 횡보 | 볼린저 | 밴드 상하단 반복 매매. SMA는 잦은 크로스로 손실 누적 |
| 하락 | SMA+리스크 또는 볼린저 | 손절/보유기간 제한 필수. 현금 비중 확대 |
| 강한 하락 | 볼린저 (보수적) | 최소 매매, 하단 반등만 선별. 현금 비중 극대화 |

### 관련 모듈

| 파일 | 역할 |
|------|------|
| `app/trading/regime.py` | `classify_regime`, `detect_current_regime`, `segment_by_regime` |
| `app/trading/backtest.py` | `run_regime_segmented_backtest` — 국면별 4개 전략 분할 시뮬레이션 |
| `app/config.py` | `StrategyConfig` — 런타임 전략 전환용 Pydantic 모델 |
| `app/trading/engine.py` | `update_strategy(config)` — 재시작 없이 전략 변경 |
| `app/api/routes.py` | `GET/POST /trading/strategy` — 전략 조회/변경 API |
| `scripts/generate_regime_report.py` | 통합 HTML 리포트 생성 (국면 + 히트맵 + 추천) |

### StrategyConfig 전체 필드

```python
class StrategyConfig(BaseModel):
    strategy_type: StrategyType      # "sma_crossover" | "bollinger"
    short_ma_period: int = 10        # SMA 단기
    long_ma_period: int = 40         # SMA 장기
    use_advanced_strategy: bool      # RSI/거래량/OBV 필터
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_ma_period: int = 15
    obv_ma_period: int = 20
    stop_loss_pct: float = 5.0       # 0=비활성
    max_holding_days: int = 20       # 0=비활성
    bollinger_period: int = 20
    bollinger_num_std: float = 2.0
    bollinger_volume_filter: bool
    use_minute_chart: bool           # 분봉/일봉 모드
    minute_short_period: int = 5
    minute_long_period: int = 20
    trailing_stop_pct: float = 0.0   # 고점 대비 N% 하락 시 매도 (0=비활성)
    capital_ratio: float = 0.0       # 예수금 대비 투자 비율 (0=target_order_amount 사용)
    auto_regime: bool = False        # 자동 국면 전환
```

## Trading Journal (매매 저널)

엔진이 생성하는 모든 시그널/주문/이벤트를 JSONL로 기록하고, 일일 HTML 리포트를 생성.

### 저장 경로

| 파일 | 경로 |
|------|------|
| 이벤트 로그 | `data/journal/logs/YYYY-MM-DD.jsonl` |
| 일일 리포트 | `data/journal/reports/YYYY-MM-DD.html` |

`TradingConfig.journal_dir`로 커스텀 경로 설정 가능 (빈 문자열이면 프로젝트 하위 `data/journal/logs/`).

### 이벤트 타입

| event_type | 시점 |
|-----------|------|
| `engine_start` | 엔진 시작 |
| `engine_stop` | 엔진 중지 |
| `signal` | 시그널 생성 시 (BUY/SELL/HOLD) |
| `order` | 매수/매도 주문 실행 |
| `force_close` | 장 마감 강제 청산 |
| `regime_change` | 시장 국면 변경 감지 |
| `strategy_change` | 전략 설정 변경 |

### 매도 사유 (reason)

| reason | 설명 |
|--------|------|
| `signal` | 전략 시그널 (데드크로스/볼린저 상단) |
| `stop_loss` | 손절 (매수가 대비 N% 하락) |
| `trailing_stop` | 트레일링 스탑 (고점 대비 N% 하락) |
| `max_holding` | 보유기간 초과 |
| `force_close` | 장 마감 강제 청산 |

### API

```bash
# 저널 날짜 목록
curl http://localhost:8000/trading/journal

# 특정 날짜 이벤트
curl http://localhost:8000/trading/journal/2026-02-14

# 일일 리포트 HTML
curl http://localhost:8000/trading/journal/2026-02-14/report
```

## Error Handling

- **연속 에러 정지**: tick에서 1개라도 종목 처리 실패 시 에러 카운터 증가, 연속 5회 시 엔진 자동 정지
- **잔고조회 재시도**: KIS 모의투자 서버의 간헐적 OPSQ2000 오류에 대해 최대 2회 재시도 (1초, 2초 백오프)
- **HTTP 재시도**: 429/5xx 응답 시 최대 3회 재시도 (1초, 2초, 4초 지수 백오프)
- **keep-alive 비활성화**: KIS API 서버의 커넥션 상태 간섭 방지
- **주문 Lock**: 종목별 asyncio.Lock으로 잔고확인→주문 원자성 보장

## KIS API TR_ID 참조 (모의투자)

| 기능 | TR_ID | API Path |
|------|-------|----------|
| 현재가 조회 | `FHKST01010100` | `/uapi/domestic-stock/v1/quotations/inquire-price` |
| 일봉 차트 | `FHKST03010100` | `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice` |
| 분봉 차트 | `FHKST03010200` | `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice` |
| 현금 매수 | `VTTC0802U` | `/uapi/domestic-stock/v1/trading/order-cash` |
| 현금 매도 | `VTTC0801U` | `/uapi/domestic-stock/v1/trading/order-cash` |
| 잔고 조회 | `VTTC8434R` | `/uapi/domestic-stock/v1/trading/inquire-balance` |

### KIS API 필수 헤더

```
Content-Type: application/json
authorization: Bearer {token}
appkey: {앱키}
appsecret: {앱시크릿}
custtype: "P" (개인)
tr_id: {TR코드}
tr_cont: "" (연속조회 키)
personalseckey: "" (필수 — 빈 문자열)
hashkey: {해시값} (POST 주문 API만)
```

## KIS MCP Server 설정

KIS Open API 코드 어시스턴트를 Claude Code에서 사용하려면 프로젝트 루트에 `.mcp.json` 파일을 생성한다.

### 설정 방법

프로젝트 루트에 `.mcp.json` 생성:
```json
{
  "mcpServers": {
    "kis-code-assistant": {
      "type": "http",
      "url": "https://kis-code-assistant-mcp--kisopenapi.run.tools"
    }
  }
}
```

### 제공 도구

| 도구 | 설명 |
|------|------|
| `search_auth_api` | 인증 (토큰 발급, 웹소켓 키) |
| `search_domestic_stock_api` | 국내주식 (시세, 호가, 주문, 잔고, 실시간) |
| `search_domestic_bond_api` | 국내채권 |
| `search_domestic_futureoption_api` | 국내선물옵션 |
| `search_overseas_stock_api` | 해외주식 |
| `search_overseas_futureoption_api` | 해외선물옵션 |
| `search_etfetn_api` | ETF/ETN |
| `search_elw_api` | ELW |
| `read_source_code` | KIS API 예제 소스코드 조회 |

## Critical Rules

- **절대 가짜 데이터 생성 금지**: API 실패 시 에러 반환
- **모의투자 전용**: 실전투자 TR_ID 사용 금지
- 전략 로직은 순수 함수로 유지 (외부 의존성 없음)

---

*Last Updated: 2026-02-14*
*Status: MVP - 국내주식 모의투자 자동매매 + 시장 국면 기반 전략 선택 + 매매 저널*
