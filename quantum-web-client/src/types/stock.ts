// 기존 DomesticStock 인터페이스 확장
export interface DomesticStock {
  stockCode: string;
  stockName: string;
  marketType: 'KOSPI' | 'KOSDAQ';
  isActive: boolean;
  sectorCode?: string;
  listingDate?: string;
}

export interface StockListResponse {
  stocks: DomesticStock[];
  totalCount: number;
  currentPage: number;
  totalPages: number;
  pageSize: number;
}

// 새로 추가된 KIS API 상세 정보 타입들

/**
 * 가격 변동 구분
 */
export enum PriceChangeSign {
  RISE = 'RISE',
  FLAT = 'FLAT', 
  FALL = 'FALL',
  UNKNOWN = 'UNKNOWN'
}

/**
 * KIS API 상세 정보
 */
export interface KisStockDetailInfo {
  // 현재가 정보
  currentPrice: number;              // 현재가
  previousDayChange: number;         // 전일대비
  changeRate: number;                // 등락률 (%)
  changeSign: PriceChangeSign;       // 등락 구분
  volume: number;                    // 거래량
  tradeAmount: number;               // 거래대금 (백만원)
  
  // 가격 정보
  openPrice: number;                 // 시가
  highPrice: number;                 // 고가
  lowPrice: number;                  // 저가
  upperLimit: number;                // 상한가
  lowerLimit: number;                // 하한가
  
  // 재무비율
  per: number;                       // PER
  pbr: number;                       // PBR
  eps: number;                       // EPS
  bps: number;                       // BPS
  marketCap: number;                 // 시가총액 (억원)
  
  // 기술적 지표
  week52High: number;                // 52주 최고가
  week52Low: number;                 // 52주 최저가
  week52HighDate: string;            // 52주 최고가 달성일
  week52LowDate: string;             // 52주 최저가 달성일
  day250High: number;                // 250일 최고가
  day250Low: number;                 // 250일 최저가
  yearHigh: number;                  // 연중 최고가
  yearLow: number;                   // 연중 최저가
  
  // 시장 정보
  foreignOwnership: number;          // 외국인 지분율 (%)
  volumeTurnover: number;            // 거래량 회전율
  marketName: string;                // 시장명
  sectorName: string;                // 업종명
  
  // 기타 정보
  listedShares: number;              // 상장주수
  settlementMonth: string;           // 결산월
  capital: string;                   // 자본금
  faceValue: number;                 // 액면가
}

/**
 * KIS API 상세 정보가 포함된 종목 정보
 */
export interface DomesticStockWithKisDetail {
  // 기본 종목 정보
  stockCode: string;
  stockName: string;
  marketType: 'KOSPI' | 'KOSDAQ';
  sectorCode?: string;
  listingDate?: string;
  
  // KIS API 실시간 데이터
  kisDetail?: KisStockDetailInfo;
  dataUpdatedAt?: string;
}

/**
 * 주가 변동 표시용 유틸리티 타입
 */
export interface PriceChangeDisplay {
  sign: PriceChangeSign;
  color: 'text-red-600' | 'text-blue-600' | 'text-gray-600';
  symbol: '▲' | '▼' | '-' | '?';
  bgColor: 'bg-red-50' | 'bg-blue-50' | 'bg-gray-50';
}

/**
 * 재무비율 표시용 그룹
 */
export interface FinancialRatios {
  per: number;
  pbr: number;
  eps: number;
  bps: number;
  marketCap: number;
}

/**
 * 기술적 지표 표시용 그룹
 */
export interface TechnicalIndicators {
  week52High: number;
  week52Low: number;
  week52HighDate: string;
  week52LowDate: string;
  day250High: number;
  day250Low: number;
  yearHigh: number;
  yearLow: number;
}

/**
 * 시장 정보 표시용 그룹
 */
export interface MarketInfo {
  foreignOwnership: number;
  volumeTurnover: number;
  marketName: string;
  sectorName: string;
  listedShares: number;
}

// 유틸리티 함수들

/**
 * 가격 변동 구분에 따른 표시 정보 반환
 */
export const getPriceChangeDisplay = (changeSign: PriceChangeSign): PriceChangeDisplay => {
  switch (changeSign) {
    case PriceChangeSign.RISE:
      return {
        sign: PriceChangeSign.RISE,
        color: 'text-red-600',
        symbol: '▲',
        bgColor: 'bg-red-50'
      };
    case PriceChangeSign.FALL:
      return {
        sign: PriceChangeSign.FALL,
        color: 'text-blue-600',
        symbol: '▼', 
        bgColor: 'bg-blue-50'
      };
    case PriceChangeSign.FLAT:
      return {
        sign: PriceChangeSign.FLAT,
        color: 'text-gray-600',
        symbol: '-',
        bgColor: 'bg-gray-50'
      };
    default:
      return {
        sign: PriceChangeSign.UNKNOWN,
        color: 'text-gray-600',
        symbol: '?',
        bgColor: 'bg-gray-50'
      };
  }
};

/**
 * 숫자 포맷팅 유틸리티
 */
export const formatNumber = (num: number, decimals: number = 0): string => {
  return new Intl.NumberFormat('ko-KR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(num);
};

/**
 * 가격 포맷팅
 */
export const formatPrice = (price: number): string => {
  return `${formatNumber(price)}원`;
};

/**
 * 퍼센트 포맷팅
 */
export const formatPercent = (percent: number): string => {
  return `${percent >= 0 ? '+' : ''}${formatNumber(percent, 2)}%`;
};

/**
 * 거래량 포맷팅 (천 단위로 표시)
 */
export const formatVolume = (volume: number): string => {
  if (volume >= 1_000_000) {
    return `${formatNumber(volume / 1_000_000, 1)}백만`;
  } else if (volume >= 1_000) {
    return `${formatNumber(volume / 1_000, 1)}천`;
  }
  return formatNumber(volume);
};

/**
 * 시가총액 포맷팅 (억원 단위)
 */
export const formatMarketCap = (marketCap: number): string => {
  if (marketCap >= 10_000) {
    return `${formatNumber(marketCap / 10_000, 1)}조원`;
  }
  return `${formatNumber(marketCap)}억원`;
};

/**
 * 거래대금 포맷팅 (백만원 단위)
 */
export const formatTradeAmount = (amount: number): string => {
  if (amount >= 1_000) {
    return `${formatNumber(amount / 1_000, 1)}십억원`;
  } else if (amount >= 100) {
    return `${formatNumber(amount / 100, 1)}억원`;
  }
  return `${formatNumber(amount)}백만원`;
};