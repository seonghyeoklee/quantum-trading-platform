# KIS Adapter Developer Guide

## Overview

KIS Adapter는 한국투자증권(Korea Investment & Securities) Open API를 RESTful API로 래핑한 FastAPI 기반 마이크로서비스입니다. 이 가이드는 개발자들이 KIS Adapter를 효과적으로 사용하고 확장할 수 있도록 구성되었습니다.

## Project Structure

```
quantum-adapter-kis/
├── main.py                    # FastAPI 애플리케이션 메인 파일
├── pyproject.toml            # Python 프로젝트 설정 (uv 패키지 매니저)
├── requirements.txt          # pip 호환 의존성 목록
├── kis_devlp.yaml           # KIS API 인증 설정 파일
├── test_with_headers.http   # HTTP 클라이언트 테스트 파일
├── CLAUDE.md                # 프로젝트 가이드
├── API_REFERENCE.md         # API 레퍼런스 문서
└── examples_user/           # KIS API 예제 코드 모음
    ├── kis_auth.py          # KIS 인증 모듈
    └── domestic_stock/      # 국내 주식 관련 함수들
        └── domestic_stock_functions.py
```

## Quick Start

### 1. 환경 설정

#### 패키지 설치 (uv 권장)
```bash
# uv를 사용한 패키지 설치 (권장)
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

#### KIS API 설정
`kis_devlp.yaml` 파일을 다음과 같이 설정하세요:

```yaml
# KIS Open API 설정
KIS:
  app_key: "your_app_key_here"
  app_secret: "your_app_secret_here" 
  base_url: "https://openapi.koreainvestment.com:9443"
  
# 계정 정보  
Account:
  account_number: "your_account_number"
  account_type: "01"  # 01: 일반계좌
  
# 환경 설정
Environment:
  mode: "real"  # real: 실거래, demo: 모의거래
```

### 2. 서버 실행

```bash
# 개발 모드 실행 (자동 리로드)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 Python 직접 실행
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. API 문서 접속

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Core Architecture

### 1. Authentication Layer

```python
# kis_auth 모듈을 통한 KIS API 인증
def check_auth():
    if not KIS_MODULE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="KIS 모듈을 사용할 수 없습니다."
        )
    return True
```

**특징:**
- `kis_devlp.yaml` 파일 기반 기본 인증
- HTTP 헤더를 통한 토큰 오버라이드 지원
- 실거래/모의거래 환경 자동 전환

### 2. API Response Model

```python
class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    timestamp: str
```

모든 API는 통일된 응답 형식을 사용하여 클라이언트 개발을 단순화합니다.

### 3. Error Handling

```python
try:
    # KIS API 호출
    result = kis_function(params)
    
    return ApiResponse(
        success=True,
        data=result.to_dict('records') if hasattr(result, 'to_dict') else result,
        message="성공적으로 조회되었습니다",
        timestamp=datetime.now().isoformat()
    )
    
except Exception as e:
    logger.error(f"API 호출 실패: {str(e)}")
    raise HTTPException(
        status_code=500,
        detail=f"API 호출 실패: {str(e)}"
    )
```

## API Categories

### 1. 국내 주식 시세 (`/domestic`)

#### 현재가 조회
- **엔드포인트**: `GET /domestic/price/{symbol}`
- **기능**: 실시간 현재가, PER/PBR 등 주요 지표 제공
- **사용 사례**: 대시보드, 포트폴리오 모니터링

#### 호가 정보 조회  
- **엔드포인트**: `GET /domestic/orderbook/{symbol}`
- **기능**: 매수/매도 10단계 호가 및 잔량
- **사용 사례**: 매매 타이밍 분석, 유동성 파악

### 2. 국내 주식 기본정보 (`/domestic`)

#### 종목 기본정보
- **엔드포인트**: `GET /domestic/info/{symbol}`
- **기능**: 기업 기본 정보, 재무 지표
- **사용 사례**: 종목 스크리닝, 기본 분석

#### 종목 검색
- **엔드포인트**: `GET /domestic/search`
- **기능**: 종목코드/심볼 기반 검색
- **사용 사례**: 종목 코드 검증, 유사 종목 찾기

### 3. 차트 데이터 (`/domestic/chart`, `/overseas/chart`)

#### 일봉 차트
- **국내**: `GET /domestic/chart/daily/{symbol}`
- **해외**: `GET /overseas/{exchange}/chart/daily/{symbol}`
- **기능**: OHLC 데이터, 거래량
- **사용 사례**: 기술적 분석, 차트 시각화

#### 분봉 차트
- **국내**: `GET /domestic/chart/minute/{symbol}`  
- **해외**: `GET /overseas/{exchange}/chart/minute/{symbol}`
- **기능**: 고빈도 OHLC 데이터
- **사용 사례**: 단타 매매, 실시간 분석

### 4. 시장 지수 (`/indices`)

#### 국내 지수
- **엔드포인트**: `GET /indices/domestic`
- **지원 지수**: KOSPI, KOSDAQ, KOSPI200
- **사용 사례**: 시장 동향 파악, 벤치마킹

### 5. 해외 주식 (`/overseas`)

#### 지원 거래소
- **NYS**: 뉴욕증권거래소
- **NAS**: 나스닥  
- **AMS**: 아메렉스
- **TSE**: 도쿄증권거래소
- **HKS**: 홍콩증권거래소
- **SHS**: 상하이증권거래소
- **SZS**: 선전증권거래소
- **LSE**: 런던증권거래소

## Development Patterns

### 1. Client Integration

#### Python Client Example
```python
import requests
from typing import Optional, Dict, Any

class KISClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None):
        self.base_url = base_url
        self.headers = {"X-KIS-Token": token} if token else {}
    
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/domestic/price/{symbol}",
            headers=self.headers
        )
        return response.json()
    
    def get_orderbook(self, symbol: str, market: str = "J") -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/domestic/orderbook/{symbol}",
            params={"market": market},
            headers=self.headers
        )
        return response.json()

# 사용 예시
client = KISClient(token="your_token_here")
price_data = client.get_stock_price("005930")  # 삼성전자
```

#### JavaScript/TypeScript Client
```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  timestamp: string;
}

class KISAdapter {
  constructor(
    private baseUrl: string = "http://localhost:8000",
    private token?: string
  ) {}

  private async request<T>(endpoint: string, params?: Record<string, string>): Promise<ApiResponse<T>> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    const headers: Record<string, string> = {
      'Accept': 'application/json',
    };
    
    if (this.token) {
      headers['X-KIS-Token'] = this.token;
    }

    const response = await fetch(url.toString(), { headers });
    return response.json();
  }

  async getStockPrice(symbol: string) {
    return this.request(`/domestic/price/${symbol}`);
  }

  async getOverseasPrice(exchange: string, symbol: string) {
    return this.request(`/overseas/${exchange}/price/${symbol}`);
  }
}

// 사용 예시
const adapter = new KISAdapter("http://localhost:8000", "your_token");
const applePrice = await adapter.getOverseasPrice("NYS", "AAPL");
```

### 2. Error Handling Best Practices

```python
def handle_kis_response(response: Dict[str, Any]) -> Any:
    """KIS API 응답 처리 헬퍼 함수"""
    if not response.get("success"):
        error_msg = response.get("message", "Unknown error")
        raise KISAPIError(f"KIS API Error: {error_msg}")
    
    return response.get("data")

class KISAPIError(Exception):
    """KIS API 관련 에러"""
    pass

# 사용 예시
try:
    price_response = client.get_stock_price("005930")
    price_data = handle_kis_response(price_response)
    print(f"현재가: {price_data.get('current_price')}")
    
except KISAPIError as e:
    logger.error(f"KIS API 에러: {e}")
    # 에러 처리 로직
    
except requests.RequestException as e:
    logger.error(f"네트워크 에러: {e}")
    # 네트워크 에러 처리
```

### 3. Caching Strategy

```python
import redis
import json
from typing import Optional
from datetime import timedelta

class CachedKISClient:
    def __init__(self, redis_client: redis.Redis, base_client: KISClient):
        self.redis = redis_client
        self.client = base_client
    
    def get_stock_price(self, symbol: str, cache_ttl: int = 5) -> Dict[str, Any]:
        """캐시된 주식 현재가 조회 (기본 5초 캐시)"""
        cache_key = f"price:{symbol}"
        
        # 캐시에서 먼저 확인
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 캐시 미스 시 API 호출
        response = self.client.get_stock_price(symbol)
        
        # 성공 시 캐시 저장
        if response.get("success"):
            self.redis.setex(
                cache_key, 
                timedelta(seconds=cache_ttl), 
                json.dumps(response)
            )
        
        return response
```

### 4. Rate Limiting

```python
import time
from collections import defaultdict, deque
from threading import Lock

class RateLimiter:
    def __init__(self):
        self.calls = defaultdict(deque)
        self.lock = Lock()
    
    def is_allowed(self, endpoint: str, limit: int, window: int) -> bool:
        """Rate limiting 체크"""
        now = time.time()
        
        with self.lock:
            # 윈도우 밖의 호출 기록 제거
            while self.calls[endpoint] and self.calls[endpoint][0] < now - window:
                self.calls[endpoint].popleft()
            
            # 제한 확인
            if len(self.calls[endpoint]) >= limit:
                return False
            
            # 호출 기록
            self.calls[endpoint].append(now)
            return True

# KIS API 호출 제한
RATE_LIMITS = {
    "/domestic/price": (20, 1),      # 초당 20회
    "/domestic/orderbook": (5, 1),    # 초당 5회
    "/domestic/chart": (200, 60),     # 분당 200회
}

limiter = RateLimiter()

def rate_limited_call(endpoint: str, func, *args, **kwargs):
    """Rate limiting이 적용된 API 호출"""
    limit, window = RATE_LIMITS.get(endpoint, (100, 60))
    
    if not limiter.is_allowed(endpoint, limit, window):
        raise Exception(f"Rate limit exceeded for {endpoint}")
    
    return func(*args, **kwargs)
```

## Testing

### 1. Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "kis-adapter"}

@patch('main.inquire_price')
def test_get_domestic_price(mock_inquire_price):
    # Mock KIS API 응답
    mock_df = Mock()
    mock_df.to_dict.return_value = [{"price": 100000, "change": 1000}]
    mock_inquire_price.return_value = mock_df
    
    response = client.get("/domestic/price/005930")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] == True
    assert "data" in data

def test_invalid_symbol():
    response = client.get("/domestic/price/INVALID")
    assert response.status_code == 500  # KIS API 에러 시
```

### 2. Integration Tests

```python
@pytest.mark.integration
def test_real_api_call():
    """실제 KIS API 호출 테스트 (통합 테스트)"""
    response = client.get("/domestic/price/005930")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] == True
    assert "timestamp" in data

@pytest.mark.integration  
def test_overseas_api():
    """해외 주식 API 통합 테스트"""
    response = client.get("/overseas/NYS/price/AAPL")
    assert response.status_code == 200
```

### 3. Performance Tests

```python
import asyncio
import aiohttp
import time

async def performance_test():
    """성능 테스트"""
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        # 동시에 10개 요청
        tasks = []
        for _ in range(10):
            task = session.get("http://localhost:8000/domestic/price/005930")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        print(f"10 requests took {end_time - start_time:.2f} seconds")
        
        for response in responses:
            assert response.status == 200

# 실행
asyncio.run(performance_test())
```

## Production Deployment

### 1. Docker Configuration

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Environment Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  kis-adapter:
    build: .
    ports:
      - "8000:8000"
    environment:
      - KIS_APP_KEY=${KIS_APP_KEY}
      - KIS_APP_SECRET=${KIS_APP_SECRET}
      - KIS_ACCOUNT_NUMBER=${KIS_ACCOUNT_NUMBER}
    volumes:
      - ./kis_devlp.yaml:/app/kis_devlp.yaml
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 3. Health Monitoring

```python
from fastapi import BackgroundTasks
import psutil
import asyncio

@app.get("/health/detailed")
async def detailed_health_check():
    """상세 헬스체크"""
    return {
        "status": "healthy",
        "service": "kis-adapter",
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "kis_connection": await check_kis_connectivity()
    }

async def check_kis_connectivity() -> bool:
    """KIS API 연결 상태 확인"""
    try:
        # 간단한 KIS API 호출로 연결 테스트
        result = inquire_price("005930")  # 삼성전자로 테스트
        return True
    except Exception:
        return False
```

## Monitoring & Logging

### 1. Structured Logging

```python
import structlog
import logging

# Structured logging 설정
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    logger.info("Request started", 
                method=request.method, 
                url=str(request.url),
                client_ip=request.client.host)
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info("Request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time)
    
    return response
```

### 2. Metrics Collection

```python
from prometheus_client import Counter, Histogram, generate_latest
import time

# Prometheus 메트릭 정의
REQUEST_COUNT = Counter('kis_adapter_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('kis_adapter_request_duration_seconds', 'Request duration', ['endpoint'])
KIS_API_CALLS = Counter('kis_api_calls_total', 'KIS API calls', ['function', 'status'])

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # 메트릭 업데이트
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(endpoint=request.url.path).observe(time.time() - start_time)
    
    return response

@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return Response(generate_latest(), media_type="text/plain")
```

## Security Considerations

### 1. API Key Management

```python
import os
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self):
        self.encryption_key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
        self.fernet = Fernet(self.encryption_key)
    
    def encrypt_token(self, token: str) -> str:
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        return self.fernet.decrypt(encrypted_token.encode()).decode()

# 환경변수에서 암호화된 토큰 로드
secure_config = SecureConfig()
```

### 2. Rate Limiting & CORS

```python
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 허용할 프론트엔드 도메인
    allow_credentials=True,
    allow_methods=["GET"],  # 읽기 전용 API
    allow_headers=["*"],
)

@app.get("/domestic/price/{symbol}")
@limiter.limit("20/minute")  # 분당 20회 제한
async def get_domestic_price(request: Request, symbol: str):
    # ... 기존 코드 ...
```

## Troubleshooting

### Common Issues

1. **KIS API 연결 실패**
   - `kis_devlp.yaml` 설정 확인
   - 네트워크 연결 상태 점검
   - API 키 유효성 검증

2. **Rate Limit 초과**
   - 호출 빈도 조절
   - 캐싱 전략 적용
   - 배치 처리 구현

3. **메모리 사용량 증가**
   - DataFrame 캐시 정리
   - 가비지 컬렉션 튜닝
   - 메모리 프로파일링

### Debug Mode

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        debug=True,
        log_level="debug"
    )
```

이 개발자 가이드를 통해 KIS Adapter를 효과적으로 활용하고 확장할 수 있습니다. 추가 질문이나 기능 요청은 프로젝트 이슈 트래커를 통해 문의해 주세요.