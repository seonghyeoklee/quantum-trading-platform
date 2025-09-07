# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Quantum Trading Platform** is an automated stock trading system built around Korea Investment & Securities (KIS) Open API integration. The platform uses a hybrid microservices architecture with JWT-based authentication, multi-environment KIS token management, and comprehensive analysis pipelines powered by Apache Airflow and Spring AI integration.

### Recent Major Additions
- **External Data Adapter**: Complete quantum-adapter-external module with real-time Naver News API and comprehensive DART public disclosure system integration
- **Apache Airflow Analysis Pipeline**: Fully functional daily stock analysis system with 10 complex DAGs
- **Spring AI Integration**: OpenAI GPT-4o-mini integration for intelligent market analysis  
- **Comprehensive Batch Analyzer**: Multi-source data analysis system (PyKRX, yfinance, FinanceDataReader)
- **Sector-Based Trading System**: Automated trading across 6 key sectors with intelligent order management

## Architecture Overview

### Microservices Structure
```
Frontend (Port 3000) ← → Backend (Port 8080) ← → KIS Adapter (Port 8000)
Next.js 15 + React 19      Spring Boot 3.5 + Kotlin    FastAPI + Python 3.13
                                      ↓
                           External Adapter (Port 8001)
                           FastAPI + Python 3.13 + Naver News + DART APIs
```

### Key Architectural Decisions
- **Server-side KIS Token Management**: All KIS authentication handled by backend
- **Multi-Environment Support**: LIVE (production) and SANDBOX (demo) trading  
- **Real-time Data**: WebSocket at ws://localhost:8000/ws/realtime
- **Chart System**: lightweight-charts v5.0.8 integration

## Development Commands

### Frontend (quantum-web-client/)
```bash
npm run dev              # Runs on quantum-trading.com:3000 (custom host)
npm run dev:local        # Runs on localhost:3000
npm run build
npm run start
npm run lint

# Frontend uses Next.js 15.5.2 with App Router
# React Strict Mode is disabled to prevent chart duplications
# API proxying configured: /api/kis/* → adapter.quantum-trading.com:8000/*
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
uv sync                  # Install dependencies with uv (Python 3.13+ required)
uv run python main.py    # Run FastAPI server on port 8000

# Run sector trading test system
cd sector_trading_test
uv run python manual_trader.py      # Interactive trading console
uv run python test_full_system.py   # System verification

# Comprehensive analysis system (recently fixed for Airflow)
uv run python -c "from trading_strategy.comprehensive_batch_analyzer import ComprehensiveBatchAnalyzer; c = ComprehensiveBatchAnalyzer(); c.run_comprehensive_analysis_sync()"

# Test individual analysis components
uv run python test_single_stock.py  # Single stock analysis test
uv run python test_ai_features.py   # AI-powered analysis test
```

### Sector Trading System Commands
```bash
# In quantum-adapter-kis/sector_trading_test/
uv run python manual_trader.py      # Manual trading console with approval workflow
uv run python test_full_system.py   # Full system verification test
uv run python test_system.py        # Basic system test

# Core modules (available for import)
# core/sector_portfolio.py     - Portfolio management
# core/enhanced_analyzer.py    - Advanced analysis without KIS API
# core/smart_order_manager.py  - Intelligent price optimization
# core/simple_data_provider.py - PyKRX/yfinance data access
```

### External Adapter (quantum-adapter-external/)
```bash
uv sync                  # Install dependencies with uv (Python 3.13+ required)
uv run python main.py    # Run FastAPI server on port 8001

# Test API endpoints with custom domain (hosts configured)
curl "http://external-api.quantum-trading.com:8001/health"                   # Health check
curl "http://external-api.quantum-trading.com:8001/news/search?query=삼성전자&display=5"  # Search news
curl "http://external-api.quantum-trading.com:8001/news/latest/애플?count=3" # Latest news
curl "http://external-api.quantum-trading.com:8001/news/financial/삼성전자"   # Financial news

# DART Disclosure API endpoints
curl "http://external-api.quantum-trading.com:8001/disclosure/recent?days=3&count=5"         # Recent disclosures
curl "http://external-api.quantum-trading.com:8001/disclosure/company/00126380?days=60&count=3"  # Samsung disclosures
curl "http://external-api.quantum-trading.com:8001/disclosure/periodic?days=7&count=3"       # Periodic disclosures (정기공시)
curl "http://external-api.quantum-trading.com:8001/disclosure/major?days=7&count=3"          # Major disclosures (주요사항보고)
curl "http://external-api.quantum-trading.com:8001/disclosure/search-company/삼성?count=5"    # Search by company keyword
curl "http://external-api.quantum-trading.com:8001/disclosure/company-info/00126380"         # Company information (기업개황)
curl "http://external-api.quantum-trading.com:8001/disclosure/company-info/00164779"         # SK Hynix company info
curl "http://external-api.quantum-trading.com:8001/disclosure/types"                         # Disclosure types reference

# API Documentation (when DEBUG=true)
# http://external-api.quantum-trading.com:8001/docs
```

### Airflow Analysis Pipeline
```bash
# Start unified infrastructure with Airflow, monitoring, and database (VERIFIED WORKING)
cd quantum-infrastructure
./start-infrastructure.sh

# Access Airflow UI
# URL: http://localhost:8081
# Login: admin / quantum123

# Manual DAG triggers via REST API (properly formatted)
TIMESTAMP=$(date +%s)
LOGICAL_DATE=$(date -u +%Y-%m-%dT%H:%M:%S)Z
curl -X POST "http://localhost:8081/api/v1/dags/quantum_daily_stock_analysis/dagRuns" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'admin:quantum123' | base64)" \
  -d "{\"dag_run_id\": \"manual_test_${TIMESTAMP}\", \"logical_date\": \"${LOGICAL_DATE}\"}"

# Key DAGs Available:
# - quantum_daily_stock_analysis (MAIN) - Comprehensive daily analysis
# - ai_data_collection_dag - AI-powered market data collection
# - ml_signal_training_dag - Machine learning signal generation
# - auto_trading_comprehensive_dag - Automated trading execution
# - portfolio_rebalancing_dag - Portfolio optimization
# - risk_management_dag - Risk assessment and monitoring
```

### Infrastructure & Monitoring
```bash
cd quantum-infrastructure
./start-infrastructure.sh    # Start unified infrastructure (Airflow, monitoring, database)
# Grafana: http://localhost:3001 (admin/quantum2024)
# Prometheus: http://localhost:9090
# Airflow: http://localhost:8081 (admin/quantum123)
```

## Configuration Requirements

### Environment Setup
1. **PostgreSQL Database**: Port 5433 (dev), 5432 (prod)
   - Database: `quantum_trading`
   - Username: `quantum` 
   - Password: `quantum123`

2. **KIS API Configuration**: Create `kis_devlp.yaml` in quantum-adapter-kis/
   ```yaml
   # Example kis_devlp.yaml structure
   my_app: "실전투자_앱키"
   my_sec: "실전투자_앱시크릿"
   paper_app: "모의투자_앱키"
   paper_sec: "모의투자_앱시크릿"
   my_htsid: "사용자_HTS_ID"
   my_acct_stock: "증권계좌_8자리"
   my_prod: "01"  # 종합계좌
   ```

3. **External APIs Configuration**: Create `.env` in quantum-adapter-external/
   ```yaml
   # Example .env structure for external adapter
   NAVER_CLIENT_ID=your_naver_client_id
   NAVER_CLIENT_SECRET=your_naver_client_secret
   DART_API_KEY=your_dart_api_key_from_opendart.fss.or.kr
   DEBUG=true
   SERVER_PORT=8001
   ```

4. **JWT Secret**: Configured in application.yml

5. **KIS Token Storage**: Configure path in kis_auth.py
   ```python
   # Line 39 in kis_auth.py
   config_root = os.path.join(os.path.expanduser("~"), "KIS", "config")
   ```

### Port Configuration
- **Frontend**: 3000 (Next.js) - quantum-trading.com:3000 or localhost:3000
- **Backend**: 8080 (Spring Boot) - api.quantum-trading.com:8080
- **KIS Adapter**: 8000 (FastAPI) - adapter.quantum-trading.com:8000
- **External Adapter**: 8001 (FastAPI) - external-api.quantum-trading.com:8001
- **Database**: 5432 (PostgreSQL - unified for trading platform & Airflow)
- **Airflow**: 8081 (Web UI)
- **Monitoring**: Grafana (3001), Prometheus (9090), Loki (3100)

### Hosts File Configuration
Add these entries to `/etc/hosts` for custom domain access:
```
127.0.0.1 quantum-trading.com
127.0.0.1 api.quantum-trading.com  
127.0.0.1 adapter.quantum-trading.com
127.0.0.1 external-api.quantum-trading.com
```

## Comprehensive DAG Analysis System

The Airflow pipeline includes 10 sophisticated DAGs for complete market analysis:

### Core Analysis DAGs
1. **quantum_daily_stock_analysis** - Main comprehensive analysis (28+ stocks)
2. **ai_data_collection_dag** - AI-powered market data aggregation
3. **ml_signal_training_dag** - Machine learning model training for signals
4. **auto_trading_comprehensive_dag** - Automated trading decision engine
5. **portfolio_rebalancing_dag** - Dynamic portfolio optimization

### Monitoring & Risk DAGs  
6. **performance_monitoring_dag** - Real-time performance tracking
7. **risk_management_dag** - Risk assessment and mitigation
8. **realtime_signal_processing_dag** - Live signal analysis
9. **quantum_realtime_monitoring_dag** - System health monitoring
10. **quantum_multi_language_example** - Multi-language integration demo

**Schedule**: Main analysis runs weekdays at 18:00 (6 PM) after market close.
**Data Processing**: Handles both domestic (KRX) and overseas (NYSE, NASDAQ) markets.
**Output**: JSON files in `analysis_results/` and PostgreSQL database storage.

## High-Level Architecture

### Infrastructure Organization
```
quantum-infrastructure/
├── airflow/                        # Airflow configuration files
│   ├── docker-compose.airflow.yml          # Full CeleryExecutor setup
│   ├── docker-compose.airflow.simple.yml   # LocalExecutor setup (recommended)
│   └── .env.airflow                        # Airflow environment variables
├── monitoring/                     # Monitoring stack configuration
├── docker-compose.monitoring.yml   # Grafana + Prometheus + Loki
├── start-monitoring.sh            # Helper script
└── test-monitoring.sh             # Monitoring validation
```

### Sector Trading System Architecture (NEW)
```
sector_trading_test/
├── core/                           # Core modules
│   ├── sector_portfolio.py        # 6-sector portfolio management
│   ├── enhanced_analyzer.py       # Analysis without KIS API (PyKRX/yfinance)
│   ├── smart_order_manager.py     # Intelligent order pricing (AGGRESSIVE/BALANCED/PATIENT)
│   ├── simple_data_provider.py    # Multi-source data provider (PyKRX priority)
│   ├── manual_executor.py          # Manual approval workflow
│   └── trade_logger.py            # Trade logging system
├── config/                        # Configuration files
│   ├── sectors_2025.yaml          # 2025 sector definitions
│   ├── strategy_config.yaml       # Trading strategy settings
│   └── risk_management.yaml       # Risk parameters
├── manual_trader.py               # Main interactive console
├── test_full_system.py            # Comprehensive verification
└── test_system.py                 # Basic system test

Sector Portfolio (1,000만원 total):
- 조선 (HD한국조선해양, 대우조선해양)
- 방산 (한화에어로스페이스, KAI)  
- 원자력 (두산에너빌리티, 한전KPS)
- AI (NAVER, 카카오)
- 반도체 (삼성전자, SK하이닉스)
- 바이오 (삼성바이오로직스, 셀트리온)
```

### Backend Architecture Pattern (Hexagonal + DDD)
```
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

### Frontend Architecture (Next.js App Router)
```
src/
├── app/                    # Next.js 13+ App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page
│   ├── domestic/          # Domestic trading pages
│   ├── overseas/          # Overseas trading pages
│   └── calendar/          # Holiday calendar
├── components/            # React components
│   ├── ui/               # shadcn/ui base components
│   ├── auth/             # Authentication components
│   ├── chart/            # Trading charts (lightweight-charts)
│   ├── layout/           # Layout components (Header, etc.)
│   ├── kis/              # KIS-specific components
│   └── market/           # Market indicators
├── contexts/             # React Context providers
│   ├── AuthContext.tsx   # User authentication state
│   ├── MarketContext.tsx # Market data state
│   └── TradingModeContext.tsx # LIVE/SANDBOX mode
├── lib/                  # Utilities and services
│   ├── api-client.ts     # Backend API client
│   └── services/         # External API services
└── hooks/                # Custom React hooks
```

### Data Flow Architecture
```
User Request → Frontend → Backend API → KIS Adapter → KIS OpenAPI
                  ↑           ↓             ↓
                JWT Auth   Server KIS    Market Data
                            ↓             ↓
                      AI Analysis ← Stock Analysis DB
                            ↑
                    Airflow Pipeline (Daily 18:00)
                    └── Sector Trading System
                         ├── PyKRX Data (No rate limit)
                         ├── Smart Order Manager
                         └── Manual Approval Workflow
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

## Technology Stack & Dependencies

### Frontend (quantum-web-client/)
- **Next.js 15.5.2** + React 19.1.0 (App Router architecture)
- **UI Components**: Radix UI primitives + Tailwind CSS + shadcn/ui
- **Forms**: React Hook Form + Zod validation
- **Charts**: lightweight-charts v5.0.8 (Korean colors: red=up, blue=down)
- **Themes**: next-themes for dark/light mode
- **State Management**: React Context (Auth, Market, TradingMode)
- **Fonts**: Geist Sans + Geist Mono

### Backend (quantum-web-api/)
- **Spring Boot 3.5.5** + Kotlin 1.9.25 + Java 21
- **Database**: PostgreSQL + Spring Data JPA
- **Security**: JWT authentication + Spring Security
- **HTTP Client**: WebFlux WebClient for KIS API calls
- **AI Integration**: Spring AI 0.8.1 + OpenAI GPT models
- **Monitoring**: Actuator + Prometheus metrics + Logbook HTTP logging

### KIS Adapter (quantum-adapter-kis/)
- **FastAPI** + Python 3.13 + uvicorn
- **Trading Libraries**: 
  - PyKRX 1.0.51+ (Korean stock data without API limits)
  - yfinance 0.2.0+ (fallback data source)
  - pandas-ta 0.3.14b0 (technical indicators)
  - backtrader 1.9.78+ (backtesting)
  - scikit-learn 1.7.1+ (machine learning)
  - aiohttp 3.12.15+ (async HTTP operations)
- **Architecture**: 17 REST endpoints + WebSocket real-time data + Airflow integration

### External Adapter (quantum-adapter-external/)
- **FastAPI** + Python 3.13 + uvicorn
- **News API Integration**: Naver News API for real-time financial news
- **DART API Integration**: Korea Financial Supervisory Service public disclosure system
- **HTTP Client**: httpx 0.25+ for async API calls
- **Environment Management**: python-dotenv for configuration
- **Validation**: Pydantic models for API request/response validation
- **Architecture**: 12 REST endpoints (4 news + 8 disclosure) + health monitoring

### Apache Airflow (Analysis Pipeline)
- **Airflow 2.8.2** with LocalExecutor setup
- **Core Dependencies**: pandas, numpy, psycopg2-binary, pykrx, pandas-ta, backtrader
- **Analysis Modules**: ComprehensiveBatchAnalyzer, AI data collection, ML signal generation
- **Database**: PostgreSQL (port 5432) - unified database for both trading platform and Airflow metadata

## Sector Trading System Details

### Smart Order Manager Strategies
```python
# Three intelligent pricing strategies based on market conditions:
AGGRESSIVE: Market orders for strong signals (RSI < 30 or > 70)
BALANCED: 0.5% discount/premium for normal conditions  
PATIENT: 1.0% discount/premium for high volatility
```

### Data Provider Priority
```python
# Avoids KIS API rate limits by using alternative sources:
1. PyKRX (primary) - No rate limits, real Korean market data
2. yfinance (secondary) - Global market data fallback
3. FinanceDataReader (tertiary) - Alternative Korean data source
4. KIS API (last resort) - Only when others unavailable
```

### Risk Management
- Maximum 30% allocation per sector
- Minimum 5% per sector
- Single stock limit: 10% of portfolio
- Auto-rebalancing signals when allocation deviates >5%

## Development Workflow

### Standard Startup Sequence
1. **Infrastructure**: Start unified infrastructure stack with `cd quantum-infrastructure && ./start-infrastructure.sh`
2. **Backend**: `cd quantum-web-api && ./gradlew bootRun`
3. **KIS Adapter**: `cd quantum-adapter-kis && uv run python main.py`
4. **Frontend**: `cd quantum-web-client && npm run dev`
5. **Sector Trading** (optional): `cd quantum-adapter-kis/sector_trading_test && uv run python manual_trader.py`
6. **Infrastructure Services**: All monitoring, Airflow, and database services managed through unified infrastructure

### Testing & Debugging
- **Frontend Development**:
  - Use browser DevTools for React Component debugging
  - Check Context state in React DevTools (Auth, Market, TradingMode)
  - Monitor API calls in Network tab (proxied through Next.js to KIS Adapter)
  - Chart debugging: React Strict Mode disabled to prevent duplicate chart instances
- **Airflow System Verification**: 
  - Monitor DAG execution via UI at http://localhost:8081
  - Check task logs: `docker exec airflow-scheduler cat /opt/airflow/logs/dag_id=quantum_daily_stock_analysis/[run_id]/task_id=[task]/attempt=1.log`
  - Verified working: ComprehensiveBatchAnalyzer with 28+ stock analysis
- **Sector Trading Tests**: 
  - `uv run python test_full_system.py` - Comprehensive system verification
  - `uv run python test_system.py` - Basic functionality test
- **Backend Tests**: `./gradlew test` (all) or `./gradlew test --tests="*Auth*"` (filtered)
- **KIS API Testing**: Individual API test files in `chk_*.py` pattern
- **Analysis System Tests**: Located in `tests/` directory and `trading_strategy/` tests

## Critical System Integration Notes

### Airflow Analysis System (Recently Stabilized)
**Key Fixes Applied**:
- Fixed `ComprehensiveBatchAnalyzer` stock_list attribute error: `self.stock_list` → `self.stock_master.keys()`
- Resolved async/sync integration: Added asyncio event loop wrapper in `run_comprehensive_analysis_sync()`
- Fixed method naming: `save_to_json` → `_save_to_json` with proper parameters
- Removed Python 3.8 incompatible yfinance to resolve TypedDict issues
- Fixed datetime import shadowing in local scope

**Docker Container Rebuild Required**: When modifying analysis code, rebuild containers:
```bash
cd quantum-infrastructure/airflow
docker-compose -f docker-compose.airflow.simple.yml down
docker-compose -f docker-compose.airflow.simple.yml up -d --build
```

**Analysis Data Sources Priority**: MultiDataProvider uses PyKRX as primary source to avoid KIS API rate limits.

### Spring AI Integration Requirements
- **OpenAI API Key**: Must be set as environment variable `OPENAI_API_KEY`
- **Model Configuration**: GPT-4o-mini with temperature 0.1 for consistent analysis
- **Fallback Behavior**: System gracefully handles missing API key but AI features will be disabled

## Important Notes

### Rate Limiting & Performance
- **KIS LIVE API**: 20 calls/second per account
- **KIS SANDBOX API**: 2 calls/second per account  
- **PyKRX Alternative**: No rate limits, recommended for analysis
- **WebSocket Limits**: Max 41 concurrent registrations
- **Chart Data**: Automatic 90-day splitting for large date ranges

### Security & Authentication
- **JWT Tokens**: 24-hour expiration with refresh capability
- **KIS Tokens**: Server-side only, 6-hour expiration, auto-refresh
- **API Keys**: Never exposed to client, stored in `kis_devlp.yaml`
- **Token Storage**: Configured path in `~/KIS/config/` by default

## Current Implementation Status

### ✅ Completed
- **External Data Adapter**: Complete quantum-adapter-external service
  - Real-time Naver News API integration (4 endpoints)
  - Comprehensive DART public disclosure system integration (8 endpoints)
  - Company information (기업개황) and disclosure search capabilities
  - Custom domain support: external-api.quantum-trading.com:8001
  - Pydantic validation models and comprehensive error handling
- **Apache Airflow Pipeline**: Fully functional daily analysis system
  - 10 complex DAGs for comprehensive market analysis
  - Verified ComprehensiveBatchAnalyzer processing 28+ stocks
  - Fixed async/sync integration issues, Python 3.8 compatibility
  - Multi-source data integration (PyKRX priority, yfinance fallback)
- **Spring AI Integration**: OpenAI GPT-4o-mini for market intelligence
  - AI-powered stock analysis and recommendations
  - Configurable model parameters (temperature: 0.1)
  - Environment variable configuration for API keys
- **Sector Trading System**: Complete automated trading system with 6 sectors
  - Smart order management with intelligent pricing
  - PyKRX integration to avoid KIS API rate limits
  - Manual approval workflow for trade execution
  - Comprehensive testing suite
- **Frontend**: Next.js app with chart system
- **KIS Adapter**: FastAPI server with 17 endpoints + WebSocket
- **Backend**: Spring Boot API with JWT auth, KIS token management, AI integration
- **Infrastructure**: Complete monitoring stack with Airflow integration
- **Analysis Engine**: Multi-source data providers with comprehensive batch processing

### 🔧 In Progress  
- **Backend Controllers**: ChartController, TradingModeController
- **WebSocket Bridge**: Backend relay from KIS Adapter to Frontend
- **Fully Automated Trading**: Remove manual approval requirement

### 📋 Pending
- **ML Integration**: Machine learning models for prediction
- **Real-time Analytics**: Live market analysis during trading hours
- **Portfolio Optimization**: Advanced allocation algorithms