# 자동매매 전략 실행 시스템 흐름도

## 🏗️ 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Strategy Management UI]
        Chart[TradingView Chart]
        Config[Strategy Configuration]
    end
    
    subgraph "Backend API Layer (Java Spring Boot)"
        API[Strategy Controller]
        Service[Strategy Execution Service]
        Trading[Auto Trading Service]
        Risk[Risk Management Service]
    end
    
    subgraph "Analysis Engine (Python FastAPI)"
        Indicators[Technical Indicators]
        SignalGen[Signal Generator]
        Backtest[Backtest Engine]
        Market[Market Data Processor]
    end
    
    subgraph "Data Sources"
        Kiwoom[Kiwoom WebSocket/API]
        Redis[Redis Cache]
        Postgres[PostgreSQL]
    end
    
    subgraph "Event Store"
        Events[Axon Server Events]
    end
    
    UI --> API
    Config --> API
    API --> Service
    Service --> SignalGen
    Service --> Trading
    Trading --> Risk
    
    SignalGen --> Indicators
    Indicators --> Market
    Market --> Kiwoom
    
    Service --> Backtest
    Backtest --> Postgres
    
    Trading --> Events
    Events --> Postgres
    
    Market --> Redis
    Chart --> Kiwoom
    
    style UI fill:#e1f5fe
    style API fill:#f3e5f5
    style SignalGen fill:#fff3e0
    style Trading fill:#e8f5e8
```

## 📊 데이터 흐름 다이어그램

```mermaid
sequenceDiagram
    participant UI as Frontend UI
    participant API as Java Backend
    participant Python as Python Adapter
    participant Kiwoom as Kiwoom API
    participant Events as Event Store
    
    UI->>API: 전략 활성화 요청
    API->>Python: 전략 설정 전달
    Python->>Kiwoom: 실시간 데이터 구독
    
    loop 실시간 데이터 처리
        Kiwoom->>Python: 시세 데이터
        Python->>Python: 기술적 지표 계산
        Python->>Python: 매매 신호 생성
        
        alt 매수/매도 신호 발생
            Python->>API: 신호 전달
            API->>API: 리스크 검증
            API->>Events: 주문 Command 발행
            Events->>API: 주문 실행 결과
            API->>UI: 거래 알림
        end
    end
```

## 🔄 모듈별 상세 역할

### 1. Frontend Strategy Management

```mermaid
graph LR
    subgraph "Strategy Management UI"
        List[전략 목록]
        Card[전략 카드]
        Config[설정 패널]
        Status[상태 모니터링]
    end
    
    List --> Card
    Card --> Config
    Card --> Status
    Config --> Backend[Backend API]
    Status --> Backend
    
    subgraph "Strategy Card Functions"
        Toggle[활성화/비활성화]
        Settings[파라미터 설정]
        Backtest[백테스팅 실행]
        Monitor[성과 모니터링]
    end
    
    Card --> Toggle
    Card --> Settings
    Card --> Backtest
    Card --> Monitor
```

### 2. Java Backend Services

```mermaid
graph TB
    subgraph "Strategy Execution Service"
        Receive[신호 수신]
        Validate[유효성 검증]
        Execute[실행 결정]
    end
    
    subgraph "Auto Trading Service"
        Order[주문 생성]
        Position[포지션 관리]
        PnL[손익 계산]
    end
    
    subgraph "Risk Management"
        Limits[한도 검증]
        Stop[손절/익절]
        Size[포지션 크기]
    end
    
    Receive --> Validate
    Validate --> Limits
    Limits --> Execute
    Execute --> Order
    Order --> Position
    Position --> PnL
    
    Stop --> Order
    Size --> Order
```

### 3. Python Analysis Engine

```mermaid
graph TB
    subgraph "Market Data Processing"
        Stream[실시간 스트림]
        Parse[데이터 파싱]
        Store[캐시 저장]
    end
    
    subgraph "Technical Indicators"
        SMA[단순 이동평균]
        EMA[지수 이동평균]
        RSI[RSI 계산]
        MACD[MACD 계산]
        BB[볼린저밴드]
    end
    
    subgraph "Signal Generation"
        Rules[규칙 엔진]
        Cross[크로스오버 감지]
        Threshold[임계값 판단]
        Signal[신호 생성]
    end
    
    Stream --> Parse
    Parse --> Store
    Store --> SMA
    Store --> EMA
    Store --> RSI
    Store --> MACD
    Store --> BB
    
    SMA --> Rules
    EMA --> Rules
    RSI --> Rules
    MACD --> Rules
    BB --> Rules
    
    Rules --> Cross
    Rules --> Threshold
    Cross --> Signal
    Threshold --> Signal
```

## 🎯 개별 전략 실행 흐름

### 전략 1: 이동평균 크로스오버

```mermaid
flowchart TD
    Start([시작]) --> GetData[실시간 시세 수신]
    GetData --> CalcSMA[20일/60일 SMA 계산]
    CalcSMA --> CheckCross{크로스오버 발생?}
    
    CheckCross -->|골든크로스| BuySignal[매수 신호]
    CheckCross -->|데드크로스| SellSignal[매도 신호]
    CheckCross -->|변화없음| Wait[대기]
    
    BuySignal --> CheckRisk{리스크 검증}
    SellSignal --> CheckPosition{포지션 보유?}
    
    CheckRisk -->|통과| PlaceBuyOrder[매수 주문]
    CheckRisk -->|거부| LogRisk[리스크 로그]
    
    CheckPosition -->|있음| PlaceSellOrder[매도 주문]
    CheckPosition -->|없음| LogNoPosition[포지션 없음 로그]
    
    PlaceBuyOrder --> Monitor[포지션 모니터링]
    PlaceSellOrder --> Monitor
    Monitor --> StopLoss{손절선 도달?}
    Monitor --> TakeProfit{익절선 도달?}
    
    StopLoss -->|예| ExecuteStop[손절 매도]
    TakeProfit -->|예| ExecuteProfit[익절 매도]
    
    Wait --> GetData
    LogRisk --> GetData
    LogNoPosition --> GetData
    ExecuteStop --> GetData
    ExecuteProfit --> GetData
    
    style BuySignal fill:#c8e6c9
    style SellSignal fill:#ffcdd2
    style PlaceBuyOrder fill:#e8f5e8
    style PlaceSellOrder fill:#fce4ec
```

### 전략 2: RSI 역추세 전략

```mermaid
flowchart TD
    Start([시작]) --> GetPrice[실시간 가격 수신]
    GetPrice --> CalcRSI[RSI(14) 계산]
    CalcRSI --> CheckRSI{RSI 상태 확인}
    
    CheckRSI -->|RSI ≤ 30| Oversold[과매도 구간]
    CheckRSI -->|RSI ≥ 70| Overbought[과매수 구간]
    CheckRSI -->|30 < RSI < 70| Neutral[중립 구간]
    
    Oversold --> CheckBuyCondition{매수 조건 확인}
    Overbought --> CheckSellCondition{매도 조건 확인}
    Neutral --> CheckNeutralExit{중립선 청산?}
    
    CheckBuyCondition -->|조건 만족| BuySignal[매수 신호]
    CheckBuyCondition -->|조건 불만족| Wait[대기]
    
    CheckSellCondition -->|포지션 있음| SellSignal[매도 신호]
    CheckSellCondition -->|포지션 없음| Wait
    
    CheckNeutralExit -->|설정 활성화| NeutralExit[중립선 청산]
    CheckNeutralExit -->|설정 비활성화| Wait
    
    BuySignal --> ValidateRisk{리스크 검증}
    SellSignal --> PlaceSellOrder[매도 주문]
    NeutralExit --> PlaceSellOrder
    
    ValidateRisk -->|통과| PlaceBuyOrder[매수 주문]
    ValidateRisk -->|거부| Wait
    
    PlaceBuyOrder --> MonitorPosition[포지션 모니터링]
    PlaceSellOrder --> MonitorPosition
    
    MonitorPosition --> GetPrice
    Wait --> GetPrice
    
    style Oversold fill:#c8e6c9
    style Overbought fill:#ffcdd2
    style BuySignal fill:#e8f5e8
    style SellSignal fill:#fce4ec
```

### 전략 3: 볼린저밴드 스퀴즈

```mermaid
flowchart TD
    Start([시작]) --> GetData[시세 + 거래량 수신]
    GetData --> CalcBB[볼린저밴드 계산]
    CalcBB --> CalcBandwidth[밴드폭 계산]
    CalcBandwidth --> CheckSqueeze{스퀴즈 상태?}
    
    CheckSqueeze -->|스퀴즈 형성| WaitBreakout[돌파 대기]
    CheckSqueeze -->|정상 상태| Normal[정상 모니터링]
    
    WaitBreakout --> CheckBreakout{밴드 돌파?}
    CheckBreakout -->|상단 돌파| UpperBreak[상단 돌파]
    CheckBreakout -->|하단 이탈| LowerBreak[하단 이탈]
    CheckBreakout -->|돌파 없음| WaitBreakout
    
    UpperBreak --> CheckVolume{거래량 급증?}
    LowerBreak --> CheckVolume
    
    CheckVolume -->|급증 확인| ValidSignal[유효 신호]
    CheckVolume -->|급증 없음| FalseSignal[가짜 신호]
    
    ValidSignal --> DetermineDirection{돌파 방향}
    DetermineDirection -->|상단 돌파| BuySignal[매수 신호]
    DetermineDirection -->|하단 이탈| SellSignal[매도 신호]
    
    BuySignal --> RiskCheck{리스크 검증}
    SellSignal --> PositionCheck{포지션 확인}
    
    RiskCheck -->|통과| PlaceBuyOrder[매수 주문]
    RiskCheck -->|거부| LogRisk[리스크 로그]
    
    PositionCheck -->|보유 중| PlaceSellOrder[매도 주문]
    PositionCheck -->|보유 없음| LogNoPosition[포지션 없음]
    
    PlaceBuyOrder --> SetStopLoss[손절선 설정]
    PlaceSellOrder --> SetStopLoss
    SetStopLoss --> MonitorTime[시간 모니터링]
    
    MonitorTime --> CheckHoldingPeriod{최대 보유기간?}
    CheckHoldingPeriod -->|초과| ForceExit[강제 청산]
    CheckHoldingPeriod -->|유지| MonitorTime
    
    Normal --> GetData
    FalseSignal --> GetData
    LogRisk --> GetData
    LogNoPosition --> GetData
    ForceExit --> GetData
    
    style UpperBreak fill:#c8e6c9
    style LowerBreak fill:#ffcdd2
    style ValidSignal fill:#fff3e0
    style BuySignal fill:#e8f5e8
    style SellSignal fill:#fce4ec
```

### 전략 4: MACD 다이버전스

```mermaid
flowchart TD
    Start([시작]) --> GetPrice[가격 데이터 수신]
    GetPrice --> CalcMACD[MACD/Signal 계산]
    CalcMACD --> StoreHistory[이력 저장]
    StoreHistory --> FindPeaks[고점/저점 탐지]
    
    FindPeaks --> CheckDivergence{다이버전스 확인}
    CheckDivergence -->|강세 다이버전스| BullishDiv[강세 다이버전스]
    CheckDivergence -->|약세 다이버전스| BearishDiv[약세 다이버전스]
    CheckDivergence -->|다이버전스 없음| NoDivergence[다이버전스 없음]
    
    BullishDiv --> CheckSignalCross{시그널 교차?}
    BearishDiv --> CheckSignalCross
    
    CheckSignalCross -->|MACD > Signal| BullishCross[강세 교차]
    CheckSignalCross -->|MACD < Signal| BearishCross[약세 교차]
    CheckSignalCross -->|교차 없음| WaitCross[교차 대기]
    
    BullishCross --> ValidateBuy{매수 조건 검증}
    BearishCross --> ValidateSell{매도 조건 검증}
    
    ValidateBuy --> CheckVolume{거래량 확인}
    ValidateSell --> CheckPosition{포지션 확인}
    
    CheckVolume -->|거래량 증가| BuySignal[매수 신호]
    CheckVolume -->|거래량 부족| WeakSignal[약한 신호]
    
    CheckPosition -->|포지션 보유| SellSignal[매도 신호]
    CheckPosition -->|포지션 없음| NoPosition[포지션 없음]
    
    BuySignal --> ExecuteRiskCheck{리스크 검증}
    SellSignal --> ExecuteSell[매도 실행]
    
    ExecuteRiskCheck -->|통과| ExecuteBuy[매수 실행]
    ExecuteRiskCheck -->|거부| RiskRejected[리스크 거부]
    
    ExecuteBuy --> MonitorDivergence[다이버전스 모니터링]
    ExecuteSell --> MonitorDivergence
    
    MonitorDivergence --> CheckReverse{반전 신호?}
    CheckReverse -->|반전 감지| ReverseAction[반전 대응]
    CheckReverse -->|유지| ContinueMonitor[계속 모니터링]
    
    NoDivergence --> GetPrice
    WaitCross --> GetPrice
    WeakSignal --> GetPrice
    NoPosition --> GetPrice
    RiskRejected --> GetPrice
    ReverseAction --> GetPrice
    ContinueMonitor --> GetPrice
    
    style BullishDiv fill:#c8e6c9
    style BearishDiv fill:#ffcdd2
    style BullishCross fill:#e8f5e8
    style BearishCross fill:#fce4ec
    style BuySignal fill:#4caf50
    style SellSignal fill:#f44336
```

## 🔄 통합 백테스팅 흐름

```mermaid
flowchart TD
    Start([백테스팅 시작]) --> LoadStrategy[전략 설정 로드]
    LoadStrategy --> LoadHistoryData[과거 데이터 로드]
    LoadHistoryData --> InitPortfolio[포트폴리오 초기화]
    
    InitPortfolio --> TimeLoop{시간 순회}
    TimeLoop -->|데이터 있음| ProcessBar[캔들 처리]
    TimeLoop -->|데이터 끝| CalculateResults[결과 계산]
    
    ProcessBar --> UpdateIndicators[지표 업데이트]
    UpdateIndicators --> CheckSignals[신호 확인]
    CheckSignals --> ExecuteTrades[거래 실행]
    ExecuteTrades --> UpdatePortfolio[포트폴리오 업데이트]
    UpdatePortfolio --> RecordMetrics[성과 기록]
    RecordMetrics --> TimeLoop
    
    CalculateResults --> CalcReturns[수익률 계산]
    CalcReturns --> CalcSharpe[샤프비율 계산]
    CalcSharpe --> CalcMDD[MDD 계산]
    CalcMDD --> CalcWinRate[승률 계산]
    CalcWinRate --> GenerateReport[보고서 생성]
    GenerateReport --> End([백테스팅 완료])
    
    style ProcessBar fill:#e3f2fd
    style ExecuteTrades fill:#fff3e0
    style GenerateReport fill:#e8f5e8
```

## 🚨 위험 관리 체계

```mermaid
flowchart TD
    Signal[매매 신호] --> RiskGate{위험 관리 게이트}
    
    RiskGate --> CheckBalance{잔고 확인}
    RiskGate --> CheckPosition{포지션 확인}
    RiskGate --> CheckVolatility{변동성 확인}
    RiskGate --> CheckDrawdown{손실 한도 확인}
    
    CheckBalance -->|충분| BalanceOK[잔고 OK]
    CheckBalance -->|부족| BalanceNG[잔고 부족]
    
    CheckPosition -->|한도 내| PositionOK[포지션 OK]
    CheckPosition -->|한도 초과| PositionNG[포지션 초과]
    
    CheckVolatility -->|정상| VolatilityOK[변동성 OK]
    CheckVolatility -->|과도| VolatilityNG[변동성 과도]
    
    CheckDrawdown -->|한도 내| DrawdownOK[손실 OK]
    CheckDrawdown -->|한도 초과| DrawdownNG[손실 초과]
    
    BalanceOK --> RiskDecision{위험 종합 판단}
    PositionOK --> RiskDecision
    VolatilityOK --> RiskDecision
    DrawdownOK --> RiskDecision
    
    BalanceNG --> RejectTrade[거래 거부]
    PositionNG --> RejectTrade
    VolatilityNG --> RejectTrade
    DrawdownNG --> RejectTrade
    
    RiskDecision -->|모든 조건 통과| ApproveTrade[거래 승인]
    RiskDecision -->|일부 조건 실패| RejectTrade
    
    ApproveTrade --> ExecuteTrade[거래 실행]
    RejectTrade --> LogRisk[위험 로그]
    
    style ApproveTrade fill:#c8e6c9
    style RejectTrade fill:#ffcdd2
    style RiskDecision fill:#fff3e0
```

이 문서는 자동매매 전략 실행 시스템의 전체적인 구조와 각 모듈 간의 상호작용, 그리고 개별 전략별 세부 실행 흐름을 시각적으로 보여줍니다. 각 다이어그램은 실제 구현 시 참고할 수 있는 상세한 로직 흐름을 제공합니다.