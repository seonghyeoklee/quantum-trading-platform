'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";

export function SimpleTradingChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Dynamic import to prevent SSR issues
    import('lightweight-charts').then((LightweightCharts) => {
      if (!chartContainerRef.current) return;

      try {
        console.log('📊 Lightweight Charts 모듈 로드됨:', Object.keys(LightweightCharts));
        
        // Create chart using the correct API
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

        chartRef.current = chart;

        // Add candlestick series using the official API (Korean colors)
        let mainSeries;
        try {
          // Try different ways to add candlestick series
          if (chart.addCandlestickSeries) {
            // Legacy method for older versions
            mainSeries = chart.addCandlestickSeries({
              upColor: '#FF0000',
              downColor: '#0000FF',
              borderUpColor: '#FF0000',
              borderDownColor: '#0000FF',
              wickUpColor: '#FF0000',
              wickDownColor: '#0000FF',
            });
            console.log('✅ Legacy Candlestick series 생성 성공');
          } else if (LightweightCharts.CandlestickSeries) {
            // New method with series class
            mainSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {
              upColor: '#FF0000',
              downColor: '#0000FF',
              borderVisible: false,
              wickUpColor: '#FF0000',
              wickDownColor: '#0000FF',
            });
            console.log('✅ New API Candlestick series 생성 성공');
          } else {
            throw new Error('No candlestick method available');
          }
        } catch (candlestickError) {
          console.log('❌ Candlestick series 실패, Line series로 대체:', candlestickError);
          // Fallback to line series
          try {
            if (chart.addLineSeries) {
              mainSeries = chart.addLineSeries({
                color: '#2962FF',
                lineWidth: 2,
              });
            } else if (LightweightCharts.LineSeries) {
              mainSeries = chart.addSeries(LightweightCharts.LineSeries, {
                color: '#2962FF',
                lineWidth: 2,
              });
            } else {
              throw new Error('No line series method available');
            }
            console.log('✅ Line series 생성 성공');
          } catch (lineError) {
            console.error('❌ Line series도 실패:', lineError);
            throw lineError;
          }
        }

        // Generate sample data
        const candlestickData = [];
        const lineData = [];
        const basePrice = 69000;
        let currentPrice = basePrice;
        
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 365);
        
        for (let i = 0; i < 365; i++) {
          const date = new Date(startDate);
          date.setDate(date.getDate() + i);
          
          // Skip weekends
          if (date.getDay() === 0 || date.getDay() === 6) continue;
          
          const variation = (Math.random() - 0.5) * 0.05; // ±2.5% change
          const open = currentPrice;
          const volatility = Math.random() * 0.02; // 0-2% volatility
          const high = open * (1 + volatility);
          const low = open * (1 - volatility);
          const close = open * (1 + variation);
          const time = Math.floor(date.getTime() / 1000); // Unix timestamp
          
          // Candlestick data format
          candlestickData.push({
            time,
            open,
            high,
            low, 
            close
          });
          
          // Line data format (just close price)
          lineData.push({
            time,
            value: close
          });
          
          currentPrice = close;
        }

        // Set data based on series type
        try {
          if (mainSeries && mainSeries.setData) {
            // Check if we have candlestick data and it's properly formatted
            if (candlestickData.length > 0 && candlestickData[0] && typeof candlestickData[0].open !== 'undefined') {
              mainSeries.setData(candlestickData);
              console.log('✅ Candlestick 데이터 설정 완료:', candlestickData.length, '개');
            } else {
              mainSeries.setData(lineData);
              console.log('✅ Line 데이터 설정 완료:', lineData.length, '개');
            }
          } else {
            console.warn('❌ mainSeries 또는 setData 메서드가 없습니다');
          }
        } catch (dataError) {
          console.error('❌ 데이터 설정 실패:', dataError);
        }
        chart.timeScale().fitContent();
        
        setIsLoading(false);
        console.log('✅ 차트 로딩 완료');

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
        setIsLoading(false);
      }
    }).catch((error) => {
      console.error('❌ lightweight-charts 로딩 실패:', error);
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

  return (
    <Card className="w-full h-[400px]">
      <CardContent className="p-0 h-full relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
            <div className="text-center">
              <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-2"></div>
              <p className="text-sm text-muted-foreground">차트를 불러오는 중...</p>
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