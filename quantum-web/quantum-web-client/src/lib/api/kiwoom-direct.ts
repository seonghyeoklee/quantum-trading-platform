/**
 * 키움 어댑터 직접 호출 API 클라이언트
 * 프록시 없이 키움 어댑터로 직접 요청
 */

import { getKiwoomAdapterUrl } from '../api-config';

const KIWOOM_ADAPTER_URL = getKiwoomAdapterUrl();

export interface KiwoomApiResponse<T = any> {
  Code: number;
  Header: {
    'next-key': string;
    'cont-yn': string;
    'api-id': string;
  };
  Body: T;
}

export interface StockListRequest {
  mrkt_tp: string; // 시장구분 (0: 코스피, 10: 코스닥, etc.)
}

export interface ProgramTradeRequest {
  trde_upper_tp: string; // 매매상위구분 (1: 순매도상위, 2: 순매수상위)
  amt_qty_tp: string;    // 금액수량구분 (1: 금액, 2: 수량)
  mrkt_tp: string;       // 시장구분 (P00101: 코스피, P10102: 코스닥)
  stex_tp: string;       // 거래소구분 (1: KRX, 2: NXT, 3: 통합)
}

/**
 * 키움 종목정보 리스트 조회 (fn_ka10099)
 */
export async function getStockList(
  request: StockListRequest,
  contYn: string = 'N'
): Promise<KiwoomApiResponse> {
  const response = await fetch(`${KIWOOM_ADAPTER_URL}/api/fn_ka10099?cont_yn=${contYn}`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`키움 API 호출 실패: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * 키움 프로그램 거래 상위 50 조회 (fn_ka90003)
 */
export async function getProgramTradeTop50(
  request: ProgramTradeRequest,
  contYn: string = 'N'
): Promise<KiwoomApiResponse> {
  const response = await fetch(`${KIWOOM_ADAPTER_URL}/api/fn_ka90003?cont_yn=${contYn}`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`키움 API 호출 실패: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * 키움 OAuth 토큰 발급 (fn_au10001)
 */
export async function getKiwoomToken(): Promise<KiwoomApiResponse> {
  const response = await fetch(`${KIWOOM_ADAPTER_URL}/api/fn_au10001`, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  });

  if (!response.ok) {
    throw new Error(`키움 토큰 발급 실패: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * 키움 어댑터 헬스 체크
 */
export async function checkKiwoomHealth(): Promise<any> {
  const response = await fetch(`${KIWOOM_ADAPTER_URL}/health`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`키움 어댑터 헬스체크 실패: ${response.status} ${response.statusText}`);
  }

  return response.json();
}