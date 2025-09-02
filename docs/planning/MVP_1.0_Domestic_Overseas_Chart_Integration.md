# MVP 1.0 국내/해외 주식 통합 차트 시스템 가이드

## 시스템 아키텍처

```
헤더: [국내] [해외] - 차트 - 종목 - 전략 - 자동매매 ...
          ↓
Next.js Frontend (포트 3000) - 전역 상태 관리
    ↓ HTTP/REST API
Spring Boot Backend (포트 8080) - 시장별 라우팅
    ↓ HTTP/REST API  
Python FastAPI KIS Adapter (포트 8000) - 국내/해외 분리 API
    ↓ HTTPS API Calls
Korea Investment & Securities API
```

## API 구조 설계

### FastAPI 엔드포인트 구조 (포트 8000)

#### 국내 주식 API
```
GET /domestic/chart/daily/{symbol}?period=D&start_date=20241201&end_date=20241231
GET /domestic/chart/minute/{symbol}?time_div=1&start_time=090000&end_time=153000
GET /domestic/price/{symbol}?market=J
```

#### 해외 주식 API
```
GET /overseas/{exchange}/chart/daily/{symbol}?start_date=20241201&end_date=20241231&period=D
GET /overseas/{exchange}/chart/minute/{symbol}?nmin=1&pinc=1
GET /overseas/{exchange}/price/{symbol}
```

#### 시장 정보 API
```
GET /markets/info                                    # 지원 시장 정보
GET /markets/domestic/sample-symbols                 # 국내 주요 종목
GET /markets/overseas/{exchange}/sample-symbols      # 거래소별 주요 종목
```

### 지원 거래소

**해외 거래소 목록:**
- **NYS**: 뉴욕증권거래소 (NYSE)
- **NAS**: 나스닥 (NASDAQ)
- **AMS**: 아메리칸증권거래소 (AMEX)
- **HKS**: 홍콩증권거래소 (HKEX)
- **SHS**: 중국 상해거래소 (SSE)
- **SZS**: 중국 심천거래소 (SZSE)
- **TSE**: 도쿄증권거래소 (TSE)
- **HSX**: 베트남 호치민거래소 (HOSE)
- **HNX**: 베트남 하노이거래소 (HNX)

## 국내 vs 해외 API 차이점

### 파라미터 차이
```python
# 국내 - 선택적 날짜
GET /domestic/chart/daily/005930?period=D&count=100
# start_date, end_date 선택사항

# 해외 - 필수 날짜 
GET /overseas/NAS/chart/daily/AAPL?start_date=20241201&end_date=20241231&period=D
# start_date, end_date 필수
```

### 종목 코드 형식
- **국내**: 6자리 숫자 (005930, 000660)
- **해외**: 심볼 (AAPL, TSLA, NVDA)

### KIS API 호출 차이
```python
# 국내
inquire_daily_itemchartprice(
    FID_COND_MRKT_DIV_CODE="J",
    FID_INPUT_ISCD="005930", 
    FID_PERIOD_DIV_CODE="D"
)

# 해외
overseas_daily_chart(
    fid_cond_mrkt_div_code="N",
    fid_input_iscd="AAPL",
    fid_input_date_1="20241201",  # 필수
    fid_input_date_2="20241231"   # 필수
)
```

## 프론트엔드 전역 상태 관리

### Zustand 스토어 구조
```typescript
interface MarketStore {
  selectedMarket: 'domestic' | 'overseas'
  selectedExchange?: string  // 해외 선택시만 사용
  setMarket: (market: 'domestic' | 'overseas', exchange?: string) => void
  
  // 차트 설정
  defaultPeriod: string
  defaultDateRange: number
}

const useMarketStore = create<MarketStore>((set) => ({
  selectedMarket: 'domestic',
  selectedExchange: undefined,
  defaultPeriod: 'D',
  defaultDateRange: 30,
  
  setMarket: (market, exchange) => set({
    selectedMarket: market,
    selectedExchange: market === 'overseas' ? exchange : undefined
  })
}))
```

### 헤더 컴포넌트
```typescript
const Header = () => {
  const { selectedMarket, selectedExchange, setMarket } = useMarketStore()
  
  return (
    <nav className="flex items-center space-x-4">
      {/* 시장 선택 토글 */}
      <MarketToggle
        value={selectedMarket}
        onChange={(market) => {
          if (market === 'overseas') {
            // 해외 선택시 거래소 선택 모달
            setMarket(market, 'NAS') // 기본값
          } else {
            setMarket(market)
          }
        }}
        options={[
          { value: 'domestic', label: '국내' },
          { value: 'overseas', label: '해외' }
        ]}
      />
      
      {/* 해외 거래소 선택 */}
      {selectedMarket === 'overseas' && (
        <ExchangeSelector
          value={selectedExchange}
          onChange={(exchange) => setMarket('overseas', exchange)}
        />
      )}
      
      {/* 메뉴 */}
      <NavLink to="/chart">차트</NavLink>
      <NavLink to="/stocks">종목</NavLink>
      <NavLink to="/strategy">전략</NavLink>
      <NavLink to="/auto-trading">자동매매</NavLink>
    </nav>
  )
}
```

## Spring Boot 라우팅 로직

### WebClient 설정
```kotlin
@Configuration
class WebClientConfig {
    @Bean
    fun kisWebClient(): WebClient {
        return WebClient.builder()
            .baseUrl("http://localhost:8000")
            .build()
    }
}
```

### 통합 차트 서비스
```kotlin
@Service
class ChartService(private val kisWebClient: WebClient) {
    
    suspend fun getChart(
        market: String,
        symbol: String, 
        exchange: String? = null,
        period: String = "D"
    ): ChartResponse {
        val uri = when (market) {
            "domestic" -> "/domestic/chart/daily/$symbol?period=$period"
            "overseas" -> "/overseas/$exchange/chart/daily/$symbol?period=$period" +
                         "&start_date=${getStartDate()}&end_date=${getEndDate()}"
            else -> throw IllegalArgumentException("Unsupported market: $market")
        }
        
        return kisWebClient.get()
            .uri(uri)
            .retrieve()
            .awaitBody<ChartResponse>()
    }
    
    private fun getStartDate(): String = 
        LocalDate.now().minusDays(30).format(DateTimeFormatter.ofPattern("yyyyMMdd"))
        
    private fun getEndDate(): String = 
        LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"))
}
```

### REST 컨트롤러
```kotlin
@RestController
@RequestMapping("/api/chart")
class ChartController(private val chartService: ChartService) {
    
    @GetMapping("/{market}/daily/{symbol}")
    suspend fun getDailyChart(
        @PathVariable market: String,
        @PathVariable symbol: String,
        @RequestParam exchange: String?,
        @RequestParam(defaultValue = "D") period: String
    ): ChartResponse {
        return chartService.getChart(market, symbol, exchange, period)
    }
}
```

## 사용자 시나리오

### 시나리오 1: 국내 주식 조회
1. 헤더에서 **[국내]** 선택
2. 차트 페이지 이동
3. "005930" (삼성전자) 검색
4. → `GET /api/chart/domestic/daily/005930`
5. → FastAPI: `GET /domestic/chart/daily/005930`

### 시나리오 2: 해외 주식 조회  
1. 헤더에서 **[해외]** 선택
2. 거래소를 **NASDAQ** 선택
3. 차트 페이지 이동
4. "AAPL" 검색
5. → `GET /api/chart/overseas/daily/AAPL?exchange=NAS`
6. → FastAPI: `GET /overseas/NAS/chart/daily/AAPL`

### 시나리오 3: 시장 간 전환
1. 국내에서 삼성전자 차트 조회 중
2. 헤더에서 **[해외]** 클릭
3. → 전역 상태 변경
4. → 같은 차트 페이지에서 해외 검색으로 자동 전환
5. AAPL 검색하여 해외 차트 조회

## API 테스트 예시

### 국내 주식 조회
```bash
# 삼성전자 일봉 조회
curl "http://localhost:8000/domestic/chart/daily/005930?period=D&count=30"

# 삼성전자 현재가 조회  
curl "http://localhost:8000/domestic/price/005930"

# 국내 주요 종목 목록
curl "http://localhost:8000/markets/domestic/sample-symbols"
```

### 해외 주식 조회
```bash
# AAPL 일봉 조회 (NASDAQ)
curl "http://localhost:8000/overseas/NAS/chart/daily/AAPL?start_date=20241201&end_date=20241231"

# TSLA 현재가 조회 (NASDAQ)
curl "http://localhost:8000/overseas/NAS/price/TSLA"

# NASDAQ 주요 종목 목록
curl "http://localhost:8000/markets/overseas/NAS/sample-symbols"
```

### 시장 정보 조회
```bash
# 지원 시장 및 거래소 정보
curl "http://localhost:8000/markets/info"

# API 엔드포인트 목록
curl "http://localhost:8000/api/endpoints"
```

## 에러 처리

### 거래소 코드 검증
```json
{
  "detail": "지원하지 않는 거래소입니다. 지원 거래소: NYS, NAS, AMS, HKS, SHS, SZS, TSE, HSX, HNX"
}
```

### 해외 주식 필수 파라미터
```json
{
  "detail": "해외 주식은 start_date, end_date가 필수입니다."
}
```

### 모듈 로드 실패
```json
{
  "detail": "해외 주식 모듈을 사용할 수 없습니다. 설정을 확인해주세요."
}
```

## 보안 및 성능

### Rate Limiting 적용
- **국내**: 초당 20회
- **해외**: 초당 2회 (더 제한적)
- 거래소별 독립적인 rate limiting 적용

### 캐싱 전략
- 현재가: 1초 캐시
- 일봉 데이터: 1분 캐시  
- 시장 정보: 1시간 캐시

### 로깅 정책
- 국내/해외 API 호출 분리 로깅
- 거래소별 에러율 모니터링
- 인기 종목 추적

이제 완전한 국내/해외 통합 시스템으로 사용자가 헤더에서 시장을 선택하면 모든 기능이 해당 시장에 맞게 동작합니다.