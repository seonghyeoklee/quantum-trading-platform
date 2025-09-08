// KIS API 관심종목 등록 상위 조회 타입 정의

export interface PopularStockItem {
  mrkt_div_cls_name: string;      // 시장구분명 (코스피, 코스닥)
  mksc_shrn_iscd: string;         // 종목코드
  hts_kor_isnm: string;           // 한글종목명
  stck_prpr: string;              // 현재가
  prdy_vrss: string;              // 전일대비
  prdy_vrss_sign: string;         // 전일대비부호 (2:상승, 3:보합, 5:하락)
  prdy_ctrt: string;              // 전일대비율
  acml_vol: string;               // 누적거래량
  acml_tr_pbmn: string;           // 누적거래대금
  askp: string;                   // 매도호가
  bidp: string;                   // 매수호가
  data_rank: string;              // 순위
  inter_issu_reg_csnu: string;    // 관심종목등록자수
}

export interface PopularStocksApiResponse {
  rt_cd: string;                  // 응답코드
  msg_cd: string;                 // 메시지코드
  msg1: string;                   // 메시지
  output: PopularStockItem[];     // 결과 데이터
}

// 프론트엔드에서 사용할 변환된 타입
export interface PopularStock {
  symbol: string;                 // 종목코드
  name: string;                   // 종목명
  market: 'KOSPI' | 'KOSDAQ';     // 시장구분
  price: number;                  // 현재가
  change: number;                 // 전일대비
  changePercent: number;          // 전일대비율
  volume: number;                 // 거래량
  rank: number;                   // 인기순위
  registrationCount: number;      // 관심등록자수
}

// 시장 필터 옵션
export type MarketCode = '0000' | '0001' | '1001' | '2001';

export interface MarketFilter {
  code: MarketCode;
  label: string;
}

export const MARKET_FILTERS: MarketFilter[] = [
  { code: '0000', label: '전체' },
  { code: '0001', label: '거래소' },
  { code: '1001', label: '코스닥' },
  { code: '2001', label: '코스피200' },
];