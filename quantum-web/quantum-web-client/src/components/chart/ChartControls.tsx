'use client';

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown } from "lucide-react";
import { ChartTimeframe, ChartType, StockInfo } from './ChartTypes';

interface ChartControlsProps {
  currentTimeframe: ChartTimeframe;
  currentChartType: ChartType;
  currentStock: StockInfo;
  isStockSelected?: boolean;
  onTimeframeChange: (timeframe: ChartTimeframe) => void;
  onChartTypeChange: (chartType: ChartType) => void;
  onStockChange: (symbol: string) => void;
}

const timeframes: { value: ChartTimeframe; label: string }[] = [
  { value: '1D', label: '1일' },
  { value: '5D', label: '5일' },
  { value: '1M', label: '1개월' },
  { value: '3M', label: '3개월' },
  { value: '1Y', label: '1년' },
  { value: 'ALL', label: '전체' },
];

const chartTypes: { value: ChartType; label: string; description: string }[] = [
  { value: 'tick', label: '틱', description: '틱차트' },
  { value: 'minute', label: '분', description: '분봉차트' },
  { value: 'daily', label: '일', description: '일봉차트' },
  { value: 'weekly', label: '주', description: '주봉차트' },
  { value: 'monthly', label: '월', description: '월봉차트' },
  { value: 'yearly', label: '년', description: '년봉차트' },
];

export default function ChartControls({
  currentTimeframe,
  currentChartType,
  currentStock,
  isStockSelected = false,
  onTimeframeChange,
  onChartTypeChange,
  onStockChange,
}: ChartControlsProps) {
  const isPositiveChange = currentStock.change >= 0;

  return (
    <div className="flex flex-col space-y-4 p-4 border-b border-border bg-card">
      {/* 상단: 동적 정보 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          {/* 종목/시장 정보 */}
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-sm font-medium text-blue-700">
                {isStockSelected ? currentStock.name.charAt(0) : '📊'}
              </span>
            </div>
            <div>
              <h2 className="text-lg font-bold">
                {isStockSelected ? `${currentStock.name} (${currentStock.symbol})` : '한국 주식 시장'}
              </h2>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <span>
                  {isStockSelected ? `${currentStock.market} • 실시간 데이터` : 'KOSPI • KOSDAQ'}
                </span>
              </div>
            </div>
          </div>
          
          {/* 동적 정보 요약 */}
          <div className="flex items-center space-x-4">
            {isStockSelected ? (
              /* 선택된 종목 정보 */
              <>
                <div className="text-center">
                  <div className="text-sm text-muted-foreground">현재가</div>
                  <div className="font-semibold">{currentStock.price.toLocaleString()}원</div>
                  <div className={`text-xs flex items-center ${isPositiveChange ? 'text-red-600' : 'text-blue-600'}`}>
                    {isPositiveChange ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                    {isPositiveChange ? '+' : ''}{currentStock.changePercent.toFixed(2)}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-muted-foreground">등락</div>
                  <div className="font-semibold">{isPositiveChange ? '+' : ''}{currentStock.change.toLocaleString()}원</div>
                  <div className="text-xs text-muted-foreground">{currentStock.market}</div>
                </div>
              </>
            ) : (
              /* 기본 지수 정보 */
              <>
                <div className="text-center">
                  <div className="text-sm text-muted-foreground">KOSPI</div>
                  <div className="font-semibold">2,647.82</div>
                  <div className="text-xs text-red-600 flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    +1.23%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-muted-foreground">KOSDAQ</div>
                  <div className="font-semibold">742.15</div>
                  <div className="text-xs text-blue-600 flex items-center">
                    <TrendingDown className="w-3 h-3 mr-1" />
                    -0.84%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-muted-foreground">USD/KRW</div>
                  <div className="font-semibold">1,347.50</div>
                  <div className="text-xs text-red-600 flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    +0.32%
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* 차트 유형 선택 */}
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-muted-foreground">차트 유형:</span>
          <Select value={currentChartType} onValueChange={onChartTypeChange}>
            <SelectTrigger className="w-[100px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {chartTypes.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 하단: 시간대 선택 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-muted-foreground">기간:</span>
          <div className="flex space-x-1">
            {timeframes.map((timeframe) => (
              <Button
                key={timeframe.value}
                variant={currentTimeframe === timeframe.value ? "default" : "outline"}
                size="sm"
                onClick={() => onTimeframeChange(timeframe.value)}
                className="text-xs"
              >
                {timeframe.label}
              </Button>
            ))}
          </div>
        </div>

        {/* 현재 종목 정보 요약 */}
        <div className="flex items-center space-x-3">
          <Badge variant={isPositiveChange ? "default" : "destructive"}>
            {isPositiveChange ? '상승' : '하락'}
          </Badge>
          <span className="text-sm text-muted-foreground">
            {isStockSelected ? currentStock.symbol : 'KOSPI'}
          </span>
        </div>
      </div>
    </div>
  );
}