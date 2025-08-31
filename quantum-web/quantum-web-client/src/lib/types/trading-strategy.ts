// 자동매매 전략 관련 타입 정의

// 전략 타입
export interface TradingStrategy {
  id: string;
  name: string;
  description: string;
  category: 'trend' | 'momentum' | 'mean_reversion' | 'volatility' | 'fundamental';
  risk_level: 'low' | 'medium' | 'high';
  min_capital: number;
  expected_return: string;
  success_rate: number;
  parameters: StrategyParameter[];
  indicators: string[];
}

// 전략 매개변수
export interface StrategyParameter {
  name: string;
  label: string;
  type: 'number' | 'boolean' | 'select';
  default_value: any;
  min_value?: number;
  max_value?: number;
  options?: string[];
  description: string;
}

// 종목 분석 데이터
export interface StockAnalysis {
  symbol: string;
  name: string;
  current_price: number;
  open_price: number;
  high_price: number;
  low_price: number;
  volume: number;
  market_cap: number;
  
  // 기술적 지표
  indicators: {
    rsi: number;
    macd: {
      macd: number;
      signal: number;
      histogram: number;
    };
    bollinger_bands: {
      upper: number;
      middle: number;
      lower: number;
    };
    moving_averages: {
      ma5: number;
      ma20: number;
      ma60: number;
      ma120: number;
    };
    stochastic: {
      k: number;
      d: number;
    };
  };
  
  // 재무 지표
  fundamental: {
    per: number;
    pbr: number;
    roe: number;
    debt_ratio: number;
    current_ratio: number;
  };
  
  // 전략 적합도 점수
  strategy_scores: {
    [strategy_id: string]: {
      score: number;
      recommendation: 'strong_buy' | 'buy' | 'hold' | 'sell' | 'strong_sell';
      reason: string;
    };
  };
}

// 자동매매 설정
export interface AutoTradingConfig {
  strategy_id: string;
  symbol: string;
  capital: number;
  max_position_size: number;
  stop_loss_percent: number;
  take_profit_percent: number;
  parameters: { [key: string]: any };
  start_time?: string;
  end_time?: string;
  is_active: boolean;
}

// 자동매매 상태
export interface AutoTradingStatus {
  id: string;
  config: AutoTradingConfig;
  status: 'preparing' | 'running' | 'paused' | 'stopped' | 'error';
  created_at: string;
  started_at?: string;
  stopped_at?: string;
  
  // 성과 지표
  performance: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    total_return: number;
    total_return_percent: number;
    max_drawdown: number;
    sharpe_ratio: number;
    current_positions: Position[];
  };
  
  // 최근 거래 내역
  recent_trades: Trade[];
}

// 포지션
export interface Position {
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
}

// 거래 내역
export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  amount: number;
  fee: number;
  executed_at: string;
  pnl?: number;
  pnl_percent?: number;
}