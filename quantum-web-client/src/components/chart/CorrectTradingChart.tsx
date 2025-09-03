'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";

export function CorrectTradingChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Dynamic import with correct v5 API
    import('lightweight-charts').then(({ createChart, CandlestickSeries }) => {
      if (!chartContainerRef.current) return;

      try {
        console.log('📊 정확한 v5 API 사용');
        
        // Create chart
        const chart = createChart(chartContainerRef.current, {
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

        // Use the correct v5 API with CandlestickSeries
        const candlestickSeries = chart.addSeries(CandlestickSeries, {
          upColor: '#FF0000',      // Red for up (Korean style)
          downColor: '#0000FF',    // Blue for down (Korean style)
          borderUpColor: '#FF0000',
          borderDownColor: '#0000FF', 
          wickUpColor: '#FF0000',
          wickDownColor: '#0000FF',
        });

        console.log('✅ CandlestickSeries 추가 성공');

        // Generate sample data
        const sampleData = [];
        const basePrice = 69000;
        let currentPrice = basePrice;
        
        const now = new Date();
        
        for (let i = 99; i >= 0; i--) {
          const date = new Date(now);
          date.setDate(date.getDate() - i);
          
          // Skip weekends
          if (date.getDay() === 0 || date.getDay() === 6) continue;
          
          const variation = (Math.random() - 0.5) * 0.05;
          const open = currentPrice;
          const volatility = Math.random() * 0.02;
          const high = open * (1 + volatility);
          const low = open * (1 - volatility);
          const close = open * (1 + variation);
          
          sampleData.push({
            time: date.getFullYear() + '-' + 
                  String(date.getMonth() + 1).padStart(2, '0') + '-' + 
                  String(date.getDate()).padStart(2, '0'),
            open: Math.round(open),
            high: Math.round(high),
            low: Math.round(low), 
            close: Math.round(close)
          });
          
          currentPrice = close;
        }

        console.log('📊 데이터 생성:', sampleData.length, '포인트');
        console.log('첫 번째 데이터:', sampleData[0]);

        candlestickSeries.setData(sampleData);
        chart.timeScale().fitContent();
        
        console.log('✅ 차트 완료!');
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

        // Return cleanup function
        return () => {
          window.removeEventListener('resize', handleResize);
          if (chart) {
            chart.remove();
          }
        };

      } catch (error) {
        console.error('❌ 오류:', error);
        setError('차트 생성 실패: ' + (error as Error).message);
        setIsLoading(false);
      }
    }).catch((importError) => {
      console.error('❌ Import 실패:', importError);
      setError('모듈 import 실패: ' + importError.message);
      setIsLoading(false);
    });

    // Cleanup if component unmounts
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
            <h3 className="text-lg font-semibold text-red-600">차트 오류</h3>
            <p className="text-sm text-muted-foreground">{error}</p>
            <div className="text-4xl">📈</div>
            <div className="mt-4 space-y-2">
              <p className="text-lg font-semibold">삼성전자 (005930)</p>
              <p className="text-3xl font-bold text-red-600">69,000원</p>
              <p className="text-green-600">+1,500원 (+2.22%)</p>
              <p className="text-xs text-muted-foreground mt-4">
                TradingView 라이브러리 문제로 텍스트 표시
              </p>
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
              <p className="text-sm text-muted-foreground">정확한 v5 API로 차트 생성 중...</p>
            </div>
          </div>
        )}
        <div
          ref={chartContainerRef}
          className="w-full h-full"
        />
      </CardContent>
    </Card>
  );
}