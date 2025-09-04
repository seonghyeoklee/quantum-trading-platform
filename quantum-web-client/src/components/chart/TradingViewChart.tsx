'use client';

import { useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel } from '@/components/ui/dropdown-menu';
import { 
  BarChart3, 
  TrendingUp, 
  Settings, 
  Maximize2, 
  Minimize2,
  Clock,
  LineChart
} from 'lucide-react';

interface TradingViewChartProps {
  symbol: string;
  market: 'domestic' | 'overseas';
  className?: string;
  key?: string; // 리렌더링 트리거용
  onFullscreenToggle?: () => void; // 외부에서 전체화면 상태 관리
}

// Mock 차트 데이터 생성 함수
const generateMockData = (symbol: string, timeframe: string) => {
  const data = [];
  let basePrice = symbol === '005930' ? 70000 : 150; // 삼성전자 vs Apple
  const now = new Date();
  
  // 시간봉에 따른 설정
  const timeSettings = {
    '1m': { count: 500, increment: 60 * 1000, volatility: 0.01 }, // 1분봉
    '5m': { count: 300, increment: 5 * 60 * 1000, volatility: 0.02 }, // 5분봉
    '15m': { count: 200, increment: 15 * 60 * 1000, volatility: 0.025 }, // 15분봉
    '1h': { count: 168, increment: 60 * 60 * 1000, volatility: 0.03 }, // 1시간봉
    '1D': { count: 100, increment: 24 * 60 * 60 * 1000, volatility: 0.05 }, // 일봉
    '1W': { count: 52, increment: 7 * 24 * 60 * 60 * 1000, volatility: 0.08 }, // 주봉
  };
  
  const setting = timeSettings[timeframe as keyof typeof timeSettings] || timeSettings['1D'];
  
  for (let i = setting.count; i >= 0; i--) {
    const date = new Date(now.getTime() - (i * setting.increment));
    
    // 시간봉에 따른 변동성 조정
    const change = (Math.random() - 0.5) * setting.volatility;
    const open = basePrice;
    const close = basePrice * (1 + change);
    const high = Math.max(open, close) * (1 + Math.random() * 0.03);
    const low = Math.min(open, close) * (1 - Math.random() * 0.03);
    
    data.push({
      time: Math.floor(date.getTime() / 1000),
      open: open,
      high: high,
      low: low,
      close: close,
    });
    
    basePrice = close; // 다음 봉의 시작점
  }
  
  return data;
};

export default function TradingViewChart({ symbol, market, className, onFullscreenToggle }: TradingViewChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chart = useRef<any>(null);
  const series = useRef<any>(null);
  const { resolvedTheme } = useTheme();
  
  const [timeframe, setTimeframe] = useState('1D');
  const [chartType, setChartType] = useState('candlestick');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [mockData, setMockData] = useState(() => generateMockData(symbol, timeframe));
  const [crosshairData, setCrosshairData] = useState<{
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
  } | null>(null);
  const [showGrid, setShowGrid] = useState(true);
  const [showCrosshair, setShowCrosshair] = useState(true);

  useEffect(() => {
    const initChart = async () => {
      if (!chartContainerRef.current) return;
      
      try {
        const { createChart, ColorType, CandlestickSeries } = await import('lightweight-charts');
        
        // 기존 차트 제거
        if (chart.current) {
          chart.current.remove();
        }

        const isDark = resolvedTheme === 'dark';
        
        // TradingView 스타일 차트 생성
        chart.current = createChart(chartContainerRef.current, {
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
          layout: {
            background: {
              type: ColorType.Solid,
              color: isDark ? '#131722' : '#ffffff'
            },
            textColor: isDark ? '#d1d4dc' : '#191919',
            fontSize: 12,
            fontFamily: '-apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif',
          },
          grid: {
            vertLines: { 
              color: showGrid ? (isDark ? '#2a2e39' : '#f0f3fa') : 'transparent',
              style: showGrid ? 0 : 4,
            },
            horzLines: { 
              color: showGrid ? (isDark ? '#2a2e39' : '#f0f3fa') : 'transparent',
              style: showGrid ? 0 : 4,
            },
          },
          crosshair: {
            mode: showCrosshair ? 1 : 0,
            vertLine: {
              width: 1,
              color: isDark ? '#758696' : '#9598a1',
              style: 3,
              visible: showCrosshair,
            },
            horzLine: {
              width: 1,
              color: isDark ? '#758696' : '#9598a1',
              style: 3,
              visible: showCrosshair,
            },
          },
          rightPriceScale: {
            borderColor: isDark ? '#2a2e39' : '#f0f3fa',
            autoScale: true,
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          },
          timeScale: {
            borderColor: isDark ? '#2a2e39' : '#f0f3fa',
            timeVisible: true,
            secondsVisible: false,
          },
          handleScroll: {
            mouseWheel: true,
            pressedMouseMove: true,
          },
          handleScale: {
            axisPressedMouseMove: true,
            mouseWheel: true,
            pinch: true,
          },
        });

        // 시리즈 타입에 따른 차트 추가
        if (chartType === 'candlestick') {
          series.current = chart.current.addSeries(CandlestickSeries, {
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
          });
        } else {
          const { LineSeries } = await import('lightweight-charts');
          series.current = chart.current.addSeries(LineSeries, {
            color: '#2196F3',
            lineWidth: 2,
          });
        }

        // Mock 데이터 설정
        const chartData = chartType === 'candlestick' 
          ? mockData 
          : mockData.map(item => ({ time: item.time, value: item.close }));
        
        series.current.setData(chartData);
        chart.current.timeScale().fitContent();

        // Crosshair 이벤트 리스너 추가
        chart.current.subscribeCrosshairMove((param: any) => {
          if (param.time && param.point && series.current) {
            const price = param.seriesData.get(series.current);
            if (price) {
              const date = new Date(param.time * 1000);
              
              if (chartType === 'candlestick' && price.open !== undefined) {
                setCrosshairData({
                  time: date.toLocaleString('ko-KR', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                  }),
                  open: price.open,
                  high: price.high,
                  low: price.low,
                  close: price.close
                });
              } else if (chartType === 'line' && price.value !== undefined) {
                // 라인차트의 경우 해당 시점의 원본 데이터를 찾아서 OHLC 표시
                const originalData = mockData.find(item => item.time === param.time);
                if (originalData) {
                  setCrosshairData({
                    time: date.toLocaleString('ko-KR', {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    }),
                    open: originalData.open,
                    high: originalData.high,
                    low: originalData.low,
                    close: originalData.close
                  });
                }
              }
            }
          } else {
            setCrosshairData(null);
          }
        });

        // 리사이즈 핸들러
        const handleResize = () => {
          if (chart.current && chartContainerRef.current) {
            chart.current.applyOptions({ 
              width: chartContainerRef.current.clientWidth,
              height: chartContainerRef.current.clientHeight,
            });
          }
        };

        // ResizeObserver로 컨테이너 크기 변화 감지
        const resizeObserver = new ResizeObserver(() => {
          handleResize();
        });
        
        if (chartContainerRef.current) {
          resizeObserver.observe(chartContainerRef.current);
        }

        window.addEventListener('resize', handleResize);
        
        return () => {
          window.removeEventListener('resize', handleResize);
          resizeObserver.disconnect();
        };

      } catch (error) {
        console.error('TradingView 차트 생성 오류:', error);
      }
    };

    initChart();

    return () => {
      if (chart.current) {
        chart.current.remove();
        chart.current = null;
        series.current = null;
      }
    };
  }, [resolvedTheme, symbol, mockData, chartType]);

  const toggleFullscreen = () => {
    if (onFullscreenToggle) {
      onFullscreenToggle();
    } else {
      setIsFullscreen(!isFullscreen);
    }
  };

  // ESC 키로 전체화면 종료
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isFullscreen) {
        toggleFullscreen();
      }
    };

    if (isFullscreen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isFullscreen]);

  // 차트 설정 업데이트
  const updateChartSettings = () => {
    if (chart.current) {
      const isDark = resolvedTheme === 'dark';
      chart.current.applyOptions({
        grid: {
          vertLines: { 
            color: showGrid ? (isDark ? '#2a2e39' : '#f0f3fa') : 'transparent',
            style: showGrid ? 0 : 4,
          },
          horzLines: { 
            color: showGrid ? (isDark ? '#2a2e39' : '#f0f3fa') : 'transparent',
            style: showGrid ? 0 : 4,
          },
        },
        crosshair: {
          mode: showCrosshair ? 1 : 0,
          vertLine: {
            visible: showCrosshair,
          },
          horzLine: {
            visible: showCrosshair,
          },
        },
      });
    }
  };

  // 설정 변경시 차트 업데이트
  useEffect(() => {
    updateChartSettings();
  }, [showGrid, showCrosshair, resolvedTheme]);

  // 시간봉 변경시 데이터 업데이트
  useEffect(() => {
    const newData = generateMockData(symbol, timeframe);
    setMockData(newData);
  }, [symbol, timeframe]);

  return (
    <div className={`relative ${className}`}>
      {/* 차트 툴바 */}
      <div className="absolute top-3 left-3 z-10 flex items-center space-x-2">
        <div className="bg-background/80 backdrop-blur-sm border border-border rounded-md px-2 py-1">
          <span className="text-sm font-medium">{symbol}</span>
        </div>
        
        <Select value={timeframe} onValueChange={setTimeframe}>
          <SelectTrigger className="w-16 h-8 bg-background/80 backdrop-blur-sm text-xs border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1m">1분</SelectItem>
            <SelectItem value="5m">5분</SelectItem>
            <SelectItem value="15m">15분</SelectItem>
            <SelectItem value="1h">1시간</SelectItem>
            <SelectItem value="1D">1일</SelectItem>
            <SelectItem value="1W">1주</SelectItem>
          </SelectContent>
        </Select>

        <div className="bg-background/80 backdrop-blur-sm border border-border rounded-md px-2 py-1">
          <span className="text-xs font-medium">{chartType === 'candlestick' ? '캔들' : '라인'}</span>
        </div>
      </div>

      {/* 우측 상단 컨트롤 */}
      <div className="absolute top-3 right-3 z-10 flex items-center space-x-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm"
            >
              <Settings className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel>차트 설정</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setShowGrid(!showGrid)}>
              <div className="flex items-center justify-between w-full">
                <span>그리드 표시</span>
                <div className={`w-3 h-3 rounded-sm ${showGrid ? 'bg-primary' : 'bg-muted'}`} />
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setShowCrosshair(!showCrosshair)}>
              <div className="flex items-center justify-between w-full">
                <span>십자선 표시</span>
                <div className={`w-3 h-3 rounded-sm ${showCrosshair ? 'bg-primary' : 'bg-muted'}`} />
              </div>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setChartType(chartType === 'candlestick' ? 'line' : 'candlestick')}>
              <div className="flex items-center justify-between w-full">
                <span>{chartType === 'candlestick' ? '라인차트로 전환' : '캔들차트로 전환'}</span>
                <LineChart className="w-4 h-4" />
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleFullscreen}
          className="h-8 w-8 p-0 bg-background/80 backdrop-blur-sm"
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </Button>
      </div>

      {/* 차트 컨테이너 */}
      <div 
        ref={chartContainerRef} 
        className={`w-full h-full rounded-lg border border-border ${
          isFullscreen ? 'fixed inset-0 z-50 rounded-none' : ''
        }`}
        style={{ 
          minHeight: isFullscreen ? '100vh' : '400px',
          background: resolvedTheme === 'dark' ? '#131722' : '#ffffff' 
        }}
      />

      {/* 하단 정보 - Crosshair 데이터 표시 */}
      {crosshairData && (
        <div className="absolute bottom-3 left-3 z-10">
          <div className="bg-background/90 backdrop-blur-sm border border-border rounded-md px-3 py-2 shadow-lg">
            <div className="text-xs text-muted-foreground mb-1">{crosshairData.time}</div>
            <div className="flex items-center space-x-4 text-sm">
              <span className="text-muted-foreground">O</span>
              <span className="font-medium">{crosshairData.open.toFixed(2)}</span>
              <span className="text-muted-foreground">H</span>
              <span className="font-medium">{crosshairData.high.toFixed(2)}</span>
              <span className="text-muted-foreground">L</span>
              <span className="font-medium">{crosshairData.low.toFixed(2)}</span>
              <span className="text-muted-foreground">C</span>
              <span className={`font-medium ${
                crosshairData.close >= crosshairData.open 
                  ? 'text-green-500' 
                  : 'text-red-500'
              }`}>
                {crosshairData.close.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}