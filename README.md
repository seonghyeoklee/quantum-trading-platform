# Quantum Trading Platform

국내/해외(미국)주식 모의투자 자동매매 시스템

Python + FastAPI 기반. KIS Open API 모의투자 환경에서 SMA 크로스오버 + RSI/거래량/OBV 복합 전략 및 볼린저 밴드 전략으로 자동매매를 수행합니다. 국내(KRX) + 미국(NASDAQ/NYSE/AMEX) 동시 지원.

## Features

- **분봉/일봉 기반 자동매매** — 1분봉 장중 데이트레이딩 또는 일봉 스윙 트레이딩
- **복합 전략** — SMA 크로스오버 + RSI/거래량/OBV 필터, 볼린저 밴드 전략
- **시장 국면 판별** — SMA 정배열/역배열 기반 강세/약세/횡보 분류 → 최적 전략 자동 전환
- **국내 + 미국 동시 지원** — 장 시간 자동 판별, 24시간 운영 가능
- **리스크 관리** — 손절, 트레일링 스탑, 최대 보유일 제한, 동적 주문수량
- **백테스트** — yfinance 기반 과거 데이터 시뮬레이션 + 국면별 분할 백테스트
- **매매 저널** — JSONL 이벤트 로깅 + HTML 일일 리포트
- **실시간 대시보드** — 브라우저 폴링 기반 모니터링 UI
- **런타임 전략 전환** — 재시작 없이 API로 전략 변경

## Tech Stack

| 구성요소 | 기술 |
|---------|------|
| Language | Python 3.13+ |
| Framework | FastAPI + Uvicorn |
| HTTP Client | httpx (비동기) |
| Data Model | Pydantic v2 |
| Test | pytest + pytest-asyncio |
| Package | uv |
| Deploy | Docker |

## Quick Start

### 1. 설치

```bash
git clone <repository-url>
cd quantum-trading-platform
uv sync --extra dev
```

백테스트를 사용하려면:

```bash
uv sync --extra dev --extra backtest
```

### 2. KIS API 설정

**모의투자 전용** (`openapivts.koreainvestment.com:29443`)

`~/KIS/config/kis_devlp.yaml` 파일 생성:

```yaml
paper_app: "모의투자_앱키"
paper_sec: "모의투자_앱시크릿"
my_paper_stock: "모의투자_계좌번호_8자리"
my_prod: "01"
my_htsid: "HTS_ID"
```

또는 환경변수 사용:

```bash
export KIS_APP_KEY="앱키"
export KIS_APP_SECRET="앱시크릿"
export KIS_ACCOUNT_NO="계좌번호"
```

### 3. 서버 실행

```bash
uv run python -m app.main
# → http://localhost:8000
```

### 4. 자동매매 시작

```bash
# 국내주식만
curl -X POST http://localhost:8000/trading/start \
  -H "Content-Type: application/json" \
  -d '{"market": "domestic"}'

# 미국주식만
curl -X POST http://localhost:8000/trading/start \
  -H "Content-Type: application/json" \
  -d '{"market": "us"}'

# 종목 지정
curl -X POST http://localhost:8000/trading/start \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["005930", "AAPL"], "market": null}'
```

### 5. 대시보드

브라우저에서 http://localhost:8000/dashboard 접속

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | 실시간 트레이딩 대시보드 (HTML) |
| GET | `/health` | 헬스체크 |
| GET | `/market/price/{symbol}` | 종목 현재가 조회 |
| POST | `/trading/start` | 자동매매 시작 |
| POST | `/trading/stop` | 자동매매 중지 |
| GET | `/trading/status` | 엔진 상태/시그널/주문 이력 |
| GET | `/trading/positions` | 보유 포지션 + 계좌 요약 |
| GET | `/trading/strategy` | 현재 전략 설정 조회 |
| POST | `/trading/strategy` | 전략 런타임 변경 |
| GET | `/trading/journal` | 저널 날짜 목록 |
| GET | `/trading/journal/{date}` | 특정 날짜 이벤트 조회 |
| GET | `/trading/journal/{date}/report` | 일일 리포트 HTML |
| POST | `/backtest` | 과거 데이터 백테스트 |

## Trading Strategies

### SMA 크로스오버 (기본)

단기/장기 이동평균선 교차로 매매 시그널 생성.

- **분봉 모드**: SMA(5분) / SMA(20분) — 장중 데이트레이딩
- **일봉 모드**: SMA(10) / SMA(40) — 스윙 트레이딩
- 골든크로스 → 매수, 데드크로스 → 매도

### 복합 전략 (SMA + RSI/거래량/OBV)

크로스오버 시그널에 추가 필터를 적용하여 오시그널 감소:

- RSI 과매수(70)/과매도(30) 영역에서 역방향 시그널 차단
- 거래량 SMA 대비 확인
- OBV 추세 확인

### 볼린저 밴드

볼린저 밴드 상하단 기반 역추세 매매. 횡보장에서 유리.

## Market Regime Detection

SMA(20/60/120) 배열로 시장 국면을 판별하고, 국면에 맞는 전략을 선택합니다.

| 국면 | 조건 | 추천 전략 |
|------|------|----------|
| 강한 상승 | 완전 정배열 (`last > SMA20 > SMA60 > SMA120`) | B&H 또는 SMA 기본 |
| 상승 | `last > SMA60`, `SMA20 > SMA60` | SMA 기본 |
| 횡보 | SMA 엇갈림 | 볼린저 |
| 하락 | `last < SMA60`, `SMA20 < SMA60` | SMA+리스크 관리 |
| 강한 하락 | 완전 역배열 | 볼린저 (보수적) |

```bash
# 국면 분석 리포트 생성
uv run python scripts/generate_regime_report.py
# → regime_strategy_report.html
```

## Risk Management

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `stop_loss_pct` | 매수가 대비 N% 하락 시 손절 | 5.0 |
| `trailing_stop_pct` | 고점 대비 N% 하락 시 매도 | 0 (비활성) |
| `max_holding_days` | 최대 보유 거래일 초과 시 매도 | 20 |
| `capital_ratio` | 예수금 대비 투자 비율 | 0 (고정금액) |
| `target_order_amount` | 종목당 주문금액 (원) | 1,000,000 |

## Project Structure

```
quantum-trading-platform/
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── config.py            # 설정 + StrategyConfig
│   ├── models.py            # Pydantic 데이터 모델
│   ├── dashboard.py         # 실시간 대시보드 HTML
│   ├── report_theme.py      # 공통 HTML 리포트 테마
│   ├── kis/                 # KIS API 클라이언트
│   │   ├── client.py        # HTTP 클라이언트
│   │   ├── auth.py          # 토큰 발급/관리
│   │   ├── market.py        # 국내주식 시세
│   │   ├── order.py         # 국내주식 주문/잔고
│   │   ├── overseas_market.py  # 해외주식 시세
│   │   └── overseas_order.py   # 해외주식 주문/잔고
│   ├── trading/             # 자동매매 핵심
│   │   ├── engine.py        # 자동매매 루프
│   │   ├── strategy.py      # 매매 전략
│   │   ├── regime.py        # 시장 국면 판별
│   │   ├── journal.py       # 매매 저널
│   │   ├── backtest.py      # 백테스트 엔진
│   │   └── calendar.py      # 매매일/장시간 판단
│   └── api/
│       └── routes.py        # API 엔드포인트
├── scripts/                 # 분석/리포트 스크립트
├── tests/                   # 테스트 (200+ 케이스)
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Development

### 테스트 실행

```bash
# 전체 테스트
uv run pytest tests/ -v

# 단위 테스트만 (KIS API 키 불필요)
uv run pytest tests/test_strategy.py tests/test_engine.py tests/test_calendar.py tests/test_regime.py tests/test_journal.py -v
```

### Docker

```bash
docker compose up -d      # 서버 기동
docker compose logs -f    # 로그 확인
docker compose down       # 종료
```

### 리포트 생성

```bash
# 국면 기반 전략 비교 리포트
uv run python scripts/generate_regime_report.py

# 전략 비교 리포트
uv run python scripts/generate_comparison_report.py

# 일일 매매 저널 리포트
uv run python scripts/generate_daily_report.py              # 오늘
uv run python scripts/generate_daily_report.py 2026-02-14   # 특정 날짜
```

## License

MIT
