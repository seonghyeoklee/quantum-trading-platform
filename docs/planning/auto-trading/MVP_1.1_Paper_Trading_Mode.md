# MVP 1.1 모의투자 모드

## 모의투자 모드 개요

모의투자 모드는 **실제 돈을 사용하지 않고** 가상의 자금으로 자동매매 시스템을 체험할 수 있는 핵심 기능입니다. 사용자는 실제 시장 데이터를 기반으로 한 시뮬레이션을 통해 자동매매 전략의 효과를 안전하게 검증할 수 있습니다.

## 핵심 원칙

### 1. 실제 시장 데이터 사용
- **실시간 가격**: KIS API에서 제공하는 실제 시장 가격 사용
- **실시간 호가**: 실제 매수/매도 호가 정보 활용
- **시장 시간**: 실제 거래시간(09:00-15:30)에만 모의거래 실행

### 2. 현실적인 거래 조건
- **체결 가격**: 호가 스프레드를 고려한 현실적 체결 가격
- **거래량 제한**: 실제 거래량 범위 내에서 모의거래 가능
- **거래 수수료**: 실제 증권사 수수료 반영 (KIS 기준)

### 3. 투명한 결과 제공
- **모든 거래 기록**: 매수/매도 시점, 가격, 수량 상세 기록
- **수익률 계산**: 실시간 평가손익 및 실현손익 분리 계산
- **성과 분석**: 승률, 평균 수익률, 최대 낙폭 등 통계 제공

## 시스템 아키텍처

### 데이터 플로우
```
실시간 시장 데이터 → 전략 엔진 → 신호 발생 → 모의 주문 → 가상 포트폴리오 업데이트
        ↑                ↓            ↓           ↓              ↓
   KIS API (실제)    Backend Logic   UI 알림    가상 주문 처리    수익률 계산
```

### 핵심 컴포넌트

#### 1. 가상 주문 처리 엔진
```typescript
interface VirtualOrder {
  id: string;
  strategyId: string;
  type: 'BUY' | 'SELL';
  symbol: string;
  requestPrice: number;    // 주문 요청 가격
  quantity: number;        // 주문 수량
  requestTime: Date;       // 주문 요청 시간
  
  // 체결 결과
  executionPrice?: number; // 실제 체결 가격
  executedQuantity?: number; // 체결 수량
  executionTime?: Date;    // 체결 시간
  status: 'PENDING' | 'EXECUTED' | 'PARTIALLY_EXECUTED' | 'CANCELLED';
  
  // 수수료 및 세금
  commission: number;      // 거래 수수료
  tax: number;            // 거래세 (매도시)
  totalAmount: number;     // 총 거래 금액
}

class VirtualOrderEngine {
  async placeOrder(order: VirtualOrder): Promise<VirtualOrderResult> {
    // 1. 시장 시간 확인
    if (!this.isMarketOpen()) {
      throw new Error('장외시간에는 주문할 수 없습니다');
    }
    
    // 2. 현재 호가 정보 조회
    const orderbook = await this.getOrderbook(order.symbol);
    
    // 3. 체결 가격 결정
    const executionPrice = this.determineExecutionPrice(order, orderbook);
    
    // 4. 수수료 계산
    const commission = this.calculateCommission(executionPrice * order.quantity);
    const tax = order.type === 'SELL' ? this.calculateTax(executionPrice * order.quantity) : 0;
    
    // 5. 가상 주문 체결
    return {
      ...order,
      executionPrice,
      executedQuantity: order.quantity,
      executionTime: new Date(),
      status: 'EXECUTED',
      commission,
      tax,
      totalAmount: executionPrice * order.quantity + commission + tax
    };
  }
  
  private determineExecutionPrice(order: VirtualOrder, orderbook: Orderbook): number {
    if (order.type === 'BUY') {
      // 매수 주문: 매도 1호가로 체결 (현실적)
      return orderbook.askPrice1;
    } else {
      // 매도 주문: 매수 1호가로 체결 (현실적)
      return orderbook.bidPrice1;
    }
  }
}
```

#### 2. 가상 포트폴리오 관리자
```typescript
interface VirtualPosition {
  symbol: string;
  symbolName: string;
  quantity: number;        // 보유 수량
  averagePrice: number;    // 평균 매수가
  currentPrice: number;    // 현재가
  
  // 손익 계산
  totalCost: number;       // 총 매수 비용 (수수료 포함)
  currentValue: number;    // 현재 평가 금액
  unrealizedPnL: number;   // 평가 손익
  unrealizedPnLPercent: number; // 평가 수익률
  
  // 매매 기록
  buyTransactions: VirtualTransaction[];
  sellTransactions: VirtualTransaction[];
  
  updatedAt: Date;
}

interface VirtualTransaction {
  id: string;
  type: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  commission: number;
  tax: number;
  totalAmount: number;
  executedAt: Date;
  strategyId: string;
}

class VirtualPortfolioManager {
  async updatePosition(order: VirtualOrderResult): Promise<VirtualPosition> {
    const position = await this.getPosition(order.symbol) || this.createNewPosition(order.symbol);
    
    if (order.type === 'BUY') {
      // 매수: 평균단가 재계산
      const newTotalCost = position.totalCost + order.totalAmount;
      const newQuantity = position.quantity + order.executedQuantity;
      position.averagePrice = newTotalCost / newQuantity;
      position.quantity = newQuantity;
      position.totalCost = newTotalCost;
      
      // 매수 거래 기록
      position.buyTransactions.push({
        id: order.id,
        type: 'BUY',
        price: order.executionPrice,
        quantity: order.executedQuantity,
        commission: order.commission,
        tax: order.tax,
        totalAmount: order.totalAmount,
        executedAt: order.executionTime,
        strategyId: order.strategyId
      });
      
    } else {
      // 매도: 수량 차감 및 실현손익 계산
      position.quantity -= order.executedQuantity;
      
      // 실현손익 = (매도가 - 평균단가) * 매도수량 - 수수료 - 세금
      const realizedPnL = (order.executionPrice - position.averagePrice) * order.executedQuantity - order.commission - order.tax;
      
      // 매도 거래 기록
      position.sellTransactions.push({
        id: order.id,
        type: 'SELL',
        price: order.executionPrice,
        quantity: order.executedQuantity,
        commission: order.commission,
        tax: order.tax,
        totalAmount: order.totalAmount,
        executedAt: order.executionTime,
        strategyId: order.strategyId
      });
      
      // 실현손익 기록
      await this.recordRealizedPnL(order.strategyId, realizedPnL);
    }
    
    // 현재가 업데이트 및 평가손익 계산
    position.currentPrice = await this.getCurrentPrice(order.symbol);
    position.currentValue = position.quantity * position.currentPrice;
    position.unrealizedPnL = position.currentValue - (position.averagePrice * position.quantity);
    position.unrealizedPnLPercent = (position.unrealizedPnL / (position.averagePrice * position.quantity)) * 100;
    position.updatedAt = new Date();
    
    return await this.savePosition(position);
  }
}
```

#### 3. 실시간 평가손익 계산기
```typescript
class PnLCalculator {
  async calculateRealTimePnL(strategyId: string): Promise<StrategyPnL> {
    const positions = await this.getPositions(strategyId);
    const realizedTransactions = await this.getRealizedTransactions(strategyId);
    
    let totalUnrealizedPnL = 0;
    let totalCurrentValue = 0;
    let totalCost = 0;
    
    // 보유 포지션의 평가손익 계산
    for (const position of positions) {
      const currentPrice = await this.getCurrentPrice(position.symbol);
      const currentValue = position.quantity * currentPrice;
      const positionCost = position.averagePrice * position.quantity;
      
      totalUnrealizedPnL += (currentValue - positionCost);
      totalCurrentValue += currentValue;
      totalCost += positionCost;
    }
    
    // 실현손익 합계
    const totalRealizedPnL = realizedTransactions.reduce((sum, tx) => sum + tx.realizedPnL, 0);
    
    // 전체 손익 계산
    const totalPnL = totalRealizedPnL + totalUnrealizedPnL;
    const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;
    
    return {
      strategyId,
      totalInvestment: totalCost,
      currentValue: totalCurrentValue,
      realizedPnL: totalRealizedPnL,
      unrealizedPnL: totalUnrealizedPnL,
      totalPnL,
      totalPnLPercent,
      updatedAt: new Date()
    };
  }
}
```

## 수수료 및 세금 계산

### 실제 KIS 수수료 구조 반영
```typescript
class FeeCalculator {
  // KIS 증권 온라인 수수료 (2024년 기준)
  calculateCommission(amount: number, market: 'domestic' | 'overseas'): number {
    if (market === 'domestic') {
      // 국내 주식: 0.015% (최소 1,000원)
      const commission = amount * 0.00015;
      return Math.max(commission, 1000);
    } else {
      // 해외 주식: 0.25% (최소 $15)
      const commission = amount * 0.0025;
      return Math.max(commission, 15); // USD 기준
    }
  }
  
  calculateTax(sellAmount: number, market: 'domestic' | 'overseas'): number {
    if (market === 'domestic') {
      // 국내 주식 거래세: 0.3%
      return sellAmount * 0.003;
    } else {
      // 해외 주식: 거래세 없음
      return 0;
    }
  }
  
  // 실제 순수익 계산 (수수료 및 세금 차감 후)
  calculateNetProfit(buyAmount: number, sellAmount: number, market: 'domestic' | 'overseas'): number {
    const buyCommission = this.calculateCommission(buyAmount, market);
    const sellCommission = this.calculateCommission(sellAmount, market);
    const sellTax = this.calculateTax(sellAmount, market);
    
    return sellAmount - buyAmount - buyCommission - sellCommission - sellTax;
  }
}
```

## 현실적인 체결 시뮬레이션

### 호가 스프레드 고려
```typescript
class ExecutionSimulator {
  // 실제 호가창을 고려한 체결가 결정
  async simulateExecution(order: VirtualOrder): Promise<ExecutionResult> {
    const orderbook = await this.getOrderbook(order.symbol);
    
    if (order.type === 'BUY') {
      // 매수 주문: 일반적으로 매도 1호가에 체결
      const executionPrice = orderbook.askPrice1;
      const availableQuantity = orderbook.askQuantity1;
      
      // 주문 수량이 호가 수량보다 큰 경우 부분 체결
      const executedQuantity = Math.min(order.quantity, availableQuantity);
      
      return {
        executionPrice,
        executedQuantity,
        status: executedQuantity === order.quantity ? 'FULLY_EXECUTED' : 'PARTIALLY_EXECUTED'
      };
    } else {
      // 매도 주문: 일반적으로 매수 1호가에 체결
      const executionPrice = orderbook.bidPrice1;
      const availableQuantity = orderbook.bidQuantity1;
      
      const executedQuantity = Math.min(order.quantity, availableQuantity);
      
      return {
        executionPrice,
        executedQuantity,
        status: executedQuantity === order.quantity ? 'FULLY_EXECUTED' : 'PARTIALLY_EXECUTED'
      };
    }
  }
  
  // 시장 충격 고려 (대량 주문 시)
  calculateMarketImpact(order: VirtualOrder, orderbook: Orderbook): number {
    const totalVolume = orderbook.totalVolume;
    const orderRatio = (order.quantity / totalVolume) * 100;
    
    // 전체 거래량의 1% 이상인 경우 슬리피지 발생
    if (orderRatio > 1.0) {
      return 0.001 * orderRatio; // 0.1%씩 슬리피지 증가
    }
    
    return 0;
  }
}
```

## 사용자 인터페이스

### 모의투자 대시보드
```tsx
function PaperTradingDashboard({ strategyId }: Props) {
  const [pnl, setPnL] = useState<StrategyPnL | null>(null);
  const [positions, setPositions] = useState<VirtualPosition[]>([]);
  const [recentOrders, setRecentOrders] = useState<VirtualOrder[]>([]);
  
  useEffect(() => {
    // 실시간 손익 업데이트 (30초마다)
    const interval = setInterval(async () => {
      const latestPnL = await fetchPnL(strategyId);
      setPnL(latestPnL);
    }, 30000);
    
    return () => clearInterval(interval);
  }, [strategyId]);
  
  return (
    <div className="space-y-6">
      {/* 전체 손익 요약 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">📊 모의투자 현황</h2>
        
        {pnl && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {pnl.totalInvestment.toLocaleString()}원
              </div>
              <div className="text-sm text-gray-600">투자 원금</div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {pnl.currentValue.toLocaleString()}원
              </div>
              <div className="text-sm text-gray-600">현재 평가액</div>
            </div>
            
            <div className="text-center">
              <div className={`text-2xl font-bold ${
                pnl.totalPnL >= 0 ? 'text-red-600' : 'text-blue-600'
              }`}>
                {pnl.totalPnL >= 0 ? '+' : ''}{pnl.totalPnL.toLocaleString()}원
              </div>
              <div className="text-sm text-gray-600">총 손익</div>
            </div>
            
            <div className="text-center">
              <div className={`text-2xl font-bold ${
                pnl.totalPnLPercent >= 0 ? 'text-red-600' : 'text-blue-600'
              }`}>
                {pnl.totalPnLPercent >= 0 ? '+' : ''}{pnl.totalPnLPercent.toFixed(2)}%
              </div>
              <div className="text-sm text-gray-600">수익률</div>
            </div>
          </div>
        )}
      </div>
      
      {/* 보유 포지션 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">📈 보유 종목</h3>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">종목</th>
                <th className="text-right p-2">수량</th>
                <th className="text-right p-2">평균가</th>
                <th className="text-right p-2">현재가</th>
                <th className="text-right p-2">평가손익</th>
                <th className="text-right p-2">수익률</th>
              </tr>
            </thead>
            <tbody>
              {positions.map(position => (
                <tr key={position.symbol} className="border-b">
                  <td className="p-2">
                    <div>
                      <div className="font-medium">{position.symbolName}</div>
                      <div className="text-gray-500">{position.symbol}</div>
                    </div>
                  </td>
                  <td className="text-right p-2">{position.quantity}주</td>
                  <td className="text-right p-2">{position.averagePrice.toLocaleString()}원</td>
                  <td className="text-right p-2">{position.currentPrice.toLocaleString()}원</td>
                  <td className={`text-right p-2 ${
                    position.unrealizedPnL >= 0 ? 'text-red-600' : 'text-blue-600'
                  }`}>
                    {position.unrealizedPnL >= 0 ? '+' : ''}{position.unrealizedPnL.toLocaleString()}원
                  </td>
                  <td className={`text-right p-2 ${
                    position.unrealizedPnLPercent >= 0 ? 'text-red-600' : 'text-blue-600'
                  }`}>
                    {position.unrealizedPnLPercent >= 0 ? '+' : ''}{position.unrealizedPnLPercent.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* 최근 거래 내역 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">📋 최근 거래</h3>
        
        <div className="space-y-2">
          {recentOrders.map(order => (
            <div key={order.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <div className="font-medium">
                  {order.type === 'BUY' ? '매수' : '매도'} {order.symbol}
                </div>
                <div className="text-sm text-gray-600">
                  {order.executedQuantity}주 × {order.executionPrice?.toLocaleString()}원
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600">
                  {format(order.executionTime, 'MM/dd HH:mm')}
                </div>
                <div className={order.type === 'BUY' ? 'text-red-600' : 'text-blue-600'}>
                  {order.totalAmount.toLocaleString()}원
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

## 성과 분석 및 리포팅

### 주요 성과 지표
```typescript
interface PerformanceMetrics {
  // 기본 수익률 지표
  totalReturn: number;           // 총 수익률
  annualizedReturn: number;      // 연환산 수익률
  
  // 리스크 지표
  volatility: number;            // 변동성 (표준편차)
  maxDrawdown: number;           // 최대 낙폭
  sharpeRatio: number;           // 샤프 비율
  
  // 거래 성과 지표
  winRate: number;               // 승률
  profitFactor: number;          // 수익/손실 비율
  averageWin: number;            // 평균 수익
  averageLoss: number;           // 평균 손실
  
  // 거래 빈도
  totalTrades: number;           // 총 거래 횟수
  tradesPerMonth: number;        // 월 평균 거래 횟수
  
  // 벤치마크 대비
  benchmarkReturn: number;       // 벤치마크 수익률 (코스피/S&P500)
  alpha: number;                 // 알파 (초과 수익률)
  beta: number;                  // 베타 (시장 민감도)
}
```

## 실전 전환 준비

### 실전 모드로의 안전한 전환
1. **충분한 모의투자 경험**: 최소 3개월 이상 모의투자 실행
2. **안정적인 수익률**: 모의투자에서 +수익률 달성
3. **전략 이해도**: 손실 상황에 대한 대처 방안 숙지
4. **자금 관리**: 실제 투자 가능한 여유 자금 확보

### 실전 전환 체크리스트
```
□ 모의투자 기간: 3개월 이상
□ 모의투자 수익률: +5% 이상
□ 최대 낙폭 경험: -10% 이상 상황 대처 경험
□ 거래 빈도: 월 5회 이상 안정적 거래
□ 전략 이해도: 골든크로스/데드크로스 원리 완전 이해
□ 리스크 관리: 손절 규칙 철저히 준수
□ 자금 여유도: 투자금액이 전체 자산의 10% 이하
```

## 다음 단계

모의투자 모드를 통해 검증된 전략은:

1. **MVP 1.2**에서 더 정교한 전략으로 발전
2. **MVP 1.3**에서 실제 거래 모드로 전환  
3. **MVP 2.0**에서 AI 기반 고도화된 전략으로 진화

이렇게 **안전하고 현실적인 모의투자 시스템**을 통해 사용자는 자동매매의 위험과 기회를 충분히 학습한 후 실전에 임할 수 있습니다.