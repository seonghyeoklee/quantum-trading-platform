'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { TrendingUp, TrendingDown, Settings, BarChart } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

const Chart = dynamic(() => import('react-apexcharts'), { 
  ssr: false,
  loading: () => <div className="h-96 flex items-center justify-center">Loading chart...</div>
});

interface TechnicalIndicatorChartProps {
  symbol: string;
  symbolName?: string;
  timeframe?: '1m' | '5m' | '15m' | '1h' | '1d';
}

interface IndicatorData {
  timestamp: number;
  ma5?: number;
  ma20?: number;
  ma60?: number;
  ema12?: number;
  ema26?: number;
  macd?: number;
  signal?: number;
  histogram?: number;
  rsi?: number;
  stochK?: number;
  stochD?: number;
  upperBB?: number;
  lowerBB?: number;
  middleBB?: number;
}

interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface IndicatorConfig {
  movingAverages: {
    ma5: boolean;
    ma20: boolean;
    ma60: boolean;
    ema12: boolean;
    ema26: boolean;
  };
  oscillators: {
    macd: boolean;
    rsi: boolean;
    stochastic: boolean;
  };
  bands: {
    bollinger: boolean;
  };
}

export const TechnicalIndicatorChart: React.FC<TechnicalIndicatorChartProps> = ({
  symbol,
  symbolName,
  timeframe = '1d'
}) => {
  const [candleData, setCandleData] = useState<CandleData[]>([]);
  const [indicatorData, setIndicatorData] = useState<IndicatorData[]>([]);
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<IndicatorConfig>({
    movingAverages: {
      ma5: true,
      ma20: true,
      ma60: false,
      ema12: false,
      ema26: false,
    },
    oscillators: {
      macd: true,
      rsi: true,
      stochastic: false,
    },
    bands: {
      bollinger: false,
    }
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // 캔들 데이터와 기술적 지표 데이터 로드
        const [candleResponse, indicatorResponse] = await Promise.all([
          apiClient.getChartData(symbol, timeframe),
          apiClient.getTechnicalIndicators(symbol, timeframe)
        ]);

        setCandleData(candleResponse.data || []);
        setIndicatorData(indicatorResponse.indicators || []);
        
      } catch (error) {
        console.error('Failed to load technical data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [symbol, timeframe]);

  // 메인 차트 (캔들스틱 + 이동평균 + 볼린저 밴드)
  const mainChartOptions = {
    chart: {
      type: 'candlestick',
      height: 400,
      toolbar: {
        show: true,
        tools: {
          download: true,
          selection: true,
          zoom: true,
          pan: true,
        }
      },
      zoom: {
        enabled: true,
        type: 'x',
      }
    },
    title: {
      text: `${symbolName || symbol} - Technical Analysis`,
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
    stroke: {
      width: [1, 2, 2, 2, 2, 2, 1, 1] // 캔들, MA선들, 볼린저밴드
    },
    legend: {
      show: true,
      position: 'top',
      horizontalAlign: 'left'
    }
  };

  // 메인 차트 시리즈 (캔들 + 이동평균 + 볼린저밴드)
  const mainChartSeries = [
    {
      name: 'Candlestick',
      type: 'candlestick',
      data: candleData.map(item => ({
        x: item.timestamp,
        y: [item.open, item.high, item.low, item.close]
      }))
    },
    ...(config.movingAverages.ma5 ? [{
      name: 'MA5',
      type: 'line',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.ma5
      })).filter(item => item.y !== undefined)
    }] : []),
    ...(config.movingAverages.ma20 ? [{
      name: 'MA20',
      type: 'line',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.ma20
      })).filter(item => item.y !== undefined)
    }] : []),
    ...(config.movingAverages.ma60 ? [{
      name: 'MA60',
      type: 'line',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.ma60
      })).filter(item => item.y !== undefined)
    }] : []),
    ...(config.movingAverages.ema12 ? [{
      name: 'EMA12',
      type: 'line',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.ema12
      })).filter(item => item.y !== undefined)
    }] : []),
    ...(config.movingAverages.ema26 ? [{
      name: 'EMA26',
      type: 'line',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.ema26
      })).filter(item => item.y !== undefined)
    }] : []),
    ...(config.bands.bollinger ? [
      {
        name: 'Upper BB',
        type: 'line',
        data: indicatorData.map(item => ({
          x: item.timestamp,
          y: item.upperBB
        })).filter(item => item.y !== undefined)
      },
      {
        name: 'Lower BB',
        type: 'line',
        data: indicatorData.map(item => ({
          x: item.timestamp,
          y: item.lowerBB
        })).filter(item => item.y !== undefined)
      },
    ] : [])
  ];

  // MACD 차트 옵션
  const macdChartOptions = {
    chart: {
      type: 'line',
      height: 200,
      toolbar: { show: false },
    },
    title: {
      text: 'MACD',
      align: 'left',
      style: { fontSize: '14px' }
    },
    xaxis: {
      type: 'datetime',
      labels: { show: false }
    },
    yaxis: {
      labels: {
        formatter: (value: number) => value.toFixed(2)
      }
    },
    stroke: {
      width: [2, 2, 1]
    },
    legend: {
      show: true,
      position: 'top',
      fontSize: '12px'
    },
    colors: ['#2563EB', '#DC2626', '#10B981']
  };

  const macdChartSeries = config.oscillators.macd ? [
    {
      name: 'MACD',
      type: 'line',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.macd
      })).filter(item => item.y !== undefined)
    },
    {
      name: 'Signal',
      type: 'line',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.signal
      })).filter(item => item.y !== undefined)
    },
    {
      name: 'Histogram',
      type: 'column',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.histogram
      })).filter(item => item.y !== undefined)
    }
  ] : [];

  // RSI 차트 옵션
  const rsiChartOptions = {
    chart: {
      type: 'line',
      height: 150,
      toolbar: { show: false },
    },
    title: {
      text: 'RSI',
      align: 'left',
      style: { fontSize: '14px' }
    },
    xaxis: {
      type: 'datetime',
      labels: { show: false }
    },
    yaxis: {
      min: 0,
      max: 100,
      tickAmount: 4,
      labels: {
        formatter: (value: number) => value.toFixed(0)
      }
    },
    stroke: {
      width: 2
    },
    annotations: {
      yaxis: [
        {
          y: 70,
          borderColor: '#EF4444',
          borderWidth: 1,
          strokeDashArray: 2,
          label: {
            text: 'Overbought (70)',
            position: 'left',
            style: { fontSize: '10px' }
          }
        },
        {
          y: 30,
          borderColor: '#10B981',
          borderWidth: 1,
          strokeDashArray: 2,
          label: {
            text: 'Oversold (30)',
            position: 'left',
            style: { fontSize: '10px' }
          }
        }
      ]
    },
    colors: ['#8B5CF6']
  };

  const rsiChartSeries = config.oscillators.rsi ? [{
    name: 'RSI',
    data: indicatorData.map(item => ({
      x: item.timestamp,
      y: item.rsi
    })).filter(item => item.y !== undefined)
  }] : [];

  // Stochastic 차트 옵션
  const stochChartOptions = {
    chart: {
      type: 'line',
      height: 150,
      toolbar: { show: false },
    },
    title: {
      text: 'Stochastic',
      align: 'left',
      style: { fontSize: '14px' }
    },
    xaxis: {
      type: 'datetime'
    },
    yaxis: {
      min: 0,
      max: 100,
      tickAmount: 4,
      labels: {
        formatter: (value: number) => value.toFixed(0)
      }
    },
    stroke: {
      width: [2, 2]
    },
    annotations: {
      yaxis: [
        {
          y: 80,
          borderColor: '#EF4444',
          borderWidth: 1,
          strokeDashArray: 2,
        },
        {
          y: 20,
          borderColor: '#10B981',
          borderWidth: 1,
          strokeDashArray: 2,
        }
      ]
    },
    colors: ['#F59E0B', '#EC4899']
  };

  const stochChartSeries = config.oscillators.stochastic ? [
    {
      name: '%K',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.stochK
      })).filter(item => item.y !== undefined)
    },
    {
      name: '%D',
      data: indicatorData.map(item => ({
        x: item.timestamp,
        y: item.stochD
      })).filter(item => item.y !== undefined)
    }
  ] : [];

  const updateConfig = (category: keyof IndicatorConfig, key: string, value: boolean) => {
    setConfig(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      {/* 메인 차트 */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">기술적 분석</CardTitle>
            <div className="flex items-center gap-2">
              <Select value={timeframe} onValueChange={() => {}}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1m">1분</SelectItem>
                  <SelectItem value="5m">5분</SelectItem>
                  <SelectItem value="15m">15분</SelectItem>
                  <SelectItem value="1h">1시간</SelectItem>
                  <SelectItem value="1d">1일</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 메인 차트 */}
          <Chart
            options={mainChartOptions}
            series={mainChartSeries}
            type="candlestick"
            height={400}
          />

          {/* MACD 차트 */}
          {config.oscillators.macd && (
            <Chart
              options={macdChartOptions}
              series={macdChartSeries}
              type="line"
              height={200}
            />
          )}

          {/* RSI 차트 */}
          {config.oscillators.rsi && (
            <Chart
              options={rsiChartOptions}
              series={rsiChartSeries}
              type="line"
              height={150}
            />
          )}

          {/* Stochastic 차트 */}
          {config.oscillators.stochastic && (
            <Chart
              options={stochChartOptions}
              series={stochChartSeries}
              type="line"
              height={150}
            />
          )}
        </CardContent>
      </Card>

      {/* 설정 패널 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Settings size={16} />
            지표 설정
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 이동평균선 */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">이동평균선</h4>
            <div className="space-y-2">
              {Object.entries(config.movingAverages).map(([key, value]) => (
                <div key={key} className="flex items-center space-x-2">
                  <Checkbox
                    id={key}
                    checked={value}
                    onCheckedChange={(checked) => 
                      updateConfig('movingAverages', key, checked as boolean)
                    }
                  />
                  <label htmlFor={key} className="text-sm font-medium">
                    {key.toUpperCase()}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* 오실레이터 */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">오실레이터</h4>
            <div className="space-y-2">
              {Object.entries(config.oscillators).map(([key, value]) => (
                <div key={key} className="flex items-center space-x-2">
                  <Checkbox
                    id={key}
                    checked={value}
                    onCheckedChange={(checked) => 
                      updateConfig('oscillators', key, checked as boolean)
                    }
                  />
                  <label htmlFor={key} className="text-sm font-medium">
                    {key.toUpperCase()}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* 밴드/채널 */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">밴드</h4>
            <div className="space-y-2">
              {Object.entries(config.bands).map(([key, value]) => (
                <div key={key} className="flex items-center space-x-2">
                  <Checkbox
                    id={key}
                    checked={value}
                    onCheckedChange={(checked) => 
                      updateConfig('bands', key, checked as boolean)
                    }
                  />
                  <label htmlFor={key} className="text-sm font-medium">
                    {key === 'bollinger' ? '볼린저밴드' : key.toUpperCase()}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* 지표 요약 */}
          <div className="space-y-3">
            <h4 className="font-semibold text-sm">현재 지표 값</h4>
            <div className="space-y-2 text-xs">
              {indicatorData.length > 0 && (
                <>
                  {config.oscillators.rsi && (
                    <div className="flex justify-between">
                      <span>RSI:</span>
                      <span className={`font-semibold ${
                        (indicatorData[indicatorData.length - 1]?.rsi || 0) > 70 ? 'text-red-600' :
                        (indicatorData[indicatorData.length - 1]?.rsi || 0) < 30 ? 'text-green-600' : ''
                      }`}>
                        {indicatorData[indicatorData.length - 1]?.rsi?.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {config.oscillators.macd && (
                    <div className="flex justify-between">
                      <span>MACD:</span>
                      <span className="font-semibold">
                        {indicatorData[indicatorData.length - 1]?.macd?.toFixed(2)}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TechnicalIndicatorChart;