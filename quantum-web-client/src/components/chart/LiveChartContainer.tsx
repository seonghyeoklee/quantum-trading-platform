'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, BarChart3, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import SimpleChart from './SimpleChart';
import ChartControls from './ChartControls';
import { CandlestickData, ChartConfig } from './types';
import { quantumApiClient } from '@/lib/services/quantum-api-client';
import { convertQuantumToChartData } from './utils';

interface LiveChartContainerProps {
  symbol: string;
  stockName?: string;
  height?: number;
  className?: string;
}

export default function LiveChartContainer({
  symbol,
  stockName,
  height = 500,
  className = ''
}: LiveChartContainerProps) {
  
  // 상태 관리
  const [chartData, setChartData] = useState<CandlestickData[]>([]);
  const [currentPrice, setCurrentPrice] = useState<any>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 차트 설정 상태
  const [chartConfig, setChartConfig] = useState<ChartConfig>({
    symbol,
    timeframe: '1M',
    showVolume: true,
    showMA: false,
    maPeriods: [5, 20]
  });

  // 차트 데이터 로딩
  const loadChartData = async (config: ChartConfig = chartConfig) => {
    try {
      console.log('📈 차트 데이터 로딩 시작:', { symbol, timeframe: config.timeframe });
      
      let chartResponse;
      
      // 🚀 새로운 통합 차트 API 사용
      let period: 'D' | 'W' | 'M' | 'Y' = 'D';
      switch (config.timeframe) {
        case '1D':
        case '5D':
          period = 'D';
          console.log('🔄 일봉 차트 API 호출 중...');
          break;
        case '1M':
        case '3M':
          period = 'W';
          console.log('🔄 주봉 차트 API 호출 중...');
          break;
        case '1Y':
          period = 'M';
          console.log('🔄 월봉 차트 API 호출 중...');
          break;
        case '5Y':
          period = 'Y';
          console.log('🔄 년봉 차트 API 호출 중...');
          break;
        default:
          period = 'D';
          console.log('🔄 기본 일봉 차트 API 호출 중...');
      }
      
      chartResponse = await quantumApiClient.getChart(symbol, period);

      console.log('📊 API 응답 받음:', chartResponse);

      // 데이터 변환
      const convertedData = convertQuantumToChartData(chartResponse);
      console.log('✅ 차트 데이터 변환 완료:', { 
        originalDataCount: chartResponse?.output2?.length || 0,
        convertedDataCount: convertedData.length,
        sampleData: convertedData.slice(0, 2)
      });
      
      setChartData(convertedData);
      setError(null);
      
    } catch (err) {
      console.error('❌ 차트 데이터 로딩 실패:', err);
      setError('차트 데이터를 불러올 수 없습니다.');
    }
  };

  // 현재가 로딩
  const loadCurrentPrice = async () => {
    try {
      console.log('💰 현재가 로딩 시작:', symbol);
      
      const priceResponse = await quantumApiClient.getCurrentPrice(symbol);
      console.log('✅ 현재가 로딩 완료:', priceResponse.output?.stck_prpr);
      
      setCurrentPrice(priceResponse.output);
      
    } catch (err) {
      console.error('❌ 현재가 로딩 실패:', err);
      // 현재가 로딩 실패는 치명적이지 않으므로 에러 설정하지 않음
    }
  };

  // 초기 데이터 로딩
  useEffect(() => {
    const loadAllData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        await Promise.all([
          loadChartData(),
          loadCurrentPrice()
        ]);
        
      } catch (err) {
        console.error('❌ 데이터 로딩 실패:', err);
        setError('데이터를 불러올 수 없습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    loadAllData();
  }, [symbol]);

  // 차트 설정 변경 시 데이터 다시 로딩
  useEffect(() => {
    if (!isLoading) {
      loadChartData(chartConfig);
    }
  }, [chartConfig.timeframe]);

  // 차트 설정 변경 핸들러
  const handleConfigChange = (newConfig: ChartConfig) => {
    setChartConfig(newConfig);
  };

  // 새로고침 핸들러
  const handleRefresh = async () => {
    try {
      setIsRefreshing(true);
      setError(null);
      
      await Promise.all([
        loadChartData(),
        loadCurrentPrice()
      ]);
      
    } catch (err) {
      console.error('❌ 새로고침 실패:', err);
      setError('데이터를 새로고침할 수 없습니다.');
    } finally {
      setIsRefreshing(false);
    }
  };

  // 가격 변화 계산
  const getPriceInfo = () => {
    if (!currentPrice) return null;
    
    const current = parseFloat(currentPrice.stck_prpr || 0);
    const change = parseFloat(currentPrice.prdy_vrss || 0);
    const changePercent = parseFloat(currentPrice.prdy_ctrt || 0);
    const sign = currentPrice.prdy_vrss_sign || '3';
    
    return {
      current,
      change,
      changePercent,
      isPositive: sign === '2', // 2: 상승, 4: 하락, 3: 보합
      isNegative: sign === '4',
      name: currentPrice.hts_kor_isnm || stockName || symbol
    };
  };

  const priceInfo = getPriceInfo();

  // 로딩 상태
  if (isLoading) {
    return (
      <Card className={`w-full ${className}`}>
        <CardContent className="flex items-center justify-center p-8" style={{ height }}>
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-sm text-muted-foreground">차트 데이터 로딩 중...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <Card className={`w-full ${className}`}>
        <CardContent className="flex items-center justify-center p-8" style={{ height }}>
          <div className="text-center">
            <AlertCircle className="w-8 h-8 mx-auto mb-4 text-destructive" />
            <p className="text-sm text-destructive mb-4">{error}</p>
            <Button variant="outline" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              다시 시도
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            {/* 종목 정보 */}
            <div className="flex items-center gap-3">
              <CardTitle className="text-xl font-bold">
                {priceInfo?.name || stockName || symbol}
              </CardTitle>
              <Badge variant="secondary" className="text-xs font-mono">
                {symbol}
              </Badge>
            </div>
            
            {/* 가격 정보 */}
            {priceInfo && (
              <div className="flex items-center gap-4">
                <span className="text-3xl font-bold">
                  ₩{priceInfo.current.toLocaleString()}
                </span>
                
                {(priceInfo.isPositive || priceInfo.isNegative) && (
                  <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                    priceInfo.isPositive 
                      ? 'bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400' 
                      : 'bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400'
                  }`}>
                    {priceInfo.isPositive ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    
                    <span>
                      {priceInfo.change >= 0 ? '+' : ''}{priceInfo.change.toLocaleString()}
                    </span>
                    <span>
                      ({priceInfo.changePercent >= 0 ? '+' : ''}{priceInfo.changePercent}%)
                    </span>
                  </div>
                )}
                
                {!priceInfo.isPositive && !priceInfo.isNegative && (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium bg-gray-50 text-gray-600 dark:bg-gray-900 dark:text-gray-400">
                    <Minus className="w-4 h-4" />
                    <span>변동없음</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 차트 상태 표시 */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <BarChart3 className="w-4 h-4" />
            <span>{chartData.length}개 데이터</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 차트 컨트롤 */}
        <ChartControls
          config={chartConfig}
          onConfigChange={handleConfigChange}
          onRefresh={handleRefresh}
          isLoading={isRefreshing}
        />

        {/* 차트 */}
        <div className="w-full border border-border rounded-lg overflow-hidden bg-card">
          <SimpleChart
            data={chartData}
            config={chartConfig}
            height={height - 150} // 헤더와 컨트롤 높이 제외
            className="w-full"
          />
        </div>

        {/* 차트 정보 푸터 */}
        {chartData.length > 0 && (
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t border-border">
            <div className="flex items-center gap-4">
              <span>기간: {chartConfig.timeframe}</span>
              <span>거래량: {chartConfig.showVolume ? '표시' : '숨김'}</span>
              {chartConfig.showMA && (
                <span>이동평균: {chartConfig.maPeriods.join(', ')}일</span>
              )}
            </div>
            <span>
              실시간 업데이트: {new Date().toLocaleTimeString('ko-KR')}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
