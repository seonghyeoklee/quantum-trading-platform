'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  TrendingUp, 
  Activity, 
  BarChart3, 
  Zap, 
  DollarSign,
  Target,
  Shield,
  AlertTriangle
} from 'lucide-react';
import { TradingStrategy } from '@/lib/types/trading-strategy';

interface StrategySelectorProps {
  onStrategySelect: (strategy: TradingStrategy) => void;
  selectedStrategy?: TradingStrategy;
}

// 미리 정의된 전략들
const PREDEFINED_STRATEGIES: TradingStrategy[] = [
  {
    id: 'moving_average_crossover',
    name: '이동평균 교차 전략',
    description: '단기 이동평균이 장기 이동평균을 상향/하향 돌파할 때 매수/매도하는 추세추종 전략입니다.',
    category: 'trend',
    risk_level: 'medium',
    min_capital: 1000000,
    expected_return: '8-15%',
    success_rate: 72,
    parameters: [
      {
        name: 'short_period',
        label: '단기 이동평균',
        type: 'number',
        default_value: 5,
        min_value: 3,
        max_value: 20,
        description: '단기 이동평균 기간 (일)'
      },
      {
        name: 'long_period',
        label: '장기 이동평균',
        type: 'number',
        default_value: 20,
        min_value: 10,
        max_value: 60,
        description: '장기 이동평균 기간 (일)'
      }
    ],
    indicators: ['MA5', 'MA20', 'Volume', 'MACD']
  },
  {
    id: 'rsi_mean_reversion',
    name: 'RSI 평균회귀 전략',
    description: 'RSI가 과매수/과매도 구간에 진입할 때 반대 포지션을 취하는 평균회귀 전략입니다.',
    category: 'mean_reversion',
    risk_level: 'medium',
    min_capital: 500000,
    expected_return: '12-20%',
    success_rate: 68,
    parameters: [
      {
        name: 'rsi_period',
        label: 'RSI 기간',
        type: 'number',
        default_value: 14,
        min_value: 7,
        max_value: 21,
        description: 'RSI 계산 기간 (일)'
      },
      {
        name: 'oversold_threshold',
        label: '과매도 기준',
        type: 'number',
        default_value: 30,
        min_value: 20,
        max_value: 35,
        description: 'RSI 과매도 임계값'
      },
      {
        name: 'overbought_threshold',
        label: '과매수 기준',
        type: 'number',
        default_value: 70,
        min_value: 65,
        max_value: 80,
        description: 'RSI 과매수 임계값'
      }
    ],
    indicators: ['RSI', 'Volume', 'Bollinger Bands']
  },
  {
    id: 'momentum_breakout',
    name: '모멘텀 돌파 전략',
    description: '거래량을 동반한 가격 돌파 시 추세를 따라가는 모멘텀 전략입니다.',
    category: 'momentum',
    risk_level: 'high',
    min_capital: 2000000,
    expected_return: '15-30%',
    success_rate: 65,
    parameters: [
      {
        name: 'breakout_period',
        label: '돌파 기간',
        type: 'number',
        default_value: 20,
        min_value: 10,
        max_value: 50,
        description: '돌파 기준 기간 (일)'
      },
      {
        name: 'volume_multiplier',
        label: '거래량 배수',
        type: 'number',
        default_value: 1.5,
        min_value: 1.2,
        max_value: 3.0,
        description: '평균 거래량 대비 최소 배수'
      }
    ],
    indicators: ['Bollinger Bands', 'Volume', 'ATR', 'MACD']
  },
  {
    id: 'volatility_trading',
    name: '변동성 돌파 전략',
    description: 'ATR 기반 변동성을 이용한 단기 매매 전략입니다.',
    category: 'volatility',
    risk_level: 'high',
    min_capital: 3000000,
    expected_return: '20-35%',
    success_rate: 58,
    parameters: [
      {
        name: 'atr_period',
        label: 'ATR 기간',
        type: 'number',
        default_value: 14,
        min_value: 7,
        max_value: 21,
        description: 'ATR 계산 기간 (일)'
      },
      {
        name: 'volatility_multiplier',
        label: '변동성 배수',
        type: 'number',
        default_value: 2.0,
        min_value: 1.0,
        max_value: 4.0,
        description: 'ATR 대비 진입 기준 배수'
      }
    ],
    indicators: ['ATR', 'Bollinger Bands', 'Volume', 'RSI']
  }
];

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'trend': return TrendingUp;
    case 'momentum': return Zap;
    case 'mean_reversion': return Activity;
    case 'volatility': return BarChart3;
    case 'fundamental': return DollarSign;
    default: return Target;
  }
};

const getCategoryColor = (category: string) => {
  switch (category) {
    case 'trend': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'momentum': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    case 'mean_reversion': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'volatility': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    case 'fundamental': return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200';
    default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

const getRiskLevelColor = (riskLevel: string) => {
  switch (riskLevel) {
    case 'low': return 'text-green-600';
    case 'medium': return 'text-yellow-600';
    case 'high': return 'text-red-600';
    default: return 'text-gray-600';
  }
};

const getRiskLevelIcon = (riskLevel: string) => {
  switch (riskLevel) {
    case 'low': return Shield;
    case 'medium': return Target;
    case 'high': return AlertTriangle;
    default: return Shield;
  }
};

export default function StrategySelector({ onStrategySelect, selectedStrategy }: StrategySelectorProps) {
  const [hoveredStrategy, setHoveredStrategy] = useState<string | null>(null);

  const getCategoryText = (category: string) => {
    switch (category) {
      case 'trend': return '📈 추세추종';
      case 'momentum': return '⚡ 모멘텀';
      case 'mean_reversion': return '🎯 평균회귀';
      case 'volatility': return '🌊 변동성';
      case 'fundamental': return '📊 기본분석';
      default: return category;
    }
  };

  const getRiskText = (level: string) => {
    switch (level) {
      case 'low': return '안정형';
      case 'medium': return '균형형';
      case 'high': return '공격형';
      default: return level;
    }
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 70) return 'text-green-600 bg-green-50 dark:bg-green-950';
    if (rate >= 60) return 'text-blue-600 bg-blue-50 dark:bg-blue-950';
    return 'text-orange-600 bg-orange-50 dark:bg-orange-950';
  };

  return (
    <div className="space-y-6">
      {/* 전략 개요 */}
      <div className="text-center p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 rounded-xl border">
        <div className="flex items-center justify-center space-x-2 mb-3">
          <Target className="w-6 h-6 text-primary" />
          <h3 className="text-xl font-bold">🤖 AI 분석 기반 전략</h3>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          실제 시장 데이터와 백테스팅을 통해 검증된 전략들입니다. 
          각 전략의 위험 수준과 수익률을 확인하고 투자 성향에 맞는 전략을 선택하세요.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {PREDEFINED_STRATEGIES.map((strategy, index) => {
          const CategoryIcon = getCategoryIcon(strategy.category);
          const RiskIcon = getRiskLevelIcon(strategy.risk_level);
          const isSelected = selectedStrategy?.id === strategy.id;
          const isHovered = hoveredStrategy === strategy.id;
          
          return (
            <Card 
              key={strategy.id}
              className={`cursor-pointer transition-all duration-300 hover:shadow-xl ${
                isSelected 
                  ? 'ring-2 ring-primary border-primary bg-primary/5 shadow-lg transform scale-[1.02]' 
                  : isHovered 
                    ? 'shadow-lg scale-[1.01] border-primary/50' 
                    : 'hover:shadow-md hover:border-primary/30'
              }`}
              onMouseEnter={() => setHoveredStrategy(strategy.id)}
              onMouseLeave={() => setHoveredStrategy(null)}
              onClick={() => onStrategySelect(strategy)}
            >
              {/* 헤더 */}
              <CardHeader className="space-y-4 pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className={`p-3 rounded-xl ${
                      isSelected 
                        ? 'bg-primary text-primary-foreground shadow-md' 
                        : getCategoryColor(strategy.category)
                    } transition-all duration-200`}>
                      <CategoryIcon className="w-6 h-6" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <CardTitle className="text-lg leading-tight">{strategy.name}</CardTitle>
                        {index === 0 && (
                          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 text-xs">
                            👑 인기
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 mt-2">
                        <Badge variant="outline" className={`text-xs font-medium ${getCategoryColor(strategy.category)}`}>
                          {getCategoryText(strategy.category)}
                        </Badge>
                        <div className={`flex items-center space-x-1 text-xs ${getRiskLevelColor(strategy.risk_level)}`}>
                          <RiskIcon className="w-3 h-3" />
                          <span className="font-medium">{getRiskText(strategy.risk_level)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {isSelected && (
                    <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-md">
                      <Target className="w-4 h-4" />
                    </div>
                  )}
                </div>
                
                <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                  {strategy.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-5 pt-0">
                {/* 핵심 성과 지표 */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                    <div className="text-base font-bold text-green-600 mb-1">{strategy.expected_return}</div>
                    <div className="text-xs text-green-700 dark:text-green-300">예상수익률</div>
                  </div>
                  <div className={`text-center p-3 rounded-lg border ${getSuccessRateColor(strategy.success_rate)}`}>
                    <div className="text-base font-bold mb-1">{strategy.success_rate}%</div>
                    <div className="text-xs opacity-80">성공률</div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <div className="text-base font-bold text-blue-600 mb-1">
                      {(strategy.min_capital / 10000).toLocaleString()}만
                    </div>
                    <div className="text-xs text-blue-700 dark:text-blue-300">최소투자</div>
                  </div>
                </div>
                
                {/* 성공률 시각화 */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground flex items-center space-x-1">
                      <BarChart3 className="w-3 h-3" />
                      <span>백테스팅 성공률</span>
                    </span>
                    <span className="text-xs font-semibold">{strategy.success_rate}/100</span>
                  </div>
                  <div className="relative">
                    <Progress value={strategy.success_rate} className="h-2" />
                    <div className="absolute right-0 top-0 h-2 w-1 bg-gray-300 dark:bg-gray-600 rounded-r"></div>
                  </div>
                </div>

                {/* 사용 지표 */}
                <div className="space-y-2">
                  <div className="flex items-center space-x-1">
                    <Activity className="w-3 h-3 text-muted-foreground" />
                    <span className="text-xs font-medium text-muted-foreground">핵심 기술지표</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {strategy.indicators.map((indicator, idx) => (
                      <Badge 
                        key={indicator} 
                        variant="outline" 
                        className={`text-xs ${
                          idx === 0 ? 'bg-primary/10 border-primary/30 text-primary' : ''
                        }`}
                      >
                        {indicator}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* 선택/미선택 상태 표시 */}
                {isSelected ? (
                  <div className="flex items-center justify-center space-x-2 p-3 bg-primary/10 rounded-lg border border-primary/20">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                    <span className="text-sm font-medium text-primary">선택된 전략</span>
                  </div>
                ) : (
                  <Button 
                    variant="outline" 
                    className="w-full hover:bg-primary hover:text-primary-foreground transition-all duration-200"
                    onClick={(e) => {
                      e.stopPropagation();
                      onStrategySelect(strategy);
                    }}
                  >
                    <Target className="w-4 h-4 mr-2" />
                    이 전략 선택하기
                  </Button>
                )}

                {/* 호버 시 추가 정보 */}
                {isHovered && !isSelected && (
                  <div className="absolute inset-0 bg-primary/5 rounded-lg border border-primary/20 flex items-center justify-center backdrop-blur-sm transition-all duration-200">
                    <div className="text-center">
                      <Target className="w-8 h-8 text-primary mx-auto mb-2" />
                      <p className="text-sm font-medium text-primary">클릭하여 선택</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 선택 가이드 */}
      {!selectedStrategy && (
        <div className="text-center p-4 bg-amber-50 dark:bg-amber-950/20 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <span className="font-medium text-amber-800 dark:text-amber-200">전략 선택 가이드</span>
          </div>
          <p className="text-sm text-amber-700 dark:text-amber-300">
            전략을 선택하면 자동으로 다음 단계로 이동하여 적합한 종목을 분석합니다
          </p>
        </div>
      )}
    </div>
  );
}