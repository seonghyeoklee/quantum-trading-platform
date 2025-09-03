# KIS Adapter API Reference

## Overview

KIS Adapter는 한국투자증권(KIS) Open API를 RESTful API 형태로 제공하는 FastAPI 기반 어댑터 서비스입니다. 국내외 주식 시세 조회, 차트 데이터, 종목 정보 등을 통합된 인터페이스로 제공합니다.

**서비스 포트**: `8000`  
**문서 URL**: `http://localhost:8000/docs` (Swagger UI)  
**Base URL**: `http://localhost:8000`

## Trading Mode (거래 모드)

KIS Adapter는 실전투자와 모의투자 환경을 동적으로 전환할 수 있는 Trading Mode 기능을 지원합니다.

### 지원 모드

| 모드 | 값 | 서버 환경 | 설명 |
|------|-----|-----------|------|
| **실전투자** | `LIVE` | prod | 실제 KIS 서버 (openapi.koreainvestment.com:9443) |
| **모의투자** | `SANDBOX` | vps | KIS VPS 서버 (openapivts.koreainvestment.com:29443) |

### 사용 방법

모든 API 엔드포인트에서 `trading_mode` 쿼리 파라미터를 사용할 수 있습니다:

```http
# 기본값 (모의투자)
GET /domestic/price/005930

# 명시적 모의투자
GET /domestic/price/005930?trading_mode=SANDBOX

# 실전투자
GET /domestic/price/005930?trading_mode=LIVE
X-KIS-Token: YOUR_LIVE_ACCESS_TOKEN
```

### 기본값 및 검증

- **기본값**: `SANDBOX` (안전한 모의투자 환경)
- **유효성 검증**: `LIVE` 또는 `SANDBOX`만 허용
- **잘못된 값**: HTTP 422 에러 반환

```json
// 잘못된 trading_mode 사용 시 응답
{
  "detail": [
    {
      "loc": ["query", "trading_mode"],
      "msg": "string should match pattern '^(LIVE|SANDBOX)$'",
      "type": "value_error.regex"
    }
  ]
}
```

## Authentication

KIS Adapter는 **우선순위 기반 이중 인증 시스템**을 사용합니다.

### 인증 우선순위

1. **X-KIS-Token 헤더** (최우선)
2. **kis_devlp.yaml 설정 파일** (대체 수단)

### Header 기반 인증 (우선순위 1)
```http
X-KIS-Token: YOUR_ACCESS_TOKEN_HERE
```

헤더를 통해 KIS API 액세스 토큰을 전달할 수 있습니다. 이 방식이 최우선 순위로 적용됩니다.

### 설정 파일 인증 (우선순위 2)
헤더가 없으면 `kis_devlp.yaml` 설정 파일의 기본 인증 정보를 자동으로 사용합니다.

**장점**:
- 헤더 인증: 동적 토큰 관리, 다중 사용자 지원
- 설정 파일: 간편한 개발 환경, 자동 대체

## Response Format

모든 API는 다음과 같은 통일된 응답 형식을 사용합니다:

```json
{
  "success": true,
  "data": {
    // 실제 데이터
  },
  "message": "성공적으로 조회되었습니다",
  "timestamp": "2024-12-02T10:30:00Z"
}
```

## API Endpoints

### Trading Mode 지원 현황

✅ **모든 17개 API가 Trading Mode를 지원합니다**

| 카테고리 | API 개수 | 엔드포인트 |
|----------|---------|------------|
| **국내 주식** | 6개 | price, chart/daily, chart/minute, orderbook, info, search |
| **국내 지수** | 3개 | indices/domestic, chart/daily, chart/minute |
| **해외 주식** | 5개 | price, chart/daily, chart/minute, info, search |
| **해외 지수** | 3개 | indices/overseas, chart/daily, chart/minute |
| **총계** | **17개** | **모든 API가 trading_mode 파라미터 지원** |

### 통합 파라미터 스펙

모든 API 엔드포인트에서 다음 파라미터를 공통으로 지원합니다:

```yaml
trading_mode:
  type: string
  default: "SANDBOX"
  pattern: "^(LIVE|SANDBOX)$"
  description: "거래 모드: LIVE(실전투자) | SANDBOX(모의투자)"
  
x_kis_token:
  type: string
  in: header
  required: false
  description: "KIS API 인증 토큰 (선택사항)"
```

### 1. 서비스 정보

#### Health Check
```http
GET /health
```
서비스 상태를 확인합니다.

#### API 정보
```http
GET /
```
사용 가능한 모든 API 엔드포인트 목록을 반환합니다.

---

### 2. 국내 주식 시세

#### 현재가 조회
```http
GET /domestic/price/{symbol}
```

**Parameters:**
- `symbol` (path): 종목코드 (예: 005930)
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:
- 현재가, 전일대비, 등락률
- 시가, 고가, 저가, 상한가, 하한가
- 거래량, 거래대금
- PER, PBR, EPS, BPS
- 52주 고가/저가, 외국인 보유율

**Example:**
```bash
curl -X GET "http://localhost:8000/domestic/price/005930?trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 호가정보 조회
```http
GET /domestic/orderbook/{symbol}
```

**Parameters:**
- `symbol` (path): 종목코드 (예: 005930)
- `market` (query, optional): 시장구분 (J: KRX, NX: NXT, UN: 통합) - 기본값: J
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 매수/매도 10단계 호가와 잔량
- 총 매수/매도 잔량 및 건수
- 현재가 대비 호가 비교 정보
- 시간외 호가 정보

**Example:**
```bash
curl -X GET "http://localhost:8000/domestic/orderbook/005930?market=J&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

---

### 3. 국내 주식 기본정보

#### 종목 기본정보 조회
```http
GET /domestic/info/{symbol}
```

**Parameters:**
- `symbol` (path): 종목코드 (예: 005930)
- `product_type` (query, optional): 상품유형코드 - 기본값: 300
  - 300: 주식/ETF/ETN/ELW
  - 301: 선물옵션
  - 302: 채권
  - 306: ELS
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 종목명, 종목코드, 시장구분
- 업종분류, 상장주식수, 액면가
- 자본금, 시가총액, 발행주식수
- 외국인 한도, 대주주 정보
- 결산월, 공시구분 등 기업정보

**Example:**
```bash
curl -X GET "http://localhost:8000/domestic/info/005930?product_type=300&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 종목 검색
```http
GET /domestic/search
```

**Parameters:**
- `symbol` (query, required): 검색할 종목코드 또는 심볼
- `product_type` (query, optional): 상품유형코드 - 기본값: 300
  - 300: 주식/ETF/ETN/ELW
  - 301: 선물옵션
  - 302: 채권
  - 306: ELS
  - 512: 해외주식
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 종목명, 종목코드, 심볼
- 시장구분, 상품구분
- 매칭된 종목들의 기본 정보

**Example:**
```bash
curl -X GET "http://localhost:8000/domestic/search?symbol=삼성전자&product_type=300&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

---

### 4. 국내 주식 차트

#### 일봉/주봉/월봉 차트 조회
```http
GET /domestic/chart/daily/{symbol}
```

**Parameters:**
- `symbol` (path): 종목코드 (예: 005930)
- `period` (query, optional): 차트 주기 (D: 일봉, W: 주봉, M: 월봉) - 기본값: D
- `start_date` (query, optional): 시작일 (YYYYMMDD)
- `end_date` (query, optional): 종룼일 (YYYYMMDD)
- `count` (query, optional): 조회 건수 - 기본값: 100
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가)
- 거래량, 거래대금
- 최대 100건까지 조회 가능

**Example:**
```bash
curl -X GET "http://localhost:8000/domestic/chart/daily/005930?period=D&count=30&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 분봉 차트 조회
```http
GET /domestic/chart/minute/{symbol}
```

**Parameters:**
- `symbol` (path): 종목코드 (예: 005930)
- `time_div` (query, optional): 분봉 단위 (1, 3, 5, 10, 15, 30, 60) - 기본값: 1
- `start_time` (query, optional): 시작시간 (HHMMSS) - 기본값: 090000
- `end_time` (query, optional): 종료시간 (HHMMSS) - 기본값: 153000
- `trading_mode` (query, optional): 거래 모드 - 기본가: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가)
- 거래량
- 분봉별 히스토리 데이터

**Example:**
```bash
curl -X GET "http://localhost:8000/domestic/chart/minute/005930?time_div=5&start_time=090000&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

---

### 5. 국내 시장지수

#### 시장지수 조회
```http
GET /indices/domestic
```

**Parameters:**
- `index_code` (query, optional): 지수코드 - 기본값: 0001
  - 0001: KOSPI (코스피)
  - 1001: KOSDAQ (코스닥)
  - 2001: KOSPI200 (코스피200)
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 현재 지수 값, 전일대비, 등락률
- 시가, 고가, 저가 지수
- 거래량, 거래대금
- 상승/하락 종목수
- 지수 구성 시가총액 정보

**Example:**
```bash
curl -X GET "http://localhost:8000/indices/domestic?index_code=0001&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 국내 지수 일봉/주봉/월봉 차트 조회
```http
GET /indices/domestic/chart/daily/{index_code}
```

**Parameters:**
- `index_code` (path): 지수코드 (예: 0001)
- `start_date` (query, required): 시작일 (YYYYMMDD)
- `end_date` (query, required): 종료일 (YYYYMMDD) 
- `period` (query, optional): 기간구분 (D:일봉, W:주봉, M:월봉, Y:년봉) - 기본값: D
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가) 지수
- 거래량 정보
- 날짜별 히스토리 데이터

**Example:**
```bash
curl -X GET "http://localhost:8000/indices/domestic/chart/daily/0001?start_date=20241201&end_date=20241231&period=D&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 국내 지수 분봉 차트 조회
```http
GET /indices/domestic/chart/minute/{index_code}
```

**Parameters:**
- `index_code` (path): 지수코드 (예: 0001)
- `time_div` (query, optional): 분봉 단위 (30, 60, 600, 3600) - 기본값: 30
- `include_past` (query, optional): 과거 데이터 포함 여부 (Y: 포함, N: 당일만) - 기본값: Y
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가) 지수
- 거래량 정보  
- 분봉별 히스토리 데이터

**Example:**
```bash
curl -X GET "http://localhost:8000/indices/domestic/chart/minute/0001?time_div=30&include_past=Y&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

---

### 6. 해외 주식

#### 해외 주식 현재가 조회
```http
GET /overseas/{exchange}/price/{symbol}
```

**Parameters:**
- `exchange` (path): 거래소 코드
  - NYS: 뉴욕증권거래소 (NYSE)
  - NAS: 나스닥 (NASDAQ)
  - AMS: 아메렉스 (AMEX)
  - TSE: 도쿄증권거래소
  - HKS: 홍콩증권거래소
  - SHS: 상하이증권거래소
  - SZS: 선전증권거래소
  - LSE: 런던증권거래소
- `symbol` (path): 종목 심볼 (예: AAPL)
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 현재가, 전일대비, 등락률 (현지 통화)
- 시가, 고가, 저가
- 거래량, 거래대금
- 52주 고가/저가
- 시가총액

**Example:**
```bash
curl -X GET "http://localhost:8000/overseas/NYS/price/AAPL?trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 해외 주식 일봉 차트 조회
```http
GET /overseas/{exchange}/chart/daily/{symbol}
```

**Parameters:**
- `exchange` (path): 거래소 코드
- `symbol` (path): 종목 심볼 (예: AAPL)
- `start_date` (query, required): 시작일 (YYYYMMDD)
- `end_date` (query, required): 종료일 (YYYYMMDD)
- `period` (query, optional): 차트 주기 (D: 일봉, W: 주봉, M: 월봉) - 기본값: D
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가) - 현지 통화
- 거래량
- 날짜별 히스토리 데이터

**Example:**
```bash
curl -X GET "http://localhost:8000/overseas/NYS/chart/daily/AAPL?start_date=20241201&end_date=20241231&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 해외 주식 분봉 차트 조회
```http
GET /overseas/{exchange}/chart/minute/{symbol}
```

**Parameters:**
- `exchange` (path): 거래소 코드
- `symbol` (path): 종목 심볼 (예: AAPL)
- `nmin` (query, optional): 분봉 단위 (1, 3, 5, 10, 15, 30, 60) - 기본값: 1
- `pinc` (query, optional): 전일포함여부 (0: 미포함, 1: 포함) - 기본값: 1
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가) - 현지 통화
- 거래량
- 분봉별 히스토리 데이터

**Example:**
```bash
curl -X GET "http://localhost:8000/overseas/NYS/chart/minute/AAPL?nmin=5&pinc=1&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

---

### 7. 해외 주식 기본정보

#### 해외 주식 기본정보 조회
```http
GET /overseas/{exchange}/info/{symbol}
```

**Parameters:**
- `exchange` (path): 거래소 코드
  - NYS: 뉴욕증권거래소 (NYSE)
  - NAS: 나스닥 (NASDAQ)
  - AMS: 아메렉스 (AMEX)
  - TSE: 도쿄증권거래소
  - HKS: 홍콩증권거래소
  - SHS: 상하이증권거래소
  - SZS: 선전증권거래소
- `symbol` (path): 종목 심볼 (예: AAPL, TSLA, 6758)
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 종목명, 종목 심볼, 거래소 정보
- 업종, 섹터 분류 정보
- 상장 정보 및 기업 개요
- 발행주식수, 시가총액
- 기타 기본 재무 정보

**Example:**
```bash
curl -X GET "http://localhost:8000/overseas/NYS/info/AAPL?trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 해외 주식 검색
```http
GET /overseas/{exchange}/search
```

**Parameters:**
- `exchange` (path): 거래소 코드
- `symbol` (query, optional): 종목 심볼 검색
- `schz_bnti_qty` (query, optional): 거래단위 수량
- `rsp_tp` (query, optional): 응답 유형 (0: 전체, 1: 요약)
- `start_rank` (query, optional): 시작 순위
- `end_rank` (query, optional): 종료 순위
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 검색된 종목들의 기본 정보
- 종목 심볼, 종목명, 거래소
- 현재가, 등락률 (조건에 따라)
- 거래량 및 시가총액 정보

**Example:**
```bash
curl -X GET "http://localhost:8000/overseas/NAS/search?symbol=AAPL&rsp_tp=0&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

---

### 8. 해외 시장지수

#### 해외 시장지수 조회
```http
GET /indices/overseas/{exchange}
```

**Parameters:**
- `exchange` (path): 거래소/지역 코드
  - US: 미국 시장
  - JP: 일본 시장
  - HK: 홍콩 시장
  - CN: 중국 시장
- `index_code` (query, required): 지수 코드
  - 미국: SPX (S&P500), DJI (다우존스), NDX (나스닥종합), RUT (러셀2000)
  - 일본: N225 (니케이225), TPX (도쿄증권거래소)
  - 홍콩: HSI (항셍지수), HSCEI (H주지수)
  - 중국: SHCOMP (상해종합), SZCOMP (심천종합)
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- 현재 지수 값, 전일대비, 등락률
- 시가, 고가, 저가 지수
- 거래량 및 거래대금
- 지수 구성 정보

**Example:**
```bash
curl -X GET "http://localhost:8000/indices/overseas/US?index_code=SPX&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 해외 지수 일봉 차트 조회
```http
GET /indices/overseas/{exchange}/chart/daily/{index_code}
```

**Parameters:**
- `exchange` (path): 거래소/지역 코드
- `index_code` (path): 지수 코드
- `start_date` (query, required): 시작일 (YYYYMMDD)
- `end_date` (query, required): 종료일 (YYYYMMDD)
- `period` (query, optional): 차트 주기 (D: 일봉, W: 주봉, M: 월봉) - 기본값: D
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가) 지수 값
- 거래량 정보
- 날짜별 히스토리 데이터

**Example:**
```bash
curl -X GET "http://localhost:8000/indices/overseas/US/chart/daily/SPX?start_date=20241201&end_date=20241231&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

#### 해외 지수 분봉 차트 조회
```http
GET /indices/overseas/{exchange}/chart/minute/{index_code}
```

**Parameters:**
- `exchange` (path): 거래소/지역 코드
- `index_code` (path): 지수 코드
- `nmin` (query, optional): 분봉 단위 (1, 3, 5, 10, 15, 30, 60) - 기본값: 1
- `pinc` (query, optional): 전일포함여부 (0: 미포함, 1: 포함) - 기본값: 1
- `trading_mode` (query, optional): 거래 모드 - 기본값: SANDBOX
  - LIVE: 실전투자 모드
  - SANDBOX: 모의투자 모드
- `X-KIS-Token` (header, optional): KIS API 인증 토큰

**Response Data:**
- OHLC (시가, 고가, 저가, 종가) 지수 값
- 거래량 정보
- 분봉별 히스토리 데이터

**Example:**
```bash
curl -X GET "http://localhost:8000/indices/overseas/US/chart/minute/DJI?nmin=5&pinc=1&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN"
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "data": null,
  "message": "에러 메시지",
  "timestamp": "2024-12-02T10:30:00Z"
}
```

### Common Error Codes

| HTTP Status | Description | 해결방법 |
|-------------|-------------|----------|
| 400 | Bad Request | 요청 파라미터를 확인하세요 |
| 401 | Unauthorized | KIS API 토큰을 확인하세요 |
| 404 | Not Found | 종목코드나 거래소 코드를 확인하세요 |
| 500 | Internal Server Error | 서버 로그를 확인하고 관리자에게 문의하세요 |
| 503 | Service Unavailable | KIS 모듈 설정을 확인하세요 |

## Rate Limiting

KIS API의 호출 제한이 적용됩니다:
- **현재가 조회**: 초당 20회 (국내/해외)
- **호가 조회**: 초당 5회 (국내)
- **차트 조회**: 분당 200회 (국내/해외)
- **종목 기본정보**: 분당 100회 (국내/해외)
- **종목 검색**: 분당 50회 (국내/해외)
- **시장지수**: 분당 100회 (국내/해외)
- **기타 API**: 분당 100회

## Usage Examples

### Python Example
```python
import requests

# 삼성전자 현재가 조회
response = requests.get(
    "http://localhost:8000/domestic/price/005930",
    headers={"X-KIS-Token": "your_token_here"}
)

data = response.json()
if data["success"]:
    print(f"삼성전자 현재가: {data['data']}")
else:
    print(f"에러: {data['message']}")
```

### JavaScript Example
```javascript
// 애플 주식 현재가 조회
fetch("http://localhost:8000/overseas/NYS/price/AAPL", {
    headers: {
        "X-KIS-Token": "your_token_here"
    }
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log("애플 현재가:", data.data);
    } else {
        console.error("에러:", data.message);
    }
});

// 애플 기본정보 조회
fetch("http://localhost:8000/overseas/NYS/info/AAPL", {
    headers: {
        "X-KIS-Token": "your_token_here"
    }
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log("애플 기본정보:", data.data);
    } else {
        console.error("에러:", data.message);
    }
});

// S&P 500 지수 조회
fetch("http://localhost:8000/indices/overseas/US?index_code=SPX", {
    headers: {
        "X-KIS-Token": "your_token_here"
    }
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log("S&P 500:", data.data);
    } else {
        console.error("에러:", data.message);
    }
});
```

### cURL Example
```bash
# 코스피 지수 조회
curl -X GET "http://localhost:8000/indices/domestic?index_code=0001&trading_mode=LIVE" \
  -H "accept: application/json" \
  -H "X-KIS-Token: your_token_here"

# 국내 지수 일봉 차트 (코스피)
curl -X GET "http://localhost:8000/indices/domestic/chart/daily/0001?start_date=20241201&end_date=20241231&period=D&trading_mode=LIVE" \
  -H "accept: application/json" \
  -H "X-KIS-Token: your_token_here"

# 국내 지수 분봉 차트 (코스닥 30분봉)
curl -X GET "http://localhost:8000/indices/domestic/chart/minute/1001?time_div=30&include_past=Y&trading_mode=LIVE" \
  -H "accept: application/json" \
  -H "X-KIS-Token: your_token_here"

# 해외 주식 기본정보 조회 (애플)
curl -X GET "http://localhost:8000/overseas/NYS/info/AAPL?trading_mode=LIVE" \
  -H "accept: application/json" \
  -H "X-KIS-Token: your_token_here"

# 해외 주식 검색 (나스닥)
curl -X GET "http://localhost:8000/overseas/NAS/search?symbol=AAPL&rsp_tp=0&trading_mode=LIVE" \
  -H "accept: application/json" \
  -H "X-KIS-Token: your_token_here"

# S&P 500 지수 조회
curl -X GET "http://localhost:8000/indices/overseas/US?index_code=SPX&trading_mode=LIVE" \
  -H "X-KIS-Token: YOUR_TOKEN" \
  -H "accept: application/json" \
  -H "X-KIS-Token: your_token_here"

# 해외 지수 일봉 차트 (니케이 225)
curl -X GET "http://localhost:8000/indices/overseas/JP/chart/daily/N225?start_date=20241201&end_date=20241231&trading_mode=LIVE" \
  -H "accept: application/json" \
  -H "X-KIS-Token: your_token_here"
```

## Development Notes

1. **토큰 없이 사용**: 헤더 없이도 `kis_devlp.yaml` 설정으로 기본 동작
2. **CORS 지원**: 웹 애플리케이션에서 직접 호출 가능
3. **자동 문서화**: `/docs` 에서 Swagger UI 제공
4. **타입 안정성**: Pydantic 모델로 응답 데이터 검증
5. **에러 로깅**: 모든 에러는 서버 로그에 기록됨
6. **해외 시장 지원**: 미국, 일본, 홍콩, 중국 등 7개 거래소 지원
7. **글로벌 지수**: S&P500, 다우존스, 니케이225, 항셍지수 등 주요 지수 제공
8. **종목 검색**: 해외 주식 조건부 검색 및 필터링 기능
9. **실시간 데이터**: 해외 주식 기본정보 및 시장지수 실시간 조회
10. **국내 지수 차트**: 코스피/코스닥/코스피200 등 일/주/월/년봉 및 분봉 차트
11. **해외 지수 차트**: 글로벌 주요 지수 일봉/분봉 차트 데이터 제공

## Trading Mode 사용 가이드

### 시나리오별 활용 예시

#### 1. 개발/테스트 환경
```bash
# 기본값 사용 (SANDBOX)
curl "http://localhost:8000/domestic/price/005930"

# 명시적 SANDBOX 지정
curl "http://localhost:8000/domestic/price/005930?trading_mode=SANDBOX"
```

#### 2. 프로덕션 환경 (실전투자)
```bash
# LIVE 모드 + 토큰
curl "http://localhost:8000/domestic/price/005930?trading_mode=LIVE" \
     -H "X-KIS-Token: YOUR_LIVE_ACCESS_TOKEN"
```

#### 3. 백엔드 API 통합
```kotlin
// Spring Boot RestTemplate 패턴
val response = restTemplate.getForObject(
    "http://localhost:8000/domestic/price/{symbol}?trading_mode={mode}",
    ApiResponse::class.java,
    mapOf("symbol" to "005930", "mode" to "LIVE")
)
```

#### 4. 프론트엔드 통합
```javascript
// JavaScript fetch 패턴
const response = await fetch(
  `http://localhost:8000/domestic/price/005930?trading_mode=LIVE`,
  {
    headers: { 'X-KIS-Token': kisToken }
  }
);
```

### 모드별 주의사항

#### LIVE 모드 (실전투자)
- ⚠️ **실제 거래 데이터**: 실제 주식 시장 데이터를 사용합니다
- 🔒 **인증 필수**: X-KIS-Token 헤더 권장
- 💰 **비용 발생**: KIS API 호출 비용이 발생할 수 있습니다
- 📊 **실시간 데이터**: 실제 시장 데이터 반영

#### SANDBOX 모드 (모의투자)
- ✅ **안전한 테스트**: 실제 거래에 영향 없음
- 🆓 **무료 사용**: 대부분의 호출이 무료입니다
- 🎭 **모의 데이터**: KIS VPS 서버의 모의 데이터 사용
- 🚀 **개발 친화적**: 제한 없는 테스트 가능

### 성능 고려사항

#### Rate Limiting
- **LIVE 모드**: 20 calls/second
- **SANDBOX 모드**: 2 calls/second
- **WebSocket**: 최대 41개 동시 등록

#### 토큰 관리
- **유효기간**: KIS 토큰 6시간
- **재발급**: 분당 1회 제한
- **캐싱**: 토큰 재사용 권장

## Support

- **문서**: `/docs` (Swagger UI)
- **설정 파일**: `kis_devlp.yaml`
- **로그 파일**: 애플리케이션 로그 확인
- **테스트 파일**: `test_with_headers.http`
- **개발자 가이드**: `docs/planning/TRADING_MODE_GUIDE.md`
- **기술 명세서**: `docs/planning/MVP_1.0_KIS_Adapter_Trading_Mode_Implementation.md`

---

*이 문서는 KIS Adapter API v1.0 + Trading Mode 지원 버전 기준으로 작성되었습니다.*