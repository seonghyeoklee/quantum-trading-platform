# Backend KIS 토큰 관리 제거 실행 가이드

## 🎯 백엔드 제거 개요

**대상**: Spring Boot Kotlin 백엔드의 모든 KIS 토큰 관리 기능
**소요시간**: 약 1일
**난이도**: 중급 (데이터베이스 스키마 변경 포함)

## 📋 제거 체크리스트

### Phase 1: 데이터베이스 정리 ✅

#### 1. 기존 KIS 관련 테이블 확인
```sql
-- 제거 전 데이터 백업 (필요시)
SELECT COUNT(*) FROM kis_accounts;
SELECT COUNT(*) FROM kis_tokens;

-- 테이블 존재 여부 확인
SHOW TABLES LIKE 'kis_%';
```

#### 2. 데이터베이스 마이그레이션 스크립트 생성
```sql
-- src/main/resources/db/migration/V{version}__remove_kis_token_tables.sql
-- KIS 관련 테이블 제거
DROP TABLE IF EXISTS kis_tokens;
DROP TABLE IF EXISTS kis_accounts;

-- 관련 인덱스 제거 (자동 삭제되지만 명시적 확인)
-- DROP INDEX IF EXISTS idx_kis_tokens_user_environment;
-- DROP INDEX IF EXISTS idx_kis_accounts_user_environment;

-- 시퀀스 제거 (PostgreSQL의 경우)
-- DROP SEQUENCE IF EXISTS kis_tokens_seq;
-- DROP SEQUENCE IF EXISTS kis_accounts_seq;
```

#### 3. 마이그레이션 실행
```bash
cd quantum-web-api
./gradlew flywayMigrate
# 또는 애플리케이션 실행 시 자동 마이그레이션
./gradlew bootRun
```

### Phase 2: 코드 파일 제거 ✅

#### 1. 엔티티 클래스 제거
```bash
# 제거할 파일들
rm src/main/kotlin/com/quantum/web/entity/KisAccount.kt
rm src/main/kotlin/com/quantum/web/entity/KisToken.kt

# enum 클래스 제거 (다른 곳에서 사용하지 않는 경우)
rm src/main/kotlin/com/quantum/web/entity/TokenStatus.kt
rm src/main/kotlin/com/quantum/web/entity/KisEnvironment.kt
```

#### 2. 레포지토리 인터페이스 제거
```bash
rm src/main/kotlin/com/quantum/web/repository/KisAccountRepository.kt
rm src/main/kotlin/com/quantum/web/repository/KisTokenRepository.kt
```

#### 3. 서비스 클래스 제거
```bash
rm src/main/kotlin/com/quantum/web/service/KisTokenService.kt
rm src/main/kotlin/com/quantum/web/service/KisApiClient.kt

# 암호화 서비스 (KIS 전용인 경우만)
rm src/main/kotlin/com/quantum/web/service/EncryptionService.kt
```

#### 4. 컨트롤러 제거
```bash
rm src/main/kotlin/com/quantum/web/controller/KisTokenController.kt
rm src/main/kotlin/com/quantum/web/controller/KisAccountController.kt
```

#### 5. DTO 및 요청/응답 클래스 제거
```bash
rm src/main/kotlin/com/quantum/web/dto/KisAccountRequest.kt
rm src/main/kotlin/com/quantum/web/dto/TokenResponse.kt
rm src/main/kotlin/com/quantum/web/dto/TokenRefreshRequest.kt
rm src/main/kotlin/com/quantum/web/dto/ValidationResponse.kt
```

### Phase 3: 설정 파일 정리 ✅

#### 1. application.yml 수정
```yaml
# 제거할 설정들
# kis:
#   token:
#     expires-hours: 6
#     encryption-key: ${KIS_ENCRYPTION_KEY:default-key}
#   api:
#     base-url: ${KIS_API_URL:https://openapi.koreainvestment.com:9443}
#   scheduler:
#     token-refresh-cron: "0 0 */5 * * *"
#     enabled: true

# 유지할 설정들 (기존 애플리케이션 설정)
server:
  port: 8080
spring:
  datasource:
    url: ${DATABASE_URL:jdbc:postgresql://localhost:5433/quantum_trading}
    # ... 기존 설정 유지
```

#### 2. 환경 변수 정리
```bash
# .env 파일에서 제거 (있다면)
# KIS_ENCRYPTION_KEY=
# KIS_API_URL=
```

### Phase 4: 의존성 주입 및 참조 제거 ✅

#### 1. 다른 서비스에서 KIS 관련 의존성 제거
```kotlin
// 예: UserService.kt에서 KIS 관련 의존성 제거
@Service
class UserService(
    private val userRepository: UserRepository,
    // private val kisTokenService: KisTokenService // 제거
) {
    
    // KIS 관련 메서드들 제거
    // suspend fun linkKisAccount(userId: Long, request: KisAccountRequest) { ... }
    // suspend fun getKisTokens(userId: Long): List<KisToken> { ... }
}
```

#### 2. 컴포넌트 스캔에서 제거되었는지 확인
```kotlin
// Application.kt 또는 Configuration에서 확인
// KIS 관련 패키지가 컴포넌트 스캔에서 자동 제외되는지 확인
```

### Phase 5: 테스트 코드 정리 ✅

#### 1. KIS 관련 테스트 파일 제거
```bash
rm src/test/kotlin/com/quantum/web/service/KisTokenServiceTest.kt
rm src/test/kotlin/com/quantum/web/controller/KisTokenControllerTest.kt
rm src/test/kotlin/com/quantum/web/repository/KisAccountRepositoryTest.kt
```

#### 2. 통합 테스트에서 KIS 관련 부분 제거
```kotlin
// ApplicationIntegrationTest.kt에서 수정
@SpringBootTest
class ApplicationIntegrationTest {
    
    @Test
    fun contextLoads() {
        // KIS 관련 빈들이 로드되지 않아도 정상 동작하는지 확인
    }
    
    // KIS 관련 테스트 메서드들 제거
    // @Test fun testKisTokenCreation() { ... }
    // @Test fun testKisAccountValidation() { ... }
}
```

## 🔧 수정 필요 파일들

### 1. 기존 인증 관련 코드 수정

#### AuthController.kt 수정
```kotlin
@RestController
@RequestMapping("/api/auth")
class AuthController(
    private val authService: AuthService,
    // private val kisTokenService: KisTokenService // 제거
) {
    
    @PostMapping("/login")
    suspend fun login(@RequestBody request: LoginRequest): ResponseEntity<LoginResponse> {
        val result = authService.login(request.email, request.password)
        
        // KIS 토큰 관련 로직 제거
        // val kisTokens = kisTokenService.getUserTokens(result.userId)
        
        return ResponseEntity.ok(LoginResponse(
            accessToken = result.accessToken,
            refreshToken = result.refreshToken,
            user = result.user
            // kisTokens = kisTokens // 제거
        ))
    }
}
```

#### LoginResponse.kt 수정
```kotlin
data class LoginResponse(
    val accessToken: String,
    val refreshToken: String,
    val user: UserInfo,
    // val kisTokens: Map<String, KisTokenInfo>? = null // 제거
)
```

### 2. 차트 관련 서비스 수정

#### ChartController.kt 수정 (KIS API 호출 방식 변경)
```kotlin
@RestController
@RequestMapping("/api/charts")
class ChartController(
    private val chartService: ChartService
    // private val kisTokenService: KisTokenService // 제거
) {
    
    @GetMapping("/domestic/{symbol}")
    suspend fun getDomesticChart(
        @PathVariable symbol: String,
        authentication: Authentication
    ): ResponseEntity<ChartResponse> {
        // 직접 KIS Adapter 호출 방식으로 변경
        return chartService.getDomesticChartData(symbol)
    }
}
```

#### ChartService.kt 수정
```kotlin
@Service
class ChartService(
    private val restTemplate: RestTemplate
    // private val kisTokenService: KisTokenService // 제거
) {
    
    suspend fun getDomesticChartData(symbol: String): ResponseEntity<ChartResponse> {
        // 기존: KIS 토큰 사용한 직접 호출
        // val kisToken = kisTokenService.getValidToken(userId, "SANDBOX")
        
        // 변경: KIS Adapter를 통한 간접 호출
        val response = restTemplate.getForEntity(
            "http://localhost:8000/domestic/chart/daily/$symbol",
            ChartResponse::class.java
        )
        
        return response
    }
}
```

## ✅ 제거 검증 단계

### 1. 빌드 검증
```bash
cd quantum-web-api

# 1. 컴파일 오류 없는지 확인
./gradlew compileKotlin

# 2. 전체 빌드 성공 확인
./gradlew build

# 3. 테스트 실행 (KIS 관련 테스트 제외)
./gradlew test
```

### 2. 애플리케이션 실행 검증
```bash
# 1. 애플리케이션 정상 실행 확인
./gradlew bootRun

# 2. 액추에이터를 통한 상태 확인
curl http://localhost:8080/actuator/health

# 3. 기본 API 엔드포인트 확인
curl http://localhost:8080/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com", "password":"password"}'
```

### 3. 데이터베이스 검증
```sql
-- KIS 관련 테이블이 제거되었는지 확인
SHOW TABLES LIKE 'kis_%';
-- 결과: Empty set (정상)

-- 기존 테이블들은 유지되는지 확인
SHOW TABLES;
-- users, portfolios 등 기존 테이블 존재 확인
```

### 4. API 엔드포인트 검증
```bash
# 제거된 KIS API가 404 반환하는지 확인
curl http://localhost:8080/api/kis/token -X POST
# Expected: 404 Not Found

curl http://localhost:8080/api/kis-accounts/me
# Expected: 404 Not Found

# 기존 API는 정상 동작하는지 확인
curl http://localhost:8080/api/auth/login -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com", "password":"password123"}'
# Expected: 200 OK with JWT token
```

## 🚨 주의사항 및 백업

### 제거 전 백업
```bash
# 1. 데이터베이스 백업
pg_dump quantum_trading > backup_before_kis_removal.sql

# 2. 코드 백업 (Git 커밋)
git add .
git commit -m "feat: backup before KIS token management removal"
git push origin feature/kis-token-removal
```

### 롤백 계획
```bash
# 문제 발생 시 롤백 방법
# 1. Git을 통한 코드 롤백
git reset --hard HEAD~1

# 2. 데이터베이스 롤백  
psql quantum_trading < backup_before_kis_removal.sql

# 3. 애플리케이션 재시작
./gradlew bootRun
```

## 🎯 제거 후 추가 작업

### 1. 문서 업데이트
- API 문서에서 KIS 관련 엔드포인트 제거
- 아키텍처 다이어그램 단순화
- README.md 업데이트

### 2. 모니터링 설정 변경
- KIS 토큰 상태 모니터링 제거
- 토큰 갱신 알람 해제
- 대시보드에서 KIS 관련 메트릭 제거

### 3. CI/CD 파이프라인 정리
- KIS 관련 환경 변수 제거
- 토큰 관리 관련 배포 스크립트 정리

---

**백엔드 개발자 참고사항**: 이 제거 작업을 통해 코드베이스가 대폭 단순해지고 유지보수성이 크게 향상됩니다. 다만 제거 과정에서 의존성 체크를 꼼꼼히 하여 기존 기능에 영향이 없도록 주의해야 합니다.