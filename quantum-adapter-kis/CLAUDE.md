# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KIS Adapter** is a FastAPI-based microservice that bridges the Quantum Trading Platform with Korea Investment & Securities (KIS) Open API. It provides unified REST interfaces for domestic/overseas stock data, real-time pricing, advanced trading strategies, and comprehensive market analysis.

## Architecture Overview

### Core Components
- **FastAPI Server**: Main application running on port 8000 (main.py)
- **KIS Authentication**: Token management and API authentication (examples_llm/kis_auth.py)
- **Dual API Structure**: LLM-optimized individual functions + integrated user examples
- **Trading Strategy Engine**: Multi-source data analysis with AI-powered insights
- **Sector Trading System**: Automated portfolio management across 6 key sectors
- **WebSocket Support**: Real-time market data streaming

### Key Features
- **Multi-Environment Support**: Production (prod) and sandbox (vps) trading environments
- **Market Coverage**: Domestic (KRX) and overseas markets (NAS, NYS, HKS, TSE, SHS, SZS)
- **Auto Data Splitting**: Handles large date ranges by splitting into 90-day chunks
- **AI-Enhanced Analysis**: Comprehensive batch analysis system with PostgreSQL storage
- **Real-time Data**: WebSocket endpoint for live market data streaming
- **DINO Test System**: Automated stock scoring system with 15-point scale analysis
- **Database Token Management**: PostgreSQL-based KIS token storage and management

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended - Python 3.13+ required)
uv sync

# Alternative with pip
pip install -r requirements.txt

# Verify Python version
python --version  # Should be >= 3.13
```

### Running the Server
```bash
# Start FastAPI server (default port 8000)
uv run python main.py

# Development with auto-reload
uvicorn main:app --reload --port 8000
```

### Testing Individual APIs
```bash
# Test specific KIS API functions (examples_llm pattern)
cd examples_llm/domestic_stock/inquire_price
python chk_inquire_price.py

# Test integrated functionality (examples_user pattern)  
cd examples_user/domestic_stock
python domestic_stock_examples.py
```

### Sector Trading System
```bash
# Interactive trading console with approval workflow
cd sector_trading_test
uv run python manual_trader.py

# Comprehensive system verification
uv run python test_full_system.py

# Basic system test
uv run python test_system.py
```

### Trading Strategy Analysis
```bash
# Run comprehensive batch analysis
uv run python -c "from trading_strategy.comprehensive_batch_analyzer import ComprehensiveBatchAnalyzer; c = ComprehensiveBatchAnalyzer(); c.run_comprehensive_analysis_sync()"

# Test single stock analysis
cd trading_strategy
uv run python test_single_stock.py

# Test AI-powered analysis features
uv run python test_ai_features.py
```

### DINO Test System
```bash
# Test financial analysis (5-point scale)
uv run python test_dino_finance.py

# Test technical analysis (5-point scale)  
uv run python test_dino_technical.py

# Test price analysis (5-point scale)
uv run python test_dino_price.py

# Test specific stock with detailed output
uv run python test_dino_finance.py 005930
uv run python test_dino_price.py 000660
```

## Project Structure

### Dual Architecture System
The project follows a unique dual structure optimized for both AI and human developers:

**`examples_llm/`** - Individual API Functions (AI-Optimized)
- Each KIS API function has its own folder
- Pattern: `function_name/function_name.py` + `chk_function_name.py`
- Clear separation of concerns for AI code analysis
- Individual testing capability

**`examples_user/`** - Integrated Examples (Human-Friendly)
- Functions grouped by market category (domestic_stock, overseas_stock, etc.)
- Pattern: `category_functions.py` + `category_examples.py`
- WebSocket variants: `category_functions_ws.py` + `category_examples_ws.py`

### Trading Strategy Engine
```
trading_strategy/
├── comprehensive_batch_analyzer.py    # Main analysis engine
├── core/
│   ├── kis_data_provider.py          # KIS API data integration
│   ├── signal_detector.py            # Trading signal detection
│   ├── technical_analysis.py         # Technical indicators
│   └── backtester.py                 # Strategy backtesting
├── strategies/                       # Trading strategy implementations
├── backtesting/                      # Backtesting framework
└── tests/                           # Strategy testing suite
```

### Sector Trading System
```
sector_trading_test/
├── core/
│   ├── sector_portfolio.py           # 6-sector portfolio management
│   ├── enhanced_analyzer.py          # PyKRX/yfinance analysis (no KIS API limits)
│   ├── smart_order_manager.py        # Intelligent order pricing
│   ├── simple_data_provider.py       # Multi-source data provider
│   └── manual_executor.py            # Manual approval workflow
├── config/
│   ├── sectors_2025.yaml            # 2025 sector definitions
│   ├── strategy_config.yaml         # Trading strategy settings
│   └── risk_management.yaml         # Risk parameters
└── manual_trader.py                 # Interactive trading console
```

### DINO Test System
```
dino_test/
├── finance_scorer.py                # Financial analysis scoring (5 points)
├── finance_data_collector.py        # KIS financial data collection
├── technical_analyzer.py            # Technical analysis scoring (5 points) 
├── technical_data_collector.py      # Chart data collection with indicators
├── price_analyzer.py                # Price analysis scoring (5 points)
├── price_data_collector.py          # 52-week high/low analysis
├── __init__.py                      # Package initialization
└── [future] material_analyzer.py    # Material analysis scoring (5 points - pending)
```

### Database Token Management
```
db_token_manager.py                   # PostgreSQL direct connection for KIS tokens
├── DBTokenManager class              # Token management with database
├── get_kis_token_from_db()          # Retrieve valid tokens by user
├── get_token_status_from_db()       # Check token validity and expiration
└── is_db_available()                # Database connection health check
```

## KIS API Configuration

### Authentication Setup
1. **API Keys**: Configure in `kis_devlp.yaml` at project root
   ```yaml
   my_app: "실전투자_앱키"
   my_sec: "실전투자_앱시크릿"
   paper_app: "모의투자_앱키"
   paper_sec: "모의투자_앱시크릿"
   ```

2. **Environment Selection**: 
   ```python
   # Production environment
   ka.auth(svr="prod", product="01")
   
   # Sandbox environment  
   ka.auth(svr="vps", product="01")
   ```

3. **Token Storage**: 
   - **Database**: PostgreSQL-based token management via `db_token_manager.py` (preferred)
   - **File-based**: Configured in `examples_llm/kis_auth.py` line 35-41 (fallback)
   ```python
   config_root = os.path.join(os.path.expanduser("~"), "KIS", "config")
   ```

### Rate Limits & Performance
- **Production**: 20 calls/second per account
- **Sandbox**: 2 calls/second per account  
- **Alternative Data Sources**: PyKRX (no rate limits), yfinance (fallback)
- **WebSocket Limits**: Max 41 concurrent registrations

## FastAPI REST API Endpoints

### Core Domestic Endpoints
```
GET /domestic/price/{symbol}              # Current price
GET /domestic/chart/{symbol}              # Chart data (D/W/M/Y periods) 
GET /domestic/index/{index_code}          # Index prices
GET /domestic/ranking/top-interest-stock  # Popular stocks
GET /domestic/holiday                     # Market holidays
```

### Core Overseas Endpoints
```
GET /overseas/{exchange}/price/{symbol}        # Current price
GET /overseas/{exchange}/chart/{symbol}        # Chart data
GET /overseas/{exchange}/index/{index_code}    # Index prices
```

### DINO Test Endpoints
```
GET /dino-test/finance/{stock_code}            # Financial analysis (5-point scale)
GET /dino-test/technical/{stock_code}          # Technical analysis (5-point scale)
GET /dino-test/price/{stock_code}              # Price analysis (5-point scale)
GET /dino-test/finance-batch                   # Batch financial analysis
```

### Utility Endpoints
```
POST /auth/refresh-token?environment=prod|vps # Token management
GET /health                                    # Health check
WebSocket /ws/realtime                         # Real-time data stream
```

## Data Processing Features

### Auto Data Splitting
For large date ranges, the system automatically:
1. Splits requests into 90-day chunks
2. Makes sequential API calls to stay within rate limits
3. Combines results into unified response
4. Maintains data integrity and chronological order

### Multi-Source Data Integration
- **Primary**: KIS Open API (real-time, authenticated)
- **Secondary**: PyKRX (Korean market data, no rate limits)
- **Tertiary**: yfinance (global market data fallback)
- **AI Enhancement**: PostgreSQL storage with comprehensive analysis

## Trading Strategy System Details

### Sector Portfolio Management
- **6 Key Sectors**: 조선, 방산, 원자력, AI, 반도체, 바이오
- **Risk Management**: Max 30% per sector, 10% per stock
- **Total Portfolio**: 1,000만원 target allocation
- **Rebalancing**: Auto-signals when allocation deviates >5%

### Smart Order Management
- **AGGRESSIVE**: Market orders for strong signals (RSI < 30 or > 70)
- **BALANCED**: 0.5% discount/premium for normal conditions  
- **PATIENT**: 1.0% discount/premium for high volatility

### Data Provider Priority
1. **PyKRX** (primary) - No rate limits, real Korean market data
2. **yfinance** (secondary) - Global market data fallback
3. **FinanceDataReader** (tertiary) - Alternative Korean data source
4. **KIS API** (authenticated) - Real-time data when others unavailable

## Security Considerations

### Authentication Security
- **API Keys**: Stored in separate YAML file (never in code)
- **Token Storage**: Encrypted local storage with secure directory placement
- **Environment Separation**: Clear prod/sandbox isolation
- **Rate Limiting**: Built-in throttling to prevent API quota exhaustion

### Configuration Management
- **Secrets**: Never commit `kis_devlp.yaml` or token files
- **Paths**: Configurable token storage location
- **Logging**: Structured logging without sensitive data exposure

## Integration Notes

### FastAPI Auto-Reload
The server uses uvicorn's auto-reload feature. Changes to `main.py` or imported modules will automatically restart the server.

### Error Handling
- Comprehensive logging with structured formats
- Graceful degradation when data sources are unavailable
- Automatic fallback between data providers
- Rate limit handling with exponential backoff

### WebSocket Real-time Data
- Connection management with heartbeat support
- Broadcast capability for multiple clients
- Automatic reconnection handling
- Both KIS API polling and demo data generation support

## Development Best Practices

### Code Organization
- **Function Isolation**: Each API function in separate file for AI analysis
- **Category Grouping**: Related functions grouped for user convenience
- **Consistent Naming**: Clear, descriptive function and variable names
- **Dual Documentation**: Korean and English comments where appropriate

### Testing Strategy
- **Individual Testing**: Each function has dedicated test file (`chk_*.py`)
- **Integration Testing**: Category-level examples for end-to-end testing
- **System Testing**: Full sector trading system verification
- **Performance Testing**: Strategy backtesting and analysis validation

### Configuration Files
- **YAML Configuration**: `kis_devlp.yaml` for all API credentials
- **Sector Configuration**: `sector_trading_test/config/sectors_2025.yaml`
- **Strategy Configuration**: Multiple YAML files for different strategies
- **Risk Management**: Separate configuration for risk parameters

## DINO Test System Details

### Scoring Architecture
The DINO Test system implements a comprehensive 15-point stock analysis framework:

- **Financial Area (5 points)**: Revenue growth, operating profit, margins, retained earnings, debt ratio
- **Technical Area (5 points)**: OBV analysis, RSI indicators, investor sentiment, MACD signals  
- **Price Area (5 points)**: 52-week high/low positioning with risk assessment
- **Material Area (5 points)**: [Future] Dividend rate, earnings surprise, institutional investment, themes

### Implementation Architecture
- **Excel Formula Integration**: Implements `MAX(0,MIN(5,2+SUM(individual_scores)))` calculation
- **Real Data Processing**: Uses actual KIS API data, no mock or sample data
- **Multi-batch Collection**: Overcomes KIS API 100-record limits with sequential calls
- **Korean User Interface**: Raw data presented with Korean keys and formatted values

### Key Technical Features
- **Financial Data Sources**: 5 KIS APIs (income_statement, balance_sheet, financial_ratio, etc.)
- **Technical Indicators**: pandas_ta integration for OBV, RSI, Stochastic, MACD calculations
- **Price Analysis**: 52-week high/low analysis with momentum and risk scoring
- **Database Integration**: PostgreSQL storage with multi-user JWT support