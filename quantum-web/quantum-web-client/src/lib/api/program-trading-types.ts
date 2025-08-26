// 프로그램 순매수 상위 50 API 타입 정의

// 요청 타입
export interface ProgramTradingRequest {
  trde_upper_tp: '1' | '2';  // 1:순매도상위, 2:순매수상위
  amt_qty_tp: '1' | '2';     // 1:금액, 2:수량
  mrkt_tp: 'P00101' | 'P10102'; // P00101:코스피, P10102:코스닥
  stex_tp: '1' | '2' | '3';  // 1:KRX, 2:NXT, 3:통합
}

// 응답 헤더 타입
export interface ProgramTradingResponseHeader {
  'cont-yn': string;        // 연속조회여부
  'next-key': string;       // 연속조회키
  'api-id': string;         // TR명
}

// 프로그램 순매수 항목 타입
export interface ProgramTradingItem {
  rank: string;             // 순위
  stk_cd: string;          // 종목코드
  stk_nm: string;          // 종목명
  cur_prc: string;         // 현재가
  flu_sig: string;         // 등락기호
  pred_pre: string;        // 전일대비
  flu_rt: string;          // 등락율
  acc_trde_qty: string;    // 누적거래량
  prm_sell_amt: string;    // 프로그램매도금액
  prm_buy_amt: string;     // 프로그램매수금액
  prm_netprps_amt: string; // 프로그램순매수금액
}

// 응답 바디 타입 (실제 키움 API 응답에 맞게 수정)
export interface ProgramTradingResponseBody {
  prm_netprps_upper_50: ProgramTradingItem[];
  return_code: number;
  return_msg: string;
}

// 전체 응답 타입 (실제 키움 API 응답에 맞게 수정)
export interface ProgramTradingResponse {
  Code: number;
  Header: ProgramTradingResponseHeader;
  Body: ProgramTradingResponseBody;
}

// 파싱된 프로그램 거래 데이터 (화면 표시용)
export interface ProgramTradingData {
  rank: number;
  stockCode: string;
  stockName: string;
  currentPrice: number;
  changeSign: 'up' | 'down' | 'flat';
  changeAmount: number;
  changeRate: number;
  volume: number;
  sellAmount: number;
  buyAmount: number;
  netAmount: number;
  netAmountFormatted: string; // 억원 단위로 포맷팅된 순매수금액
}