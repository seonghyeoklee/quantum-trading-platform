# MVP 1.0 인증 아키텍처 (서버 중심 설계)

## 📖 개요

사용자 JWT 인증 기반의 단순화된 서버 중심 아키텍처

**핵심 플로우**: 사용자 로그인 → JWT 인증 → Spring Boot API → KIS Adapter (자체 토큰 관리)

## 🏗️ 서버 중심 아키텍처

### 단순화된 접근법 (Security-First)

```
모든 데이터 요청:
Next.js Client → Spring Boot API → KIS Adapter → KIS API
```

**핵심 특징**:
- 모든 KIS 요청이 Spring Boot 경유 → 보안성 향상
- KIS Adapter는 자체 토큰 관리 → 복잡성 제거
- 중앙화된 인증 → 토큰 관리 단순화

## 🔐 Frontend 인증 시스템

### AuthContext 단순화된 설계

```typescript
interface AuthContextType {
  // JWT 기반 인증만
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  
  // KIS 관련 기능 제거됨
  // 모든 KIS 요청은 Spring Boot API를 통해 처리
}
```

### 단순화된 로그인 플로우

**JWT 로그인만**
```
사용자 입력 (email, password) 
→ POST /api/v1/auth/login 
→ JWT 토큰 발급 
→ localStorage 저장
```

**로그인 구현**
```typescript
const login = async (email: string, password: string) => {
  try {
    const response = await apiClient.post('/api/v1/auth/login', { email, password }, false);
    const data = response.data;
    
    if (data.accessToken) {
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);
      localStorage.setItem('user', JSON.stringify(data.user));
      setUser(data.user);
      
      // KIS 토큰 관리는 서버에서 자동 처리
    }
  } catch (error) {
    // 에러 처리
  }
};
```

### JWT 토큰 관리

```typescript
// JWT 토큰만 관리하면 됨
const refreshJWTToken = async () => {
  try {
    const refreshToken = localStorage.getItem('refreshToken');
    const response = await apiClient.post('/api/v1/auth/refresh', { refreshToken });
    
    if (response.data.accessToken) {
      localStorage.setItem('accessToken', response.data.accessToken);
      return response.data.accessToken;
    }
  } catch (error) {
    console.error('JWT token refresh failed:', error);
    // 로그인 페이지로 리다이렉트
    router.push('/login?reason=token_expired');
  }
};
```

## 🖥️ Backend API 설계

### 차트 데이터 조회 (KIS Adapter 연동)
```
GET /api/v1/chart/{symbol}/daily
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "symbol": "005930",
  "data": [
    {
      "date": "20250203",
      "open": 71000,
      "high": 72000,
      "low": 70500,
      "close": 71500,
      "volume": 1234567
    }
  ]
}
```

### 현재가 조회
```
GET /api/v1/stocks/{symbol}/price
Authorization: Bearer {JWT_TOKEN}

Response:
{
  "symbol": "005930",
  "currentPrice": 71500,
  "change": 500,
  "changePercent": 0.70
}
```

## ⚡ Spring Boot API 호출 패턴

### API 클라이언트 구현
```typescript
const fetchStockData = async (endpoint: string, params: any) => {
  const token = localStorage.getItem('accessToken');
  
  if (!token) {
    throw new Error('JWT token not available');
  }
  
  const response = await fetch(`http://localhost:8080/api/v1${endpoint}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    ...params
  });
  
  if (response.status === 401) {
    // JWT 토큰 갱신
    await refreshJWTToken();
    // 재시도 로직
  }
  
  return response.json();
};
```

### 사용 예시
```typescript
// 차트 데이터 조회
const chartData = await fetchStockData('/chart/005930/daily', {});

// 현재가 조회  
const currentPrice = await fetchStockData('/stocks/005930/price', {});
```

## 🛡️ 보안 및 에러 처리

### JWT 토큰 에러 처리
```typescript
const handleAPIError = async (error: any) => {
  if (error.status === 401) {
    try {
      await refreshJWTToken();
      return true; // 재시도 가능
    } catch (refreshError) {
      router.push('/login?reason=token_expired');
      return false;
    }
  }
  throw error;
};
```

### 로딩 상태 관리
```typescript
const ChartComponent = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadChartData = async () => {
      try {
        setLoading(true);
        const data = await fetchStockData('/chart/005930/daily', {});
        setChartData(data);
      } catch (err) {
        setError('차트 데이터 로딩 실패');
      } finally {
        setLoading(false);
      }
    };
    
    loadChartData();
  }, []);
  
  if (loading) return <div>차트 로딩 중...</div>;
  if (error) return <div>에러: {error}</div>;
  
  return <TradingChart data={chartData} />;
};
```

## 🚀 주요 장점

### 1. 단순성
- **토큰 관리 단순화**: JWT 토큰만 관리
- **아키텍처 명확성**: 선형적인 요청 플로우
- **개발 복잡성 감소**: 클라이언트 토큰 관리 불필요

### 2. 보안성
- **중앙화된 인증**: 모든 KIS 요청이 서버를 경유
- **토큰 노출 방지**: KIS 토큰이 클라이언트에 노출되지 않음
- **서버 측 제어**: KIS API 호출을 서버에서 완전 제어

### 3. 유지보수성
- **일관된 에러 처리**: 모든 API 에러를 서버에서 처리
- **로깅 중앙화**: 모든 KIS API 호출 로그 통합
- **모니터링 용이**: 단일 지점에서 API 상태 모니터링

### 4. 확장성
- **서버 레벨 캐싱**: Redis 등을 활용한 효율적 캐싱
- **Rate Limiting**: 서버에서 KIS API 호출 제한 관리
- **로드 밸런싱**: Spring Boot 서버 수평 확장 가능

## 🧪 테스트 시나리오

1. **사용자 로그인**: JWT 토큰 발급 → 차트 데이터 조회 가능
2. **JWT 토큰 만료**: API 호출 시 401 → 자동 갱신 → 재시도
3. **KIS API 에러**: 서버에서 처리 → 적절한 에러 메시지 반환
4. **서버 재시작**: KIS Adapter 자체 토큰 관리로 자동 복구
5. **네트워크 오류**: 서버 레벨에서 재시도 및 에러 처리

이 서버 중심 아키텍처로 **안전한 토큰 관리**와 **단순한 클라이언트 구현**을 동시에 만족하는 최적의 인증 시스템을 구축할 수 있습니다.