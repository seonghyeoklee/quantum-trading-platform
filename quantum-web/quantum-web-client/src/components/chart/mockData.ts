import { CandlestickData, StockInfo } from './ChartTypes';

// Mock 삼성전자 데이터 생성 함수
const generateMockData = (days: number, basePrice: number = 71400): CandlestickData[] => {
  const data: CandlestickData[] = [];
  const startDate = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(startDate);
    date.setDate(date.getDate() - i);
    
    // 이전 데이터의 종가를 다음 데이터의 시가로 사용
    const previousClose = i === days - 1 ? basePrice : data[data.length - 1]?.close || basePrice;
    
    // 랜덤한 변동성을 추가
    const volatility = 0.02; // 2% 변동성
    const change = (Math.random() - 0.5) * 2 * volatility;
    
    const open = previousClose * (1 + (Math.random() - 0.5) * 0.005);
    const close = open * (1 + change);
    const high = Math.max(open, close) * (1 + Math.random() * 0.01);
    const low = Math.min(open, close) * (1 - Math.random() * 0.01);
    
    data.push({
      time: date.toISOString().split('T')[0],
      open: Math.round(open),
      high: Math.round(high),
      low: Math.round(low),
      close: Math.round(close),
    });
  }
  
  return data;
};

// 시간대별 Mock 데이터
export const mockSamsungData = {
  '1D': generateMockData(1),
  '5D': generateMockData(5), 
  '1M': generateMockData(30),
  '3M': generateMockData(90),
  '1Y': generateMockData(365),
  'ALL': generateMockData(365 * 3), // 3년치 데이터
};

export const mockStockInfo: StockInfo = {
  symbol: '005930',
  name: '삼성전자',
  price: 71400,
  change: -900,
  changePercent: -1.24,
  market: 'KOSPI'
};

// Mock 데이터는 이제 실제 API 연동으로 교체됨
// 필요시 테스트용으로만 사용