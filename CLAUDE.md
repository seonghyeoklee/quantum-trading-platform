# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Quantum Trading Platform** is a comprehensive stock trading system integrating two complementary components:
1. **quantum-trading-app**: Spring Boot web application with DINO analysis system
2. **quantum-adapter-kis**: Python FastAPI microservice for KIS Open API integration

## Technology Stack & Architecture

### quantum-trading-app (Primary Application)
- **Backend**: Spring Boot 3.5.6 + Java 21
- **Frontend**: Thymeleaf templates + Bootstrap 5.3 + Material UI design
- **Database**: PostgreSQL (primary) + H2 (testing)
- **Build Tool**: Gradle with Kotlin DSL
- **Features**: DINO stock analysis system, KIS token management, web interface

### quantum-adapter-kis (KIS API Service)
- **Framework**: Python FastAPI
- **Purpose**: KIS API integration, trading strategies, real-time data
- **Features**: Comprehensive trading analysis, VWAP strategies, sector trading

### Infrastructure
- **PostgreSQL**: Shared database for both services (port 5432)
- **Docker Compose**: Database orchestration (quantum-trading-app/docker-compose.yml)
- **Airflow**: Data pipeline orchestration (legacy/reference)
- **Web Client**: Next.js frontend (quantum-web-client - minimal structure)

## Development Commands

### quantum-trading-app (Main Application)

#### Database Setup (Required First)
```bash
cd quantum-trading-app/

# Start PostgreSQL
docker-compose up -d

# Verify database
docker logs quantum-postgres
docker exec quantum-postgres psql -U quantum -d quantum_trading -c "\dt"
```

#### Building and Running
```bash
# Build and run (standard workflow)
./gradlew bootRun

# Build only
./gradlew build

# Run tests
./gradlew test

# Run specific test
./gradlew test --tests "DinoFinanceServiceTest"

# Clean build
./gradlew clean build

# Stop database
docker-compose down
```

#### Java 21 Compatibility Note
May encounter compatibility issues between Gradle Kotlin DSL and Java 21. Simply retry:
```bash
./gradlew clean
./gradlew bootRun  # Usually succeeds on retry
```

### quantum-adapter-kis (KIS API Service)

#### Environment Setup
```bash
cd quantum-adapter-kis/

# Install dependencies (Python 3.13+ required)
uv sync

# Alternative with pip
pip install -r requirements.txt
```

#### Running Services
```bash
# Start FastAPI server
uv run python main.py

# Development with auto-reload
uvicorn main:app --reload --port 8000
```

#### Trading Systems Testing
```bash
# DINO analysis system
uv run python test_dino_finance.py
uv run python test_dino_technical.py 005930

# Sector trading system
cd sector_trading_test
uv run python manual_trader.py

# VWAP strategy
uv run python test_vwap_backtest.py
```

## Architecture Patterns

### Domain-Driven Design (KIS Module)
**quantum-trading-app** implements DDD patterns:

- **KisToken** (Aggregate Root): Token lifecycle management
- **Token** (Value Object): Immutable token data with expiration logic
- **KisTokenId** (Value Object): Composite identifier (environment + type)
- **KisTokenRepository**: Domain persistence abstraction
- **KisTokenPersistenceService**: Domain-infrastructure coordination

### Database Schema

PostgreSQL database `quantum_trading` is shared between both applications and contains the following key tables:

#### KIS Tokens (Shared by both services)
```sql
kis_tokens (
    environment VARCHAR(10),    -- PROD/VPS
    token_type VARCHAR(20),     -- ACCESS_TOKEN/WEBSOCKET_KEY
    token_value TEXT,
    expires_at TIMESTAMP,
    status VARCHAR(10),         -- ACTIVE/EXPIRED/INVALID
    PRIMARY KEY (environment, token_type)
)
```

#### DINO Analysis Results
```sql
dino_finance_results (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10),
    analysis_date DATE,
    revenue_growth_score INTEGER,
    operating_profit_score INTEGER,
    operating_margin_score INTEGER,
    retention_rate_score INTEGER,
    debt_ratio_score INTEGER,
    total_score INTEGER,         -- 0-5 final score
    UNIQUE(stock_code, analysis_date)
)
```

#### Daily Chart Data (Used by both services)
```sql
daily_chart_data (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10),
    stck_bsop_date DATE,        -- Business operation date
    stck_clpr DECIMAL(10,2),    -- Closing price
    stck_oprc DECIMAL(10,2),    -- Opening price
    stck_hgpr DECIMAL(10,2),    -- High price
    stck_lwpr DECIMAL(10,2),    -- Low price
    acml_vol BIGINT,            -- Volume
    acml_tr_pbmn DECIMAL(15,2), -- Trading value
    UNIQUE(stock_code, stck_bsop_date)
)
```

### DINO Analysis System (15-Point Stock Evaluation)

**Implementation**: quantum-trading-app/src/main/java/com/quantum/dino/
**Algorithm**: `MAX(0, MIN(5, 2 + individual_scores))` (Python → Java translation)

**5 Finance Metrics**:
- Revenue growth analysis
- Operating profit evaluation
- Operating margin assessment
- Retained earnings analysis
- Debt ratio evaluation

### Token Management Strategy
- **Automatic Reuse**: PostgreSQL caching until expiration
- **Proactive Renewal**: 1 hour before expiration
- **Scheduled Maintenance**: Daily refresh (9 AM KST)
- **Environment Isolation**: Separate PROD/VPS tokens
- **Cross-Service**: Shared by both applications via database
- **Database-First**: quantum-adapter-kis has `db_token_manager.py` for direct PostgreSQL access

## Configuration

### Application Configuration
**quantum-trading-app**: `src/main/resources/application.yml`
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/quantum_trading
    username: quantum
    password: quantum123
  jpa:
    hibernate:
      ddl-auto: update  # Auto-schema updates
```

**quantum-adapter-kis**: Uses same database via `db_token_manager.py`
```python
# Database connection details
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "quantum_trading",
    "user": "quantum",
    "password": "quantum123"
}
```

### Secret Management
**Both applications**: `application-secrets.yml` (git-ignored)
- KIS API credentials (prod/vps keys)
- Account numbers and HTS ID
- Auto-imported by Spring Boot

### KIS API Configuration
**quantum-adapter-kis**: `kis_devlp.yaml` at project root
```yaml
my_app: "실전투자_앱키"
my_sec: "실전투자_앱시크릿"
paper_app: "모의투자_앱키"
paper_sec: "모의투자_앱시크릿"
my_htsid: "사용자_HTS_ID"
my_acct_stock: "증권계좌_8자리"
my_prod: "01"
```

## Key Endpoints & Services

### quantum-trading-app (Web Interface)
- `GET /`: Dashboard overview
- `GET /dino`: DINO stock analysis interface
- `GET /api/kis/tokens/status`: Token management status

### quantum-adapter-kis (API Service)
- `GET /domestic/price/{symbol}`: Current stock price
- `GET /domestic/chart/{symbol}`: Chart data
- `GET /dino-test/finance/{stock_code}`: Financial analysis
- `WebSocket /ws/realtime`: Real-time data streaming

## Development Guidelines

### KIS Token Management
- Use `KisTokenManager` for token access (not `KisTokenService` directly)
- Tokens automatically cached and reused from PostgreSQL
- No manual refresh needed - handled by scheduling
- Persistence ensures continuity across restarts

### DINO System Development
- Finance analysis follows exact Python algorithm translation
- Scoring: `MAX(0, MIN(5, 2 + sum_of_individual_scores))`
- One analysis per stock per day with database caching
- Business logic in service layer, controllers handle web concerns

### Data Integrity Rules
**CRITICAL**: Never generate mock/dummy/fake data when APIs fail

When KIS API calls fail or data unavailable:
- ✅ **CORRECT**: Return HTTP error codes (404, 503, etc.)
- ❌ **FORBIDDEN**: Generate placeholder or dummy data

## Quick Start Checklist

1. **Prerequisites**: Java 21, Python 3.13+, Docker Desktop
2. **Database**: `cd quantum-trading-app && docker-compose up -d`
3. **Secrets**: Verify `application-secrets.yml` exists in resources
4. **Main App**: `./gradlew bootRun` (retry if build error)
5. **KIS Service**: `cd quantum-adapter-kis && uv sync && uv run python main.py`
6. **Verify**: Visit `http://localhost:8080/dino` for DINO analysis
7. **API Test**: `curl http://localhost:8000/health` for KIS service

## Common Development Tasks

### Database Operations
```bash
# Check PostgreSQL status
docker ps --filter "name=quantum-postgres"

# View logs
docker logs quantum-postgres --tail 50

# Reset database (removes all data)
cd quantum-trading-app
docker-compose down -v && docker-compose up -d

# Connect to database
docker exec quantum-postgres psql -U quantum -d quantum_trading
```

### Service Monitoring
```bash
# Spring Boot application logs
cd quantum-trading-app
./gradlew bootRun | grep -E "(ERROR|WARN|DINO|KIS)"

# FastAPI service logs
cd quantum-adapter-kis
uv run python main.py

# Check token status
curl -s http://localhost:8080/api/kis/tokens/status | jq .
curl -s http://localhost:8000/auth/refresh-token?environment=prod
```

### Testing Individual Components
```bash
# Test DINO analysis
cd quantum-trading-app
./gradlew test --tests "*Dino*"

# Test KIS integration patterns
cd quantum-adapter-kis/examples_llm/domestic_stock/inquire_price
python chk_inquire_price.py

# Test sector trading
cd quantum-adapter-kis/sector_trading_test
uv run python test_system.py

# Test database token management
cd quantum-adapter-kis
uv run python -c "from db_token_manager import is_db_available; print('DB Available:', is_db_available())"

# Test DINO scoring system
uv run python test_dino_finance.py 005930
uv run python test_dino_technical.py 005930
uv run python test_dino_price.py 005930
```

---

*Last Updated: 2025-09-24*
*Status: Dual Architecture - Spring Boot App + FastAPI Service*