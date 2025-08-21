/**
 * Trading Platform Type Definitions
 * 
 * 백엔드 API와 프론트엔드 간 데이터 교환을 위한 타입 정의
 */

// API Response Wrapper
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  errorCode?: string;
  timestamp: string;
}

// Chart Data Types
export interface ChartDataResponse {
  symbol: string;
  timeframe: string;
  candles: CandleData[];
  volume: VolumeData;
}

export interface CandleData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface VolumeData {
  points: VolumePoint[];
}

export interface VolumePoint {
  timestamp: string;
  volume: number;
}

// Real-time Data Types
export interface RealtimeDataResponse {
  type: 'QUOTE' | 'TRADE' | 'ORDER_UPDATE' | 'PORTFOLIO_UPDATE';
  symbol?: string;
  timestamp: string;
  data: QuoteData | TradeData | OrderUpdate | PortfolioUpdate;
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

export interface OrderUpdate {
  orderId: string;
  status: 'PENDING' | 'SUBMITTED' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  filledQuantity: number;
  remainingQuantity: number;
  averagePrice: number;
  updateTime: string;
}

export interface PortfolioUpdate {
  portfolioId: string;
  totalValue: number;
  cashBalance: number;
  unrealizedPnL: number;
  realizedPnL: number;
  updateTime: string;
}

// Trading Types
export interface Order {
  orderId: string;
  portfolioId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
  quantity: number;
  price?: number;
  stopPrice?: number;
  status: 'PENDING' | 'SUBMITTED' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  filledQuantity: number;
  remainingQuantity: number;
  averagePrice?: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateOrderRequest {
  portfolioId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
  quantity: number;
  price?: number;
  stopPrice?: number;
}

// Portfolio Types
export interface Portfolio {
  portfolioId: string;
  userId: string;
  name: string;
  totalValue: number;
  cashBalance: number;
  unrealizedPnL: number;
  realizedPnL: number;
  createdAt: string;
  updatedAt: string;
}

export interface Position {
  portfolioId: string;
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
  updatedAt: string;
}

// Market Data Types
export interface Quote {
  symbol: string;
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
  timestamp: string;
}

export interface OrderBookEntry {
  price: number;
  size: number;
  count: number;
}

export interface OrderBook {
  symbol: string;
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  timestamp: string;
}

// Chart Configuration Types
export interface ChartConfig {
  symbol: string;
  timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M';
  indicators: ChartIndicator[];
  theme: 'light' | 'dark';
}

export interface ChartIndicator {
  type: 'MA' | 'EMA' | 'RSI' | 'MACD' | 'BOLLINGER_BANDS';
  period?: number;
  parameters?: Record<string, any>;
  visible: boolean;
}

// WebSocket Event Types
export type WebSocketEventType = 
  | 'quotes'
  | 'trades' 
  | 'orderUpdates'
  | 'portfolioUpdates'
  | 'chartData';

export interface WebSocketSubscription {
  type: WebSocketEventType;
  symbol?: string;
  portfolioId?: string;
  callback: (data: any) => void;
}