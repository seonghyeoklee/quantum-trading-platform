# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Quantum Trading App** is a Spring Boot 3.5.6 application built with Java 25, designed as a web-based admin interface for automated stock trading using Korea Investment & Securities (KIS) Open API. The application uses Thymeleaf for server-side rendering with a Material UI-inspired design system.

## Technology Stack

- **Backend**: Spring Boot 3.5.6 + Java 25
- **Frontend**: Thymeleaf templates + Bootstrap 5.3 + Material UI design principles
- **Database**: H2 (in-memory for development)
- **Build Tool**: Gradle with Kotlin DSL
- **Static Resources**: CSS with Material Design patterns, vanilla JavaScript

## Development Commands

### Building and Running

```bash
# 🚀 Quick Start (테스트 모드 - API 키 불필요)
./gradlew bootRun --args='--spring.profiles.active=test'

# 🔑 실제 KIS API 사용 (로컬 개발)
./gradlew bootRun --args='--spring.profiles.active=local'

# 📦 Build the application
./gradlew build

# 🧪 Run tests
./gradlew test

# 🧹 Clean build
./gradlew clean build
```

### KIS API 설정 (필수)

실제 KIS API를 사용하려면 다음 중 하나의 방법으로 시크릿을 설정하세요:

**방법 1: 환경변수 파일 (.env)**
```bash
# .env 파일이 이미 실제 키로 설정되어 있음
./gradlew bootRun
```

**방법 2: Spring Profile 사용**
```bash
# application-local.yml이 실제 키로 설정되어 있음
./gradlew bootRun --args='--spring.profiles.active=local'
```

**방법 3: 테스트 모드 (API 키 없이 DINO 테스트만)**
```bash
./gradlew bootRun --args='--spring.profiles.active=test'
# http://localhost:8080/dino 접속하여 삼성전자(005930) 테스트
```

### Java 25 Compatibility Note

This project specifically requires Java 25. There are known compatibility issues with Gradle's Kotlin DSL and Java 25 that may cause build failures with error messages like `IllegalArgumentException: 25`. The project is configured to work with Java 25 despite these issues - persist with the build commands as they typically succeed on subsequent attempts.

## Architecture Overview

### Package Structure

- **`com.quantum`**: Root package containing the main application class
- **`com.quantum.controller`**: Web controllers (Dashboard, KIS Token endpoints)
- **`com.quantum.kis`**: KIS API integration module
  - **`config`**: Configuration classes for KIS API credentials and settings
  - **`service`**: Business logic for KIS API operations (token management)
  - **`dto`**: Data Transfer Objects for API requests/responses
  - **`domain`**: Core domain objects (KisEnvironment, TokenType enums)
  - **`exception`**: Custom exceptions for KIS API errors

### Key Components

#### KIS API Integration
The application integrates with Korea Investment & Securities Open API through a modular design:

- **`KisConfigProperties`**: Configuration binding from `application.yml` with validation
- **`KisTokenService`**: Generic token issuance service supporting access tokens and WebSocket keys
- **`TokenType` enum**: Type-safe token operations with different endpoints and request types
- **`KisEnvironment` enum**: Environment management (PROD/VPS) with different base URLs

#### Web Layer
- **`DashboardController`**: Main controller handling dashboard and navigation routes
- **`KisTokenController`**: REST endpoints for KIS token operations
- **Thymeleaf Templates**: Fragment-based layout system with `layout.html` as master template

#### Frontend Architecture
- **Material UI Design System**: Clean, professional interface using CSS Custom Properties
- **Theme Support**: Light/dark mode toggle with localStorage persistence
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **Component Structure**: Card-based dashboard layout with stat cards, charts, and tables

## Configuration

### Application Configuration (`application.yml`)

```yaml
spring:
  application:
    name: quantum-trading-app

kis:
  api:
    my-app: ${KIS_MY_APP:your-prod-app-key}
    my-sec: ${KIS_MY_SEC:your-prod-secret-key}
    paper-app: ${KIS_PAPER_APP:your-vps-app-key}
    paper-sec: ${KIS_PAPER_SEC:your-vps-secret-key}
    my-agent: ${KIS_USER_AGENT:QuantumTradingApp/1.0}
```

### Environment Variables for KIS API

Set these environment variables for KIS API integration:
- `KIS_MY_APP`: Production app key
- `KIS_MY_SEC`: Production secret key
- `KIS_PAPER_APP`: VPS/Paper trading app key
- `KIS_PAPER_SEC`: VPS/Paper trading secret key
- `KIS_USER_AGENT`: Custom user agent string

## Design System

### CSS Architecture
- **CSS Custom Properties**: Theme-aware color system with light/dark mode support
- **Material Design**: Clean, flat design with appropriate shadows and typography
- **Component Classes**:
  - `.stat-card`: Dashboard metric cards with hover effects
  - `.sidebar`: Fixed navigation with Material design principles
  - `.main-content`: Responsive content area with proper spacing

### Color Palette
- **Primary**: `#1976d2` (Material Blue)
- **Success**: `#388e3c` (Material Green)
- **Warning**: `#f57c00` (Material Orange)
- **Error**: `#d32f2f` (Material Red)
- **Info**: `#0288d1` (Material Light Blue)

## API Endpoints

### Web Routes
- `GET /`: Dashboard page
- `GET /stocks`: Stock management page (placeholder)
- `GET /news`: News monitoring page (placeholder)
- `GET /backtest`: Backtesting page (placeholder)
- `GET /orders`: Order management page (placeholder)
- `GET /system`: System status page (placeholder)
- `GET /logs`: Log viewer page (placeholder)
- `GET /settings`: Settings page (placeholder)

### KIS API Routes
- `POST /api/kis/token/{env}`: Get access token for specified environment
- `POST /api/kis/websocket-key/{env}`: Get WebSocket key for specified environment

## Development Guidelines

### KIS API Integration
- All KIS API calls go through `KisTokenService` with proper error handling
- Use `KisEnvironment` enum for environment management (PROD/VPS)
- Token requests are type-safe through `TokenType` enum
- Debug logging includes curl commands for API troubleshooting

### Frontend Development
- Follow Material UI design principles for new components
- Use CSS Custom Properties for theming
- Maintain responsive design patterns
- Keep JavaScript minimal and vanilla (no frameworks)

### Error Handling
- KIS API errors are wrapped in `KisApiException`
- Configuration validation happens at startup through `KisConfigProperties`
- All controllers use proper error responses and logging

## Testing

### Running Tests
```bash
# Run all tests
./gradlew test

# Run specific test class
./gradlew test --tests "KisTokenServiceTest"

# Run tests with debug output
./gradlew test --debug
```

The project uses JUnit 5 for testing with Spring Boot test support.