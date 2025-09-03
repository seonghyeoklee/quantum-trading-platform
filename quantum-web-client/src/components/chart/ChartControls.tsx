'use client';

import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { RefreshCw, BarChart3, TrendingUp } from 'lucide-react';
import { ChartConfig } from './types';

interface ChartControlsProps {
  config: ChartConfig;
  onConfigChange: (config: ChartConfig) => void;
  onRefresh: () => void;
  isLoading?: boolean;
  className?: string;
}

export default function ChartControls({
  config,
  onConfigChange,
  onRefresh,
  isLoading = false,
  className = ''
}: ChartControlsProps) {
  
  const handleTimeframeChange = (timeframe: string) => {
    onConfigChange({
      ...config,
      timeframe: timeframe as ChartConfig['timeframe']
    });
  };

  const handleVolumeToggle = (showVolume: boolean) => {
    onConfigChange({
      ...config,
      showVolume
    });
  };

  const handleMAToggle = (showMA: boolean) => {
    onConfigChange({
      ...config,
      showMA
    });
  };

  const handleMAPeriodChange = (periods: string) => {
    const periodArray = periods.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p));
    onConfigChange({
      ...config,
      maPeriods: periodArray
    });
  };

  return (
    <div className={`flex flex-wrap items-center gap-4 p-4 bg-card border border-border rounded-lg shadow-sm ${className}`}>
      
      {/* 시간프레임 선택 */}
      <div className="flex items-center gap-2">
        <Label htmlFor="timeframe" className="text-sm font-medium whitespace-nowrap">
          기간
        </Label>
        <Select value={config.timeframe} onValueChange={handleTimeframeChange}>
          <SelectTrigger className="w-24">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1D">1일</SelectItem>
            <SelectItem value="5D">5일</SelectItem>
            <SelectItem value="1M">1개월</SelectItem>
            <SelectItem value="3M">3개월</SelectItem>
            <SelectItem value="1Y">1년</SelectItem>
            <SelectItem value="5Y">5년</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* 구분선 */}
      <div className="h-6 w-px bg-border" />

      {/* 거래량 표시 토글 */}
      <div className="flex items-center gap-2">
        <BarChart3 className="w-4 h-4 text-muted-foreground" />
        <Label htmlFor="volume" className="text-sm font-medium whitespace-nowrap">
          거래량
        </Label>
        <Switch
          id="volume"
          checked={config.showVolume}
          onCheckedChange={handleVolumeToggle}
        />
      </div>

      {/* 이동평균선 토글 */}
      <div className="flex items-center gap-2">
        <TrendingUp className="w-4 h-4 text-muted-foreground" />
        <Label htmlFor="ma" className="text-sm font-medium whitespace-nowrap">
          이동평균
        </Label>
        <Switch
          id="ma"
          checked={config.showMA}
          onCheckedChange={handleMAToggle}
        />
      </div>

      {/* 이동평균 기간 설정 */}
      {config.showMA && (
        <>
          <div className="h-6 w-px bg-border" />
          <div className="flex items-center gap-2">
            <Label htmlFor="maPeriods" className="text-sm font-medium whitespace-nowrap">
              MA 기간
            </Label>
            <Select 
              value={config.maPeriods.join(', ')} 
              onValueChange={handleMAPeriodChange}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="5, 20">5일, 20일</SelectItem>
                <SelectItem value="5, 20, 60">5일, 20일, 60일</SelectItem>
                <SelectItem value="10, 30">10일, 30일</SelectItem>
                <SelectItem value="20, 60">20일, 60일</SelectItem>
                <SelectItem value="12, 26">12일, 26일</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </>
      )}

      {/* 새로고침 버튼 */}
      <div className="ml-auto">
        <Button
          variant="outline"
          size="sm"
          onClick={onRefresh}
          disabled={isLoading}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          새로고침
        </Button>
      </div>
    </div>
  );
}