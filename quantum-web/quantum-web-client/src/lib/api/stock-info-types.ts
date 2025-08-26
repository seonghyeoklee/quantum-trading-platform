// 키움 종목 기본 정보 API 타입 정의 (fn_ka10001)

// 키움 종목 기본 정보 응답 인터페이스
export interface KiwoomStockBasicInfoResponse {
  Code: number;
  Header: {
    "next-key": string;
    "cont-yn": string;
    "api-id": string;
  };
  Body: KiwoomStockBasicInfoBody;
}

// 키움 종목 기본 정보 본문
export interface KiwoomStockBasicInfoBody {
  stk_cd: string;           // 종목코드
  stk_nm: string;           // 종목명
  setl_mm: string;          // 결산월
  fav: string;              // 액면가
  cap: string;              // 시가총액 (억원)
  flo_stk: string;          // 유동주식수 (천주)
  crd_rt: string;           // 신용비율 (%)
  oyr_hgst: string;         // 연중최고가
  oyr_lwst: string;         // 연중최저가
  mac: string;              // 상장주식수 (천주)
  mac_wght: string;         // 상장주식수 가중치
  for_exh_rt: string;       // 외국인보유비율 (%)
  repl_pric: string;        // 대용가격
  per: string;              // PER (배)
  eps: string;              // EPS (원)
  roe: string;              // ROE (%)
  pbr: string;              // PBR (배)
  ev: string;               // EV/EBITDA (배)
  bps: string;              // BPS (원)
  sale_amt: string;         // 매출액 (억원)
  bus_pro: string;          // 영업이익 (억원)
  cup_nga: string;          // 당기순이익 (억원)
  "250hgst": string;        // 52주 최고가
  "250lwst": string;        // 52주 최저가
  high_pric: string;        // 당일고가
  open_pric: string;        // 시가
  low_pric: string;         // 당일저가
  upl_pric: string;         // 상한가
  lst_pric: string;         // 하한가
  base_pric: string;        // 기준가
  exp_cntr_pric: string;    // 예상체결가
  exp_cntr_qty: string;     // 예상체결량
  "250hgst_pric_dt": string; // 52주 최고가일
  "250hgst_pric_pre_rt": string; // 52주 최고가 대비율
  "250lwst_pric_dt": string; // 52주 최저가일
  "250lwst_pric_pre_rt": string; // 52주 최저가 대비율
  cur_prc: string;          // 현재가
  pre_sig: string;          // 전일대비구분 (1:상한,2:상승,3:보합,4:하한,5:하락)
  pred_pre: string;         // 전일대비
  flu_rt: string;           // 등락율 (%)
  trde_qty: string;         // 거래량
  trde_pre: string;         // 거래대금 (억원)
  fav_unit: string;         // 액면가단위
  dstr_stk: string;         // 유통주식수 (천주)
  dstr_rt: string;          // 유통비율 (%)
  return_code: number;      // 응답코드
  return_msg: string;       // 응답메시지
}

// 프론트엔드용 정제된 종목 기본 정보 인터페이스
export interface StockBasicInfo {
  // 기본 정보
  symbol: string;           // 종목코드
  name: string;             // 종목명
  
  // 현재가 정보
  currentPrice: number;     // 현재가
  change: number;           // 전일대비
  changePercent: number;    // 등락률 (%)
  changeDirection: 'up' | 'down' | 'unchanged'; // 등락 방향
  
  // 당일 거래 정보
  openPrice: number;        // 시가
  highPrice: number;        // 고가
  lowPrice: number;         // 저가
  volume: number;           // 거래량
  tradingValue: number;     // 거래대금 (억원)
  
  // 가격 범위 정보
  upperLimit: number;       // 상한가
  lowerLimit: number;       // 하한가
  basePrice: number;        // 기준가
  week52High: number;       // 52주 최고가
  week52Low: number;        // 52주 최저가
  week52HighDate: string;   // 52주 최고가일
  week52LowDate: string;    // 52주 최저가일
  yearHigh: number;         // 연중 최고가
  yearLow: number;          // 연중 최저가
  
  // 재무 지표
  per: number;              // PER (배)
  pbr: number;              // PBR (배)
  roe: number;              // ROE (%)
  eps: number;              // EPS (원)
  bps: number;              // BPS (원)
  evEbitda: number;         // EV/EBITDA (배)
  
  // 회사 정보
  faceValue: number;        // 액면가
  marketCap: number;        // 시가총액 (억원)
  listedShares: number;     // 상장주식수 (천주)
  floatingShares: number;   // 유동주식수 (천주)
  circulatingShares: number; // 유통주식수 (천주)
  circulatingRatio: number; // 유통비율 (%)
  
  // 외국인/기관 정보
  foreignOwnership: number; // 외국인 보유비율 (%)
  creditRatio: number;      // 신용비율 (%)
  
  // 재무 성과 (연간)
  revenue: number;          // 매출액 (억원)
  operatingProfit: number;  // 영업이익 (억원)
  netIncome: number;        // 당기순이익 (억원)
  
  // 메타 정보
  settlementMonth: number;  // 결산월
  lastUpdated: string;      // 최종 업데이트 시간
}

// 종목 검색 요청 인터페이스
export interface StockSearchRequest {
  stk_cd: string;           // 종목코드 (6자리)
}

// 종목 정보 캐시 인터페이스
export interface StockInfoCache {
  [symbol: string]: {
    data: StockBasicInfo;
    timestamp: number;
    ttl: number;            // TTL in milliseconds
  };
}

// 종목 정보 상태 인터페이스
export interface StockInfoState {
  data: StockBasicInfo | null;
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
}

// 종목 비교 정보 (향후 확장용)
export interface StockComparison {
  symbols: string[];
  data: StockBasicInfo[];
  benchmarkSymbol?: string; // 기준 종목 (예: KOSPI 지수)
}

// API 에러 타입
export interface StockInfoApiError {
  code: number;
  message: string;
  detail?: string;
  timestamp: string;
}

// 종목 즐겨찾기 (향후 확장용)
export interface StockFavorite {
  symbol: string;
  name: string;
  addedAt: string;
  tags?: string[];
}