'use client';

import React, { useEffect, useState, useRef } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, TrendingDown, Activity, BarChart3, LineChart } from 'lucide-react';
import { useWebSocket } from '@/lib/websocket';
import { apiClient } from '@/lib/api-client';

// ApexCharts를 동적 임포트로 로드 (SSR 이슈 방지)
const Chart = dynamic(() => import('react-apexcharts'), { 
  ssr: false,
  loading: () => <div className="h-96 flex items-center justify-center">Loading chart...</div>
});

interface StockChartProps {
  symbol: string;
  symbolName?: string;
  height?: number;
  showOrderBook?: boolean;
  showTrades?: boolean;
}

interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface QuoteData {
  currentPrice: number;
  changeAmount: number;
  changePercent: number;
  bidPrice: number;
  askPrice: number;
  bidSize: number;
  askSize: number;
  volume: number;
  high: number;
  low: number;
  open: number;
}

interface TradeData {
  price: number;
  size: number;
  side: 'BUY' | 'SELL';
  tradeTime: string;
}

export const StockChart: React.FC<StockChartProps> = ({
  symbol,
  symbolName,
  height = 400,
  showOrderBook = true,
  showTrades = true,
}) => {
  const [candleData, setCandleData] = useState<CandleData[]>([]);
  const [currentQuote, setCurrentQuote] = useState<QuoteData | null>(null);
  const [recentTrades, setRecentTrades] = useState<TradeData[]>([]);
  const [chartType, setChartType] = useState<'candle' | 'line'>('candle');
  const [timeframe, setTimeframe] = useState<'1m' | '5m' | '15m' | '1h' | '1d'>('5m');
  const [loading, setLoading] = useState(true);

  const { 
    subscribeToQuotes, 
    subscribeToTrades, 
    unsubscribeFromQuotes, 
    unsubscribeFromTrades,
    isConnected 
  } = useWebSocket();

  // 초기 차트 데이터 로드
  useEffect(() => {
    const loadChartData = async () => {
      try {
        setLoading(true);
        const response = await apiClient.getChartData(symbol, timeframe);
        setCandleData(response.data || []);
      } catch (error) {
        console.error('Failed to load chart data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadChartData();
  }, [symbol, timeframe]);

  // WebSocket 실시간 데이터 구독
  useEffect(() => {
    if (!isConnected) return;

    // 시세 구독
    const quoteUnsubscribe = subscribeToQuotes(symbol, (data) => {
      if (data.type === 'QUOTE') {
        setCurrentQuote(data.data);
        
        // 현재 캔들 업데이트 (실시간 가격 반영)
        setCandleData(prev => {
          if (prev.length === 0) return prev;
          
          const updatedData = [...prev];
          const lastCandle = updatedData[updatedData.length - 1];
          const currentPrice = data.data.currentPrice;
          
          // 마지막 캔들의 close, high, low 업데이트
          updatedData[updatedData.length - 1] = {
            ...lastCandle,
            close: currentPrice,
            high: Math.max(lastCandle.high, currentPrice),
            low: Math.min(lastCandle.low, currentPrice),
            volume: data.data.volume,
          };
          
          return updatedData;
        });
      }
    });

    // 거래 내역 구독 (옵션)
    let tradeUnsubscribe: (() => void) | undefined;
    if (showTrades) {
      tradeUnsubscribe = subscribeToTrades(symbol, (data) => {
        if (data.type === 'TRADE') {
          setRecentTrades(prev => [data.data, ...prev.slice(0, 19)]); // 최근 20개만 유지
        }
      });
    }

    return () => {
      quoteUnsubscribe();
      if (tradeUnsubscribe) tradeUnsubscribe();
    };
  }, [symbol, isConnected, subscribeToQuotes, subscribeToTrades, showTrades]);

  // ApexCharts 설정
  const chartOptions = {
    chart: {
      type: chartType === 'candle' ? 'candlestick' : 'line',
      height: height,
      toolbar: {
        show: true,
        tools: {
          download: true,
          selection: true,
          zoom: true,
          zoomin: true,
          zoomout: true,
          pan: true,
        }
      },
      zoom: {
        enabled: true,
        type: 'x',
      },
      animations: {
        enabled: true,
        easing: 'easeinout',
        speed: 300,
      }
    },
    title: {
      text: `${symbolName || symbol} - ${timeframe}`,
      align: 'left'
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeFormatter: {
          year: 'yyyy',
          month: 'MMM \'yy',
          day: 'dd MMM',
          hour: 'HH:mm',
          minute: 'HH:mm',
        }
      }
    },
    yaxis: {
      tooltip: {
        enabled: true
      },
      labels: {
        formatter: (value: number) => value.toLocaleString()
      }
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: '#00B746',
          downward: '#EF403C'
        },
        wick: {
          useFillColor: true
        }
      }
    },
    grid: {
      borderColor: '#e7e7e7',
      row: {
        colors: ['#f3f3f3', 'transparent'],
        opacity: 0.5
      }
    },
    tooltip: {
      shared: true,
      custom: function({ seriesIndex, dataPointIndex, w }: any) {
        const data = w.globals.initialSeries[seriesIndex].data[dataPointIndex];
        if (!data) return '';
        
        const date = new Date(data.x);
        return `<div class="p-3">
          <div class="font-semibold">${date.toLocaleString()}</div>
          <div class="grid grid-cols-2 gap-2 mt-2 text-sm">
            <div>Open: ${data.y[0]?.toLocaleString()}</div>
            <div>High: ${data.y[1]?.toLocaleString()}</div>
            <div>Low: ${data.y[2]?.toLocaleString()}</div>
            <div>Close: ${data.y[3]?.toLocaleString()}</div>
          </div>
        </div>`;
      }
    }
  };

  const chartSeries = chartType === 'candle' 
    ? [{
        name: 'Candlestick',
        data: candleData.map(item => ({
          x: item.timestamp,
          y: [item.open, item.high, item.low, item.close]
        }))
      }]
    : [{
        name: 'Price',
        data: candleData.map(item => ({
          x: item.timestamp,
          y: item.close
        }))
      }];

  const formatPrice = (price: number) => {
    return price.toLocaleString('ko-KR');
  };

  const formatChange = (change: number, changePercent: number) => {
    const isPositive = change >= 0;
    const sign = isPositive ? '+' : '';
    return (
      <div className={`flex items-center gap-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
        <span>{sign}{formatPrice(change)} ({sign}{changePercent.toFixed(2)}%)</span>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* 현재 시세 정보 */}
      {currentQuote && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{symbolName || symbol}</CardTitle>
              <Badge variant={isConnected ? "default" : "secondary"}>
                <Activity size={12} className="mr-1" />
                {isConnected ? "실시간" : "연결 중"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">현재가</p>
                <p className="text-2xl font-bold">{formatPrice(currentQuote.currentPrice)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">등락</p>
                {formatChange(currentQuote.changeAmount, currentQuote.changePercent)}
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">거래량</p>
                <p className="text-lg font-semibold">{currentQuote.volume.toLocaleString()}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">고가/저가</p>
                <p className="text-sm">
                  <span className="text-red-600">{formatPrice(currentQuote.high)}</span>
                  {' / '}
                  <span className="text-blue-600">{formatPrice(currentQuote.low)}</span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* 메인 차트 */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">주가 차트</CardTitle>
              <div className="flex items-center gap-2">
                {/* 차트 타입 선택 */}
                <div className="flex rounded-lg border p-1">
                  <Button
                    variant={chartType === 'candle' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setChartType('candle')}
                    className="h-8"
                  >
                    <BarChart3 size={14} className="mr-1" />
                    캔들
                  </Button>
                  <Button
                    variant={chartType === 'line' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setChartType('line')}
                    className="h-8"
                  >
                    <LineChart size={14} className="mr-1" />
                    라인
                  </Button>
                </div>
                
                {/* 시간 단위 선택 */}
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value as any)}
                  className="px-3 py-1 border rounded-md text-sm"
                >
                  <option value="1m">1분</option>
                  <option value="5m">5분</option>
                  <option value="15m">15분</option>
                  <option value="1h">1시간</option>
                  <option value="1d">1일</option>
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-96 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <Chart
                options={chartOptions}
                series={chartSeries}
                type={chartType === 'candle' ? 'candlestick' : 'line'}
                height={height}
              />
            )}
          </CardContent>
        </Card>

        {/* 사이드 패널 */}
        <div className="space-y-4">
          {/* 호가 정보 */}
          {showOrderBook && currentQuote && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">호가 정보</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between items-center p-2 bg-red-50 rounded">
                  <span className="text-sm">매도호가</span>
                  <div className="text-right">
                    <div className="text-red-600 font-semibold">{formatPrice(currentQuote.askPrice)}</div>
                    <div className="text-xs text-muted-foreground">{currentQuote.askSize.toLocaleString()}</div>
                  </div>
                </div>
                <div className="flex justify-between items-center p-2 bg-blue-50 rounded">
                  <span className="text-sm">매수호가</span>
                  <div className="text-right">
                    <div className="text-blue-600 font-semibold">{formatPrice(currentQuote.bidPrice)}</div>
                    <div className="text-xs text-muted-foreground">{currentQuote.bidSize.toLocaleString()}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 최근 거래 내역 */}
          {showTrades && recentTrades.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">최근 거래</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 max-h-80 overflow-y-auto">
                  {recentTrades.slice(0, 10).map((trade, index) => (
                    <div key={index} className="flex justify-between items-center py-1 text-sm border-b last:border-b-0">
                      <div className={`px-2 py-1 rounded text-xs font-semibold ${
                        trade.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {trade.side}
                      </div>
                      <div className="text-right">
                        <div className="font-semibold">{formatPrice(trade.price)}</div>
                        <div className="text-xs text-muted-foreground">{trade.size.toLocaleString()}</div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(trade.tradeTime).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default StockChart;