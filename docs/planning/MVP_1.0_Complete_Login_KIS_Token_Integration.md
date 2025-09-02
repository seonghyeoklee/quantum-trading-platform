# MVP 1.0 Complete Login-KIS Token Integration Flow

## 플로우 개요

사용자 로그인 → JWT 인증 → KIS 계정 확인 → KIS 토큰 발급/저장 → 클라이언트 토큰 저장 → 직접 KIS Adapter 호출

## 기존 AuthContext 확장 설계

### 현재 AuthContext 구조 분석
- JWT 기반 인증 (accessToken, refreshToken)
- localStorage에 토큰 저장
- 자동 토큰 갱신 (tryRefreshToken)
- 사용자 정보 캐싱

### KIS 토큰 통합 확장

```typescript
interface KISTokenInfo {
  token: string;
  environment: 'LIVE' | 'SANDBOX';
  expiresAt: string;
  issuedAt: string;
  appKey: string;
  appSecret: string; // 암호화 저장
}

interface AuthContextType {
  // 기존 JWT 관련
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  
  // 새로운 KIS 토큰 관련
  kisTokens: {
    live?: KISTokenInfo;
    sandbox?: KISTokenInfo;
  };
  hasKISAccount: boolean;
  setupKISAccount: (appKey: string, appSecret: string, environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  refreshKISToken: (environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  getActiveKISToken: () => string | null;
}
```

## 완전한 로그인 플로우

### Step 1: 사용자 로그인 (기존 유지)
```
사용자 입력 (email, password) 
→ POST /api/v1/auth/login 
→ JWT 토큰 발급 
→ localStorage 저장
```

### Step 2: KIS 계정 확인 및 토큰 처리
```typescript
// login 함수 내부 확장
const login = async (email: string, password: string) => {
  try {
    // 1. JWT 로그인 (기존)
    const response = await apiClient.post('/api/v1/auth/login', { email, password }, false);
    const data = response.data;
    
    if (data.accessToken) {
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);
      localStorage.setItem('user', JSON.stringify(data.user));
      setUser(data.user);
      
      // 2. KIS 토큰 확인 및 발급 (신규)
      await checkAndIssueKISTokens();
      
      setIsLoading(false);
      const returnUrl = localStorage.getItem('returnUrl') || '/';
      localStorage.removeItem('returnUrl');
      router.push(returnUrl);
    }
  } catch (error) {
    // 에러 처리
  }
};
```

### Step 3: KIS 토큰 확인 및 발급 로직
```typescript
const checkAndIssueKISTokens = async () => {
  try {
    // 3-1. 사용자 KIS 계정 정보 확인
    const kisAccountResponse = await apiClient.get('/api/v1/kis-accounts/me', true);
    
    if (kisAccountResponse.data) {
      const kisAccount = kisAccountResponse.data;
      
      // 3-2. 각 환경별로 토큰 확인 및 발급
      for (const env of ['LIVE', 'SANDBOX']) {
        if (kisAccount[env.toLowerCase()]) {
          const tokenInfo = await checkAndRefreshKISToken(env, kisAccount[env.toLowerCase()]);
          if (tokenInfo) {
            // 3-3. 클라이언트에 토큰 저장
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

### Step 4: KIS 토큰 검증 및 발급
```typescript
const checkAndRefreshKISToken = async (environment: 'LIVE' | 'SANDBOX', accountInfo: any) => {
  try {
    // 4-1. 기존 토큰 확인
    const existingToken = localStorage.getItem(`kisToken_${environment}`);
    
    if (existingToken) {
      const tokenData = JSON.parse(existingToken);
      const now = new Date();
      const expiryTime = new Date(tokenData.expiresAt);
      
      // 4-2. 토큰이 유효하면 그대로 사용
      if (now < expiryTime) {
        return tokenData;
      }
    }
    
    // 4-3. 토큰이 없거나 만료되면 새로 발급
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
        appSecret: accountInfo.appSecret // 이미 서버에서 암호화됨
      };
      
      // 4-4. localStorage에 저장
      localStorage.setItem(`kisToken_${environment}`, JSON.stringify(newTokenInfo));
      
      return newTokenInfo;
    }
  } catch (error) {
    console.error(`Failed to refresh KIS token for ${environment}:`, error);
    return null;
  }
};
```

## Spring Boot Backend 지원 API

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

## Next.js 클라이언트 토큰 사용

### KIS Adapter 직접 호출
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

## KIS Token Context 생성

```typescript
interface KISContextType {
  currentEnvironment: 'LIVE' | 'SANDBOX';
  switchEnvironment: (env: 'LIVE' | 'SANDBOX') => void;
  callKISAPI: (endpoint: string, params?: any) => Promise<any>;
  isTokenValid: (env: 'LIVE' | 'SANDBOX') => boolean;
}

export function KISProvider({ children }: { children: ReactNode }) {
  const { kisTokens, refreshKISToken } = useAuth();
  const [currentEnvironment, setCurrentEnvironment] = useState<'LIVE' | 'SANDBOX'>('SANDBOX');
  
  const callKISAPI = async (endpoint: string, params?: any) => {
    const token = kisTokens[currentEnvironment.toLowerCase()]?.token;
    
    if (!token || !isTokenValid(currentEnvironment)) {
      await refreshKISToken(currentEnvironment);
    }
    
    return fetchKISData(endpoint, params);
  };
  
  return (
    <KISContext.Provider value={{ currentEnvironment, switchEnvironment: setCurrentEnvironment, callKISAPI, isTokenValid }}>
      {children}
    </KISContext.Provider>
  );
}
```

## 에러 처리 및 복구

### 토큰 만료 처리
```typescript
const handleKISAPIError = async (error: any, environment: string) => {
  if (error.status === 401) {
    try {
      await refreshKISToken(environment);
      // 원래 요청 재시도
      return true;
    } catch (refreshError) {
      // 토큰 갱신 실패 시 로그인 페이지로
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

## 환경 전환 UI

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

## 보안 고려사항

### 클라이언트 토큰 보안
- KIS 토큰만 클라이언트 저장 (앱키/시크릿은 서버에만)
- localStorage 대신 sessionStorage 고려
- 토큰 암호화 저장 옵션

### API 보안
- CORS 설정으로 허용된 도메인만 접근
- Rate Limiting 클라이언트 적용
- 토큰 탈취 시 서버 측에서 무효화 가능

## 테스트 시나리오

1. **신규 사용자 로그인**: JWT → KIS 계정 없음 → 계정 연결 안내
2. **기존 사용자 로그인**: JWT → KIS 토큰 유효 → 바로 사용 가능
3. **토큰 만료**: API 호출 시 401 → 자동 갱신 → 재시도
4. **환경 전환**: SANDBOX ↔ LIVE 토글 → 해당 환경 토큰 사용
5. **KIS API 에러**: Rate limit, 서버 에러 → 적절한 에러 메시지

이 설계로 사용자는 로그인 한 번으로 KIS API를 직접 호출할 수 있고, 토큰 관리는 자동으로 처리됩니다.