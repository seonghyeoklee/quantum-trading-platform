// 프로그램 순매수 상위 50 API 호출 함수

import {
  ProgramTradingRequest,
  ProgramTradingResponse,
  ProgramTradingData,
  ProgramTradingItem
} from './program-trading-types';

const KIWOOM_ADAPTER_URL = process.env.NEXT_PUBLIC_KIWOOM_ADAPTER_URL || 'http://localhost:10201';

// API 호출 함수 (연속조회 지원) - 직접 호출 방식
export async function getProgramTradingRanking(
  request: ProgramTradingRequest,
  contYn: 'Y' | 'N' = 'N',
  nextKey?: string
): Promise<ProgramTradingResponse> {
  const url = `${KIWOOM_ADAPTER_URL}/api/fn_ka90003?cont_yn=${contYn}`;
  
  // 연속조회를 위한 헤더 구성
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'api-id': 'ka90003'
  };
  
  if (contYn === 'Y' && nextKey) {
    headers['cont-yn'] = 'Y';
    headers['next-key'] = nextKey;
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`프로그램 거래 데이터 조회 실패: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  
  // API 응답 검증
  if (!data.Body || !data.Body.prm_netprps_upper_50) {
    throw new Error('유효하지 않은 API 응답 형식입니다.');
  }

  return data;
}

// 데이터 파싱 유틸리티 함수
export function parseProgramTradingData(items: ProgramTradingItem[]): ProgramTradingData[] {
  return items.map((item) => {
    // 숫자 파싱
    const currentPrice = parseInt(item.cur_prc) || 0;
    const changeAmount = parseInt(item.pred_pre) || 0;
    const changeRate = parseFloat(item.flu_rt) || 0;
    const volume = parseInt(item.acc_trde_qty) || 0;
    const sellAmount = parseInt(item.prm_sell_amt) || 0;
    const buyAmount = parseInt(item.prm_buy_amt) || 0;
    const netAmount = parseInt(item.prm_netprps_amt) || 0;

    // 등락 기호 파싱
    let changeSign: 'up' | 'down' | 'flat' = 'flat';
    if (item.flu_sig === '1' || item.flu_sig === '2' || changeAmount > 0) {
      changeSign = 'up';
    } else if (item.flu_sig === '4' || item.flu_sig === '5' || changeAmount < 0) {
      changeSign = 'down';
    }

    // 순매수금액을 억원 단위로 포맷팅
    const netAmountFormatted = formatAmount(netAmount);

    return {
      rank: parseInt(item.rank) || 0,
      stockCode: item.stk_cd,
      stockName: item.stk_nm,
      currentPrice,
      changeSign,
      changeAmount: Math.abs(changeAmount),
      changeRate: Math.abs(changeRate),
      volume,
      sellAmount,
      buyAmount,
      netAmount,
      netAmountFormatted
    };
  });
}

// 금액 포맷팅 함수 (억원 단위)
export function formatAmount(amount: number): string {
  if (amount === 0) return '0';
  
  const absAmount = Math.abs(amount);
  const isNegative = amount < 0;
  
  if (absAmount >= 100000000) {
    const formatted = (absAmount / 100000000).toFixed(1);
    return `${isNegative ? '-' : '+'}${formatted}억`;
  } else if (absAmount >= 10000) {
    const formatted = (absAmount / 10000).toFixed(0);
    return `${isNegative ? '-' : '+'}${formatted}만`;
  } else {
    return `${isNegative ? '-' : '+'}${absAmount.toLocaleString()}원`;
  }
}

// 숫자를 천 단위 구분 기호로 포맷팅
export function formatNumber(num: number): string {
  return num.toLocaleString('ko-KR');
}

// 가격 포맷팅 (원 단위)
export function formatPrice(price: number): string {
  return `${price.toLocaleString('ko-KR')}원`;
}

// 거래량 포맷팅
export function formatVolume(volume: number): string {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(1)}억주`;
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(0)}만주`;
  } else {
    return `${volume.toLocaleString('ko-KR')}주`;
  }
}

// 기본 요청 객체들
export const DEFAULT_REQUESTS = {
  // 코스피 순매수 상위 (금액 기준)
  KOSPI_BUY_AMOUNT: {
    trde_upper_tp: '2' as const,
    amt_qty_tp: '1' as const,
    mrkt_tp: 'P00101' as const,
    stex_tp: '1' as const
  },
  
  // 코스닥 순매수 상위 (금액 기준)
  KOSDAQ_BUY_AMOUNT: {
    trde_upper_tp: '2' as const,
    amt_qty_tp: '1' as const,
    mrkt_tp: 'P10102' as const,
    stex_tp: '1' as const
  },
  
  // 코스피 순매도 상위 (금액 기준)
  KOSPI_SELL_AMOUNT: {
    trde_upper_tp: '1' as const,
    amt_qty_tp: '1' as const,
    mrkt_tp: 'P00101' as const,
    stex_tp: '1' as const
  },
  
  // 코스닥 순매도 상위 (금액 기준)
  KOSDAQ_SELL_AMOUNT: {
    trde_upper_tp: '1' as const,
    amt_qty_tp: '1' as const,
    mrkt_tp: 'P10102' as const,
    stex_tp: '1' as const
  }
};