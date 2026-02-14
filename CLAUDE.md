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
│   ├── config.py              # 설정 (KIS API, 매매 파라미터)
│   ├── models.py              # Pydantic 데이터 모델
│   ├── kis/                   # KIS API 클라이언트
│   │   ├── client.py          # HTTP 클라이언트 (재시도, rate limit, keep-alive 비활성화)
│   │   ├── auth.py            # 토큰 발급/관리 (파일 캐싱: ~/.cache/kis/token.json)
│   │   ├── market.py          # 현재가/일봉/분봉 차트 조회
│   │   └── order.py           # 매수/매도 주문, 잔고 조회 (OPSQ2000 재시도)
│   ├── trading/               # 자동매매 핵심
│   │   ├── engine.py          # 자동매매 루프 (분봉/일봉, 동적수량, 부분실패 감지)
│   │   ├── strategy.py        # SMA 크로스오버 + RSI/거래량/OBV 복합 전략
│   │   ├── backtest.py        # 백테스트 엔진 (yfinance 기반)
│   │   └── calendar.py        # 매매일/장시간 판단
│   └── api/
│       └── routes.py          # API 엔드포인트 (매매 + 백테스트)
├── scripts/                   # 백테스트 최적화 스크립트
│   ├── optimize.sh            # 파라미터 탐색 실행
│   ├── run_backtest.py        # 단일 백테스트 실행
│   └── generate_report.py     # 최적화 결과 리포트
├── tests/
│   ├── test_strategy.py       # 전략 로직 단위 테스트 (29개)
│   ├── test_engine.py         # 엔진 로직 + E2E 테스트 (19개)
│   ├── test_calendar.py       # 매매일/장시간 단위 테스트 (14개)
│   ├── test_backtest.py       # 백테스트 단위 테스트
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
uv run pytest tests/test_strategy.py tests/test_engine.py tests/test_calendar.py -v
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
- 효성중공업 240만원 → 1주, 두산에너빌리티 2만원 → 50주, 삼성전자 5.5만원 → 18주

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
*Status: MVP - 국내주식 모의투자 자동매매*
