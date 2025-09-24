# KIS 모듈 아키텍처 리팩토링 플랜

## 📋 개요

현재 KIS 토큰 관리 모듈을 **DDD (Domain-Driven Design) + 헥사고날 아키텍처**로 리팩토링하여 명확한 레이어 분리와 의존성 역전을 달성합니다.

## 🎯 리팩토링 목표

1. **명확한 레이어 분리**: Domain, Application, Infrastructure 레이어 명확히 구분
2. **의존성 역전**: 포트와 어댑터를 통한 올바른 의존성 방향 설정
3. **테스트 용이성**: 인터페이스 기반으로 Mock 테스트 가능
4. **확장성**: 새로운 외부 시스템 연동 시 최소 변경으로 확장 가능

## 🚨 현재 문제점 분석

### 아키텍처 문제점

1. **레이어 혼재**
   - `KisTokenService`: Infrastructure 역할을 Application Layer에서 수행
   - `KisTokenManager`: Use Case인데 Service로 명명
   - `KisTokenPersistenceService`: Repository 역할을 Service로 명명

2. **의존성 방향 위반**
   - Application Layer가 Infrastructure 직접 의존 (RestClient)
   - 도메인 규칙이 외부 기술에 종속될 위험

3. **포트와 어댑터 부재**
   - 외부 KIS API에 대한 추상화 부족
   - 테스트하기 어려운 구조

### 현재 패키지 구조
```
com.quantum.kis/
├── config/                  ❌ Infrastructure가 Root에 위치
├── controller/              ❌ Infrastructure가 Root에 위치
├── dto/                     ❌ Infrastructure DTO가 Root에 위치
├── service/                 ❌ Application과 Infrastructure 혼재
├── scheduler/               ❌ Infrastructure가 Root에 위치
├── domain/                  ✅ 올바른 위치
└── infrastructure/          ✅ 일부만 올바른 위치
    └── persistence/
```

## 🏗️ 목표 아키텍처 (헥사고날 + DDD)

### 새로운 패키지 구조

```
com.quantum.kis/
├── domain/                           # 🟢 Domain Layer
│   ├── token/
│   │   ├── KisToken.java            # Aggregate Root
│   │   ├── Token.java               # Value Object
│   │   ├── KisTokenId.java          # Value Object
│   │   ├── TokenStatus.java         # Value Object
│   │   └── KisTokenRepository.java  # Repository Interface (Domain)
│   ├── KisEnvironment.java          # Value Object
│   ├── TokenType.java               # Value Object
│   └── exception/
│       └── KisApiException.java     # Domain Exception
│
├── application/                      # 🟡 Application Layer
│   ├── port/
│   │   ├── in/                      # Inbound Ports (Use Cases)
│   │   │   ├── GetTokenUseCase.java
│   │   │   ├── RefreshTokenUseCase.java
│   │   │   ├── GetTokenStatusUseCase.java
│   │   │   └── CleanupExpiredTokensUseCase.java
│   │   └── out/                     # Outbound Ports
│   │       ├── KisTokenRepositoryPort.java
│   │       ├── KisApiPort.java
│   │       └── NotificationPort.java
│   └── service/
│       └── KisTokenApplicationService.java  # Use Case 구현체
│
└── infrastructure/                   # 🔵 Infrastructure Layer
    ├── adapter/
    │   ├── in/                      # Inbound Adapters
    │   │   ├── web/
    │   │   │   ├── KisTokenController.java
    │   │   │   ├── KisTokenManagementController.java
    │   │   │   └── dto/             # Web DTO
    │   │   │       ├── TokenInfoDto.java
    │   │   │       └── TokenStatusResponseDto.java
    │   │   └── scheduler/
    │   │       └── KisTokenScheduler.java
    │   └── out/                     # Outbound Adapters
    │       ├── persistence/
    │       │   ├── KisTokenEntity.java
    │       │   ├── JpaKisTokenRepository.java
    │       │   └── KisTokenRepositoryAdapter.java
    │       ├── kis/
    │       │   ├── KisApiAdapter.java
    │       │   └── dto/             # KIS API DTO
    │       │       ├── AccessTokenResponse.java
    │       │       ├── WebSocketKeyResponse.java
    │       │       ├── KisTokenRequest.java
    │       │       └── KisWebSocketRequest.java
    │       └── notification/
    │           └── LoggingNotificationAdapter.java
    └── config/
        ├── KisConfig.java
        ├── KisApiConfig.java
        ├── KisConfigProperties.java
        └── BeanConfiguration.java
```

## 🔄 상세 리팩토링 계획

### Phase 1: 포트 정의 (Interfaces)

#### 1.1 Inbound Ports (Use Cases)
```java
// application/port/in/GetTokenUseCase.java
public interface GetTokenUseCase {
    String getValidAccessToken(KisEnvironment environment);
    String getValidWebSocketKey(KisEnvironment environment);
}

// application/port/in/RefreshTokenUseCase.java
public interface RefreshTokenUseCase {
    void refreshAccessToken(KisEnvironment environment);
    void refreshWebSocketKey(KisEnvironment environment);
}

// application/port/in/GetTokenStatusUseCase.java
public interface GetTokenStatusUseCase {
    Map<String, TokenInfo> getAllTokenStatus();
    List<KisToken> getTokensByEnvironment(KisEnvironment environment);
}

// application/port/in/CleanupExpiredTokensUseCase.java
public interface CleanupExpiredTokensUseCase {
    void cleanupExpiredTokens();
}
```

#### 1.2 Outbound Ports
```java
// application/port/out/KisTokenRepositoryPort.java
public interface KisTokenRepositoryPort {
    Optional<KisToken> findById(KisTokenId id);
    KisToken save(KisToken kisToken);
    List<KisToken> findAll();
    List<KisToken> findByEnvironment(KisEnvironment environment);
    void deleteExpiredTokens();
}

// application/port/out/KisApiPort.java
public interface KisApiPort {
    AccessTokenResponse issueAccessToken(KisEnvironment environment);
    WebSocketKeyResponse issueWebSocketKey(KisEnvironment environment);
}

// application/port/out/NotificationPort.java
public interface NotificationPort {
    void notifyTokenRefreshed(KisEnvironment environment, TokenType tokenType);
    void notifyTokenExpired(KisEnvironment environment, TokenType tokenType);
}
```

### Phase 2: Application Service 구현

```java
// application/service/KisTokenApplicationService.java
@Service
@Transactional
public class KisTokenApplicationService implements
    GetTokenUseCase, RefreshTokenUseCase, GetTokenStatusUseCase, CleanupExpiredTokensUseCase {

    private final KisTokenRepositoryPort repositoryPort;
    private final KisApiPort kisApiPort;
    private final NotificationPort notificationPort;

    // Use Case 구현...
}
```

### Phase 3: Infrastructure Adapters 구현

#### 3.1 Outbound Adapters

```java
// infrastructure/adapter/out/kis/KisApiAdapter.java
@Component
public class KisApiAdapter implements KisApiPort {
    private final RestClient restClient;
    private final KisConfig config;
    // KIS API 호출 로직...
}

// infrastructure/adapter/out/persistence/KisTokenRepositoryAdapter.java
@Repository
public class KisTokenRepositoryAdapter implements KisTokenRepositoryPort {
    private final JpaKisTokenRepository jpaRepository;
    // JPA 연동 로직...
}
```

#### 3.2 Inbound Adapters

```java
// infrastructure/adapter/in/web/KisTokenController.java
@RestController
public class KisTokenController {
    private final GetTokenUseCase getTokenUseCase;
    private final GetTokenStatusUseCase getTokenStatusUseCase;
    // Web API 엔드포인트...
}

// infrastructure/adapter/in/scheduler/KisTokenScheduler.java
@Component
public class KisTokenScheduler {
    private final RefreshTokenUseCase refreshTokenUseCase;
    private final CleanupExpiredTokensUseCase cleanupUseCase;
    // 스케줄링 로직...
}
```

### Phase 4: 의존성 주입 설정

```java
// infrastructure/config/BeanConfiguration.java
@Configuration
public class BeanConfiguration {

    @Bean
    public KisApiPort kisApiPort(RestClient restClient, KisConfig config) {
        return new KisApiAdapter(restClient, config);
    }

    @Bean
    public KisTokenRepositoryPort kisTokenRepositoryPort(JpaKisTokenRepository jpaRepository) {
        return new KisTokenRepositoryAdapter(jpaRepository);
    }

    // 기타 Bean 설정...
}
```

## 📋 마이그레이션 체크리스트

### ✅ Phase 1: 포트 정의
- [ ] Inbound Ports (Use Cases) 인터페이스 생성
- [ ] Outbound Ports 인터페이스 생성
- [ ] 패키지 구조 생성

### ✅ Phase 2: Application Layer
- [ ] KisTokenApplicationService 구현
- [ ] Use Cases 구현
- [ ] 단위 테스트 작성

### ✅ Phase 3: Infrastructure Adapters
- [ ] KisApiAdapter 구현 (기존 KisTokenService 이전)
- [ ] KisTokenRepositoryAdapter 구현
- [ ] Web Controllers 포트 연결
- [ ] Scheduler 포트 연결

### ✅ Phase 4: 정리 및 테스트
- [ ] 기존 클래스 제거
- [ ] 의존성 주입 설정
- [ ] 통합 테스트 작성
- [ ] 문서화 업데이트

## 🧪 테스트 전략

### 단위 테스트
```java
// Application Service 테스트 (포트 Mock 사용)
@ExtendWith(MockitoExtension.class)
class KisTokenApplicationServiceTest {
    @Mock private KisTokenRepositoryPort repositoryPort;
    @Mock private KisApiPort kisApiPort;
    @InjectMocks private KisTokenApplicationService service;

    @Test
    void 유효한_액세스_토큰_반환() {
        // given
        given(repositoryPort.findById(any())).willReturn(Optional.of(validToken));

        // when & then
        assertThat(service.getValidAccessToken(PROD)).isEqualTo("valid-token");
    }
}
```

### 통합 테스트
```java
// Adapter 테스트 (실제 외부 연동)
@SpringBootTest
@TestPropertySource(properties = {
    "kis.prod=https://openapi-test.koreainvestment.com:9443",
    "kis.my-app=test-app-key"
})
class KisApiAdapterIntegrationTest {

    @Autowired private KisApiPort kisApiPort;

    @Test
    void KIS_API_토큰_발급_통합테스트() {
        // 실제 KIS API 호출 테스트
    }
}
```

## 📈 기대 효과

### 1. 유지보수성 향상
- 각 레이어의 책임이 명확히 분리
- 비즈니스 로직이 기술적 세부사항과 분리

### 2. 테스트 용이성
- 포트를 통한 Mock 테스트 가능
- 각 레이어별 독립적 테스트

### 3. 확장성
- 새로운 외부 API 연동 시 어댑터만 추가
- 새로운 UI (CLI, GraphQL 등) 추가 시 inbound adapter만 추가

### 4. 도메인 중심 설계
- 비즈니스 규칙이 중심이 되는 설계
- 기술적 제약사항으로부터 도메인 로직 보호

## 🚧 리스크 및 완화 방안

### 리스크
1. **복잡성 증가**: 레이어 분리로 인한 초기 복잡도 증가
2. **러닝 커브**: 팀원들의 DDD/헥사고날 이해 필요
3. **마이그레이션 위험**: 기존 기능 동작 보장

### 완화 방안
1. **점진적 마이그레이션**: Phase별 단계적 진행
2. **테스트 우선**: 기존 기능 동작 보장을 위한 테스트 작성
3. **문서화**: 아키텍처 결정사항 문서화
4. **코드 리뷰**: 아키텍처 준수 여부 지속적 검증

---

**작성일**: 2025-09-24
**작성자**: Claude Code
**버전**: 1.0
**상태**: 계획 단계