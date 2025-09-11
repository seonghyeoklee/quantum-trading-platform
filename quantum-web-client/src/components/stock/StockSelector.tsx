'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, Filter, TrendingUp, Building2, Activity, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api';
import { 
  DomesticStock, 
  StockListResponse, 
  DomesticStockWithKisDetail, 
  KisStockDetailInfo,
  getPriceChangeDisplay,
  formatPrice,
  formatPercent,
  formatVolume,
  PriceChangeSign
} from '@/types/stock';

interface StockSelectorProps {
  onStockSelect?: (stock: DomesticStock) => void;
  className?: string;
  showSearch?: boolean;
  showFilter?: boolean;
  pageSize?: number;
  selectionMode?: 'single' | 'multiple';
  selectedStocks?: DomesticStock[];
  placeholder?: string;
  title?: string;
  showKisDetail?: boolean;  // KIS API 상세 정보 표시 여부
}

export default function StockSelector({
  onStockSelect,
  className,
  showSearch = true,
  showFilter = true,
  pageSize = 20,
  selectionMode = 'single',
  selectedStocks = [],
  placeholder = '종목명 또는 종목코드 검색...',
  title = '종목 선택',
  showKisDetail = false
}: StockSelectorProps) {
  const [stocks, setStocks] = useState<DomesticStock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [marketFilter, setMarketFilter] = useState<'ALL' | 'KOSPI' | 'KOSDAQ'>('ALL');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  
  // KIS API 상세 정보 상태
  const [stockDetails, setStockDetails] = useState<Map<string, KisStockDetailInfo>>(new Map());
  const [loadingDetails, setLoadingDetails] = useState<Set<string>>(new Set());

  // KIS API 상세 정보 가져오기
  const fetchStockDetail = async (stockCode: string) => {
    if (!showKisDetail || loadingDetails.has(stockCode)) {
      return;
    }

    setLoadingDetails(prev => new Set([...prev, stockCode]));

    try {
      const response = await apiClient.get<DomesticStockWithKisDetail>(
        `/api/v1/stocks/domestic/${stockCode}/detail`,
        false
      );
      
      if (response.data && response.data.kisDetail) {
        setStockDetails(prev => new Map(prev).set(stockCode, response.data!.kisDetail!));
      }
    } catch (err) {
      console.error(`KIS 상세 정보 조회 실패 - ${stockCode}:`, err);
      // 에러 발생 시에도 로딩 상태를 제거하되, 무음으로 처리
    } finally {
      setLoadingDetails(prev => {
        const newSet = new Set(prev);
        newSet.delete(stockCode);
        return newSet;
      });
    }
  };

  // API 호출 함수들
  const fetchStocks = async (page: number = 0, keyword?: string, market?: string) => {
    setLoading(true);
    setError(null);

    try {
      let endpoint = `/api/v1/stocks/domestic?page=${page}&size=${pageSize}`;
      
      if (keyword && keyword.trim()) {
        endpoint = `/api/v1/stocks/domestic/search?keyword=${encodeURIComponent(keyword.trim())}&page=${page}&size=${pageSize}`;
      }
      
      if (market && market !== 'ALL') {
        endpoint += `&marketType=${market}`;
      }

      const response = await apiClient.get<StockListResponse>(endpoint, false);
      
      if (response.data) {
        const stocks = response.data.stocks;
        setStocks(stocks);
        setCurrentPage(response.data.currentPage);
        setTotalPages(response.data.totalPages);
        setTotalCount(response.data.totalCount);
        
        // KIS 상세 정보가 활성화된 경우 각 종목의 상세 정보를 병렬로 가져오기
        if (showKisDetail && stocks.length > 0) {
          stocks.forEach(stock => {
            fetchStockDetail(stock.stockCode);
          });
        }
      }
      
    } catch (err) {
      console.error('종목 조회 실패:', err);
      setError(err instanceof Error ? err.message : '종목 조회에 실패했습니다.');
      setStocks([]);
    } finally {
      setLoading(false);
    }
  };

  // 초기 데이터 로드
  useEffect(() => {
    fetchStocks();
  }, []);

  // 검색어 변경 시 디바운스 적용
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchKeyword !== '') {
        fetchStocks(0, searchKeyword, marketFilter !== 'ALL' ? marketFilter : undefined);
        setCurrentPage(0);
      } else {
        fetchStocks(0, undefined, marketFilter !== 'ALL' ? marketFilter : undefined);
        setCurrentPage(0);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchKeyword, marketFilter]);

  // 종목 선택 핸들러
  const handleStockSelect = (stock: DomesticStock) => {
    if (onStockSelect) {
      onStockSelect(stock);
    }
  };

  // 선택된 종목인지 확인
  const isStockSelected = (stock: DomesticStock) => {
    return selectedStocks.some(selected => selected.stockCode === stock.stockCode);
  };

  // 페이지 변경
  const handlePageChange = (newPage: number) => {
    fetchStocks(newPage, searchKeyword || undefined, marketFilter !== 'ALL' ? marketFilter : undefined);
  };

  // 필터링된 표시용 메모
  const displayInfo = useMemo(() => {
    const marketText = marketFilter === 'ALL' ? '전체' : marketFilter;
    const searchText = searchKeyword ? `"${searchKeyword}" 검색결과` : '전체 종목';
    return `${marketText} | ${searchText} (${totalCount}건)`;
  }, [marketFilter, searchKeyword, totalCount]);

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <TrendingUp className="w-5 h-5 text-primary" />
          {title}
        </CardTitle>
        
        {/* 검색 및 필터 */}
        <div className="space-y-3">
          {showSearch && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder={placeholder}
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
          )}
          
          {showFilter && (
            <div className="flex gap-2">
              <Button
                variant={marketFilter === 'ALL' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMarketFilter('ALL')}
              >
                전체
              </Button>
              <Button
                variant={marketFilter === 'KOSPI' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMarketFilter('KOSPI')}
                className="text-red-600 hover:text-red-700"
              >
                KOSPI
              </Button>
              <Button
                variant={marketFilter === 'KOSDAQ' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMarketFilter('KOSDAQ')}
                className="text-blue-600 hover:text-blue-700"
              >
                KOSDAQ
              </Button>
            </div>
          )}
          
          <div className="text-sm text-muted-foreground">
            {displayInfo}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {error && (
          <div className="text-center py-8 text-red-500">
            <p>{error}</p>
            <Button 
              variant="outline" 
              size="sm" 
              className="mt-2"
              onClick={() => fetchStocks()}
            >
              다시 시도
            </Button>
          </div>
        )}
        
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-2 text-muted-foreground">종목 조회 중...</p>
          </div>
        )}
        
        {!loading && !error && stocks.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <Building2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>조회된 종목이 없습니다.</p>
          </div>
        )}
        
        {!loading && !error && stocks.length > 0 && (
          <>
            <div className="h-96 overflow-y-auto">
              <div className="space-y-2">
                {stocks.map((stock) => {
                  const isSelected = isStockSelected(stock);
                  const kisDetail = stockDetails.get(stock.stockCode);
                  const isLoadingDetail = loadingDetails.has(stock.stockCode);
                  
                  return (
                    <div
                      key={stock.stockCode}
                      className={cn(
                        'p-3 rounded-lg border cursor-pointer transition-colors hover:bg-accent',
                        isSelected ? 'bg-accent border-primary' : 'border-border'
                      )}
                      onClick={() => handleStockSelect(stock)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm">{stock.stockName}</span>
                            <Badge 
                              variant="secondary" 
                              className={cn(
                                'text-xs',
                                stock.marketType === 'KOSPI' ? 'text-red-600' : 'text-blue-600'
                              )}
                            >
                              {stock.marketType}
                            </Badge>
                          </div>
                          
                          <div className="text-sm text-muted-foreground space-y-1">
                            <p>
                              {stock.stockCode}
                              {stock.sectorCode && ` | ${stock.sectorCode}`}
                            </p>
                            
                            {/* KIS API 상세 정보 표시 */}
                            {showKisDetail && (
                              <div className="mt-2">
                                {isLoadingDetail ? (
                                  <div className="flex items-center gap-2">
                                    <div className="w-4 h-4 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
                                    <span className="text-xs text-muted-foreground">실시간 데이터 로딩 중...</span>
                                  </div>
                                ) : kisDetail ? (
                                  <div className="space-y-1 text-xs">
                                    <div className="flex items-center gap-4">
                                      {/* 현재가와 등락률 */}
                                      <div className="flex items-center gap-1">
                                        <DollarSign className="w-3 h-3" />
                                        <span className="font-medium">{formatPrice(kisDetail.currentPrice)}</span>
                                        <span 
                                          className={cn(
                                            'flex items-center gap-1',
                                            getPriceChangeDisplay(kisDetail.changeSign).color
                                          )}
                                        >
                                          {getPriceChangeDisplay(kisDetail.changeSign).symbol}
                                          {formatPercent(kisDetail.changeRate)}
                                        </span>
                                      </div>
                                      
                                      {/* 거래량 */}
                                      <div className="flex items-center gap-1">
                                        <Activity className="w-3 h-3" />
                                        <span>{formatVolume(kisDetail.volume)}</span>
                                      </div>
                                    </div>
                                    
                                    {/* 재무비율 */}
                                    <div className="flex items-center gap-3 text-muted-foreground">
                                      <span>PER {kisDetail.per.toFixed(1)}</span>
                                      <span>PBR {kisDetail.pbr.toFixed(2)}</span>
                                      <span>시총 {(kisDetail.marketCap / 10000).toFixed(1)}조</span>
                                    </div>
                                  </div>
                                ) : null}
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {isSelected && (
                          <div className="w-4 h-4 rounded-full bg-primary flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-white"></div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            {/* 페이징 */}
            {totalPages > 1 && (
              <div className="mt-4 flex items-center justify-between text-sm">
                <div className="text-muted-foreground">
                  페이지 {currentPage + 1} / {totalPages}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage <= 0}
                  >
                    이전
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage >= totalPages - 1}
                  >
                    다음
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}