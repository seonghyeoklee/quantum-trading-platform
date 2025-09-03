// KIS 8000포트 국내 API 응답 타입 정의

/**
 * 국내 주식 현재가 정보
 */
export interface KISDomesticPrice {
  symbol: string;           // 종목코드
  name: string;            // 종목명
  price: number;           // 현재가
  change: number;          // 전일대비 (원)
  changePercent: number;   // 등락률 (%)
  volume: number;          // 거래량
  amount?: number;         // 거래대금
  high: number;            // 고가
  low: number;             // 저가
  open: number;            // 시가
  prevClose: number;       // 전일종가
  timestamp: string;       // 업데이트 시간
}

/**
 * 국내 주식 호가 정보
 */
export interface KISDomesticOrderbook {
  symbol: string;
  name: string;
  asks: Array<{           // 매도호가 (상위 10호가)
    price: number;
    quantity: number;
    total: number;
  }>;
  bids: Array<{           // 매수호가 (상위 10호가)
    price: number;
    quantity: number;
    total: number;
  }>;
  timestamp: string;
}

/**
 * 국내 주식 차트 데이터 (일봉/분봉)
 */
export interface KISDomesticChartItem {
  date: string;           // YYYYMMDD 또는 YYYYMMDDHHmm
  time?: string;          // 분봉용 시간 (HHmm)
  open: number;           // 시가
  high: number;           // 고가
  low: number;            // 저가
  close: number;          // 종가
  volume: number;         // 거래량
  amount?: number;        // 거래대금
}

export interface KISDomesticChart {
  symbol: string;
  name: string;
  period: 'daily' | 'minute';  // 차트 주기
  data: KISDomesticChartItem[];
  lastUpdate: string;
}

/**
 * 국내 주식 종목 기본정보
 */
export interface KISDomesticInfo {
  symbol: string;         // 종목코드
  name: string;           // 종목명
  market: string;         // 시장구분 (KOSPI, KOSDAQ)
  sector: string;         // 업종
  industry?: string;      // 세부업종
  listingDate: string;    // 상장일 (YYYYMMDD)
  shareCount: number;     // 상장주식수
  marketCap?: number;     // 시가총액
  faceValue: number;      // 액면가
  capital: number;        // 자본금
  per?: number;           // PER
  pbr?: number;           // PBR
  eps?: number;           // EPS
  bps?: number;           // BPS
  description?: string;   // 기업 개요
}

/**
 * 국내 주식 검색 결과
 */
export interface KISDomesticSearchItem {
  symbol: string;         // 종목코드
  name: string;           // 종목명
  market: string;         // 시장구분
  sector?: string;        // 업종
  price?: number;         // 현재가
  change?: number;        // 전일대비
  changePercent?: number; // 등락률
}

export interface KISDomesticSearchResult {
  query: string;          // 검색어
  total: number;          // 총 결과수
  items: KISDomesticSearchItem[];
}

/**
 * 국내 시장지수 정보
 */
export interface KISDomesticIndex {
  code: string;           // 지수코드
  name: string;           // 지수명
  value: number;          // 지수값
  change: number;         // 전일대비
  changePercent: number;  // 등락률
  volume?: number;        // 거래량
  amount?: number;        // 거래대금
  timestamp: string;      // 업데이트 시간
}

export interface KISDomesticIndices {
  kospi: KISDomesticIndex;    // 코스피
  kosdaq: KISDomesticIndex;   // 코스닥
  kospi200?: KISDomesticIndex; // 코스피200
  krx300?: KISDomesticIndex;   // KRX300
  lastUpdate: string;
}

/**
 * TradingView 차트용 캔들스틱 데이터 변환 타입
 */
export interface TradingViewCandle {
  time: number;           // Unix timestamp (seconds)
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

/**
 * API 에러 응답
 */
export interface KISApiError {
  error: string;
  message: string;
  code?: string;
  timestamp: string;
}