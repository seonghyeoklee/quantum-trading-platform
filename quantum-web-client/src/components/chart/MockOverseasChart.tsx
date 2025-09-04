'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  RefreshCw, 
  TrendingUp, 
  TrendingDown, 
  Wifi, 
  WifiOff,
  Activity,
  Clock,
  BarChart3
} from 'lucide-react';

interface MockOverseasChartProps {
  symbol: string;
  stockName?: string;
  height?: number;
  className?: string;
}

export default function MockOverseasChart({ 
  symbol, 
  stockName,
  height = 400,
  className = '' 
}: MockOverseasChartProps) {
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [priceChange, setPriceChange] = useState<number>(0);
  const [priceChangePercent, setPriceChangePercent] = useState<number>(0);
  const [lastUpdateTime, setLastUpdateTime] = useState<string>('');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [volume, setVolume] = useState<string>('0');

  // 가격 업데이트 시뮬레이션
  useEffect(() => {
    const symbolName = symbol.replace('RBAQ', '');
    const basePrices: { [key: string]: number } = {
      'AAPL': 180.50, 'MSFT': 378.85, 'GOOGL': 139.69, 'AMZN': 146.09,
      'TSLA': 248.50, 'META': 338.54, 'NVDA': 875.30, 'NFLX': 432.84
    };
    
    const basePrice = basePrices[symbolName] || 100;
    setCurrentPrice(basePrice);

    // 연결 시뮬레이션
    const connectTimeout = setTimeout(() => {
      setIsConnected(true);
    }, 1000);

    // 실시간 업데이트 시뮬레이션
    const updateInterval = setInterval(() => {
      const change = (Math.random() - 0.5) * 0.02; // ±1% 변동
      const newPrice = basePrice * (1 + change);
      const changeAmount = newPrice - basePrice;
      const changePercent = (changeAmount / basePrice) * 100;
      
      setCurrentPrice(newPrice);
      setPriceChange(changeAmount);
      setPriceChangePercent(changePercent);
      setLastUpdateTime(new Date().toLocaleTimeString());
      setVolume((Math.random() * 50000000 + 5000000).toFixed(0));
    }, 2000);

    return () => {
      clearTimeout(connectTimeout);
      clearInterval(updateInterval);
    };
  }, [symbol]);

  const isPriceUp = priceChange > 0;
  const isPriceDown = priceChange < 0;
  const priceColor = isPriceUp ? 'text-red-600' : isPriceDown ? 'text-blue-600' : 'text-gray-500';
  const ConnectionIcon = isConnected ? Wifi : WifiOff;
  const connectionColor = isConnected ? 'text-green-500' : 'text-red-500';

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 연결 상태 및 가격 정보 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <ConnectionIcon className={`w-4 h-4 ${connectionColor}`} />
            <span className={`text-sm ${connectionColor}`}>
              {isConnected ? 'Mock Connected' : 'Connecting...'}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          {currentPrice > 0 && (
            <>
              <div className="text-right">
                <div className="text-xl font-bold">${currentPrice.toFixed(2)}</div>
                <div className={`text-sm flex items-center ${priceColor}`}>
                  {isPriceUp && <TrendingUp className="w-3 h-3 mr-1" />}
                  {isPriceDown && <TrendingDown className="w-3 h-3 mr-1" />}
                  {priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)} 
                  ({priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                </div>
              </div>
              
            </>
          )}
        </div>
      </div>

      {/* 모의 차트 영역 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              {stockName || symbol.replace('RBAQ', '')} Chart
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              Mock Data
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div 
            className="w-full border border-dashed border-border rounded-lg flex items-center justify-center bg-muted/20"
            style={{ height: `${height}px` }}
          >
            <div className="text-center space-y-4">
              <BarChart3 className="w-16 h-16 mx-auto text-muted-foreground opacity-50" />
              <div>
                <h3 className="text-lg font-semibold mb-2">Mock Overseas Chart</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  해외 주식 차트 데이터를 시뮬레이션합니다
                </p>
              </div>
            </div>
          </div>
          
          {/* 모의 데이터 표시 */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">현재가</span>
              <div className="font-medium">${currentPrice.toFixed(2)}</div>
            </div>
            <div>
              <span className="text-muted-foreground">변동</span>
              <div className={`font-medium ${priceColor}`}>
                {priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)}
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">변동률</span>
              <div className={`font-medium ${priceColor}`}>
                {priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%
              </div>
            </div>
            <div>
              <span className="text-muted-foreground">거래량</span>
              <div className="font-medium">{parseInt(volume).toLocaleString()}</div>
            </div>
          </div>
          
          {/* 푸터 정보 */}
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-4 border-t border-border mt-4">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3" />
                Mock Simulation
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              {lastUpdateTime && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {lastUpdateTime}
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

    </div>
  );
}