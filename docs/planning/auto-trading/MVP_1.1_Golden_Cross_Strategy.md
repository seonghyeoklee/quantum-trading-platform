# MVP 1.1 골든크로스 전략

## 전략 개요

골든크로스(Golden Cross)는 **단기 이동평균선이 장기 이동평균선을 상향 돌파**할 때 발생하는 매수 신호로, 기술적 분석에서 가장 기본적이면서도 널리 사용되는 전략 중 하나입니다.

### MVP 1.1에서 선택한 이유
1. **시각적 명확성**: 차트에서 쉽게 확인 가능한 직관적 신호
2. **구현 단순성**: 이동평균선 계산만으로 구현 가능
3. **검증된 효과**: 수십 년간 사용되어 온 전통적 기법
4. **기존 인프라 활용**: 현재 TradingChart.tsx에 이미 구현된 이동평균선 사용

## 기술적 정의

### 사용하는 이동평균선
- **단기선**: 5일 단순이동평균선 (Simple Moving Average, SMA)  
- **장기선**: 20일 단순이동평균선 (Simple Moving Average, SMA)

### 신호 발생 조건

#### 골든크로스 (매수 신호)
```
조건: SMA(5) > SMA(20) 이면서 전일에는 SMA(5) ≤ SMA(20) 인 상황
확인: 3일 연속 SMA(5) > SMA(20) 유지 시 신호 확정
```

#### 데드크로스 (매도 신호)  
```
조건: SMA(5) < SMA(20) 이면서 전일에는 SMA(5) ≥ SMA(20) 인 상황
확인: 3일 연속 SMA(5) < SMA(20) 유지 시 신호 확정
```

### 가짜 신호 방지
시장의 잦은 등락으로 인한 잦은 매매를 방지하기 위해 **3일 연속 조건 유지**를 필수로 합니다.

```
예시:
Day 1: SMA(5) = 70,000, SMA(20) = 69,500 → 골든크로스 발생 (대기)
Day 2: SMA(5) = 70,200, SMA(20) = 69,600 → 골든크로스 유지 (대기)  
Day 3: SMA(5) = 70,400, SMA(20) = 69,700 → 골든크로스 유지 (신호 확정!)
```

## 구현 아키텍처

### 데이터 플로우
```
실시간 가격 데이터 → 이동평균 계산 → 크로스 감지 → 신호 발생 → 모의 주문
        ↑                  ↓               ↓            ↓           ↓
   KIS API (1초)      Backend Service   신호 검증    사용자 알림   포트폴리오 업데이트
```

### 핵심 컴포넌트

#### 1. 이동평균 계산 엔진
```typescript
interface MovingAverageData {
  date: string;
  price: number;
  sma5: number;
  sma20: number;
  volume: number;
}

class MovingAverageCalculator {
  calculateSMA(prices: number[], period: number): number {
    if (prices.length < period) {
      throw new Error(`Not enough data points. Need ${period}, got ${prices.length}`);
    }
    
    const sum = prices.slice(-period).reduce((acc, price) => acc + price, 0);
    return sum / period;
  }
  
  async getMovingAverageData(symbol: string, days: number = 100): Promise<MovingAverageData[]> {
    // KIS API에서 과거 데이터 조회 (이동평균 계산을 위해 추가 데이터 필요)
    const extendedDays = days + 20; // 20일 이동평균을 위해 20일 추가
    const chartData = await kisChartService.getDomesticDailyChart(symbol, extendedDays);
    
    const result: MovingAverageData[] = [];
    
    for (let i = 19; i < chartData.length; i++) { // 20일부터 계산 가능
      const recentPrices = chartData.slice(0, i + 1).map(data => data.close);
      
      const sma5 = recentPrices.length >= 5 
        ? this.calculateSMA(recentPrices, 5)
        : null;
      const sma20 = this.calculateSMA(recentPrices, 20);
      
      if (sma5 !== null) {
        result.push({
          date: chartData[i].date,
          price: chartData[i].close,
          sma5,
          sma20,
          volume: chartData[i].volume
        });
      }
    }
    
    return result;
  }
}
```

#### 2. 크로스 신호 감지기
```typescript
interface CrossSignal {
  type: 'GOLDEN_CROSS' | 'DEAD_CROSS';
  date: string;
  price: number;
  sma5: number;
  sma20: number;
  confidence: 'TENTATIVE' | 'CONFIRMED';
  confirmationDays: number;
}

class GoldenCrossDetector {
  private signalHistory: Map<string, CrossSignal[]> = new Map();
  
  async detectCrossSignal(symbol: string): Promise<CrossSignal | null> {
    const maData = await this.movingAverageCalculator.getMovingAverageData(symbol, 30);
    
    if (maData.length < 4) {
      return null; // 최소 4일 데이터 필요 (3일 확인 + 현재)
    }
    
    const latest = maData[maData.length - 1];
    const previous = maData[maData.length - 2];
    
    // 크로스 발생 감지
    let crossType: 'GOLDEN_CROSS' | 'DEAD_CROSS' | null = null;
    
    if (previous.sma5 <= previous.sma20 && latest.sma5 > latest.sma20) {
      crossType = 'GOLDEN_CROSS';
    } else if (previous.sma5 >= previous.sma20 && latest.sma5 < latest.sma20) {
      crossType = 'DEAD_CROSS';
    }
    
    if (!crossType) {
      return null;
    }
    
    // 3일 연속 확인
    const confirmationDays = this.countConsecutiveDays(maData, crossType);
    const confidence = confirmationDays >= 3 ? 'CONFIRMED' : 'TENTATIVE';
    
    const signal: CrossSignal = {
      type: crossType,
      date: latest.date,
      price: latest.price,
      sma5: latest.sma5,
      sma20: latest.sma20,
      confidence,
      confirmationDays
    };
    
    // 신호 히스토리 저장
    const history = this.signalHistory.get(symbol) || [];
    history.push(signal);
    this.signalHistory.set(symbol, history);
    
    return signal;
  }
  
  private countConsecutiveDays(maData: MovingAverageData[], crossType: 'GOLDEN_CROSS' | 'DEAD_CROSS'): number {
    let count = 0;
    
    for (let i = maData.length - 1; i >= 0; i--) {
      const data = maData[i];
      
      if (crossType === 'GOLDEN_CROSS') {
        if (data.sma5 > data.sma20) {
          count++;
        } else {
          break;
        }
      } else {
        if (data.sma5 < data.sma20) {
          count++;
        } else {
          break;
        }
      }
    }
    
    return count;
  }
}
```

#### 3. 전략 실행 엔진
```typescript
interface GoldenCrossStrategy {
  id: string;
  symbol: string;
  symbolName: string;
  investmentAmount: number;
  stopLossPercent: number;
  isActive: boolean;
  
  // 전략별 설정
  confirmationDays: number;    // 기본값: 3일
  minimumVolume: number;       // 최소 거래량 조건
  maxPositionSize: number;     // 최대 보유 비중
}

class GoldenCrossExecutor {
  async executeStrategy(strategy: GoldenCrossStrategy): Promise<void> {
    // 현재 보유 포지션 확인
    const currentPosition = await this.portfolioManager.getPosition(strategy.symbol);
    
    // 신호 감지
    const signal = await this.crossDetector.detectCrossSignal(strategy.symbol);
    
    if (!signal || signal.confidence !== 'CONFIRMED') {
      return; // 확정 신호가 아니면 대기
    }
    
    // 추가 필터링 조건 확인
    if (!this.passesAdditionalFilters(signal, strategy)) {
      await this.logService.log(`신호 발생했으나 추가 조건 미충족: ${strategy.symbol}`);
      return;
    }
    
    if (signal.type === 'GOLDEN_CROSS' && !currentPosition) {
      // 매수 실행
      await this.executeBuyOrder(strategy, signal);
      
    } else if (signal.type === 'DEAD_CROSS' && currentPosition) {
      // 매도 실행
      await this.executeSellOrder(strategy, signal, currentPosition);
    }
  }
  
  private passesAdditionalFilters(signal: CrossSignal, strategy: GoldenCrossStrategy): boolean {
    // 1. 거래량 조건 확인 (평균 거래량의 80% 이상)
    if (signal.volume && signal.volume < strategy.minimumVolume) {
      return false;
    }
    
    // 2. 가격 상승폭 확인 (하루 15% 이상 급등 시 제외)
    const priceChange = Math.abs((signal.price - signal.sma20) / signal.sma20);
    if (priceChange > 0.15) {
      return false;
    }
    
    // 3. 이동평균선 간격 확인 (너무 가까우면 제외)
    const spreadPercent = Math.abs(signal.sma5 - signal.sma20) / signal.sma20;
    if (spreadPercent < 0.01) { // 1% 미만이면 제외
      return false;
    }
    
    return true;
  }
  
  private async executeBuyOrder(strategy: GoldenCrossStrategy, signal: CrossSignal): Promise<void> {
    const currentPrice = await this.priceService.getCurrentPrice(strategy.symbol);
    const quantity = Math.floor(strategy.investmentAmount / currentPrice);
    
    const order: VirtualOrder = {
      id: uuidv4(),
      strategyId: strategy.id,
      type: 'BUY',
      symbol: strategy.symbol,
      requestPrice: currentPrice,
      quantity,
      requestTime: new Date(),
      status: 'PENDING'
    };
    
    const result = await this.virtualOrderEngine.placeOrder(order);
    
    // 알림 발송
    await this.notificationService.sendBuySignal({
      strategyId: strategy.id,
      symbol: strategy.symbol,
      symbolName: strategy.symbolName,
      price: result.executionPrice,
      quantity: result.executedQuantity,
      totalAmount: result.totalAmount,
      reason: '골든크로스 신호 확정'
    });
    
    await this.logService.log(
      `매수 실행: ${strategy.symbolName} ${result.executedQuantity}주 @ ${result.executionPrice}원`
    );
  }
  
  private async executeSellOrder(
    strategy: GoldenCrossStrategy, 
    signal: CrossSignal, 
    position: VirtualPosition
  ): Promise<void> {
    const currentPrice = await this.priceService.getCurrentPrice(strategy.symbol);
    
    const order: VirtualOrder = {
      id: uuidv4(),
      strategyId: strategy.id,
      type: 'SELL',
      symbol: strategy.symbol,
      requestPrice: currentPrice,
      quantity: position.quantity, // 전량 매도
      requestTime: new Date(),
      status: 'PENDING'
    };
    
    const result = await this.virtualOrderEngine.placeOrder(order);
    
    // 수익률 계산
    const profitLoss = (result.executionPrice - position.averagePrice) * result.executedQuantity;
    const profitLossPercent = (profitLoss / (position.averagePrice * result.executedQuantity)) * 100;
    
    // 알림 발송
    await this.notificationService.sendSellSignal({
      strategyId: strategy.id,
      symbol: strategy.symbol,
      symbolName: strategy.symbolName,
      price: result.executionPrice,
      quantity: result.executedQuantity,
      totalAmount: result.totalAmount,
      profitLoss,
      profitLossPercent,
      reason: '데드크로스 신호 확정'
    });
    
    await this.logService.log(
      `매도 실행: ${strategy.symbolName} ${result.executedQuantity}주 @ ${result.executionPrice}원 (${profitLossPercent.toFixed(2)}%)`
    );
  }
}
```

### 4. 손절 관리 시스템
```typescript
class StopLossManager {
  async checkStopLoss(strategy: GoldenCrossStrategy): Promise<void> {
    const position = await this.portfolioManager.getPosition(strategy.symbol);
    
    if (!position || position.quantity === 0) {
      return;
    }
    
    const currentPrice = await this.priceService.getCurrentPrice(strategy.symbol);
    const lossPercent = ((currentPrice - position.averagePrice) / position.averagePrice) * 100;
    
    // 손절 조건 확인
    if (lossPercent <= strategy.stopLossPercent) {
      await this.executeStopLossOrder(strategy, position, currentPrice, lossPercent);
    }
  }
  
  private async executeStopLossOrder(
    strategy: GoldenCrossStrategy,
    position: VirtualPosition,
    currentPrice: number,
    lossPercent: number
  ): Promise<void> {
    const order: VirtualOrder = {
      id: uuidv4(),
      strategyId: strategy.id,
      type: 'SELL',
      symbol: strategy.symbol,
      requestPrice: currentPrice,
      quantity: position.quantity,
      requestTime: new Date(),
      status: 'PENDING'
    };
    
    const result = await this.virtualOrderEngine.placeOrder(order);
    
    await this.notificationService.sendStopLossSignal({
      strategyId: strategy.id,
      symbol: strategy.symbol,
      symbolName: strategy.symbolName,
      price: result.executionPrice,
      quantity: result.executedQuantity,
      lossPercent: lossPercent,
      reason: `손절 조건 도달 (${strategy.stopLossPercent}%)`
    });
    
    await this.logService.log(
      `손절 실행: ${strategy.symbolName} ${result.executedQuantity}주 @ ${result.executionPrice}원 (${lossPercent.toFixed(2)}%)`
    );
  }
}
```

## 실시간 모니터링 시스템

### 모니터링 주기
- **시장 시간 중 (09:00-15:30)**: 30초마다 체크
- **시장 시간 외**: 1시간마다 체크 (다음 날 준비)

### 모니터링 대시보드
```tsx
function GoldenCrossMonitor({ strategyId }: Props) {
  const [strategy, setStrategy] = useState<GoldenCrossStrategy | null>(null);
  const [currentSignal, setCurrentSignal] = useState<CrossSignal | null>(null);
  const [maData, setMAData] = useState<MovingAverageData[]>([]);
  const [isMarketOpen, setIsMarketOpen] = useState(false);
  
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isMarketOpen) {
      // 시장 시간 중: 30초마다 업데이트
      interval = setInterval(async () => {
        const signal = await fetchCurrentSignal(strategyId);
        setCurrentSignal(signal);
        
        const maData = await fetchMovingAverageData(strategyId);
        setMAData(maData);
      }, 30000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [strategyId, isMarketOpen]);
  
  return (
    <div className="space-y-6">
      {/* 전략 상태 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">{strategy?.symbolName} 골든크로스 전략</h2>
            <div className="text-sm text-gray-600">
              {strategy?.symbol} | 투자금액: {strategy?.investmentAmount.toLocaleString()}원
            </div>
          </div>
          
          <div className={`px-4 py-2 rounded-full text-sm font-medium ${
            strategy?.isActive 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-800'
          }`}>
            {strategy?.isActive ? '🟢 실행 중' : '⏸️ 일시정지'}
          </div>
        </div>
      </div>
      
      {/* 현재 신호 상태 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">📊 현재 신호 상태</h3>
        
        {currentSignal ? (
          <div className="space-y-3">
            <div className={`p-4 rounded-lg ${
              currentSignal.type === 'GOLDEN_CROSS' 
                ? 'bg-yellow-50 border border-yellow-200'
                : 'bg-blue-50 border border-blue-200'
            }`}>
              <div className="flex items-center gap-3">
                <div className="text-2xl">
                  {currentSignal.type === 'GOLDEN_CROSS' ? '📈' : '📉'}
                </div>
                <div>
                  <div className="font-semibold">
                    {currentSignal.type === 'GOLDEN_CROSS' ? '골든크로스' : '데드크로스'} 
                    {currentSignal.confidence === 'CONFIRMED' ? ' 확정' : ' 대기'}
                  </div>
                  <div className="text-sm text-gray-600">
                    확인일수: {currentSignal.confirmationDays}/3일
                  </div>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-600">현재가</div>
                <div className="font-semibold">{currentSignal.price.toLocaleString()}원</div>
              </div>
              <div>
                <div className="text-gray-600">5일선</div>
                <div className="font-semibold text-pink-600">
                  {currentSignal.sma5.toLocaleString()}원
                </div>
              </div>
              <div>
                <div className="text-gray-600">20일선</div>
                <div className="font-semibold text-yellow-600">
                  {currentSignal.sma20.toLocaleString()}원
                </div>
              </div>
              <div>
                <div className="text-gray-600">차이</div>
                <div className={`font-semibold ${
                  currentSignal.sma5 > currentSignal.sma20 ? 'text-red-600' : 'text-blue-600'
                }`}>
                  {((currentSignal.sma5 - currentSignal.sma20) / currentSignal.sma20 * 100).toFixed(2)}%
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            현재 신호가 없습니다. 계속 모니터링 중...
          </div>
        )}
      </div>
      
      {/* 이동평균선 차트 미니뷰 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">📈 이동평균선 추이</h3>
        <div className="h-64">
          <MovingAverageChart data={maData} />
        </div>
      </div>
      
      {/* 최근 신호 히스토리 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">📋 신호 히스토리</h3>
        <SignalHistoryTable strategyId={strategyId} />
      </div>
    </div>
  );
}
```

## 성과 분석

### 골든크로스 전략 특성
- **장점**: 
  - 명확한 추세 전환 신호
  - 큰 상승장에서 효과적
  - 장기 보유 전략에 적합
  
- **단점**:
  - 횡보장에서 많은 거짓 신호 발생
  - 신호 발생이 늦어 초기 상승 구간 놓칠 수 있음
  - 급변하는 시장에서는 늦은 반응

### 기대 성과 지표
- **승률**: 40-60% (시장 상황에 따라 변동)
- **평균 수익률**: 단일 거래당 5-15%
- **최대 손실**: 설정한 손절률에 의해 제한 (-5% ~ -10%)
- **연간 거래 횟수**: 5-15회 (종목에 따라 다름)

## 다음 단계 확장 계획

### MVP 1.2에서 추가할 기능
1. **RSI 필터**: 골든크로스 + RSI 30 이하에서 매수
2. **거래량 확인**: 평균 거래량 대비 일정 수준 이상일 때만 신호 확정
3. **변동성 필터**: 변동성이 너무 클 때는 신호 무시

### MVP 1.3에서 실전 적용
1. **실제 KIS API 주문 연동**
2. **포지션 사이징**: 전략별 투자 비중 관리
3. **리스크 관리**: 전체 포트폴리오 관점의 위험 관리

이렇게 **검증된 골든크로스 전략**을 기반으로 사용자는 자동매매의 기본기를 익히고, 점진적으로 더 정교한 전략으로 발전시킬 수 있습니다.