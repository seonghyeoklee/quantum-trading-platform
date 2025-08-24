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

        // v4 방식으로 캔들스틱 시리즈 생성
        series.current = chart.current.addCandlestickSeries({
          upColor: '#22c55e',
          downColor: '#ef4444',
          borderDownColor: '#ef4444',
          borderUpColor: '#22c55e',
          wickDownColor: '#ef4444',
          wickUpColor: '#22c55e',
          priceFormat: {
            type: 'price',
            precision: 0,
            minMove: 1,
          },
        });

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
          console.log('차트 데이터 변환 시작:', { chartType, timeframe, 원본개수: data.length, 첫번째원본: data[0] });
          
          // 차트 타입에 따른 시간 형식 처리
          const chartData = data.map((item, index) => {
            let timeValue = item.time;
            
            if (typeof timeValue === 'string' && timeValue.includes(' ')) {
              const [date, time] = timeValue.split(' ');
              
              // 틱/분봉차트의 경우 Unix timestamp 사용, 일봉 이상은 날짜 문자열 사용
              if (chartType === 'tick' || chartType === 'minute') {
                // 분봉/틱차트: Unix timestamp (초 단위)
                timeValue = Math.floor(new Date(timeValue).getTime() / 1000);
              } else {
                // 일봉, 주봉, 월봉, 년봉: 날짜 문자열
                timeValue = date;
              }
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
          
          console.log('차트 데이터 변환 완료:', {
            변환후개수: chartData.length,
            첫번째데이터: chartData[0],
            마지막데이터: chartData[chartData.length - 1],
            시간형식샘플: chartData.slice(0, 3).map(d => d.time)
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
  }, [data, height, resolvedTheme, chartType, stockName]);

  return (
    <div className="w-full h-full">
      <div 
        ref={chartContainerRef} 
        className="w-full rounded-lg border border-border"
        style={{ height: `${height}px` }}
      />
    </div>
  );
}