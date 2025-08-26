// 키움 API 타입 정의
export interface KiwoomApiRequest {
  data: {
    stk_cd: string;           // 종목코드 (6자리)
    base_dt?: string;         // 기준일자 YYYYMMDD (일/주/월/년봉)
    tic_scope?: string;       // 틱/분봉 범위 ("1", "3", "5", "10", "15", "30", "45", "60")
    upd_stkpc_tp: string;     // 수정주가구분 ("0": 미적용, "1": 적용)
  };
  cont_yn: string;            // 연속조회여부 ("N": 신규, "Y": 연속)
  next_key: string;           // 연속조회키
}

// 일봉/주봉/월봉/년봉 차트 API 응답
export interface KiwoomDailyApiResponse {
  Code: number;
  Header: {
    "next-key": string;
    "cont-yn": string;
    "api-id": string;
  };
  Body: {
    stk_cd: string;
    stk_dt_pole_chart_qry: KiwoomDailyChartData[];
  };
}

// 분봉 차트 API 응답
export interface KiwoomMinuteApiResponse {
  Code: number;
  Header: {
    "next-key": string;
    "cont-yn": string;
    "api-id": string;
  };
  Body: {
    stk_cd: string;
    stk_min_pole_chart_qry: KiwoomMinuteChartData[];
  };
}

// 틱 차트 API 응답
export interface KiwoomTickApiResponse {
  Code: number;
  Header: {
    "next-key": string;
    "cont-yn": string;
    "api-id": string;
  };
  Body: {
    stk_cd: string;
    last_tic_cnt: string;
    stk_tic_chart_qry: KiwoomTickChartData[]; // 실제 필드명: stk_tic_chart_qry (NOT stk_tic_pole_chart_qry)
  };
}

// 주봉 차트 API 응답
export interface KiwoomWeeklyApiResponse {
  Code: number;
  Header: {
    "next-key": string;
    "cont-yn": string;
    "api-id": string;
  };
  Body: {
    stk_cd: string;
    stk_stk_pole_chart_qry: KiwoomDailyChartData[]; // 주봉은 일봉과 동일한 데이터 구조
  };
}

// 월봉 차트 API 응답 (예상)
export interface KiwoomMonthlyApiResponse {
  Code: number;
  Header: {
    "next-key": string;
    "cont-yn": string;
    "api-id": string;
  };
  Body: {
    stk_cd: string;
    stk_mth_pole_chart_qry: KiwoomDailyChartData[]; // 월봉도 일봉과 동일한 데이터 구조 예상
  };
}

// 년봉 차트 API 응답 (예상)
export interface KiwoomYearlyApiResponse {
  Code: number;
  Header: {
    "next-key": string;
    "cont-yn": string;
    "api-id": string;
  };
  Body: {
    stk_cd: string;
    stk_yr_pole_chart_qry: KiwoomDailyChartData[]; // 년봉도 일봉과 동일한 데이터 구조 예상
  };
}

// 통합 API 응답 타입
export type KiwoomApiResponse = KiwoomDailyApiResponse | KiwoomMinuteApiResponse | KiwoomTickApiResponse | KiwoomWeeklyApiResponse | KiwoomMonthlyApiResponse | KiwoomYearlyApiResponse;

// 일봉/주봉/월봉/년봉 차트 데이터
export interface KiwoomDailyChartData {
  cur_prc: string;          // 현재가 (종가)
  trde_qty: string;         // 거래량
  trde_prica: string;       // 거래대금
  dt: string;               // 날짜 YYYYMMDD
  open_pric: string;        // 시가
  high_pric: string;        // 고가
  low_pric: string;         // 저가
  upd_stkpc_tp: string;     // 수정주가타입
  upd_rt: string;           // 수정비율
  bic_inds_tp: string;      // 대업종타입
  sm_inds_tp: string;       // 소업종타입
  stk_infr: string;         // 주식정보
  upd_stkpc_event: string;  // 수정주가이벤트
  pred_close_pric: string;  // 예상종가 (전일종가)
}

// 분봉 차트 데이터 (fn_ka10080)
export interface KiwoomMinuteChartData {
  cur_prc: string;          // 현재가
  trde_qty: string;         // 거래량
  cntr_tm: string;          // 체결시간 HHMMSS
  open_pric: string;        // 시가
  high_pric: string;        // 고가
  low_pric: string;         // 저가
  upd_stkpc_tp: string;     // 수정주가구분
  upd_rt: string;           // 수정비율
  bic_inds_tp: string;      // 대업종구분
  sm_inds_tp: string;       // 소업종구분
  stk_infr: string;         // 종목정보
  upd_stkpc_event: string;  // 수정주가이벤트
  pred_close_pric: string;  // 전일종가
}

// 틱 차트 데이터 (fn_ka10079) - 분봉과 동일 구조
export interface KiwoomTickChartData {
  cur_prc: string;          // 현재가
  trde_qty: string;         // 거래량
  cntr_tm: string;          // 체결시간 HHMMSS
  open_pric: string;        // 시가
  high_pric: string;        // 고가
  low_pric: string;         // 저가
  upd_stkpc_tp: string;     // 수정주가구분
  upd_rt: string;           // 수정비율
  bic_inds_tp: string;      // 대업종구분
  sm_inds_tp: string;       // 소업종구분
  stk_infr: string;         // 종목정보
  upd_stkpc_event: string;  // 수정주가이벤트
  pred_close_pric: string;  // 전일종가
}

// 통합 차트 데이터 타입
export type KiwoomChartData = KiwoomDailyChartData | KiwoomMinuteChartData | KiwoomTickChartData;

// 차트 API 엔드포인트 매핑
export const CHART_API_ENDPOINTS = {
  tick: '/api/fn_ka10079',      // 틱차트
  minute: '/api/fn_ka10080',    // 분봉차트
  daily: '/api/fn_ka10081',     // 일봉차트
  weekly: '/api/fn_ka10082',    // 주봉차트
  monthly: '/api/fn_ka10083',   // 월봉차트
  yearly: '/api/fn_ka10094',    // 년봉차트
} as const;

// 시간대별 차트 타입 매핑
export const TIMEFRAME_TO_CHART_TYPE = {
  '1D': 'minute',     // 1일은 분봉으로
  '5D': 'minute',     // 5일은 분봉으로
  '1M': 'monthly',    // 1개월은 월봉으로 (fn_ka10083)
  '3M': 'daily',      // 3개월은 일봉으로 (fn_ka10081)
  '1Y': 'daily',      // 1년은 일봉으로 (fn_ka10081)
  'ALL': 'weekly',    // 전체는 주봉으로 (fn_ka10082)
} as const;

// 차트 타입별 기본 틱/분봉 범위
export const DEFAULT_TIC_SCOPE = {
  tick: '1',
  minute: '30',    // 30분봉을 기본으로
  daily: undefined,
  weekly: undefined,
  monthly: undefined,
  yearly: undefined,
} as const;

// 종목 리스트 API (fn_ka10099) 요청
export interface KiwoomStockListRequest {
  mrkt_tp: string; // 시장구분: 0:코스피, 10:코스닥, 3:ELW, 8:ETF, 30:K-OTC, 50:코넥스, 5:신주인수권, 4:뮤추얼펀드, 6:리츠, 9:하이일드
}

// 종목 리스트 API 응답
export interface KiwoomStockListApiResponse {
  Code: number;
  Header: {
    "cont-yn": string;
    "next-key": string;
    "api-id": string;
  };
  Body: {
    list: KiwoomStockInfo[];
  };
}

// 종목 정보 데이터
export interface KiwoomStockInfo {
  code: string;             // 종목코드 (단축코드)
  name: string;             // 종목명
  listCount: string;        // 상장주식수
  auditInfo: string;        // 감리구분
  regDay: string;           // 상장일
  lastPrice: string;        // 전일종가
  state: string;            // 종목상태
  marketCode: string;       // 시장구분코드
  marketName: string;       // 시장명
  upName: string;           // 업종명
  upSizeName: string;       // 회사크기분류
  companyClassName?: string; // 회사분류 (코스닥만)
  orderWarning: string;     // 투자유의종목여부 (0:해당없음, 2:정리매매, 3:단기과열, 4:투자위험, 5:투자경과, 1:ETF투자주의요망)
  nxtEnable: string;        // NXT가능여부 (Y:가능)
}

// 시장 구분 코드
export const MARKET_TYPES = {
  KOSPI: '0',      // 코스피
  KOSDAQ: '10',    // 코스닥
  ELW: '3',        // ELW
  ETF: '8',        // ETF
  K_OTC: '30',     // K-OTC
  KONEX: '50',     // 코넥스
  RIGHTS: '5',     // 신주인수권
  MUTUAL: '4',     // 뮤추얼펀드
  REITS: '6',      // 리츠
  HIGH_YIELD: '9', // 하이일드
} as const;

// 시장명 매핑
export const MARKET_NAMES = {
  '0': 'KOSPI',
  '10': 'KOSDAQ',
  '3': 'ELW',
  '8': 'ETF',
  '30': 'K-OTC',
  '50': 'KONEX',
  '5': '신주인수권',
  '4': '뮤추얼펀드',
  '6': '리츠',
  '9': '하이일드',
} as const;