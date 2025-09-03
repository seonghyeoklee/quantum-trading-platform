# KIS Adapter Trading Mode 개발자 가이드

## 📖 개요

이 가이드는 Quantum Trading Platform의 KIS Adapter에서 Trading Mode 기능을 사용하는 개발자를 위한 실용적인 문서입니다.

**Target Audience**: 백엔드 개발자, 프론트엔드 개발자, API 통합 담당자
**Prerequisites**: KIS Open API 기본 지식, HTTP API 호출 경험
**Related Systems**: Spring Boot Backend, Next.js Frontend

## 🎯 Quick Start

### 기본 사용법

```bash
# 모의투자 모드 (기본값)
curl "http://localhost:8000/domestic/price/005930"

# 실전투자 모드
curl "http://localhost:8000/domestic/price/005930?trading_mode=LIVE" \
     -H "X-KIS-Token: YOUR_ACCESS_TOKEN"
```

### 지원되는 값

- **LIVE**: 실전투자 (Production KIS Server)
- **SANDBOX**: 모의투자 (VPS KIS Server, 기본값)

## 🏗️ 아키텍처 이해

### 인증 우선순위 시스템

```
1순위: X-KIS-Token 헤더 (외부 제공 토큰)
   ↓ 없으면
2순위: kis_devlp.yaml 설정 파일 토큰
```

### 서버 매핑 규칙

```yaml
LIVE 모드:
  server: prod
  endpoint: openapi.koreainvestment.com:9443
  
SANDBOX 모드:
  server: vps  
  endpoint: openapivts.koreainvestment.com:29443
```

## 🔧 API 사용 가이드

### 1. 국내 주식 API (6개)

#### 현재가 조회
```bash
# SANDBOX (기본값)
GET /domestic/price/005930

# LIVE 모드
GET /domestic/price/005930?trading_mode=LIVE
X-KIS-Token: YOUR_LIVE_TOKEN
```

#### 일봉/주봉/월봉 차트
```bash
# 삼성전자 최근 30일 일봉
GET /domestic/chart/daily/005930?period=D&count=30&trading_mode=LIVE
```

#### 분봉 차트
```bash
# 삼성전자 1분봉 (현재시간 기준)
GET /domestic/chart/minute/005930?time_div=1&start_time=090000
```

#### 호가정보
```bash
GET /domestic/orderbook/005930?trading_mode=LIVE
```

#### 종목 기본정보
```bash  
GET /domestic/info/005930
```

#### 종목 검색
```bash
GET /domestic/search?symbol=005930
```

### 2. 국내 지수 API (3개)

#### 시장지수 조회
```bash
# 코스피
GET /indices/domestic?index_code=0001

# 코스닥
GET /indices/domestic?index_code=1001

# 코스피200
GET /indices/domestic?index_code=2001
```

#### 지수 일봉 차트
```bash
GET /indices/domestic/chart/daily/0001?start_date=20241201&end_date=20241231&period=D
```

#### 지수 분봉 차트
```bash
GET /indices/domestic/chart/minute/0001?time_div=30&include_past=Y
```

### 3. 해외 주식 API (5개)

#### 해외 주식 현재가
```bash
# 애플(AAPL) - 뉴욕증권거래소
GET /overseas/NYS/price/AAPL?trading_mode=LIVE

# 테슬라(TSLA) - 나스닥
GET /overseas/NAS/price/TSLA
```

#### 해외 일봉 차트
```bash
GET /overseas/NYS/chart/daily/AAPL?start_date=20241201&end_date=20241231&period=D
```

#### 해외 분봉 차트
```bash  
GET /overseas/NYS/chart/minute/AAPL?nmin=1&pinc=1
```

#### 해외 종목 기본정보
```bash
# 애플 기본정보
GET /overseas/NYS/info/AAPL

# 소니(일본)
GET /overseas/TSE/info/6758
```

#### 해외 종목 검색
```bash
GET /overseas/NAS/search?symbol=AAPL&rsp_tp=0
```

### 4. 해외 지수 API (3개)

#### 해외 시장지수
```bash
# S&P 500
GET /indices/overseas/US?index_code=SPX

# 다우존스
GET /indices/overseas/US?index_code=DJI

# 니케이225
GET /indices/overseas/JP?index_code=N225
```

## 💻 코드 예시

### JavaScript/TypeScript (프론트엔드)

```typescript
// KIS Adapter 직접 호출 패턴
async function fetchStockPrice(symbol: string, mode: 'LIVE' | 'SANDBOX' = 'SANDBOX') {
  const url = `http://localhost:8000/domestic/price/${symbol}?trading_mode=${mode}`;
  const headers: Record<string, string> = {};
  
  // KIS 토큰이 있으면 헤더에 추가
  const kisToken = getKISToken();
  if (kisToken) {
    headers['X-KIS-Token'] = kisToken;
  }
  
  try {
    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Stock price fetch failed:', error);
    throw error;
  }
}

// 사용 예시
const price = await fetchStockPrice('005930', 'LIVE');
console.log('삼성전자 현재가:', price.data);
```

### Kotlin (백엔드)

```kotlin
@Service
class KisAdapterService(
    private val restTemplate: RestTemplate
) {
    
    fun getDomesticStockPrice(
        symbol: String, 
        tradingMode: String = "SANDBOX",
        kisToken: String? = null
    ): ApiResponse {
        val url = "http://localhost:8000/domestic/price/{symbol}?trading_mode={mode}"
        val headers = HttpHeaders()
        
        kisToken?.let { headers.set("X-KIS-Token", it) }
        
        val entity = HttpEntity<String>(headers)
        val uriVariables = mapOf(
            "symbol" to symbol,
            "mode" to tradingMode
        )
        
        return try {
            restTemplate.exchange(url, HttpMethod.GET, entity, ApiResponse::class.java, uriVariables).body
                ?: throw RuntimeException("Empty response from KIS Adapter")
        } catch (e: Exception) {
            logger.error("KIS Adapter call failed", e)
            throw KisAdapterException("Failed to fetch stock price", e)
        }
    }
}
```

### Python (KIS Adapter 내부)

```python
# 실제 구현된 함수 예시
@app.get("/domestic/price/{symbol}")
async def get_domestic_current_price(
    symbol: str,
    trading_mode: str = Query(
        "SANDBOX", 
        description="거래 모드: LIVE(실전투자) | SANDBOX(모의투자)", 
        regex="^(LIVE|SANDBOX)$"
    ),
    x_kis_token: Optional[str] = Header(
        None, 
        alias="X-KIS-Token", 
        description="KIS API 인증 토큰 (선택사항)"
    )
):
    try:
        # 통합 인증 시스템
        server_mode = authenticate_kis(x_kis_token, trading_mode)
        
        # KIS API 호출
        trenv = ka.getTREnv()
        res = ka.kis_app_inquire_price(symbol, trenv)
        
        if res.isOK():
            return create_success_response(res.getBody(), "현재가 조회 성공")
        else:
            return create_error_response(f"KIS API 오류: {res.getMessage()}")
            
    except Exception as e:
        logger.error(f"현재가 조회 실패: {str(e)}")
        return create_error_response(f"서버 오류: {str(e)}")
```

## 🚨 에러 처리 가이드

### 일반적인 에러 상황

#### 1. 잘못된 trading_mode 값

```json
// Request
GET /domestic/price/005930?trading_mode=INVALID

// Response (422)
{
  "detail": [
    {
      "loc": ["query", "trading_mode"],
      "msg": "string should match pattern '^(LIVE|SANDBOX)$'",
      "type": "value_error.regex",
      "ctx": {"pattern": "^(LIVE|SANDBOX)$"}
    }
  ]
}
```

#### 2. KIS API 인증 실패

```json
// Response (500)
{
  "success": false,
  "message": "KIS API 오류: [40003000] 인증 토큰이 유효하지 않습니다",
  "data": null,
  "timestamp": "2025-09-02T10:30:00Z"
}
```

#### 3. 네트워크 오류

```json
// Response (500)
{
  "success": false,
  "message": "서버 오류: Connection timeout",
  "data": null,
  "timestamp": "2025-09-02T10:30:00Z"
}
```

### 에러 처리 모범 사례

```typescript
async function robustKisCall(symbol: string, mode: 'LIVE' | 'SANDBOX') {
  const maxRetries = 3;
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await fetchStockPrice(symbol, mode);
      return result;
    } catch (error) {
      lastError = error;
      console.warn(`Attempt ${attempt} failed:`, error);
      
      // 422 에러는 재시도하지 않음 (클라이언트 오류)
      if (error.status === 422) {
        throw error;
      }
      
      // 마지막 시도가 아니면 대기 후 재시도
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  }
  
  throw lastError;
}
```

## ⚡ 성능 최적화

### 1. 토큰 관리 최적화

```typescript
class KISTokenManager {
  private tokenCache: Map<string, string> = new Map();
  
  async getToken(mode: 'LIVE' | 'SANDBOX'): Promise<string> {
    const cached = this.tokenCache.get(mode);
    if (cached && this.isTokenValid(cached)) {
      return cached;
    }
    
    // 새 토큰 발급
    const newToken = await this.issueNewToken(mode);
    this.tokenCache.set(mode, newToken);
    return newToken;
  }
  
  private isTokenValid(token: string): boolean {
    // JWT 토큰 만료 시간 확인 로직
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }
}
```

### 2. 배치 처리

```typescript
async function batchStockPrices(symbols: string[], mode: 'LIVE' | 'SANDBOX') {
  const BATCH_SIZE = 10;
  const results: any[] = [];
  
  for (let i = 0; i < symbols.length; i += BATCH_SIZE) {
    const batch = symbols.slice(i, i + BATCH_SIZE);
    const promises = batch.map(symbol => 
      fetchStockPrice(symbol, mode).catch(error => ({ symbol, error }))
    );
    
    const batchResults = await Promise.all(promises);
    results.push(...batchResults);
    
    // Rate limiting 고려한 대기
    if (i + BATCH_SIZE < symbols.length) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  return results;
}
```

## 📊 모니터링 & 로깅

### 로그 분석 가이드

KIS Adapter 로그에서 확인해야 할 주요 패턴:

```bash
# 인증 성공 로그
✅ 인증 시스템: 🔑 외부 토큰 사용: ***제공됨*** (모드: LIVE)
✅ 서버 매핑: 🌐 KIS 서버 연결: LIVE → prod → openapi.koreainvestment.com:9443

# 인증 실패 로그
❌ 인증 오류: [40003000] 유효하지 않은 토큰

# API 호출 로그  
🔄 KIS API Call: API 호출 시작
✅ API Response: 응답 성공 (200ms)
```

### 메트릭 수집

```python
# KIS Adapter 내부에서 수집하는 메트릭
- trading_mode별 호출 횟수
- 응답 시간 분포
- 에러율 (trading_mode별)
- 토큰 사용 패턴
```

## 🔒 보안 고려사항

### 1. 토큰 관리

- **X-KIS-Token 헤더**: HTTPS 연결에서만 사용
- **kis_devlp.yaml**: 파일 권한 600으로 설정
- **로그**: 토큰 값 마스킹 처리 필수

### 2. 환경 분리

```yaml
# 개발 환경에서는 SANDBOX만 사용
development:
  default_trading_mode: SANDBOX
  allow_live_mode: false

# 프로덕션 환경에서만 LIVE 허용  
production:
  default_trading_mode: SANDBOX  # 안전한 기본값
  allow_live_mode: true
```

## 🛠️ 트러블슈팅

### 일반적인 문제와 해결책

#### Q1: "trading_mode 파라미터가 인식되지 않아요"
A1: KIS Adapter가 최신 버전인지 확인하고, OpenAPI 문서(`/docs`)에서 해당 API가 trading_mode를 지원하는지 확인하세요.

#### Q2: "LIVE 모드에서 계속 에러가 나요"  
A2: kis_devlp.yaml의 LIVE 환경 설정과 실제 KIS 계좌 권한을 확인하세요.

#### Q3: "토큰이 계속 만료돼요"
A3: KIS 토큰은 6시간마다 갱신이 필요합니다. 토큰 캐싱과 자동 갱신 로직을 구현하세요.

### 디버깅 체크리스트

```bash
# 1. 서비스 상태 확인
curl http://localhost:8000/health

# 2. OpenAPI 문서 확인
open http://localhost:8000/docs

# 3. 설정 파일 확인
cat ~/KIS/config/kis_devlp.yaml

# 4. 로그 확인
tail -f kis_adapter.log | grep "trading_mode"
```

## 📚 참고 자료

- [KIS Open API 공식 문서](https://apiportal.koreainvestment.com/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [프로젝트 기술 명세서](./MVP_1.0_KIS_Adapter_Trading_Mode_Implementation.md)
- [메인 프로젝트 문서](../../CLAUDE.md)

---

**마지막 업데이트**: 2025-09-02  
**문서 버전**: 1.0  
**관련 구현**: MVP 1.0 KIS Adapter Trading Mode