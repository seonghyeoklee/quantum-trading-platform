# 🌐 웹 UI 통합 사양서 - Quantum Trading Platform

## 🎯 개요

Python 기반 주식 분석 엔진을 Next.js 프론트엔드와 Spring Boot 백엔드에 완전 통합하여 직관적인 웹 분석 서비스를 제공하는 통합 사양서입니다.

## 📊 현재 시스템 현황

### 완성된 분석 엔진
- ✅ **MultiDataProvider**: 3개 소스 통합 (PyKRX, FDR, yfinance)
- ✅ **TechnicalAnalyzer**: 20개 기술적 지표
- ✅ **SignalDetector**: 종목별 최적 골든크로스 감지
- ✅ **GoldenCrossBacktester**: 2년 백테스팅 검증
- ✅ **투자 점수 시스템**: 100점 만점 평가

### 성능 지표
- **분석 속도**: 0.5초 (486일 데이터)
- **정확도**: 시장 대비 +1.72%p
- **처리량**: 25.3 종목/초

## 🔌 Backend API 통합 계획

### 1. Spring Boot Controller 구현

#### AnalysisController.kt
```kotlin
@RestController
@RequestMapping("/api/v1/analysis")
class AnalysisController(
    private val analysisService: AnalysisService
) {
    
    @PostMapping("/{symbol}")
    fun analyzeStock(
        @PathVariable symbol: String,
        @RequestBody request: AnalysisRequest
    ): ResponseEntity<AnalysisResponse> {
        
        val result = analysisService.runPythonAnalysis(
            symbol = symbol,
            period = request.period ?: 730,
            includeBacktest = request.includeBacktest ?: true
        )
        
        return ResponseEntity.ok(result)
    }
    
    @GetMapping("/{symbol}/history")
    fun getAnalysisHistory(
        @PathVariable symbol: String,
        @RequestParam days: Int = 30
    ): ResponseEntity<List<AnalysisResult>> {
        // DB에서 분석 기록 조회
    }
    
    @GetMapping("/user/watchlist")
    fun getUserWatchlist(): ResponseEntity<List<WatchlistItem>> {
        // 사용자 관심종목 조회
    }
}
```

#### Python 프로세스 실행 방식
```kotlin
@Service
class AnalysisService {
    
    fun runPythonAnalysis(symbol: String, period: Int, includeBacktest: Boolean): AnalysisResponse {
        
        // 방법 1: ProcessBuilder 직접 실행
        val process = ProcessBuilder(
            "uv", "run", "python", 
            "trading_strategy/demo_single_stock_analysis.py",
            "--symbol", symbol,
            "--period", period.toString(),
            "--format", "json"
        ).start()
        
        val result = process.inputStream.bufferedReader().readText()
        val analysisData = objectMapper.readValue(result, AnalysisResponse::class.java)
        
        // DB 저장
        saveAnalysisResult(analysisData)
        
        return analysisData
    }
    
    // 방법 2: HTTP 통신 (FastAPI 서버)
    fun runPythonAnalysisViaHttp(symbol: String): AnalysisResponse {
        val response = restTemplate.postForObject(
            "http://localhost:8000/analysis",
            AnalysisRequest(symbol),
            AnalysisResponse::class.java
        )
        return response!!
    }
}
```

### 2. 데이터 모델 정의

#### Request/Response DTO
```kotlin
data class AnalysisRequest(
    val period: Int? = 730,
    val includeBacktest: Boolean? = true,
    val indicators: List<String>? = null
)

data class AnalysisResponse(
    val symbol: String,
    val symbolName: String,
    val analyzedAt: LocalDateTime,
    
    // 투자 평가
    val investmentScore: Double,        // 41.0
    val recommendation: String,         // "매수비추천"
    val riskLevel: String,             // "높음"
    
    // 현재 시장 데이터
    val currentPrice: Long,            // 69500
    val priceChange: Double,           // -1.70
    
    // 신호 정보
    val signal: SignalInfo,
    
    // 백테스팅 결과
    val backtest: BacktestResult,
    
    // 기술적 지표
    val indicators: TechnicalIndicators,
    
    // 메타 정보
    val analysisTime: Long,            // 500ms
    val dataQuality: String,           // "EXCELLENT"
    val dataDays: Int                  // 486
)

data class SignalInfo(
    val type: String,                  // "NONE", "GOLDEN_CROSS", "DEAD_CROSS"
    val confidence: String,            // "CONFIRMED", "TENTATIVE", "WEAK"
    val strength: Double,              // 0-100
    val reason: String?                // "SMA5가 SMA20 아래 위치"
)

data class BacktestResult(
    val totalReturn: Double,           // 0.02
    val trades: Int,                   // 10
    val winRate: Double,               // 20.0
    val maxProfit: Double,             // 6.90
    val maxLoss: Double,               // -7.55
    val vsMarket: Double               // +1.72
)

data class TechnicalIndicators(
    val rsi: Double,                   // 39.8
    val sma5: Long,                    // 69140
    val sma20: Long,                   // 70405
    val sma60: Long,                   // 65910
    val volatility: Double,            // 1.87
    val macd: Double,                  // 447.97
    val macdSignal: Double,            // 886.58
    val volumeRatio: Double            // 거래량 비율
)
```

### 3. 데이터베이스 설계

#### 분석 결과 저장 테이블
```sql
CREATE TABLE analysis_results (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    symbol VARCHAR(10) NOT NULL,
    symbol_name VARCHAR(50),
    analyzed_at TIMESTAMP NOT NULL,
    
    -- 투자 평가
    investment_score DECIMAL(5,2),
    recommendation VARCHAR(20),
    risk_level VARCHAR(20),
    
    -- 시장 데이터
    current_price BIGINT,
    price_change DECIMAL(5,2),
    
    -- 신호 정보
    signal_type VARCHAR(20),
    signal_confidence VARCHAR(20),
    signal_strength DECIMAL(5,2),
    signal_reason TEXT,
    
    -- 백테스팅 결과
    backtest_return DECIMAL(5,2),
    backtest_trades INTEGER,
    backtest_win_rate DECIMAL(5,2),
    backtest_max_profit DECIMAL(5,2),
    backtest_max_loss DECIMAL(5,2),
    backtest_vs_market DECIMAL(5,2),
    
    -- 기술적 지표
    rsi DECIMAL(5,2),
    sma5 BIGINT,
    sma20 BIGINT,
    sma60 BIGINT,
    volatility DECIMAL(5,2),
    macd DECIMAL(10,2),
    macd_signal DECIMAL(10,2),
    volume_ratio DECIMAL(5,2),
    
    -- 메타 정보
    analysis_time INTEGER,
    data_quality VARCHAR(20),
    data_days INTEGER,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 인덱스 생성
CREATE INDEX idx_analysis_symbol_date ON analysis_results(symbol, analyzed_at DESC);
CREATE INDEX idx_analysis_user_date ON analysis_results(user_id, analyzed_at DESC);
```

## 🎨 Frontend UI/UX 구현

### 1. 페이지 구조

#### `/analysis` - 분석 요청 페이지
```typescript
// pages/analysis/index.tsx
export default function AnalysisPage() {
  const [symbol, setSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  
  const handleAnalysis = async () => {
    setLoading(true)
    router.push(`/analysis/${symbol}/progress`)
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {/* 종목 검색 */}
        <StockSearchInput 
          value={symbol}
          onChange={setSymbol}
          placeholder="종목코드 또는 종목명 입력 (예: 005930, 삼성전자)"
        />
        
        {/* 인기 종목 바로가기 */}
        <PopularStocks onSelect={setSymbol} />
        
        {/* 분석 옵션 */}
        <AnalysisOptions />
        
        {/* 시작 버튼 */}
        <Button 
          onClick={handleAnalysis}
          className="w-full py-4 text-lg"
          disabled={!symbol || loading}
        >
          📊 AI 분석 시작하기
        </Button>
      </div>
    </div>
  )
}
```

#### `/analysis/[symbol]/progress` - 실시간 진행 화면
```typescript
// pages/analysis/[symbol]/progress.tsx
export default function AnalysisProgressPage() {
  const { symbol } = useRouter().query
  const [progress, setProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(1)
  const [logs, setLogs] = useState<string[]>([])
  
  useEffect(() => {
    // Server-Sent Events 또는 WebSocket으로 실시간 진행 상황 수신
    const eventSource = new EventSource(`/api/v1/analysis/${symbol}/stream`)
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setProgress(data.progress)
      setCurrentStep(data.step)
      setLogs(prev => [...prev, data.message])
      
      if (data.completed) {
        router.push(`/analysis/${symbol}/result`)
      }
    }
    
    return () => eventSource.close()
  }, [symbol])
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* 진행 바 */}
        <ProgressBar 
          steps={[
            "데이터 수집",
            "기술적 분석", 
            "신호 감지",
            "백테스팅",
            "최종 평가"
          ]}
          currentStep={currentStep}
          progress={progress}
        />
        
        {/* 실시간 로그 */}
        <LogViewer logs={logs} />
      </div>
    </div>
  )
}
```

#### `/analysis/[symbol]/result` - 결과 대시보드
```typescript
// pages/analysis/[symbol]/result.tsx
export default function AnalysisResultPage() {
  const { symbol } = useRouter().query
  const { data: analysis, loading } = useAnalysisResult(symbol as string)
  
  if (loading) return <LoadingSkeleton />
  
  return (
    <div className="container mx-auto px-4 py-8">
      {/* 헤더 */}
      <ResultHeader analysis={analysis} />
      
      {/* 메인 대시보드 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* 투자 점수 카드 */}
        <InvestmentScoreCard score={analysis.investmentScore} />
        
        {/* 현재 신호 카드 */}
        <SignalStatusCard signal={analysis.signal} />
        
        {/* 백테스팅 카드 */}
        <BacktestResultCard backtest={analysis.backtest} />
        
        {/* 기술적 지표 카드 */}
        <TechnicalIndicatorsCard indicators={analysis.indicators} />
      </div>
      
      {/* 차트 영역 */}
      <div className="mb-8">
        <TradingChartWithIndicators 
          symbol={symbol as string}
          analysis={analysis}
        />
      </div>
      
      {/* 액션 버튼 */}
      <ActionButtons 
        onAddToWatchlist={() => {}}
        onReAnalyze={() => {}}
        onShare={() => {}}
      />
    </div>
  )
}
```

### 2. 핵심 컴포넌트

#### 투자 점수 카드
```typescript
// components/analysis/InvestmentScoreCard.tsx
interface InvestmentScoreCardProps {
  score: number
  recommendation: string
  riskLevel: string
}

export function InvestmentScoreCard({ score, recommendation, riskLevel }: InvestmentScoreCardProps) {
  const scoreColor = score >= 70 ? 'text-green-500' : score >= 50 ? 'text-yellow-500' : 'text-red-500'
  const bgColor = score >= 70 ? 'bg-green-50' : score >= 50 ? 'bg-yellow-50' : 'bg-red-50'
  
  return (
    <Card className={`${bgColor} border-2`}>
      <CardContent className="text-center py-8">
        <h3 className="text-lg font-medium mb-4">투자 적합성 점수</h3>
        
        {/* 점수 게이지 */}
        <div className="relative w-32 h-32 mx-auto mb-4">
          <CircularProgress value={score} className={scoreColor} />
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-3xl font-bold ${scoreColor}`}>
              {score.toFixed(1)}
            </span>
          </div>
        </div>
        
        {/* 추천 등급 */}
        <div className="space-y-2">
          <Badge variant={score >= 70 ? 'default' : score >= 50 ? 'secondary' : 'destructive'}>
            {recommendation}
          </Badge>
          <p className="text-sm text-gray-600">
            리스크 수준: {riskLevel}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
```

#### 실시간 차트 통합
```typescript
// components/analysis/TradingChartWithIndicators.tsx
export function TradingChartWithIndicators({ symbol, analysis }: Props) {
  const { data: chartData } = useChartData(symbol, 730) // 2년 데이터
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>기술적 분석 차트</CardTitle>
      </CardHeader>
      <CardContent>
        <TradingChart
          data={chartData}
          symbol={symbol}
          indicators={{
            sma5: analysis.indicators.sma5,
            sma20: analysis.indicators.sma20,
            sma60: analysis.indicators.sma60,
            rsi: analysis.indicators.rsi
          }}
          signals={[
            // 골든크로스/데드크로스 포인트 표시
          ]}
          width="100%"
          height={400}
        />
        
        {/* 지표 범례 */}
        <div className="flex flex-wrap gap-4 mt-4">
          <LegendItem color="pink" label={`SMA5: ${analysis.indicators.sma5:,}원`} />
          <LegendItem color="yellow" label={`SMA20: ${analysis.indicators.sma20:,}원`} />
          <LegendItem color="white" label={`SMA60: ${analysis.indicators.sma60:,}원`} />
          <LegendItem color="blue" label={`RSI: ${analysis.indicators.rsi}`} />
        </div>
      </CardContent>
    </Card>
  )
}
```

### 3. 상태 관리

#### React Query를 이용한 데이터 관리
```typescript
// hooks/useAnalysis.ts
export function useAnalysisResult(symbol: string) {
  return useQuery({
    queryKey: ['analysis', symbol],
    queryFn: () => analysisApi.getResult(symbol),
    staleTime: 1000 * 60 * 60, // 1시간
  })
}

export function useRunAnalysis() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (symbol: string) => analysisApi.runAnalysis(symbol),
    onSuccess: (data, symbol) => {
      queryClient.setQueryData(['analysis', symbol], data)
    }
  })
}

// api/analysis.ts
export const analysisApi = {
  runAnalysis: (symbol: string): Promise<AnalysisResponse> =>
    fetch(`/api/v1/analysis/${symbol}`, { 
      method: 'POST',
      body: JSON.stringify({ period: 730, includeBacktest: true })
    }).then(res => res.json()),
    
  getResult: (symbol: string): Promise<AnalysisResponse> =>
    fetch(`/api/v1/analysis/${symbol}/latest`).then(res => res.json()),
    
  getHistory: (symbol: string, days: number = 30): Promise<AnalysisResult[]> =>
    fetch(`/api/v1/analysis/${symbol}/history?days=${days}`).then(res => res.json())
}
```

## 🔄 실시간 진행 표시 구현

### Server-Sent Events (SSE) 방식
```kotlin
// Spring Boot SSE Controller
@GetMapping("/{symbol}/stream", produces = ["text/event-stream"])
fun streamAnalysis(@PathVariable symbol: String): SseEmitter {
    val emitter = SseEmitter(Long.MAX_VALUE)
    
    // Python 프로세스 실행 및 진행 상황 스트리밍
    executor.execute {
        try {
            emitter.send("data: {\"step\": 1, \"progress\": 20, \"message\": \"데이터 수집 중...\"}\n\n")
            Thread.sleep(1000)
            
            emitter.send("data: {\"step\": 2, \"progress\": 40, \"message\": \"기술적 분석 중...\"}\n\n")
            Thread.sleep(1000)
            
            // ... 분석 완료
            emitter.send("data: {\"completed\": true, \"progress\": 100}\n\n")
            emitter.complete()
            
        } catch (e: Exception) {
            emitter.completeWithError(e)
        }
    }
    
    return emitter
}
```

## 📊 성능 최적화 전략

### 1. 응답 시간 최적화
- Python 프로세스 풀링
- 분석 결과 Redis 캐싱 (1시간)
- 차트 데이터 CDN 배포

### 2. 사용자 경험 최적화
- 스켈레톤 UI로 즉각적 피드백
- 점진적 결과 표시
- 오프라인 상태 처리

### 3. 확장성 고려
- 분석 작업 큐잉 (Redis Queue)
- 마이크로서비스 분리
- 데이터베이스 샤딩

## 🚀 단계별 구현 계획

### Week 1: 기본 통합
- [ ] Backend API Controller 구현
- [ ] Python 프로세스 실행 로직
- [ ] 기본 DB 스키마 생성
- [ ] Frontend 분석 요청 페이지

### Week 2: UI/UX 완성
- [ ] 실시간 진행 표시 (SSE)
- [ ] 결과 대시보드 UI
- [ ] 차트 통합 및 지표 표시
- [ ] 반응형 디자인 적용

### Week 3: 고급 기능
- [ ] 분석 히스토리 조회
- [ ] 관심종목 관리
- [ ] 종목 비교 기능
- [ ] 성과 추적 시스템

---

이 사양서를 바탕으로 강력한 AI 주식 분석 웹 서비스를 구축할 수 있습니다! 🚀