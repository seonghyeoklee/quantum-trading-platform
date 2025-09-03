// Lightweight Charts 공식 문서 기반 타입 정의
// https://tradingview.github.io/lightweight-charts/

export interface CandlestickData {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface LineData {
  time: string | number;
  value: number;
}

export interface HistogramData {
  time: string | number;
  value: number;
  color?: string;
}

export interface ChartConfig {
  symbol: string;
  timeframe: '1D' | '5D' | '1M' | '3M' | '1Y' | '5Y';
  showVolume: boolean;
  showMA: boolean;
  maPeriods: number[];
}

export interface ChartTheme {
  layout: {
    background: { type: 'solid'; color: string };
    textColor: string;
  };
  grid: {
    vertLines: { color: string };
    horzLines: { color: string };
  };
  crosshair: {
    mode: number;
  };
  priceScale: {
    borderColor: string;
  };
  timeScale: {
    borderColor: string;
    timeVisible: boolean;
    secondsVisible: boolean;
  };
}

export interface MovingAverageConfig {
  period: number;
  color: string;
  lineWidth: number;
}