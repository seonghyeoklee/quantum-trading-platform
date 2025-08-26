# Kiwoom Securities API Integration Guide

## 📋 목차
1. [개요](#개요)
2. [아키텍처](#아키텍처)
3. [API 엔드포인트](#api-엔드포인트)
4. [사용 가이드](#사용-가이드)
5. [Python 어댑터 API](#python-어댑터-api)
6. [모니터링](#모니터링)
7. [문제 해결](#문제-해결)

## 개요

Quantum Trading Platform의 키움증권 API 통합은 다음 기능을 제공합니다:

- **실시간 시장 데이터**: WebSocket을 통한 실시간 가격 정보
- **자동매매 주문**: REST API를 통한 주문 실행
- **계좌 관리**: 다중 사용자 계좌 지원
- **토큰 관리**: 자동 갱신 및 캐싱
- **사용 모니터링**: API 사용량 추적 및 분석

## 아키텍처

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Frontend    │────▶│  Spring API  │────▶│Python Adapter│
│  (Next.js)   │     │  (Java 21)   │     │  (FastAPI)   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  PostgreSQL  │     │ Kiwoom Open  │
                     │   (Query DB)  │     │     API      │
                     └──────────────┘     └──────────────┘
```

## API 엔드포인트

### 🔐 인증 관련

#### 계좌 정보 조회
```http
GET /api/v1/kiwoom-accounts/me
Authorization: Bearer {JWT_TOKEN}
```

**Response:**
```json
{
  "hasAccount": true,
  "kiwoomAccountId": "KIWOOM_ACC_001",
  "assignedAt": "2024-11-26T10:00:00Z",
  "isActive": true,
  "hasValidToken": true,
  "tokenExpiresAt": "2024-11-27T10:00:00Z"
}
```

#### 인증 정보 업데이트
```http
PUT /api/v1/kiwoom-accounts/me/credentials
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "clientId": "your-app-key",
  "clientSecret": "your-app-secret"
}
```

#### 토큰 조회
```http
GET /api/v1/kiwoom-accounts/me/token
Authorization: Bearer {JWT_TOKEN}
```

**Response:**
```json
{
  "hasToken": true,
  "accessToken": "kiwoom-access-token",
  "tokenType": "Bearer",
  "message": "Token retrieved successfully"
}
```

### 📊 시장 데이터

#### 주식 정보 조회
```http
GET /api/v1/stocks/{stockCode}
Authorization: Bearer {JWT_TOKEN}
```

#### 차트 데이터 조회
```http
GET /api/v1/charts/{stockCode}?period={period}&interval={interval}
Authorization: Bearer {JWT_TOKEN}
```

Parameters:
- `period`: D (일), W (주), M (월), Y (년)
- `interval`: 1, 5, 10, 30, 60 (분)

### 💼 주문 관련

#### 주문 생성
```http
POST /api/v1/orders
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "stockCode": "005930",
  "orderType": "LIMIT",
  "orderSide": "BUY",
  "quantity": 10,
  "price": 70000
}
```

#### 주문 취소
```http
DELETE /api/v1/orders/{orderId}
Authorization: Bearer {JWT_TOKEN}
```

### 🔄 실시간 데이터 (WebSocket)

#### 연결
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/realtime');

ws.onopen = () => {
  // 인증
  ws.send(JSON.stringify({
    type: 'AUTH',
    token: 'your-jwt-token'
  }));
  
  // 종목 구독
  ws.send(JSON.stringify({
    type: 'SUBSCRIBE',
    stockCodes: ['005930', '000660']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('실시간 데이터:', data);
};
```

## 사용 가이드

### 1. 초기 설정

1. **키움증권 Open API 가입**
   - [키움증권 Open API 센터](https://apiportal.koreainvestment.com) 접속
   - 앱 등록 및 App Key/Secret 발급

2. **환경 변수 설정**
   ```bash
   # .env.local (Frontend)
   NEXT_PUBLIC_API_URL=http://localhost:8080
   
   # application.yml (Backend)
   kiwoom:
     adapter-url: http://localhost:8100
   ```

3. **계좌 연결**
   - 관리자가 사용자에게 키움증권 계좌 할당
   - 사용자가 App Key/Secret 입력

### 2. 기본 사용법

```javascript
// Frontend 예제
import { useKiwoomAPI } from '@/hooks/useKiwoomAPI';

function TradingComponent() {
  const { account, updateCredentials, getToken } = useKiwoomAPI();
  
  // 계좌 정보 확인
  if (!account.hasAccount) {
    return <div>계좌가 연결되지 않았습니다.</div>;
  }
  
  // 인증 정보 업데이트
  const handleUpdateCredentials = async () => {
    await updateCredentials({
      clientId: 'your-app-key',
      clientSecret: 'your-app-secret'
    });
  };
  
  // 토큰 갱신
  const handleRefreshToken = async () => {
    const token = await getToken();
    console.log('New token:', token);
  };
}
```

### 3. 주문 실행

```java
// Backend 예제
@Service
public class TradingService {
    
    @Autowired
    private CommandGateway commandGateway;
    
    public void createOrder(String userId, OrderRequest request) {
        // 1. 키움증권 계좌 확인
        KiwoomAccountView account = kiwoomQueryService
            .getUserKiwoomAccount(userId)
            .orElseThrow(() -> new IllegalStateException("No account"));
        
        // 2. 주문 생성
        CreateOrderCommand command = new CreateOrderCommand(
            OrderId.generate(),
            UserId.of(userId),
            Symbol.of(request.getStockCode()),
            request.getOrderType(),
            request.getOrderSide(),
            Quantity.of(request.getQuantity()),
            Money.of(request.getPrice())
        );
        
        commandGateway.send(command);
    }
}
```

## Python 어댑터 API

### 환경 설정
```bash
# Sandbox 모드
KIWOOM_SANDBOX_MODE=true
KIWOOM_SANDBOX_APP_KEY=your-sandbox-key
KIWOOM_SANDBOX_APP_SECRET=your-sandbox-secret

# Production 모드
KIWOOM_SANDBOX_MODE=false
KIWOOM_PRODUCTION_APP_KEY=your-production-key
KIWOOM_PRODUCTION_APP_SECRET=your-production-secret
```

### 주요 엔드포인트

#### OAuth 토큰 발급
```http
POST http://localhost:8100/api/fn_au10001
```

#### 주식 정보 조회
```http
GET http://localhost:8100/api/stocks/{stock_code}
```

#### 차트 데이터
```http
GET http://localhost:8100/api/chart/{stock_code}/{period}
```

#### WebSocket 실시간 데이터
```python
import asyncio
import websockets
import json

async def connect_realtime():
    async with websockets.connect('ws://localhost:8100/ws/realtime') as ws:
        # 종목 구독
        await ws.send(json.dumps({
            'type': 'SUBSCRIBE',
            'stock_codes': ['005930', '000660']
        }))
        
        # 데이터 수신
        async for message in ws:
            data = json.loads(message)
            print(f"실시간: {data}")

asyncio.run(connect_realtime())
```

## 모니터링

### 1. API 사용량 확인

```sql
-- 일별 API 사용량
SELECT 
    DATE(usage_timestamp) as date,
    COUNT(*) as total_calls,
    SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as success_count,
    AVG(response_time_ms) as avg_response_time
FROM kiwoom_api_usage_log_view
WHERE usage_timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(usage_timestamp)
ORDER BY date DESC;
```

### 2. Grafana 대시보드

- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: quantum123

주요 메트릭:
- API 호출 성공률
- 평균 응답 시간
- 엔드포인트별 사용량
- 에러 발생 빈도

### 3. 로그 확인

```bash
# Python 어댑터 로그
docker logs quantum-kiwoom-adapter

# Spring API 로그
docker logs quantum-web-api

# 특정 사용자 API 사용 로그
curl -X GET http://localhost:8080/api/v1/admin/kiwoom/logs?userId=USER_001 \
  -H "Authorization: Bearer {ADMIN_TOKEN}"
```

## 문제 해결

### 자주 발생하는 문제

#### 1. 토큰 만료
**증상**: 401 Unauthorized 에러
**해결**:
```javascript
// 토큰 갱신
const refreshToken = async () => {
  const response = await fetch('/api/kiwoom-accounts/me/token', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  });
  const data = await response.json();
  if (data.hasToken) {
    // 새 토큰으로 업데이트
    localStorage.setItem('kiwoomToken', data.accessToken);
  }
};
```

#### 2. WebSocket 연결 실패
**증상**: WebSocket connection failed
**해결**:
1. Python 어댑터 상태 확인: `curl http://localhost:8100/health`
2. 네트워크 설정 확인: `docker network ls`
3. 방화벽 설정 확인

#### 3. API 사용 한도 초과
**증상**: 429 Too Many Requests
**해결**:
- API 호출 간격 조정 (최소 100ms)
- 배치 요청 사용
- 캐싱 활용

#### 4. 계좌 연결 안됨
**증상**: "No account assigned" 에러
**해결**:
1. 관리자에게 계좌 할당 요청
2. 인증 정보 업데이트
3. 토큰 갱신

### 디버깅 팁

1. **상세 로그 활성화**
   ```yaml
   # application.yml
   logging:
     level:
       com.quantum.trading.platform: DEBUG
   ```

2. **API 테스트**
   ```bash
   # Health check
   curl http://localhost:8080/actuator/health
   
   # Kiwoom adapter health
   curl http://localhost:8100/health
   ```

3. **데이터베이스 직접 조회**
   ```bash
   psql -h localhost -p 5433 -U quantum -d quantum_trading
   
   # 계좌 상태 확인
   SELECT * FROM kiwoom_account_view WHERE user_id = 'USER_001';
   
   # API 사용 로그 확인
   SELECT * FROM kiwoom_api_usage_log_view 
   WHERE user_id = 'USER_001' 
   ORDER BY usage_timestamp DESC LIMIT 10;
   ```

## 보안 고려사항

1. **API Key 관리**
   - 절대 코드에 하드코딩하지 마세요
   - 환경 변수 또는 Secret Manager 사용
   - 정기적으로 키 갱신

2. **네트워크 보안**
   - HTTPS 사용 (Production)
   - IP 화이트리스트 설정
   - Rate limiting 적용

3. **데이터 암호화**
   - Client ID/Secret은 AES-256으로 암호화
   - 민감한 데이터는 로그에 남기지 않음

## 추가 리소스

- [키움증권 Open API 문서](https://apiportal.koreainvestment.com/apiservice/oauth2)
- [Quantum Trading Platform GitHub](https://github.com/your-org/quantum-trading-platform)
- [FastAPI 문서](https://fastapi.tiangolo.com)
- [Axon Framework 문서](https://docs.axoniq.io)