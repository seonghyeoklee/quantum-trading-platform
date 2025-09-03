# Quantum Trading Platform - MVP 1.0 KIS API 유량 제한 정책

**📋 기획 히스토리 #012 - KIS API 유량 제한 정책**

## 프로젝트 개요
- **버전**: MVP 1.0
- **목적**: KIS API 유량 제한 준수한 안정적 자동매매 시스템
- **기준일**: 2025.04.28 KIS 공식 정책
- **특징**: Rate Limiting 시스템으로 API 안정성 확보

---

## KIS API 유량 제한 정책 (2025.04.28 기준)

### REST API 유량 제한
- **실전투자 (LIVE)**: 1초당 20건
- **모의투자 (SANDBOX)**: 1초당 2건  
- **제한 단위**: 계좌별 (1계좌당 독립적 유량)
- **초과시**: 429 Too Many Requests 응답

### WEBSOCKET 유량 제한
- **세션당 등록 제한**: 실시간 데이터 최대 41건
- **제한 범위**: 국내주식 + 해외주식 + 국내파생 + 해외파생 합산
- **실시간 데이터 종류**: 
  - 실시간체결가
  - 호가
  - 예상체결  
  - 체결통보
- **제한 단위**: 계좌(앱키)별 1세션
- **다중 세션**: 1개 PC에서 여러 계좌(앱키) 동시 연결 가능

### 유량 확대 방안
- **현재**: 초과 유량 과금 정책 없음
- **해결책**: 추가 계좌 API 신청 후 다중 앱키 사용
- **제한 기준**: 앱키 단위로 유량 분리

---

## 시스템 설계 영향 분석

### Rate Limiting 구현 필요사항
1. **환경별 유량 관리**: LIVE(20건/초), SANDBOX(2건/초)
2. **Queue 시스템**: 대기열로 유량 초과 방지
3. **다중 계좌 지원**: 유량 확장을 위한 멀티 앱키
4. **에러 처리**: 유량 초과시 대기 및 재시도

### 기술적 구현 전략
```kotlin
// 환경별 유량 제한 설정
enum class KisRateLimit(
    val restCallsPerSecond: Int,
    val websocketSessionLimit: Int,
    val websocketDataLimit: Int
) {
    LIVE(20, 1, 41),    // 실전투자
    SANDBOX(2, 1, 41)   // 모의투자
}

// 유량 제한 체크 로직
class KisRateLimiter {
    fun canMakeApiCall(kisSettingId: Long, environment: KisEnvironment): Boolean {
        val limit = KisRateLimit.valueOf(environment.name)
        val recentCalls = getRecentApiCalls(kisSettingId, Duration.ofSeconds(1))
        
        return recentCalls.size < limit.restCallsPerSecond
    }
    
    fun waitUntilNextAvailableSlot(kisSettingId: Long, environment: KisEnvironment): Duration {
        // 다음 호출 가능 시간 계산
        val limit = KisRateLimit.valueOf(environment.name)
        val oldestCall = getOldestRecentCall(kisSettingId, Duration.ofSeconds(1))
        
        return if (oldestCall != null) {
            Duration.between(Instant.now(), oldestCall.plus(1, ChronoUnit.SECONDS))
        } else {
            Duration.ZERO
        }
    }
}
```

---

## 데이터베이스 스키마 확장

### API 호출 이력 관리 테이블
```sql
-- API 호출 유량 관리
CREATE TABLE kis_api_usage_log (
    id BIGSERIAL PRIMARY KEY,
    kis_setting_id BIGINT NOT NULL REFERENCES user_kis_settings(id),
    
    -- 호출 정보
    api_endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    
    -- 유량 관리
    called_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    response_status INT,
    response_time_ms INT,
    
    -- 제한 관리
    environment VARCHAR(20) NOT NULL, -- 'LIVE' or 'SANDBOX' 
    rate_limit_remaining INT, -- 남은 호출 수
    rate_limit_reset_at TIMESTAMP, -- 제한 리셋 시간
    
    -- 에러 처리
    is_rate_limited BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

-- 유량 관리용 인덱스
CREATE INDEX idx_kis_api_usage_setting_time ON kis_api_usage_log(kis_setting_id, called_at);
CREATE INDEX idx_kis_api_usage_environment_time ON kis_api_usage_log(environment, called_at);
CREATE INDEX idx_kis_api_usage_rate_limited ON kis_api_usage_log(is_rate_limited, called_at);
```

### 웹소켓 실시간 등록 관리 테이블
```sql
-- 웹소켓 실시간 데이터 등록 현황
CREATE TABLE kis_websocket_registrations (
    id BIGSERIAL PRIMARY KEY,
    kis_setting_id BIGINT NOT NULL REFERENCES user_kis_settings(id),
    
    -- 등록 정보
    data_type VARCHAR(50) NOT NULL, -- '실시간체결가', '호가', '예상체결', '체결통보'
    symbol VARCHAR(20), -- 종목코드 (체결통보의 경우 NULL)
    hts_id VARCHAR(50), -- 체결통보용 HTS ID
    
    -- 상태 관리
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    unregistered_at TIMESTAMP,
    
    -- 제약조건
    CONSTRAINT check_symbol_or_hts_id CHECK (
        (data_type = '체결통보' AND hts_id IS NOT NULL AND symbol IS NULL) OR
        (data_type != '체결통보' AND symbol IS NOT NULL AND hts_id IS NULL)
    )
);

-- 인덱스
CREATE INDEX idx_kis_websocket_setting_active ON kis_websocket_registrations(kis_setting_id, is_active);
CREATE INDEX idx_kis_websocket_data_type ON kis_websocket_registrations(data_type, is_active);
```

---

## API 설계 (유량 관리 기능)

### 유량 상태 조회
```bash
# 계좌별 API 사용량 조회
curl -X GET "http://localhost:8080/api/v1/kis/settings/{settingId}/rate-limit" \
  -H "Authorization: Bearer {user_token}"

# 응답
{
  "settingId": 1,
  "environment": "LIVE",
  "rateLimit": {
    "restCallsPerSecond": 20,
    "currentUsage": 15,
    "remainingCalls": 5,
    "resetAt": "2025-09-01T10:30:01",
    "nextAvailableAt": "2025-09-01T10:30:00.250"
  },
  "websocketLimit": {
    "maxDataRegistrations": 41,
    "currentRegistrations": 25,
    "availableSlots": 16,
    "registrationsByType": {
      "실시간체결가": 10,
      "호가": 8,
      "예상체결": 5,
      "체결통보": 1
    }
  }
}
```

### 다중 계좌 설정 (유량 확장용)
```bash
# 동일 환경에 추가 계좌 등록
curl -X POST http://localhost:8080/api/v1/kis/settings \
  -H "Authorization: Bearer {user_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "LIVE",
    "appKey": "추가_앱키",
    "appSecret": "추가_앱시크릿", 
    "htsId": "사용자_HTS_ID",
    "accountNumber": "추가계좌번호",
    "productCode": "01",
    "purpose": "RATE_LIMIT_EXPANSION",
    "description": "유량 확장을 위한 추가 계좌"
  }'

# 응답
{
  "id": 3,
  "environment": "LIVE",
  "accountNumber": "추가계좌번호",
  "purpose": "RATE_LIMIT_EXPANSION",
  "combinedRateLimit": {
    "totalCallsPerSecond": 40, // 기본 20 + 추가 20
    "activeAccounts": 2
  }
}
```

### API 호출시 유량 관리
```bash
# 주가 조회 (유량 관리 적용)
curl -X GET "http://localhost:8080/api/v1/trading/stock/005930/price?env=LIVE" \
  -H "Authorization: Bearer {user_token}"

# 유량 초과시 응답
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 1

{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "API 호출 유량을 초과했습니다",
  "details": {
    "environment": "LIVE", 
    "limit": 20,
    "current": 20,
    "retryAfterSeconds": 1,
    "nextAvailableAt": "2025-09-01T10:30:01"
  },
  "suggestions": [
    "1초 후 재시도하세요",
    "추가 계좌 등록으로 유량을 확장할 수 있습니다",
    "SANDBOX 환경에서 테스트하세요 (2건/초)"
  ]
}
```

### 웹소켓 실시간 데이터 관리
```bash
# 실시간 데이터 등록 현황 조회
curl -X GET "http://localhost:8080/api/v1/kis/websocket/registrations" \
  -H "Authorization: Bearer {user_token}"

# 응답
{
  "totalLimit": 41,
  "currentRegistrations": [
    {
      "type": "실시간체결가",
      "symbols": ["005930", "000660", "035420"],
      "count": 3
    },
    {
      "type": "호가",
      "symbols": ["005930", "000660"],
      "count": 2  
    },
    {
      "type": "체결통보",
      "htsId": "사용자_HTS_ID",
      "count": 1
    }
  ],
  "used": 6,
  "available": 35
}
```

### 실시간 데이터 등록/해제
```bash
# 실시간 체결가 등록
curl -X POST "http://localhost:8080/api/v1/kis/websocket/register" \
  -H "Authorization: Bearer {user_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "environment": "LIVE",
    "dataType": "실시간체결가",
    "symbols": ["005930", "000660", "035420"]
  }'

# 등록 한도 초과시 응답
HTTP/1.1 400 Bad Request
{
  "error": "WEBSOCKET_REGISTRATION_LIMIT_EXCEEDED",
  "message": "실시간 데이터 등록 한도를 초과했습니다",
  "details": {
    "limit": 41,
    "current": 38,
    "requested": 5,
    "available": 3
  },
  "suggestion": "기존 등록을 해제하거나 추가 계좌를 사용하세요"
}
```

---

## Rate Limiting 시스템 구현

### 호출 빈도 제어 로직
```kotlin
@Service
class KisApiRateLimitService {
    
    @Cacheable("rate-limit-status")
    fun checkRateLimit(kisSettingId: Long, environment: KisEnvironment): RateLimitStatus {
        val limit = KisRateLimit.valueOf(environment.name)
        val recentCalls = getRecentApiCalls(kisSettingId, Duration.ofSeconds(1))
        
        return RateLimitStatus(
            limit = limit.restCallsPerSecond,
            current = recentCalls.size,
            remaining = limit.restCallsPerSecond - recentCalls.size,
            resetAt = LocalDateTime.now().plusSeconds(1)
        )
    }
    
    @Async
    fun logApiCall(kisSettingId: Long, endpoint: String, httpMethod: String, 
                  responseStatus: Int, responseTime: Long) {
        val log = KisApiUsageLog(
            kisSettingId = kisSettingId,
            apiEndpoint = endpoint,
            httpMethod = httpMethod,
            responseStatus = responseStatus,
            responseTimeMs = responseTime.toInt(),
            isRateLimited = responseStatus == 429
        )
        
        apiUsageLogRepository.save(log)
    }
}
```

### Queue 기반 API 호출 관리
```kotlin
@Component
class KisApiCallQueue {
    private val queues = ConcurrentHashMap<Long, BlockingQueue<ApiCallRequest>>()
    
    @Scheduled(fixedDelay = 50) // 50ms마다 실행
    fun processQueuedCalls() {
        queues.forEach { (kisSettingId, queue) ->
            val setting = kisSettingRepository.findById(kisSettingId)
            if (setting != null && rateLimitService.canMakeApiCall(kisSettingId, setting.environment)) {
                val request = queue.poll()
                request?.let { 
                    processApiCall(it)
                }
            }
        }
    }
    
    fun queueApiCall(kisSettingId: Long, request: ApiCallRequest): CompletableFuture<ApiResponse> {
        val queue = queues.computeIfAbsent(kisSettingId) { LinkedBlockingQueue() }
        queue.offer(request)
        return request.future
    }
}
```

---

## 성능 최적화 전략

### API 호출 최적화
1. **배치 처리**: 가능한 경우 여러 종목 한번에 조회
   - 예: 여러 종목 현재가 → 1회 호출로 처리
2. **캐싱 전략**: 자주 조회하는 데이터 Redis 캐시
   - TTL: 실시간 데이터 1초, 기본 정보 1분
3. **우선순위 처리**: 중요한 API 호출 우선 실행
   - 체결 알림 > 현재가 조회 > 과거 데이터
4. **지연 호출**: 비중요한 호출은 유량 여유시 실행

### 다중 계좌 활용 전략
1. **로드 밸런싱**: 여러 앱키간 호출 분산
   ```kotlin
   fun selectOptimalAccount(environment: KisEnvironment): UserKisSetting {
       return accounts.filter { it.environment == environment }
                     .minByOrNull { it.getCurrentUsage() }
   }
   ```

2. **페일오버**: 한 계좌 유량 초과시 다른 계좌 사용
3. **전용 목적별 분리**: 
   - 실시간 데이터 전용 계좌
   - API 호출 전용 계좌
   - 백업 계좌

### 웹소켓 최적화
1. **선택적 등록**: 필요한 종목만 실시간 등록
2. **동적 관리**: 거래 종료 종목 자동 해제
3. **우선순위**: 중요 종목 우선 등록

---

## 모니터링 및 알림

### 유량 사용량 대시보드
- **실시간 사용량**: 환경별, 계좌별 현재 사용률
- **히스토리**: 시간별 API 호출 패턴
- **경고**: 유량 80% 초과시 알림
- **예측**: 사용 패턴 기반 유량 부족 예상

### 알림 정책
```yaml
경고 수준:
  - 70% 사용: 정보성 알림
  - 80% 사용: 주의 경고
  - 90% 사용: 심각 경고  
  - 100% 사용: 긴급 알림 + 추가 계좌 권장
```

---

## 에러 처리 및 복구

### 유량 초과 에러 처리
1. **자동 대기**: 다음 사용 가능 시점까지 대기
2. **계좌 전환**: 다른 사용 가능 계좌로 자동 전환
3. **Queue 활용**: 대기열에 등록 후 순차 처리
4. **사용자 알림**: 유량 초과 상황 및 대응 방안 안내

### 장애 복구 절차
1. **상태 확인**: 모든 계좌의 유량 상태 체크
2. **우선순위 재조정**: 중요 API 우선 처리
3. **임시 제한**: 비필수 API 일시 중단
4. **추가 계좌**: 긴급시 임시 계좌 활성화

---

**문서 작성일**: 2025-09-01  
**작성자**: 기획자  
**버전**: MVP 1.0  
**참고**: KIS API 유량 안내 (2025.04.28 기준)  
**다음 업데이트**: 실제 운영 데이터 기반 최적화

이 KIS API 유량 제한 정책을 준수하여 안정적이고 효율적인 자동매매 시스템을 구축할 수 있습니다.