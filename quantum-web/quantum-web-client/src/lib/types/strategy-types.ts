// 자동매매 전략 타입 정의

export type StrategyCategory = 'technical' | 'market' | 'fundamental';

export type StrategyDifficulty = 'beginner' | 'intermediate' | 'advanced';

export type StrategyStatus = 'active' | 'inactive' | 'testing';

export interface StrategyParameter {
  id: string;
  name: string;
  description: string;
  type: 'number' | 'percentage' | 'boolean' | 'select';
  defaultValue: any;
  min?: number;
  max?: number;
  options?: string[];
  unit?: string;
}

export interface BacktestResult {
  period: string;
  totalReturn: number;         // 총 수익률 (%)
  annualReturn: number;        // 연환산 수익률 (%)
  maxDrawdown: number;         // 최대 손실폭 (%)
  sharpeRatio: number;         // 샤프 비율
  winRate: number;             // 승률 (%)
  totalTrades: number;         // 총 거래 횟수
  avgHoldingPeriod: number;    // 평균 보유 기간 (일)
  volatility: number;          // 변동성 (%)
}

export interface TradingStrategy {
  id: string;
  name: string;
  category: StrategyCategory;
  difficulty: StrategyDifficulty;
  status: StrategyStatus;
  description: string;
  longDescription: string;
  
  // 전략 특성
  icon: string;                // 아이콘 이름 (lucide-react)
  tags: string[];              // 태그들
  riskLevel: 'low' | 'medium' | 'high'; // 위험도
  timeframe: string;           // 시간프레임 (예: "일봉", "30분봉")
  marketSuitability: string[];  // 적합한 시장 (예: ["상승장", "횡보장"])
  
  // 설정 가능한 파라미터들
  parameters: StrategyParameter[];
  
  // 백테스팅 결과
  backtest?: BacktestResult;
  
  // 메타데이터
  createdAt: Date;
  updatedAt: Date;
  isPopular: boolean;          // 인기 전략 여부
  isFavorite?: boolean;        // 사용자 즐겨찾기 여부
  
  // 알림 설정
  enableAlerts: boolean;
  alertConditions?: string[];
}

// 전략 카테고리별 정보
export const STRATEGY_CATEGORIES = {
  technical: {
    name: '기술적 분석',
    icon: 'TrendingUp',
    description: '차트 패턴과 기술적 지표를 활용한 매매 전략',
    color: 'blue'
  },
  market: {
    name: '시장 지표',
    icon: 'BarChart3',
    description: '시장 상황과 거래량 지표를 기반으로 한 전략',
    color: 'green'
  },
  fundamental: {
    name: '재무 지표',
    icon: 'Calculator',
    description: '기업의 재무제표와 밸류에이션을 고려한 전략',
    color: 'purple'
  }
};

// 위험도별 정보
export const RISK_LEVELS = {
  low: { 
    name: '낮음', 
    color: 'text-green-600 bg-green-100', 
    description: '안정적이고 보수적인 전략' 
  },
  medium: { 
    name: '보통', 
    color: 'text-yellow-600 bg-yellow-100', 
    description: '균형잡힌 수익과 위험' 
  },
  high: { 
    name: '높음', 
    color: 'text-red-600 bg-red-100', 
    description: '적극적이고 공격적인 전략' 
  }
};

// 난이도별 정보
export const DIFFICULTY_LEVELS = {
  beginner: { 
    name: '초급', 
    color: 'text-green-600 bg-green-100', 
    description: '투자 초보자에게 적합' 
  },
  intermediate: { 
    name: '중급', 
    color: 'text-orange-600 bg-orange-100', 
    description: '어느 정도 경험이 있는 투자자용' 
  },
  advanced: { 
    name: '고급', 
    color: 'text-red-600 bg-red-100', 
    description: '전문적인 지식이 필요한 전략' 
  }
};

// 전략 상태별 정보
export const STRATEGY_STATUSES = {
  active: { 
    name: '활성화', 
    color: 'text-green-600 bg-green-100', 
    description: '현재 실행 중인 전략' 
  },
  inactive: { 
    name: '비활성화', 
    color: 'text-gray-600 bg-gray-100', 
    description: '일시 정지된 전략' 
  },
  testing: { 
    name: '테스팅', 
    color: 'text-blue-600 bg-blue-100', 
    description: '백테스팅 또는 페이퍼 트레이딩 중' 
  }
};