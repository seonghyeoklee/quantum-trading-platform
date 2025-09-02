# MVP 1.0 하이브리드 KIS 토큰 관리 아키텍처 구현 계획

## 새로운 아키텍처 개념

### 하이브리드 호출 패턴
```
실시간 데이터 (빠른 응답 필요):
Next.js Client → (직접) → KIS Adapter → KIS API

토큰 관리 & 설정 데이터:
Next.js Client → Spring Boot → (필요시) KIS Adapter
```

## 기존 vs 새로운 접근법

### Before (서버 중심 구조)
```
Next.js → Spring Boot (프록시) → KIS Adapter → KIS API
- 모든 요청이 Spring Boot를 거침
- 네트워크 홉 증가 (성능 저하)
- 서버 부하 집중
```

### After (하이브리드 구조)
```
Next.js → 직접 KIS Adapter 호출 (실시간 데이터)
  ↓ 토큰 관리는
Spring Boot (토큰 발급/갱신) ← 필요시 호출
- 실시간 데이터는 직접 호출 (성능 향상)
- 토큰 관리는 서버에서 담당 (보안)
- 부하 분산 효과
```

---

## Phase 1: 클라이언트 KIS 토큰 관리

### 1. Next.js KIS 토큰 스토어 구현

#### KIS Token Context
```typescript
interface KisTokenStore {
  // 토큰 상태
  kisToken: string | null
  tokenExpiresAt: Date | null
  environment: 'LIVE' | 'SANDBOX'
  
  // 계정 정보
  kisAccount: KisAccount | null
  isConnected: boolean
  
  // 액션
  setKisToken: (token: string, expiresAt: Date) => void
  refreshToken: () => Promise<void>
  connectKisAccount: (account: KisAccountRequest) => Promise<void>
  disconnectKisAccount: () => void
  switchEnvironment: (env: 'LIVE' | 'SANDBOX') => void
}

const useKisTokenStore = create<KisTokenStore>((set, get) => ({
  // 초기 상태
  kisToken: null,
  tokenExpiresAt: null,
  environment: 'SANDBOX',
  kisAccount: null,
  isConnected: false,
  
  // 토큰 설정 및 로컬 저장
  setKisToken: (token, expiresAt) => {
    const encryptedToken = encryptToken(token)
    localStorage.setItem('kis_token', encryptedToken)
    localStorage.setItem('kis_token_expires', expiresAt.toISOString())
    
    set({ 
      kisToken: token, 
      tokenExpiresAt: expiresAt,
      isConnected: true 
    })
  },
  
  // 토큰 자동 갱신
  refreshToken: async () => {
    const { kisAccount, environment } = get()
    if (!kisAccount) return
    
    try {
      const response = await fetch('/api/kis/token/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ environment })
      })
      
      const { token, expiresAt } = await response.json()
      get().setKisToken(token, new Date(expiresAt))
    } catch (error) {
      console.error('토큰 갱신 실패:', error)
      set({ isConnected: false })
    }
  }
}))
```

#### Token Storage (암호화)
```typescript
// 클라이언트 암호화 유틸리티
export class TokenStorage {
  private static readonly ENCRYPTION_KEY = process.env.NEXT_PUBLIC_ENCRYPTION_KEY!
  
  static saveToken(token: string, expiresAt: Date): void {
    const encrypted = CryptoJS.AES.encrypt(token, this.ENCRYPTION_KEY).toString()
    localStorage.setItem('kis_token', encrypted)
    localStorage.setItem('kis_token_expires', expiresAt.toISOString())
  }
  
  static getToken(): { token: string | null, expiresAt: Date | null } {
    const encrypted = localStorage.getItem('kis_token')
    const expiresStr = localStorage.getItem('kis_token_expires')
    
    if (!encrypted || !expiresStr) {
      return { token: null, expiresAt: null }
    }
    
    try {
      const token = CryptoJS.AES.decrypt(encrypted, this.ENCRYPTION_KEY).toString(CryptoJS.enc.Utf8)
      const expiresAt = new Date(expiresStr)
      
      return { token, expiresAt }
    } catch (error) {
      return { token: null, expiresAt: null }
    }
  }
  
  static isTokenValid(): boolean {
    const { token, expiresAt } = this.getToken()
    return !!(token && expiresAt && expiresAt > new Date())
  }
}
```

### 2. KIS API 클라이언트 서비스

#### Direct KIS Adapter Client
```typescript
export class DirectKisClient {
  private baseURL = process.env.NEXT_PUBLIC_KIS_ADAPTER_URL || 'http://localhost:8000'
  private tokenStore = useKisTokenStore
  
  constructor() {
    // 요청 인터셉터
    this.setupInterceptors()
  }
  
  private setupInterceptors() {
    // 401 에러 시 토큰 갱신 및 재시도
    this.axios.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 401) {
          await this.tokenStore.getState().refreshToken()
          // 원래 요청 재시도
          return this.axios.request(error.config)
        }
        return Promise.reject(error)
      }
    )
  }
  
  // 국내 차트 데이터 조회
  async getDomesticChart(symbol: string, options: ChartOptions = {}): Promise<ChartResponse> {
    const token = this.getValidToken()
    
    const response = await fetch(`${this.baseURL}/domestic/chart/daily/${symbol}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-KIS-Token': token,
        'Content-Type': 'application/json'
      },
      ...this.buildQueryParams(options)
    })
    
    if (!response.ok) {
      throw new KisApiError(`차트 조회 실패: ${response.statusText}`)
    }
    
    return response.json()
  }
  
  // 해외 차트 데이터 조회  
  async getOverseasChart(
    exchange: string, 
    symbol: string, 
    options: OverseasChartOptions
  ): Promise<ChartResponse> {
    const token = this.getValidToken()
    
    const response = await fetch(
      `${this.baseURL}/overseas/${exchange}/chart/daily/${symbol}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-KIS-Token': token,
          'Content-Type': 'application/json'
        },
        ...this.buildQueryParams(options)
      }
    )
    
    return response.json()
  }
  
  private getValidToken(): string {
    const { kisToken, tokenExpiresAt } = this.tokenStore.getState()
    
    if (!kisToken || !tokenExpiresAt) {
      throw new Error('KIS 토큰이 없습니다. 계정을 연결해주세요.')
    }
    
    if (tokenExpiresAt <= new Date()) {
      throw new Error('KIS 토큰이 만료되었습니다.')
    }
    
    return kisToken
  }
}
```

### 3. 사용자 KIS 계정 연동 UI

#### KIS 계정 등록 폼
```typescript
const KisAccountSetupForm = () => {
  const kisTokenStore = useKisTokenStore()
  const [formData, setFormData] = useState<KisAccountForm>({
    appKey: '',
    appSecret: '',
    accountNumber: '',
    environment: 'SANDBOX'
  })
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      // 1. Spring Boot에서 계정 검증
      const validateResponse = await fetch('/api/kis/account/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (!validateResponse.ok) {
        throw new Error('KIS 계정 정보가 올바르지 않습니다.')
      }
      
      // 2. 토큰 발급 요청
      const tokenResponse = await fetch('/api/kis/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      const { token, expiresAt } = await tokenResponse.json()
      
      // 3. 토큰 저장 및 상태 업데이트
      kisTokenStore.setKisToken(token, new Date(expiresAt))
      kisTokenStore.setKisAccount(formData)
      
      toast.success('KIS 계정이 성공적으로 연결되었습니다.')
      
    } catch (error) {
      toast.error(error.message)
    }
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>KIS 계정 연결</CardTitle>
        <CardDescription>
          한국투자증권 계정 정보를 입력하여 실시간 데이터를 조회하세요.
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="environment">환경 선택</Label>
            <Select 
              value={formData.environment} 
              onValueChange={(value) => setFormData({...formData, environment: value})}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="SANDBOX">SANDBOX (모의투자)</SelectItem>
                <SelectItem value="LIVE">LIVE (실계좌)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="appKey">App Key</Label>
            <Input
              id="appKey"
              type="password"
              value={formData.appKey}
              onChange={(e) => setFormData({...formData, appKey: e.target.value})}
              placeholder="KIS Open API App Key"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="appSecret">App Secret</Label>
            <Input
              id="appSecret"
              type="password"
              value={formData.appSecret}
              onChange={(e) => setFormData({...formData, appSecret: e.target.value})}
              placeholder="KIS Open API App Secret"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="accountNumber">계좌번호</Label>
            <Input
              id="accountNumber"
              value={formData.accountNumber}
              onChange={(e) => setFormData({...formData, accountNumber: e.target.value})}
              placeholder="12345678-01"
              required
            />
          </div>
          
          <Button type="submit" className="w-full">
            계정 연결하기
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
```

#### 토큰 상태 표시 컴포넌트
```typescript
const KisConnectionStatus = () => {
  const { kisToken, tokenExpiresAt, isConnected, environment } = useKisTokenStore()
  
  const getStatusColor = () => {
    if (!isConnected) return 'text-red-500'
    if (tokenExpiresAt && tokenExpiresAt <= new Date()) return 'text-yellow-500'
    return 'text-green-500'
  }
  
  const getStatusText = () => {
    if (!isConnected) return '연결 안됨'
    if (tokenExpiresAt && tokenExpiresAt <= new Date()) return '토큰 만료'
    return '연결됨'
  }
  
  return (
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 rounded-full ${getStatusColor().replace('text-', 'bg-')}`} />
      <span className={`text-sm ${getStatusColor()}`}>
        KIS {environment}: {getStatusText()}
      </span>
      {tokenExpiresAt && (
        <span className="text-xs text-muted-foreground">
          만료: {tokenExpiresAt.toLocaleString()}
        </span>
      )}
    </div>
  )
}
```

---

## Phase 2: Spring Boot 토큰 발급 서비스

### 1. KIS 토큰 발급 API

#### 토큰 관리 도메인 엔티티
```kotlin
@Entity
@Table(name = "kis_accounts")
data class KisAccount(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,
    
    @Column(name = "user_id", nullable = false)
    val userId: Long,
    
    @Column(name = "app_key", nullable = false)
    @Encrypted
    val appKey: String,
    
    @Column(name = "app_secret", nullable = false)
    @Encrypted
    val appSecret: String,
    
    @Column(name = "account_number", nullable = false)
    @Encrypted
    val accountNumber: String,
    
    @Enumerated(EnumType.STRING)
    @Column(name = "environment")
    val environment: KisEnvironment,
    
    @Column(name = "is_active")
    val isActive: Boolean = true,
    
    @CreationTimestamp
    val createdAt: LocalDateTime,
    
    @UpdateTimestamp
    val updatedAt: LocalDateTime
)

@Entity
@Table(name = "kis_tokens")  
data class KisToken(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,
    
    @Column(name = "user_id", nullable = false)
    val userId: Long,
    
    @Column(name = "access_token", length = 2048)
    @Encrypted
    val accessToken: String,
    
    @Column(name = "expires_at")
    val expiresAt: LocalDateTime,
    
    @Enumerated(EnumType.STRING)
    @Column(name = "environment")
    val environment: KisEnvironment,
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status")
    val status: TokenStatus = TokenStatus.ACTIVE
)
```

#### 토큰 발급 REST API
```kotlin
@RestController
@RequestMapping("/api/kis")
class KisTokenController(
    private val kisTokenService: KisTokenService
) {
    
    @PostMapping("/account/validate")
    suspend fun validateAccount(
        @RequestBody request: KisAccountRequest,
        authentication: Authentication
    ): ResponseEntity<ValidationResponse> {
        val userId = authentication.name.toLong()
        
        return try {
            kisTokenService.validateKisAccount(userId, request)
            ResponseEntity.ok(ValidationResponse(true, "계정 정보가 유효합니다."))
        } catch (e: Exception) {
            ResponseEntity.badRequest()
                .body(ValidationResponse(false, e.message ?: "계정 검증 실패"))
        }
    }
    
    @PostMapping("/token")
    suspend fun issueToken(
        @RequestBody request: KisAccountRequest,
        authentication: Authentication
    ): ResponseEntity<TokenResponse> {
        val userId = authentication.name.toLong()
        
        return try {
            val tokenInfo = kisTokenService.issueToken(userId, request)
            ResponseEntity.ok(TokenResponse(
                token = tokenInfo.accessToken,
                expiresAt = tokenInfo.expiresAt,
                environment = tokenInfo.environment
            ))
        } catch (e: Exception) {
            ResponseEntity.status(500)
                .body(TokenResponse(error = e.message ?: "토큰 발급 실패"))
        }
    }
    
    @PostMapping("/token/refresh")
    suspend fun refreshToken(
        @RequestBody request: TokenRefreshRequest,
        authentication: Authentication
    ): ResponseEntity<TokenResponse> {
        val userId = authentication.name.toLong()
        
        return try {
            val tokenInfo = kisTokenService.refreshToken(userId, request.environment)
            ResponseEntity.ok(TokenResponse(
                token = tokenInfo.accessToken,
                expiresAt = tokenInfo.expiresAt,
                environment = tokenInfo.environment
            ))
        } catch (e: Exception) {
            ResponseEntity.status(401)
                .body(TokenResponse(error = e.message ?: "토큰 갱신 실패"))
        }
    }
}
```

### 2. 토큰 관리 서비스

#### KIS 토큰 서비스
```kotlin
@Service
@Transactional
class KisTokenService(
    private val kisAccountRepository: KisAccountRepository,
    private val kisTokenRepository: KisTokenRepository,
    private val kisApiClient: KisApiClient,
    private val encryptionService: EncryptionService
) {
    
    suspend fun issueToken(userId: Long, request: KisAccountRequest): KisToken {
        // 1. 계정 정보 저장 (기존 계정 업데이트 또는 신규 생성)
        val kisAccount = saveOrUpdateKisAccount(userId, request)
        
        // 2. KIS API로 토큰 발급 요청
        val tokenResponse = kisApiClient.getAccessToken(
            appKey = request.appKey,
            appSecret = request.appSecret,
            environment = request.environment
        )
        
        // 3. 토큰 DB 저장
        val kisToken = KisToken(
            userId = userId,
            accessToken = tokenResponse.accessToken,
            expiresAt = LocalDateTime.now().plusHours(6),
            environment = request.environment,
            status = TokenStatus.ACTIVE
        )
        
        return kisTokenRepository.save(kisToken)
    }
    
    suspend fun refreshToken(userId: Long, environment: KisEnvironment): KisToken {
        // 기존 계정 정보 조회
        val kisAccount = kisAccountRepository.findByUserIdAndEnvironment(userId, environment)
            ?: throw KisAccountNotFoundException("KIS 계정이 연결되지 않았습니다.")
        
        // 새 토큰 발급
        return issueToken(userId, KisAccountRequest(
            appKey = kisAccount.appKey,
            appSecret = kisAccount.appSecret,
            accountNumber = kisAccount.accountNumber,
            environment = environment
        ))
    }
    
    @Scheduled(fixedRate = 3600000) // 1시간마다 실행
    fun scheduleTokenRefresh() {
        // 만료 1시간 전인 토큰들 갱신
        val tokensToRefresh = kisTokenRepository.findTokensNearExpiry(
            LocalDateTime.now().plusHours(1)
        )
        
        tokensToRefresh.forEach { token ->
            try {
                runBlocking {
                    refreshToken(token.userId, token.environment)
                }
                log.info("토큰 자동 갱신 완료: userId=${token.userId}, env=${token.environment}")
            } catch (e: Exception) {
                log.error("토큰 자동 갱신 실패: userId=${token.userId}", e)
            }
        }
    }
}
```

---

## Phase 3: KIS Adapter 확장

### 1. CORS 및 클라이언트 지원 확장

#### main.py CORS 설정 업데이트
```python
# 기존 CORS에 Next.js 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Spring Boot
        "http://localhost:3000",  # Next.js (추가)
        "https://your-domain.com"  # 프로덕션 도메인
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 클라이언트 토큰 미들웨어
```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class ClientTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 클라이언트 직접 호출 감지
        origin = request.headers.get("origin")
        is_client_call = origin and origin.startswith("http://localhost:3000")
        
        if is_client_call:
            # 클라이언트 호출인 경우 토큰 검증
            auth_header = request.headers.get("Authorization")
            kis_token = request.headers.get("X-KIS-Token")
            
            if not auth_header or not kis_token:
                raise HTTPException(
                    status_code=401, 
                    detail="인증 토큰이 필요합니다."
                )
            
            # JWT 토큰 검증 (간단한 검증)
            try:
                jwt_token = auth_header.replace("Bearer ", "")
                # 여기서 JWT 검증 로직 (선택사항)
                request.state.is_client_call = True
                request.state.kis_token = kis_token
            except Exception as e:
                raise HTTPException(status_code=401, detail="유효하지 않은 토큰")
        
        response = await call_next(request)
        return response

# 미들웨어 등록
app.add_middleware(ClientTokenMiddleware)
```

### 2. 토큰 갱신 엔드포인트 추가

```python
@app.post("/token/refresh")
async def refresh_kis_token(
    request: Request,
    refresh_request: TokenRefreshRequest
):
    """KIS 토큰 갱신 (클라이언트용)"""
    
    try:
        # Spring Boot 토큰 갱신 API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8080/api/kis/token/refresh",
                json={"environment": refresh_request.environment},
                headers={
                    "Authorization": request.headers.get("Authorization"),
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return ApiResponse(
                    success=True,
                    data=token_data,
                    message="토큰이 성공적으로 갱신되었습니다.",
                    timestamp=datetime.now().isoformat()
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="토큰 갱신 실패"
                )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"토큰 갱신 중 오류 발생: {str(e)}"
        )
```

---

## 클라이언트 사용 플로우

### 초기 설정 플로우
1. **사용자 KIS 계정 등록**
   - Next.js에서 KIS 계정 정보 입력 폼 제공
   - appKey, appSecret, 계좌번호, 환경(LIVE/SANDBOX) 선택

2. **Spring Boot 검증 및 토큰 발급**
   - `POST /api/kis/account/validate`: 계정 정보 검증
   - `POST /api/kis/token`: 첫 KIS 토큰 발급
   - 토큰과 만료시간을 클라이언트로 반환

3. **클라이언트 토큰 저장**
   - localStorage에 암호화하여 KIS 토큰 저장
   - Zustand 스토어에 토큰 상태 업데이트
   - 연결 완료 상태로 변경

### 실시간 데이터 조회 플로우
1. **차트 페이지 접근**
   - 사용자가 국내/해외 차트 페이지 접근
   - 시장 선택 상태 확인 (domestic/overseas + exchange)

2. **직접 API 호출**
   - Next.js에서 KIS Adapter로 직접 HTTP 요청
   - `GET localhost:8000/domestic/chart/daily/005930`
   - Authorization 헤더에 JWT + X-KIS-Token 헤더에 KIS 토큰 포함

3. **빠른 응답 및 렌더링**
   - 중간 서버(Spring Boot) 거치지 않고 바로 데이터 수신
   - 실시간 차트 컴포넌트에 즉시 데이터 반영

### 토큰 만료시 자동 처리 플로우
1. **401 Error 감지**
   - KIS Adapter에서 토큰 만료 응답 (401 Unauthorized)
   - axios interceptor에서 자동으로 감지

2. **자동 갱신 시도**  
   - Spring Boot `/api/kis/token/refresh` 호출
   - 새로운 KIS 토큰 발급 받음
   - localStorage 및 Zustand 스토어 업데이트

3. **원래 요청 재시도**
   - 실패했던 차트 조회 API 자동으로 재호출
   - 사용자는 중단 없이 차트 데이터 확인
   - 토큰 갱신 과정이 백그라운드에서 투명하게 처리

---

## 주요 장점

### 1. 성능 향상
- **네트워크 홉 감소**: Next.js → KIS Adapter (1홉)
- **서버 부하 감소**: Spring Boot가 모든 요청을 프록시하지 않음  
- **실시간성 향상**: 중간 서버 없이 직접 데이터 조회
- **병렬 처리**: 여러 종목 데이터를 동시에 조회 가능

### 2. 확장성 및 유연성
- **수평 확장**: KIS Adapter를 여러 인스턴스로 확장 가능
- **부하 분산**: 실시간 데이터와 비즈니스 로직 완전 분리
- **캐싱 효율**: 클라이언트별 독립적인 브라우저 캐싱
- **오프라인 저항성**: 토큰이 있으면 일부 기능 독립 동작

### 3. 사용자 경험
- **빠른 응답**: 실시간 차트 데이터 즉시 로딩
- **투명한 토큰 관리**: 사용자가 토큰 상태 직접 확인
- **끊김 없는 서비스**: 토큰 갱신이 백그라운드에서 자동 처리
- **환경 전환**: LIVE/SANDBOX 간 빠른 전환

### 4. 보안 및 안정성
- **이중 토큰 인증**: JWT(사용자 인증) + KIS Token(API 인증)
- **클라이언트 암호화**: 브라우저 저장 토큰 AES 암호화
- **서버 측 암호화**: DB 저장 계정 정보 및 토큰 암호화  
- **자동 토큰 갱신**: 만료 전 사전 갱신으로 서비스 중단 방지

---

## 구현 우선순위

### High Priority (1주차)
1. **Next.js KIS Token Context 구현**
   - Zustand 기반 토큰 상태 관리
   - localStorage 암호화 저장/불러오기
   - 토큰 만료 검사 로직

2. **Spring Boot 토큰 발급 API 구현**  
   - KIS 계정/토큰 엔티티 생성
   - 토큰 발급/갱신 REST API
   - KIS API 클라이언트 구현

3. **KIS Adapter CORS 설정 확장**
   - Next.js 직접 호출 허용
   - 클라이언트 토큰 미들웨어
   - 기본 인증 검증 로직

### Medium Priority (2주차)  
1. **클라이언트 Direct API Client 구현**
   - axios 기반 KIS Adapter 직접 호출 클라이언트
   - 401 에러 자동 재시도 interceptor
   - 요청 대기열 및 배칭 처리

2. **토큰 자동 갱신 로직 구현**
   - 만료 전 사전 갱신 (5.5시간 후)
   - 실패 시 지수 백오프 재시도
   - 사용자 알림 및 에러 처리

3. **사용자 KIS 계정 연동 UI 완성**
   - 계정 등록/수정/삭제 폼
   - 토큰 상태 실시간 표시
   - 환경 전환(LIVE/SANDBOX) UI

### Low Priority (3주차)
1. **토큰 갱신 스케줄러 구현**
   - Spring Boot 스케줄러로 배치 갱신
   - 갱신 실패 모니터링 및 알람
   - 토큰 사용 통계 및 분석

2. **성능 최적화 및 모니터링**
   - 요청 응답 시간 모니터링
   - KIS API 사용량 추적
   - 에러율 및 성공율 대시보드

3. **에러 처리 및 사용자 알림**
   - 토스트 알림 시스템
   - 에러 복구 가이드 제공
   - 고객 지원을 위한 로그 수집

이 하이브리드 아키텍처로 구현하면 **빠른 실시간 데이터 조회**와 **안전한 토큰 관리**를 동시에 만족하는 최적의 시스템을 구축할 수 있습니다.