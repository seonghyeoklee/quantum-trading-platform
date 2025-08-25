'use client';

import { useEffect, useRef, useCallback, useMemo } from 'react';
import { useTheme } from 'next-themes';
import { CandlestickData } from './ChartTypes';
import { RealtimeCandleData, ChartUpdateData } from '@/lib/api/websocket-types';

interface TradingChartProps {
  data: CandlestickData[];
  width?: number;
  height?: number;
  symbol?: string;
  timeframe?: string;
  chartType?: string;
  stockName?: string;
  realtimeData?: RealtimeCandleData;  // 실시간 업데이트 데이터
  onRealtimeUpdate?: (data: RealtimeCandleData) => void;  // 실시간 데이터 콜백
}

export default function TradingChart({ 
  data, 
  width = 800, 
  height = 400,
  symbol = '005930',
  timeframe = '1M',
  chartType = 'daily',
  stockName,
  realtimeData,
  onRealtimeUpdate
}: TradingChartProps) {
  console.log('TradingChart 시작:', { 데이터길이: data.length, symbol, chartType, stockName });

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chart = useRef<any>(null);
  const series = useRef<any>(null);
  const { resolvedTheme } = useTheme();
  
  // TradingView 공식 방식의 실시간 업데이트를 위한 상태
  const lastUpdateTimeRef = useRef<string>('');
  const isRealtimeEnabledRef = useRef<boolean>(true);
  const realtimeUpdateIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // 실시간 데이터 큐 (TradingView 가이드 방식)
  const realtimeDataQueueRef = useRef<RealtimeCandleData[]>([]);
  const currentCandleRef = useRef<ChartUpdateData | null>(null);

  // 실시간 데이터를 차트 형식으로 변환
  // 차트 타입별 시간 정규화 함수 - 초기 데이터와 실시간 데이터 일관성 보장
  const normalizeTimeByChartType = useCallback((timestamp: string, chartType: string): string | number => {
    // 유효하지 않은 시간 처리
    if (!timestamp) {
      console.warn('⚠️ 빈 timestamp 입력:', timestamp);
      return Math.floor(Date.now() / 1000);
    }
    
    const date = new Date(timestamp);
    
    // 잘못된 날짜 처리
    if (isNaN(date.getTime())) {
      console.warn('⚠️ 잘못된 timestamp:', timestamp);
      return Math.floor(Date.now() / 1000);
    }
    
    console.log('🕐 시간 정규화 시작:', { 
      원본시간: timestamp, 
      chartType,
      파싱된날짜: date.toISOString() 
    });
    
    // 한국 시장 시간 고려 (UTC+9)
    const kstOffset = 9 * 60 * 60 * 1000; // 9시간을 밀리초로
    const kstDate = new Date(date.getTime());
    
    switch (chartType) {
      case 'tick':
        // 틱차트: 실시간 그대로 (밀리초 제거)
        return Math.floor(kstDate.getTime() / 1000);
        
      case 'minute':
        // 1분봉: 초와 밀리초를 0으로 설정하여 1분 간격으로 그룹핑
        kstDate.setSeconds(0, 0);
        return Math.floor(kstDate.getTime() / 1000);
        
      case '3minute':
        // 3분봉: 3분 간격으로 그룹핑 (09:30, 09:33, 09:36...)
        const minutes3 = Math.floor(kstDate.getMinutes() / 3) * 3;
        kstDate.setMinutes(minutes3, 0, 0);
        return Math.floor(kstDate.getTime() / 1000);
        
      case '5minute':
        // 5분봉: 5분 간격으로 그룹핑 (09:30, 09:35, 09:40...)
        const minutes5 = Math.floor(kstDate.getMinutes() / 5) * 5;
        kstDate.setMinutes(minutes5, 0, 0);
        return Math.floor(kstDate.getTime() / 1000);
        
      case '15minute':
        // 15분봉: 15분 간격으로 그룹핑 (09:30, 09:45, 10:00...)
        const minutes15 = Math.floor(kstDate.getMinutes() / 15) * 15;
        kstDate.setMinutes(minutes15, 0, 0);
        return Math.floor(kstDate.getTime() / 1000);
        
      case '30minute':
        // 30분봉: 30분 간격으로 그룹핑 (09:30, 10:00, 10:30...)
        const minutes30 = Math.floor(kstDate.getMinutes() / 30) * 30;
        kstDate.setMinutes(minutes30, 0, 0);
        return Math.floor(kstDate.getTime() / 1000);
        
      case 'hourly':
        // 1시간봉: 분과 초를 0으로 설정
        kstDate.setMinutes(0, 0, 0);
        return Math.floor(kstDate.getTime() / 1000);
        
      case 'daily':
        // 일봉: 날짜만 사용 (TradingView는 'YYYY-MM-DD' 형식 허용)
        return kstDate.toISOString().split('T')[0];
        
      case 'weekly':
        // 주봉: 해당 주의 월요일로 정규화
        const dayOfWeek = kstDate.getDay();
        const mondayOffset = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
        const monday = new Date(kstDate);
        monday.setDate(kstDate.getDate() + mondayOffset);
        monday.setHours(0, 0, 0, 0);
        return monday.toISOString().split('T')[0];
        
      case 'monthly':
        // 월봉: 해당 월의 1일로 정규화
        return `${kstDate.getFullYear()}-${String(kstDate.getMonth() + 1).padStart(2, '0')}-01`;
        
      case 'yearly':
        // 년봉: 해당 연도의 1월 1일로 정규화
        return `${kstDate.getFullYear()}-01-01`;
        
      default:
        // 기본값: Unix timestamp (분봉으로 처리)
        console.warn('⚠️ 알 수 없는 chartType:', chartType, '- 분봉으로 처리');
        kstDate.setSeconds(0, 0);
        return Math.floor(kstDate.getTime() / 1000);
    }
  }, []);

  // 초기 차트 데이터의 시간 형식을 기억하는 ref
  const initialDataTimeFormatRef = useRef<'string' | 'number' | null>(null);

  const convertRealtimeToChartData = useCallback((realtimeData: RealtimeCandleData): ChartUpdateData => {
    let timeValue: string | number = realtimeData.time;
    
    console.log('🔄 실시간 데이터 변환 시작:', { 
      원본시간: timeValue, 
      chartType, 
      타입: typeof timeValue,
      초기데이터형식: initialDataTimeFormatRef.current
    });
    
    // 핵심: 초기 데이터와 동일한 형식으로 강제 변환
    if (initialDataTimeFormatRef.current === 'string') {
      // 초기 데이터가 문자열이면 실시간도 문자열로
      if (typeof timeValue === 'number') {
        timeValue = new Date(timeValue * 1000).toISOString().split('T')[0];
      } else if (typeof timeValue === 'string') {
        // 이미 문자열이지만 정규화 필요
        timeValue = normalizeTimeByChartType(timeValue, chartType);
      }
    } else if (initialDataTimeFormatRef.current === 'number') {
      // 초기 데이터가 숫자면 실시간도 숫자로
      if (typeof timeValue === 'string') {
        timeValue = Math.floor(new Date(timeValue).getTime() / 1000);
      }
      // 이미 숫자인 경우 그대로 사용
    } else {
      // 초기 데이터 형식이 없으면 기본 정규화
      if (typeof timeValue === 'string') {
        timeValue = normalizeTimeByChartType(timeValue, chartType);
      } else if (typeof timeValue === 'number') {
        const isoString = new Date(timeValue * 1000).toISOString();
        timeValue = normalizeTimeByChartType(isoString, chartType);
      }
    }
    
    console.log('✅ 실시간 데이터 변환 완료:', { 
      변환후시간: timeValue, 
      타입: typeof timeValue,
      차트타입: chartType,
      유효성: typeof timeValue === 'number' ? timeValue > 0 : timeValue.length > 0,
      최종OHLCV: {
        time: timeValue,
        open: realtimeData.open,
        high: realtimeData.high,
        low: realtimeData.low,
        close: realtimeData.close,
        volume: realtimeData.volume
      }
    });

    return {
      time: timeValue,
      open: realtimeData.open,
      high: realtimeData.high,
      low: realtimeData.low,
      close: realtimeData.close,
      volume: realtimeData.volume,
    };
  }, [chartType, normalizeTimeByChartType]);

  // TradingView 가이드 방식의 실시간 데이터 제너레이터 (안전한 버전)
  const processRealtimeUpdate = useCallback(() => {
    if (realtimeDataQueueRef.current.length === 0 || !series.current || !chart.current) {
      return;
    }

    const update = realtimeDataQueueRef.current.shift();
    if (!update) return;

    try {
      const updateData = convertRealtimeToChartData(update);
      
      // 시간 형식 호환성 검사
      const currentTimeType = typeof updateData.time;
      const expectedTimeType = initialDataTimeFormatRef.current;
      
      if (expectedTimeType && currentTimeType !== expectedTimeType) {
        console.warn('⚠️ 시간 형식 불일치 감지! 차트 리셋 필요:', {
          예상형식: expectedTimeType,
          실제형식: currentTimeType,
          초기데이터형식: initialDataTimeFormatRef.current,
          실시간시간값: updateData.time
        });
        
        // 시간 형식이 다르면 실시간 업데이트 중단
        console.log('🛑 시간 형식 불일치로 실시간 업데이트 중단');
        return;
      }
      
      console.log('📈 TradingView series.update() 호출 직전:', {
        symbol: update.symbol,
        time: update.time,
        정규화된시간: updateData.time,
        시간타입: typeof updateData.time,
        초기데이터시간타입: initialDataTimeFormatRef.current,
        OHLCV: updateData
      });

      try {
        // TradingView 가이드: 단순히 series.update() 호출
        series.current.update(updateData);
        console.log('✅ series.update() 성공');
      } catch (updateError) {
        console.error('❌ series.update() 실패:', {
          error: updateError,
          updateData,
          시간타입: typeof updateData.time,
          시간값: updateData.time,
          초기데이터시간타입: initialDataTimeFormatRef.current
        });
        
        // 업데이트 실패 시 실시간 업데이트 중단
        console.log('🛑 series.update() 실패로 실시간 업데이트 중단');
        if (realtimeUpdateIntervalRef.current) {
          clearInterval(realtimeUpdateIntervalRef.current);
          realtimeUpdateIntervalRef.current = null;
        }
        return;
      }
      
      // 현재 캔들 정보 추적
      currentCandleRef.current = updateData;
      
      // 실시간 스크롤 (TradingView 가이드 방식)
      if (chart.current) {
        chart.current.timeScale().scrollToRealTime();
      }

      lastUpdateTimeRef.current = update.time;
      onRealtimeUpdate?.(update);
      
    } catch (error) {
      console.error('실시간 차트 업데이트 오류:', error);
      
      // 오류 발생 시 실시간 업데이트 중단
      if (realtimeUpdateIntervalRef.current) {
        clearInterval(realtimeUpdateIntervalRef.current);
        realtimeUpdateIntervalRef.current = null;
      }
    }
  }, [convertRealtimeToChartData, onRealtimeUpdate]);

  // TradingView 가이드 방식의 실시간 차트 업데이트 함수
  const updateChart = useCallback((realtimeData: RealtimeCandleData) => {
    if (!isRealtimeEnabledRef.current) {
      console.log('실시간 업데이트 비활성화됨');
      return;
    }

    // 실시간 데이터를 큐에 추가 (TradingView 가이드 방식)
    realtimeDataQueueRef.current.push(realtimeData);
    
    console.log('📊 실시간 데이터 큐에 추가:', {
      symbol: realtimeData.symbol,
      time: realtimeData.time,
      큐길이: realtimeDataQueueRef.current.length
    });

    // 실시간 업데이트 인터벌이 없으면 시작 (TradingView 가이드: 100ms)
    if (!realtimeUpdateIntervalRef.current && series.current) {
      console.log('🚀 실시간 업데이트 인터벌 시작 (100ms)');
      realtimeUpdateIntervalRef.current = setInterval(() => {
        processRealtimeUpdate();
      }, 100);
    }
  }, [processRealtimeUpdate]);

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
            secondsVisible: chartType === 'tick' || chartType === 'minute',
            tickMarkFormatter: (time: any) => {
              // 한국어 날짜 형식으로 포맷
              const date = new Date(typeof time === 'number' ? time * 1000 : time);
              const isIntraday = chartType === 'tick' || chartType === 'minute';
              
              if (isIntraday) {
                // 틱/분봉: 시:분 형식
                return date.toLocaleTimeString('ko-KR', { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  hour12: false 
                });
              } else {
                // 일봉 이상: 월/일 또는 년/월 형식
                if (chartType === 'yearly') {
                  return date.toLocaleDateString('ko-KR', { year: 'numeric' });
                } else if (chartType === 'monthly') {
                  return date.toLocaleDateString('ko-KR', { 
                    year: 'numeric', 
                    month: 'short' 
                  });
                } else {
                  return date.toLocaleDateString('ko-KR', { 
                    month: 'short', 
                    day: 'numeric' 
                  });
                }
              }
            }
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

        // 새로운 차트가 생성될 때 실시간 상태 초기화 (TradingView 가이드 방식)
        console.log('🔄 차트 시리즈 생성 - 실시간 상태 초기화');
        realtimeDataQueueRef.current = [];
        currentCandleRef.current = null;
        initialDataTimeFormatRef.current = null; // 시간 형식 기억도 초기화
        
        // 기존 인터벌 정리
        if (realtimeUpdateIntervalRef.current) {
          clearInterval(realtimeUpdateIntervalRef.current);
          realtimeUpdateIntervalRef.current = null;
        }

        // 가격 포맷터 설정 (한국어 천 단위 구분)
        chart.current.priceScale('right').applyOptions({
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
          entireTextOnly: false,
          ticksVisible: true,
          // Y축 가격 포맷터
          priceFormatter: (price: number) => {
            return new Intl.NumberFormat('ko-KR', {
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(price);
          },
        });

        // 툴팁 정보 표시를 위한 범례 표시
        const toolTipWidth = 240;
        const toolTipHeight = 150;
        const toolTipMargin = 15;

        // 툴팁 엘리먼트 생성
        const toolTip = document.createElement('div');
        toolTip.style.cssText = `
          width: ${toolTipWidth}px;
          min-height: ${toolTipHeight}px;
          position: absolute;
          display: none;
          padding: 12px;
          box-sizing: border-box;
          font-size: 12px;
          text-align: left;
          z-index: 1000;
          top: 12px;
          left: 12px;
          pointer-events: none;
          border: 1px solid ${isDark ? '#44403c' : '#d6d3d1'};
          border-radius: 6px;
          background: ${isDark ? '#1c1917' : '#ffffff'};
          color: ${isDark ? '#fafaf9' : '#0c0a09'};
          box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.2);
          backdrop-filter: blur(8px);
          line-height: 1.4;
        `;
        chartContainerRef.current.appendChild(toolTip);

        // 마우스 이동 이벤트 핸들러
        chart.current.subscribeCrosshairMove((param: any) => {
          if (
            param.point === undefined ||
            !param.time ||
            param.point.x < 0 ||
            param.point.x > chartContainerRef.current!.clientWidth ||
            param.point.y < 0 ||
            param.point.y > height
          ) {
            toolTip.style.display = 'none';
          } else {
            const data = param.seriesData.get(series.current);
            if (data) {
              // 날짜/시간 포맷
              const date = new Date(typeof param.time === 'number' ? param.time * 1000 : param.time);
              let timeStr = '';
              
              if (chartType === 'tick' || chartType === 'minute') {
                timeStr = date.toLocaleString('ko-KR', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: false
                });
              } else {
                timeStr = date.toLocaleDateString('ko-KR', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric'
                });
              }

              // 가격 정보 포맷 (한국어 천 단위 구분)
              const formatPrice = (price: number) => {
                return new Intl.NumberFormat('ko-KR').format(price) + '원';
              };

              // 등락 계산
              const change = data.close - data.open;
              const changePercent = ((change / data.open) * 100).toFixed(2);
              const changeColor = change >= 0 ? '#22c55e' : '#ef4444';
              const changeSign = change >= 0 ? '+' : '';

              toolTip.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 6px; font-size: 13px;">${stockName || symbol}</div>
                <div style="margin-bottom: 8px; font-size: 11px; color: #6b7280;">${timeStr}</div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-bottom: 8px;">
                  <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280;">시가:</span>
                    <span style="font-weight: 500;">${formatPrice(data.open)}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280;">고가:</span>
                    <span style="color: #22c55e; font-weight: 500;">${formatPrice(data.high)}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280;">저가:</span>
                    <span style="color: #ef4444; font-weight: 500;">${formatPrice(data.low)}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280;">종가:</span>
                    <span style="color: ${changeColor}; font-weight: bold;">${formatPrice(data.close)}</span>
                  </div>
                </div>
                
                <div style="padding-top: 8px; border-top: 1px solid ${isDark ? '#374151' : '#e5e7eb'};">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #6b7280;">등락:</span>
                    <div style="text-align: right;">
                      <div style="color: ${changeColor}; font-weight: bold; font-size: 13px;">
                        ${changeSign}${formatPrice(Math.abs(change))}
                      </div>
                      <div style="color: ${changeColor}; font-size: 11px;">
                        ${changeSign}${changePercent}%
                      </div>
                    </div>
                  </div>
                </div>
              `;

              toolTip.style.display = 'block';

              // 툴팁 위치 조정 (화면 밖으로 나가지 않도록)
              const container = chartContainerRef.current!;
              let left = param.point.x + toolTipMargin;
              let top = param.point.y + toolTipMargin;

              if (left > container.clientWidth - toolTipWidth) {
                left = param.point.x - toolTipMargin - toolTipWidth;
              }

              if (top > height - toolTipHeight) {
                top = param.point.y - toolTipMargin - toolTipHeight;
              }

              toolTip.style.left = left + 'px';
              toolTip.style.top = top + 'px';
            }
          }
        });
        
        console.log('캔들스틱 시리즈 생성 완료 (v4):', !!series.current);

        // 데이터가 있으면 설정
        if (data.length > 0) {
          console.log('🔍 초기 차트 데이터 분석:', { 
            chartType, 
            timeframe, 
            원본개수: data.length, 
            첫번째원본: data[0],
            마지막원본: data[data.length - 1],
            시간형식샘플: data.slice(0, 3).map(d => ({ time: d.time, type: typeof d.time }))
          });
          
          // 차트 타입에 따른 시간 형식 처리 (실시간 데이터와 동일한 규칙 적용)
          const chartData = data.map((item, index) => {
            let timeValue = item.time;
            
            // 문자열 날짜-시간 처리 (예: "2024-08-25 09:30:00")
            if (typeof timeValue === 'string' && timeValue.includes(' ')) {
              const [date, time] = timeValue.split(' ');
              
              // 차트 타입별 시간 정규화 (실시간 데이터와 동일한 로직)
              if (chartType === 'tick' || chartType === 'minute' || chartType.includes('minute')) {
                // 분봉/틱차트: Unix timestamp (초 단위) - 실시간 데이터와 일치
                timeValue = Math.floor(new Date(timeValue).getTime() / 1000);
              } else {
                // 일봉, 주봉, 월봉, 년봉: 날짜 문자열 - 실시간 데이터와 일치
                timeValue = date;
              }
            }
            // 이미 적절한 형식인 경우 그대로 유지
            else if (typeof timeValue === 'string' && !timeValue.includes(' ')) {
              // 날짜만 있는 경우 (일봉 데이터)
              if (chartType === 'tick' || chartType === 'minute' || chartType.includes('minute')) {
                // 분봉으로 변경되었다면 Unix timestamp로 변환
                timeValue = Math.floor(new Date(timeValue + ' 09:00:00').getTime() / 1000);
              }
              // 일봉 이상인 경우 날짜 문자열 그대로 유지
            }
            else if (typeof timeValue === 'number') {
              // Unix timestamp인 경우
              if (chartType === 'daily' || chartType === 'weekly' || chartType === 'monthly' || chartType === 'yearly') {
                // 일봉 이상으로 변경되었다면 날짜 문자열로 변환
                timeValue = new Date(timeValue * 1000).toISOString().split('T')[0];
              }
              // 분봉/틱봉인 경우 Unix timestamp 그대로 유지
            }
            
            return {
              time: timeValue,
              open: item.open,
              high: item.high,
              low: item.low,
              close: item.close,
            };
          })
          // 시간순 정렬 
          .sort((a, b) => {
            if (typeof a.time === 'number' && typeof b.time === 'number') {
              return a.time - b.time;
            }
            return new Date(a.time.toString()).getTime() - new Date(b.time.toString()).getTime();
          })
          // 중복 제거는 하지 않음 - 모든 데이터 유지
          .filter((item, index, array) => {
            // 완전히 동일한 시간 값만 제거 (연속된 것만)
            if (index === 0) return true;
            return item.time !== array[index - 1].time;
          });
          
          // 초기 데이터의 시간 형식 기억 (중요!)
          if (chartData.length > 0) {
            initialDataTimeFormatRef.current = typeof chartData[0].time;
            console.log('📌 초기 데이터 시간 형식 기억:', initialDataTimeFormatRef.current);
          }
          
          console.log('📊 초기 차트 데이터 변환 완료:', {
            변환후개수: chartData.length,
            첫번째데이터: chartData[0],
            마지막데이터: chartData[chartData.length - 1],
            시간형식샘플: chartData.slice(0, 5).map(d => ({ 
              time: d.time, 
              type: typeof d.time,
              original: data[chartData.indexOf(d)]?.time 
            })),
            실제사용될형식: typeof chartData[0]?.time,
            기억된형식: initialDataTimeFormatRef.current
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
      
      // TradingView 가이드: 정리 작업
      if (realtimeUpdateIntervalRef.current) {
        clearInterval(realtimeUpdateIntervalRef.current);
        realtimeUpdateIntervalRef.current = null;
      }
      
      if (chart.current) {
        chart.current.remove();
        chart.current = null;
        series.current = null;
      }
      
      // 실시간 데이터 큐 정리
      realtimeDataQueueRef.current = [];
      initialDataTimeFormatRef.current = null;
    };
  }, [data, height, resolvedTheme, chartType, stockName]);

  // 실시간 데이터 처리 useEffect (초기 차트 로드 완료 후에만)
  useEffect(() => {
    // 초기 데이터가 없거나 차트/시리즈가 없으면 실시간 업데이트 스킵
    if (!data || data.length === 0 || !chart.current || !series.current) {
      console.log('⏳ 실시간 업데이트 대기 중 (초기 데이터 로드 중):', {
        데이터있음: !!data && data.length > 0,
        차트있음: !!chart.current,
        시리즈있음: !!series.current
      });
      return;
    }

    if (realtimeData && realtimeData.symbol === symbol) {
      console.log('🟢 실시간 업데이트 시작:', {
        symbol: realtimeData.symbol,
        초기데이터개수: data.length,
        실시간데이터: realtimeData
      });
      updateChart(realtimeData);
    }
  }, [realtimeData, symbol, updateChart, data]);

  // 실시간 업데이트 토글 함수 (외부에서 사용 가능)
  const toggleRealtimeUpdates = useCallback((enabled: boolean) => {
    isRealtimeEnabledRef.current = enabled;
    console.log('실시간 업데이트 토글:', enabled);
  }, []);

  // TradingView 가이드: Go to Realtime 버튼 이벤트 처리
  useEffect(() => {
    const handleGoToRealtime = () => {
      if (chart.current) {
        console.log('📈 Go to Realtime 버튼 클릭 - 실시간 스크롤 활성화');
        chart.current.timeScale().scrollToRealTime();
      }
    };

    const chartContainer = chartContainerRef.current;
    if (chartContainer) {
      chartContainer.addEventListener('goToRealtime', handleGoToRealtime);
      return () => {
        chartContainer.removeEventListener('goToRealtime', handleGoToRealtime);
      };
    }
  }, []);

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