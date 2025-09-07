'use client';

import React, { useState, useEffect } from 'react';
import { format, isSameMonth, isToday, isWeekend } from 'date-fns';
import { ko } from 'date-fns/locale';
import Calendar from 'react-calendar';
import { 
  Calendar as CalendarIcon, 
  ChevronLeft, 
  ChevronRight,
  Info,
  TrendingUp,
  Building2,
  BanknoteIcon,
  XCircle,
  RefreshCw
} from 'lucide-react';
import { KisHolidayApiResponse, KisHolidayItem } from '@/types/kis-holiday';
import { cn } from '@/lib/utils';

// react-calendar의 Value 타입 정의
type ValuePiece = Date | null;
type Value = ValuePiece | [ValuePiece, ValuePiece];

interface HolidayCalendarProps {
  className?: string;
}

// 날짜 상태 타입 정의
type DateStatus = {
  type: 'market-open' | 'trading' | 'business' | 'no-settlement' | 'holiday';
  label: string;
  icon: React.ReactNode;
  priority: number;
  className: string;
};

export default function HolidayCalendar({ className }: HolidayCalendarProps) {
  const currentDate = new Date();
  const [selectedDate, setSelectedDate] = useState<Value>(currentDate);
  const [activeStartDate, setActiveStartDate] = useState(currentDate);
  const [holidayData, setHolidayData] = useState<KisHolidayItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  // 휴장일 달력 데이터 로드
  const fetchHolidayData = async (year: number, month: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const startDate = `${year}-${month.toString().padStart(2, '0')}-01`;
      const lastDay = new Date(year, month, 0).getDate();
      const endDate = `${year}-${month.toString().padStart(2, '0')}-${lastDay.toString().padStart(2, '0')}`;

      const apiUrl = `http://api.quantum-trading.com:8080/api/v1/kis/holidays/calendar?startDate=${startDate}&endDate=${endDate}`;
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
      }

      const data: KisHolidayApiResponse = await response.json();
      
      if (data.success && data.data) {
        setHolidayData(data.data);
      } else {
        console.warn('휴장일 데이터가 없거나 형식이 올바르지 않습니다:', data);
        setHolidayData([]);
      }
    } catch (error) {
      console.error('휴장일 데이터 로드 실패:', error);
      setError(error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.');
      setHolidayData([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 컴포넌트 마운트 및 월 변경 시 데이터 로드
  useEffect(() => {
    const year = activeStartDate.getFullYear();
    const month = activeStartDate.getMonth() + 1;
    fetchHolidayData(year, month);
  }, [activeStartDate]);

  // 날짜별 상태 확인
  const getDateStatus = (date: Date): DateStatus | null => {
    const dateString = format(date, 'yyyyMMdd');
    const holiday = holidayData.find(item => item.bass_dt === dateString);
    
    if (!holiday) return null;

    // 우선순위별 상태 확인 (높은 우선순위부터)
    const statusMap: Record<string, DateStatus> = {
      '0': {
        type: 'holiday',
        label: '휴장',
        icon: <XCircle className="w-3 h-3" />,
        priority: 1,
        className: 'bg-red-100 text-red-700 border-red-300 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800'
      },
      '1': {
        type: 'market-open',
        label: '개장',
        icon: <TrendingUp className="w-3 h-3" />,
        priority: 4,
        className: 'bg-green-100 text-green-700 border-green-300 dark:bg-green-950/30 dark:text-green-400 dark:border-green-800'
      },
      '2': {
        type: 'trading',
        label: '거래',
        icon: <Building2 className="w-3 h-3" />,
        priority: 3,
        className: 'bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800'
      },
      '3': {
        type: 'business',
        label: '영업',
        icon: <BanknoteIcon className="w-3 h-3" />,
        priority: 3,
        className: 'bg-cyan-100 text-cyan-700 border-cyan-300 dark:bg-cyan-950/30 dark:text-cyan-400 dark:border-cyan-800'
      },
      '4': {
        type: 'no-settlement',
        label: '결제불가',
        icon: <XCircle className="w-3 h-3" />,
        priority: 2,
        className: 'bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-950/30 dark:text-orange-400 dark:border-orange-800'
      }
    };

    // 각 필드를 확인하여 가장 우선순위가 높은 상태 반환
    const possibleStatuses = [];
    if (holiday.bzdy_yn === '0') possibleStatuses.push(statusMap['0']);
    if (holiday.tr_dy_yn === '1') possibleStatuses.push(statusMap['1']);
    if (holiday.opnd_yn === '1') possibleStatuses.push(statusMap['2']);
    if (holiday.sttl_dy_yn === '0') possibleStatuses.push(statusMap['4']);
    
    // 우선순위가 가장 높은 것 반환 (낮은 숫자가 높은 우선순위)
    return possibleStatuses.sort((a, b) => a.priority - b.priority)[0] || null;
  };

  // 달력 타일 클래스 이름
  const getTileClassName = ({ date, view }: { date: Date; view: string }) => {
    if (view !== 'month') return null;
    
    const classes = ['react-calendar__tile'];
    
    // 오늘 날짜
    if (isToday(date)) {
      classes.push('react-calendar__tile--now');
    }
    
    // 선택된 날짜
    if (selectedDate && selectedDate instanceof Date && format(date, 'yyyy-MM-dd') === format(selectedDate, 'yyyy-MM-dd')) {
      classes.push('react-calendar__tile--active');
    }
    
    // 현재 월이 아닌 날짜
    if (!isSameMonth(date, activeStartDate)) {
      classes.push('react-calendar__tile--neighboringMonth');
    }
    
    // 주말
    if (isWeekend(date)) {
      classes.push('react-calendar__tile--weekends');
    }
    
    // 휴일 상태
    const status = getDateStatus(date);
    if (status?.type === 'holiday') {
      classes.push('react-calendar__tile--holiday');
    }
    
    return classes.join(' ');
  };

  // 달력 타일 내용
  const getTileContent = ({ date, view }: { date: Date; view: string }) => {
    if (view !== 'month') return null;
    
    const status = getDateStatus(date);
    if (!status) return null;

    return (
      <div className="absolute bottom-1 left-1 right-1">
        <div className={cn('calendar-badge text-xs px-1 py-0.5 rounded flex items-center gap-1', status.className)}>
          {status.icon}
          <span className="text-xs">{status.label}</span>
        </div>
      </div>
    );
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-primary/10 rounded-xl">
            <CalendarIcon className="w-8 h-8 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">트레이딩 캘린더</h1>
            <p className="text-muted-foreground">KIS 휴장일 및 시장 운영 정보</p>
          </div>
        </div>
        
        <button
          onClick={() => fetchHolidayData(activeStartDate.getFullYear(), activeStartDate.getMonth() + 1)}
          disabled={isLoading}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg border border-border bg-card hover:bg-accent transition-colors",
            "text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          )}
        >
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
          새로고침
        </button>
      </div>

      {/* 에러 상태 */}
      {error && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
          <div className="flex items-center gap-2 text-destructive">
            <Info className="w-4 h-4" />
            <span className="font-medium">데이터 로드 실패</span>
          </div>
          <p className="text-sm text-destructive/80 mt-1">{error}</p>
        </div>
      )}

      {/* 범례 */}
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="text-sm font-medium text-foreground mb-3">범례</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="flex items-center gap-2">
            <div className="calendar-badge bg-red-100 text-red-700 border-red-300 dark:bg-red-950/30 dark:text-red-400 dark:border-red-800">
              <XCircle className="w-3 h-3" />
              <span>휴장</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="calendar-badge bg-green-100 text-green-700 border-green-300 dark:bg-green-950/30 dark:text-green-400 dark:border-green-800">
              <TrendingUp className="w-3 h-3" />
              <span>개장</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="calendar-badge bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950/30 dark:text-blue-400 dark:border-blue-800">
              <Building2 className="w-3 h-3" />
              <span>거래</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="calendar-badge bg-cyan-100 text-cyan-700 border-cyan-300 dark:bg-cyan-950/30 dark:text-cyan-400 dark:border-cyan-800">
              <BanknoteIcon className="w-3 h-3" />
              <span>영업</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="calendar-badge bg-orange-100 text-orange-700 border-orange-300 dark:bg-orange-950/30 dark:text-orange-400 dark:border-orange-800">
              <XCircle className="w-3 h-3" />
              <span>결제불가</span>
            </div>
          </div>
        </div>
      </div>

      {/* 달력 */}
      <div className="bg-card rounded-lg border border-border p-6 calendar-container">
        <Calendar
          onChange={handleDateChange}
          onActiveStartDateChange={handleActiveStartDateChange}
          value={selectedDate}
          view="month"
          locale="ko-KR"
          calendarType="gregory"
          showNeighboringMonth={true}
          formatShortWeekday={(locale, date) => {
            const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
            return weekdays[date.getDay()];
          }}
          tileClassName={getTileClassName}
          tileContent={getTileContent}
          prevLabel={<ChevronLeft className="w-5 h-5" />}
          nextLabel={<ChevronRight className="w-5 h-5" />}
          prev2Label={null}
          next2Label={null}
          className="react-calendar-enhanced"
        />
      </div>

      {/* 선택된 날짜 정보 */}
      {selectedDate && selectedDate instanceof Date && (
        <div className="bg-card rounded-lg border border-border p-4">
          <h3 className="text-lg font-semibold text-foreground mb-3">
            {format(selectedDate, 'yyyy년 M월 d일 EEEE', { locale: ko })}
          </h3>
          {(() => {
            const status = getDateStatus(selectedDate);
            if (status) {
              return (
                <div className="flex items-center gap-3">
                  <div className={cn('calendar-badge', status.className)}>
                    {status.icon}
                    <span>{status.label}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {status.type === 'holiday' ? '증권시장 휴장일입니다' :
                     status.type === 'market-open' ? '증권시장 개장일입니다' :
                     status.type === 'trading' ? '거래 가능한 날입니다' :
                     status.type === 'business' ? '영업일입니다' :
                     status.type === 'no-settlement' ? '결제가 불가능한 날입니다' : ''}
                  </span>
                </div>
              );
            } else {
              return (
                <p className="text-sm text-muted-foreground">
                  일반 영업일입니다.
                </p>
              );
            }
          })()}
        </div>
      )}
    </div>
  );
}