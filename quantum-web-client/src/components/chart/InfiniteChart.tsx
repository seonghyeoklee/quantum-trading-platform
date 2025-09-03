'use client';

import { useEffect, useLayoutEffect, useRef, useState, useCallback } from 'react';
import { useTheme } from 'next-themes';
import { CandlestickData } from './types';
import { quantumApiClient } from '@/lib/services/quantum-api-client';
import { convertQuantumToChartData } from './utils';

interface InfiniteChartProps {
  symbol: string;
  stockName?: string;
  height?: number;
  className?: string;
}

// Datafeed 클래스 - 데모 코드 패턴 적용
class QuantumDatafeed {
  private symbol: string;
  private _earliestDate: Date;
  private _data: CandlestickData[];

  constructor(symbol: string) {
    this.symbol = symbol;
    // 1년 전부터 시작
    this._earliestDate = new Date();
    this._earliestDate.setFullYear(this._earliestDate.getFullYear() - 1);
    this._data = [];
  }

  async getBars(numberOfExtraBars: number): Promise<CandlestickData[]> {
    try {
      console.log(`📊 ${numberOfExtraBars}개 추가 데이터 로드 중...`);
      
      // 가장 오래된 날짜에서 더 과거 데이터 요청
      const endDate = this._earliestDate.toISOString().slice(0, 10).replace(/-/g, '');
      const startDate = (() => {
        const date = new Date(this._earliestDate);
        // numberOfExtraBars에 비례해서 기간 설정 (일주일당 1개 데이터)
        date.setDate(date.getDate() - (numberOfExtraBars * 7));
        return date.toISOString().slice(0, 10).replace(/-/g, '');
      })();

      const chartResponse = await quantumApiClient.getChart(this.symbol, 'W', startDate, endDate);
      const historicalData = convertQuantumToChartData(chartResponse);
      
      if (historicalData.length > 0) {
        // 새로운 데이터를 기존 데이터 앞에 추가 (데모와 동일한 패턴)
        this._data = [...historicalData, ...this._data];
        this._earliestDate = new Date(Number(historicalData[0].time) * 1000);
        console.log(`✅ ${historicalData.length}개 과거 데이터 추가됨`);
      }

      return this._data;
    } catch (err) {
      console.error('❌ 추가 데이터 로드 실패:', err);
      return this._data;
    }
  }

  async getInitialData(): Promise<CandlestickData[]> {
    try {
      console.log('🚀 초기 데이터 로딩...');
      
      // 최근 1년치 주봉 데이터
      const endDate = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const startDate = this._earliestDate.toISOString().slice(0, 10).replace(/-/g, '');

      const chartResponse = await quantumApiClient.getChart(this.symbol, 'W', startDate, endDate);
      const initialData = convertQuantumToChartData(chartResponse);
      
      this._data = initialData;
      if (initialData.length > 0) {
        this._earliestDate = new Date(Number(initialData[0].time) * 1000);
        console.log(`✅ 초기 데이터 ${initialData.length}개 로드 완료`);
      }

      return this._data;
    } catch (err) {
      console.error('❌ 초기 데이터 로드 실패:', err);
      return [];
    }
  }
}

export default function InfiniteChart({ 
  symbol, 
  stockName,
  height = 500,
  className = ''
}: InfiniteChartProps) {
  // 컴포넌트 인스턴스 고유 ID
  const instanceId = useRef(Math.random().toString(36).substr(2, 9));
  
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const seriesRef = useRef<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const datafeedRef = useRef<QuantumDatafeed | null>(null);
  const { resolvedTheme } = useTheme();
  
  console.log(`🎯 InfiniteChart 인스턴스 ${instanceId.current} 생성됨`);
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPrice, setCurrentPrice] = useState<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any

  // 차트 초기화 (데모 코드 구조 적용)
  const initChart = useCallback(async () => {
    console.log(`🚀 [${instanceId.current}] initChart 호출됨, ref 상태:`, !!chartContainerRef.current);
    
    if (!chartContainerRef.current) {
      console.error('❌ 차트 컨테이너 없음 - initChart에서 확인');
      return;
    }

    const container = chartContainerRef.current;
    console.log('📐 컨테이너 크기:', {
      width: container.clientWidth,
      height: container.clientHeight,
      offsetWidth: container.offsetWidth,
      offsetHeight: container.offsetHeight
    });

    try {
      setIsLoading(true);
      setError(null);

      // 기존 차트 제거 (중복 생성 방지)
      if (chartRef.current) {
        console.log('🗑️ 기존 차트 제거 중...');
        chartRef.current.remove();
        chartRef.current = null;
      }
      
      // 기존 시리즈 참조도 초기화
      if (seriesRef.current) {
        seriesRef.current = null;
      }
      
      // 컨테이너 내용 완전히 비우기 (혹시 남은 차트 요소 제거)
      if (container.firstChild) {
        console.log('🧹 컨테이너 내용 완전 정리 중...');
        container.innerHTML = '';
      }

      console.log('🎨 차트 초기화 시작...');

      // Lightweight Charts v5.0 동적 import (데모와 동일)
      const { createChart, ColorType, CandlestickSeries } = await import('lightweight-charts');
      
      const isDark = resolvedTheme === 'dark';

      // 차트 옵션 (v5.0 데모와 동일한 간단한 스타일)
      const chartOptions = {
        layout: {
          textColor: isDark ? '#f8fafc' : 'black',
          background: { 
            type: ColorType.Solid, 
            color: isDark ? '#0f172a' : 'white' 
          },
        },
      };

      // 차트 생성
      chartRef.current = createChart(container, chartOptions);

      // 캔들스틱 시리즈 추가 (v5.0 데모와 정확히 동일한 방식)
      seriesRef.current = chartRef.current.addSeries(CandlestickSeries, {
        upColor: '#26a69a',      // 데모와 동일한 색상
        downColor: '#ef5350',    // 데모와 동일한 색상
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });

      // 데이터피드 초기화
      datafeedRef.current = new QuantumDatafeed(symbol);

      // 현재가 정보 로드
      console.log(`📡 [${instanceId.current}] 현재가 정보 로드 시작: ${symbol}`);
      const priceResponse = await quantumApiClient.getCurrentPrice(symbol);
      setCurrentPrice(priceResponse.output);
      console.log(`✅ [${instanceId.current}] 현재가 정보 로드 완료:`, priceResponse.output);

      // 초기 데이터 로드 (데모의 200개와 유사)
      console.log(`📊 [${instanceId.current}] 초기 데이터 로드 시작...`);
      const initialData = await datafeedRef.current.getInitialData();
      console.log(`📊 [${instanceId.current}] 초기 데이터 로드 완료:`, {
        데이터개수: initialData.length,
        첫번째: initialData[0],
        마지막: initialData[initialData.length - 1]
      });
      
      if (initialData.length > 0) {
        seriesRef.current.setData(initialData);
        console.log('✅ 차트에 데이터 설정 완료');
      } else {
        console.error('❌ 초기 데이터가 없습니다!');
        setError('데이터를 불러올 수 없습니다.');
        setIsLoading(false);
        return;
      }

      // 무한 스크롤 설정 (데모와 정확히 동일한 로직)
      chartRef.current.timeScale().subscribeVisibleLogicalRangeChange((logicalRange: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
        if (logicalRange && logicalRange.from < 10) {
          // load more data - 데모와 동일한 로직
          const numberBarsToLoad = 50 - logicalRange.from;
          console.log(`🔄 무한 스크롤 트리거: from=${logicalRange.from}, 로드할 개수=${numberBarsToLoad}`);
          if (datafeedRef.current) {
            datafeedRef.current.getBars(numberBarsToLoad).then(data => {
              setTimeout(() => {
                if (seriesRef.current) {
                  console.log(`📊 ${data.length}개 데이터로 차트 업데이트`);
                  seriesRef.current.setData(data);
                }
              }, 250); // add a loading delay - 데모와 동일
            }).catch(err => {
              console.error('❌ 무한 스크롤 데이터 로드 실패:', err);
            });
          }
        }
      });

      // 차트 크기 조정 핸들러
      const handleResize = () => {
        if (chartRef.current && chartContainerRef.current) {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth,
          });
        }
      };

      window.addEventListener('resize', handleResize);
      setIsLoading(false);

      console.log('✅ Infinite Chart 초기화 완료');

    } catch (err) {
      console.error(`❌ [${instanceId.current}] 차트 초기화 실패:`, err);
      setError(`차트를 불러올 수 없습니다. (인스턴스: ${instanceId.current})`);
      setIsLoading(false);
    }
  }, [symbol, resolvedTheme, height]);

  // 컴포넌트 마운트 시 차트 초기화 (한 번만 실행)
  useLayoutEffect(() => {
    console.log(`🔧 [${instanceId.current}] useLayoutEffect 실행 (최초 1회), ref 상태:`, !!chartContainerRef.current);
    
    if (chartContainerRef.current) {
      console.log(`🎯 [${instanceId.current}] DOM ref 준비됨, 차트 초기화 시작`);
      initChart();
    } else {
      // ref가 아직 준비되지 않은 경우 짧은 지연 후 재시도
      const timer = setTimeout(() => {
        if (chartContainerRef.current) {
          console.log(`🎯 [${instanceId.current}] 지연 후 ref 준비됨, 차트 초기화 시작`);
          initChart();
        } else {
          console.error(`❌ [${instanceId.current}] chartContainerRef.current가 여전히 null입니다!`);
        }
      }, 50);
      
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 빈 의존성 배열로 한 번만 실행

  // 클린업 전용 useEffect
  useEffect(() => {
    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, []);

  return (
    <div className={className}>
      {/* 주식 정보 헤더 */}
      {currentPrice && (
        <div className="mb-4 p-4 bg-card rounded-lg border">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">{currentPrice.hts_kor_isnm || stockName || symbol}</h2>
              <p className="text-sm text-muted-foreground">{symbol}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">₩{parseInt(currentPrice.stck_prpr || 0).toLocaleString()}</div>
              <div className={`text-sm ${
                currentPrice.prdy_vrss_sign === '2' ? 'text-red-600' : 
                currentPrice.prdy_vrss_sign === '4' ? 'text-blue-600' : 'text-gray-600'
              }`}>
                {currentPrice.prdy_vrss_sign === '2' ? '+' : currentPrice.prdy_vrss_sign === '4' ? '-' : ''}
                {Math.abs(parseInt(currentPrice.prdy_vrss || 0)).toLocaleString()} 
                ({currentPrice.prdy_vrss_sign === '2' ? '+' : currentPrice.prdy_vrss_sign === '4' ? '-' : ''}
                {Math.abs(parseFloat(currentPrice.prdy_ctrt || 0)).toFixed(2)}%)
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 차트 컨테이너 - 항상 렌더링 */}
      <div className="relative">
        <div 
          ref={chartContainerRef} 
          className="w-full rounded-lg border border-border bg-card"
          style={{ 
            height: `${height}px`,
            minHeight: `${height}px`,
            width: '100%',
            minWidth: '300px',
            display: 'block',
            position: 'relative'
          }}
          id={`chart-container-${instanceId.current}`}
        />
        
        {/* 로딩 오버레이 */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-card/80 rounded-lg">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
              <p className="text-sm text-muted-foreground">차트 로딩 중...</p>
            </div>
          </div>
        )}
        
        {/* 에러 오버레이 */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-card/80 rounded-lg">
            <div className="text-center">
              <div className="text-destructive mb-2 text-2xl">⚠️</div>
              <p className="text-sm text-destructive mb-2">{error}</p>
              <button 
                onClick={() => initChart()} 
                className="text-xs text-primary hover:underline"
              >
                다시 시도
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* 안내 메시지 */}
      <div className="mt-2 text-xs text-muted-foreground text-center">
        📊 왼쪽으로 스크롤하면 과거 데이터가 자동으로 로드됩니다 (Infinite History 데모와 동일한 로직)
      </div>
    </div>
  );
}