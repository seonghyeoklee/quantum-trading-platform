'use client';

import { useMarket } from '@/contexts/MarketContext';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Building2, 
  Globe, 
  TrendingUp, 
  TrendingDown,
  Clock,
  Wifi,
  WifiOff
} from 'lucide-react';

interface MarketIndicatorProps {
  variant?: 'badge' | 'button' | 'detailed' | 'compact';
  showStatus?: boolean;
  showTime?: boolean;
  interactive?: boolean;
}

export function MarketIndicator({ 
  variant = 'badge', 
  showStatus = true, 
  showTime = false,
  interactive = false 
}: MarketIndicatorProps) {
  const { currentMarket, selectedExchange, switchMarket } = useMarket();

  const marketConfig = {
    domestic: {
      label: '국내',
      icon: Building2,
      color: 'bg-blue-500',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-700',
      borderColor: 'border-blue-200',
      exchanges: ['KOSPI', 'KOSDAQ', 'KONEX'],
      timezone: 'Asia/Seoul',
      tradingHours: '09:00-15:30'
    },
    overseas: {
      label: '해외',
      icon: Globe,
      color: 'bg-green-500',
      bgColor: 'bg-green-50',
      textColor: 'text-green-700',
      borderColor: 'border-green-200',
      exchanges: ['NASDAQ', 'NYSE', 'LSE', 'TSE'],
      timezone: 'America/New_York',
      tradingHours: '09:30-16:00 (현지시간)'
    }
  };

  const config = marketConfig[currentMarket];
  const IconComponent = config.icon;

  // 거래시간 체크 (간단한 예시)
  const isMarketOpen = () => {
    const now = new Date();
    const hour = now.getHours();
    
    if (currentMarket === 'domestic') {
      // 한국 시장: 09:00-15:30 (주말 제외)
      const dayOfWeek = now.getDay();
      return dayOfWeek >= 1 && dayOfWeek <= 5 && hour >= 9 && hour < 16;
    } else {
      // 해외 시장 (간단화): 22:30-05:00 한국시간 (미국 시장 기준)
      return hour >= 22 || hour < 5;
    }
  };

  const marketOpen = isMarketOpen();

  if (variant === 'compact') {
    return (
      <div className="flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${config.color}`} />
        <span className="text-xs font-medium">{config.label}</span>
        {showStatus && (
          <div className={`w-1.5 h-1.5 rounded-full ${
            marketOpen ? 'bg-green-400' : 'bg-red-400'
          }`} />
        )}
      </div>
    );
  }

  if (variant === 'badge') {
    return (
      <Badge 
        variant="outline" 
        className={`${config.bgColor} ${config.borderColor} ${config.textColor}`}
      >
        <IconComponent className="w-3 h-3 mr-1" />
        {config.label}
        {selectedExchange && (
          <span className="ml-1 opacity-75">• {selectedExchange}</span>
        )}
      </Badge>
    );
  }

  if (variant === 'button') {
    return (
      <div className="flex space-x-1">
        <Button
          variant={currentMarket === 'domestic' ? 'default' : 'outline'}
          size="sm"
          onClick={() => interactive && switchMarket('domestic')}
          disabled={!interactive}
          className={currentMarket === 'domestic' ? 
            'bg-blue-600 hover:bg-blue-700' : 
            'border-blue-200 text-blue-700 hover:bg-blue-50'
          }
        >
          <Building2 className="w-4 h-4 mr-2" />
          국내
        </Button>
        
        <Button
          variant={currentMarket === 'overseas' ? 'default' : 'outline'}
          size="sm"
          onClick={() => interactive && switchMarket('overseas')}
          disabled={!interactive}
          className={currentMarket === 'overseas' ? 
            'bg-green-600 hover:bg-green-700' : 
            'border-green-200 text-green-700 hover:bg-green-50'
          }
        >
          <Globe className="w-4 h-4 mr-2" />
          해외
        </Button>
      </div>
    );
  }

  if (variant === 'detailed') {
    return (
      <div className={`p-4 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 rounded-lg ${config.color} flex items-center justify-center`}>
              <IconComponent className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className={`font-semibold ${config.textColor}`}>
                {config.label} 시장
              </h3>
              {selectedExchange && (
                <p className="text-sm text-muted-foreground">
                  {selectedExchange}
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {marketOpen ? (
              <Wifi className="w-4 h-4 text-green-600" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-600" />
            )}
            <span className={`text-sm font-medium ${
              marketOpen ? 'text-green-600' : 'text-red-600'
            }`}>
              {marketOpen ? '개장' : '폐장'}
            </span>
          </div>
        </div>

        {showTime && (
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <Clock className="w-3 h-3" />
              <span>거래시간: {config.tradingHours}</span>
            </div>
            <div>
              {new Date().toLocaleTimeString('ko-KR', {
                timeZone: config.timezone,
                hour: '2-digit',
                minute: '2-digit'
              })} ({config.timezone.split('/')[1]})
            </div>
          </div>
        )}

        <div className="mt-3 flex space-x-2">
          {config.exchanges.map((exchange) => (
            <Badge
              key={exchange}
              variant={selectedExchange === exchange ? 'default' : 'outline'}
              className="text-xs"
            >
              {exchange}
            </Badge>
          ))}
        </div>

        {showStatus && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-red-500" />
                <div>
                  <div className="font-medium">상승종목</div>
                  <div className="text-xs text-muted-foreground">
                    {currentMarket === 'domestic' ? '1,234개' : '2,856개'}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <TrendingDown className="w-4 h-4 text-blue-500" />
                <div>
                  <div className="font-medium">하락종목</div>
                  <div className="text-xs text-muted-foreground">
                    {currentMarket === 'domestic' ? '987개' : '1,743개'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}

export default MarketIndicator;