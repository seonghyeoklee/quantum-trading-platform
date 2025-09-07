'use client';

import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import Calendar, { CalendarProps } from 'react-calendar';
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from 'lucide-react';
import { KisHolidayApiResponse, KisHolidayItem } from '@/types/kis-holiday';

// react-calendar의 Value 타입 정의
type ValuePiece = Date | null;
type Value = ValuePiece | [ValuePiece, ValuePiece];

interface HolidayCalendarProps {
  className?: string;
}

export default function HolidayCalendar({ className }: HolidayCalendarProps) {
  // 실제 현재 날짜 자동 가져오기
  const currentDate = new Date();
  const [selectedDate, setSelectedDate] = useState<Value>(currentDate);
  const [activeStartDate, setActiveStartDate] = useState(currentDate);
  const [holidayData, setHolidayData] = useState<KisHolidayItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiMessage, setApiMessage] = useState<string>('');

  // 날짜 변경 핸들러
  const handleDateChange = (value: Value) => {
    setSelectedDate(value);
  };

  // 월 변경 핸들러
  const handleActiveStartDateChange = ({ activeStartDate }: { activeStartDate: Date | null }) => {
    if (activeStartDate) {
      setActiveStartDate(activeStartDate);
    }
  };

  // 휴장일 달력 데이터 로드 (Spring Boot 직접 호출)
  const fetchHolidayData = async (year: number, month: number) => {
    setIsLoading(true);
    setError(null);
    setApiMessage('');
    
    try {
      // 시작일과 종료일 계산 (해당 월 전체)
      const startDate = `${year}-${month.toString().padStart(2, '0')}-01`;
      const lastDay = new Date(year, month, 0).getDate();
      const endDate = `${year}-${month.toString().padStart(2, '0')}-${lastDay.toString().padStart(2, '0')}`;

      // Spring Boot API 직접 호출
      const apiUrl = `http://api.quantum-trading.com:8080/api/v1/kis/holidays/calendar?startDate=${startDate}&endDate=${endDate}`;
      console.log('🔗 Fetching directly from Spring Boot:', apiUrl);

      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Spring Boot API 호출 실패: ${response.status} ${response.statusText} - ${errorText}`);
      }
      
      const apiResponse: KisHolidayApiResponse = await response.json();
      
      if (apiResponse.calendar) {
        setHolidayData(apiResponse.calendar || []);
        setApiMessage('달력 정보 조회 완료');
        console.log('✅ Calendar data loaded directly:', apiResponse.calendar?.length || 0, 'calendar items');
        console.log('📅 Date range:', apiResponse.startDate, 'to', apiResponse.endDate);
        console.log('📊 Total count:', apiResponse.totalCount);
      } else {
        throw new Error('달력 데이터를 불러올 수 없습니다');
      }
    } catch (error) {
      console.error('❌ Spring Boot API 호출 실패:', error);
      setError(error instanceof Error ? error.message : 'Spring Boot 서버 연결 중 오류가 발생했습니다');
      setHolidayData([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 현재 표시된 월 정보 및 데이터 로드
  useEffect(() => {
    const year = activeStartDate.getFullYear();
    const month = activeStartDate.getMonth() + 1;
    
    console.log('Calendar month changed:', format(activeStartDate, 'yyyy-MM', { locale: ko }));
    fetchHolidayData(year, month);
  }, [activeStartDate]);

  // 날짜별 거래일 정보 조회 함수 (모든 날짜 정보 포함)
  const getCalendarInfoForDate = (date: Date): KisHolidayItem | null => {
    const dateString = format(date, 'yyyy-MM-dd');
    return holidayData.find(item => item.date === dateString) || null;
  };

  // 날짜 상태 분석 함수 - 전문적인 스타일
  type DateStatus = {
    type: string;
    label: string;
    priority: number;
    color: string;
    bgColor: string;
    borderColor: string;
  };

  const getDateStatus = (holiday: KisHolidayItem | null): DateStatus | null => {
    if (!holiday) return null;
    
    // KIS API 기준 상태 분석 (새 필드 우선, 기존 필드 fallback)
    const isMarketOpen = holiday.opnd_yn === 'Y' || holiday.isOpeningDay;    // 개장일 (주문 가능)
    const isBusinessDay = holiday.bzdy_yn === 'Y' || holiday.isBusinessDay;   // 영업일 (금융기관 업무)
    const isTradingDay = holiday.tr_day_yn === 'Y' || holiday.isTradingDay;  // 거래일 (증권업무)
    const isSettlementDay = holiday.sttl_day_yn === 'Y' || holiday.isSettlementDay; // 결제일
    
    // 우선순위: 개장일 > 거래일 > 영업일 > 결제일
    if (isMarketOpen) {
      return { 
        type: 'market-open', 
        label: '개장일', 
        priority: 1,
        color: 'text-green-700',
        bgColor: 'bg-green-100',
        borderColor: 'border-green-300'
      };
    }
    
    if (isTradingDay) {
      return { 
        type: 'trading', 
        label: '거래일', 
        priority: 2,
        color: 'text-blue-700',
        bgColor: 'bg-blue-100',
        borderColor: 'border-blue-300'
      };
    }
    
    if (isBusinessDay) {
      return { 
        type: 'business', 
        label: '영업일', 
        priority: 3,
        color: 'text-cyan-700',
        bgColor: 'bg-cyan-50',
        borderColor: 'border-cyan-200'
      };
    }
    
    if (!isSettlementDay) {
      return { 
        type: 'no-settlement', 
        label: '결제불가', 
        priority: 4,
        color: 'text-orange-700',
        bgColor: 'bg-orange-50',
        borderColor: 'border-orange-200'
      };
    }
    
    // 모든 업무가 불가능한 휴일
    return { 
      type: 'holiday', 
      label: '휴장일', 
      priority: 5,
      color: 'text-red-700',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200'
    };
  };

  return (
    <div className={`w-full ${className}`}>

      {/* Professional Trading Calendar - Full Width */}
      <div className="bg-card border border-border rounded-2xl shadow-lg backdrop-blur-sm w-full min-h-[700px]" style={{
        background: 'linear-gradient(135deg, rgb(var(--card)), rgb(var(--card) / 0.98))',
        padding: '2rem'
      }}>
        {/* Professional Month Header with Status */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-border">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-muted-foreground">
                {isLoading ? '데이터 로드 중...' : apiMessage || '실시간 거래일 정보'}
              </span>
            </div>
          </div>
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 px-3 py-1 rounded-md border border-destructive/20">
              {error}
            </div>
          )}
        </div>
        
        {/* Professional Weekday Headers */}
        <div className="mb-6">
          <div className="grid grid-cols-7 gap-1 mb-4 bg-muted/30 rounded-xl p-3">
            <div className="text-center py-2 font-semibold text-destructive/80 text-base">일</div>
            <div className="text-center py-2 font-semibold text-muted-foreground text-base">월</div>
            <div className="text-center py-2 font-semibold text-muted-foreground text-base">화</div>
            <div className="text-center py-2 font-semibold text-muted-foreground text-base">수</div>
            <div className="text-center py-2 font-semibold text-muted-foreground text-base">목</div>
            <div className="text-center py-2 font-semibold text-muted-foreground text-base">금</div>
            <div className="text-center py-2 font-semibold text-destructive/80 text-base">토</div>
          </div>
        </div>
        
        <Calendar
          onChange={handleDateChange}
          value={selectedDate}
          onActiveStartDateChange={handleActiveStartDateChange}
          locale="en-US"
          showNavigation={true}
          showNeighboringMonth={false}
          prevLabel={<ChevronLeft className="h-6 w-6" />}
          nextLabel={<ChevronRight className="h-6 w-6" />}
          prev2Label={null}
          next2Label={null}
          className="google-calendar-style"
          tileContent={({ date, view }) => {
            if (view === 'month') {
              const calendarInfo = getCalendarInfoForDate(date);
              const status = getDateStatus(calendarInfo);
              
              return (
                <div className="absolute inset-0 p-1 pt-6 flex flex-col overflow-hidden">
                  {/* 로딩 상태 */}
                  {isLoading && (
                    <div className="flex items-center justify-center">
                      <div className="w-1 h-1 bg-primary rounded-full animate-pulse"></div>
                    </div>
                  )}
                  
                  {/* 거래일 상태 정보 */}
                  {!isLoading && calendarInfo && (
                    <>
                      {/* 주요 상태 표시 - 작은 뱃지 */}
                      {status && (
                        <div className="mb-1">
                          <div className={`inline-block px-1 py-0.5 rounded text-xs font-medium leading-none ${status.bgColor} ${status.color} ${status.borderColor} border`} style={{ fontSize: '8px' }}>
                            {status.label.charAt(0)}
                          </div>
                        </div>
                      )}
                      
                      {/* 휴장일 이름 */}
                      {calendarInfo.holidayName && calendarInfo.holidayName.trim() !== '' && (
                        <div className="mb-1">
                          <span className="text-xs text-muted-foreground bg-muted/20 px-0.5 rounded" style={{ fontSize: '8px', lineHeight: '10px' }}>
                            {calendarInfo.holidayName.length > 3 ? calendarInfo.holidayName.substring(0, 3) : calendarInfo.holidayName}
                          </span>
                        </div>
                      )}
                      
                      {/* 상태 점들 */}
                      <div className="flex gap-0.5 flex-wrap">
                        {(() => {
                          const isMarketOpen = calendarInfo.opnd_yn === 'Y' || calendarInfo.isOpeningDay;
                          const isTradingDay = calendarInfo.tr_day_yn === 'Y' || calendarInfo.isTradingDay;
                          const isBusinessDay = calendarInfo.bzdy_yn === 'Y' || calendarInfo.isBusinessDay;
                          const isSettlementDay = calendarInfo.sttl_day_yn === 'Y' || calendarInfo.isSettlementDay;
                          
                          return (
                            <>
                              {isMarketOpen && (
                                <div className="w-1 h-1 bg-green-500 rounded-full" title="개장일"></div>
                              )}
                              {isTradingDay && !isMarketOpen && (
                                <div className="w-1 h-1 bg-blue-500 rounded-full" title="거래일"></div>
                              )}
                              {isBusinessDay && !isTradingDay && (
                                <div className="w-1 h-1 bg-cyan-500 rounded-full" title="영업일"></div>
                              )}
                              {!isSettlementDay && (
                                <div className="w-1 h-1 bg-orange-400 rounded-full" title="결제불가"></div>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    </>
                  )}
                </div>
              );
            }
            return null;
          }}
          tileClassName={({ date, view }) => {
            if (view === 'month') {
              const calendarInfo = getCalendarInfoForDate(date);
              if (calendarInfo && (!calendarInfo.isTradingDay || !calendarInfo.isBusinessDay)) {
                return 'has-holiday';
              }
            }
            return '';
          }}
        />
      </div>
    </div>
  );
}