'use client';

import { useEffect, useRef, useCallback } from 'react';
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
  console.log('TradingChart 시작:', { 데이터길이: data.length, symbol, chartType, stockName });

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
      
      console.log('차트 초기화 시작 (v4), 데이터 길이:', data.length);
      
      try {
        // lightweight-charts v4 방식
        const { createChart, ColorType } = await import('lightweight-charts');
        
        console.log('lightweight-charts v4 로드 완료');
        
        // 기존 차트 제거
        if (chart.current) {
          chart.current.remove();
        }

        const isDark = resolvedTheme === 'dark';
        
        console.log('차트 생성 시도 (v4)...');
        
        // v4 방식으로 차트 생성
        chart.current = createChart(chartContainerRef.current, {
          width: chartContainerRef.current.clientWidth,
          height: height,
          layout: {
            background: {
              type: ColorType.Solid,
              color: isDark ? '#0c0a09' : '#ffffff'
            },
            textColor: isDark ? '#fafaf9' : '#0c0a09',
            fontSize: 12,
            fontFamily: 'ui-sans-serif, system-ui, -apple-system, sans-serif',
          },
          grid: {
            vertLines: { 
              color: isDark ? '#292524' : '#e7e5e4',
              style: 1, // 점선
            },
            horzLines: { 
              color: isDark ? '#292524' : '#e7e5e4',
              style: 1, // 점선
            },
          },
          crosshair: {
            mode: 1, // Normal crosshair mode
            vertLine: {
              width: 1,
              color: isDark ? '#78716c' : '#57534e',
              style: 0, // 실선
            },
            horzLine: {
              width: 1,
              color: isDark ? '#78716c' : '#57534e',
              style: 0, // 실선
            },
          },
          rightPriceScale: {
            borderColor: isDark ? '#44403c' : '#d6d3d1',
            autoScale: true,
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
            ticksVisible: true,
            entireTextOnly: false,
          },
          timeScale: {
            borderColor: isDark ? '#44403c' : '#d6d3d1',
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

        console.log('차트 인스턴스 생성 완료 (v4):', {
          chartExists: !!chart.current,
          addCandlestickSeries: typeof chart.current?.addCandlestickSeries
        });

        // v4 방식으로 캔들스틱 시리즈 생성 (한국식 색상: 빨강=상승, 파랑=하락)
        series.current = chart.current.addCandlestickSeries({
          upColor: '#ef4444',      // 상승: 빨강
          downColor: '#3b82f6',    // 하락: 파랑
          borderDownColor: '#3b82f6',  // 하락 테두리: 파랑
          borderUpColor: '#ef4444',    // 상승 테두리: 빨강
          wickDownColor: '#3b82f6',    // 하락 심지: 파랑
          wickUpColor: '#ef4444',      // 상승 심지: 빨강
          priceFormat: {
            type: 'price',
            precision: 0,
            minMove: 1,
          },
        });

        console.log('캔들스틱 시리즈 생성 완료 (v4):', !!series.current);

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
