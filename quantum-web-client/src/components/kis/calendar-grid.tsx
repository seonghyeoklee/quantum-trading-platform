'use client';

import React from 'react';
import { format, getDay } from 'date-fns';
import { cn } from '@/lib/utils';
import { CalendarDay, CalendarDayStatus } from '@/types/kis-holiday';

interface CalendarGridProps {
  days: CalendarDay[];
  isLoading?: boolean;
}

export default function CalendarGrid({ days, isLoading }: CalendarGridProps) {
  // 요일 헤더
  const weekDays = ['일', '월', '화', '수', '목', '금', '토'];

  // 날짜 상태에 따른 스타일 계산
  const getDayStatus = (day: CalendarDay): CalendarDayStatus => {
    const dayOfWeek = getDay(day.date);
    
    // 주말 체크 (일요일: 0, 토요일: 6)
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      return 'weekend';
    }
    
    // 휴장일 정보가 있는 경우
    if (day.holidayInfo) {
      // 영업일이면서 거래일인 경우 정상 영업일
      if (day.holidayInfo.isBusinessDay && day.holidayInfo.isTradingDay) {
        return 'business';
      }
      // 휴장일인 경우
      if (!day.holidayInfo.isBusinessDay || !day.holidayInfo.isTradingDay) {
        return 'holiday';
      }
    }
    
    // 기본 평일 (휴장일 정보가 없는 경우)
    return 'business';
  };

  // 세련된 카드 스타일 캘린더
  const getStatusStyles = (status: CalendarDayStatus, isCurrentMonth: boolean, isToday: boolean) => {
    let baseStyles = "relative flex flex-col p-3 h-32 text-sm transition-all duration-200 cursor-pointer rounded-lg border border-border/50 hover:border-border hover:shadow-md hover:scale-[1.02] hover:z-10";
    
    let bgStyles = "";
    let textColor = "";
    let specialStyles = "";
    
    // 오늘 날짜 특별 스타일
    if (isToday) {
      bgStyles = "bg-gradient-to-br from-primary/10 to-primary/5";
      specialStyles = "border-primary/40 shadow-md ring-2 ring-primary/20";
      textColor = "text-foreground";
    } else {
      switch (status) {
        case 'business':
          if (isCurrentMonth) {
            bgStyles = "bg-gradient-to-br from-card to-card/95 hover:from-primary/5 hover:to-primary/10";
            textColor = "text-foreground";
          } else {
            bgStyles = "bg-gradient-to-br from-muted/10 to-muted/5 hover:from-muted/20 hover:to-muted/10";
            textColor = "text-muted-foreground";
          }
          break;
        case 'holiday':
          if (isCurrentMonth) {
            bgStyles = "bg-gradient-to-br from-destructive/5 to-destructive/10 hover:from-destructive/10 hover:to-destructive/15";
            textColor = "text-foreground";
            specialStyles = "border-destructive/20";
          } else {
            bgStyles = "bg-gradient-to-br from-muted/10 to-muted/5 hover:from-muted/20 hover:to-muted/10";
            textColor = "text-muted-foreground";
          }
          break;
        case 'weekend':
          if (isCurrentMonth) {
            bgStyles = "bg-gradient-to-br from-muted/15 to-muted/5 hover:from-muted/25 hover:to-muted/15";
            textColor = "text-muted-foreground";
          } else {
            bgStyles = "bg-gradient-to-br from-muted/10 to-muted/5 hover:from-muted/20 hover:to-muted/10";
            textColor = "text-muted-foreground";
          }
          break;
        default:
          bgStyles = "bg-gradient-to-br from-card to-card/90 hover:from-muted/30 hover:to-muted/20";
          textColor = "text-foreground";
      }
    }
    
    return cn(baseStyles, bgStyles, textColor, specialStyles);
  };

  // 로딩 상태 렌더링
  if (isLoading) {
    return (
      <div>
        {/* 요일 헤더 */}
        <div className="grid grid-cols-7 bg-muted/30">
          {weekDays.map((day, index) => (
            <div 
              key={day} 
              className={cn(
                "p-3 text-center text-sm font-medium border border-border",
                index === 0 || index === 6 ? "text-destructive" : "text-foreground"
              )}
            >
              {day}
            </div>
          ))}
        </div>
        
        {/* 로딩 스켈레톤 */}
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 42 }).map((_, index) => (
            <div 
              key={index} 
              className="h-32 bg-muted/20 border border-border animate-pulse p-3 rounded-lg"
            >
              <div className="w-8 h-6 bg-muted-foreground/30 rounded mb-2"></div>
              <div className="w-full h-2 bg-muted-foreground/20 rounded mt-auto"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {weekDays.map((day, index) => (
          <div 
            key={day} 
            className={cn(
              "p-2 text-center text-sm font-semibold",
              index === 0 || index === 6 ? "text-destructive" : "text-foreground"
            )}
          >
            {day}
          </div>
        ))}
      </div>
      
      {/* 달력 그리드 */}
      <div className="grid grid-cols-7 gap-2">
        {days.map((day, index) => {
          const status = getDayStatus(day);
          const styles = getStatusStyles(status, day.isCurrentMonth, day.isToday);
          
          return (
            <div
              key={index}
              className={styles}
              title={day.holidayInfo ? 
                `${format(day.date, 'yyyy-MM-dd')} - ${day.holidayInfo.holidayName}` : 
                format(day.date, 'yyyy-MM-dd')
              }
            >
              {/* 날짜 번호와 상태 */}
              <div className="flex items-start justify-between mb-2">
                <span className={cn(
                  "font-bold text-lg leading-none",
                  day.isToday 
                    ? "w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-base shadow-sm" 
                    : ""
                )}>
                  {day.dayNumber}
                </span>
                
                {/* 상태 표시점 */}
                {day.holidayInfo && !day.holidayInfo.isTradingDay && (
                  <div className="w-2 h-2 bg-destructive rounded-full shadow-sm" title="휴장일"></div>
                )}
              </div>
              
              {/* 휴일 정보 표시 */}
              {day.holidayInfo && day.holidayInfo.holidayName && (
                <div className="mt-auto">
                  <div className="text-xs text-destructive font-semibold leading-tight truncate bg-destructive/10 px-2 py-1 rounded-md">
                    {day.holidayInfo.holidayName}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}