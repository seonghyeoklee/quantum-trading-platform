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

const stockOptions = [
  { symbol: '005930', name: '삼성전자' },
  { symbol: '035420', name: 'NAVER' },
  { symbol: '035720', name: '카카오' },
];

export default function ChartControls({
  currentTimeframe,
  currentChartType,
  currentStock,
  onTimeframeChange,
  onChartTypeChange,
  onStockChange,
}: ChartControlsProps) {
  const isPositiveChange = currentStock.change >= 0;

  return (
    <div className="flex flex-col space-y-4 p-4 border-b border-border bg-card">
      {/* 상단: 종목 정보 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* 종목 선택 */}
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-sm font-medium text-primary">
                {currentStock.name.charAt(0)}
              </span>
            </div>
            <div>
              <Select value={currentStock.symbol} onValueChange={onStockChange}>
                <SelectTrigger className="w-48 border-none shadow-none p-0 h-auto bg-transparent">
                  <SelectValue>
                    <div>
                      <h2 className="text-lg font-bold text-left">
                        {currentStock.name} ({currentStock.symbol})
                      </h2>
                      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                        <span>{currentStock.market}</span>
                        <span>•</span>
                        <span>한국 주식</span>
                      </div>
                    </div>
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {stockOptions.map((stock) => (
                    <SelectItem key={stock.symbol} value={stock.symbol}>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{stock.name}</span>
                        <span className="text-muted-foreground">({stock.symbol})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {/* 현재 가격 */}
          <div className="text-right">
            <div className="text-2xl font-bold">
              {currentStock.price.toLocaleString('ko-KR')}
            </div>
            <div className={`flex items-center text-sm ${
              isPositiveChange ? 'text-bull' : 'text-bear'
            }`}>
              {isPositiveChange ? (
                <TrendingUp className="w-3 h-3 mr-1" />
              ) : (
                <TrendingDown className="w-3 h-3 mr-1" />
              )}
              <span>
                {isPositiveChange ? '+' : ''}{currentStock.change.toLocaleString('ko-KR')} 
                ({isPositiveChange ? '+' : ''}{currentStock.changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>

        {/* 차트 유형 선택 */}
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-muted-foreground">차트 유형:</span>
          <Select value={currentChartType} onValueChange={onChartTypeChange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {chartTypes.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  <div>
                    <div className="font-medium">{type.label}</div>
                    <div className="text-xs text-muted-foreground">{type.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 하단: 시간대 선택 버튼 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {timeframes.map((timeframe) => (
            <Button
              key={timeframe.value}
              variant={currentTimeframe === timeframe.value ? "default" : "outline"}
              size="sm"
              onClick={() => onTimeframeChange(timeframe.value)}
              className={currentTimeframe === timeframe.value ? 
                "bg-primary text-primary-foreground" : ""
              }
            >
              {timeframe.label}
            </Button>
          ))}
        </div>

        {/* 추가 정보 */}
        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <Badge variant="outline" className="text-xs">
            실시간
          </Badge>
          <span>마지막 업데이트: 방금 전</span>
        </div>
      </div>
    </div>
  );
}