# KIS 토큰 관리 기능 완전 제거 계획서

## 📖 제거 개요

**제거 목적**: KIS 토큰 관리의 복잡성 제거 및 아키텍처 단순화
**제거 범위**: 백엔드/프론트엔드 KIS 토큰 관리 기능 전체
**대안 방안**: KIS Adapter 자체 토큰 관리 방식으로 회귀

## 🎯 제거 배경

### 현재 문제점
1. **복잡한 토큰 관리**: 클라이언트/서버 이중 토큰 관리
2. **인증 복잡성**: JWT + KIS Token 하이브리드 시스템
3. **개발 부담**: 토큰 갱신/저장/암호화 로직 복잡
4. **유지보수 비용**: 토큰 만료 처리 및 에러 복구 로직

### 목표 아키텍처
```
Before (복잡한 하이브리드):
Frontend → JWT 인증 → Backend 토큰 발급 → KIS Adapter 호출

After (단순화):
Frontend → 직접 KIS Adapter 호출 (Adapter 자체 토큰 관리)
```

## 🗑️ 제거 대상 목록

### Backend (Spring Boot) 제거 대상

#### 1. 엔티티 및 도메인
```kotlin
// 완전 제거 대상
- KisAccount.kt
- KisToken.kt  
- KisAccountRepository.kt
- KisTokenRepository.kt
- TokenStatus.kt (enum)
- KisEnvironment.kt (enum)
```

#### 2. REST API 컨트롤러
```kotlin
// 완전 제거 대상
- KisTokenController.kt
  - POST /api/kis/account/validate
  - POST /api/kis/token
  - POST /api/kis/token/refresh
  - GET /api/kis-accounts/me
```

#### 3. 서비스 및 비즈니스 로직
```kotlin
// 완전 제거 대상
- KisTokenService.kt
- KisApiClient.kt
- EncryptionService.kt (KIS 관련 부분)
- TokenRefreshScheduler.kt
```

#### 4. 설정 및 구성
```kotlin
// 제거 대상
- KisTokenConfig.kt
- 토큰 관리 관련 application.yml 설정
- KIS 토큰 DB 스키마 및 마이그레이션
```

### Frontend (Next.js) 제거 대상

#### 1. Context 및 상태 관리
```typescript
// 완전 제거 대상
- KisTokenContext.tsx
- useKisTokenStore.ts (Zustand)
- KISTokenInfo interface
- kisTokens 상태 관리 로직
```

#### 2. 인증 시스템 수정
```typescript
// AuthContext.tsx에서 제거할 부분
interface AuthContextType {
  // 제거 대상
  kisTokens: { live?: KISTokenInfo; sandbox?: KISTokenInfo; }
  hasKISAccount: boolean
  setupKISAccount: (...) => Promise<void>
  refreshKISToken: (...) => Promise<void>
  getActiveKISToken: () => string | null
}

// 제거할 함수들
- checkAndIssueKISTokens()
- checkAndRefreshKISToken()  
- setKISToken()
- refreshKISToken()
```

#### 3. UI 컴포넌트
```typescript
// 완전 제거 대상
- KisAccountSetupForm.tsx
- KisConnectionStatus.tsx
- KISAccountSetup.tsx
- MarketEnvironmentToggle.tsx (KIS 토큰 관련 부분)
```

#### 4. API 클라이언트
```typescript
// 제거 대상
- DirectKisClient.ts
- KIS 토큰 관련 axios interceptor
- localStorage KIS 토큰 저장/암호화 로직
- TokenStorage.ts 클래스
```

#### 5. 설정 및 환경변수
```typescript
// 제거 대상
- NEXT_PUBLIC_ENCRYPTION_KEY
- NEXT_PUBLIC_KIS_ADAPTER_URL (선택사항)
- KIS 토큰 관련 localStorage 키들
```

### KIS Adapter (Python) 수정 대상

#### 제거할 부분
```python
# 제거 대상
- ClientTokenMiddleware 클래스
- X-KIS-Token 헤더 검증 로직
- JWT 토큰 검증 로직
- /token/refresh 엔드포인트
```

#### 유지할 부분
```python
# 유지 대상 (기존 방식)
- kis_devlp.yaml 기반 토큰 관리
- 내부 토큰 자동 갱신 로직
- 기존 API 엔드포인트들
```

## 🔄 제거 실행 계획

### Phase 1: Backend 제거 (1일)

#### 1단계: 데이터베이스 정리
```sql
-- KIS 관련 테이블 제거
DROP TABLE IF EXISTS kis_tokens;
DROP TABLE IF EXISTS kis_accounts;

-- 관련 인덱스 및 제약조건 제거
-- 마이그레이션 스크립트 생성
```

#### 2단계: 코드 제거
```kotlin
// 1. 컨트롤러 제거
rm src/main/kotlin/.../KisTokenController.kt

// 2. 서비스 제거  
rm src/main/kotlin/.../KisTokenService.kt
rm src/main/kotlin/.../KisApiClient.kt

// 3. 엔티티 제거
rm src/main/kotlin/.../KisAccount.kt
rm src/main/kotlin/.../KisToken.kt

// 4. 레포지토리 제거
rm src/main/kotlin/.../KisAccountRepository.kt  
rm src/main/kotlin/.../KisTokenRepository.kt
```

#### 3단계: 설정 정리
```yaml
# application.yml에서 제거
kis:
  token:
    expires-hours: 6
    encryption-key: ${KIS_ENCRYPTION_KEY:}
  scheduler:
    token-refresh-cron: "0 0 */5 * * *"
```

### Phase 2: Frontend 제거 (1일)

#### 1단계: Context 및 상태 제거
```bash
# Context 제거
rm src/contexts/KisTokenContext.tsx
rm src/stores/useKisTokenStore.ts

# AuthContext 수정 - KIS 토큰 관련 제거
# - AuthContextType interface 수정
# - KIS 토큰 관련 함수들 제거
```

#### 2단계: 컴포넌트 제거
```bash
# UI 컴포넌트 제거
rm src/components/kis/KisAccountSetupForm.tsx
rm src/components/kis/KisConnectionStatus.tsx  
rm src/components/auth/KISAccountSetup.tsx

# API 클라이언트 제거
rm src/services/DirectKisClient.ts
rm src/utils/TokenStorage.ts
```

#### 3단계: 환경 설정 정리
```bash
# .env.local에서 제거
NEXT_PUBLIC_ENCRYPTION_KEY=
NEXT_PUBLIC_KIS_ADAPTER_URL=

# localStorage 정리 스크립트 추가 (한 번만 실행)
localStorage.removeItem('kis_token_LIVE')
localStorage.removeItem('kis_token_SANDBOX')
```

### Phase 3: KIS Adapter 정리 (0.5일)

#### 수정 사항
```python
# main.py에서 제거
- ClientTokenMiddleware 클래스
- app.add_middleware(ClientTokenMiddleware)

# CORS 설정 단순화 (기존 Spring Boot만)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Next.js 제거
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# 토큰 갱신 엔드포인트 제거
@app.post("/token/refresh") # 이 함수 전체 제거
```

## 🎯 제거 후 새로운 아키텍처

### 단순화된 데이터 플로우
```
사용자 요청 → Next.js Frontend → Spring Boot API → KIS Adapter → KIS API
                                    ↑
                                KIS Adapter가 
                              자체 토큰 관리 수행
```

### 장점
1. **개발 복잡성 50% 감소**: 이중 토큰 관리 제거
2. **유지보수 비용 절약**: 토큰 갱신 로직 제거
3. **에러 포인트 감소**: 토큰 만료 처리 로직 단순화
4. **성능 향상**: 불필요한 토큰 검증 제거

### 주의사항
1. **KIS Adapter 의존성**: KIS Adapter의 안정성이 더 중요해짐
2. **직접 호출 불가**: Frontend에서 KIS Adapter 직접 호출 불가
3. **환경 전환**: SANDBOX/LIVE 전환이 서버 측에서만 가능

## ✅ 제거 검증 체크리스트

### Backend 검증
- [ ] KIS 관련 테이블 모두 제거됨
- [ ] KIS 관련 엔티티/레포지토리 제거됨
- [ ] KIS 토큰 API 엔드포인트 제거됨
- [ ] 애플리케이션 정상 빌드 및 실행
- [ ] 기존 기능 (로그인/차트) 정상 동작

### Frontend 검증  
- [ ] KIS 토큰 관련 Context/Store 제거됨
- [ ] KIS 관련 UI 컴포넌트 제거됨
- [ ] localStorage KIS 토큰 정리됨
- [ ] 애플리케이션 정상 빌드 및 실행
- [ ] 로그인 후 차트 조회 정상 동작

### KIS Adapter 검증
- [ ] 클라이언트 토큰 미들웨어 제거됨
- [ ] CORS 설정이 Spring Boot만 허용하도록 수정됨
- [ ] 기존 API 엔드포인트 정상 동작
- [ ] 자체 토큰 관리 (kis_devlp.yaml) 정상 동작

## 📝 제거 후 업데이트 필요 문서

1. **인증 아키텍처 문서 수정**
   - `MVP_1.0_Authentication_Architecture.md` 단순화 버전으로 업데이트

2. **개발자 가이드 업데이트**
   - `TRADING_MODE_GUIDE.md`에서 토큰 관리 부분 제거

3. **README 업데이트**
   - 메인 `CLAUDE.md` 파일에서 KIS 토큰 관리 부분 제거

## 🚀 제거 후 기대 효과

### 개발 생산성 향상
- **코드 복잡성 50% 감소**: 토큰 관리 로직 제거
- **개발 속도 30% 향상**: 인증 관련 버그 및 이슈 감소
- **신규 개발자 온보딩 시간 단축**: 단순한 아키텍처

### 시스템 안정성 향상
- **장애 포인트 감소**: 토큰 만료/갱신 오류 제거
- **의존성 단순화**: 클라이언트-서버-어댑터 선형 구조
- **에러 추적 용이**: 단순한 데이터 플로우

### 유지보수 비용 절감
- **토큰 관리 로직 제거**: 복잡한 갱신/암호화 로직 불필요
- **모니터링 대상 감소**: 토큰 상태 모니터링 불필요
- **보안 취약점 감소**: 클라이언트 토큰 저장 리스크 제거

---

**기획자 의견**: 이 제거 계획을 통해 시스템을 대폭 단순화하고, 개발팀의 생산성을 크게 향상시킬 수 있습니다. 단, KIS Adapter의 안정성과 자체 토큰 관리 기능에 대한 의존도가 높아지므로, Adapter의 모니터링과 장애 대응 체계를 강화해야 합니다.