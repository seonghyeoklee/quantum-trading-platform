# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Quantum Trading Platform** is a simplified stock trading system focused on Korea Investment & Securities (KIS) Open API integration. The project has been completely reset to a minimal architecture for single-developer productivity.

### Current Status (2025-01-23)

**🔄 PROJECT RESET**: The platform has been completely refactored from a complex microservices architecture to a minimal, single-developer-friendly structure.

**Architecture Change**:
- **BEFORE**: Complex microservices (Next.js + Spring Boot + FastAPI + Docker + Airflow + PostgreSQL)
- **AFTER**: Minimal structure with KIS API reference code only

## Current Project Structure

```
quantum-trading-platform/
├── .claude/                    # Claude Code configuration
├── .git/                       # Git version control
├── .idea/                      # IntelliJ IDEA settings
├── .gitignore                  # Git ignore rules
├── CLAUDE.md                   # This documentation file
└── quantum-adapter-kis/        # KIS API reference code (Python FastAPI)
```

## Removed Components

The following components were removed in the project reset:

### ❌ Removed Modules
- **quantum-web-client/**: Next.js 15 + React 19 frontend (152 files removed)
- **quantum-web-api/**: Spring Boot 3.3.4 + Kotlin backend (100+ files removed)
- **quantum-adapter-external/**: External APIs adapter (FastAPI + Naver/DART)
- **quantum-infrastructure/**: Docker + Airflow + monitoring infrastructure
- **database/**: PostgreSQL schemas and ETL scripts
- **airflow/**: Analysis pipeline DAGs
- **docs/**: Project documentation

### 📊 Reset Statistics
- **335 files deleted** (67,899 lines of code removed)
- **Complexity reduced by 90%+**
- **From microservices to minimal structure**

## Remaining Reference Code

### quantum-adapter-kis/ (Reference Only)

The KIS adapter contains valuable reference implementations:

```bash
# Check what's available
cd quantum-adapter-kis/
ls -la

# Key reference components:
# - KIS API integration patterns
# - Authentication handling
# - Real-time data WebSocket
# - Trading strategy examples
# - DINO analysis system
# - Sector trading system
```

## Development Approach

### 🎯 New Philosophy
- **Simplicity First**: Start minimal, add only what's needed
- **Single Developer**: Optimize for 1-person development team
- **Incremental Growth**: Add features one at a time
- **Java-Focused**: Prefer Java/Spring ecosystem for main development

### 🚀 Next Steps (To Be Defined)

The platform is now ready for incremental feature development:

1. **New Technology Stack** (TBD):
   - Spring Boot (Java 25 preferred)
   - Thymeleaf + Bootstrap (instead of React)
   - H2 Database (instead of PostgreSQL)
   - Single JAR deployment (no Docker)

2. **Core Features** (TBD):
   - Basic stock price lookup
   - Simple portfolio tracking
   - Essential KIS API integration

3. **Development Workflow**:
   - Start with minimal viable features
   - Reference quantum-adapter-kis/ for KIS API patterns
   - Add complexity only when absolutely necessary

## KIS API Reference

### Configuration Requirements

For KIS API integration, create `kis_devlp.yaml` in quantum-adapter-kis/:

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

### Reference Commands

```bash
# Run reference KIS adapter (for API testing)
cd quantum-adapter-kis/
uv sync                    # Install dependencies
uv run python main.py      # Start FastAPI server on port 8000

# Test KIS API endpoints
curl "http://localhost:8000/health"                      # Health check
curl "http://localhost:8000/domestic/price/005930"       # Samsung stock price
```

## Branch Structure

- **main**: Stable release branch
- **feature/project-refactoring**: Current refactoring branch (active)

## Critical Development Rules

### 🚨 Data Integrity Rule
**NEVER generate mock/dummy/fake data when APIs fail or return errors.**

When KIS API calls fail or data is unavailable:
- ✅ **CORRECT**: Return appropriate HTTP error codes (404, 503, etc.)
- ❌ **FORBIDDEN**: Generate placeholder or dummy data

### 🛡️ Security Guidelines
- **API Keys**: Never commit credentials to git
- **KIS Tokens**: Store securely, implement proper refresh logic
- **Environment Variables**: Use for sensitive configuration

## Development Status

### ✅ Completed
- Project architecture reset and simplification
- Complex microservices removed
- KIS API reference code preserved
- Git history maintained in feature branch

### 🔄 In Progress
- Defining new minimal architecture
- Planning incremental feature development

### 📋 Planned
- New Spring Boot application structure
- Basic KIS API integration
- Simple web interface
- Essential trading features

## Notes for Future Development

1. **Start Simple**: Begin with a single Spring Boot application
2. **Reference First**: Use quantum-adapter-kis/ for KIS API patterns
3. **Incremental Addition**: Add features only when needed
4. **Java Ecosystem**: Prefer Java tools and libraries for consistency
5. **Single Developer**: Optimize all decisions for solo development efficiency

---

*Last Updated: 2025-01-23*
*Status: Project Reset Complete - Ready for New Development*