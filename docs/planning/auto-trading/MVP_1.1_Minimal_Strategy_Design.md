# MVP 1.1 최소 전략 설계

## 설계 철학

**"복잡함을 피하고 단순함을 추구한다"**

MVP 1.1은 사용자가 자동매매의 기본 개념을 이해하고 경험할 수 있도록 **가장 간단하면서도 효과적인 전략 하나**에 집중합니다.

## 전략 선정 근거

### 왜 골든크로스인가?

1. **직관적 이해**: 초보자도 쉽게 이해할 수 있는 시각적 신호
2. **검증된 효과**: 전통적으로 널리 사용되는 기술적 분석 도구
3. **구현 단순성**: 이동평균선 계산만으로 구현 가능
4. **확장 가능성**: 향후 복합 전략의 기본 구성 요소

### 기존 차트 시스템과의 연계
현재 TradingChart.tsx에서 이미 구현된 기능을 활용:
- ✅ 5일 이동평균선 (분홍색)
- ✅ 20일 이동평균선 (노란색)
- ✅ 실시간 데이터 업데이트
- ✅ 차트 시각화

## 전략 설정 마법사

### Step-by-Step UI 플로우

```typescript
interface StrategyWizardStep {
  step: number;
  title: string;
  description: string;
  component: React.Component;
  validation: ValidationRule[];
}

const STRATEGY_WIZARD_STEPS: StrategyWizardStep[] = [
  {
    step: 1,
    title: "거래 모드 선택",
    description: "모의투자로 안전하게 시작하세요",
    component: TradingModeSelector,
    validation: [] // 현재는 모의투자 고정
  },
  {
    step: 2, 
    title: "시장 선택",
    description: "국내 또는 해외 시장을 선택하세요",
    component: MarketSelector,
    validation: [{ required: true, message: "시장을 선택해주세요" }]
  },
  {
    step: 3,
    title: "종목 선택", 
    description: "투자하고 싶은 종목을 선택하세요",
    component: StockSelector,
    validation: [{ required: true, message: "종목을 선택해주세요" }]
  },
  {
    step: 4,
    title: "전략 확인",
    description: "골든크로스 전략을 사용합니다",
    component: StrategyConfirm,
    validation: [] // 현재는 골든크로스 고정
  },
  {
    step: 5,
    title: "투자 설정",
    description: "투자금액과 리스크를 설정하세요",
    component: InvestmentSettings,
    validation: [
      { required: true, message: "투자금액을 입력해주세요" },
      { min: 10000, message: "최소 1만원 이상 입력해주세요" },
      { max: 10000000, message: "최대 1천만원까지 설정 가능합니다" }
    ]
  }
];
```

### 1단계: 거래 모드 선택

```tsx
function TradingModeSelector({ value, onChange }: Props) {
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            📊
          </div>
          <div>
            <h3 className="font-semibold text-blue-900">모의투자 모드</h3>
            <p className="text-sm text-blue-700">
              실제 돈을 사용하지 않고 가상으로 투자를 체험합니다
            </p>
          </div>
          <div className="ml-auto">
            <input 
              type="radio" 
              name="tradingMode" 
              value="paper" 
              checked={true} 
              disabled 
              className="w-5 h-5"
            />
          </div>
        </div>
      </div>
      
      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 opacity-50">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
            💰
          </div>
          <div>
            <h3 className="font-semibold text-gray-600">실전 투자 모드</h3>
            <p className="text-sm text-gray-500">
              실제 돈으로 투자합니다 (MVP 1.3에서 지원 예정)
            </p>
          </div>
          <div className="ml-auto">
            <span className="text-xs bg-gray-200 px-2 py-1 rounded">준비중</span>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 2단계: 시장 선택

```tsx
function MarketSelector({ value, onChange }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <button 
        onClick={() => onChange('domestic')}
        className={`p-6 rounded-lg border-2 transition-all ${
          value === 'domestic' 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-200 hover:border-gray-300'
        }`}
      >
        <div className="text-center space-y-2">
          <div className="text-2xl">🇰🇷</div>
          <h3 className="font-semibold">국내 주식</h3>
          <p className="text-sm text-gray-600">
            코스피, 코스닥 상장 종목
          </p>
          <div className="text-xs text-gray-500">
            삼성전자, SK하이닉스, NAVER 등
          </div>
        </div>
      </button>
      
      <button 
        onClick={() => onChange('overseas')}
        className={`p-6 rounded-lg border-2 transition-all ${
          value === 'overseas' 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-200 hover:border-gray-300'
        }`}
      >
        <div className="text-center space-y-2">
          <div className="text-2xl">🇺🇸</div>
          <h3 className="font-semibold">해외 주식</h3>
          <p className="text-sm text-gray-600">
            미국, 일본, 홍콩 상장 종목
          </p>
          <div className="text-xs text-gray-500">
            Apple, Tesla, Microsoft 등
          </div>
        </div>
      </button>
    </div>
  );
}
```

### 3단계: 종목 선택

```tsx
interface StockOption {
  symbol: string;
  name: string;
  market: string;
  currentPrice?: number;
  change?: number;
  changePercent?: number;
  popular?: boolean;
}

const DOMESTIC_STOCKS: StockOption[] = [
  { symbol: '005930', name: '삼성전자', market: 'KOSPI', popular: true },
  { symbol: '000660', name: 'SK하이닉스', market: 'KOSPI', popular: true },
  { symbol: '035420', name: 'NAVER', market: 'KOSPI', popular: true },
  { symbol: '035720', name: '카카오', market: 'KOSPI', popular: true },
  { symbol: '005380', name: '현대차', market: 'KOSPI' },
  { symbol: '207940', name: '삼성바이오로직스', market: 'KOSPI' },
  { symbol: '051910', name: 'LG화학', market: 'KOSPI' },
  { symbol: '006400', name: '삼성SDI', market: 'KOSPI' },
];

const OVERSEAS_STOCKS: StockOption[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', market: 'NASDAQ', popular: true },
  { symbol: 'TSLA', name: 'Tesla Inc.', market: 'NASDAQ', popular: true },
  { symbol: 'MSFT', name: 'Microsoft Corporation', market: 'NASDAQ', popular: true },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', market: 'NASDAQ', popular: true },
  { symbol: 'NVDA', name: 'NVIDIA Corporation', market: 'NASDAQ' },
  { symbol: 'META', name: 'Meta Platforms Inc.', market: 'NASDAQ' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', market: 'NASDAQ' },
  { symbol: 'NFLX', name: 'Netflix Inc.', market: 'NASDAQ' },
];

function StockSelector({ market, value, onChange }: Props) {
  const [searchTerm, setSearchTerm] = useState('');
  const stocks = market === 'domestic' ? DOMESTIC_STOCKS : OVERSEAS_STOCKS;
  
  const filteredStocks = stocks.filter(stock =>
    stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    stock.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <div className="space-y-4">
      {/* 검색 입력 */}
      <div className="relative">
        <input
          type="text"
          placeholder="종목명 또는 코드로 검색..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg pl-10"
        />
        <div className="absolute left-3 top-3.5 text-gray-400">🔍</div>
      </div>
      
      {/* 인기 종목 */}
      <div>
        <h4 className="font-medium mb-2 text-gray-700">인기 종목</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {filteredStocks.filter(stock => stock.popular).map(stock => (
            <StockCard 
              key={stock.symbol}
              stock={stock}
              selected={value === stock.symbol}
              onClick={() => onChange(stock.symbol)}
            />
          ))}
        </div>
      </div>
      
      {/* 전체 종목 */}
      <div>
        <h4 className="font-medium mb-2 text-gray-700">전체 종목</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-60 overflow-y-auto">
          {filteredStocks.map(stock => (
            <StockCard 
              key={stock.symbol}
              stock={stock}
              selected={value === stock.symbol}
              onClick={() => onChange(stock.symbol)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 4단계: 전략 확인

```tsx
function StrategyConfirm({ symbol, symbolName }: Props) {
  return (
    <div className="space-y-6">
      {/* 선택된 종목 요약 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium mb-2">선택된 종목</h4>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            📈
          </div>
          <div>
            <div className="font-semibold">{symbolName}</div>
            <div className="text-sm text-gray-600">{symbol}</div>
          </div>
        </div>
      </div>
      
      {/* 골든크로스 전략 설명 */}
      <div className="bg-yellow-50 p-6 rounded-lg border border-yellow-200">
        <h3 className="font-semibold text-yellow-900 mb-3 flex items-center gap-2">
          ⚡ 골든크로스 전략
        </h3>
        
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-yellow-800 mb-1">🎯 매수 신호</h4>
            <p className="text-sm text-yellow-700">
              5일 이동평균선이 20일 이동평균선을 위로 돌파할 때 매수
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-yellow-800 mb-1">📉 매도 신호</h4>
            <p className="text-sm text-yellow-700">
              5일 이동평균선이 20일 이동평균선을 아래로 돌파할 때 매도
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-yellow-800 mb-1">⏱️ 신호 확인</h4>
            <p className="text-sm text-yellow-700">
              3일 연속 유지될 때 신호 확정 (가짜 신호 방지)
            </p>
          </div>
        </div>
      </div>
      
      {/* 주의사항 */}
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h4 className="font-medium text-blue-900 mb-2">💡 참고사항</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• 횡보장에서는 잦은 매매로 손실 가능</li>
          <li>• 강한 추세장에서 효과적</li>
          <li>• 모의투자로 먼저 경험해보세요</li>
        </ul>
      </div>
    </div>
  );
}
```

### 5단계: 투자 설정

```tsx
function InvestmentSettings({ value, onChange }: Props) {
  const [investmentAmount, setInvestmentAmount] = useState(1000000);
  const [stopLossPercent, setStopLossPercent] = useState(-5);
  
  return (
    <div className="space-y-6">
      {/* 투자금액 설정 */}
      <div>
        <label className="block font-medium mb-3">💰 투자금액</label>
        <div className="space-y-3">
          <div>
            <input
              type="range"
              min="100000"
              max="10000000"
              step="100000"
              value={investmentAmount}
              onChange={(e) => setInvestmentAmount(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>10만원</span>
              <span>1,000만원</span>
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {investmentAmount.toLocaleString()}원
            </div>
            <div className="text-sm text-gray-600">
              모의투자 금액
            </div>
          </div>
        </div>
      </div>
      
      {/* 손절률 설정 */}
      <div>
        <label className="block font-medium mb-3">📉 손절률</label>
        <div className="space-y-3">
          <div>
            <input
              type="range"
              min="-20"
              max="-1"
              step="1"
              value={stopLossPercent}
              onChange={(e) => setStopLossPercent(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>-20%</span>
              <span>-1%</span>
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {stopLossPercent}%
            </div>
            <div className="text-sm text-gray-600">
              이 비율만큼 하락하면 자동 매도
            </div>
          </div>
        </div>
      </div>
      
      {/* 예상 매수 가능 주식 수 */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-medium mb-2">📊 예상 매수 정보</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <div>예상 주가: 70,000원 (현재가 기준)</div>
          <div>예상 매수 주식 수: {Math.floor(investmentAmount / 70000)}주</div>
          <div>예상 매수 금액: {(Math.floor(investmentAmount / 70000) * 70000).toLocaleString()}원</div>
        </div>
      </div>
    </div>
  );
}
```

## 전략 저장 및 실행

### 설정 완료 후 저장
```typescript
interface StrategyConfig {
  name: string;                    // "삼성전자 골든크로스 전략"
  market: 'domestic' | 'overseas';
  symbol: string;
  symbolName: string;
  strategyType: 'golden_cross';    // 현재는 고정
  investmentAmount: number;
  stopLossPercent: number;
  isPaperTrading: true;           // MVP 1.1에서는 고정
  isActive: true;                 // 생성 즉시 활성화
}

async function createStrategy(config: StrategyConfig) {
  const response = await fetch('/api/v1/trading-strategies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  
  if (response.ok) {
    const strategy = await response.json();
    // 전략 생성 완료 → 모니터링 화면으로 이동
    router.push(`/auto-trading/monitor/${strategy.id}`);
  }
}
```

## 설정 검증 규칙

### 필수 검증 항목
1. **시장 선택**: domestic 또는 overseas 중 하나 필수
2. **종목 선택**: 유효한 종목 코드 필수
3. **투자금액**: 10,000원 ~ 10,000,000원 범위
4. **손절률**: -1% ~ -20% 범위

### 추가 검증 로직
```typescript
function validateStrategyConfig(config: StrategyConfig): ValidationResult {
  const errors: string[] = [];
  
  // 시장 검증
  if (!['domestic', 'overseas'].includes(config.market)) {
    errors.push('올바른 시장을 선택해주세요');
  }
  
  // 종목 검증
  if (!config.symbol || config.symbol.length === 0) {
    errors.push('종목을 선택해주세요');
  }
  
  // 투자금액 검증
  if (config.investmentAmount < 10000) {
    errors.push('최소 투자금액은 1만원입니다');
  }
  if (config.investmentAmount > 10000000) {
    errors.push('최대 투자금액은 1천만원입니다');
  }
  
  // 손절률 검증
  if (config.stopLossPercent >= 0) {
    errors.push('손절률은 음수여야 합니다');
  }
  if (config.stopLossPercent < -20) {
    errors.push('손절률은 -20%보다 클 수 없습니다');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

## 다음 단계

이렇게 설계된 **최소 전략 설정 시스템**을 통해 사용자는:

1. **직관적으로** 자동매매 전략을 설정할 수 있고
2. **안전하게** 모의투자로 경험을 쌓을 수 있으며  
3. **단계적으로** 더 복잡한 전략으로 발전시킬 수 있습니다

다음 문서에서는 **모의투자 모드의 구체적인 구현 방법**을 다루겠습니다.