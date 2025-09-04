'use client';

// KIS Adapter API 응답 인터페이스 (8000포트 직접 연동)
interface KISApiResponse {
  success: boolean;
  data: {
    records?: any[];
  } | any;
  message: string;
  timestamp: string;
}

// KIS API 원본 데이터 구조
interface KISRawChartItem {
  [key: string]: string; // 모든 필드가 문자열로 전달됨
}

// 기존 인터페이스 유지 (하위 호환성)
export interface KISChartData {
  date: string;      // YYYYMMDD
  open: number;      // 시가
  high: number;      // 고가
  low: number;       // 저가
  close: number;     // 종가
  volume: number;    // 거래량
  amount?: number;   // 거래대금 (선택적)
}

export interface KISCurrentPrice {
  symbol: string;
  price: number;           // 현재가
  change: number;          // 전일대비
  changePercent: number;   // 등락률
  volume: number;          // 당일 거래량
  amount?: number;         // 당일 거래대금
  timestamp: string;       // 업데이트 시간
}

export interface KISChartResponse {
  symbol: string;
  symbolName: string;
  market: 'domestic' | 'overseas';
  data: KISChartData[];
}

export type ChartPeriod = 'D' | 'W' | 'M';

// TradingView용 캔들 데이터 인터페이스
export interface TradingViewCandle {
  time: number;      // Unix timestamp
  open: number;      // 시가
  high: number;      // 고가
  low: number;       // 저가
  close: number;     // 종가
  volume?: number;   // 거래량 (선택적)
}

// KIS 8000포트 전용 차트 서비스 클래스
export class KISChartService {
  private readonly baseUrl = 'http://localhost:8000';
  
  /**
   * KIS 토큰 가져오기 (localStorage에서)
   */
  private getKISToken(): string | null {
    try {
      // SANDBOX 토큰 우선, 없으면 LIVE 토큰
      const sandboxToken = localStorage.getItem('kisToken_SANDBOX');
      const liveToken = localStorage.getItem('kisToken_LIVE');
      
      if (sandboxToken) {
        const tokenData = JSON.parse(sandboxToken);
        return tokenData.token;
      }
      
      if (liveToken) {
        const tokenData = JSON.parse(liveToken);
        return tokenData.token;
      }
      
      return null;
    } catch (error) {
      console.warn('KIS 토큰 가져오기 실패:', error);
      return null;
    }
  }
  /**
   * 국내 주식 일봉 차트 데이터 조회 (8000포트 직접 호출)
   * @param symbol 종목코드 (6자리)
   * @param count 조회 개수 (기본 100일)
   * @returns KIS 차트 데이터
   */
  async getDomesticDailyChart(symbol: string, count: number = 100): Promise<KISChartData[]> {
    try {
      console.log(`📊 KIS 8000포트 국내 일봉 데이터 직접 조회: ${symbol}`);
      
      // API URL 구성
      const url = `${this.baseUrl}/domestic/chart/daily/${symbol}?period=D&count=${count}`;
      
      // 요청 헤더 구성
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // KIS 토큰이 있으면 헤더에 추가
      const kisToken = this.getKISToken();
      if (kisToken) {
        headers['X-KIS-Token'] = kisToken;
      }
      
      // API 호출
      const response = await fetch(url, {
        method: 'GET',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
      }
      
      const apiData: KISApiResponse = await response.json();
      
      if (!apiData.success) {
        throw new Error(`API 응답 실패: ${apiData.message}`);
      }
      
      // 데이터 변환
      const records = apiData.data.records || apiData.data;
      const chartData = this.convertRawDataToKISChartData(records);
      
      console.log(`✅ KIS 8000포트 국내 일봉 데이터 완료: ${chartData.length}개`);
      return chartData;
      
    } catch (error) {
      console.error('❌ KIS 8000포트 국내 일봉 데이터 조회 실패:', error);
      throw error;
    }
  }

  /**
   * 국내 주식 분봉 차트 데이터 조회 (8000포트 직접 호출)
   * @param symbol 종목코드 (6자리)
   * @param count 조회 개수 (기본 100분)
   * @returns KIS 차트 데이터
   */
  async getDomesticMinuteChart(symbol: string, count: number = 100): Promise<KISChartData[]> {
    try {
      console.log(`📊 KIS 8000포트 국내 분봉 데이터 직접 조회: ${symbol}`);
      
      // API URL 구성
      const url = `${this.baseUrl}/domestic/chart/minute/${symbol}?period=1&count=${count}`;
      
      // 요청 헤더 구성
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      // KIS 토큰이 있으면 헤더에 추가
      const kisToken = this.getKISToken();
      if (kisToken) {
        headers['X-KIS-Token'] = kisToken;
      }
      
      // API 호출
      const response = await fetch(url, {
        method: 'GET',
        headers,
      });
      
      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
      }
      
      const apiData: KISApiResponse = await response.json();
      
      if (!apiData.success) {
        throw new Error(`API 응답 실패: ${apiData.message}`);
      }
      
      // 데이터 변환
      const records = apiData.data.records || apiData.data;
      const chartData = this.convertRawDataToKISChartData(records);
      
      console.log(`✅ KIS 8000포트 국내 분봉 데이터 완료: ${chartData.length}개`);
      return chartData;
      
    } catch (error) {
      console.error('❌ KIS 8000포트 국내 분봉 데이터 조회 실패:', error);
      throw error;
    }
  }

  /**
   * TradingView 차트용 캔들 데이터 조회 (8000포트 직접 호출)
   * @param symbol 종목코드
   * @param chartType 차트 타입 ('daily' | 'minute')
   * @returns TradingView 캔들 데이터
   */
  async getTradingViewCandles(symbol: string, chartType: 'daily' | 'minute' = 'daily'): Promise<TradingViewCandle[]> {
    try {
      console.log(`📈 TradingView 캔들 데이터 조회: ${symbol} (${chartType})`);
      
      // 직접 KIS 데이터 조회
      const kisData = chartType === 'daily' 
        ? await this.getDomesticDailyChart(symbol)
        : await this.getDomesticMinuteChart(symbol);
      
      // TradingView 형식으로 변환
      const candles = this.convertKISDataToTradingViewCandles(kisData, chartType);
      
      console.log(`✅ TradingView 캔들 데이터 완료: ${candles.length}개`);
      return candles;
      
    } catch (error) {
      console.error('❌ TradingView 캔들 데이터 조회 실패:', error);
      throw error;
    }
  }

  /**
   * 해외 주식 일봉 차트 데이터 조회 (미구현 - 다음 작업)
   * @param exchange 거래소 코드
   * @param symbol 티커
   * @param count 조회 개수
   */
  async getOverseasDailyChart(exchange: string, symbol: string, count: number = 365): Promise<KISChartData[]> {
    throw new Error('해외 차트는 다음 작업에서 구현 예정');
  }

  /**
   * KIS API 원본 데이터 → KISChartData[] 변환 (8000포트 전용)
   * @param records KIS API에서 받은 원본 데이터 (모든 필드가 문자열)
   */
  private convertRawDataToKISChartData(records: KISRawChartItem[]): KISChartData[] {
    if (!Array.isArray(records)) {
      console.warn('KIS API 데이터가 배열이 아닙니다:', records);
      return [];
    }

    return records.map(record => {
      // KIS API 실제 필드명 매핑 (현재가 API 응답 기준)
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, ''); // YYYYMMDD 형식
      
      return {
        date: record.stck_bsop_date || today, // 기준일자 (없으면 오늘 날짜)
        open: parseFloat(record.stck_oprc || '0'), // 시가
        high: parseFloat(record.stck_hgpr || '0'), // 고가 
        low: parseFloat(record.stck_lwpr || '0'), // 저가
        close: parseFloat(record.stck_prpr || record.stck_clpr || '0'), // 현재가 또는 종가
        volume: parseInt(record.acml_vol || '0'), // 거래량
        amount: record.acml_tr_pbmn ? parseFloat(record.acml_tr_pbmn) : undefined, // 거래대금 (선택적)
      };
    }).filter(item => item.close > 0); // 유효한 데이터만 필터링
  }

  /**
   * KISChartData[] → TradingViewCandle[] 변환
   */
  private convertKISDataToTradingViewCandles(items: KISChartData[], chartType: 'daily' | 'minute'): TradingViewCandle[] {
    return items.map(item => {
      let timeValue: number;
      
      if (chartType === 'daily') {
        // 일봉: 날짜 문자열을 Unix timestamp로 변환
        // "20241201" → Unix timestamp
        const year = parseInt(item.date.substring(0, 4));
        const month = parseInt(item.date.substring(4, 6)) - 1; // 0-based month
        const day = parseInt(item.date.substring(6, 8));
        timeValue = Math.floor(new Date(year, month, day).getTime() / 1000);
      } else {
        // 분봉: 날짜+시간을 Unix timestamp로 변환
        // "202412011030" → Unix timestamp
        if (item.date.length >= 12) {
          const year = parseInt(item.date.substring(0, 4));
          const month = parseInt(item.date.substring(4, 6)) - 1;
          const day = parseInt(item.date.substring(6, 8));
          const hour = parseInt(item.date.substring(8, 10));
          const minute = parseInt(item.date.substring(10, 12));
          timeValue = Math.floor(new Date(year, month, day, hour, minute).getTime() / 1000);
        } else {
          // 분봉인데 시간 정보가 없으면 일봉처럼 처리
          const year = parseInt(item.date.substring(0, 4));
          const month = parseInt(item.date.substring(4, 6)) - 1;
          const day = parseInt(item.date.substring(6, 8));
          timeValue = Math.floor(new Date(year, month, day, 9, 0).getTime() / 1000); // 09:00으로 기본값
        }
      }

      return {
        time: timeValue,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume,
      };
    }).sort((a, b) => a.time - b.time); // 시간순 정렬
  }

  /**
   * 국내 주식 일봉 차트 데이터 조회 (청크 단위로 분할 로딩)
   * @param symbol 종목코드 (6자리)
   * @param totalCount 전체 조회 개수 (기본 365일)
   * @param chunkSize 청크 크기 (기본 100일)
   * @returns KIS 차트 데이터
   */
  async getDomesticDailyChartChunked(symbol: string, totalCount: number = 365, chunkSize: number = 100): Promise<KISChartData[]> {
    try {
      console.log(`📊 KIS 8000포트 국내 일봉 데이터 청크 로딩: ${symbol} (총 ${totalCount}일)`);
      
      const allData: KISChartData[] = [];
      const chunks = Math.ceil(totalCount / chunkSize);
      
      for (let i = 0; i < chunks; i++) {
        const currentChunkSize = Math.min(chunkSize, totalCount - (i * chunkSize));
        const chunkData = await this.getDomesticDailyChart(symbol, currentChunkSize);
        allData.push(...chunkData);
        
        // 다음 청크 로딩 전 잠시 대기 (Rate Limiting 고려)
        if (i < chunks - 1) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }
      
      // 날짜순 정렬 (중복 제거)
      const uniqueData = allData
        .filter((item, index, arr) => 
          arr.findIndex(other => other.date === item.date) === index
        )
        .sort((a, b) => a.date.localeCompare(b.date));
      
      console.log(`✅ KIS 8000포트 국내 일봉 청크 로딩 완료: ${uniqueData.length}개`);
      return uniqueData;
      
    } catch (error) {
      console.error('❌ KIS 8000포트 국내 일봉 청크 로딩 실패:', error);
      throw error;
    }
  }
}

// 싱글톤 인스턴스
export const kisChartService = new KISChartService();