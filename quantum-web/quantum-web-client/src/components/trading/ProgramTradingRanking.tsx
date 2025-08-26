'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  getProgramTradingRanking, 
  parseProgramTradingData,
  formatPrice,
  formatVolume,
  DEFAULT_REQUESTS 
} from '@/lib/api/program-trading-api';
import { ProgramTradingData } from '@/lib/api/program-trading-types';
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  RefreshCw, 
  Crown,
  Activity
} from 'lucide-react';

interface ProgramTradingRankingProps {
  onStockClick?: (stockCode: string, stockName: string) => void;
  maxItems?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
  className?: string;
}

export default function ProgramTradingRanking({
  onStockClick,
  maxItems = 10,
  autoRefresh = true,
  refreshInterval = 30000, // 30초
  className
}: ProgramTradingRankingProps) {
  const [data, setData] = useState<ProgramTradingData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [market, setMarket] = useState<'KOSPI' | 'KOSDAQ'>('KOSPI');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // 데이터 로드 함수 (단일 조회)
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const request = market === 'KOSPI' 
        ? DEFAULT_REQUESTS.KOSPI_BUY_AMOUNT 
        : DEFAULT_REQUESTS.KOSDAQ_BUY_AMOUNT;

      // 단일 요청만 실행
      const response = await getProgramTradingRanking(request, 'N');
      const parsedData = parseProgramTradingData(response.Body.prm_netprps_upper_50);
      
      console.log(`${parsedData.length}개 데이터 로드 완료`);
      
      // maxItems만큼만 표시
      setData(parsedData.slice(0, maxItems));
      setLastUpdated(new Date());
    } catch (err) {
      console.error('프로그램 거래 데이터 로드 실패:', err);
      setError(err instanceof Error ? err.message : '데이터 로드 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [market, maxItems]);

  // 컴포넌트 마운트 시 데이터 로드
  useEffect(() => {
    loadData();
  }, [loadData]);

  // 자동 새로고침
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, loadData]);

  // 종목 클릭 핸들러
  const handleStockClick = (item: ProgramTradingData) => {
    onStockClick?.(item.stockCode, item.stockName);
  };

  // 수동 새로고침
  const handleRefresh = () => {
    loadData();
  };

  // 등락 색상 결정
  const getChangeColor = (changeSign: string) => {
    switch (changeSign) {
      case 'up': return 'text-red-600';
      case 'down': return 'text-blue-600';
      default: return 'text-muted-foreground';
    }
  };

  // 등락 아이콘
  const getChangeIcon = (changeSign: string) => {
    switch (changeSign) {
      case 'up': return <TrendingUp className="w-3 h-3" />;
      case 'down': return <TrendingDown className="w-3 h-3" />;
      default: return null;
    }
  };

  // 순위별 크라운 색상 (작은 사이즈)
  const getRankBadge = (rank: number) => {
    if (rank === 1) return <Crown className="w-2.5 h-2.5 fill-yellow-400 text-yellow-600" />;
    if (rank === 2) return <Crown className="w-2.5 h-2.5 fill-gray-400 text-gray-600" />;
    if (rank === 3) return <Crown className="w-2.5 h-2.5 fill-orange-400 text-orange-600" />;
    return <span className="text-xs font-medium text-muted-foreground text-center w-4">{rank}</span>;
  };

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center">
            <BarChart3 className="w-4 h-4 mr-2" />
            프로그램 순매수 상위
          </CardTitle>
          <div className="flex items-center space-x-2">
            {/* 시장 선택 */}
            <div className="flex">
              <Button
                variant={market === 'KOSPI' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMarket('KOSPI')}
                className="text-xs px-2 py-1 h-auto rounded-r-none"
              >
                코스피
              </Button>
              <Button
                variant={market === 'KOSDAQ' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMarket('KOSDAQ')}
                className="text-xs px-2 py-1 h-auto rounded-l-none"
              >
                코스닥
              </Button>
            </div>
            
            {/* 새로고침 버튼 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
              className="p-1"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* 마지막 업데이트 시간 */}
        {lastUpdated && (
          <div className="text-xs text-muted-foreground flex items-center">
            <Activity className="w-3 h-3 mr-1" />
            {lastUpdated.toLocaleTimeString('ko-KR')} 업데이트
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        {error && (
          <div className="p-4 text-center">
            <p className="text-sm text-red-600">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="mt-2 text-xs"
            >
              다시 시도
            </Button>
          </div>
        )}

        {loading && data.length === 0 && (
          <div className="p-4">
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="animate-pulse flex items-center space-x-3 py-2">
                  <div className="w-4 h-4 bg-muted rounded"></div>
                  <div className="flex-1">
                    <div className="h-3 bg-muted rounded w-20 mb-1"></div>
                    <div className="h-2 bg-muted rounded w-16"></div>
                  </div>
                  <div className="text-right">
                    <div className="h-3 bg-muted rounded w-12 mb-1"></div>
                    <div className="h-2 bg-muted rounded w-8"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!loading && data.length > 0 && (
          <div className="max-h-96 overflow-y-auto">
            {data.map((item, index) => (
              <div
                key={`${item.stockCode}-${index}`}
                onClick={() => handleStockClick(item)}
                className="flex items-center space-x-3 px-3 py-2 hover:bg-muted/50 cursor-pointer transition-colors border-b border-border last:border-b-0"
              >
                {/* 순위 */}
                <div className="w-5 flex justify-center items-center">
                  {getRankBadge(item.rank)}
                </div>

                {/* 종목 정보 */}
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm truncate">
                    {item.stockName}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {item.stockCode}
                  </div>
                </div>

                {/* 현재가 및 등락 */}
                <div className="text-right min-w-0">
                  <div className="text-sm font-semibold">
                    {formatPrice(item.currentPrice)}
                  </div>
                  <div className={`text-xs flex items-center justify-end ${getChangeColor(item.changeSign)}`}>
                    {getChangeIcon(item.changeSign)}
                    <span className="ml-1">
                      {item.changeSign === 'up' ? '+' : item.changeSign === 'down' ? '-' : ''}
                      {item.changeRate.toFixed(2)}%
                    </span>
                  </div>
                </div>

                {/* 순매수 금액 */}
                <div className="text-right min-w-0">
                  <div className="text-sm font-bold text-red-600">
                    {item.netAmountFormatted}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    순매수
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && data.length === 0 && !error && (
          <div className="p-4 text-center text-muted-foreground">
            <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">데이터가 없습니다</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}