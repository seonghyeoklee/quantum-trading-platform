# KIS Adapter API

## 📋 Overview

KIS Adapter는 한국투자증권(Korea Investment & Securities) Open API를 RESTful API로 제공하는 FastAPI 기반 마이크로서비스입니다. 국내외 주식 시세, 차트 데이터, 종목 정보 등을 통합된 인터페이스로 제공하며, Quantum Trading Platform의 핵심 구성 요소입니다.

### 🎯 Key Features

- **통합 REST API**: KIS Open API를 RESTful 인터페이스로 래핑
- **국내외 주식 지원**: 한국 주식 + 8개 해외 거래소 지원
- **실시간 데이터**: 현재가, 호가, 차트 데이터 제공
- **헤더 기반 인증**: 유연한 토큰 관리 시스템
- **자동 문서화**: Swagger UI를 통한 대화형 API 문서
- **Spring Boot 통합**: CORS 설정으로 웹 애플리케이션 연동 지원

### 🚀 Quick Start

```bash
# 1. 의존성 설치 (uv 권장)
uv sync

# 2. 개발 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. API 문서 접속
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### 📊 Supported APIs

#### 🇰🇷 국내 주식 (Domestic Stocks)

| Category | Endpoint | Description |
|----------|----------|-------------|
| **시세** | `GET /domestic/price/{symbol}` | 현재가, PER/PBR, 거래량 등 |
| | `GET /domestic/orderbook/{symbol}` | 매수/매도 10단계 호가 |
| **차트** | `GET /domestic/chart/daily/{symbol}` | 일봉/주봉/월봉 OHLC |
| | `GET /domestic/chart/minute/{symbol}` | 분봉 OHLC (1분~60분) |
| **기본정보** | `GET /domestic/info/{symbol}` | 종목 기본정보, 기업정보 |
| | `GET /domestic/search` | 종목코드/심볼 검색 |
| **지수** | `GET /indices/domestic` | KOSPI, KOSDAQ, KOSPI200 |

#### 🌍 해외 주식 (Overseas Stocks)

| Exchange | Code | Description |
|----------|------|-------------|
| NYSE | NYS | 뉴욕증권거래소 |
| NASDAQ | NAS | 나스닥 |
| AMEX | AMS | 아메렉스 |
| TSE | TSE | 도쿄증권거래소 |
| HKEX | HKS | 홍콩증권거래소 |
| SSE | SHS | 상하이증권거래소 |
| SZSE | SZS | 선전증권거래소 |
| LSE | LSE | 런던증권거래소 |

**Endpoints:**
- `GET /overseas/{exchange}/price/{symbol}` - 현재가
- `GET /overseas/{exchange}/chart/daily/{symbol}` - 일봉 차트
- `GET /overseas/{exchange}/chart/minute/{symbol}` - 분봉 차트

### 🔐 Authentication

#### Method 1: Header-based (Recommended)
```bash
curl -H "X-KIS-Token: YOUR_ACCESS_TOKEN" \
     http://localhost:8000/domestic/price/005930
```

#### Method 2: Configuration File
```yaml
# kis_devlp.yaml
KIS:
  app_key: "your_app_key"
  app_secret: "your_app_secret"
  base_url: "https://openapi.koreainvestment.com:9443"
```

### 📝 API Response Format

모든 API는 통일된 응답 형식을 사용합니다:

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

### 💡 Usage Examples

#### Python
```python
import requests

# 삼성전자 현재가 조회
response = requests.get(
    "http://localhost:8000/domestic/price/005930",
    headers={"X-KIS-Token": "your_token"}
)

data = response.json()
if data["success"]:
    print(f"현재가: {data['data']}")
```

#### JavaScript
```javascript
// 애플 주식 현재가 조회
const response = await fetch(
    "http://localhost:8000/overseas/NYS/price/AAPL",
    {
        headers: {
            "X-KIS-Token": "your_token"
        }
    }
);

const data = await response.json();
if (data.success) {
    console.log("애플 현재가:", data.data);
}
```

#### cURL
```bash
# 코스피 지수 조회
curl -X GET "http://localhost:8000/indices/domestic?index_code=0001" \
  -H "X-KIS-Token: your_token"
```

### 🛠️ Development Setup

#### Prerequisites
- Python 3.11+
- uv package manager (권장)
- KIS Open API 계정

#### Installation
```bash
# 1. Repository Clone
git clone https://github.com/your-org/quantum-trading-platform.git
cd quantum-trading-platform/quantum-adapter-kis

# 2. Install Dependencies
uv sync

# Alternative: pip install -r requirements.txt

# 3. Configure KIS API
cp kis_devlp.yaml.example kis_devlp.yaml
# Edit kis_devlp.yaml with your API credentials

# 4. Run Development Server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Project Structure
```
quantum-adapter-kis/
├── main.py                    # FastAPI application
├── pyproject.toml            # uv project configuration
├── requirements.txt          # pip compatibility
├── kis_devlp.yaml           # KIS API configuration
├── test_with_headers.http   # HTTP test cases
├── API_REFERENCE.md         # Complete API documentation
├── DEVELOPER_GUIDE.md       # Developer guide
├── CLAUDE.md                # Project documentation
└── examples_user/           # KIS API usage examples
    ├── kis_auth.py          # Authentication module
    └── domestic_stock/      # Stock functions
```

### 🧪 Testing

#### Interactive Testing
Visit http://localhost:8000/docs for Swagger UI where you can:
- Browse all available endpoints
- Test APIs interactively
- View detailed documentation
- Generate code samples

#### HTTP Test File
Use `test_with_headers.http` with your HTTP client:
```http
### 삼성전자 현재가 조회
GET http://localhost:8000/domestic/price/005930
X-KIS-Token: YOUR_ACCESS_TOKEN_HERE

### 애플 주식 현재가 조회
GET http://localhost:8000/overseas/NYS/price/AAPL
X-KIS-Token: YOUR_ACCESS_TOKEN_HERE
```

### 📊 Rate Limits

KIS API 호출 제한이 적용됩니다:
- **현재가 조회**: 초당 20회
- **호가 조회**: 초당 5회  
- **차트 조회**: 분당 200회
- **기타 API**: 분당 100회

### 🌐 Integration

#### Spring Boot Integration
CORS가 설정되어 있어 웹 애플리케이션에서 직접 호출 가능:

```javascript
// React/Vue/Angular 등에서 직접 호출
const stockPrice = await fetch('http://localhost:8000/domestic/price/005930')
  .then(res => res.json());
```

#### Docker Support
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY . .
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 🔍 Monitoring

#### Health Check
```bash
curl http://localhost:8000/health
# {"status": "healthy", "service": "kis-adapter"}
```

#### Metrics Endpoint (if enabled)
```bash
curl http://localhost:8000/metrics  # Prometheus format
```

### 📚 Documentation

- **API Reference**: [API_REFERENCE.md](./API_REFERENCE.md) - Complete endpoint documentation
- **Developer Guide**: [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - Integration and development patterns
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

### 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### 📄 License

이 프로젝트는 한국투자증권 Open API를 기반으로 하며, 해당 API의 이용약관을 준수해야 합니다.

### ⚠️ Disclaimer

- 이 소프트웨어는 교육 및 개발 목적으로 제공됩니다
- 실제 거래에 사용하기 전 충분한 테스트를 수행하세요
- 투자 손실에 대한 책임은 사용자에게 있습니다

### 📞 Support

- **Issues**: GitHub Issues에서 버그 리포트 및 기능 요청
- **Documentation**: Swagger UI에서 실시간 API 문서 확인
- **KIS API**: [한국투자증권 OpenAPI 포털](https://apiportal.koreainvestment.com/)

---

**Quantum Trading Platform** - Building the future of automated trading 🚀