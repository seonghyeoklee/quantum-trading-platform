import {
  KiwoomApiRequest,
  KiwoomApiResponse,
  KiwoomDailyApiResponse,
  KiwoomMinuteApiResponse,
  KiwoomTickApiResponse,
  KiwoomWeeklyApiResponse,
  KiwoomMonthlyApiResponse,
  KiwoomYearlyApiResponse,
  KiwoomChartData,
  KiwoomDailyChartData,
  KiwoomMinuteChartData,
  KiwoomTickChartData,
  CHART_API_ENDPOINTS,
  TIMEFRAME_TO_CHART_TYPE,
  DEFAULT_TIC_SCOPE,
  KiwoomStockListRequest,
  KiwoomStockListApiResponse,
  KiwoomStockInfo,
  MARKET_TYPES
} from './kiwoom-types';
import { ChartTimeframe, ChartType, CandlestickData } from '@/components/chart/ChartTypes';

const KIWOOM_API_BASE_URL = 'http://localhost:8100';

class KiwoomApiService {

  /**
   * 키움 차트 API 호출
   */
  async fetchChartData(
    symbol: string,
    chartType: ChartType,
    ticScope?: string,
    baseDate?: string,
    continuePrev?: { cont_yn: string; next_key: string }
  ): Promise<KiwoomApiResponse> {

    const endpoint = CHART_API_ENDPOINTS[chartType];
    const url = `${KIWOOM_API_BASE_URL}${endpoint}`;

    // 요청 데이터 구성
    const requestData: KiwoomApiRequest = {
      data: {
        stk_cd: symbol,
        upd_stkpc_tp: "1", // 수정주가 적용
      },
      cont_yn: continuePrev?.cont_yn || "N",
      next_key: continuePrev?.next_key || "",
    };

    // 차트 타입별 파라미터 추가
    if (chartType === 'tick' || chartType === 'minute') {
      requestData.data.tic_scope = ticScope || DEFAULT_TIC_SCOPE[chartType] || "1";
    }

    if (chartType === 'daily' || chartType === 'weekly' || chartType === 'monthly' || chartType === 'yearly') {
      requestData.data.base_dt = baseDate || this.getCurrentDate();
    }

    console.log('키움 API 요청:', { url, requestData });

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`API 요청 실패: ${response.status} ${response.statusText}`);
      }

      const data: KiwoomApiResponse = await response.json();

      console.log('키움 API 응답:', data);

      if (data.Code !== 200) {
        throw new Error(`키움 API 에러: HTTP ${data.Code}`);
      }

      return data;

    } catch (error) {
      console.error('키움 API 호출 에러:', error);
      throw error;
    }
  }

  /**
   * 차트 타입별 직접 조회 (사용자가 차트 타입을 직접 선택)
   */
  async getChartDataByType(
    symbol: string,
    chartType: ChartType,
    timeframe?: ChartTimeframe
  ): Promise<CandlestickData[]> {
    let allData: KiwoomChartData[] = [];
    let nextKey = "";
    let hasMore = true;

    console.log(`🎯 ${symbol} ${chartType} 차트 데이터 직접 요청 시작`);

    try {
      // 연속조회로 충분한 데이터 수집
      const maxDataLimit = chartType === 'daily' ? 2000 : chartType === 'monthly' ? 500 : 1000;
      while (hasMore && allData.length < maxDataLimit) {
        const continuePrev = nextKey ? { cont_yn: "Y", next_key: nextKey } : undefined;

        const response = await this.fetchChartData(
          symbol,
          chartType,
          undefined, // ticScope는 기본값 사용
          undefined, // baseDate는 현재 날짜 사용
          continuePrev
        );

        // 차트 타입별로 적절한 데이터 필드 선택
        const chartData = this.extractChartDataFromResponse(response, chartType);
        allData = [...allData, ...chartData];
        nextKey = response.Header["next-key"];
        hasMore = nextKey && nextKey.trim() !== "";

        console.log(`🔍 [${chartType}] 데이터 수집: ${chartData.length}개 추가, 총 ${allData.length}개`);

        // 너무 빈번한 요청 방지
        if (hasMore) {
          await this.sleep(100); // 100ms 대기
        }
      }

      // timeframe이 주어진 경우에만 필터링 적용
      let filteredData = allData;
      if (timeframe) {
        filteredData = this.filterDataByTimeframe(allData, timeframe);
      }

      console.log(`🎯 최종 데이터: ${filteredData.length}개`);

      const convertedData = this.convertToChartData(filteredData);
      console.log(`📈 변환 후 차트 데이터: ${convertedData.length}개`);
      
      return convertedData;

    } catch (error) {
      console.error(`차트 데이터 조회 실패 (${symbol}, ${chartType}):`, error);
      throw error;
    }
  }

  /**
   * 시간대별 차트 데이터 조회 (기존 방식 - 호환성 유지)
   */
  async getChartDataByTimeframe(
    symbol: string,
    timeframe: ChartTimeframe
  ): Promise<CandlestickData[]> {

    const chartType = TIMEFRAME_TO_CHART_TYPE[timeframe];
    let allData: KiwoomChartData[] = [];
    let nextKey = "";
    let hasMore = true;

    console.log(`${symbol} ${timeframe} 차트 데이터 요청 시작 (차트타입: ${chartType})`);

    try {
      // 연속조회로 충분한 데이터 수집 - 더 많은 데이터 수집
      const maxDataLimit = timeframe === '1Y' ? 2000 : timeframe === '3M' ? 500 : 1000;
      while (hasMore && allData.length < maxDataLimit) {
        const continuePrev = nextKey ? { cont_yn: "Y", next_key: nextKey } : undefined;

        const response = await this.fetchChartData(
          symbol,
          chartType,
          undefined, // ticScope는 기본값 사용
          undefined, // baseDate는 현재 날짜 사용
          continuePrev
        );

        // 차트 타입별로 적절한 데이터 필드 선택
        const chartData = this.extractChartDataFromResponse(response, chartType);
        allData = [...allData, ...chartData];
        nextKey = response.Header["next-key"];
        hasMore = nextKey && nextKey.trim() !== "";

        console.log(`🔍 [단계 ${allData.length <= chartData.length ? '1' : '2+'}] 데이터 수집: ${chartData.length}개 추가, 총 ${allData.length}개`);
        
        // 첫 번째 수집에서 샘플 데이터 확인
        if (allData.length <= chartData.length && chartData.length > 0) {
          console.log('📊 수집된 데이터 샘플:', {
            첫번째: chartData[0],
            마지막: chartData[chartData.length - 1],
            타입확인: typeof chartData[0]
          });
        }

        // 너무 빈번한 요청 방지
        if (hasMore) {
          await this.sleep(100); // 100ms 대기
        }
      }

      // 시간대별 필터링
      const filteredData = this.filterDataByTimeframe(allData, timeframe);

      console.log(`🎯 최종 데이터: ${filteredData.length}개`);

      const convertedData = this.convertToChartData(filteredData);
      console.log(`📈 변환 후 차트 데이터: ${convertedData.length}개`);
      
      return convertedData;

    } catch (error) {
      console.error(`차트 데이터 조회 실패 (${symbol}, ${timeframe}):`, error);
      throw error;
    }
  }

  /**
   * API 응답에서 차트 타입별 데이터 추출
   */
  private extractChartDataFromResponse(response: KiwoomApiResponse, chartType: ChartType): KiwoomChartData[] {
    switch (chartType) {
      case 'tick':
        return (response as KiwoomTickApiResponse).Body.stk_tic_chart_qry || [];
      case 'minute':
        return (response as KiwoomMinuteApiResponse).Body.stk_min_pole_chart_qry || [];
      case 'daily':
        return (response as KiwoomDailyApiResponse).Body.stk_dt_pole_chart_qry || [];
      case 'weekly':
        return (response as KiwoomWeeklyApiResponse).Body.stk_stk_pole_chart_qry || [];
      case 'monthly':
        return (response as KiwoomMonthlyApiResponse).Body.stk_mth_pole_chart_qry || [];
      case 'yearly':
        return (response as KiwoomYearlyApiResponse).Body.stk_yr_pole_chart_qry || [];
      default:
        console.warn(`Unknown chart type: ${chartType}`);
        return [];
    }
  }

  /**
   * 키움 데이터를 차트 데이터로 변환
   */
  private convertToChartData(data: KiwoomChartData[]): CandlestickData[] {
    console.log('convertToChartData 시작:', { 원본데이터수: data.length, 샘플데이터: data.slice(0, 2) });

    const converted = data
      .map((item, index) => {
        const timeFormatted = this.formatTimeForChart(item);
        const result = {
          time: timeFormatted,
          open: parseFloat(item.open_pric || '0'),
          high: parseFloat(item.high_pric || '0'),
          low: parseFloat(item.low_pric || '0'),
          close: parseFloat(item.cur_prc || '0'),
          volume: parseFloat(item.trde_qty || '0'),
        };
        
        // 처음 몇 개 데이터의 변환 과정 상세 로깅
        if (index < 3) {
          console.log(`📊 키움 API 데이터 변환 상세 [${index}]:`, {
            원본: item,
            시간변환: { 
              원본필드: ('dt' in item ? item.dt : 'cntr_tm' in item ? item.cntr_tm : 'unknown'), 
              변환후: timeFormatted, 
              타입: typeof timeFormatted 
            },
            OHLCV: { 
              open: result.open, high: result.high, 
              low: result.low, close: result.close, volume: result.volume 
            }
          });
        }
        
        return result;
      })
      .filter(item => !isNaN(item.open) && !isNaN(item.high) && !isNaN(item.low) && !isNaN(item.close))
      .filter(item => item.open > 0 && item.high > 0 && item.low > 0 && item.close > 0) // 0인 데이터 제외
      .sort((a, b) => a.time.localeCompare(b.time)); // 시간순 정렬

    console.log('convertToChartData 완료:', { 변환된데이터수: converted.length, 샘플변환데이터: converted.slice(0, 2) });

    return converted;
  }

  /**
   * 시간대별 데이터 필터링
   */
  private filterDataByTimeframe(data: KiwoomChartData[], timeframe: ChartTimeframe): KiwoomChartData[] {
    console.log(`🔧 필터링 시작: ${timeframe}, 원본 데이터: ${data.length}개`);
    
    // 분봉/틱 데이터는 실시간이므로 모든 데이터를 반환
    if (data.length > 0 && 'cntr_tm' in data[0]) {
      console.log('분봉/틱 데이터 - 필터링 없이 모든 데이터 반환');
      return data;
    }

    // 일봉 데이터만 시간대별 필터링 적용 - 한국 시간 기준
    const systemNow = new Date();
    const now = new Date(systemNow.toLocaleString("en-US", {timeZone: "Asia/Seoul"}));
    
    console.log(`📅 현재 날짜 확인: ${now.toISOString()} (${now.getFullYear()}년 ${now.getMonth() + 1}월 ${now.getDate()}일)`);
    console.log(`🌍 시스템 시간: ${systemNow.toISOString()}`);
    
    const cutoffDate = new Date(now);

    switch (timeframe) {
      case '1D':
        // 1일이지만 30일치 데이터 제공 (스크롤 가능)
        cutoffDate.setDate(now.getDate() - 30);
        break;
      case '5D':
        // 5일이지만 60일치 데이터 제공
        cutoffDate.setDate(now.getDate() - 60);
        break;
      case '1M':
        // 1개월이지만 6개월치 데이터 제공
        const targetMonth1M = now.getMonth() - 6;
        if (targetMonth1M < 0) {
          cutoffDate.setFullYear(now.getFullYear() - 1);
          cutoffDate.setMonth(targetMonth1M + 12);
        } else {
          cutoffDate.setMonth(targetMonth1M);
        }
        break;
      case '3M':
        // 3개월이지만 1년치 데이터 제공
        cutoffDate.setFullYear(now.getFullYear() - 1);
        break;
      case '1Y':
        // 1년이지만 2년치 데이터 제공
        cutoffDate.setFullYear(now.getFullYear() - 2);
        break;
      case 'ALL':
        console.log('ALL 선택 - 전체 데이터 반환');
        return data; // 전체 데이터 반환
    }

    const cutoffString = this.formatDateForFilter(cutoffDate);
    console.log(`📍 계산된 기준일: ${cutoffDate.toISOString()} (${cutoffDate.getFullYear()}년 ${cutoffDate.getMonth() + 1}월 ${cutoffDate.getDate()}일)`);
    console.log(`📍 필터링 기준일 문자열: ${cutoffString} (${timeframe} 기간)`);

    const filtered = data.filter(item => {
      const dailyItem = item as KiwoomDailyChartData;
      return dailyItem.dt >= cutoffString;
    });

    console.log(`✅ 필터링 완료: ${filtered.length}개 (원본 ${data.length}개 → 필터링 ${filtered.length}개)`);
    
    if (filtered.length > 0) {
      console.log('필터링 후 날짜 범위:', {
        첫번째: filtered[0],
        마지막: filtered[filtered.length - 1]
      });
    }
    
    return filtered;
  }

  /**
   * 현재 날짜를 YYYYMMDD 형식으로 반환
   */
  private getCurrentDate(): string {
    // 한국 시간 기준으로 현재 날짜 가져오기
    const now = new Date();
    const koreaTime = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Seoul"}));
    
    console.log(`🕒 시스템 현재 시간: ${now.toISOString()}`);
    console.log(`🇰🇷 한국 현재 시간: ${koreaTime.toISOString()}`);
    
    const year = koreaTime.getFullYear();
    const month = String(koreaTime.getMonth() + 1).padStart(2, '0');
    const day = String(koreaTime.getDate()).padStart(2, '0');
    
    const dateString = `${year}${month}${day}`;
    console.log(`📅 현재 날짜 문자열: ${dateString}`);
    
    return dateString;
  }

  /**
   * 차트 데이터의 시간 포맷팅 (일봉/분봉/틱 구분)
   */
  private formatTimeForChart(item: KiwoomChartData): string {
    // 분봉/틱 데이터인 경우 (cntr_tm 필드 존재)
    if ('cntr_tm' in item) {
      const minuteData = item as KiwoomMinuteChartData | KiwoomTickChartData;
      // 현재 날짜 + 체결시간으로 구성 (YYYY-MM-DD HH:MM:SS)
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');

      const timeStr = minuteData.cntr_tm || '000000';
      const hour = timeStr.substring(0, 2);
      const minute = timeStr.substring(2, 4);
      const second = timeStr.substring(4, 6);

      const result = `${year}-${month}-${day} ${hour}:${minute}:${second}`;
      console.log(`⏰ 분봉/틱 시간 변환:`, { 
        원본cntr_tm: minuteData.cntr_tm, 
        변환결과: result, 
        타입: typeof result 
      });
      return result;
    }

    // 일봉 데이터인 경우 (dt 필드 사용)
    const dailyData = item as KiwoomDailyChartData;
    const result = this.formatDateForChart(dailyData.dt);
    console.log(`📅 일봉 시간 변환:`, { 
      원본dt: dailyData.dt, 
      변환결과: result, 
      타입: typeof result 
    });
    return result;
  }

  /**
   * YYYYMMDD를 차트용 날짜 형식으로 변환
   */
  private formatDateForChart(dateString: string): string {
    const year = dateString.substring(0, 4);
    const month = dateString.substring(4, 6);
    const day = dateString.substring(6, 8);
    return `${year}-${month}-${day}`;
  }

  /**
   * Date 객체를 YYYYMMDD 형식으로 변환 (필터링용) - 한국시간 기준
   */
  private formatDateForFilter(date: Date): string {
    // 이미 한국시간으로 변환된 Date 객체를 받으므로 그대로 사용
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const formatted = `${year}${month}${day}`;
    
    console.log(`🔢 날짜 포맷팅: ${date.toISOString()} → ${formatted}`);
    return formatted;
  }

  /**
   * 지연 실행 (API 호출 간격 조정용)
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 종목 리스트 조회 (fn_ka10099)
   * @param marketType 시장구분 (0:코스피, 10:코스닥, 8:ETF 등)
   * @param searchQuery 검색어 (종목명 필터링용)
   * @returns 종목 정보 배열
   */
  async getStockList(
    marketType: string = MARKET_TYPES.KOSPI,
    searchQuery?: string
  ): Promise<KiwoomStockInfo[]> {
    console.log(`📋 종목 리스트 조회 시작: 시장=${marketType}, 검색어="${searchQuery || '전체'}"`);
    
    try {
      const requestData: KiwoomStockListRequest = {
        mrkt_tp: marketType
      };

      console.log(`🔗 API 요청:`, requestData);

      const response = await fetch(`/api/kiwoom/fn_ka10099?cont_yn=N`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`종목 리스트 API 호출 실패: ${response.status} ${response.statusText}`);
      }

      const apiResponse: KiwoomStockListApiResponse = await response.json();
      console.log(`✅ API 원본 응답:`, apiResponse);
      console.log(`📊 응답 구조:`, { 
        코드: apiResponse.Code, 
        Header: apiResponse.Header,
        Body: apiResponse.Body,
        종목수: apiResponse.Body?.list?.length || 0 
      });

      if (apiResponse.Code !== 200) {
        throw new Error(`API 에러 코드: ${apiResponse.Code}`);
      }

      let stockList = apiResponse.Body?.list || [];
      console.log('🏢 원본 종목 리스트 첫 3개:', stockList.slice(0, 3));
      
      // 검색어 필터링
      if (searchQuery && searchQuery.trim()) {
        const query = searchQuery.trim().toLowerCase();
        stockList = stockList.filter(stock => 
          stock.name.toLowerCase().includes(query) || 
          stock.code.includes(query)
        );
        console.log(`🔍 검색어 "${searchQuery}" 필터링 결과: ${stockList.length}개`);
      }

      // 가격 정보가 있는 종목만 필터링 (차트 조회 가능한 종목)
      const validStocks = stockList.filter(stock => 
        stock.lastPrice && 
        stock.lastPrice !== '0' && 
        stock.state !== '상장폐지'
      );

      console.log(`📊 최종 종목 리스트: ${validStocks.length}개`);
      
      return validStocks;

    } catch (error) {
      console.error(`❌ 종목 리스트 조회 실패:`, error);
      throw error;
    }
  }

  /**
   * 인기 종목 리스트 조회 (KOSPI + KOSDAQ 대형주)
   */
  async getPopularStocks(): Promise<KiwoomStockInfo[]> {
    try {
      console.log('🔥 인기 종목 리스트 조회 시작');
      
      // KOSPI 대형주 + KOSDAQ 주요종목 병렬 조회
      const [kospiStocks, kosdaqStocks] = await Promise.all([
        this.getStockList(MARKET_TYPES.KOSPI),
        this.getStockList(MARKET_TYPES.KOSDAQ)
      ]);

      // 시가총액 기준 상위 종목들 (전일종가 * 상장주식수가 큰 순)
      const allStocks = [...kospiStocks, ...kosdaqStocks];
      
      const popularStocks = allStocks
        .filter(stock => parseInt(stock.lastPrice) > 1000) // 1천원 이상
        .sort((a, b) => {
          // 간단한 시가총액 추정 (전일종가 * 상장주식수)
          const marketCapA = parseInt(a.lastPrice) * parseInt(a.listCount);
          const marketCapB = parseInt(b.lastPrice) * parseInt(b.listCount);
          return marketCapB - marketCapA;
        })
        .slice(0, 50); // 상위 50개
      
      console.log(`🏆 인기 종목 추출 완료: ${popularStocks.length}개`);
      
      return popularStocks;
      
    } catch (error) {
      console.error('❌ 인기 종목 조회 실패:', error);
      // 에러 시 기본 종목들 반환
      return [];
    }
  }
}

// 싱글톤 인스턴스 생성
export const kiwoomApiService = new KiwoomApiService();
