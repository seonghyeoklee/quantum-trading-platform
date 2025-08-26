'use client';

import { useMemo, useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { RealtimeQuoteData } from '@/lib/api/websocket-types';

interface RealtimePriceProps {
  data: RealtimeQuoteData | null;
  className?: string;
}

export default function RealtimePrice({ data, className }: RealtimePriceProps) {
  const [priceAnimation, setPriceAnimation] = useState<'none' | 'up' | 'down'>('none');
  const [prevPrice, setPrevPrice] = useState<number | null>(null);

  // 가격 변동 애니메이션 (덜 자극적으로 개선)
  useEffect(() => {
    if (data && prevPrice !== null && data.currentPrice !== prevPrice) {
      const direction = data.currentPrice > prevPrice ? 'up' : 'down';
      
      // 중복 애니메이션 방지
      if (priceAnimation === 'none') {
        setPriceAnimation(direction);
        
        // 1.5초 후 애니메이션 제거 (더 짧게)
        const timer = setTimeout(() => {
          setPriceAnimation('none');
        }, 1500);
        
        return () => clearTimeout(timer);
      }
    }
    
    if (data) {
      setPrevPrice(data.currentPrice);
    }
  }, [data?.currentPrice, prevPrice, priceAnimation]);

  // 가격 포맷 함수
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  // 변동률 색상 결정
  const getPriceColor = (direction: 'up' | 'down' | 'unchanged') => {
    switch (direction) {
      case 'up': return 'text-red-500'; // 한국 주식: 상승은 빨간색
      case 'down': return 'text-blue-500'; // 한국 주식: 하락은 파란색  
      case 'unchanged': return 'text-muted-foreground';
      default: return 'text-foreground';
    }
  };

  // 변동률 아이콘
  const getChangeIcon = (direction: 'up' | 'down' | 'unchanged') => {
    switch (direction) {
      case 'up': return <TrendingUp className="w-4 h-4" />;
      case 'down': return <TrendingDown className="w-4 h-4" />;
      case 'unchanged': return <Minus className="w-4 h-4" />;
      default: return null;
    }
  };

  // 애니메이션 클래스 (더욱 은은하게 개선)
  const getAnimationClass = () => {
    switch (priceAnimation) {
      case 'up': return 'bg-red-500/5 border-red-500/20 transition-all duration-500 ease-out';
      case 'down': return 'bg-blue-500/5 border-blue-500/20 transition-all duration-500 ease-out';
      case 'none': return 'transition-all duration-500 ease-out';
      default: return '';
    }
  };

  if (!data) {
    return (
      <div className={`p-4 border rounded-lg bg-muted ${className || ''}`}>
        <div className="text-center text-sm text-muted-foreground">
          실시간 데이터 연결 중...
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 border rounded-lg transition-all duration-300 ${getAnimationClass()} ${className || ''}`}>
      {/* 종목명 및 코드 */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="font-semibold text-lg">{data.name}</h3>
          <p className="text-sm text-muted-foreground">{data.symbol}</p>
        </div>
        <div className="text-xs text-muted-foreground">
          {new Date(data.timestamp).toLocaleTimeString('ko-KR')}
        </div>
      </div>

      {/* 현재가 */}
      <div className={`text-2xl font-bold mb-2 ${getPriceColor(data.changeDirection)}`}>
        {formatPrice(data.currentPrice)}원
      </div>

      {/* 등락 정보 */}
      <div className={`flex items-center space-x-2 ${getPriceColor(data.changeDirection)}`}>
        {getChangeIcon(data.changeDirection)}
        <span className="font-medium">
          {data.change >= 0 ? '+' : ''}{formatPrice(data.change)}원
        </span>
        <span className="text-sm">
          ({data.changePercent >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%)
        </span>
      </div>

      {/* 상세 정보 */}
      <div className="mt-4 pt-4 border-t border-border">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">시가</span>
              <span>{formatPrice(data.open)}원</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">고가</span>
              <span className="text-red-500">{formatPrice(data.high)}원</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">저가</span>
              <span className="text-blue-500">{formatPrice(data.low)}원</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">전일종가</span>
              <span>{formatPrice(data.previousClose)}원</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">거래량</span>
              <span>{formatPrice(data.volume)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">상태</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <span className="text-xs">실시간</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}