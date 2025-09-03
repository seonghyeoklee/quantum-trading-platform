// 차트 데이터 변환 및 계산 유틸리티
import { CandlestickData, LineData, HistogramData } from './types';

/**
 * Quantum 백엔드 API 데이터를 Lightweight Charts 형식으로 변환
 */
export function convertQuantumToChartData(apiResponse: any): CandlestickData[] { // eslint-disable-line @typescript-eslint/no-explicit-any
  console.log('🔄 convertQuantumToChartData 호출됨:', { 
    hasResponse: !!apiResponse,
    hasOutput2: !!apiResponse?.output2,
    output2Type: typeof apiResponse?.output2,
    output2Length: apiResponse?.output2?.length
  });
  
  // output2 배열에서 차트 데이터 추출
  const chartData = apiResponse?.output2;
  if (!Array.isArray(chartData)) {
    console.warn('⚠️ output2가 배열이 아닙니다:', { chartData, type: typeof chartData });
    return [];
  }
  
  const convertedData = chartData.map((item, index) => {
    // Quantum API 응답 형식에 따라 데이터 추출
    const time = item.stck_bsop_date || item.date;
    const open = parseFloat(item.stck_oprc || 0);
    const high = parseFloat(item.stck_hgpr || 0);
    const low = parseFloat(item.stck_lwpr || 0);
    const close = parseFloat(item.stck_clpr || 0);
    const volume = parseFloat(item.acml_vol || 0);

    const converted = {
      time: convertDateToTime(time),
      open: open,
      high: high,
      low: low,
      close: close,
      volume: volume > 0 ? volume : undefined
    };
    
    // 처음 몇 개 데이터 로그 출력
    if (index < 2) {
      console.log(`📊 데이터 변환 샘플 ${index}:`, {
        original: item,
        converted: converted,
        timeFormat: typeof converted.time,
        pricesValid: open > 0 && high > 0 && low > 0 && close > 0
      });
    }

    return converted;
  });
  
  const filteredData = convertedData.filter((item, index) => {
    // 유효한 데이터만 필터링
    const isValid = item.open > 0 && item.high > 0 && item.low > 0 && item.close > 0;
    if (!isValid && index < 3) {
      console.warn('❌ 유효하지 않은 데이터:', item);
    }
    return isValid;
  });
  
  const sortedData = filteredData.sort((a, b) => {
    // 시간순 정렬
    const timeA = typeof a.time === 'string' ? new Date(a.time).getTime() : Number(a.time);
    const timeB = typeof b.time === 'string' ? new Date(b.time).getTime() : Number(b.time);
    return timeA - timeB;
  });
  
  console.log('✅ 최종 데이터 변환 결과:', {
    원본: chartData.length,
    변환됨: convertedData.length,
    필터링됨: filteredData.length,
    정렬됨: sortedData.length,
    첫번째데이터: sortedData[0],
    마지막데이터: sortedData[sortedData.length - 1]
  });
  
  return sortedData;
}

/**
 * 레거시 KIS API 데이터를 Lightweight Charts 형식으로 변환 (호환성 유지)
 */
export function convertKISToChartData(kisData: any[]): CandlestickData[] { // eslint-disable-line @typescript-eslint/no-explicit-any
  if (!Array.isArray(kisData)) return [];
  
  return kisData.map(item => {
    // KIS API 응답 형식에 따라 데이터 추출
    const time = item.date || item.stck_bsop_dt || item.time || item.timestamp;
    const open = parseFloat(item.stck_oprc || item.open || item.o || 0);
    const high = parseFloat(item.stck_hgpr || item.high || item.h || 0);
    const low = parseFloat(item.stck_lwpr || item.low || item.l || 0);
    const close = parseFloat(item.stck_prpr || item.close || item.c || 0);
    const volume = parseFloat(item.cntg_vol || item.volume || item.v || 0);

    return {
      time: convertDateToTime(time),
      open: open,
      high: high,
      low: low,
      close: close,
      volume: volume > 0 ? volume : undefined
    };
  }).filter(item => 
    // 유효한 데이터만 필터링
    item.open > 0 && item.high > 0 && item.low > 0 && item.close > 0
  ).sort((a, b) => {
    // 시간순 정렬
    const timeA = typeof a.time === 'string' ? new Date(a.time).getTime() : Number(a.time);
    const timeB = typeof b.time === 'string' ? new Date(b.time).getTime() : Number(b.time);
    return timeA - timeB;
  });
}

/**
 * 날짜 문자열을 Lightweight Charts 시간 형식으로 변환
 */
export function convertDateToTime(dateStr: string): string {
  if (!dateStr) return new Date().toISOString().split('T')[0];
  
  // YYYYMMDD 형식을 YYYY-MM-DD로 변환
  if (dateStr.length === 8 && /^\d{8}$/.test(dateStr)) {
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
  }
  
  // 이미 올바른 형식이면 그대로 반환
  return dateStr;
}

/**
 * 단순 이동평균 계산
 */
export function calculateSMA(data: CandlestickData[], period: number): LineData[] {
  if (!data || data.length < period) return [];
  
  const smaData: LineData[] = [];
  
  for (let i = period - 1; i < data.length; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) {
      sum += data[j].close;
    }
    
    smaData.push({
      time: data[i].time,
      value: Math.round((sum / period) * 100) / 100
    });
  }
  
  return smaData;
}

/**
 * 거래량 데이터를 히스토그램 형식으로 변환
 */
export function convertToVolumeData(
  data: CandlestickData[], 
  upColor: string = '#ef4444', 
  downColor: string = '#3b82f6'
): HistogramData[] {
  return data
    .filter(item => item.volume !== undefined && item.volume > 0)
    .map(item => ({
      time: item.time,
      value: item.volume!,
      color: item.close >= item.open ? upColor : downColor
    }));
}

/**
 * 차트 테마 생성 (다크/라이트 모드)
 */
export function createChartTheme(isDark: boolean) {
  return {
    layout: {
      background: { type: 'solid' as const, color: isDark ? '#0f172a' : '#ffffff' },
      textColor: isDark ? '#f8fafc' : '#0f172a',
    },
    grid: {
      vertLines: { color: isDark ? '#334155' : '#e2e8f0' },
      horzLines: { color: isDark ? '#334155' : '#e2e8f0' },
    },
    crosshair: {
      mode: 1, // Normal crosshair mode
    },
    priceScale: {
      borderColor: isDark ? '#334155' : '#e2e8f0',
    },
    timeScale: {
      borderColor: isDark ? '#334155' : '#e2e8f0',
      timeVisible: true,
      secondsVisible: false,
    },
  };
}