'use client';

import { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, TrendingDown, Building2, Zap } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { kiwoomApiService } from '@/lib/api/kiwoom-service';
import { KiwoomStockInfo, MARKET_TYPES, MARKET_NAMES } from '@/lib/api/kiwoom-types';

interface StockSearchProps {
  onStockSelect: (stock: KiwoomStockInfo) => void;
  className?: string;
}

export default function StockSearch({ onStockSelect, className }: StockSearchProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [stockList, setStockList] = useState<KiwoomStockInfo[]>([]);
  const [filteredStocks, setFilteredStocks] = useState<KiwoomStockInfo[]>([]);
  const [selectedMarket, setSelectedMarket] = useState<string>(MARKET_TYPES.KOSPI);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [popularStocks, setPopularStocks] = useState<KiwoomStockInfo[]>([]);
  
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 인기 종목 로드
  useEffect(() => {
    const loadPopularStocks = async () => {
      try {
        const stocks = await kiwoomApiService.getPopularStocks();
        setPopularStocks(stocks.slice(0, 10)); // 상위 10개만
      } catch (error) {
        console.error('인기 종목 로드 실패:', error);
      }
    };
    
    loadPopularStocks();
  }, []);

  // 시장 변경 시 또는 결과 창 표시 시 종목 리스트 로드
  useEffect(() => {
    const loadStockList = async () => {
      // 결과 창이 표시되고 해당 시장의 데이터가 없는 경우에만 로드
      if (!showResults) {
        console.log('🚫 종목 로드 스킵: showResults=false');
        return;
      }
      
      console.log('📋 종목 리스트 로드 시작: selectedMarket=', selectedMarket);
      setLoading(true);
      try {
        const stocks = await kiwoomApiService.getStockList(selectedMarket);
        console.log('✅ 종목 리스트 로드 완료:', stocks.length, '개');
        setStockList(stocks);
        filterStocks(stocks, searchQuery);
      } catch (error) {
        console.error('❌ 종목 리스트 로드 실패:', error);
        setStockList([]);
        setFilteredStocks([]);
      } finally {
        setLoading(false);
      }
    };

    if (showResults) {
      loadStockList();
    }
  }, [selectedMarket, showResults]);

  // 검색어 변경 시 필터링
  useEffect(() => {
    filterStocks(stockList, searchQuery);
  }, [searchQuery, stockList]);

  const filterStocks = (stocks: KiwoomStockInfo[], query: string) => {
    console.log('🔍 필터링 시작: stocks=', stocks.length, ', query="', query, '"');
    
    if (!query.trim()) {
      const result = stocks.slice(0, 50); // 상위 50개만 표시
      console.log('📄 전체 목록 표시:', result.length, '개 (상위 50개)');
      setFilteredStocks(result);
      return;
    }

    const filtered = stocks.filter(stock =>
      stock.name.toLowerCase().includes(query.toLowerCase()) ||
      stock.code.includes(query)
    ).slice(0, 20); // 검색 결과는 20개로 제한

    console.log('🔍 검색 결과:', filtered.length, '개');
    setFilteredStocks(filtered);
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      setShowResults(true);
    }
  };

  const handleStockClick = (stock: KiwoomStockInfo) => {
    onStockSelect(stock);
    setShowResults(false);
    setSearchQuery('');
    inputRef.current?.blur();
  };

  const handleFocus = () => {
    console.log('🎯 검색창 포커스');
    setShowResults(true);
  };

  const formatPrice = (price: string) => {
    const num = parseInt(price);
    if (isNaN(num)) return '0원';
    return new Intl.NumberFormat('ko-KR').format(num) + '원';
  };

  const getMarketBadgeColor = (marketCode: string) => {
    switch (marketCode) {
      case '0': return 'bg-blue-500 text-white';
      case '10': return 'bg-purple-500 text-white';
      case '8': return 'bg-green-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getWarningBadge = (warning: string) => {
    switch (warning) {
      case '2': return { text: '정리매매', color: 'bg-red-500 text-white' };
      case '3': return { text: '단기과열', color: 'bg-orange-500 text-white' };
      case '4': return { text: '투자위험', color: 'bg-red-600 text-white' };
      case '5': return { text: '투자경고', color: 'bg-red-400 text-white' };
      case '1': return { text: 'ETF주의', color: 'bg-yellow-500 text-black' };
      default: return null;
    }
  };

  // 외부 클릭 시 결과 창 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative ${className}`} ref={searchRef}>
      {/* 검색 입력 */}
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            ref={inputRef}
            type="text"
            placeholder="종목명 또는 종목코드 검색..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={handleFocus}
            className="pl-10 pr-4"
          />
        </div>
        
        {/* 시장 선택 */}
        <div className="flex space-x-1">
          {[
            { value: MARKET_TYPES.KOSPI, label: 'KOSPI' },
            { value: MARKET_TYPES.KOSDAQ, label: 'KOSDAQ' },
            { value: MARKET_TYPES.ETF, label: 'ETF' },
          ].map((market) => (
            <Button
              key={market.value}
              variant={selectedMarket === market.value ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedMarket(market.value)}
              className="text-xs"
            >
              {market.label}
            </Button>
          ))}
        </div>
      </div>

      {/* 검색 결과 드롭다운 */}
      {showResults && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-background border border-border rounded-md shadow-lg z-50 max-h-96 overflow-y-auto">
          {!searchQuery.trim() && (
            <>
              {/* 인기 종목 섹션 */}
              <div className="p-3 border-b border-border">
                <div className="flex items-center space-x-2 mb-2">
                  <Zap className="w-4 h-4 text-orange-500" />
                  <span className="text-sm font-medium text-muted-foreground">인기 종목</span>
                </div>
                <div className="space-y-1">
                  {popularStocks.slice(0, 5).map((stock) => (
                    <div
                      key={stock.code}
                      onClick={() => handleStockClick(stock)}
                      className="flex items-center justify-between p-2 hover:bg-muted cursor-pointer rounded-sm"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <Building2 className="w-4 h-4 text-primary" />
                        </div>
                        <div>
                          <div className="font-medium">{stock.name}</div>
                          <div className="text-xs text-muted-foreground">{stock.code}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium">{formatPrice(stock.lastPrice)}</div>
                        <Badge className={`text-xs ${getMarketBadgeColor(stock.marketCode)}`}>
                          {MARKET_NAMES[stock.marketCode as keyof typeof MARKET_NAMES]}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* 검색 결과 또는 전체 목록 */}
          {loading ? (
            <div className="p-4 text-center text-muted-foreground">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              종목 정보 로딩 중...
            </div>
          ) : (
            <div className="max-h-64 overflow-y-auto">
              {filteredStocks.length > 0 ? (
                <>
                  {searchQuery.trim() && (
                    <div className="p-2 text-xs text-muted-foreground border-b border-border">
                      검색 결과 {filteredStocks.length}개
                    </div>
                  )}
                  {filteredStocks.map((stock) => {
                    const warning = getWarningBadge(stock.orderWarning);
                    
                    return (
                      <div
                        key={stock.code}
                        onClick={() => handleStockClick(stock)}
                        className="flex items-center justify-between p-3 hover:bg-muted cursor-pointer border-b border-border last:border-b-0"
                      >
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <Building2 className="w-5 h-5 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{stock.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {stock.code} • {stock.upName}
                            </div>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge className={`text-xs ${getMarketBadgeColor(stock.marketCode)}`}>
                                {MARKET_NAMES[stock.marketCode as keyof typeof MARKET_NAMES]}
                              </Badge>
                              {warning && (
                                <Badge className={`text-xs ${warning.color}`}>
                                  {warning.text}
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium">{formatPrice(stock.lastPrice)}</div>
                          <div className="text-xs text-muted-foreground">
                            {stock.upSizeName}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </>
              ) : (
                <div className="p-4 text-center text-muted-foreground">
                  {searchQuery.trim() ? '검색 결과가 없습니다' : '종목을 검색해보세요'}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}