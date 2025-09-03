'use client';

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { CandlestickData, ChartConfig } from './types';
import { createChartTheme, calculateSMA, convertToVolumeData, calculateMultipleMA } from './utils';
import ChartTooltip from './ChartTooltip';

interface SimpleChartProps {
  data: CandlestickData[];
  config: ChartConfig;
  height?: number;
  className?: string;
}

export default function SimpleChart({ 
  data, 
  config, 
  height = 400,
  className = ''
}: SimpleChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  
  // ref 변경 감지 및 차트 초기화
  useEffect(() => {
    console.log('🔗 chartContainerRef 변경됨:', !!chartContainerRef.current);
    if (chartContainerRef.current && data.length > 0) {
      console.log('📦 컨테이너 요소 정보:', {
        tagName: chartContainerRef.current.tagName,
        clientWidth: chartContainerRef.current.clientWidth,
        clientHeight: chartContainerRef.current.clientHeight,
        isConnected: chartContainerRef.current.isConnected
      });
      
      // ref가 설정되면 즉시 차트 초기화
      console.log('🚀 ref 설정됨 - 차트 초기화 시작');
      initChart();
    }
  });
  const chartRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const candlestickSeriesRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const volumeSeriesRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const maSeriesRefs = useRef<{ [key: string]: any }>({});  // eslint-disable-line @typescript-eslint/no-explicit-any
  const { resolvedTheme } = useTheme();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // 툴팁 상태
  const [tooltipData, setTooltipData] = useState<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [tooltipVisible, setTooltipVisible] = useState(false);

  const initChart = async () => {
    if (!chartContainerRef.current || !data.length) {
      console.log('⚠️ 차트 초기화 조건 미충족');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

        // 기존 차트 제거
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }

        // Lightweight Charts 동적 import
        const { createChart, ColorType } = await import('lightweight-charts');
        
        const isDark = resolvedTheme === 'dark';
        const theme = createChartTheme(isDark);
        
        // 차트 생성 (공식 문서 방식)
        const container = chartContainerRef.current;
        if (!container) {
          console.error('❌ 차트 컨테이너 없음');
          return;
        }
        
        console.log('📦 차트 컨테이너 정보:', {
          clientWidth: container.clientWidth,
          clientHeight: container.clientHeight,
          offsetWidth: container.offsetWidth,
          offsetHeight: container.offsetHeight,
          style: container.style.cssText
        });
        
        chartRef.current = createChart(container, {
          width: container.clientWidth,
          height: height,
          layout: {
            background: { type: ColorType.Solid, color: theme.layout.background.color },
            textColor: theme.layout.textColor,
            // 패널 설정 추가 (공식 문서 방식)
            panes: {
              separatorColor: isDark ? '#334155' : '#e2e8f0',
              separatorHoverColor: isDark ? '#475569' : '#cbd5e1',
              enableResize: true, // 사용자가 패널 크기 조정 가능
            },
          },
          grid: theme.grid,
          crosshair: {
            ...theme.crosshair,
            vertLine: {
              color: isDark ? '#64748b' : '#94a3b8',
              width: 1,
              style: 2, // 점선
              labelBackgroundColor: isDark ? '#334155' : '#e2e8f0',
            },
            horzLine: {
              color: isDark ? '#64748b' : '#94a3b8',
              width: 1,
              style: 2, // 점선
              labelBackgroundColor: isDark ? '#334155' : '#e2e8f0',
            },
          },
          rightPriceScale: {
            ...theme.priceScale,
            scaleMargins: {
              top: 0.1,
              bottom: 0.1, // 거래량이 별도 패널에 있으므로 여백 조정 불필요
            },
          },
          timeScale: theme.timeScale,
        });

        // 캔들스틱 시리즈 추가
        const candlestickSeries = chartRef.current.addCandlestickSeries({
          upColor: '#ef4444',      // 한국식 빨강 (상승)
          downColor: '#3b82f6',    // 한국식 파랑 (하락)
          borderVisible: false,
          wickUpColor: '#ef4444',
          wickDownColor: '#3b82f6',
        });

        // 데이터 설정
        console.log('📊 차트에 데이터 설정 중:', {
          dataLength: data.length,
          firstData: data[0],
          lastData: data[data.length - 1],
          sampleData: data.slice(0, 3)
        });
        
        try {
          candlestickSeries.setData(data);
          console.log('✅ 캔들스틱 데이터 설정 완료');
        } catch (err) {
          console.error('❌ 캔들스틱 데이터 설정 실패:', err);
          throw err;
        }

        // 거래량 차트 (별도 패널에 표시 - 공식 문서 방식)
        if (config.showVolume && data.some(d => d.volume)) {
          console.log('📊 거래량 시리즈 생성 중...');
          
          // 거래량을 패널 인덱스 1에 추가 (별도 패널)
          const volumeSeries = chartRef.current.addHistogramSeries({
            color: isDark ? '#475569' : '#94a3b8',
            priceFormat: {
              type: 'volume',
            },
          }, 1); // 패널 인덱스 1 (별도 패널)

          const volumeData = convertToVolumeData(data, '#ef4444', '#3b82f6');
          volumeSeries.setData(volumeData);
          
          // 거래량 패널 크기 조정
          const volumePane = chartRef.current.panes()[1];
          if (volumePane) {
            volumePane.setHeight(120); // 거래량 패널 높이 120px로 설정
            console.log('✅ 거래량 패널 설정 완료');
          }
        }

        // 이동평균선 (옵션)
        if (config.showMA && config.maPeriods.length > 0) {
          const colors = ['#ff6b35', '#f7931e', '#ffcd3c']; // 이동평균선 색상
          
          config.maPeriods.forEach((period, index) => {
            const maData = calculateSMA(data, period);
            if (maData.length > 0) {
              const maSeries = chartRef.current.addLineSeries({
                color: colors[index % colors.length],
                lineWidth: 2,
                title: `MA${period}`,
              });
              maSeries.setData(maData);
            }
          });
        }

        // 툴팁 이벤트 핸들러
        const handleCrosshairMove = (param: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
          if (!param || !param.time) {
            setTooltipVisible(false);
            return;
          }

          const dataPoint = data.find(d => d.time === param.time);
          if (!dataPoint) {
            setTooltipVisible(false);
            return;
          }

          // 이전 데이터와 비교하여 변동 계산
          const prevIndex = data.findIndex(d => d.time === param.time) - 1;
          const prevData = prevIndex >= 0 ? data[prevIndex] : null;
          const change = prevData ? dataPoint.close - prevData.close : 0;
          const changePercent = prevData ? (change / prevData.close) * 100 : 0;

          setTooltipData({
            time: dataPoint.time,
            open: dataPoint.open,
            high: dataPoint.high,
            low: dataPoint.low,
            close: dataPoint.close,
            volume: dataPoint.volume,
            change: change,
            changePercent: changePercent
          });

          // 마우스 위치 계산
          const container = chartContainerRef.current;
          if (container && param.point) {
            const rect = container.getBoundingClientRect();
            setTooltipPosition({
              x: rect.left + param.point.x,
              y: rect.top + param.point.y
            });
            setTooltipVisible(true);
          }
        };

        // 차트에서 마우스가 벗어날 때
        const handleMouseLeave = () => {
          setTooltipVisible(false);
        };

        // 이벤트 리스너 등록
        chartRef.current.subscribeCrosshairMove(handleCrosshairMove);
        container.addEventListener('mouseleave', handleMouseLeave);

        // 차트 크기 조정 핸들러
        const handleResize = () => {
          if (chartRef.current && chartContainerRef.current) {
            chartRef.current.applyOptions({
              width: chartContainerRef.current.clientWidth,
            });
          }
        };

        window.addEventListener('resize', handleResize);
        
        console.log('🎉 차트 초기화 완료!', {
          chartExists: !!chartRef.current,
          containerExists: !!container,
          dataLength: data.length
        });
        
        setIsLoading(false);

        // 클린업 함수 반환
        return () => {
          window.removeEventListener('resize', handleResize);
          container.removeEventListener('mouseleave', handleMouseLeave);
          if (chartRef.current) {
            chartRef.current.unsubscribeCrosshairMove(handleCrosshairMove);
            chartRef.current.remove();
            chartRef.current = null;
          }
        };

      } catch (err) {
        console.error('차트 초기화 실패:', err);
        setError('차트를 불러올 수 없습니다.');
        setIsLoading(false);
      }
  };

  // 데이터나 설정 변경 시 차트 재초기화
  useEffect(() => {
    console.log('📊 데이터/설정 변경됨:', { 
      dataLength: data.length,
      hasContainer: !!chartContainerRef.current,
      config: config.timeframe
    });
    
    if (chartContainerRef.current && data.length > 0) {
      console.log('🔄 차트 재초기화 시작');
      initChart();
    } else if (data.length === 0) {
      setIsLoading(false);
    }
  }, [data, config, height, resolvedTheme]);

  // 로딩 상태
  if (isLoading) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
          <p className="text-sm text-muted-foreground">차트 로딩 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-center">
          <div className="text-destructive mb-2 text-2xl">⚠️</div>
          <p className="text-sm text-destructive mb-2">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="text-xs text-primary hover:underline"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  // 빈 데이터
  if (!data.length) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-center text-muted-foreground">
          <div className="text-4xl mb-2">📊</div>
          <p className="text-sm">차트 데이터가 없습니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <div 
        ref={chartContainerRef} 
        className="w-full rounded-lg relative border border-gray-200 dark:border-gray-700"
        style={{ 
          height: height,
          minHeight: height,
          minWidth: 300,
          backgroundColor: 'transparent'
        }}
        onLoad={() => console.log('📦 컨테이너 DOM 로드됨')}
      >
        {/* 디버깅용 플레이스홀더 */}
        <div className="absolute inset-0 flex items-center justify-center text-gray-400 pointer-events-none">
          {isLoading ? '차트 로딩 중...' : '차트 컨테이너'}
        </div>
      </div>
      
      {/* 툴팁 */}
      <ChartTooltip
        data={tooltipData}
        position={tooltipPosition}
        visible={tooltipVisible}
      />
    </div>
  );
}