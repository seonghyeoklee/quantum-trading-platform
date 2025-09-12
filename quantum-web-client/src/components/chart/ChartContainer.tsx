'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react';
import SimpleChart from './SimpleChart';
import ChartControls from './ChartControls';
import { CandlestickData, ChartConfig } from './types';

interface ChartContainerProps {
  data: CandlestickData[] | undefined;
  symbol: string;
  stockName?: string;
  height?: number;
  className?: string;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export default function ChartContainer({
  data,
  symbol,
  stockName,
  height = 500,
  className = '',
  onRefresh,
  isLoading = false
}: ChartContainerProps) {
  
  // 차트 설정 상태
  const [chartConfig, setChartConfig] = useState<ChartConfig>({
    symbol,
    timeframe: '1M',
    showVolume: true,
    showMA: false,
    maPeriods: [5, 20]
  });

  // 가격 변화 계산
  const getPriceChange = () => {
    if (!data || data.length < 2) return { change: 0, changePercent: 0, trend: 'neutral' as const };
    
    const latest = data[data.length - 1];
    const previous = data[data.length - 2];
    const change = latest.close - previous.close;
    const changePercent = (change / previous.close) * 100;
    
    return {
      change: Math.round(change * 100) / 100,
      changePercent: Math.round(changePercent * 100) / 100,
      trend: change > 0 ? 'up' as const : change < 0 ? 'down' as const : 'neutral' as const
    };
  };

  // 차트 설정 변경 핸들러
  const handleConfigChange = (newConfig: ChartConfig) => {
    setChartConfig(newConfig);
  };

  // 새로고침 핸들러
  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  const priceChange = getPriceChange();
  const currentPrice = data && data.length > 0 ? data[data.length - 1].close : 0;

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            {/* 종목 정보 */}
            <div className="flex items-center gap-3">
              <CardTitle className="text-xl font-bold">
                {stockName || symbol}
              </CardTitle>
              <Badge variant="secondary" className="text-xs font-mono">
                {symbol}
              </Badge>
            </div>
            
            {/* 가격 정보 */}
            {currentPrice > 0 && (
              <div className="flex items-center gap-4">
                <span className="text-3xl font-bold">
                  ₩{currentPrice.toLocaleString()}
                </span>
                
                {priceChange.trend !== 'neutral' && (
                  <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                    priceChange.trend === 'up' 
                      ? 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400' 
                      : 'bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400'
                  }`}>
                    {priceChange.trend === 'up' ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    
                    <span>
                      {priceChange.change >= 0 ? '+' : ''}{priceChange.change.toLocaleString()}
                    </span>
                    <span>
                      ({priceChange.changePercent >= 0 ? '+' : ''}{priceChange.changePercent}%)
                    </span>
                  </div>
                )}
                
                {priceChange.trend === 'neutral' && (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-gray-50 text-gray-600 dark:bg-gray-900 dark:text-gray-400">
                    <Minus className="w-4 h-4" />
                    <span>변동없음</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 차트 상태 표시 */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <BarChart3 className="w-4 h-4" />
            <span>{data ? data.length : 0}개 데이터</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 차트 컨트롤 */}
        <ChartControls
          config={chartConfig}
          onConfigChange={handleConfigChange}
          onRefresh={handleRefresh}
          isLoading={isLoading}
        />

        {/* 차트 */}
        <div className="w-full border border-border rounded-lg overflow-hidden bg-card">
          <SimpleChart
            data={data || []}
            config={chartConfig}
            height={height - 150} // 헤더와 컨트롤 높이 제외
            className="w-full"
          />
        </div>

        {/* 차트 정보 푸터 */}
        {data && data.length > 0 && (
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
            <div className="flex items-center gap-4">
              <span>기간: {chartConfig.timeframe}</span>
              <span>거래량: {chartConfig.showVolume ? '표시' : '숨김'}</span>
              {chartConfig.showMA && (
                <span>이동평균: {chartConfig.maPeriods.join(', ')}일</span>
              )}
            </div>
            <span>
              업데이트: {new Date().toLocaleTimeString('ko-KR')}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}