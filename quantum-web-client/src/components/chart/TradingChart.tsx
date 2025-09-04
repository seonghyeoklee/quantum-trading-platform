'use client';

import { useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';
import { CandlestickData } from './ChartTypes';

interface TradingChartProps {
  data: CandlestickData[];
  width?: number;
  height?: number;
  symbol?: string;
  timeframe?: string;
  chartType?: string;
  stockName?: string;
}

export default function TradingChart({ 
  data, 
  width = 800, 
  height = 400,
  symbol = '005930',
  timeframe = '1M',
  chartType = 'daily',
  stockName
}: TradingChartProps) {
  console.log('TradingChart v5 시작:', { 데이터길이: data.length, symbol, chartType, stockName });

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chart = useRef<any>(null);
  const series = useRef<any>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    const handleResize = () => {
      if (chart.current && chartContainerRef.current) {
        chart.current.applyOptions({ 
          width: chartContainerRef.current.clientWidth 
        });
      }
    };

    const initChart = async () => {
      if (!chartContainerRef.current) return;
      
      console.log('차트 초기화 시작 (v5), 데이터 길이:', data.length);
      
      try {
        // lightweight-charts v5 방식
        const { createChart, ColorType, CandlestickSeries } = await import('lightweight-charts');
        
        console.log('lightweight-charts v5 로드 완료');
        
        // 기존 차트 제거
        if (chart.current) {
          chart.current.remove();
        }

        const isDark = resolvedTheme === 'dark';
        
        console.log('차트 생성 시도 (v5)...');
        
        // v5 방식으로 차트 생성 (TradingView 스타일)
        chart.current = createChart(chartContainerRef.current, {
          width: chartContainerRef.current.clientWidth,
          height: height,
          layout: {
            background: {
              type: ColorType.Solid,
              color: isDark ? '#131722' : '#ffffff'  // TradingView 다크 색상
            },
            textColor: isDark ? '#d1d4dc' : '#191919',  // TradingView 텍스트 색상
            fontSize: 12,
            fontFamily: '-apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif',
          },
          grid: {
            vertLines: { 
              color: isDark ? '#2a2e39' : '#f0f3fa',
              style: 0,
            },
            horzLines: { 
              color: isDark ? '#2a2e39' : '#f0f3fa', 
              style: 0,
            },
          },
          crosshair: {
            mode: 1,
            vertLine: {
              width: 1,
              color: isDark ? '#758696' : '#9598a1',
              style: 3, // 점선
            },
            horzLine: {
              width: 1,
              color: isDark ? '#758696' : '#9598a1',
              style: 3, // 점선
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
            horzTouchDrag: true,
            vertTouchDrag: true,
          },
          handleScale: {
            axisPressedMouseMove: true,
            mouseWheel: true,
            pinch: true,
          },
        });

        console.log('차트 인스턴스 생성 완료 (v5):', {
          chartExists: !!chart.current,
          addSeries: typeof chart.current?.addSeries
        });

        // v5 방식으로 캔들스틱 시리즈 생성 (TradingView 기본 색상)
        series.current = chart.current.addSeries(CandlestickSeries, {
          upColor: '#26a69a',      // TradingView 상승 색상 (청록색)
          downColor: '#ef5350',    // TradingView 하락 색상 (빨강)
          borderVisible: false,
          wickUpColor: '#26a69a',
          wickDownColor: '#ef5350',
          priceFormat: {
            type: 'price',
            precision: 0,
            minMove: 1,
          },
        });

        console.log('캔들스틱 시리즈 생성 완료 (v5):', !!series.current);

        // 데이터가 있으면 설정
        if (data.length > 0) {
          console.log('🔍 초기 차트 데이터 분석:', { 
            chartType, 
            timeframe, 
            원본개수: data.length, 
            첫번째원본: data[0],
            마지막원본: data[data.length - 1]
          });
          
          // 간단한 데이터 변환 (타입 오류 방지)
          const chartData = data.map((item) => ({
            time: item.time,
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
          }));
          
          console.log('📊 차트 데이터 변환 완료:', {
            변환후개수: chartData.length,
            첫번째데이터: chartData[0],
            마지막데이터: chartData[chartData.length - 1]
          });
          
          series.current.setData(chartData);
          chart.current.timeScale().fitContent();
        }

        // 리사이즈 이벤트 리스너 추가
        window.addEventListener('resize', handleResize);
        
        console.log('차트 생성 완료 (v4)');

      } catch (error) {
        console.error('차트 생성 오류 (v4):', error);
        console.error('에러 스택:', error instanceof Error ? error.stack : 'No stack');
      }
    };

    initChart();

    return () => {
      window.removeEventListener('resize', handleResize);
      
      if (chart.current) {
        chart.current.remove();
        chart.current = null;
        series.current = null;
      }
    };
  }, [data, height, resolvedTheme, chartType]);

  return (
    <div className="w-full h-full">
      <div 
        ref={chartContainerRef} 
        className="w-full rounded-lg border border-border trading-chart-container"
        style={{ height: `${height}px` }}
      />
    </div>
  );
}
