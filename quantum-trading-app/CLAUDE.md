# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Quantum Trading App** is a Spring Boot 3.5.6 application built with Java 21, designed as a web-based admin interface for automated stock trading using Korea Investment & Securities (KIS) Open API. The application features a sophisticated DINO (15-point stock evaluation system), backtesting functionality, and uses Thymeleaf for server-side rendering with a modern Material UI design system.

## Technology Stack

- **Backend**: Spring Boot 3.5.6 + Java 21
- **Frontend**: Thymeleaf templates + Bootstrap 5.3 + Material UI design principles
- **Database**: PostgreSQL (primary) + H2 (testing)
- **Build Tool**: Gradle with Kotlin DSL
- **Infrastructure**: Docker Compose for PostgreSQL
- **Static Resources**: CSS with Material Design patterns, vanilla JavaScript

## Development Commands

### Database Setup (Required First)
```bash
# Start PostgreSQL with Docker Compose
docker-compose up -d

# Verify PostgreSQL is running
docker logs quantum-postgres

# Check database tables (after first run)
docker exec quantum-postgres psql -U quantum -d quantum_trading -c "\dt"

# Connect to database for manual queries
docker exec quantum-postgres psql -U quantum -d quantum_trading
```

### Building and Running
```bash
# 🚀 Standard run (with PostgreSQL and real KIS API)
./gradlew bootRun

# 📦 Build the application
./gradlew build

# 🧪 Run tests
./gradlew test

# 🔍 Run specific test class
./gradlew test --tests "DinoFinanceServiceTest"

# 🧹 Clean build
./gradlew clean build

# 🔧 Stop PostgreSQL when done
docker-compose down
```

### Troubleshooting Java 25 Build Issues
```bash
# If build fails with "IllegalArgumentException: 25", retry:
./gradlew clean
./gradlew bootRun  # Usually succeeds on 2nd-3rd attempt
```

### Secret Management
The application uses `application-secrets.yml` for KIS API credentials:
- **Location**: `src/main/resources/application-secrets.yml`
- **Status**: File exists and is git-ignored for security
- **Contents**: Real KIS API keys, account numbers, HTS ID
- **Import**: Automatically loaded via `spring.config.import` in application.yml

### Java 25 Compatibility Note

This project specifically requires Java 25. There are known compatibility issues with Gradle's Kotlin DSL and Java 25 that may cause build failures with error messages like `IllegalArgumentException: 25`. The project is configured to work with Java 25 despite these issues - persist with the build commands as they typically succeed on subsequent attempts.

## Architecture Overview

### Package Structure

- **`com.quantum`**: Root package containing the main application class
- **`com.quantum.controller`**: Web controllers (Dashboard)
- **`com.quantum.kis`**: KIS API integration module (Domain-Driven Design)
  - **`config`**: Configuration classes for KIS API credentials and settings
  - **`service`**: Business logic for KIS API operations (token management, persistence)
  - **`dto`**: Data Transfer Objects for API requests/responses
  - **`domain`**: Core domain objects and value objects (KisEnvironment, TokenType, Token, KisToken)
  - **`infrastructure`**: JPA entities and repository implementations
  - **`scheduler`**: Automated token refresh and cleanup
  - **`exception`**: Custom exceptions for KIS API errors
- **`com.quantum.dino`**: DINO stock evaluation system
  - **`controller`**: Web controller for DINO analysis interface
  - **`service`**: Finance analysis business logic (translates Python algorithms to Java)
  - **`dto`**: Result DTOs for analysis output
  - **`domain`**: JPA entities for storing analysis results
- **`com.quantum.backtest`**: Backtesting system (Domain-Driven Design + Hexagonal Architecture)
  - **`domain`**: Core domain objects (Backtest, Trade, BacktestConfig, BacktestResult, PriceData)
  - **`application/port/in`**: Use case interfaces (RunBacktestUseCase, GetBacktestUseCase, CancelBacktestUseCase)
  - **`application/port/out`**: Repository abstractions (BacktestRepositoryPort, MarketDataPort)
  - **`application/service`**: Business logic implementation (BacktestApplicationService)
  - **`infrastructure/adapter/in/web`**: Web controllers (BacktestController)
  - **`infrastructure/adapter/out/persistence`**: JPA repository implementations
  - **`infrastructure/adapter/out/market`**: Market data adapters (MockMarketDataAdapter)
  - **`infrastructure/persistence`**: JPA entities (BacktestEntity, TradeEntity)

### Key Architectural Patterns

#### Domain-Driven Design (KIS Module)
The KIS token management follows DDD principles:
- **`KisToken`** (Aggregate Root): Manages token lifecycle and business rules
- **`Token`** (Value Object): Immutable token data with expiration logic
- **`KisTokenId`** (Value Object): Composite identifier (environment + token type)
- **`KisTokenRepository`** (Repository Interface): Domain persistence abstraction
- **`KisTokenPersistenceService`**: Coordinates between domain and infrastructure

#### Token Management Strategy
- **Automatic Reuse**: Tokens are cached in PostgreSQL and reused until expiration
- **Proactive Renewal**: Tokens renewed 1 hour before expiration to prevent failures
- **Scheduled Maintenance**: Daily refresh (9 AM KST) and cleanup cycles
- **Environment Isolation**: Separate tokens for PROD/VPS environments

#### DINO Analysis System
15-point stock evaluation system with 5 finance metrics:
- **Finance Analyzer**: Revenue growth, operating profit, margins, debt ratios
- **Scoring Algorithm**: `MAX(0, MIN(5, 2 + individual_scores))` (Python → Java translation)
- **Daily Analysis**: One analysis per stock per day with result caching
- **Sample Data**: Samsung Electronics (005930) included for testing

#### Backtesting System (Hexagonal Architecture)
Complete backtesting engine following DDD + Hexagonal Architecture principles:
- **Core Domain**: Pure business logic (Backtest aggregate root, Trade value objects)
- **Application Layer**: Use cases and service orchestration (BacktestApplicationService)
- **Infrastructure Layer**: Adapters for web, persistence, and market data
- **Synchronous Execution**: Simplified from async to avoid concurrency issues
- **Strategy Support**: Currently implements Buy-and-Hold strategy
- **Result Calculation**: Comprehensive metrics including returns, drawdown, trade statistics

### Database Schema

#### KIS Tokens Table
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

#### DINO Results Table
```sql
dino_finance_results (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10),
    analysis_date DATE,
    revenue_growth_score INTEGER,  -- ±1 points
    operating_profit_score INTEGER, -- ±2 points
    operating_margin_score INTEGER, -- +1 point
    retention_rate_score INTEGER,   -- ±1 point
    debt_ratio_score INTEGER,       -- ±1 point
    total_score INTEGER,            -- 0-5 final score
    UNIQUE(stock_code, analysis_date)
)
```

#### Backtesting Tables
```sql
backtests (
    id VARCHAR(36) PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) NOT NULL,
    strategy_type VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    progress_percentage INTEGER NOT NULL DEFAULT 0,
    -- Result fields
    total_return DECIMAL(8,4),
    annualized_return DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    total_trades INTEGER,
    win_trades INTEGER,
    loss_trades INTEGER,
    win_rate DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    final_capital DECIMAL(15,2),
    total_fees DECIMAL(15,2)
)

trades (
    id BIGSERIAL PRIMARY KEY,
    backtest_id VARCHAR(36) NOT NULL REFERENCES backtests(id),
    trade_timestamp TIMESTAMP NOT NULL,
    trade_type VARCHAR(255) NOT NULL, -- BUY/SELL
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    reason VARCHAR(500)
)
```

## Configuration

### Database Configuration
PostgreSQL is the primary database with automatic schema updates:
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/quantum_trading
    username: quantum
    password: quantum123
  jpa:
    hibernate:
      ddl-auto: update  # Auto-creates/updates schema
```

### Secret Management
Sensitive KIS API credentials are stored in `application-secrets.yml` (git-ignored):
- Production and VPS API keys
- Account numbers and HTS ID
- Automatically imported by Spring Boot

## Design System

### CSS Architecture
- **CSS Custom Properties**: Theme-aware color system with light/dark mode support
- **Material Design**: Clean, flat design with appropriate shadows and typography
- **Component Classes**:
  - `.stat-card`: Dashboard metric cards with hover effects
  - `.sidebar`: Fixed navigation with Material design principles
  - `.main-content`: Responsive content area with proper spacing

### Modern Color Palette
- **Primary**: `#6366f1` (Indigo - Trust & Professionalism)
- **Success**: `#10b981` (Emerald - Profit/Success)
- **Warning**: `#f59e0b` (Amber - Caution)
- **Error**: `#ef4444` (Red - Loss/Risk)
- **Info**: `#0ea5e9` (Sky Blue - Information)
- **Background**: `#f1f5f9` (Slate 100)
- **Cards**: Gradient effects with hover animations

## Key Endpoints

### Main Application Routes
- `GET /`: Dashboard with system overview
- `GET /dino`: DINO stock analysis interface (primary feature)
- `GET /api/kis/tokens/status`: KIS token management status

### Backtesting Routes
- `GET /backtest`: Backtesting list with pagination
- `GET /backtest/create`: Backtesting creation form
- `POST /backtest/create`: Execute new backtest with validation
- `GET /backtest/{id}`: Backtest detail view with results
- `POST /backtest/{id}/cancel`: Cancel running backtest
- `GET /backtest/{id}/progress`: AJAX progress endpoint for real-time updates

### DINO Analysis
- **URL**: `http://localhost:8080/dino`
- **Function**: Displays finance analysis for Samsung Electronics (005930)
- **Features**: 5-metric scoring system, Material UI interface, real KIS API data
- **Expected**: Real-time calculation of revenue growth, operating profit, margins, retention rate, debt ratio

### Backtesting System
- **URL**: `http://localhost:8080/backtest`
- **Function**: Complete backtesting engine with DDD + Hexagonal Architecture
- **Features**: Buy-and-Hold strategy, real-time progress tracking, comprehensive results
- **Expected**: Historical price data simulation, trade execution, performance metrics calculation

## Development Guidelines

### KIS Token Management
- **Use `KisTokenManager`** for token access (not `KisTokenService` directly)
- Tokens are automatically cached and reused from PostgreSQL
- No manual token refresh needed - handled by scheduling and business logic
- Token persistence ensures continuity across application restarts

### DINO System Development
- Finance analysis follows exact Python algorithm translation
- Scoring: `MAX(0, MIN(5, 2 + sum_of_individual_scores))`
- One analysis per stock per day with database caching
- All business logic in service layer, controllers handle web concerns only

### Database Operations
- JPA entities use `ddl-auto: update` for automatic schema evolution
- Domain objects (KisToken, Token, Backtest, Trade) separate from JPA entities
- Repository pattern with domain abstractions
- PostgreSQL provides persistence; H2 for testing

### Backtesting System Development
- Follows DDD + Hexagonal Architecture principles
- Synchronous execution to avoid concurrency issues (simplified from async)
- Domain layer: Pure business logic with aggregate roots and value objects
- Application layer: Use cases and orchestration services
- Infrastructure layer: Adapters for web, persistence, and market data
- All backtests stored with complete audit trail and trade history

## Critical Notes

### Java 21 Compatibility
This project uses Java 21. The build system is configured for Java 21 compatibility with Spring Boot 3.5.6.

### Token Optimization
The system automatically minimizes KIS API calls through intelligent caching and proactive token renewal. Tokens persist in PostgreSQL and are reused until 1 hour before expiration.

## Quick Start Checklist

1. **Prerequisites**: Java 21, Docker Desktop running
2. **Database**: `docker-compose up -d` (starts PostgreSQL)
3. **Secrets**: Verify `application-secrets.yml` exists in resources
4. **Build**: `./gradlew bootRun`
5. **Access**: Navigate to `http://localhost:8080/dino` for DINO analysis or `http://localhost:8080/backtest` for backtesting
6. **Verify**: Check database tables with `docker exec quantum-postgres psql -U quantum -d quantum_trading -c "\dt"`

## Common Development Tasks

### Database Management
```bash
# Check PostgreSQL container status
docker ps --filter "name=quantum-postgres"

# View recent PostgreSQL logs
docker logs quantum-postgres --tail 50

# Reset database (removes all data)
docker-compose down -v && docker-compose up -d
```

### Application Monitoring
```bash
# View application logs (if running)
./gradlew bootRun | grep -E "(ERROR|WARN|INFO.*DINO|INFO.*KIS)"

# Check KIS token status via API
curl -s http://localhost:8080/api/kis/tokens/status | jq .

# Test backtesting endpoints
curl -s http://localhost:8080/backtest | grep -o 'class=".*"' | head -5
```