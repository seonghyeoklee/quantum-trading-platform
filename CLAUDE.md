# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Quantum Trading Platform** is an automated stock trading system built around Korea Investment & Securities (KIS) Open API integration. The platform uses a hybrid microservices architecture with JWT-based authentication and multi-environment KIS token management for both live and sandbox trading.

## Architecture Overview

### Microservices Structure
```
Frontend (Port 3000) ← → Backend (Port 8080) ← → KIS Adapter (Port 8000)
Next.js 15 + React 19      Spring Boot 3.5 + Kotlin    FastAPI + Python 3.13
```

### Key Architectural Decisions
- **Server-side KIS Token Management**: All KIS authentication handled by backend
- **Multi-Environment Support**: LIVE (production) and SANDBOX (demo) trading  
- **Real-time Data**: WebSocket at ws://localhost:8000/ws/realtime
- **Chart System**: lightweight-charts v5.0.8 integration

## Development Commands

### Frontend (quantum-web-client/)
```bash
npm run dev              # Runs on quantum-trading.com (custom host)
npm run dev:local        # Runs on localhost:3000
npm run build
npm run start
npm run lint
```

### Backend (quantum-web-api/)  
```bash
./gradlew bootRun
./gradlew build
./gradlew test
./gradlew test --tests="*Auth*"   # Specific test filtering

# Spring AI requires OpenAI API key
export OPENAI_API_KEY=sk-your-api-key-here
```

### KIS Adapter (quantum-adapter-kis/)
```bash
uv sync                  # Install dependencies with uv
uv run python main.py    # Run FastAPI server on port 8000
# Test files pattern: chk_*.py for individual API testing
```

### Infrastructure & Monitoring (quantum-infrastructure/)
```bash
docker-compose -f docker-compose.monitoring.yml up -d  # Start monitoring stack
./start-monitoring.sh    # Helper script to start all services
# Grafana: http://localhost:3001 (admin/quantum2024)
# Prometheus: http://localhost:9090
```

## Configuration Requirements

### Environment Setup
1. **PostgreSQL Database**: Port 5433 (dev), 5432 (prod)
   - Database: `quantum_trading`
   - Username: `quantum` 
   - Password: `quantum123`

2. **KIS API Configuration**: Create `kis_devlp.yaml` in quantum-adapter-kis/
   - Required for KIS API authentication
   - Contains LIVE/SANDBOX API keys

3. **JWT Secret**: Configured in application.yml

### Port Configuration
- **Frontend**: 3000 (Next.js)
- **Backend**: 8080 (Spring Boot)  
- **KIS Adapter**: 8000 (FastAPI)
- **Database**: 5433 (dev), 5432 (prod)
- **Monitoring**: Grafana (3001), Prometheus (9090), Loki (3100)

## High-Level Architecture

### Backend Architecture Pattern (Hexagonal + DDD)
```
quantum-web-api follows Domain-Driven Design with Hexagonal Architecture:

domain/                 # Business logic, entities, domain services
├── User.kt            # Aggregate root with domain events
├── KisAccount.kt      # KIS trading accounts
└── KisToken.kt        # Server-side token management

application/           # Use cases and port definitions  
├── port/
│   ├── incoming/      # Primary ports (use cases)
│   └── outgoing/      # Secondary ports (repositories)
└── usecase/           # Application services implementation

infrastructure/        # Technical implementations
├── persistence/       # JPA repositories and database adapters
├── security/          # JWT, Spring Security adapters
├── client/            # External API clients (KIS)
└── ai/                # Spring AI integration

presentation/          # Controllers and DTOs
├── web/              # REST controllers
└── dto/              # Request/response objects
```

### Authentication Flow
1. User Login → JWT tokens (access/refresh)
2. Backend validates JWT and manages KIS tokens server-side
3. Frontend makes authenticated requests to backend
4. Backend proxies to KIS Adapter with server-managed tokens

### Data Flow Architecture
```
User Request → Frontend → Backend API → KIS Adapter → KIS OpenAPI
                  ↑           ↓             ↓
                JWT Auth   Server KIS    Market Data
                            ↓
                      AI Analysis ← Stock Analysis DB
```

### Analysis Database Schema
- **stock_master**: 종목 마스터 (국내/해외 종목 기본 정보)
- **stock_analysis**: 주식 분석 결과 (투자 점수, 신호, 백테스팅, 기술적 지표)
  - `raw_analysis` JSONB field contains original analysis data
- **analysis_summary**: 섹터/시장별 집계 데이터
- **stock_popularity**: 종목 관심도/인기도 데이터

### Critical Backend APIs (Implementation Priority)

**Available AI APIs:**
```kotlin
// AITestController.kt - Spring AI integration testing
GET /api/v1/ai/test                    # Environment configuration test
POST /api/v1/ai/chat                   # Basic AI chat functionality
```

**Missing Controllers (URGENT):**
```kotlin
// ChartController.kt - Frontend is calling these endpoints
GET /api/v1/chart/{symbol}/daily       
GET /api/v1/chart/{symbol}/current     
GET /api/v1/chart/{symbol}/overseas    

// TradingModeController.kt - Frontend expects these
GET /api/v1/trading-mode/status
POST /api/v1/trading-mode/switch
```

### KIS Adapter API Pattern
```python
# Core domestic endpoints
GET /domestic/price/{symbol}           # Current price
GET /domestic/chart/{symbol}           # Chart data (D/W/M/Y periods)
GET /domestic/index/{index_code}       # Index prices
GET /domestic/ranking/top-interest-stock # Popular stocks

# Core overseas endpoints  
GET /overseas/{exchange}/price/{symbol}        # Current price
GET /overseas/{exchange}/chart/{symbol}        # Chart data
GET /overseas/{exchange}/index/{index_code}    # Index prices

# Utility endpoints
POST /auth/refresh-token?environment=prod|vps # Token management
GET /health                                    # Health check
WebSocket /ws/realtime                         # Real-time data stream
```

### WebSocket Integration
- **KIS Adapter WebSocket**: ws://localhost:8000/ws/realtime
- **Backend Bridge**: Needs implementation to relay to frontend
- **Data Format**: JSON with real-time price/volume updates

## Technology Stack & Dependencies

### Frontend (quantum-web-client/)
- **Next.js 15.5.2** + React 19.1.0
- **UI Components**: Radix UI primitives + Tailwind CSS
- **Forms**: React Hook Form + Zod validation
- **Charts**: lightweight-charts v5.0.8
- **Themes**: next-themes for dark/light mode

### Backend (quantum-web-api/)
- **Spring Boot 3.5.5** + Kotlin 1.9.25 + Java 21
- **Database**: PostgreSQL + Spring Data JPA
- **Security**: JWT authentication + Spring Security
- **HTTP Client**: WebFlux WebClient for KIS API calls
- **AI Integration**: Spring AI 0.8.1 + OpenAI GPT models
- **Monitoring**: Actuator + Prometheus metrics + Logbook HTTP logging

### KIS Adapter (quantum-adapter-kis/)
- **FastAPI** + Python 3.13 + uvicorn
- **Dependencies**: pandas, requests, websockets, pycryptodome
- **Architecture**: 17 REST endpoints + WebSocket real-time data

## Chart System Technical Notes

**Library**: lightweight-charts v5.0.8
- **Official Docs**: https://tradingview.github.io/lightweight-charts/docs
- **Korean Market Colors**: Red (#FF0000) for up, Blue (#0000FF) for down
- **SSR**: Always use dynamic import with `ssr: false` in Next.js

**Common Issues**:
1. API changes in v5: Use `addSeries(CandlestickSeries, options)`
2. Import: `const { createChart, CandlestickSeries } = LightweightCharts`

## Development Workflow

### Standard Startup Sequence
1. **Database**: Start PostgreSQL database (port 5433 for dev)
2. **Backend**: `cd quantum-web-api && ./gradlew bootRun`
3. **KIS Adapter**: `cd quantum-adapter-kis && uv run python main.py`
4. **Frontend**: `cd quantum-web-client && npm run dev`
5. **Optional Monitoring**: `cd quantum-infrastructure && docker-compose -f docker-compose.monitoring.yml up -d`

### Testing & Debugging
- **Backend Tests**: `./gradlew test` (all) or `./gradlew test --tests="*Auth*"` (filtered)
- **KIS API Testing**: Individual API test files in `chk_*.py` pattern
- **Integration Testing**: JWT authentication, KIS token refresh, market data flow
- **API Documentation**: KIS Adapter includes comprehensive FastAPI docs at `/docs`
- **Health Checks**: `/health` endpoints on all services
- **Monitoring**: Grafana dashboards for logs, metrics, and performance

## Current Implementation Status

### ✅ Completed
- **Frontend**: Next.js app with chart system (TradingChart.tsx), Radix UI components
- **KIS Adapter**: FastAPI server with 17 endpoints, WebSocket real-time data, automatic data splitting
- **Backend**: Spring Boot API with JWT auth, KIS token management, PostgreSQL integration
- **AI Integration**: Spring AI 0.8.1 with basic OpenAI GPT support and test endpoints
- **Infrastructure**: Grafana + Loki + Prometheus monitoring stack
- **Database**: JPA entities, PostgreSQL schema, and analysis data tables

### 🔧 In Progress  
- **Backend Controllers**: ChartController, TradingModeController implementations
- **WebSocket Bridge**: Backend relay from KIS Adapter to Frontend
- **MVP 1.1**: Auto-trading features and signal processing

### 📋 Pending
- **Real-time Integration**: Complete WebSocket data flow
- **Trading Engine**: Signal calculations and automated execution
- **Advanced Features**: Portfolio management, risk controls

## Important Notes

### Rate Limiting & Performance
- **KIS LIVE API**: 20 calls/second per account
- **KIS SANDBOX API**: 2 calls/second per account  
- **WebSocket Limits**: Max 41 concurrent registrations
- **Chart Data**: Automatic 90-day splitting for large date ranges
- **Real-time Data**: 1-second polling interval with 0.2s per symbol

### Security & Authentication
- **JWT Tokens**: 24-hour expiration with refresh capability
- **KIS Tokens**: Server-side only, 6-hour expiration, auto-refresh
- **API Keys**: Never exposed to client, stored in `kis_devlp.yaml`
- **Monitoring**: Sensitive data automatically masked in logs

### Configuration Notes
- **CORS**: Allows localhost:3000, localhost:8080 for development
- **Database**: p6spy enabled for SQL logging in development
- **Logging**: JSON format with Logbook for HTTP requests
- **Frontend Rewrites**: `/api/kis/*` proxied to `adapter.quantum-trading.com:8000`
- **Spring AI**: OpenAI API key required via `OPENAI_API_KEY` environment variable
- **Auto-Configuration**: Spring Cloud Function excluded to prevent conflicts

## Architecture Decision Records

### Why Separate KIS Adapter?
- **Isolation**: KIS API complexity isolated from main business logic
- **Language Optimization**: Python better suited for pandas data processing
- **Rate Limiting**: Dedicated service for managing API quotas
- **Real-time**: WebSocket implementation optimized for streaming data

### Why Server-side Token Management?
- **Security**: KIS tokens never exposed to browser
- **Reliability**: Centralized token refresh and error handling  
- **Rate Limiting**: Single point of control for API quota management
- **Compliance**: Meets securities trading security requirements

## Component Collaboration  

When working on this project, identify your primary focus area:
- **Frontend**: Next.js components, UI/UX, chart integration, TypeScript
- **Backend**: Spring Boot APIs, Kotlin services, database, authentication
- **KIS Adapter**: Python FastAPI, KIS API integration, real-time WebSocket data  
- **Infrastructure**: Docker monitoring, Grafana dashboards, PostgreSQL
- **Integration**: Cross-service communication, JWT flows, WebSocket bridges