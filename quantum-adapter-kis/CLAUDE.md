# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**KIS Adapter** is a FastAPI-based microservice that serves as a bridge between the Quantum Trading Platform and the Korea Investment & Securities (KIS) Open API. It provides a unified REST interface for accessing domestic and overseas stock market data, real-time pricing, and chart information.

## Architecture Overview

### Core Components
- **FastAPI Server**: Main application running on port 8000 (main.py)
- **KIS Authentication**: Token management and API authentication (kis_auth.py)
- **API Integration**: Pre-built functions for all KIS OpenAPI endpoints
- **WebSocket Support**: Real-time data streaming capabilities
- **Dual Structure**: LLM-friendly individual functions + user-friendly integrated examples

### Key Features
- **Multi-Environment Support**: Production (prod) and sandbox (vps) trading environments
- **Market Coverage**: Domestic (KRX) and overseas markets (NAS, NYS, HKS, TSE, SHS, SZS)
- **Auto Data Splitting**: Handles large date ranges by splitting into 90-day chunks
- **Real-time Data**: WebSocket endpoint for live market data streaming
- **CORS Support**: Configured for cross-origin requests from web clients

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (recommended)
uv sync

# Alternative with pip
pip install -r requirements.txt

# Verify installation
python --version  # Should be >= 3.13
```

### Running the Server
```bash
# Start FastAPI server (default port 8000)
uv run python main.py

# Alternative direct execution
python main.py

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

## Project Structure

### Dual Architecture System
The project follows a unique dual structure designed for both AI and human developers:

**`examples_llm/`** - Individual API Functions
- Each KIS API function has its own folder
- Pattern: `function_name/function_name.py` + `chk_function_name.py`
- Optimized for LLM exploration and single-function testing
- Clear separation of concerns for AI code analysis

**`examples_user/`** - Integrated Examples
- Functions grouped by market category (domestic_stock, overseas_stock, etc.)
- Pattern: `category_functions.py` + `category_examples.py`
- WebSocket variants: `category_functions_ws.py` + `category_examples_ws.py`
- Designed for practical trading application development

### Core Categories
```
domestic_stock/          # 국내주식 (Korean stocks)
domestic_bond/           # 국내채권 (Korean bonds)  
domestic_futureoption/   # 국내선물옵션 (Korean derivatives)
overseas_stock/          # 해외주식 (International stocks)
overseas_futureoption/   # 해외선물옵션 (International derivatives)
elw/                     # ELW (Equity-Linked Warrants)
etfetn/                  # ETF/ETN (Exchange-Traded Funds/Notes)
```

## KIS API Configuration

### Authentication Setup
1. **API Keys**: Configure in `kis_devlp.yaml`
   - Production keys: `my_app`, `my_sec`
   - Sandbox keys: `paper_app`, `paper_sec`
   - Account numbers: `my_acct_stock`, `my_paper_stock`

2. **Environment Selection**: 
   ```python
   # Production environment
   ka.auth(svr="prod", product="01")
   
   # Sandbox environment  
   ka.auth(svr="vps", product="01")
   ```

### Token Management
- **Auto Token Refresh**: Handled automatically by kis_auth.py
- **Token Storage**: Local file system with secure naming
- **Rate Limits**: 
  - Production: 20 calls/second
  - Sandbox: 2 calls/second

## FastAPI REST API Endpoints

### Core Domestic Endpoints
```
GET /domestic/price/{symbol}              # Current price
GET /domestic/chart/{symbol}              # Chart data (D/W/M/Y periods) 
GET /domestic/index/{index_code}          # Index prices
GET /domestic/ranking/top-interest-stock  # Popular stocks
```

### Core Overseas Endpoints
```
GET /overseas/{exchange}/price/{symbol}        # Current price
GET /overseas/{exchange}/chart/{symbol}        # Chart data
GET /overseas/{exchange}/index/{index_code}    # Index prices
GET /overseas/{exchange}/index/{index_code}/chart # Index chart data
```

### Utility Endpoints
```
POST /auth/refresh-token?environment=prod|vps  # Token management
GET /health                                     # Health check
WebSocket /ws/realtime                          # Real-time data stream
```

### Exchange Codes
- **NAS**: NASDAQ
- **NYS**: New York Stock Exchange  
- **HKS**: Hong Kong Stock Exchange
- **TSE**: Tokyo Stock Exchange
- **SHS**: Shanghai Stock Exchange
- **SZS**: Shenzhen Stock Exchange

## WebSocket Integration

### Real-time Data Streaming
```python
# WebSocket endpoint
ws://localhost:8000/ws/realtime

# Message format
{
    "type": "ping",
    "data": {"message": "heartbeat"}
}

# Response format
{
    "type": "pong", 
    "timestamp": "2024-01-01T12:00:00"
}
```

### Connection Management
- **Connection Manager**: Handles multiple WebSocket connections
- **Heartbeat Support**: Ping/pong mechanism for connection health
- **Broadcast Capability**: Real-time data distribution to all clients
- **Auto-disconnect**: Graceful handling of connection failures

## Data Processing Features

### Auto Data Splitting
For large date ranges, the system automatically:
1. Splits requests into 90-day chunks
2. Makes sequential API calls to stay within rate limits
3. Combines results into unified response
4. Maintains data integrity and order

### Chart Data Periods
- **D**: Daily (일봉)
- **W**: Weekly (주봉)  
- **M**: Monthly (월봉)
- **Y**: Yearly (년봉)

## Error Handling & Logging

### Comprehensive Logging
- **Request/Response Logging**: All API calls logged with timestamps
- **Error Tracking**: Detailed error messages with context
- **Performance Monitoring**: Response time tracking
- **Log Levels**: INFO, WARNING, ERROR with appropriate filtering

### Error Response Format
```json
{
    "error": "error_type",
    "message": "Human readable error message",
    "detail": "Technical error details",
    "timestamp": "2024-01-01T12:00:00"
}
```

## Security Considerations

### Authentication Security
- **API Keys**: Stored in separate YAML file (never in code)
- **Token Encryption**: AES encryption for stored tokens
- **Secure Token Storage**: Random file naming with secure directory placement
- **Environment Separation**: Clear prod/sandbox isolation

### CORS Configuration
```python
origins = [
    "http://localhost:3000",           # Frontend development
    "http://localhost:8080",           # Backend API  
    "https://quantum-trading.com",     # Production domain
    "https://*.quantum-trading.com"    # Subdomain support
]
```

## Integration with Quantum Trading Platform

### API Bridge Pattern
The KIS Adapter serves as a microservice bridge:
```
Frontend (Next.js) → Backend (Spring Boot) → KIS Adapter (FastAPI) → KIS OpenAPI
```

### Data Flow
1. **Request Flow**: Frontend → Backend → KIS Adapter → KIS API
2. **Response Flow**: KIS API → KIS Adapter (process/format) → Backend → Frontend
3. **Real-time Flow**: KIS API → WebSocket → All connected clients

### Chart Integration
- **Chart Library**: Supports lightweight-charts integration
- **Data Format**: OHLCV format with Korean market conventions
- **Color Scheme**: Red (상승), Blue (하락) following Korean market standards
- **Time Zone**: KST (Korea Standard Time) for domestic markets

## Performance Considerations

### Rate Limiting
- **Production API**: 20 requests/second maximum
- **Sandbox API**: 2 requests/second maximum
- **Auto-throttling**: Built-in request throttling to prevent API quota exhaustion
- **Queue Management**: Request queuing for high-volume scenarios

### Data Caching
- **Token Caching**: Authentication tokens cached until expiration
- **Response Optimization**: Efficient data structure for chart data
- **Memory Management**: Proper cleanup of large datasets

## Development Best Practices

### Code Organization
- **Function Isolation**: Each API function in separate file for LLM analysis
- **Category Grouping**: Related functions grouped for user convenience
- **Consistent Naming**: Clear, descriptive function and variable names
- **Documentation**: Comprehensive docstrings in both Korean and English

### Testing Strategy
- **Individual Testing**: Each function has dedicated test file (`chk_*.py`)
- **Integration Testing**: Category-level examples for end-to-end testing
- **Manual Testing**: HTTP test files for manual API verification
- **Environment Testing**: Separate test flows for prod and sandbox

### Configuration Management
- **Environment Variables**: Use `kis_devlp.yaml` for all configuration
- **Secret Management**: Never commit API keys or tokens to version control
- **Path Configuration**: Configurable paths for token storage and logs
- **Logging Configuration**: Adjustable log levels and formats

## Troubleshooting Guide

### Common Issues
1. **Token Expiration**: Tokens expire every 6 hours, auto-refresh implemented
2. **Rate Limiting**: Monitor API call frequency, implement backoff strategies
3. **Data Splits**: Large date ranges automatically split, verify data completeness
4. **WebSocket Disconnects**: Implement reconnection logic in clients
5. **Market Hours**: KIS API availability varies by market trading hours

### Debugging Commands
```bash
# Check server status
curl http://localhost:8000/health

# Test token refresh
curl -X POST "http://localhost:8000/auth/refresh-token?environment=prod"

# Verify domestic stock price
curl "http://localhost:8000/domestic/price/005930"  # Samsung Electronics

# Check logs
tail -f logs/kis_adapter.log
```

## Dependencies & Requirements

### Core Dependencies
- **Python 3.13+**: Required runtime version
- **FastAPI**: Web framework for REST API
- **uvicorn**: ASGI server for FastAPI
- **pandas**: Data manipulation and analysis
- **websockets**: Real-time communication
- **pycryptodome**: Encryption for token security
- **PyYAML**: Configuration file parsing
- **requests**: HTTP client for KIS API calls

### Optional Dependencies
- **backtrader**: Backtesting framework
- **pandas-ta**: Technical analysis indicators
- **matplotlib**: Chart plotting capabilities
- **yfinance**: Alternative data source
- **pykrx**: Korean market data utilities

### Package Management
- **Primary**: Use `uv` for fastest dependency management
- **Alternative**: Use `pip` with requirements.txt
- **Lock File**: uv.lock ensures reproducible builds