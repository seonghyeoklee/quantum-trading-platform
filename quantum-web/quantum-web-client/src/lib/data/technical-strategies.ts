// 기술적 분석 자동매매 전략 데이터

import { TradingStrategy } from '@/lib/types/strategy-types';

export const technicalAnalysisStrategies: TradingStrategy[] = [
  {
    id: 'moving-average-crossover',
    name: '이동평균 크로스오버',
    category: 'technical',
    difficulty: 'beginner',
    status: 'active',
    description: '단기 이동평균이 장기 이동평균을 돌파할 때 매매 신호를 생성하는 전략',
    longDescription: `
      가장 기본적이고 널리 사용되는 기술적 분석 전략입니다. 
      단기 이동평균선(예: 20일)이 장기 이동평균선(예: 60일)을 상향 돌파하면 매수하고, 
      하향 돌파하면 매도하는 방식으로 작동합니다.
      
      **장점:**
      - 이해하기 쉽고 구현이 간단
      - 강한 추세에서 효과적
      - 다양한 시장 상황에 적용 가능
      
      **단점:**
      - 횡보장에서 잦은 가짜 신호 발생
      - 지연 신호로 인한 수익 기회 손실
      - 급변하는 시장에서 반응 속도 저하
    `,
    icon: 'TrendingUp',
    tags: ['추세 추종', '이동평균', '골든크로스', '데드크로스'],
    riskLevel: 'medium',
    timeframe: '일봉',
    marketSuitability: ['상승장', '하락장'],
    parameters: [
      {
        id: 'short_period',
        name: '단기 이동평균 기간',
        description: '빠른 반응을 위한 단기 이동평균선의 기간',
        type: 'number',
        defaultValue: 20,
        min: 5,
        max: 50,
        unit: '일'
      },
      {
        id: 'long_period',
        name: '장기 이동평균 기간',
        description: '추세 확인을 위한 장기 이동평균선의 기간',
        type: 'number',
        defaultValue: 60,
        min: 20,
        max: 200,
        unit: '일'
      },
      {
        id: 'stop_loss',
        name: '손절 비율',
        description: '매수가 대비 손절매 비율',
        type: 'percentage',
        defaultValue: 5,
        min: 1,
        max: 15,
        unit: '%'
      },
      {
        id: 'take_profit',
        name: '익절 비율',
        description: '매수가 대비 익절매 비율',
        type: 'percentage',
        defaultValue: 10,
        min: 5,
        max: 30,
        unit: '%'
      }
    ],
    backtest: {
      period: '2022-01-01 ~ 2024-12-31',
      totalReturn: 15.3,
      annualReturn: 7.2,
      maxDrawdown: -12.5,
      sharpeRatio: 1.24,
      winRate: 58.3,
      totalTrades: 124,
      avgHoldingPeriod: 18,
      volatility: 16.8
    },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-15'),
    isPopular: true,
    enableAlerts: true,
    alertConditions: ['골든크로스 발생', '데드크로스 발생', '손익 구간 진입']
  },

  {
    id: 'rsi-reversal',
    name: 'RSI 역추세 전략',
    category: 'technical',
    difficulty: 'intermediate',
    status: 'active',
    description: 'RSI 지표의 과매수/과매도 구간에서 역추세 매매를 실행하는 전략',
    longDescription: `
      RSI(Relative Strength Index) 지표를 활용한 역추세 전략입니다.
      RSI가 70 이상에서 과매수 신호로 매도하고, 30 이하에서 과매도 신호로 매수합니다.
      
      **전략 원리:**
      - RSI 70 이상: 과매수 구간, 매도 신호
      - RSI 30 이하: 과매도 구간, 매수 신호
      - 중간값(50) 근처에서는 관망
      
      **적용 시장:**
      - 박스권 횡보장에서 가장 효과적
      - 변동성이 큰 개별 종목에 적합
      - 단기 스윙 트레이딩에 유용
    `,
    icon: 'BarChart',
    tags: ['RSI', '역추세', '과매수', '과매도', '오실레이터'],
    riskLevel: 'medium',
    timeframe: '4시간봉',
    marketSuitability: ['횡보장', '변동성장'],
    parameters: [
      {
        id: 'rsi_period',
        name: 'RSI 기간',
        description: 'RSI 계산에 사용할 기간',
        type: 'number',
        defaultValue: 14,
        min: 7,
        max: 28,
        unit: '봉'
      },
      {
        id: 'oversold_level',
        name: '과매도 기준선',
        description: '매수 신호를 발생시킬 RSI 하한선',
        type: 'number',
        defaultValue: 30,
        min: 20,
        max: 40,
        unit: ''
      },
      {
        id: 'overbought_level',
        name: '과매수 기준선',
        description: '매도 신호를 발생시킬 RSI 상한선',
        type: 'number',
        defaultValue: 70,
        min: 60,
        max: 80,
        unit: ''
      },
      {
        id: 'exit_neutral',
        name: '중립선 청산',
        description: 'RSI 50선 터치 시 포지션 청산 여부',
        type: 'boolean',
        defaultValue: true
      }
    ],
    backtest: {
      period: '2022-01-01 ~ 2024-12-31',
      totalReturn: 22.7,
      annualReturn: 10.8,
      maxDrawdown: -8.3,
      sharpeRatio: 1.67,
      winRate: 64.2,
      totalTrades: 86,
      avgHoldingPeriod: 12,
      volatility: 14.2
    },
    createdAt: new Date('2024-01-02'),
    updatedAt: new Date('2024-01-16'),
    isPopular: false,
    enableAlerts: true,
    alertConditions: ['RSI 과매수 진입', 'RSI 과매도 진입', 'RSI 중립선 돌파']
  },

  {
    id: 'bollinger-band-squeeze',
    name: '볼린저 밴드 스퀴즈',
    category: 'technical',
    difficulty: 'advanced',
    status: 'testing',
    description: '볼린저 밴드의 수축과 확장을 이용한 변동성 돌파 전략',
    longDescription: `
      볼린저 밴드의 특성을 활용한 고급 전략입니다.
      밴드가 수축(스퀴즈)된 후 확장되면서 발생하는 변동성 돌파를 포착합니다.
      
      **전략 구성요소:**
      - 볼린저 밴드 상하단 라인
      - 20일 이동평균선 (중심선)
      - 표준편차 배수 설정
      
      **매매 조건:**
      - 스퀴즈 구간: 밴드폭이 임계값 이하로 수축
      - 돌파 신호: 가격이 밴드를 벗어나며 거래량 급증
      - 추세 확인: 중심선 방향과 돌파 방향 일치
      
      **장점:**
      - 높은 성공률의 돌파 신호
      - 명확한 손절 구간 설정
      - 변동성 확대 초기 진입 가능
    `,
    icon: 'Activity',
    tags: ['볼린저밴드', '변동성', '돌파', '스퀴즈', '거래량'],
    riskLevel: 'high',
    timeframe: '일봉',
    marketSuitability: ['변동성장', '트렌드 전환'],
    parameters: [
      {
        id: 'bb_period',
        name: '볼린저 밴드 기간',
        description: '이동평균 및 표준편차 계산 기간',
        type: 'number',
        defaultValue: 20,
        min: 10,
        max: 50,
        unit: '일'
      },
      {
        id: 'bb_deviation',
        name: '표준편차 배수',
        description: '볼린저 밴드 상하단 라인의 표준편차 배수',
        type: 'number',
        defaultValue: 2.0,
        min: 1.5,
        max: 3.0,
        unit: '배'
      },
      {
        id: 'squeeze_threshold',
        name: '스퀴즈 임계값',
        description: '밴드폭이 이 값 이하일 때 스퀴즈로 판단',
        type: 'percentage',
        defaultValue: 15,
        min: 10,
        max: 25,
        unit: '%'
      },
      {
        id: 'volume_factor',
        name: '거래량 증가 배수',
        description: '평균 거래량의 몇 배 이상일 때 유효한 돌파로 인정',
        type: 'number',
        defaultValue: 1.5,
        min: 1.2,
        max: 3.0,
        unit: '배'
      },
      {
        id: 'holding_period',
        name: '최대 보유 기간',
        description: '신호 발생 후 최대 보유 가능 기간',
        type: 'number',
        defaultValue: 10,
        min: 5,
        max: 30,
        unit: '일'
      }
    ],
    backtest: {
      period: '2022-01-01 ~ 2024-12-31',
      totalReturn: 31.2,
      annualReturn: 14.7,
      maxDrawdown: -18.6,
      sharpeRatio: 1.89,
      winRate: 71.4,
      totalTrades: 42,
      avgHoldingPeriod: 8,
      volatility: 22.3
    },
    createdAt: new Date('2024-01-03'),
    updatedAt: new Date('2024-01-17'),
    isPopular: true,
    enableAlerts: true,
    alertConditions: ['밴드 스퀴즈 형성', '상단 돌파', '하단 이탈', '거래량 급증']
  },

  {
    id: 'macd-divergence',
    name: 'MACD 다이버전스',
    category: 'technical',
    difficulty: 'advanced',
    status: 'inactive',
    description: '가격과 MACD의 다이버전스를 포착하여 추세 전환을 예측하는 전략',
    longDescription: `
      MACD 지표와 주가 간의 다이버전스를 활용한 고급 기술적 분석 전략입니다.
      가격과 지표 간의 방향성 불일치를 통해 추세 전환 시점을 포착합니다.
      
      **다이버전스 유형:**
      - 강세 다이버전스: 가격 하락, MACD 상승
      - 약세 다이버전스: 가격 상승, MACD 하락
      - 히든 다이버전스: 추세 지속 신호
      
      **매매 신호:**
      - 다이버전스 형성 + 시그널 라인 교차
      - 거래량 확인을 통한 신호 검증
      - 지지/저항선과의 연계 분석
    `,
    icon: 'GitBranch',
    tags: ['MACD', '다이버전스', '추세전환', '시그널라인'],
    riskLevel: 'high',
    timeframe: '일봉',
    marketSuitability: ['추세 전환', '조정 구간'],
    parameters: [
      {
        id: 'fast_ema',
        name: '빠른 EMA 기간',
        description: 'MACD 계산용 단기 지수이동평균 기간',
        type: 'number',
        defaultValue: 12,
        min: 8,
        max: 18,
        unit: '일'
      },
      {
        id: 'slow_ema',
        name: '느린 EMA 기간',
        description: 'MACD 계산용 장기 지수이동평균 기간',
        type: 'number',
        defaultValue: 26,
        min: 20,
        max: 35,
        unit: '일'
      },
      {
        id: 'signal_period',
        name: '시그널 라인 기간',
        description: 'MACD의 시그널 라인 이동평균 기간',
        type: 'number',
        defaultValue: 9,
        min: 5,
        max: 15,
        unit: '일'
      },
      {
        id: 'divergence_lookback',
        name: '다이버전스 탐색 기간',
        description: '다이버전스를 찾기 위한 과거 데이터 검색 범위',
        type: 'number',
        defaultValue: 20,
        min: 10,
        max: 40,
        unit: '일'
      }
    ],
    backtest: {
      period: '2022-01-01 ~ 2024-12-31',
      totalReturn: 18.9,
      annualReturn: 8.9,
      maxDrawdown: -15.2,
      sharpeRatio: 1.34,
      winRate: 52.7,
      totalTrades: 37,
      avgHoldingPeriod: 15,
      volatility: 19.6
    },
    createdAt: new Date('2024-01-04'),
    updatedAt: new Date('2024-01-18'),
    isPopular: false,
    enableAlerts: false,
    alertConditions: ['강세 다이버전스', '약세 다이버전스', 'MACD 시그널 교차']
  }
];

// 전략 검색 및 필터링 함수
export function getTechnicalStrategiesByCategory() {
  return technicalAnalysisStrategies;
}

export function getTechnicalStrategyById(id: string) {
  return technicalAnalysisStrategies.find(strategy => strategy.id === id);
}

export function getPopularTechnicalStrategies() {
  return technicalAnalysisStrategies.filter(strategy => strategy.isPopular);
}

export function getActiveTechnicalStrategies() {
  return technicalAnalysisStrategies.filter(strategy => strategy.status === 'active');
}