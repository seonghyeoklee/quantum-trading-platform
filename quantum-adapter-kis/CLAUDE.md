# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Korea Investment & Securities (KIS) Open API sample code repository designed for both LLM-based automated environments and Python developers. It provides comprehensive examples for connecting to and using the KIS Open API for stock trading, market data, and financial analysis.

**Target APIs**: Korean domestic stocks, bonds, futures/options, overseas stocks, ETF/ETN, ELW
**Key Features**: REST API calls, WebSocket real-time data, authentication management

## Development Environment Setup

### Package Management
This project uses **uv** as the recommended package manager for fast dependency management.

```bash
# Install dependencies
uv sync

# For development with existing pip/venv
pip install -r requirements.txt
```

### Required Configuration
1. **kis_devlp.yaml**: Contains API credentials and account information
   - Located at project root
   - Must be configured with your KIS API keys before use
   - Includes real/demo trading environments

2. **Authentication Path**: 
   - Modify `config_root` in `kis_auth.py` (line ~39)
   - Default: `~/KIS/config/` (recommended to use secure, non-obvious paths)

### Python Requirements
- Python 3.9+ (project specifies >=3.13 in pyproject.toml)
- Key dependencies: pandas, requests, websockets, PyYAML, pycryptodome, PyQt6/PySide6

## Project Architecture

### Dual Structure Design

**examples_llm/**: LLM-optimized single-function examples
- Each API function isolated in its own folder
- Pattern: `[function_name]/[function_name].py` + `chk_[function_name].py`
- Ideal for focused API exploration and testing

**examples_user/**: User-oriented integrated examples  
- Category-based organization with comprehensive function collections
- Pattern: `[category]_functions.py` + `[category]_examples.py` + `*_ws.py` variants
- Suitable for real trading applications

### Core Categories
- `domestic_stock/`: Korean domestic stock APIs
- `domestic_bond/`: Korean bond market APIs  
- `domestic_futureoption/`: Korean derivatives
- `overseas_stock/`: International stock markets
- `overseas_futureoption/`: International derivatives
- `elw/`: ELW (Equity Linked Warrants)
- `etfetn/`: ETF/ETN products

### Authentication System
- **kis_auth.py**: Central authentication module (exists in both examples_llm/ and examples_user/)
- Handles access token management and API request routing
- Supports both production (실전) and demo (모의) environments
- WebSocket connection management for real-time data

## Running Examples

### LLM Examples (Single Function Testing)
```bash
# Navigate to specific function folder
cd examples_llm/domestic_stock/inquire_price/

# Run test with authentication
python chk_inquire_price.py
```

### User Examples (Integrated Functions)
```bash
# Navigate to category folder  
cd examples_user/domestic_stock/

# Run REST API examples
python domestic_stock_examples.py

# Run WebSocket examples  
python domestic_stock_examples_ws.py
```

**Note**: Most example files contain multiple function calls. Comment out unused functions and modify input parameters before execution.

## Code Patterns & Conventions

### Authentication Pattern
```python
import kis_auth as ka

# Initialize authentication (modify svr and product as needed)
ka.auth(svr="prod", product="01")  # prod=real trading, vps=demo
trenv = ka.getTREnv()

# For WebSocket
ka.auth_ws()
kws = ka.KISWebSocket(api_url="/tryitout")
```

### API Function Structure
- **Parameter validation**: Required parameters validated at function start
- **Environment routing**: Different TR_ID values for real/demo environments  
- **Response handling**: Consistent error checking with `res.isOK()`
- **DataFrame output**: Most functions return pandas DataFrames

### File Naming Convention
- REST API functions: Based on API endpoint paths
- WebSocket functions: Descriptive names with `_ws` suffix
- Test files: Prefixed with `chk_`
- Snake_case throughout following Python conventions

## Key Files & Utilities

### Authentication & Config
- `kis_auth.py`: Core authentication and API calling utilities
- `kis_devlp.yaml`: Configuration file (requires user setup)

### Stock Information
- `stocks_info/`: Master code files for various markets and instruments
- Contains market code mappings, sector codes, member codes
- Both Korean (`.h`) and Python (`.py`) formats available

### Legacy Code
- `legacy/`: Previous version samples for reference
- Contains older REST and Postman examples

## Testing & Development

### Token Management
```python
# Force token refresh (limit: 1 per minute)
ka.auth(svr="prod")  # or "vps" for demo
```

### Error Handling
- Network timeouts and API rate limits are handled in kis_auth.py
- Check kis_devlp.yaml configuration for authentication errors
- Verify HTS ID accuracy for WebSocket connection issues

### Common Issues
- **Token errors**: Re-authenticate using `ka.auth()`
- **Config errors**: Verify kis_devlp.yaml app keys and account numbers
- **WebSocket errors**: Confirm HTS ID in kis_devlp.yaml
- **Dependency errors**: Run `uv sync --reinstall`

## API Environment Switching

### Real vs Demo Trading
Configure in function calls:
- `env_dv="real"`: Production trading
- `env_dv="demo"`: Paper trading

### Account Types (my_prod in kis_devlp.yaml)
- "01": General account
- "03": Domestic futures/options
- "08": Overseas futures/options  
- "22": Pension savings
- "29": Retirement pension

## Development Notes

This codebase follows the coding conventions in `docs/convention.md`:
- Snake_case naming throughout
- Comprehensive docstrings with examples
- Type hints for function parameters
- Modular design with single responsibility principle
- Explicit imports (no wildcards)
- Structured error handling with logging