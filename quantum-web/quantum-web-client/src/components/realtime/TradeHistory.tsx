'use client';

import { useState, useEffect, useMemo } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { RealtimeTradeData } from '@/lib/api/websocket-types';

interface TradeHistoryProps {
  trades: RealtimeTradeData[];
  className?: string;
  maxItems?: number;  // 최대 표시 개수 (기본값: 50)
}

export default function TradeHistory({ trades, className, maxItems = 50 }: TradeHistoryProps) {
  const [animatedTrades, setAnimatedTrades] = useState<Set<string>>(new Set());

  // 최신 체결 내역만 표시 (시간 역순 정렬)
  const displayTrades = useMemo(() => {
    return [...trades]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, maxItems);
  }, [trades, maxItems]);

  // 새로운 체결 내역 애니메이션 (성능 최적화)
  useEffect(() => {
    if (displayTrades.length > 0) {
      const latestTrade = displayTrades[0]; // displayTrades는 시간 역순이므로 최신이 첫 번째
      const tradeId = latestTrade.id || `${latestTrade.symbol}-${latestTrade.timestamp}-${Date.now()}`;
      
      // 이미 애니메이션 중인 트레이드는 스킵
      if (!animatedTrades.has(tradeId)) {
        setAnimatedTrades(prev => new Set(prev).add(tradeId));
        
        // 1초 후 애니메이션 제거 (더 빠르게)
        const timer = setTimeout(() => {
          setAnimatedTrades(prev => {
            const newSet = new Set(prev);
            newSet.delete(tradeId);
            return newSet;
          });
        }, 1000);
        
        return () => clearTimeout(timer);
      }
    }
  }, [displayTrades.length]); // displayTrades 의존성으로 변경하고 animatedTrades 제거 (순환 의존성 방지)

  // 가격 포맷 함수
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  // 거래량 포맷 함수
  const formatVolume = (volume: number) => {
    if (volume >= 1000000) {
      return (volume / 1000000).toFixed(1) + 'M';
    } else if (volume >= 1000) {
      return (volume / 1000).toFixed(1) + 'K';
    }
    return volume.toLocaleString('ko-KR');
  };

  // 시간 포맷 함수 (HH:mm:ss)
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // 체결 타입에 따른 색상
  const getTradeColor = (tradeType: 'buy' | 'sell' | 'unknown') => {
    switch (tradeType) {
      case 'buy': return 'text-red-600';  // 매수 체결 (빨간색)
      case 'sell': return 'text-blue-600'; // 매도 체결 (파란색)
      case 'unknown': return 'text-muted-foreground'; // 불명 (회색)
      default: return 'text-foreground';
    }
  };

  // 체결 타입 아이콘
  const getTradeIcon = (tradeType: 'buy' | 'sell' | 'unknown') => {
    switch (tradeType) {
      case 'buy': return <TrendingUp className="w-3 h-3" />;
      case 'sell': return <TrendingDown className="w-3 h-3" />;
      case 'unknown': return <Minus className="w-3 h-3" />;
      default: return null;
    }
  };

  // 가격 변동 표시
  const getPriceChangeDisplay = (changeFromPrevious: number) => {
    if (changeFromPrevious > 0) {
      return (
        <span className="text-red-600 text-xs">
          ▲{formatPrice(changeFromPrevious)}
        </span>
      );
    } else if (changeFromPrevious < 0) {
      return (
        <span className="text-blue-600 text-xs">
          ▼{formatPrice(Math.abs(changeFromPrevious))}
        </span>
      );
    } else {
      return <span className="text-muted-foreground text-xs">-</span>;
    }
  };

  if (!trades || trades.length === 0) {
    return (
      <div className={`border rounded-lg bg-background ${className || ''}`}>
        <div className="p-3 border-b border-border bg-muted/50">
          <h3 className="font-semibold text-sm">체결 내역</h3>
        </div>
        <div className="p-4 text-center text-sm text-muted-foreground">
          체결 내역이 없습니다
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg bg-background ${className || ''}`}>
      {/* 헤더 */}
      <div className="p-3 border-b border-border bg-muted/50">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">체결 내역</h3>
          <div className="text-xs text-muted-foreground">
            최근 {displayTrades.length}건
          </div>
        </div>
      </div>

      {/* 컬럼 헤더 */}
      <div className="px-3 py-2 border-b border-border bg-muted/20">
        <div className="grid grid-cols-5 gap-2 text-xs font-medium text-muted-foreground">
          <div className="text-center">시간</div>
          <div className="text-right">체결가</div>
          <div className="text-center">변동</div>
          <div className="text-right">수량</div>
          <div className="text-center">구분</div>
        </div>
      </div>

      {/* 체결 내역 리스트 */}
      <div className="max-h-96 overflow-y-auto">
        {displayTrades.map((trade, index) => {
          // 고유 ID가 있으면 사용하고, 없으면 폴백 방식 사용
          const tradeId = trade.id || `${trade.symbol}-${trade.timestamp}-${index}`;
          const isAnimated = animatedTrades.has(tradeId);
          
          return (
            <div 
              key={tradeId}
              className={`
                grid grid-cols-5 gap-2 items-center px-3 py-2 text-xs border-b border-border/50 last:border-b-0
                hover:bg-muted/50 transition-all duration-500
                ${isAnimated ? 'bg-yellow-50 dark:bg-yellow-900/10' : ''}
              `}
            >
              {/* 체결 시간 */}
              <div className="text-center text-muted-foreground">
                {formatTime(trade.timestamp)}
              </div>

              {/* 체결가 */}
              <div className={`text-right font-medium ${getTradeColor(trade.tradeType)}`}>
                {formatPrice(trade.price)}
              </div>

              {/* 직전대비 변동 */}
              <div className="text-center">
                {getPriceChangeDisplay(trade.changeFromPrevious)}
              </div>

              {/* 체결 수량 */}
              <div className="text-right">
                {formatVolume(trade.volume)}
              </div>

              {/* 매수/매도 구분 */}
              <div className={`flex items-center justify-center ${getTradeColor(trade.tradeType)}`}>
                {getTradeIcon(trade.tradeType)}
              </div>
            </div>
          );
        })}
      </div>

      {/* 통계 정보 */}
      <div className="p-3 border-t border-border bg-muted/20">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="space-y-1">
            <div className="text-muted-foreground">총 체결 건수</div>
            <div className="font-medium">{trades.length.toLocaleString('ko-KR')}건</div>
          </div>
          <div className="space-y-1">
            <div className="text-muted-foreground">총 체결량</div>
            <div className="font-medium">
              {formatVolume(trades.reduce((sum, trade) => sum + trade.volume, 0))}
            </div>
          </div>
        </div>

        {/* 매수/매도 비율 */}
        {trades.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-muted-foreground mb-2">체결 구분</div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-center">
                <div className="text-red-600 font-medium">
                  {trades.filter(t => t.tradeType === 'buy').length}
                </div>
                <div className="text-muted-foreground">매수</div>
              </div>
              <div className="text-center">
                <div className="text-blue-600 font-medium">
                  {trades.filter(t => t.tradeType === 'sell').length}
                </div>
                <div className="text-muted-foreground">매도</div>
              </div>
              <div className="text-center">
                <div className="text-muted-foreground font-medium">
                  {trades.filter(t => t.tradeType === 'unknown').length}
                </div>
                <div className="text-muted-foreground">기타</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}