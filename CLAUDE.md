# CLAUDE.md

## Project Overview

**Quantum Trading Platform** — 국내주식 모의투자 자동매매 시스템 (MVP)

Python + FastAPI 기반. KIS Open API 모의투자 환경에서 이동평균 크로스오버 전략으로 자동매매.

## Technology Stack

- **Python 3.13+**, FastAPI, Uvicorn
- **httpx**: KIS API 비동기 호출
- **Pydantic v2**: 데이터 모델 + 설정
- **pytest + pytest-asyncio**: 테스트
- **uv**: 패키지 관리

## Project Structure

```
quantum-trading-platform/
├── app/
│   ├── main.py                # FastAPI 진입점
│   ├── config.py              # 설정 (KIS API, 매매 파라미터)
│   ├── models.py              # Pydantic 데이터 모델
│   ├── kis/                   # KIS API 클라이언트
│   │   ├── client.py          # HTTP 클라이언트 (재시도, rate limit)
│   │   ├── auth.py            # 토큰 발급/관리 (메모리 캐싱)
│   │   ├── market.py          # 현재가/차트 조회
│   │   └── order.py           # 매수/매도 주문, 잔고 조회
│   ├── trading/               # 자동매매 핵심
│   │   ├── engine.py          # 자동매매 루프 (시작/중지/상태)
│   │   ├── strategy.py        # 이동평균 크로스오버 전략
│   │   └── calendar.py        # 매매일/장시간 판단
│   └── api/
│       └── routes.py          # API 엔드포인트
├── tests/
│   ├── test_strategy.py       # 전략 로직 단위 테스트
│   ├── test_engine.py         # 엔진 로직 단위 테스트
│   ├── test_calendar.py       # 매매일/장시간 단위 테스트
│   └── test_kis_client.py     # KIS API 통합 테스트
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

### Run Strategy Tests Only
```bash
uv run pytest tests/test_strategy.py -v
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | 헬스체크 |
| GET | `/market/price/{symbol}` | 종목 현재가 |
| POST | `/trading/start` | 자동매매 시작 (body: `{"symbols": ["005930"]}`) |
| POST | `/trading/stop` | 자동매매 중지 |
| GET | `/trading/status` | 엔진 상태/시그널/주문 이력 |
| GET | `/trading/positions` | 보유 포지션 |

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

## Trading Strategy

**이동평균 크로스오버 (SMA Crossover)**
- 단기: SMA(5), 장기: SMA(20)
- 골든크로스 (SMA5가 SMA20 상향돌파) → **매수**
- 데드크로스 (SMA5가 SMA20 하향돌파) → **매도**
- 장 시간: 09:00 ~ 15:20, 주기: 1분

## KIS API TR_ID 참조 (모의투자)

| 기능 | TR_ID | API Path |
|------|-------|----------|
| 현재가 조회 | `FHKST01010100` | `/uapi/domestic-stock/v1/quotations/inquire-price` |
| 일봉 차트 | `FHKST03010100` | `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice` |
| 현금 매수 | `VTTC0802U` | `/uapi/domestic-stock/v1/trading/order-cash` |
| 현금 매도 | `VTTC0801U` | `/uapi/domestic-stock/v1/trading/order-cash` |
| 잔고 조회 | `VTTC8434R` | `/uapi/domestic-stock/v1/trading/inquire-balance` |

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

### 사용 예시

Claude Code에서 KIS API 관련 질문을 하면 MCP 도구가 자동으로 호출됨:
- "삼성전자 현재가 조회 코드 짜줘" → `search_domestic_stock_api` 호출
- "해외주식 잔고 조회 방법 알려줘" → `search_overseas_stock_api` 호출
- "토큰 발급 코드 보여줘" → `search_auth_api` 호출

### 주의사항

- `.mcp.json`은 `.gitignore`에 추가하지 않음 (팀 공유 설정)
- MCP 서버는 외부 호스팅이므로 별도 설치 불필요
- API 키/시크릿은 MCP에 전달되지 않음 (코드 검색용도만)

## Critical Rules

- **절대 가짜 데이터 생성 금지**: API 실패 시 에러 반환
- **모의투자 전용**: 실전투자 TR_ID 사용 금지
- 전략 로직은 순수 함수로 유지 (외부 의존성 없음)

---

*Last Updated: 2026-02-13*
*Status: MVP - 국내주식 모의투자 자동매매*
