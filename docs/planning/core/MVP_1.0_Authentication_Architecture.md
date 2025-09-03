# MVP 1.0 인증 아키텍처 통합 설계

## 📖 개요

사용자 JWT 인증과 KIS API 토큰을 통합한 하이브리드 인증 시스템 아키텍처

**핵심 플로우**: 사용자 로그인 → JWT 인증 → KIS 계정 확인 → KIS 토큰 발급/저장 → 클라이언트 토큰 저장 → 직접 KIS Adapter 호출

## 🏗️ 하이브리드 아키텍처

### 새로운 접근법 (Performance-First)

```
실시간 데이터 (빠른 응답 필요):
Next.js Client → (직접) → KIS Adapter → KIS API

토큰 관리 & 설정 데이터:
Next.js Client → Spring Boot → (필요시) KIS Adapter
```

**Before (서버 중심)**:
- 모든 요청이 Spring Boot 경유 → 네트워크 홉 증가
- 서버 부하 집중 → 성능 저하

**After (하이브리드)**:
- 실시간 데이터는 직접 호출 → 성능 향상
- 토큰 관리는 서버 담당 → 보안 유지
- 부하 분산 효과 → 확장성 향상

## 🔐 Frontend 인증 시스템

### AuthContext 확장 설계

```typescript
interface AuthContextType {
  // 기존 JWT 관련
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  
  // KIS 토큰 통합
  kisTokens: {
    live?: KISTokenInfo;
    sandbox?: KISTokenInfo;
  };
  hasKISAccount: boolean;
  setupKISAccount: (appKey: string, appSecret: string, environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  refreshKISToken: (environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  getActiveKISToken: () => string | null;
}

interface KISTokenInfo {
  token: string;
  environment: 'LIVE' | 'SANDBOX';
  expiresAt: string;
  issuedAt: string;
  appKey: string;
  appSecret: string; // 암호화 저장
}
```

### 완전한 로그인 플로우

**Step 1: 사용자 로그인 (기존 유지)**
```
사용자 입력 (email, password) 
→ POST /api/v1/auth/login 
→ JWT 토큰 발급 
→ localStorage 저장
```

**Step 2: KIS 토큰 통합 처리**
```typescript
const login = async (email: string, password: string) => {
  try {
    // 1. JWT 로그인
    const response = await apiClient.post('/api/v1/auth/login', { email, password }, false);
    const data = response.data;
    
    if (data.accessToken) {
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);
      localStorage.setItem('user', JSON.stringify(data.user));
      setUser(data.user);
      
      // 2. KIS 토큰 확인 및 발급
      await checkAndIssueKISTokens();
    }
  } catch (error) {
    // 에러 처리
  }
};
```

**Step 3: KIS 토큰 자동 처리**
```typescript
const checkAndIssueKISTokens = async () => {
  try {
    // KIS 계정 정보 확인
    const kisAccountResponse = await apiClient.get('/api/v1/kis-accounts/me', true);
    
    if (kisAccountResponse.data) {
      const kisAccount = kisAccountResponse.data;
      
      // 각 환경별 토큰 처리
      for (const env of ['LIVE', 'SANDBOX']) {
        if (kisAccount[env.toLowerCase()]) {
          const tokenInfo = await checkAndRefreshKISToken(env, kisAccount[env.toLowerCase()]);
          if (tokenInfo) {
            setKISToken(env, tokenInfo);
          }
        }
      }
      setHasKISAccount(true);
    } else {
      setHasKISAccount(false);
    }
  } catch (error) {
    console.error('KIS token check failed:', error);
    setHasKISAccount(false);
  }
};
```

### 토큰 검증 및 갱신

```typescript
const checkAndRefreshKISToken = async (environment: 'LIVE' | 'SANDBOX', accountInfo: any) => {
  try {
    // 기존 토큰 확인
    const existingToken = localStorage.getItem(`kisToken_${environment}`);
    
    if (existingToken) {
      const tokenData = JSON.parse(existingToken);
      const now = new Date();
      const expiryTime = new Date(tokenData.expiresAt);
      
      // 토큰이 유효하면 재사용
      if (now < expiryTime) {
        return tokenData;
      }
    }
    
    // 새 토큰 발급
    const tokenResponse = await apiClient.post('/api/v1/kis-accounts/me/token', {
      environment: environment
    }, true);
    
    if (tokenResponse.data.success) {
      const newTokenInfo = {
        token: tokenResponse.data.token,
        environment: environment,
        expiresAt: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(), // 6시간
        issuedAt: new Date().toISOString(),
        appKey: accountInfo.appKey,
        appSecret: accountInfo.appSecret
      };
      
      localStorage.setItem(`kisToken_${environment}`, JSON.stringify(newTokenInfo));
      return newTokenInfo;
    }
  } catch (error) {
    console.error(`Failed to refresh KIS token for ${environment}:`, error);
    return null;
  }
};
```

## 🖥️ Backend 인증 API

### KIS 계정 정보 조회
```
GET /api/v1/kis-accounts/me
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "live": {
    "appKey": "encrypted_app_key",
    "appSecret": "encrypted_app_secret",
    "accountNumber": "12345678-01"
  },
  "sandbox": {
    "appKey": "encrypted_app_key", 
    "appSecret": "encrypted_app_secret",
    "accountNumber": "12345678-01"
  }
}
```

### KIS 토큰 발급
```
POST /api/v1/kis-accounts/me/token
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

{
  "environment": "LIVE" // or "SANDBOX"
}

Response:
{
  "success": true,
  "token": "kis_access_token_here",
  "expiresIn": 21600, // 6시간 (초)
  "environment": "LIVE"
}
```

## ⚡ 클라이언트 직접 API 호출

### KIS Adapter 직접 호출 패턴
```typescript
const fetchKISData = async (endpoint: string, params: any) => {
  const activeToken = getActiveKISToken();
  
  if (!activeToken) {
    throw new Error('KIS token not available');
  }
  
  const response = await fetch(`http://localhost:8000${endpoint}`, {
    method: 'GET',
    headers: {
      'X-KIS-Token': activeToken,
      'Content-Type': 'application/json'
    },
    ...params
  });
  
  if (response.status === 401) {
    // 토큰 만료 시 자동 갱신
    await refreshKISToken(getCurrentEnvironment());
    // 재시도 로직
  }
  
  return response.json();
};
```

### 사용 예시
```typescript
// 차트 데이터 조회
const chartData = await fetchKISData('/domestic/chart/daily/005930', {
  method: 'GET'
});

// 현재가 조회  
const currentPrice = await fetchKISData('/domestic/price/005930', {
  method: 'GET'
});
```

## 🛡️ 보안 및 에러 처리

### 토큰 만료 자동 처리
```typescript
const handleKISAPIError = async (error: any, environment: string) => {
  if (error.status === 401) {
    try {
      await refreshKISToken(environment);
      return true; // 재시도 가능
    } catch (refreshError) {
      router.push('/login?reason=kis_token_expired');
      return false;
    }
  }
  throw error;
};
```

### KIS 계정 연결 안내
```typescript
const KISAccountSetup = () => {
  const { hasKISAccount, setupKISAccount } = useAuth();
  
  if (!hasKISAccount) {
    return (
      <div className="kis-setup-notice">
        <h3>KIS 계정 연결이 필요합니다</h3>
        <p>실시간 차트 데이터 조회를 위해 한국투자증권 API 계정을 연결해주세요.</p>
        <button onClick={() => router.push('/settings/kis-account')}>
          KIS 계정 연결하기
        </button>
      </div>
    );
  }
  return null;
};
```

### 환경 전환 UI
```typescript
const MarketEnvironmentToggle = () => {
  const { currentEnvironment, switchEnvironment } = useKIS();
  
  return (
    <div className="environment-toggle">
      <button 
        className={currentEnvironment === 'SANDBOX' ? 'active' : ''}
        onClick={() => switchEnvironment('SANDBOX')}
      >
        모의투자
      </button>
      <button 
        className={currentEnvironment === 'LIVE' ? 'active' : ''}
        onClick={() => switchEnvironment('LIVE')}
      >
        실전투자
      </button>
    </div>
  );
};
```

## 🚀 주요 장점

### 1. 성능 향상
- **네트워크 홉 감소**: Next.js → KIS Adapter (1홉)
- **서버 부하 감소**: Spring Boot가 모든 요청을 프록시하지 않음  
- **실시간성 향상**: 중간 서버 없이 직접 데이터 조회

### 2. 확장성 및 유연성
- **수평 확장**: KIS Adapter를 여러 인스턴스로 확장 가능
- **부하 분산**: 실시간 데이터와 비즈니스 로직 완전 분리
- **캐싱 효율**: 클라이언트별 독립적인 브라우저 캐싱

### 3. 사용자 경험
- **빠른 응답**: 실시간 차트 데이터 즉시 로딩
- **투명한 토큰 관리**: 사용자가 토큰 상태 직접 확인
- **끊김 없는 서비스**: 토큰 갱신이 백그라운드에서 자동 처리

### 4. 보안 및 안정성
- **이중 토큰 인증**: JWT(사용자 인증) + KIS Token(API 인증)
- **클라이언트 암호화**: 브라우저 저장 토큰 AES 암호화
- **서버 측 암호화**: DB 저장 계정 정보 및 토큰 암호화
- **자동 토큰 갱신**: 만료 전 사전 갱신으로 서비스 중단 방지

## 🧪 테스트 시나리오

1. **신규 사용자 로그인**: JWT → KIS 계정 없음 → 계정 연결 안내
2. **기존 사용자 로그인**: JWT → KIS 토큰 유효 → 바로 사용 가능
3. **토큰 만료**: API 호출 시 401 → 자동 갱신 → 재시도
4. **환경 전환**: SANDBOX ↔ LIVE 토글 → 해당 환경 토큰 사용
5. **KIS API 에러**: Rate limit, 서버 에러 → 적절한 에러 메시지

이 하이브리드 아키텍처로 **빠른 실시간 데이터 조회**와 **안전한 토큰 관리**를 동시에 만족하는 최적의 인증 시스템을 구축할 수 있습니다.