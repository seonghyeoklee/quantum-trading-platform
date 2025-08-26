# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 Project Overview

**Kiwoom Adapter** - FastAPI-based Python REST API service for integrating Kiwoom Securities trading functionality within the larger Quantum Trading Platform ecosystem. This adapter serves as a bridge between the Java-based CQRS/Event Sourcing platform and Kiwoom's REST/WebSocket APIs.

**Core Architecture**: Microservice adapter pattern with dual-mode support (sandbox/production), real-time WebSocket data streaming, and comprehensive OAuth token management.

**Technology Stack**: Python 3.11, FastAPI, Pydantic, WebSockets, OpenTelemetry tracing, structured logging (structlog)

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
└── functions/                  # Business logic layer
    ├── auth.py               # Authentication business logic
    ├── stock.py              # Stock operations
    └── chart.py              # Chart data processing
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
```

### FastAPI Application Features
- **Auto-Documentation**: Swagger UI at `/docs`, ReDoc at `/redoc`
- **Health Checks**: `/health` endpoint for container orchestration
- **CORS Support**: Development-friendly CORS configuration
- **Lifespan Management**: Proper startup/shutdown hooks

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

### Integration Testing Strategy
- **Mock External APIs**: Use `httpx.AsyncClient` with proper mocking
- **WebSocket Testing**: Use FastAPI's `TestClient` with WebSocket support
- **Environment Isolation**: Test both sandbox and production configurations
- **Error Scenarios**: Test all error conditions and edge cases

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

### Data Flow Patterns
```
Web Client ←→ FastAPI ←→ Kiwoom REST API
     ↓           ↓
WebSocket ←→ Kiwoom WebSocket
     ↓
Platform Event Bus (via REST callbacks)
```

---

**Development Note**: This adapter serves as a critical bridge between the main platform and Kiwoom Securities. All development must maintain strict compatibility with both the Kiwoom API specifications and the platform's integration requirements.