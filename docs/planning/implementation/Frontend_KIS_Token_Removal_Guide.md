# Frontend KIS 토큰 관리 제거 실행 가이드

## 🎯 프론트엔드 제거 개요

**대상**: Next.js React 프론트엔드의 모든 KIS 토큰 관리 기능
**소요시간**: 약 1일  
**난이도**: 중급 (Context/State 관리 및 UI 컴포넌트 제거)

## 📋 제거 체크리스트

### Phase 1: Context 및 상태 관리 제거 ✅

#### 1. KIS 전용 Context 제거
```bash
# KIS 토큰 전용 Context 파일 제거
rm src/contexts/KisTokenContext.tsx
rm src/contexts/KISProvider.tsx

# Zustand 스토어 제거 (사용하는 경우)
rm src/stores/useKisTokenStore.ts
rm src/stores/kisTokenStore.ts
```

#### 2. AuthContext에서 KIS 관련 부분 제거
```typescript
// src/contexts/AuthContext.tsx 수정
interface AuthContextType {
  // 기존 JWT 관련 (유지)
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  
  // KIS 토큰 관련 (모두 제거)
  // kisTokens: { live?: KISTokenInfo; sandbox?: KISTokenInfo; };
  // hasKISAccount: boolean;
  // setupKISAccount: (appKey: string, appSecret: string, environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  // refreshKISToken: (environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  // getActiveKISToken: () => string | null;
  // currentEnvironment: 'LIVE' | 'SANDBOX';
  // switchEnvironment: (env: 'LIVE' | 'SANDBOX') => void;
}
```

#### 3. AuthProvider에서 KIS 관련 로직 제거
```typescript
// src/contexts/AuthContext.tsx - AuthProvider 수정
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // KIS 관련 state 모두 제거
  // const [kisTokens, setKisTokens] = useState<{live?: KISTokenInfo; sandbox?: KISTokenInfo;}>({});
  // const [hasKISAccount, setHasKISAccount] = useState(false);
  // const [currentEnvironment, setCurrentEnvironment] = useState<'LIVE' | 'SANDBOX'>('SANDBOX');

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const response = await apiClient.post('/api/auth/login', { email, password });
      const data = response.data;
      
      if (data.accessToken) {
        localStorage.setItem('accessToken', data.accessToken);
        localStorage.setItem('refreshToken', data.refreshToken);
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
        
        // KIS 토큰 관련 로직 제거
        // await checkAndIssueKISTokens();
        
        setIsLoading(false);
        const returnUrl = localStorage.getItem('returnUrl') || '/';
        localStorage.removeItem('returnUrl');
        router.push(returnUrl);
      }
    } catch (error) {
      console.error('Login failed:', error);
      setIsLoading(false);
    }
  };

  // KIS 관련 함수들 모두 제거
  // const checkAndIssueKISTokens = async () => { ... }
  // const checkAndRefreshKISToken = async () => { ... }
  // const refreshKISToken = async () => { ... }
  // const setupKISAccount = async () => { ... }
  // const getActiveKISToken = () => { ... }
  // const switchEnvironment = (env) => { ... }

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      // KIS 관련 값들 모두 제거
    }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Phase 2: UI 컴포넌트 제거 ✅

#### 1. KIS 관련 UI 컴포넌트 파일 제거
```bash
# KIS 계정 관련 컴포넌트
rm src/components/kis/KisAccountSetupForm.tsx
rm src/components/kis/KisConnectionStatus.tsx
rm src/components/kis/KISAccountSetup.tsx
rm src/components/kis/KisTokenStatus.tsx

# 환경 전환 관련 컴포넌트
rm src/components/kis/MarketEnvironmentToggle.tsx
rm src/components/kis/TradingEnvironmentSelector.tsx

# 디렉터리가 비어있다면 제거
rmdir src/components/kis/
```

#### 2. 설정 페이지에서 KIS 관련 부분 제거
```typescript
// src/app/settings/page.tsx 수정
export default function SettingsPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">설정</h1>
      
      <div className="space-y-6">
        {/* 프로필 설정 (유지) */}
        <Card>
          <CardHeader>
            <CardTitle>프로필 설정</CardTitle>
          </CardHeader>
          <CardContent>
            {/* 기존 프로필 설정 유지 */}
          </CardContent>
        </Card>
        
        {/* KIS 계정 설정 제거 */}
        {/* <Card>
          <CardHeader>
            <CardTitle>KIS 계정 연결</CardTitle>
          </CardHeader>
          <CardContent>
            <KisAccountSetupForm />
          </CardContent>
        </Card> */}
        
        {/* 기타 설정들 (유지) */}
      </div>
    </div>
  );
}
```

#### 3. 헤더/네비게이션에서 KIS 상태 표시 제거
```typescript
// src/components/layout/Header.tsx 수정
import { useAuth } from '@/contexts/AuthContext';
// import { KisConnectionStatus } from '@/components/kis/KisConnectionStatus'; // 제거

export default function Header() {
  const { user, logout } = useAuth();
  
  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-semibold">Quantum Trading</h1>
          
          {/* KIS 연결 상태 표시 제거 */}
          {/* {user && <KisConnectionStatus />} */}
        </div>
        
        <div className="ml-auto flex items-center space-x-4">
          {user && (
            <>
              <span className="text-sm text-muted-foreground">
                안녕하세요, {user.name}님
              </span>
              <Button variant="outline" size="sm" onClick={logout}>
                로그아웃
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
```

### Phase 3: API 클라이언트 및 서비스 제거 ✅

#### 1. KIS 전용 API 클라이언트 제거
```bash
# KIS Adapter 직접 호출 클라이언트 제거
rm src/services/DirectKisClient.ts
rm src/services/KisApiClient.ts
rm src/lib/kisClient.ts
```

#### 2. 토큰 저장 관련 유틸리티 제거
```bash
# 토큰 암호화/저장 유틸리티 제거
rm src/utils/TokenStorage.ts  
rm src/utils/KisTokenManager.ts
rm src/lib/tokenStorage.ts
```

#### 3. API 호출 방식 변경 (간접 호출로)
```typescript
// src/services/chartService.ts 수정
class ChartService {
  private baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
  
  // 기존: KIS Adapter 직접 호출 (제거)
  // async getDomesticChart(symbol: string): Promise<ChartData> {
  //   const kisToken = getActiveKISToken();
  //   const response = await fetch(`http://localhost:8000/domestic/chart/daily/${symbol}`, {
  //     headers: { 'X-KIS-Token': kisToken }
  //   });
  //   return response.json();
  // }
  
  // 변경: Spring Boot를 통한 간접 호출
  async getDomesticChart(symbol: string): Promise<ChartData> {
    const token = localStorage.getItem('accessToken');
    
    const response = await fetch(`${this.baseURL}/api/charts/domestic/${symbol}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Chart fetch failed: ${response.statusText}`);
    }
    
    return response.json();
  }
}

export const chartService = new ChartService();
```

### Phase 4: 환경 설정 및 상수 제거 ✅

#### 1. 환경 변수 제거
```bash
# .env.local에서 제거
# NEXT_PUBLIC_KIS_ADAPTER_URL=http://localhost:8000
# NEXT_PUBLIC_ENCRYPTION_KEY=your-encryption-key
# NEXT_PUBLIC_KIS_ENVIRONMENT=SANDBOX
```

#### 2. 상수 파일에서 KIS 관련 제거
```typescript
// src/constants/api.ts 수정
export const API_ENDPOINTS = {
  // 기존 엔드포인트 (유지)
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REFRESH: '/api/auth/refresh'
  },
  
  // KIS 관련 엔드포인트 제거
  // KIS: {
  //   TOKEN: '/api/kis/token',
  //   REFRESH: '/api/kis/token/refresh',
  //   ACCOUNT: '/api/kis-accounts/me'
  // },
  
  CHARTS: {
    DOMESTIC: '/api/charts/domestic',
    OVERSEAS: '/api/charts/overseas'
  }
};

// KIS 관련 상수들 제거
// export const KIS_ENVIRONMENTS = ['LIVE', 'SANDBOX'] as const;
// export const KIS_TOKEN_EXPIRE_HOURS = 6;
// export const KIS_ADAPTER_URL = process.env.NEXT_PUBLIC_KIS_ADAPTER_URL || 'http://localhost:8000';
```

### Phase 5: 타입 정의 정리 ✅

#### 1. KIS 관련 타입 정의 제거
```typescript
// src/types/kis.ts 파일 제거
rm src/types/kis.ts
rm src/types/kisToken.ts

// 또는 types/index.ts에서 KIS 관련 타입 제거
// export interface KISTokenInfo {
//   token: string;
//   environment: 'LIVE' | 'SANDBOX';
//   expiresAt: string;
//   issuedAt: string;
//   appKey: string;
//   appSecret: string;
// }

// export interface KisAccountRequest {
//   appKey: string;
//   appSecret: string;
//   accountNumber: string;
//   environment: 'LIVE' | 'SANDBOX';
// }
```

#### 2. Auth 관련 타입에서 KIS 부분 제거
```typescript
// src/types/auth.ts 수정
export interface User {
  id: number;
  email: string;
  name: string;
  // 기타 사용자 정보
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
  // kisTokens?: { live?: KISTokenInfo; sandbox?: KISTokenInfo; }; // 제거
}
```

### Phase 6: localStorage 정리 ✅

#### 1. KIS 토큰 데이터 정리 스크립트
```typescript
// src/utils/cleanupKisData.ts (한 번 실행 후 제거)
export function cleanupKisTokenData() {
  // KIS 관련 localStorage 키들 제거
  const kisKeys = [
    'kis_token_LIVE',
    'kis_token_SANDBOX', 
    'kis_token_expires_LIVE',
    'kis_token_expires_SANDBOX',
    'kis_account_info',
    'kis_current_environment',
    'kis_connection_status'
  ];
  
  kisKeys.forEach(key => {
    localStorage.removeItem(key);
  });
  
  console.log('KIS token data cleaned up from localStorage');
}

// 애플리케이션 시작 시 한 번 실행
if (typeof window !== 'undefined') {
  cleanupKisTokenData();
}
```

#### 2. 기존 페이지에서 정리 스크립트 실행
```typescript
// src/app/layout.tsx에 한 번 추가 후 제거
'use client';

import { useEffect } from 'react';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    // KIS 데이터 정리 (한 번만 실행)
    const cleaned = localStorage.getItem('kis_data_cleaned');
    if (!cleaned) {
      // 정리 작업 수행
      const kisKeys = ['kis_token_LIVE', 'kis_token_SANDBOX', 'kis_account_info'];
      kisKeys.forEach(key => localStorage.removeItem(key));
      localStorage.setItem('kis_data_cleaned', 'true');
    }
  }, []);

  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
```

## 🔧 수정 필요 페이지들

### 1. 차트 페이지 수정
```typescript
// src/app/charts/domestic/page.tsx 수정
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
// import { useKIS } from '@/contexts/KisTokenContext'; // 제거
import { chartService } from '@/services/chartService';

export default function DomesticChartPage() {
  const { user, isAuthenticated } = useAuth();
  // const { getActiveKISToken, hasKISAccount } = useKIS(); // 제거
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const loadChartData = async (symbol: string) => {
    if (!isAuthenticated) return;
    
    // KIS 계정 체크 제거
    // if (!hasKISAccount) {
    //   alert('KIS 계정을 먼저 연결해주세요.');
    //   return;
    // }
    
    try {
      setLoading(true);
      // 간접 호출 방식으로 변경
      const data = await chartService.getDomesticChart(symbol);
      setChartData(data);
    } catch (error) {
      console.error('Chart loading failed:', error);
      alert('차트 데이터 로딩에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">국내 주식 차트</h1>
      
      {/* KIS 연결 상태 알림 제거 */}
      {/* {!hasKISAccount && (
        <Alert className="mb-4">
          <AlertDescription>
            KIS 계정을 연결해야 차트 데이터를 조회할 수 있습니다.
            <Link href="/settings" className="ml-2 underline">
              설정으로 이동
            </Link>
          </AlertDescription>
        </Alert>
      )} */}
      
      {/* 차트 컴포넌트 */}
      <div className="chart-container">
        {/* 기존 차트 렌더링 로직 유지 */}
      </div>
    </div>
  );
}
```

### 2. 프로필/설정 페이지 수정
```typescript
// src/app/profile/page.tsx 수정
export default function ProfilePage() {
  const { user } = useAuth();
  // const { kisTokens, hasKISAccount } = useKIS(); // 제거

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">프로필</h1>
      
      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>사용자 정보</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p><strong>이메일:</strong> {user?.email}</p>
              <p><strong>이름:</strong> {user?.name}</p>
            </div>
          </CardContent>
        </Card>
        
        {/* KIS 계정 정보 카드 제거 */}
        {/* <Card>
          <CardHeader>
            <CardTitle>KIS 계정 연결 상태</CardTitle>
          </CardHeader>
          <CardContent>
            {hasKISAccount ? (
              <div className="space-y-2">
                <p className="text-green-600">✓ KIS 계정이 연결되어 있습니다.</p>
                {kisTokens.live && <p>실전투자: 연결됨</p>}
                {kisTokens.sandbox && <p>모의투자: 연결됨</p>}
              </div>
            ) : (
              <p className="text-red-600">KIS 계정이 연결되지 않았습니다.</p>
            )}
          </CardContent>
        </Card> */}
      </div>
    </div>
  );
}
```

## ✅ 제거 검증 단계

### 1. 빌드 검증
```bash
cd quantum-web-client

# 1. TypeScript 컴파일 오류 확인
npm run type-check

# 2. ESLint 오류 확인  
npm run lint

# 3. 전체 빌드 성공 확인
npm run build
```

### 2. 개발 서버 실행 검증
```bash
# 개발 서버 정상 실행 확인
npm run dev

# 브라우저에서 확인할 항목:
# - 로그인 페이지 정상 동작
# - 로그인 후 메인 페이지 접근 가능  
# - 차트 페이지 접근 가능 (데이터는 백엔드 준비 후)
# - KIS 관련 오류나 경고 없음
```

### 3. 브라우저 개발자 도구 검증
```javascript
// 브라우저 콘솔에서 확인
// KIS 관련 localStorage 키가 없어야 함
Object.keys(localStorage).filter(key => key.includes('kis'));
// 결과: [] (빈 배열)

// KIS 관련 오류 로그가 없어야 함
// Console에 "KIS", "kis_token" 관련 오류 없음
```

### 4. 네트워크 요청 검증
```bash
# 브라우저 Network 탭에서 확인:
# - KIS Adapter(8000포트) 직접 호출 없음
# - Spring Boot(8080포트)를 통한 간접 호출만 존재
# - X-KIS-Token 헤더 사용 없음
```

## 🚨 주의사항 및 백업

### 제거 전 백업
```bash
# 1. Git 커밋으로 백업
git add .
git commit -m "feat: backup before KIS token management removal"
git push origin feature/frontend-kis-removal

# 2. 패키지 정보 백업
cp package.json package.json.backup
cp package-lock.json package-lock.json.backup
```

### 롤백 계획
```bash
# 문제 발생 시 롤백
# 1. Git을 통한 코드 롤백
git reset --hard HEAD~1

# 2. 의존성 복원
npm install

# 3. 개발 서버 재시작
npm run dev
```

## 🎯 제거 후 추가 작업

### 1. 차트 기능 테스트
- 백엔드에서 KIS Adapter 호출 로직 구현 후
- 차트 데이터 조회 정상 동작 확인
- 에러 처리 및 로딩 상태 표시 확인

### 2. 사용자 경험 개선
- KIS 계정 연결 없이도 사용 가능한 기능들 활성화
- 명확한 에러 메시지 및 가이드 제공
- 로딩 상태 및 피드백 개선

### 3. 문서 업데이트
- 사용자 매뉴얼에서 KIS 계정 연결 부분 제거
- 개발자 가이드 업데이트
- API 문서 수정

---

**프론트엔드 개발자 참고사항**: 이 제거 작업을 통해 클라이언트 복잡성이 대폭 감소하고 유지보수가 훨씬 쉬워집니다. 특히 토큰 관리, 암호화, 상태 동기화 등 복잡한 로직들이 제거되어 코드 안정성이 크게 향상됩니다.