// 키움 종목 기본 정보 API 서비스

import { 
  KiwoomStockBasicInfoResponse, 
  KiwoomStockBasicInfoBody,
  StockBasicInfo, 
  StockSearchRequest,
  StockInfoCache,
  StockInfoApiError 
} from './stock-info-types';

class StockInfoService {
  private readonly baseUrl: string;
  private cache: StockInfoCache = {};
  private readonly cacheTTL: number = 5 * 60 * 1000; // 5분 캐시

  constructor(baseUrl: string = 'http://localhost:8100') {
    this.baseUrl = baseUrl;
  }

  /**
   * 종목 기본 정보 조회
   */
  async getStockBasicInfo(symbol: string): Promise<StockBasicInfo> {
    // 캐시 확인
    const cachedData = this.getCachedData(symbol);
    if (cachedData) {
      console.log('📦 캐시에서 종목 정보 반환:', symbol);
      return cachedData;
    }

    try {
      console.log('🔍 키움 API 종목 정보 조회 요청:', symbol);
      
      const request: StockSearchRequest = {
        stk_cd: symbol
      };

      const response = await fetch(`${this.baseUrl}/api/fn_ka10001?cont_yn=N`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const apiResponse: KiwoomStockBasicInfoResponse = await response.json();
      
      if (apiResponse.Code !== 200) {
        throw new Error(`키움 API 오류: ${apiResponse.Code}`);
      }

      if (apiResponse.Body.return_code !== 0) {
        throw new Error(`키움 처리 오류: ${apiResponse.Body.return_msg}`);
      }

      console.log('✅ 키움 API 종목 정보 조회 성공:', symbol, apiResponse.Body);

      // 응답 데이터를 프론트엔드 형식으로 변환
      const stockInfo = this.transformApiResponse(apiResponse.Body);
      
      // 캐시에 저장
      this.setCacheData(symbol, stockInfo);

      return stockInfo;

    } catch (error) {
      console.error('❌ 종목 정보 조회 실패:', symbol, error);
      
      const apiError: StockInfoApiError = {
        code: error instanceof Error ? -1 : (error as any).code || -1,
        message: error instanceof Error ? error.message : '알 수 없는 오류',
        detail: error instanceof Error ? error.stack : undefined,
        timestamp: new Date().toISOString()
      };
      
      throw apiError;
    }
  }

  /**
   * 키움 API 응답을 프론트엔드 형식으로 변환
   */
  private transformApiResponse(body: KiwoomStockBasicInfoBody): StockBasicInfo {
    const parseNumber = (value: string): number => {
      if (!value) return 0;
      // 키움 데이터의 특수 처리: +, - 기호 및 쉼표 제거
      const cleaned = value.replace(/[+,]/g, '').trim();
      return parseFloat(cleaned) || 0;
    };

    const parseDate = (value: string): string => {
      if (!value || value.length !== 8) return '';
      // YYYYMMDD -> YYYY-MM-DD
      return `${value.substr(0, 4)}-${value.substr(4, 2)}-${value.substr(6, 2)}`;
    };

    // 등락 방향 결정
    const getChangeDirection = (code: string): 'up' | 'down' | 'unchanged' => {
      switch (code) {
        case '1': // 상한
        case '2': // 상승
          return 'up';
        case '4': // 하한
        case '5': // 하락
          return 'down';
        case '3': // 보합
        default:
          return 'unchanged';
      }
    };

    return {
      // 기본 정보
      symbol: body.stk_cd,
      name: body.stk_nm,
      
      // 현재가 정보
      currentPrice: Math.abs(parseNumber(body.cur_prc)), // 현재가는 항상 양수
      change: parseNumber(body.pred_pre), // 전일대비는 음수 허용
      changePercent: parseNumber(body.flu_rt), // 등락률은 음수 허용
      changeDirection: getChangeDirection(body.pre_sig),
      
      // 당일 거래 정보
      openPrice: Math.abs(parseNumber(body.open_pric)),
      highPrice: Math.abs(parseNumber(body.high_pric)),
      lowPrice: Math.abs(parseNumber(body.low_pric)),
      volume: parseNumber(body.trde_qty),
      tradingValue: parseNumber(body.trde_pre),
      
      // 가격 범위 정보
      upperLimit: Math.abs(parseNumber(body.upl_pric)),
      lowerLimit: Math.abs(parseNumber(body.lst_pric)),
      basePrice: parseNumber(body.base_pric),
      week52High: Math.abs(parseNumber(body["250hgst"])),
      week52Low: Math.abs(parseNumber(body["250lwst"])),
      week52HighDate: parseDate(body["250hgst_pric_dt"]),
      week52LowDate: parseDate(body["250lwst_pric_dt"]),
      yearHigh: Math.abs(parseNumber(body.oyr_hgst)),
      yearLow: Math.abs(parseNumber(body.oyr_lwst)),
      
      // 재무 지표
      per: parseNumber(body.per),
      pbr: parseNumber(body.pbr),
      roe: parseNumber(body.roe),
      eps: parseNumber(body.eps),
      bps: parseNumber(body.bps),
      evEbitda: parseNumber(body.ev),
      
      // 회사 정보
      faceValue: parseNumber(body.fav),
      marketCap: parseNumber(body.cap),
      listedShares: parseNumber(body.mac),
      floatingShares: parseNumber(body.flo_stk),
      circulatingShares: parseNumber(body.dstr_stk),
      circulatingRatio: parseNumber(body.dstr_rt),
      
      // 외국인/기관 정보
      foreignOwnership: parseNumber(body.for_exh_rt),
      creditRatio: parseNumber(body.crd_rt),
      
      // 재무 성과
      revenue: parseNumber(body.sale_amt),
      operatingProfit: parseNumber(body.bus_pro),
      netIncome: parseNumber(body.cup_nga),
      
      // 메타 정보
      settlementMonth: parseNumber(body.setl_mm),
      lastUpdated: new Date().toISOString()
    };
  }

  /**
   * 캐시에서 데이터 조회
   */
  private getCachedData(symbol: string): StockBasicInfo | null {
    const cached = this.cache[symbol];
    if (!cached) return null;

    const now = Date.now();
    if (now - cached.timestamp > cached.ttl) {
      // 캐시 만료
      delete this.cache[symbol];
      return null;
    }

    return cached.data;
  }

  /**
   * 캐시에 데이터 저장
   */
  private setCacheData(symbol: string, data: StockBasicInfo): void {
    this.cache[symbol] = {
      data,
      timestamp: Date.now(),
      ttl: this.cacheTTL
    };
  }

  /**
   * 캐시 수동 무효화
   */
  invalidateCache(symbol?: string): void {
    if (symbol) {
      delete this.cache[symbol];
      console.log('🗑️ 종목 캐시 무효화:', symbol);
    } else {
      this.cache = {};
      console.log('🗑️ 전체 종목 캐시 무효화');
    }
  }

  /**
   * 캐시 상태 조회
   */
  getCacheStatus(): { total: number; symbols: string[] } {
    const symbols = Object.keys(this.cache);
    return {
      total: symbols.length,
      symbols
    };
  }

  /**
   * 여러 종목 동시 조회 (배치)
   */
  async getMultipleStockInfo(symbols: string[]): Promise<StockBasicInfo[]> {
    console.log('📊 여러 종목 정보 배치 조회:', symbols);
    
    const promises = symbols.map(symbol => 
      this.getStockBasicInfo(symbol).catch(error => {
        console.warn(`⚠️ 종목 ${symbol} 조회 실패:`, error);
        return null;
      })
    );

    const results = await Promise.all(promises);
    return results.filter((result): result is StockBasicInfo => result !== null);
  }

  /**
   * 캐시 프리워밍 (자주 조회되는 종목들을 미리 로드)
   */
  async preloadPopularStocks(): Promise<void> {
    const popularSymbols = [
      '005930', // 삼성전자
      '000660', // SK하이닉스
      '035420', // NAVER
      '207940', // 삼성바이오로직스
      '005380', // 현대차
    ];

    console.log('🚀 인기 종목 프리로딩 시작:', popularSymbols);
    
    try {
      await this.getMultipleStockInfo(popularSymbols);
      console.log('✅ 인기 종목 프리로딩 완료');
    } catch (error) {
      console.error('❌ 인기 종목 프리로딩 실패:', error);
    }
  }
}

// 싱글톤 인스턴스
export const stockInfoService = new StockInfoService();

// 편의 함수들
export const getStockBasicInfo = (symbol: string) => stockInfoService.getStockBasicInfo(symbol);
export const getMultipleStockInfo = (symbols: string[]) => stockInfoService.getMultipleStockInfo(symbols);
export const invalidateStockCache = (symbol?: string) => stockInfoService.invalidateCache(symbol);
export const preloadPopularStocks = () => stockInfoService.preloadPopularStocks();

export default stockInfoService;