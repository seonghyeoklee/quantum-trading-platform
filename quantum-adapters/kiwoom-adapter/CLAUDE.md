# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**Kiwoom Adapter** - FastAPI-based Python REST API service for integrating Kiwoom Securities trading functionality within the larger Quantum Trading Platform ecosystem. This adapter serves as a bridge between the Java-based CQRS/Event Sourcing platform and Kiwoom's REST/WebSocket APIs.

**Core Architecture**: Microservice adapter pattern with dual-mode support (sandbox/production), real-time WebSocket data streaming, comprehensive OAuth token management, financial data analysis system with DART API integration, and advanced news sentiment analysis.

**Technology Stack**: Python 3.11, FastAPI, Pydantic, WebSockets, OpenTelemetry tracing, structured logging (structlog), DART financial data integration, BeautifulSoup web scraping, RSS feed processing

## 📁 Project Structure & Import Strategy

### Critical Import Pattern
The codebase uses a dual-import strategy to handle both development and production execution contexts:

```python
# Handle both relative and absolute imports for different execution contexts
try:
    from .config.settings import settings  # Relative imports (preferred)
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.config.settings import settings
```

This pattern is used throughout the codebase and must be maintained when adding new modules.

### Core Architecture Layers

```
src/kiwoom_api/
├── main.py                     # FastAPI application with distributed tracing
├── config/settings.py          # Environment-based dual-mode configuration
├── auth/                       # OAuth token management layer
│   ├── oauth_client.py        # OAuth client with automatic token refresh
│   ├── token_cache.py         # In-memory token caching
│   └── token_manager.py       # Token lifecycle management
├── models/                     # Pydantic data models
│   ├── auth.py               # Authentication models
│   ├── websocket.py          # WebSocket protocol models
│   └── stock.py              # Stock market data models
├── api/                        # FastAPI routers
│   ├── auth.py               # OAuth endpoints
│   ├── websocket.py          # WebSocket management endpoints
│   ├── stock.py              # Stock market data endpoints
│   └── chart.py              # Chart data endpoints
├── websocket/                  # Real-time WebSocket infrastructure
│   ├── client.py             # Kiwoom WebSocket client
│   ├── client_handler.py     # Connection management
│   └── realtime.py           # Real-time data processing
├── functions/                  # Business logic layer
│   ├── auth.py               # Authentication business logic
│   ├── stock.py              # Stock operations
│   └── chart.py              # Chart data processing
├── external/                   # External API integrations
│   ├── dart_client.py        # DART financial data client
│   └── news_crawler.py       # Multi-source news aggregation & sentiment analysis
└── analysis/                   # Financial analysis system
    ├── core/                   # Analysis engine components
    │   ├── models.py           # Analysis request/response models
    │   ├── scorer.py           # Multi-dimensional scoring system
    │   └── vlookup_calculator.py # Google Sheets VLOOKUP-based analysis
    ├── indicators/             # Financial indicators calculation
    │   ├── financial_indicators.py # Basic financial ratios
    │   ├── dart_integrated_indicators.py # DART-powered indicators
    │   └── technical.py        # Technical analysis indicators (RSI, etc.)
    └── api/                    # Analysis API endpoints
        ├── analysis_router.py  # Individual analysis endpoints
        └── comprehensive_router.py # Comprehensive analysis
```

## 💻 Development Commands

### Environment Setup
```bash
# Poetry setup (preferred)
poetry install
poetry shell

# pip setup (fallback)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Development server with auto-reload
poetry run uvicorn src.kiwoom_api.main:app --reload --host 0.0.0.0 --port 8100

# Alternative with PYTHONPATH
PYTHONPATH=./src uvicorn src.kiwoom_api.main:app --host 0.0.0.0 --port 8100 --reload

# Production mode
uvicorn src.kiwoom_api.main:app --host 0.0.0.0 --port 8100
```

### Testing Commands
```bash
# Run all tests
pytest

# Run specific test files
pytest test_websocket.py
pytest test_stock_api.py

# Run with coverage
pytest --cov=src/kiwoom_api

# Test specific WebSocket functionality
pytest test_websocket_proper.py -v
```

### Code Quality
```bash
# Code formatting
black src/ tests/
isort src/ tests/

# Linting
flake8 src/ tests/

# Type checking (if mypy is added)
mypy src/

# Install additional dependencies for analysis features
pip install beautifulsoup4 lxml feedparser
```

### Analysis System Testing
```bash
# Test DART API integration
PYTHONPATH=./src python -c "
import asyncio
from src.kiwoom_api.external.dart_client import DARTClient

async def test_dart():
    dart = DARTClient()
    result = await dart.get_financial_statement('005930', 2023, '11014')
    print(f'삼성전자 재무데이터: {list(result.keys())}')

asyncio.run(test_dart())
"

# Test news sentiment analysis
PYTHONPATH=./src python -c "
import asyncio
from src.kiwoom_api.external.news_crawler import NewsCrawler

async def test_news():
    crawler = NewsCrawler()
    result = await crawler.get_comprehensive_news('005930', '삼성전자')
    print(f'뉴스 분석 결과: {len(result.get(\"articles\", []))}건')

asyncio.run(test_news())
"

# Test analysis endpoints
curl http://localhost:8100/api/analysis/comprehensive/005930
curl http://localhost:8100/api/analysis/rsi/005930
```

## 🏗️ Architecture Principles

### Dual-Mode Environment Strategy
The application supports both sandbox (mock trading) and production (real trading) modes:

```python
# Automatic mode selection based on environment
@property
def kiwoom_base_url(self) -> str:
    if self.KIWOOM_SANDBOX_MODE:
        return "https://mockapi.kiwoom.com"  # Sandbox
    return "https://api.kiwoom.com"  # Production

@property  
def KIWOOM_APP_KEY(self) -> str:
    if self.KIWOOM_SANDBOX_MODE:
        return self.KIWOOM_SANDBOX_APP_KEY
    return self.KIWOOM_PRODUCTION_APP_KEY
```

### WebSocket Real-time Architecture
- **Client-Server Pattern**: Web clients connect to `/ws/realtime` endpoint
- **Connection Management**: Centralized connection manager with automatic cleanup
- **Data Type Support**: Multiple real-time data types (0B, 0D, 0E, 0F) with specialized clients
- **Error Resilience**: Automatic reconnection and graceful error handling

### OAuth Token Management
- **Automatic Refresh**: Tokens are automatically refreshed before expiration
- **Caching Strategy**: In-memory caching with configurable TTL
- **Environment Awareness**: Separate token endpoints for sandbox/production

### Distributed Tracing Integration
- **OpenTelemetry**: Full distributed tracing with Zipkin exporter
- **Structured Logging**: JSON-formatted logs with structured data
- **Performance Monitoring**: Request/response tracking across services

### Financial Analysis Architecture
- **Multi-dimensional Scoring**: Technical, fundamental, news sentiment, and institutional analysis
- **DART Integration**: Real-time Korean financial statement data from regulatory system
- **News Sentiment Engine**: Multi-source news aggregation with keyword-based sentiment classification
- **VLOOKUP-based Analysis**: Google Sheets compatible scoring methodology
- **Comprehensive API**: RESTful endpoints for individual indicators and comprehensive analysis

## 🔧 Key Configuration

### Required Environment Variables
```bash
# Sandbox Mode (Mock Trading)
KIWOOM_SANDBOX_MODE=true
KIWOOM_SANDBOX_APP_KEY=your_sandbox_key
KIWOOM_SANDBOX_APP_SECRET=your_sandbox_secret

# Production Mode (Real Trading)
KIWOOM_SANDBOX_MODE=false
KIWOOM_PRODUCTION_APP_KEY=your_production_key
KIWOOM_PRODUCTION_APP_SECRET=your_production_secret

# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8100
LOG_LEVEL=INFO

# WebSocket Settings
WEBSOCKET_PING_INTERVAL=60
WEBSOCKET_PING_TIMEOUT=10
WEBSOCKET_MAX_CONNECTIONS=100

# DART API Integration (Korean Financial Supervisory Service)
DART_API_KEY=your_dart_api_key_here

# Kafka Integration
ENABLE_KAFKA=false
```

### FastAPI Application Features
- **Auto-Documentation**: Swagger UI at `/docs`, ReDoc at `/redoc`
- **Health Checks**: `/health` endpoint for container orchestration
- **CORS Support**: Development-friendly CORS configuration
- **Lifespan Management**: Proper startup/shutdown hooks
- **Analysis Endpoints**: Comprehensive financial analysis at `/api/analysis/*`
- **Multi-format API**: Support for both individual indicators and comprehensive analysis

## 🚫 Critical Constraints

### Import Pattern Compliance
All new modules MUST use the dual-import pattern shown above. This ensures compatibility with both development and production execution contexts.

### Async/Await Requirements
```python
# Correct: All HTTP operations must be async
async def get_oauth_token(client_id: str, client_secret: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        return response.json()

# Incorrect: Synchronous HTTP operations
def get_oauth_token(client_id: str, client_secret: str) -> str:
    response = requests.post(url, data=data)  # Don't use requests
    return response.json()
```

### Error Handling Pattern
```python
# Correct: Use HTTPException for API errors
from fastapi import HTTPException

@router.post("/endpoint")
async def endpoint(request: RequestModel):
    try:
        result = await business_logic(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

### WebSocket Management Rules
- **Connection Lifecycle**: Always use `connection_manager` for WebSocket connections
- **Error Resilience**: Implement proper error handling for disconnections
- **Resource Cleanup**: Ensure connections are properly cleaned up on disconnect
- **Message Validation**: All WebSocket messages must be validated using Pydantic models

### Security Requirements
- **Environment Variables**: Never hardcode API keys or secrets
- **Token Rotation**: Implement automatic token refresh before expiration
- **Input Validation**: All API inputs must be validated using Pydantic models
- **Logging Safety**: Never log sensitive information (tokens, secrets)
- **DART API Keys**: Always use settings.DART_API_KEY from environment configuration
- **Multi-source Data**: Validate external data sources (news, DART) before processing

### Analysis System Requirements
- **DART Integration**: All financial indicator modules must use DARTClient with proper error handling
- **News Processing**: Implement sentiment analysis with NewsSentiment enum values (-2 to +2)
- **Scoring Consistency**: Use standardized scoring ranges across all analysis modules
- **Cache Strategy**: Implement appropriate caching for expensive DART API calls
- **Error Resilience**: Graceful degradation when external APIs (DART, news) are unavailable

## 🔄 Development Workflow

### Adding New API Endpoints
1. **Define Models**: Create Pydantic models in `models/`
2. **Business Logic**: Implement core logic in `functions/`
3. **API Router**: Create FastAPI endpoints in `api/`
4. **Update Main**: Register router in `main.py`
5. **Testing**: Add comprehensive tests

### WebSocket Development
1. **Message Models**: Define WebSocket message models in `models/websocket.py`
2. **Client Logic**: Implement client logic in `websocket/client.py`
3. **Handler Updates**: Update connection handler in `websocket/client_handler.py`
4. **API Endpoints**: Add management endpoints in `api/websocket.py`

### Adding New Analysis Indicators
1. **Create Model**: Define request/response models in `analysis/core/models.py`
2. **Implement Logic**: Add calculation logic in appropriate `analysis/indicators/` module
3. **External Integration**: Use DARTClient or NewsCrawler for data sources
4. **API Endpoint**: Add endpoint in `analysis/api/analysis_router.py`
5. **Comprehensive Integration**: Update `comprehensive_router.py` for multi-indicator analysis

### Integration Testing Strategy
- **Mock External APIs**: Use `httpx.AsyncClient` with proper mocking
- **WebSocket Testing**: Use FastAPI's `TestClient` with WebSocket support
- **Environment Isolation**: Test both sandbox and production configurations
- **Error Scenarios**: Test all error conditions and edge cases
- **DART API Testing**: Test with valid/invalid API keys and various stock codes
- **News Analysis Testing**: Validate sentiment scoring across different news sources

## 🔗 Platform Integration Context

### Parent Platform Relationship
This adapter integrates with the larger Quantum Trading Platform:
- **Event-Driven Communication**: Receives commands via REST API calls
- **Multi-Broker Architecture**: One of multiple broker adapters (KIS, Kiwoom, etc.)
- **Docker Integration**: Runs as containerized service in platform ecosystem
- **Monitoring Integration**: Shared observability with Prometheus/Grafana

### External Dependencies
- **Kiwoom APIs**: REST API for trading operations, WebSocket for real-time data
- **Platform Services**: Main Java platform for command/query operations
- **Infrastructure**: Redis for caching, monitoring stack for observability
- **DART API**: Korean Financial Supervisory Service for regulatory financial data
- **News Sources**: Multi-source news aggregation (Naver, RSS feeds, news APIs)
- **Analysis Libraries**: BeautifulSoup, feedparser, httpx for data collection and processing

### Data Flow Patterns
```
Web Client ←→ FastAPI ←→ Kiwoom REST API
     ↓           ↓
WebSocket ←→ Kiwoom WebSocket
     ↓
Platform Event Bus (via REST callbacks)

Analysis Flow:
Client Request → Analysis API → DART Client → Korean Financial Data
                             → News Crawler → Multi-source News
                             → Technical Indicators → Market Data
                             → Comprehensive Scorer → Final Analysis
```

---

**Development Note**: This adapter serves as a critical bridge between the main platform and Kiwoom Securities, enhanced with comprehensive financial analysis capabilities. All development must maintain strict compatibility with Kiwoom API specifications, Korean regulatory data standards (DART), and the platform's integration requirements. The system supports both real-time trading operations and sophisticated multi-dimensional stock analysis powered by official financial data and news sentiment analysis.