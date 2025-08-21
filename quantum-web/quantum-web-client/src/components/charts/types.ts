// Chart Component Props Types

export interface StockChartProps {
  symbol: string;
  symbolName?: string;
  height?: number;
  showOrderBook?: boolean;
  showTrades?: boolean;
}

export interface PortfolioChartProps {
  portfolioId: string;
  height?: number;
}

export interface TechnicalIndicatorChartProps {
  symbol: string;
  symbolName?: string;
  timeframe?: '1m' | '5m' | '15m' | '1h' | '1d';
}

// Data Types for Charts

export interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface QuoteData {
  currentPrice: number;
  changeAmount: number;
  changePercent: number;
  bidPrice: number;
  askPrice: number;
  bidSize: number;
  askSize: number;
  volume: number;
  high: number;
  low: number;
  open: number;
}

export interface TradeData {
  price: number;
  size: number;
  side: 'BUY' | 'SELL';
  tradeTime: string;
}

export interface PortfolioData {
  portfolioId: string;
  totalValue: number;
  cashBalance: number;
  unrealizedPnL: number;
  realizedPnL: number;
  updateTime: string;
}

export interface PnLDataPoint {
  date: string;
  portfolioValue: number;
  dailyPnL: number;
  cumulativePnL: number;
}

export interface PositionData {
  symbol: string;
  symbolName: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  marketValue: number;
  costBasis: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  weightPercent: number;
  updatedAt: string;
}

export interface IndicatorData {
  timestamp: number;
  ma5?: number;
  ma20?: number;
  ma60?: number;
  ema12?: number;
  ema26?: number;
  macd?: number;
  signal?: number;
  histogram?: number;
  rsi?: number;
  stochK?: number;
  stochD?: number;
  upperBB?: number;
  lowerBB?: number;
  middleBB?: number;
}

export interface IndicatorConfig {
  movingAverages: {
    ma5: boolean;
    ma20: boolean;
    ma60: boolean;
    ema12: boolean;
    ema26: boolean;
  };
  oscillators: {
    macd: boolean;
    rsi: boolean;
    stochastic: boolean;
  };
  bands: {
    bollinger: boolean;
  };
}

// WebSocket Message Types

export interface RealtimeMessage<T = any> {
  type: 'QUOTE' | 'TRADE' | 'ORDER_UPDATE' | 'PORTFOLIO_UPDATE';
  symbol?: string;
  portfolioId?: string;
  data: T;
  timestamp: number;
}