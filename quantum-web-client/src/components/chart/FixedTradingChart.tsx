'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";

export function FixedTradingChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Dynamic import to prevent SSR issues
    import('lightweight-charts').then((LightweightCharts) => {
      if (!chartContainerRef.current) return;

      try {
        console.log('📊 LightweightCharts 로딩됨:', LightweightCharts);
        
        // Create chart with v5 API
        const chart = LightweightCharts.createChart(chartContainerRef.current, {
          width: chartContainerRef.current.clientWidth,
          height: 400,
          layout: {
            background: { color: 'transparent' },
            textColor: '#333',
          },
          grid: {
            vertLines: { color: '#e1e1e1' },
            horzLines: { color: '#e1e1e1' },
          },
          crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
          },
          rightPriceScale: {
            borderColor: '#cccccc',
          },
          timeScale: {
            borderColor: '#cccccc',
            timeVisible: true,
            secondsVisible: false,
          },
        });

        console.log('✅ Chart 생성 성공:', chart);
        chartRef.current = chart;

        // Add candlestick series with v5 API
        const candlestickSeries = chart.addCandlestickSeries({
          upColor: '#FF0000',      // Red for up (Korean style)
          downColor: '#0000FF',    // Blue for down (Korean style)
          borderUpColor: '#FF0000',
          borderDownColor: '#0000FF', 
          wickUpColor: '#FF0000',
          wickDownColor: '#0000FF',
        });

        console.log('✅ Candlestick series 생성 성공:', candlestickSeries);

        // Generate sample data for the last 100 days
        const sampleData = [];
        const basePrice = 69000;
        let currentPrice = basePrice;
        
        const now = new Date();
        
        for (let i = 99; i >= 0; i--) {
          const date = new Date(now);
          date.setDate(date.getDate() - i);
          
          // Skip weekends
          if (date.getDay() === 0 || date.getDay() === 6) continue;
          
          const variation = (Math.random() - 0.5) * 0.05; // ±2.5% change
          const open = currentPrice;
          const volatility = Math.random() * 0.02; // 0-2% volatility
          const high = open * (1 + volatility);
          const low = open * (1 - volatility);
          const close = open * (1 + variation);
          
          sampleData.push({
            time: date.getFullYear() + '-' + 
                  String(date.getMonth() + 1).padStart(2, '0') + '-' + 
                  String(date.getDate()).padStart(2, '0'), // YYYY-MM-DD format
            open: Math.round(open),
            high: Math.round(high),
            low: Math.round(low), 
            close: Math.round(close)
          });
          
          currentPrice = close;
        }

        console.log('📊 샘플 데이터 생성:', sampleData.length, '개 포인트');
        console.log('첫 번째 데이터:', sampleData[0]);
        console.log('마지막 데이터:', sampleData[sampleData.length - 1]);

        candlestickSeries.setData(sampleData);
        chart.timeScale().fitContent();
        
        console.log('✅ 차트 데이터 설정 완료');
        setIsLoading(false);

        // Resize handler
        const handleResize = () => {
          if (chartContainerRef.current && chart) {
            chart.applyOptions({
              width: chartContainerRef.current.clientWidth,
            });
          }
        };

        window.addEventListener('resize', handleResize);

        // Cleanup function
        return () => {
          window.removeEventListener('resize', handleResize);
          if (chart) {
            chart.remove();
          }
        };

      } catch (error) {
        console.error('❌ 차트 초기화 실패:', error);
        setError('차트 로딩 실패: ' + (error as Error).message);
        setIsLoading(false);
      }
    }).catch((error) => {
      console.error('❌ lightweight-charts 로딩 실패:', error);
      setError('차트 라이브러리 로딩 실패: ' + error.message);
      setIsLoading(false);
    });

    // Cleanup if component unmounts before chart loads
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  if (error) {
    return (
      <Card className="w-full h-[400px]">
        <CardContent className="p-6 h-full flex flex-col items-center justify-center">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-red-600 mb-2">차트 로딩 오류</h3>
            <p className="text-sm text-muted-foreground">{error}</p>
            <p className="text-xs text-muted-foreground mt-2">브라우저 콘솔을 확인해주세요</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full h-[400px]">
      <CardContent className="p-0 h-full relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
            <div className="text-center">
              <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
              <p className="text-sm text-muted-foreground">TradingView 차트 로딩 중...</p>
            </div>
          </div>
        )}
        <div
          ref={chartContainerRef}
          className="w-full h-full"
          style={{ minHeight: '400px' }}
        />
      </CardContent>
    </Card>
  );
}