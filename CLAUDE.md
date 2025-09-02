# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Team Role & Collaboration

**IMPORTANT: You are part of a 4-person development team. Always identify your role when starting:**

1. **기획자 (Planner)** - Requirements definition, user stories, project roadmap, MVP scope
2. **백엔드 (Backend)** - Spring Boot API development, database design, system architecture  
3. **프론트엔드 (Frontend)** - Next.js UI/UX development, user interface implementation
4. **분석가 (Analyst)** - Trading algorithms, data analysis, automated trading logic

**Collaboration Guidelines:**
- Always state your role at the beginning of each session
- Focus on your domain expertise while considering team integration
- Coordinate with other team members on shared interfaces and APIs
- Maintain consistency with team decisions and architectural patterns

## Project Overview

**Mission**: Building an automated stock trading platform (MVP)
**Target**: Support both live trading and paper trading environments  
**Developer**: Single developer managing multiple specialized roles

This is a quantum trading platform consisting of multiple components:

- **quantum-web-api** - Spring Boot Kotlin backend API with DDD architecture
- **quantum-web-client** - Next.js 15 TypeScript frontend with Radix UI components
- **quantum-adapter-kiwoom** - FastAPI Python adapter for Kiwoom trading API
- **quantum-adapter-kis** - FastAPI Python adapter for KIS trading API (comprehensive sample code)
- **quantum-infrastructure** - Infrastructure and deployment configurations

## Development Commands

### Backend API (quantum-web-api)
```bash
cd quantum-web-api

# Build the project
./gradlew build

# Run the application (default port 8080)
./gradlew bootRun

# Run tests
./gradlew test

# Clean build artifacts
./gradlew clean

# Run a single test
./gradlew test --tests "ClassName.methodName"
```

### Frontend Client (quantum-web-client)
```bash
cd quantum-web-client

# Install dependencies
npm install

# Run development server (port 3000)
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter (ESLint)
npm run lint
```

### Python Adapters (kiwoom/kis)
```bash
cd quantum-adapter-kiwoom  # or quantum-adapter-kis

# For KIS adapter (comprehensive example repository)
# Install using uv (recommended)
uv sync

# Or use pip
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn main:app --reload --port 8001  # kiwoom: 8001
python -m uvicorn main:app --reload --port 8002  # kis: 8002

# Run KIS sample examples
cd quantum-adapter-kis/examples_user/domestic_stock
python domestic_stock_examples.py
```

## Architecture

This codebase follows **Domain-Driven Design (DDD)** and **Hexagonal Architecture** patterns with clear separation of concerns.

### Backend Architecture (Spring Boot + Kotlin)

**Technology Stack:**
- Java 21 with Kotlin 1.9.25
- Spring Boot 3.5.5 (Web, JPA, Security, Validation)
- JWT authentication (jsonwebtoken 0.11.5)
- PostgreSQL (production) + H2 (development)
- JUnit 5 for testing

**DDD Structure:**
```
com.quantum/
├── common/                     # Shared kernel
│   ├── BaseEntity.kt          # Base entity with audit fields
│   └── DomainEvent.kt         # Domain event interface
├── config/                     # Spring configuration
│   ├── SecurityConfig.kt      # Security & JWT configuration
│   ├── JwtProperties.kt       # JWT configuration properties
│   └── DataInitializer.kt     # Development data setup
├── user/                       # User bounded context
│   ├── domain/                 # Domain layer
│   │   ├── User.kt            # User aggregate root with business logic
│   │   └── UserDomainService.kt
│   ├── application/            # Application layer
│   │   ├── port/
│   │   │   ├── incoming/      # Use cases (interfaces)
│   │   │   └── outgoing/      # External dependencies (interfaces)
│   │   └── usecase/           # Use case implementations
│   ├── infrastructure/         # Infrastructure layer
│   │   ├── persistence/       # Database adapters
│   │   └── security/          # Security adapters (JWT, password)
│   └── presentation/           # Presentation layer
│       ├── web/               # REST controllers
│       └── dto/               # Data transfer objects
└── kis/                        # KIS integration domain
    └── domain/                 # KIS-specific domain objects
```

**Key Domain Patterns:**
- **Aggregate Root**: User entity with business invariants and domain events
- **Domain Events**: UserLoginEvent for audit/notification
- **Value Objects**: UserStatus, UserRole enums
- **Repository Pattern**: UserRepository interface with JPA implementation
- **Use Cases**: AuthUseCase for application services

### Frontend Architecture (Next.js + TypeScript)

**Technology Stack:**
- Next.js 15.5.2 with App Router
- React 19 with TypeScript 5
- Radix UI components with Tailwind CSS
- Form validation with react-hook-form + zod
- Theme support with next-themes

**Component Architecture:**
```
src/
├── app/                        # Next.js App Router
│   ├── layout.tsx             # Root layout with providers
│   ├── page.tsx               # Trading dashboard homepage
│   ├── login/page.tsx         # Authentication page
│   ├── profile/page.tsx       # User profile management
│   └── settings/page.tsx      # Application settings
├── components/
│   ├── auth/                  # Authentication components
│   │   ├── LoginForm.tsx      # Login form with validation
│   │   ├── LogoutDialog.tsx   # Logout confirmation
│   │   ├── ProtectedRoute.tsx # Route protection wrapper
│   │   └── UserMenu.tsx       # User navigation menu
│   ├── chart/                 # Trading chart components
│   │   ├── TradingChart.tsx   # Main chart component (placeholder)
│   │   ├── ChartContainer.tsx # Chart wrapper
│   │   ├── ChartControls.tsx  # Chart configuration
│   │   └── StockSearch.tsx    # Stock symbol search
│   ├── layout/                # Layout components
│   │   ├── Header.tsx         # Main navigation header
│   │   ├── AdminLayout.tsx    # Admin-specific layout
│   │   ├── UserLayout.tsx     # User-specific layout
│   │   ├── TradingMode*.tsx   # Trading mode indicators/toggles
│   │   └── UserInfo.tsx       # User information display
│   ├── stock/                 # Stock-related components
│   │   ├── StockBasicInfo.tsx # Basic stock information
│   │   └── StockFinancialMetrics.tsx # Financial metrics
│   ├── ui/                    # Reusable UI components (Radix UI)
│   └── theme-*.tsx            # Theme management components
└── contexts/
    ├── AuthContext.tsx        # Authentication state management
    └── TradingModeContext.tsx # Trading mode state (live/paper)
```

**Key Frontend Patterns:**
- **Context API**: AuthContext for global authentication state with JWT token management
- **Component Composition**: Radix UI primitives composed into domain-specific components
- **Form Management**: react-hook-form with zod validation schemas
- **API Integration**: Centralized API client with token refresh and error handling
- **Responsive Design**: Mobile-first design with sidebar overlays for mobile trading

### Trading Adapters

**KIS Adapter (Comprehensive):**
- **Korea Investment & Securities** Open API integration
- **Dual Structure**: examples_llm/ (single functions) + examples_user/ (integrated examples)
- **Full Market Coverage**: Domestic stocks, bonds, futures/options, overseas markets
- **Authentication**: kis_auth.py with token management and environment switching
- **Real-time Data**: WebSocket support for live market data
- **Configuration**: kis_devlp.yaml for API credentials and account settings

**Kiwoom Adapter (Basic):**
- **Kiwoom Securities** trading API integration
- **Simple FastAPI**: Basic REST endpoints (currently Hello World)
- **Future Expansion**: Prepared for Kiwoom OpenAPI integration

## Key Development Patterns

### Authentication Flow
1. **Frontend**: Login form → AuthContext.login() → JWT tokens stored in localStorage
2. **Backend**: JWT verification → User domain validation → Response with user data
3. **Token Refresh**: Automatic refresh on expiration with fallback to login redirect

### Domain Event Handling
```kotlin
// In User aggregate
fun login() {
    lastLoginAt = LocalDateTime.now()
    domainEvents.add(UserLoginEvent(...))  // Domain event for audit
}
```

### API Error Handling
- **Frontend**: ApiError class with status codes and message handling
- **Backend**: GlobalExceptionHandler for consistent error responses
- **Validation**: Both client-side (zod) and server-side (Bean Validation)

### Component Development
- **Design System**: Consistent Radix UI components with shadcn/ui patterns
- **Accessibility**: WCAG compliance built into Radix UI components
- **State Management**: React Context for global state, useState for local state
- **Form Handling**: react-hook-form with zod schemas for type-safe validation

## Development Notes

### Development Environment Configuration

#### Production-style Domain Structure (Local Development)
For realistic local development matching production environment:

**Domain Structure:**
- **Frontend**: http://quantum-trading.com:3000
- **API**: http://api.quantum-trading.com:8080
- **KIS Adapter**: http://localhost:8002 (FastAPI)
- **Kiwoom Adapter**: http://localhost:8001 (FastAPI)

**Required hosts file setup:**
```bash
sudo sh -c 'cat >> /etc/hosts << EOF

# Quantum Trading Platform - Production-style Local Development  
127.0.0.1   quantum-trading.com
127.0.0.1   api.quantum-trading.com
EOF'
```

**Environment Variables (.env.local):**
```bash
# Production Domain Structure for Local Development
NEXT_PUBLIC_API_URL=http://api.quantum-trading.com:8080
NEXT_PUBLIC_CLIENT_URL=http://quantum-trading.com:3000
NODE_ENV=development
```

**Development Workflow:**
1. Set up hosts file entries (one-time setup)
2. Start backend: `./gradlew bootRun` (serves on 0.0.0.0:8080)
3. Start frontend: `npm run dev` (binds to quantum-trading.com:3000)
4. Access application: http://quantum-trading.com:3000

**Benefits:**
- Identical to production domain structure
- Proper CORS and cookie domain testing
- Realistic authentication flow testing
- No localhost/domain conflicts

#### Fallback Localhost Configuration
- **Frontend**: http://localhost:3000 (use `npm run dev:local`)
- **Backend**: http://localhost:8080 (Spring Boot default)

### Database Setup
- **Development**: H2 in-memory database (auto-configured)
- **Production**: PostgreSQL (configured in application.yml)
- **Initialization**: DataInitializer.kt creates default admin user

### Testing Strategies
- **Backend**: JUnit 5 with Spring Boot Test slices (@WebMvcTest, @DataJpaTest)
- **Frontend**: ESLint for code quality (Jest/Testing Library integration pending)
- **API Testing**: HTTP test files for Python adapters

### Security Considerations
- **JWT Configuration**: Configurable secret and expiration in JwtProperties
- **Password Encoding**: BCrypt through PasswordEncodingAdapter
- **CORS**: Configured for development (localhost:3000)
- **API Security**: All endpoints except /api/v1/auth/** require authentication

### Trading Integration
- **KIS API**: Comprehensive sample code available in quantum-adapter-kis
- **Environment Switching**: Support for both paper trading (모의투자) and live trading (실전투자)
- **Market Data**: Real-time WebSocket connections for live market data
- **Account Management**: Multi-account support with different trading products