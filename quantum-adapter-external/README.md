# Quantum Adapter External

External data adapter for Quantum Trading Platform providing integration with:

- Naver News API
- DART API (planned)
- Other external data sources

## Features

- FastAPI REST API server on port 8001
- Secure API key management with environment variables
- Comprehensive error handling and logging
- Async HTTP client with timeout and retry logic
- Health monitoring endpoints

## API Endpoints

### Health
- `GET /health` - Service health check
- `GET /health/ready` - Readiness check

### News
- `GET /news/search` - Search news by keyword
- `GET /news/latest/{keyword}` - Get latest news for keyword
- `GET /news/financial/{symbol}` - Get financial news for stock symbol

## Setup

1. Create `.env` file with your API credentials:
```bash
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
DEBUG=true
SERVER_PORT=8001
```

2. Install dependencies:
```bash
uv sync
```

3. Run the server:
```bash
uv run python main.py
```

## Development

- Documentation: http://localhost:8001/docs (when DEBUG=true)
- Health check: http://localhost:8001/health