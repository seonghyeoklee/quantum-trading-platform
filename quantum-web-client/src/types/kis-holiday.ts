/**
 * KIS 휴장일 API 타입 정의
 */

export interface KisHolidayItem {
  date: string;                 // 날짜 (YYYY-MM-DD)
  holidayName: string;          // 휴장일명
  bzdy_yn: string;              // 영업일여부 (Y/N) - 금융기관이 업무를 하는 날
  tr_day_yn: string;            // 거래일여부 (Y/N) - 증권 업무가 가능한 날(입출금, 이체 등)
  opnd_yn: string;              // 개장일여부 (Y/N) - 주식시장이 개장되는 날 (주문 가능일)
  sttl_day_yn: string;          // 결제일여부 (Y/N) - 주식 거래에서 실제로 주식을 인수하고 돈을 지불하는 날
  
  // 기존 필드와의 호환성을 위한 computed properties
  isBusinessDay: boolean;       // bzdy_yn === 'Y'
  isTradingDay: boolean;        // tr_day_yn === 'Y'  
  isOpeningDay: boolean;        // opnd_yn === 'Y'
  isSettlementDay: boolean;     // sttl_day_yn === 'Y'
}

export interface KisHolidayApiResponse {
  startDate: string;
  endDate: string;
  calendar: KisHolidayItem[];
  totalCount: number;
}

export interface CalendarDay {
  date: Date;
  dayNumber: number;
  isCurrentMonth: boolean;
  isToday: boolean;
  holidayInfo?: KisHolidayItem;
}

export type CalendarDayStatus = 'business' | 'holiday' | 'weekend' | 'normal';