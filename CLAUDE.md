# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Team Collaboration Framework

**IMPORTANT: This is a 4-person development team project. Always identify your role when starting:**

1. **기획자 (Planner)** - Requirements definition, user stories, project roadmap, MVP scope
2. **백엔드 (Backend)** - Spring Boot API development, database design, system architecture  
3. **프론트엔드 (Frontend)** - Next.js UI/UX development, user interface implementation
4. **분석가 (Analyst)** - Trading algorithms, data analysis, automated trading logic

**Collaboration Guidelines:**
- State your role at the beginning of each session
- Focus on your domain expertise while considering team integration
- Coordinate on shared interfaces and APIs
- Maintain consistency with team decisions and architectural patterns

## Project Overview

**Quantum Trading Platform** is an automated stock trading system built around Korea Investment & Securities (KIS) Open API integration. The platform uses a hybrid microservices architecture with JWT-based authentication and multi-environment KIS token management for both live and sandbox trading.

**Mission**: Building an automated stock trading platform (MVP)
**Target**: Support both live trading and paper trading environments  
**Developer**: Single developer managing multiple specialized roles

## Architecture Overview

### Microservices Structure
```
Frontend (Port 3000) ← → Backend (Port 8080) ← → KIS Adapter (Port 8000)
Next.js 15 + React 19      Spring Boot 3.5 + Kotlin    FastAPI + Python 3.13
```

### Role-Based Component Architecture
- **quantum-web-client** - Next.js 15 TypeScript frontend (Frontend role)
- **quantum-web-api** - Spring Boot Kotlin backend API (Backend role)
- **quantum-adapter-kis** - FastAPI Python adapter for KIS API (Analyst role)
- **docs/planning/** - MVP specifications and requirements (Planner role)

### Key Architectural Decisions
- **Hybrid Token Management**: Client-side KIS tokens for direct API calls, server-side JWT for authentication
- **Multi-Environment Support**: LIVE (production) and SANDBOX (demo) trading environments  
- **Domestic/Overseas Market Separation**: Header toggle UI with separate API routing
- **Real-time Data**: WebSocket integration at ws://localhost:8000/ws/realtime
- **Chart System**: MVP 1.0 implementation with lightweight-charts library
- **Data Analysis**: Python handles calculations, Backend handles data routing

### Chart System Technical Notes (CRITICAL)

**⚠️ IMPORTANT: Always refer to official documentation for third-party libraries**

**Lightweight Charts Integration**: 
- Library: `lightweight-charts@5.0.8`
- **Official Docs**: https://tradingview.github.io/lightweight-charts/docs
- **Tutorials**: https://tradingview.github.io/lightweight-charts/tutorials
- **Demo Examples**: https://tradingview.github.io/lightweight-charts/tutorials/demos/realtime-updates

**Common Issues & Solutions**:
1. **API Changes**: `addCandlestickSeries()` → `addSeries(CandlestickSeries, options)`
2. **Import Method**: Use destructuring from module: `const { createChart, CandlestickSeries } = LightweightCharts`
3. **SSR Issues**: Always use dynamic import in Next.js with `ssr: false`
4. **Korean Colors**: Red=#FF0000 (상승), Blue=#0000FF (하락)

**Critical Rule**: When encountering library-specific errors, ALWAYS check official documentation FIRST before attempting fixes.

## Development Commands

### Frontend (quantum-web-client/)
```bash
# Development with custom host
npm run dev              # Runs on quantum-trading.com (configured host)
npm run dev:local        # Runs on localhost:3000

# Production
npm run build
npm run start

# Linting
npm run lint
```

### Backend (quantum-web-api/)  
```bash
# Development
./gradlew bootRun

# Build and test
./gradlew build
./gradlew test

# Database schema
./gradlew flywayMigrate  # If using Flyway (check build.gradle.kts)
```

### KIS Adapter (quantum-adapter-kis/)
```bash
# Using uv (recommended)
uv sync
uv run python main.py

# Traditional approach
pip install -r requirements.txt
python main.py
```

## Configuration Requirements

### Environment Setup
1. **PostgreSQL Database**: Default port 5433 for development, 5432 for production
   - Database: `quantum_trading`
   - Username: `quantum` 
   - Password: `quantum123`

2. **KIS API Configuration**: Create `kis_devlp.yaml` in quantum-adapter-kis/ root
   - Contains API keys, account numbers for LIVE/SANDBOX environments
   - Required for KIS API authentication

3. **JWT Secret**: Default development key in application.yml, change for production

### Port Configuration
- **Frontend**: 3000 (Next.js dev server)
- **Backend**: 8080 (Spring Boot)
- **KIS Adapter**: 8000 (FastAPI) ← **Updated from 8002**
- **Database**: 5433 (PostgreSQL dev), 5432 (production)

## Current Implementation Status

### ✅ **Completed Components**
- **Frontend Chart System**: TradingChart.tsx with lightweight-charts integration
- **KIS API Integration**: Full adapter with domestic/overseas stock data + **Trading Mode Support**
- **Authentication Flow**: JWT + KIS token management with multi-environment support
- **User Interface**: Complete login, settings, and market data display
- **Real-time Data**: WebSocket infrastructure ready for live market updates
- **Trading Mode System**: Complete LIVE/SANDBOX environment switching across all 17 KIS APIs

### ❌ **Missing Critical APIs (Backend Priority)**
- **Trading Mode Controller**: `/api/v1/trading-mode/*` endpoints not implemented
- **Chart Data Controller**: `/api/v1/chart/*` endpoints missing
- **WebSocket Bridge**: Backend to KIS Adapter WebSocket relay

### 🔄 **In Development**
- **Chart Data Flow**: Frontend ready, Backend API layer needed for KIS Adapter integration
- **Trading Signals**: Python calculation ready, Backend routing needed

## Key Components & Integration Points

### Authentication Flow
1. **User Login** → JWT tokens (access/refresh)
2. **KIS Account Check** → Verify LIVE/SANDBOX account setup
3. **KIS Token Issuance** → 6-hour tokens for direct API calls
4. **Client Storage** → KIS tokens cached in localStorage
5. **Direct API Access** → Next.js calls KIS Adapter with X-KIS-Token header

### Market Data Architecture
- **Domestic Stocks**: `/domestic/` endpoints with optional date parameters
- **Overseas Stocks**: `/overseas/{exchange}/` endpoints with required date parameters
- **Supported Exchanges**: NYS, NAS, AMS, HKS, SHS, SZS, TSE, HSX, HNX

### Chart System Architecture (MVP 1.0)

**Data Loading Strategy:**
1. **Initial Load**: KIS API → 1 year historical data (365 days)
2. **Real-time Updates**: WebSocket → live price/volume data
3. **Hybrid Synchronization**: Historical base + real-time overlay

**Chart Components Implementation:**
- **TradingChart.tsx**: Completed with lightweight-charts integration
- **Moving Averages**: 5-day (pink), 20-day (yellow), 60-day (white)  
- **Volume Chart**: Korean style color coding (red=up, blue=down)
- **Real-time Integration**: WebSocket updates current candle data

**Chart Data Flow:**
```
KIS Adapter (8000) → Backend API (8080) → Frontend Charts (3000)
   ↓ Historical        ↓ Token Auth       ↓ lightweight-charts
WebSocket (ws://8000) → WebSocket Bridge → Real-time Updates
```

**Required Backend APIs (Missing):**
```kotlin
GET  /api/v1/chart/{symbol}/daily        // Daily OHLCV data
GET  /api/v1/chart/{symbol}/current      // Current price info
GET  /api/v1/chart/{symbol}/indicators   // Moving averages, RSI
```

### Context Providers (Next.js)
```typescript
// Provider hierarchy in layout.tsx
<AuthProvider>          // JWT + KIS token management
  <TradingModeProvider> // LIVE/SANDBOX environment switching  
    <MarketProvider>    // Domestic/Overseas market routing
```

### Database Schema
- **Users**: Basic auth, JWT refresh tokens
- **KIS Accounts**: Encrypted API keys per user/environment
- **KIS Token History**: Token usage tracking for rate limiting

## Development Patterns

### API Calling Pattern
```typescript
// Frontend → KIS Adapter (direct) - Port 8000 with Trading Mode
const response = await fetch(`http://localhost:8000/domestic/price/005930?trading_mode=LIVE`, {
  headers: { 'X-KIS-Token': getActiveKISToken() }
});

// Frontend → KIS Adapter (SANDBOX 기본값)
const response = await fetch(`http://localhost:8000/domestic/price/005930`);

// Frontend → Backend (JWT required)
const response = await apiClient.get('/api/v1/auth/me', true);
```

### Error Handling Strategy
- **Token Expiration**: Automatic refresh for both JWT and KIS tokens
- **Rate Limiting**: Built into KIS Adapter (20/sec LIVE, 2/sec SANDBOX)
- **API Failures**: Graceful fallbacks and user notification

### Component Patterns
- **Protected Routes**: Automatic KIS setup flow for new users
- **Context Hooks**: useAuth(), useTradingMode(), useMarket()
- **UI Components**: Radix UI + Tailwind CSS + shadcn/ui
- **Chart Integration**: Lightweight Charts for market visualization

## Missing API Endpoints (Critical Implementation Needed)

### Trading Mode Management
**Current Issue**: `/api/v1/trading-mode/status` returns 500 error - controller not implemented

**Required Endpoints:**
```kotlin
GET  /api/v1/trading-mode/status     // Current mode (LIVE/SANDBOX)
POST /api/v1/trading-mode/toggle     // Switch between modes  
GET  /api/v1/trading-mode/history    // Mode change history
```

**Implementation Priority**: **CRITICAL** - Frontend is calling this API

### Chart Data APIs  
**Current Issue**: Frontend TradingChart.tsx calls missing backend endpoints

**Required Implementation:**
```kotlin
// ChartController.kt
GET  /api/v1/chart/{symbol}/daily         // Proxy to KIS Adapter
GET  /api/v1/chart/{symbol}/overseas      // Handle exchange routing
GET  /api/v1/chart/{symbol}/current       // Current price data

// KisChartService.kt  
fun getDomesticDailyChart(symbol: String)  // Call http://localhost:8000/domestic/chart/daily/{symbol}
fun getOverseasDailyChart(exchange: String, symbol: String) // Call KIS Adapter overseas endpoints
```

## Testing Strategy

### Backend Testing
```bash
./gradlew test                    # All tests
./gradlew test --tests="*Auth*"   # Authentication tests only
```

### API Testing
- KIS Adapter includes test files: `chk_*.py` pattern
- Postman collections in quantum-adapter-kis/legacy/postman/
- Example API calls in docs/planning/*.md files

### Integration Points to Test
1. JWT authentication flow end-to-end
2. KIS token issuance and refresh cycles  
3. Market data retrieval (domestic vs overseas)
4. Trading mode switching (LIVE ↔ SANDBOX)
5. CORS configuration between services

## Planning Documentation

Comprehensive planning documents in `docs/planning/`:
- **MVP_1.0_Complete_Login_KIS_Token_Integration.md**: Full authentication flow
- **MVP_1.0_Hybrid_KIS_Token_Architecture.md**: Token management architecture  
- **MVP_1.0_Chart_System_Specification.md**: Complete chart system MVP design with Kiwoom-style UI
- **MVP_1.0_Domestic_Overseas_Chart_Integration.md**: Market separation design
- **MVP_1.0_KIS_Rate_Limit_Policy.md**: API rate limiting implementation

## Security Considerations

### Token Management
- **JWT Tokens**: 24-hour expiration with refresh capability
- **KIS Tokens**: 6-hour expiration, stored client-side only
- **API Keys**: Server-side encryption, never exposed to client

### CORS Configuration
- Whitelisted origins: localhost:3000 (frontend), localhost:8080 (backend)
- Credentials allowed for cookie/token handling
- All HTTP methods permitted for development

### Rate Limiting
- **LIVE Environment**: 20 calls/second per account
- **SANDBOX Environment**: 2 calls/second per account  
- **WebSocket**: Maximum 41 concurrent registrations

## Troubleshooting

### Common Issues
1. **KIS Token Failures**: Check kis_devlp.yaml configuration and account permissions
2. **Database Connection**: Verify PostgreSQL is running on correct port
3. **CORS Errors**: Ensure all services are running and origins are configured
4. **Market Data Issues**: Verify KIS account has appropriate trading permissions
5. **Trading Mode API 500 Errors**: TradingModeController not implemented - priority backend task
6. **Chart Data Loading Fails**: Backend ChartController missing - needs KIS Adapter integration

### Development Workflow
1. Start PostgreSQL database
2. Run Spring Boot backend: `./gradlew bootRun` (Port 8080)
3. Run KIS Adapter: `uv run python main.py` (Port 8000) ← **Critical for chart data**
4. Run Next.js frontend: `npm run dev` (Port 3000)
5. Access application at configured host or localhost:3000

### Backend Development Priority
1. **URGENT**: Implement TradingModeController - Frontend calling `/api/v1/trading-mode/status`
2. **HIGH**: Implement ChartController + KisChartService for chart data routing
3. **MEDIUM**: WebSocket bridge for real-time chart updates

## KIS Adapter Trading Mode Implementation (완료)

### ✅ **구현 완료된 기능**
- **17개 API 엔드포인트** 모든 trading_mode 파라미터 적용 완료
- **통합 인증 시스템** 구축 (X-KIS-Token 헤더 > 설정 파일 우선순위)
- **서버 모드 매핑** 완성 (LIVE → prod, SANDBOX → vps)
- **OpenAPI 스펙** 자동 생성 및 Swagger UI 지원

### 🔧 **API 호출 패턴 (업데이트됨)**
```bash
# 기본 호출 (SANDBOX 모드, 기본값)
GET http://localhost:8000/domestic/price/005930

# 명시적 모드 지정
GET http://localhost:8000/domestic/price/005930?trading_mode=LIVE
X-KIS-Token: YOUR_ACCESS_TOKEN_HERE

# 지원되는 API 엔드포인트 (17개 전체)
- 국내 주식: price, chart/daily, chart/minute, orderbook, info, search (6개)
- 국내 지수: domestic, chart/daily, chart/minute (3개)  
- 해외 주식: price, chart/daily, chart/minute, info, search (5개)
- 해외 지수: overseas, chart/daily, chart/minute (3개)
```

### 🌐 **백엔드 API 연동 준비 완료**
```kotlin
// Spring Boot에서 KIS Adapter 호출 패턴
val response = restTemplate.getForObject(
    "http://localhost:8000/domestic/price/{symbol}?trading_mode={mode}",
    ApiResponse::class.java,
    mapOf(
        "symbol" to "005930",
        "mode" to tradingMode // LIVE | SANDBOX
    )
)
```

### 📱 **프론트엔드 통합 패턴**
```typescript
// 우선순위 기반 이중 인증 시스템
const response = await fetch(
  `http://localhost:8000/domestic/price/005930?trading_mode=${mode}`,
  {
    headers: {
      'X-KIS-Token': kisToken  // 1순위: 헤더 토큰
      // 2순위: 설정 파일 토큰 (자동 대체)
    }
  }
);
```

### 📋 **검증 완료 사항**
- ✅ 파라미터 유효성 검증 (LIVE|SANDBOX)
- ✅ 서버 모드 매핑 (LIVE→prod, SANDBOX→vps)  
- ✅ 토큰 우선순위화 (헤더 > 설정파일)
- ✅ OpenAPI 스펙 자동 생성
- ✅ 17개 API 전체 적용 완료

**참고 문서**: `docs/planning/MVP_1.0_KIS_Adapter_Trading_Mode_Implementation.md`