'use client';

import { useState, useEffect } from 'react';
import { CandlestickData } from './types';

interface TooltipData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
  change?: number;
  changePercent?: number;
}

interface ChartTooltipProps {
  data: TooltipData | null;
  position: { x: number; y: number };
  visible: boolean;
  className?: string;
}

export default function ChartTooltip({
  data,
  position,
  visible,
  className = ''
}: ChartTooltipProps) {
  if (!visible || !data) return null;

  const formatPrice = (price: number) => {
    return `₩${price.toLocaleString()}`;
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1000000) {
      return `${(volume / 1000000).toFixed(1)}M`;
    } else if (volume >= 1000) {
      return `${(volume / 1000).toFixed(1)}K`;
    }
    return volume.toLocaleString();
  };

  const formatDate = (timeStr: string) => {
    try {
      const date = new Date(timeStr);
      return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        weekday: 'short'
      });
    } catch {
      return timeStr;
    }
  };

  const isPositive = data.change ? data.change >= 0 : data.close >= data.open;

  return (
    <div
      className={`fixed z-50 pointer-events-none transition-all duration-200 ease-out ${className}`}
      style={{
        left: position.x + 10,
        top: position.y - 10,
        transform: position.x > window.innerWidth / 2 ? 'translateX(-100%)' : 'none',
        opacity: visible ? 1 : 0
      }}
    >
      <div className="bg-card/95 backdrop-blur-sm border border-border rounded-lg shadow-xl p-3 min-w-52">
        {/* 날짜 */}
        <div className="text-sm font-medium text-foreground mb-2 border-b border-border pb-2">
          {formatDate(data.time)}
        </div>

        {/* OHLC 정보 */}
        <div className="space-y-1.5 text-xs">
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground w-12">시가</span>
            <span className="font-mono font-medium">{formatPrice(data.open)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground w-12">고가</span>
            <span className="font-mono font-medium text-red-600 dark:text-red-400">
              {formatPrice(data.high)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground w-12">저가</span>
            <span className="font-mono font-medium text-blue-600 dark:text-blue-400">
              {formatPrice(data.low)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-muted-foreground w-12">종가</span>
            <span className={`font-mono font-bold ${
              isPositive 
                ? 'text-red-600 dark:text-red-400' 
                : 'text-blue-600 dark:text-blue-400'
            }`}>
              {formatPrice(data.close)}
            </span>
          </div>

          {/* 변동 정보 */}
          {data.change !== undefined && (
            <div className="flex justify-between items-center pt-2 mt-2 border-t border-border/50">
              <span className="text-muted-foreground w-12">변동</span>
              <div className={`font-mono font-medium text-xs ${
                isPositive 
                  ? 'text-red-600 dark:text-red-400' 
                  : 'text-blue-600 dark:text-blue-400'
              }`}>
                <div className="text-right">
                  {data.change >= 0 ? '+' : ''}{data.change.toFixed(0)}
                </div>
                {data.changePercent !== undefined && (
                  <div className="text-right text-xs opacity-80">
                    ({data.changePercent >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%)
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 거래량 */}
          {data.volume !== undefined && data.volume > 0 && (
            <div className="flex justify-between items-center pt-1">
              <span className="text-muted-foreground w-12">거래량</span>
              <span className="font-mono font-medium text-muted-foreground">
                {formatVolume(data.volume)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 툴팁 화살표 */}
      <div 
        className="absolute top-4 w-2 h-2 bg-card border-l border-t border-border rotate-45"
        style={{
          left: position.x > window.innerWidth / 2 ? 'calc(100% - 8px)' : '-4px'
        }}
      />
    </div>
  );
}
