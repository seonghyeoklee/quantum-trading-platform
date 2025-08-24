'use client';

import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import TradingChart from './TradingChart';
import ChartControls from './ChartControls';
import StockSearch from './StockSearch';
import { ChartTimeframe, ChartType, StockInfo, ChartState } from './ChartTypes';
import { kiwoomApiService } from '@/lib/api/kiwoom-service';
import { KiwoomStockInfo } from '@/lib/api/kiwoom-types';

interface ChartContainerProps {
  className?: string;
}

// 종목 정보 (6자리 종목코드 사용, 실제 API 응답 기준)
const stocksInfo: Record<string, StockInfo> = {
  // 대형주 (Large Cap)
  '005930': { symbol: '005930', name: '삼성전자', price: 70500, change: 0, changePercent: 0, market: 'KOSPI' },
  '000660': { symbol: '000660', name: 'SK하이닉스', price: 128000, change: 0, changePercent: 0, market: 'KOSPI' },
  '207940': { symbol: '207940', name: '삼성바이오로직스', price: 710000, change: 0, changePercent: 0, market: 'KOSPI' },
  '005380': { symbol: '005380', name: '현대차', price: 248000, change: 0, changePercent: 0, market: 'KOSPI' },
  '051910': { symbol: '051910', name: 'LG화학', price: 400000, change: 0, changePercent: 0, market: 'KOSPI' },
  
  // IT/테크 (IT/Tech)
  '035420': { symbol: '035420', name: 'NAVER', price: 221500, change: 0, changePercent: 0, market: 'KOSPI' },
  '035720': { symbol: '035720', name: '카카오', price: 65300, change: 0, changePercent: 0, market: 'KOSPI' },
  '036570': { symbol: '036570', name: 'NCsoft', price: 285000, change: 0, changePercent: 0, market: 'KOSPI' },
  '018260': { symbol: '018260', name: '삼성에스디에스', price: 142000, change: 0, changePercent: 0, market: 'KOSPI' },
  
  // 금융 (Financial)
  '055550': { symbol: '055550', name: '신한지주', price: 49200, change: 0, changePercent: 0, market: 'KOSPI' },
  '105560': { symbol: '105560', name: 'KB금융', price: 74600, change: 0, changePercent: 0, market: 'KOSPI' },
  '086790': { symbol: '086790', name: '하나금융지주', price: 64100, change: 0, changePercent: 0, market: 'KOSPI' },
  
  // 코스닥 (KOSDAQ)
  '091990': { symbol: '091990', name: '셀트리온헬스케어', price: 89500, change: 0, changePercent: 0, market: 'KOSDAQ' },
  '068270': { symbol: '068270', name: '셀트리온', price: 210000, change: 0, changePercent: 0, market: 'KOSPI' },
  '326030': { symbol: '326030', name: 'SK바이오팜', price: 112000, change: 0, changePercent: 0, market: 'KOSPI' },
  '028300': { symbol: '028300', name: 'HLB', price: 42750, change: 0, changePercent: 0, market: 'KOSDAQ' },
  '196170': { symbol: '196170', name: '알테오젠', price: 98600, change: 0, changePercent: 0, market: 'KOSDAQ' },
  
  // 엔터테인먼트 (Entertainment)
  '352820': { symbol: '352820', name: '하이브', price: 199000, change: 0, changePercent: 0, market: 'KOSPI' },
  '041510': { symbol: '041510', name: 'SM', price: 82900, change: 0, changePercent: 0, market: 'KOSDAQ' },
  '122870': { symbol: '122870', name: 'YG엔터테인먼트', price: 44700, change: 0, changePercent: 0, market: 'KOSDAQ' },
};

export default function ChartContainer({ className }: ChartContainerProps) {
  const [currentTimeframe, setCurrentTimeframe] = useState<ChartTimeframe>('1M');
  const [currentChartType, setCurrentChartType] = useState<ChartType>('daily');
  const [currentSymbol, setCurrentSymbol] = useState<string>('005930');
  const [selectedStock, setSelectedStock] = useState<KiwoomStockInfo | null>(null);
  const [chartState, setChartState] = useState<ChartState>({
    data: [],
    loading: false,
    error: null,
  });
  
  // API 호출 중복 방지를 위한 ref
  const loadingRef = useRef<boolean>(false);

  // 현재 종목 정보
  const currentStockInfo = useMemo(() => {
    // 검색으로 선택된 종목이 있으면 우선 사용
    if (selectedStock) {
      const basePrice = parseInt(selectedStock.lastPrice) || 0;
      
      // 차트 데이터가 있으면 최신 가격 정보 업데이트
      if (chartState.data.length > 0) {
        const latestData = chartState.data[chartState.data.length - 1];
        const previousData = chartState.data[chartState.data.length - 2];
        
        const price = latestData.close;
        const change = previousData ? latestData.close - previousData.close : latestData.close - basePrice;
        const changePercent = previousData 
          ? (change / previousData.close) * 100 
          : basePrice > 0 ? ((latestData.close - basePrice) / basePrice) * 100 : 0;
        
        return {
          symbol: selectedStock.code,
          name: selectedStock.name,
          price,
          change,
          changePercent,
          market: selectedStock.marketName || 'KOSPI',
        };
      }
      
      return {
        symbol: selectedStock.code,
        name: selectedStock.name,
        price: basePrice,
        change: 0,
        changePercent: 0,
        market: selectedStock.marketName || 'KOSPI',
      };
    }
    
    // 기본 하드코딩된 종목 정보 사용
    const baseInfo = stocksInfo[currentSymbol] || stocksInfo['005930'];
    
    // 차트 데이터가 있으면 최신 가격 정보 업데이트
    if (chartState.data.length > 0) {
      const latestData = chartState.data[chartState.data.length - 1];
      const previousData = chartState.data[chartState.data.length - 2];
      
      const price = latestData.close;
      const change = previousData ? latestData.close - previousData.close : 0;
      const changePercent = previousData ? (change / previousData.close) * 100 : 0;
      
      return {
        ...baseInfo,
        price,
        change,
        changePercent,
      };
    }
    
    return baseInfo;
  }, [currentSymbol, chartState.data, selectedStock]);

  // 컴포넌트 마운트 및 종목/시간대/차트타입 변경 시 데이터 로드
  useEffect(() => {
    let isCancelled = false;
    const requestKey = `${currentSymbol}-${currentTimeframe}-${currentChartType}`;

    const loadChartData = async () => {
      // 이미 로딩 중이거나 동일한 요청이면 중복 호출 방지
      if (loadingRef.current) {
        console.log('이미 API 호출 중입니다. 중복 호출 방지');
        return;
      }

      console.log(`차트 데이터 로드 시작: ${requestKey}`);
      
      loadingRef.current = true;
      setChartState(prev => ({ ...prev, loading: true, error: null }));

      // 300ms 디바운싱 - 빠른 연속 호출 방지
      await new Promise(resolve => setTimeout(resolve, 300));
      
      if (isCancelled) return;

      try {
        // 차트 타입이 사용자에 의해 선택된 경우 직접 타입으로 조회
        const data = await kiwoomApiService.getChartDataByType(currentSymbol, currentChartType, currentTimeframe);
        
        if (!isCancelled) {
          console.log(`차트 데이터 로드 완료: ${data.length}개`);
          
          setChartState(prev => ({
            ...prev,
            data,
            loading: false,
            error: null,
            lastUpdated: new Date(),
          }));
        }

      } catch (error) {
        if (!isCancelled) {
          console.error('차트 데이터 로드 실패:', error);
          
          setChartState(prev => ({
            ...prev,
            data: [],
            loading: false,
            error: error instanceof Error ? error.message : '데이터 로드에 실패했습니다.',
          }));
        }
      } finally {
        if (!isCancelled) {
          loadingRef.current = false;
        }
      }
    };

    loadChartData();

    return () => {
      isCancelled = true;
      loadingRef.current = false;
    };
  }, [currentSymbol, currentTimeframe, currentChartType]);

  // 수동 새로고침용 함수
  const loadChartData = useCallback(async () => {
    setChartState(prev => ({ ...prev, loading: true, error: null }));

    try {
      console.log(`수동 차트 데이터 로드: ${currentSymbol}, ${currentChartType}, ${currentTimeframe}`);
      
      const data = await kiwoomApiService.getChartDataByType(currentSymbol, currentChartType, currentTimeframe);
      
      console.log(`수동 차트 데이터 로드 완료: ${data.length}개`);
      
      setChartState(prev => ({
        ...prev,
        data,
        loading: false,
        error: null,
        lastUpdated: new Date(),
      }));

    } catch (error) {
      console.error('수동 차트 데이터 로드 실패:', error);
      
      setChartState(prev => ({
        ...prev,
        data: [],
        loading: false,
        error: error instanceof Error ? error.message : '데이터 로드에 실패했습니다.',
      }));
    }
  }, [currentSymbol, currentChartType, currentTimeframe]);

  const handleTimeframeChange = useCallback((timeframe: ChartTimeframe) => {
    setCurrentTimeframe(timeframe);
  }, []);

  const handleChartTypeChange = useCallback((chartType: ChartType) => {
    setCurrentChartType(chartType);
  }, []);

  const handleStockChange = useCallback((symbol: string) => {
    setCurrentSymbol(symbol);
  }, []);

  const handleStockSelect = useCallback((stock: KiwoomStockInfo) => {
    console.log('선택된 종목:', stock);
    setCurrentSymbol(stock.code);
    setSelectedStock(stock);
  }, []);

  // 하단 시장 데이터 계산
  const marketData = useMemo(() => {
    if (chartState.data.length === 0) {
      return {
        openPrice: 0,
        highPrice: 0,
        lowPrice: 0,
        volume: 0,
      };
    }

    const data = chartState.data;
    const openPrice = data[0]?.open || 0;
    const highPrice = Math.max(...data.map(d => d.high));
    const lowPrice = Math.min(...data.map(d => d.low));
    const volume = data.reduce((sum, d) => sum + (d.volume || 0), 0);

    return { openPrice, highPrice, lowPrice, volume };
  }, [chartState.data]);

  return (
    <div className={`flex flex-col h-full ${className || ''}`}>
      {/* 종목 검색 */}
      <div className="p-4 border-b border-border bg-card">
        <StockSearch
          onStockSelect={handleStockSelect}
          className="w-full"
        />
      </div>

      {/* 차트 컨트롤 */}
      <ChartControls
        currentTimeframe={currentTimeframe}
        currentChartType={currentChartType}
        currentStock={currentStockInfo}
        onTimeframeChange={handleTimeframeChange}
        onChartTypeChange={handleChartTypeChange}
        onStockChange={handleStockChange}
      />
      
      {/* 메인 차트 영역 */}
      <div className="flex-1 p-6 bg-background relative">
        {chartState.loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-muted-foreground">차트 데이터 로딩 중...</span>
            </div>
          </div>
        )}

        {chartState.error && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <div className="text-center">
              <div className="text-red-500 text-sm mb-2">❌ 데이터 로드 실패</div>
              <div className="text-xs text-muted-foreground mb-4">{chartState.error}</div>
              <button 
                onClick={loadChartData}
                className="px-3 py-1 text-xs bg-primary text-primary-foreground rounded hover:bg-primary/90"
              >
                다시 시도
              </button>
            </div>
          </div>
        )}

        <div className="w-full h-full">
          {console.log('TradingChart에 전달할 데이터:', {
            데이터수: chartState.data.length,
            샘플데이터: chartState.data.slice(0, 2),
            로딩상태: chartState.loading,
            에러상태: chartState.error
          })}
          <TradingChart
            data={chartState.data}
            height={400}
            symbol={currentSymbol}
            timeframe={currentTimeframe}
            chartType={currentChartType}
            stockName={currentStockInfo.name}
          />
        </div>
      </div>
      
      {/* 하단 시장 데이터 */}
      <div className="p-6 border-t border-border bg-muted">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">시가</div>
            <div className="text-sm font-medium">
              {marketData.openPrice > 0 ? marketData.openPrice.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">고가</div>
            <div className="text-sm font-medium text-bull">
              {marketData.highPrice > 0 ? marketData.highPrice.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">저가</div>
            <div className="text-sm font-medium text-bear">
              {marketData.lowPrice > 0 ? marketData.lowPrice.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">거래량</div>
            <div className="text-sm font-medium">
              {marketData.volume > 0 ? marketData.volume.toLocaleString('ko-KR') : '-'}
            </div>
          </div>
        </div>

        {/* 데이터 상태 정보 */}
        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <div className="flex items-center space-x-4">
            <span>키움증권 API 연동</span>
            {chartState.lastUpdated && (
              <span>마지막 업데이트: {chartState.lastUpdated.toLocaleTimeString('ko-KR')}</span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${chartState.error ? 'bg-red-500' : chartState.loading ? 'bg-yellow-500' : 'bg-green-500'}`} />
            <span>{chartState.error ? '연결 실패' : chartState.loading ? '로딩 중' : '연결됨'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}