export interface RealtimeCandleData {
  symbol: string;
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartUpdateData {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
