// 차트 관련 타입 정의
export interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

// 차트 상태 관리
export interface ChartState {
  data: CandlestickData[];
  loading: boolean;
  error: string | null;
  lastUpdated?: Date;
}

export interface StockInfo {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  market: 'KOSPI' | 'KOSDAQ';
}

export type ChartTimeframe = '1D' | '5D' | '1M' | '3M' | '1Y' | 'ALL';

export type ChartType = 'tick' | 'minute' | 'daily' | 'weekly' | 'monthly' | 'yearly';

export interface ChartConfig {
  timeframe: ChartTimeframe;
  chartType: ChartType;
  symbol: string;
}

// Mock 데이터를 위한 타입
export interface MockChartData {
  candlestickData: CandlestickData[];
  stockInfo: StockInfo;
}