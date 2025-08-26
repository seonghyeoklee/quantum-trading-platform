'use client';

import { useMemo } from 'react';
import { RealtimeOrderBookData, OrderBookLevel } from '@/lib/api/websocket-types';

interface OrderBookProps {
  data: RealtimeOrderBookData | null;
  className?: string;
  maxLevels?: number;  // 표시할 호가 단계 (기본값: 10)
}

export default function OrderBook({ data, className, maxLevels = 10 }: OrderBookProps) {
  
  // 호가 데이터 전처리
  const processedData = useMemo(() => {
    if (!data) return null;

    // 상위 N개 레벨만 선택
    const asks = data.asks.slice(0, maxLevels).reverse(); // 매도호가는 역순 정렬 (높은 가격이 위)
    const bids = data.bids.slice(0, maxLevels); // 매수호가는 정순 정렬 (높은 가격이 위)
    
    // 최대 잔량 계산 (게이지 바 표시용)
    const maxVolume = Math.max(
      ...asks.map(level => level.volume),
      ...bids.map(level => level.volume)
    );

    return { asks, bids, maxVolume };
  }, [data, maxLevels]);

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

  // 잔량 게이지 바 너비 계산 (퍼센트)
  const getVolumeBarWidth = (volume: number, maxVolume: number) => {
    return maxVolume > 0 ? (volume / maxVolume) * 100 : 0;
  };

  if (!data || !processedData) {
    return (
      <div className={`p-4 border rounded-lg bg-muted ${className || ''}`}>
        <h3 className="font-semibold text-sm mb-4">호가창</h3>
        <div className="text-center text-sm text-muted-foreground py-8">
          호가 데이터 연결 중...
        </div>
      </div>
    );
  }

  const { asks, bids, maxVolume } = processedData;

  return (
    <div className={`border rounded-lg bg-background ${className || ''}`}>
      {/* 헤더 */}
      <div className="p-3 border-b border-border bg-muted/50">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">호가창</h3>
          <div className="text-xs text-muted-foreground">
            {data.symbol} • {new Date(data.timestamp).toLocaleTimeString('ko-KR')}
          </div>
        </div>
      </div>

      <div className="p-3">
        {/* 호가 헤더 */}
        <div className="grid grid-cols-3 gap-2 mb-2 text-xs font-medium text-muted-foreground">
          <div className="text-right">매도잔량</div>
          <div className="text-center">호가</div>
          <div className="text-left">매수잔량</div>
        </div>

        {/* 매도호가 (상단) */}
        <div className="space-y-1 mb-3">
          {asks.map((ask, index) => (
            <div key={`ask-${index}`} className="grid grid-cols-3 gap-2 items-center text-xs">
              {/* 매도잔량 */}
              <div className="relative text-right">
                <div 
                  className="absolute inset-0 bg-blue-500/10 rounded-sm"
                  style={{ width: `${getVolumeBarWidth(ask.volume, maxVolume)}%` }}
                />
                <span className="relative z-10 text-blue-600 font-medium">
                  {formatVolume(ask.volume)}
                </span>
              </div>
              
              {/* 매도호가 */}
              <div className="text-center bg-blue-50 dark:bg-blue-950/20 rounded-sm py-1 px-2">
                <span className="text-blue-600 font-medium">
                  {formatPrice(ask.price)}
                </span>
              </div>
              
              {/* 빈 공간 */}
              <div></div>
            </div>
          ))}
        </div>

        {/* 스프레드 표시 */}
        {asks.length > 0 && bids.length > 0 && (
          <div className="flex items-center justify-center py-2 mb-3 border-y border-border">
            <div className="text-xs text-center">
              <div className="text-muted-foreground mb-1">스프레드</div>
              <div className="font-medium">
                {formatPrice(asks[asks.length - 1].price - bids[0].price)}원
              </div>
              <div className="text-muted-foreground text-[10px]">
                ({((asks[asks.length - 1].price - bids[0].price) / bids[0].price * 100).toFixed(3)}%)
              </div>
            </div>
          </div>
        )}

        {/* 매수호가 (하단) */}
        <div className="space-y-1">
          {bids.map((bid, index) => (
            <div key={`bid-${index}`} className="grid grid-cols-3 gap-2 items-center text-xs">
              {/* 빈 공간 */}
              <div></div>
              
              {/* 매수호가 */}
              <div className="text-center bg-red-50 dark:bg-red-950/20 rounded-sm py-1 px-2">
                <span className="text-red-600 font-medium">
                  {formatPrice(bid.price)}
                </span>
              </div>
              
              {/* 매수잔량 */}
              <div className="relative text-left">
                <div 
                  className="absolute inset-0 bg-red-500/10 rounded-sm"
                  style={{ width: `${getVolumeBarWidth(bid.volume, maxVolume)}%` }}
                />
                <span className="relative z-10 text-red-600 font-medium">
                  {formatVolume(bid.volume)}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* 호가 통계 */}
        <div className="mt-4 pt-3 border-t border-border">
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="space-y-1">
              <div className="flex justify-between text-muted-foreground">
                <span>매도잔량</span>
                <span className="text-blue-600 font-medium">
                  {formatVolume(data.totalAskVolume)}
                </span>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-muted-foreground">
                <span>매수잔량</span>
                <span className="text-red-600 font-medium">
                  {formatVolume(data.totalBidVolume)}
                </span>
              </div>
            </div>
          </div>
          
          {/* 매수/매도 비율 */}
          <div className="mt-2">
            <div className="text-xs text-muted-foreground mb-1">매수/매도 비율</div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-red-500 transition-all duration-300"
                style={{ 
                  width: `${(data.totalBidVolume / (data.totalBidVolume + data.totalAskVolume)) * 100}%` 
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>매수 {((data.totalBidVolume / (data.totalBidVolume + data.totalAskVolume)) * 100).toFixed(1)}%</span>
              <span>매도 {((data.totalAskVolume / (data.totalBidVolume + data.totalAskVolume)) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}