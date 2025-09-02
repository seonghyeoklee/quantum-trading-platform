'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { 
  TradingStrategy, 
  STRATEGY_CATEGORIES, 
  RISK_LEVELS, 
  DIFFICULTY_LEVELS,
  STRATEGY_STATUSES 
} from '@/lib/types/strategy-types';
import { 
  TrendingUp, 
  BarChart3, 
  Calculator, 
  Settings, 
  Play, 
  Pause, 
  Star,
  Heart,
  Info,
  Activity,
  GitBranch,
  ChevronRight,
  Zap
} from 'lucide-react';

interface StrategyCardProps {
  strategy: TradingStrategy;
  onStatusChange?: (strategyId: string, newStatus: 'active' | 'inactive') => void;
  onFavoriteToggle?: (strategyId: string) => void;
  onViewDetails?: (strategyId: string) => void;
  onSettings?: (strategyId: string) => void;
  className?: string;
}

// 아이콘 매핑
const iconMap: Record<string, any> = {
  TrendingUp,
  BarChart3,
  Calculator,
  Activity,
  GitBranch,
  BarChart: BarChart3,
  Zap
};

export default function StrategyCard({
  strategy,
  onStatusChange,
  onFavoriteToggle,
  onViewDetails,
  onSettings,
  className
}: StrategyCardProps) {
  const [isActive, setIsActive] = useState(strategy.status === 'active');
  const [isFavorite, setIsFavorite] = useState(strategy.isFavorite || false);

  const handleStatusToggle = () => {
    const newStatus = isActive ? 'inactive' : 'active';
    setIsActive(!isActive);
    onStatusChange?.(strategy.id, newStatus);
  };

  const handleFavoriteToggle = () => {
    setIsFavorite(!isFavorite);
    onFavoriteToggle?.(strategy.id);
  };

  const categoryInfo = STRATEGY_CATEGORIES[strategy.category];
  const riskInfo = RISK_LEVELS[strategy.riskLevel];
  const difficultyInfo = DIFFICULTY_LEVELS[strategy.difficulty];
  const statusInfo = STRATEGY_STATUSES[strategy.status];

  const IconComponent = iconMap[strategy.icon] || TrendingUp;

  // 백테스팅 결과 색상 계산
  const getReturnColor = (value: number) => {
    if (value > 10) return 'text-green-600';
    if (value > 0) return 'text-blue-600';
    return 'text-red-600';
  };

  return (
    <Card className={`hover:shadow-lg transition-all duration-200 ${className || ''}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className={`p-2 rounded-lg ${
              categoryInfo.color === 'blue' ? 'bg-blue-100 text-blue-600' :
              categoryInfo.color === 'green' ? 'bg-green-100 text-green-600' :
              'bg-purple-100 text-purple-600'
            }`}>
              <IconComponent className="w-5 h-5" />
            </div>
            
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <CardTitle className="text-lg">{strategy.name}</CardTitle>
                {strategy.isPopular && (
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                )}
              </div>
              
              <div className="flex items-center space-x-2 mb-2">
                <Badge variant="outline" className="text-xs">
                  {categoryInfo.name}
                </Badge>
                <Badge className={`text-xs ${difficultyInfo.color}`}>
                  {difficultyInfo.name}
                </Badge>
                <Badge className={`text-xs ${riskInfo.color}`}>
                  위험도: {riskInfo.name}
                </Badge>
              </div>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleFavoriteToggle}
            className="p-1"
          >
            <Heart className={`w-4 h-4 ${isFavorite ? 'fill-red-500 text-red-500' : 'text-muted-foreground'}`} />
          </Button>
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed">
          {strategy.description}
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 상태 및 설정 */}
        <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Switch
                checked={isActive}
                onCheckedChange={handleStatusToggle}
                disabled={strategy.status === 'testing'}
              />
              <span className="text-sm font-medium">
                {isActive ? '활성화' : '비활성화'}
              </span>
            </div>
            
            <div className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium ${statusInfo.color}`}>
              {strategy.status === 'active' && <Play className="w-3 h-3" />}
              {strategy.status === 'inactive' && <Pause className="w-3 h-3" />}
              {strategy.status === 'testing' && <Activity className="w-3 h-3" />}
              <span>{statusInfo.name}</span>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onSettings?.(strategy.id)}
            className="text-xs"
          >
            <Settings className="w-3 h-3 mr-1" />
            설정
          </Button>
        </div>

        {/* 백테스팅 결과 */}
        {strategy.backtest && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold flex items-center">
              <BarChart3 className="w-4 h-4 mr-1" />
              백테스팅 결과
            </h4>
            
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-2 bg-background rounded border">
                <div className={`text-lg font-bold ${getReturnColor(strategy.backtest.totalReturn)}`}>
                  {strategy.backtest.totalReturn > 0 ? '+' : ''}{strategy.backtest.totalReturn}%
                </div>
                <div className="text-xs text-muted-foreground">총 수익률</div>
              </div>
              
              <div className="text-center p-2 bg-background rounded border">
                <div className="text-lg font-bold text-blue-600">
                  {strategy.backtest.winRate}%
                </div>
                <div className="text-xs text-muted-foreground">승률</div>
              </div>
              
              <div className="text-center p-2 bg-background rounded border">
                <div className="text-lg font-bold text-purple-600">
                  {strategy.backtest.sharpeRatio}
                </div>
                <div className="text-xs text-muted-foreground">샤프비율</div>
              </div>
              
              <div className="text-center p-2 bg-background rounded border">
                <div className="text-lg font-bold text-red-600">
                  {strategy.backtest.maxDrawdown}%
                </div>
                <div className="text-xs text-muted-foreground">MDD</div>
              </div>
            </div>
            
            <div className="text-xs text-muted-foreground text-center">
              {strategy.backtest.period} • 총 {strategy.backtest.totalTrades}회 거래
            </div>
          </div>
        )}

        {/* 전략 특성 */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">시간프레임</span>
            <span className="font-medium">{strategy.timeframe}</span>
          </div>
          
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">적합한 시장</span>
            <div className="flex space-x-1">
              {strategy.marketSuitability.map((market, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {market}
                </Badge>
              ))}
            </div>
          </div>
        </div>

        {/* 태그 */}
        <div className="flex flex-wrap gap-1">
          {strategy.tags.map((tag, index) => (
            <Badge key={index} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>

        {/* 액션 버튼 */}
        <div className="flex space-x-2 pt-2 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetails?.(strategy.id)}
            className="flex-1 text-xs"
          >
            <Info className="w-3 h-3 mr-1" />
            상세보기
          </Button>
          
          <Button
            variant="default"
            size="sm"
            onClick={() => onViewDetails?.(strategy.id)}
            className="flex-1 text-xs"
          >
            <ChevronRight className="w-3 h-3 mr-1" />
            백테스팅
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}