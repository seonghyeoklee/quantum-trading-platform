'use client';

import { useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { TradingViewCandle } from '@/lib/types/kis-domestic-types';

// 동적 import를 위한 타입 정의
type IChartApi = any;
type ISeriesApi = any;
type CandlestickData = any;
type UTCTimestamp = any;
type CreateChartFunction = any;

interface KISChartProps {
  data: TradingViewCandle[];
  width?: number;
  height?: number;
  symbol?: string;
  chartType?: 'daily' | 'minute';
}

export default function KISChart({
  data,
  width = 800,
  height = 400,
  symbol = '',
  chartType = 'daily'
}: KISChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi | null>(null);
  const { resolvedTheme } = useTheme();
  const [chartLoaded, setChartLoaded] = useState(false);

  // 차트 초기화 (동적 import 사용)
  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return;

    console.log('📈 KIS 차트 초기화:', { symbol, chartType, 데이터길이: data.length });

    // lightweight-charts 동적 import
    import('lightweight-charts').then(({ createChart }) => {
      if (!chartContainerRef.current) return;

      // 차트 생성
      const chart = createChart(chartContainerRef.current, {
        width: width,
        height: height,
        layout: {
          background: {
            color: resolvedTheme === 'dark' ? '#1a1a1a' : '#ffffff',
          },
          textColor: resolvedTheme === 'dark' ? '#d1d5db' : '#374151',
        },
        grid: {
          vertLines: {
            color: resolvedTheme === 'dark' ? '#374151' : '#e5e7eb',
          },
          horzLines: {
            color: resolvedTheme === 'dark' ? '#374151' : '#e5e7eb',
          },
        },
        crosshair: {
          mode: 1, // Normal crosshair
        },
        rightPriceScale: {
          borderColor: resolvedTheme === 'dark' ? '#4b5563' : '#d1d5db',
        },
        timeScale: {
          borderColor: resolvedTheme === 'dark' ? '#4b5563' : '#d1d5db',
          timeVisible: chartType === 'minute',
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

      // 캔들스틱 시리즈 추가
      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#ef4444', // 상승 - 빨간색 (한국식)
        downColor: '#3b82f6', // 하락 - 파란색 (한국식)
        borderVisible: false,
        wickUpColor: '#ef4444',
        wickDownColor: '#3b82f6',
      });

      // 데이터 변환 및 설정
      const chartData: CandlestickData[] = data.map(item => ({
        time: item.time as UTCTimestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }));

      console.log('📊 차트 데이터 설정:', chartData.slice(0, 3));

      candlestickSeries.setData(chartData);
      
      // 자동 스케일링
      chart.timeScale().fitContent();

      chartRef.current = chart;
      seriesRef.current = candlestickSeries;
      setChartLoaded(true);

      console.log('✅ 차트 로드 완료');
    }).catch(error => {
      console.error('❌ 차트 로드 실패:', error);
    });

    // 정리 함수
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
        seriesRef.current = null;
      }
    };
  }, [data, width, height, symbol, chartType, resolvedTheme]);

  // 테마 변경 처리
  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.applyOptions({
        layout: {
          background: {
            color: resolvedTheme === 'dark' ? '#1a1a1a' : '#ffffff',
          },
          textColor: resolvedTheme === 'dark' ? '#d1d5db' : '#374151',
        },
        grid: {
          vertLines: {
            color: resolvedTheme === 'dark' ? '#374151' : '#e5e7eb',
          },
          horzLines: {
            color: resolvedTheme === 'dark' ? '#374151' : '#e5e7eb',
          },
        },
        rightPriceScale: {
          borderColor: resolvedTheme === 'dark' ? '#4b5563' : '#d1d5db',
        },
        timeScale: {
          borderColor: resolvedTheme === 'dark' ? '#4b5563' : '#d1d5db',
        },
      });
    }
  }, [resolvedTheme]);

  // 데이터 업데이트 (차트가 로드된 후에만)
  useEffect(() => {
    if (seriesRef.current && data.length > 0 && chartLoaded) {
      const chartData: CandlestickData[] = data.map(item => ({
        time: item.time as UTCTimestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }));

      seriesRef.current.setData(chartData);
      
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
      }
    }
  }, [data, chartLoaded]);

  return (
    <div className="w-full">
      <div className="mb-2 text-sm text-muted-foreground">
        {symbol && (
          <span>
            {symbol} - {chartType === 'daily' ? '일봉' : '분봉'} 차트
          </span>
        )}
      </div>
      <div 
        ref={chartContainerRef} 
        className="border border-border rounded-lg relative"
        style={{ width: `${width}px`, height: `${height}px` }}
      >
        {!chartLoaded && data.length > 0 && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50">
            <div className="text-sm text-muted-foreground">차트 로딩중...</div>
          </div>
        )}
      </div>
    </div>
  );
}