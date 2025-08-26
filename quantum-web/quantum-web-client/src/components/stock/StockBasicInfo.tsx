'use client';

import { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ArrowUp, 
  ArrowDown,
  RefreshCw,
  Calendar,
  Activity
} from 'lucide-react';
import { StockBasicInfo } from '@/lib/api/stock-info-types';
import { 
  MarketCapTooltip,
  ForeignOwnershipTooltip,
  UpperLimitTooltip,
  LowerLimitTooltip,
  Week52HighTooltip,
  Week52LowTooltip
} from '@/components/ui/TermTooltip';

interface StockBasicInfoProps {
  stockInfo: StockBasicInfo | null;
  loading: boolean;
  error: string | null;
  onRefresh?: () => void;
  className?: string;
}

export default function StockBasicInfoComponent({ 
  stockInfo, 
  loading, 
  error, 
  onRefresh, 
  className 
}: StockBasicInfoProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!onRefresh || isRefreshing) return;
    
    setIsRefreshing(true);
    await onRefresh();
    setTimeout(() => setIsRefreshing(false), 1000); // 최소 1초 스피너 표시
  };

  // 가격 포맷 함수
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  // 비율 포맷 함수
  const formatPercent = (percent: number, decimals: number = 2) => {
    return `${percent > 0 ? '+' : ''}${percent.toFixed(decimals)}%`;
  };

  // 큰 숫자 포맷 함수 (억, 조)
  const formatLargeNumber = (num: number, unit: string = '') => {
    if (num >= 10000) {
      return `${(num / 10000).toFixed(1)}조${unit}`;
    } else if (num >= 100) {
      return `${num.toLocaleString('ko-KR')}억${unit}`;
    } else {
      return `${num.toFixed(1)}억${unit}`;
    }
  };

  // 등락 방향에 따른 색상 클래스
  const getPriceColorClass = (direction: 'up' | 'down' | 'unchanged') => {
    switch (direction) {
      case 'up': return 'text-red-600 dark:text-red-400';
      case 'down': return 'text-blue-600 dark:text-blue-400';
      default: return 'text-muted-foreground';
    }
  };

  // 등락 방향 아이콘
  const getChangeIcon = (direction: 'up' | 'down' | 'unchanged') => {
    switch (direction) {
      case 'up': return <TrendingUp className="w-4 h-4" />;
      case 'down': return <TrendingDown className="w-4 h-4" />;
      default: return <Minus className="w-4 h-4" />;
    }
  };

  // 로딩 스켈레톤
  if (loading) {
    return (
      <div className={`space-y-4 ${className || ''}`}>
        <div className="border rounded-lg p-6 bg-background">
          <div className="animate-pulse space-y-4">
            {/* 헤더 스켈레톤 */}
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <div className="h-4 bg-muted rounded w-24"></div>
                <div className="h-6 bg-muted rounded w-32"></div>
              </div>
              <div className="h-8 w-8 bg-muted rounded-full"></div>
            </div>
            
            {/* 현재가 스켈레톤 */}
            <div className="space-y-2">
              <div className="h-8 bg-muted rounded w-40"></div>
              <div className="flex items-center space-x-2">
                <div className="h-4 bg-muted rounded w-16"></div>
                <div className="h-4 bg-muted rounded w-12"></div>
              </div>
            </div>
            
            {/* 정보 그리드 스켈레톤 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <div className="h-3 bg-muted rounded w-12"></div>
                  <div className="h-4 bg-muted rounded w-20"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className={`${className || ''}`}>
        <div className="border border-destructive rounded-lg p-6 bg-destructive/5">
          <div className="text-center space-y-4">
            <div className="text-destructive font-medium">종목 정보 조회 실패</div>
            <p className="text-sm text-muted-foreground">{error}</p>
            {onRefresh && (
              <button
                onClick={handleRefresh}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                disabled={isRefreshing}
              >
                다시 시도
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // 데이터가 없는 경우
  if (!stockInfo) {
    return (
      <div className={`${className || ''}`}>
        <div className="border rounded-lg p-6 bg-background">
          <div className="text-center text-muted-foreground">
            종목 정보를 선택해주세요
          </div>
        </div>
      </div>
    );
  }

  const priceColorClass = getPriceColorClass(stockInfo.changeDirection);

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {/* 메인 정보 카드 */}
      <div className="border rounded-lg p-6 bg-background">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-4">
          <div className="space-y-1">
            <div className="text-sm text-muted-foreground">
              {stockInfo.symbol}
            </div>
            <h2 className="text-xl font-bold">
              {stockInfo.name}
            </h2>
          </div>
          
          {onRefresh && (
            <button
              onClick={handleRefresh}
              className="p-2 hover:bg-muted rounded-full transition-colors"
              disabled={isRefreshing}
              title="새로고침"
            >
              <RefreshCw 
                className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} 
              />
            </button>
          )}
        </div>

        {/* 현재가 정보 */}
        <div className="space-y-2 mb-6">
          <div className="flex items-baseline space-x-2">
            <span className="text-3xl font-bold">
              {formatPrice(stockInfo.currentPrice)}
            </span>
            <span className="text-sm text-muted-foreground">원</span>
          </div>
          
          <div className={`flex items-center space-x-2 ${priceColorClass}`}>
            {getChangeIcon(stockInfo.changeDirection)}
            <span className="font-medium">
              {stockInfo.change > 0 ? '+' : ''}{formatPrice(stockInfo.change)}
            </span>
            <span className="font-medium">
              ({formatPercent(stockInfo.changePercent)})
            </span>
          </div>
        </div>

        {/* 당일 거래 정보 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">시가</div>
            <div className="font-medium">{formatPrice(stockInfo.openPrice)}</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">고가</div>
            <div className="font-medium text-red-600">
              {formatPrice(stockInfo.highPrice)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">저가</div>
            <div className="font-medium text-blue-600">
              {formatPrice(stockInfo.lowPrice)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">거래량</div>
            <div className="font-medium">
              {stockInfo.volume.toLocaleString('ko-KR')}
            </div>
          </div>
        </div>
      </div>

      {/* 상세 정보 그리드 */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* 가격 범위 정보 */}
        <div className="border rounded-lg p-4 bg-background">
          <h3 className="font-semibold mb-3 flex items-center">
            <Activity className="w-4 h-4 mr-2" />
            가격 범위
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <UpperLimitTooltip>
                <span className="text-sm text-muted-foreground">상한가</span>
              </UpperLimitTooltip>
              <span className="font-medium text-red-600">
                {formatPrice(stockInfo.upperLimit)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <LowerLimitTooltip>
                <span className="text-sm text-muted-foreground">하한가</span>
              </LowerLimitTooltip>
              <span className="font-medium text-blue-600">
                {formatPrice(stockInfo.lowerLimit)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <Week52HighTooltip>
                <span className="text-sm text-muted-foreground">52주 고가</span>
              </Week52HighTooltip>
              <span className="font-medium">
                {formatPrice(stockInfo.week52High)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <Week52LowTooltip>
                <span className="text-sm text-muted-foreground">52주 저가</span>
              </Week52LowTooltip>
              <span className="font-medium">
                {formatPrice(stockInfo.week52Low)}
              </span>
            </div>
          </div>
        </div>

        {/* 기업 정보 */}
        <div className="border rounded-lg p-4 bg-background">
          <h3 className="font-semibold mb-3 flex items-center">
            <Calendar className="w-4 h-4 mr-2" />
            기업 정보
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <MarketCapTooltip>
                <span className="text-sm text-muted-foreground">시가총액</span>
              </MarketCapTooltip>
              <span className="font-medium">
                {formatLargeNumber(stockInfo.marketCap)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">거래대금</span>
              <span className="font-medium">
                {formatLargeNumber(stockInfo.tradingValue)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <ForeignOwnershipTooltip>
                <span className="text-sm text-muted-foreground">외국인비율</span>
              </ForeignOwnershipTooltip>
              <span className="font-medium">
                {formatPercent(stockInfo.foreignOwnership)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">유통비율</span>
              <span className="font-medium">
                {formatPercent(stockInfo.circulatingRatio)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 업데이트 시간 */}
      <div className="text-xs text-muted-foreground text-center">
        최종 업데이트: {new Date(stockInfo.lastUpdated).toLocaleString('ko-KR')}
      </div>
    </div>
  );
}