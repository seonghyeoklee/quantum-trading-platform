'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";

export function WorkingTradingChart() {
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
        console.log('📊 Lightweight Charts v5 API 사용');
        
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
            mode: LightweightCharts.CrosshairMode?.Normal || 1,
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

        console.log('✅ Chart 생성 성공');
        chartRef.current = chart;

        // Use addSeries instead of addCandlestickSeries in v5
        const candlestickSeries = chart.addSeries(LightweightCharts.SeriesType?.Candlestick || 'Candlestick', {
          upColor: '#FF0000',      // Red for up (Korean style)
          downColor: '#0000FF',    // Blue for down (Korean style)
          borderUpColor: '#FF0000',
          borderDownColor: '#0000FF', 
          wickUpColor: '#FF0000',
          wickDownColor: '#0000FF',
        });

        console.log('✅ Candlestick series 생성 성공');

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

        console.log('📊 샘플 데이터 생성:', sampleData.length, '개');
        candlestickSeries.setData(sampleData);
        chart.timeScale().fitContent();
        
        console.log('✅ 차트 렌더링 완료');
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
        console.error('❌ 차트 생성 실패:', error);
        
        // Fallback: try different approach for v5
        try {
          console.log('🔄 Fallback: 다른 방법으로 시도');
          const chart = LightweightCharts.createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 400,
          });
          
          // Try with string type instead
          const series = chart.addSeries('candlestick', {
            upColor: '#FF0000',
            downColor: '#0000FF',
          });
          
          const simpleData = [
            { time: '2023-12-01', open: 100, high: 110, low: 95, close: 105 },
            { time: '2023-12-02', open: 105, high: 115, low: 100, close: 108 },
            { time: '2023-12-03', open: 108, high: 112, low: 103, close: 106 },
          ];
          
          series.setData(simpleData);
          chart.timeScale().fitContent();
          
          console.log('✅ Fallback 성공');
          setIsLoading(false);
          
        } catch (fallbackError) {
          console.error('❌ Fallback도 실패:', fallbackError);
          setError('차트 라이브러리 호환 문제: ' + (error as Error).message);
          setIsLoading(false);
        }
      }
    }).catch((error) => {
      console.error('❌ 모듈 로딩 실패:', error);
      setError('차트 모듈 로딩 실패: ' + error.message);
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
          <div className="text-center space-y-4">
            <h3 className="text-lg font-semibold text-red-600">차트 로딩 오류</h3>
            <p className="text-sm text-muted-foreground">{error}</p>
            <div className="text-2xl">📈</div>
            <p className="text-sm">간단한 텍스트 차트로 대체하겠습니다</p>
            <div className="mt-4 space-y-2">
              <p className="text-lg font-semibold">삼성전자 (005930)</p>
              <p className="text-2xl font-bold text-red-600">69,000원</p>
              <p className="text-green-600">+1,500원 (+2.22%)</p>
            </div>
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
              <p className="text-sm text-muted-foreground">TradingView 차트 (v5) 로딩 중...</p>
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