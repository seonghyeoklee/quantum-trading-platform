'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  Search,
  Star,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Globe,
  Activity,
  Clock,
  Volume2,
  DollarSign,
  ChevronLeft,
  ChevronRight
} from "lucide-react";

// TradingView 차트 동적 import (SSR 방지)
const TradingViewChart = dynamic(() => import('@/components/chart/TradingViewChart'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[600px] bg-muted rounded-lg flex items-center justify-center">
      <div className="text-center space-y-2">
        <BarChart3 className="w-8 h-8 mx-auto animate-pulse" />
        <p className="text-sm text-muted-foreground">차트 로딩 중...</p>
      </div>
    </div>
  )
});

// Mock 해외 주식 데이터
const overseasStocks = [
  { symbol: 'AAPL', name: 'Apple Inc.', price: 189.25, change: 2.15, changePercent: 1.15, volume: 45678901, currency: 'USD' },
  { symbol: 'MSFT', name: 'Microsoft Corp.', price: 334.89, change: -3.24, changePercent: -0.96, volume: 23456789, currency: 'USD' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 138.12, change: 1.87, changePercent: 1.37, volume: 34567890, currency: 'USD' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 144.65, change: -0.85, changePercent: -0.58, volume: 28765432, currency: 'USD' },
  { symbol: 'TSLA', name: 'Tesla Inc.', price: 254.32, change: 8.45, changePercent: 3.44, volume: 67891234, currency: 'USD' },
  { symbol: 'META', name: 'Meta Platforms', price: 298.76, change: 4.23, changePercent: 1.44, volume: 19876543, currency: 'USD' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 421.85, change: 12.67, changePercent: 3.10, volume: 56789012, currency: 'USD' },
  { symbol: 'NFLX', name: 'Netflix Inc.', price: 385.12, change: -2.34, changePercent: -0.60, volume: 12345678, currency: 'USD' },
];

const usIndices = [
  { name: 'S&P 500', symbol: 'SPY', value: 4234.87, change: 28.45, changePercent: 0.68 },
  { name: 'NASDAQ', symbol: 'QQQ', value: 14567.92, change: -45.23, changePercent: -0.31 },
  { name: 'Dow Jones', symbol: 'DIA', value: 33891.45, change: 156.78, changePercent: 0.47 },
  { name: 'Russell 2000', symbol: 'IWM', value: 1876.34, change: -12.56, changePercent: -0.66 },
];

const globalNews = [
  { id: 1, title: 'Apple reports strong Q3 earnings despite supply chain challenges', time: '15분 전', source: 'Reuters' },
  { id: 2, title: 'Tesla stock surges on autonomous driving breakthrough', time: '32분 전', source: 'Bloomberg' },
  { id: 3, title: 'Microsoft announces new AI partnership with OpenAI', time: '1시간 전', source: 'TechCrunch' },
  { id: 4, title: 'Fed signals potential rate cuts in 2024', time: '1시간 전', source: 'CNBC' },
  { id: 5, title: 'NVIDIA continues to dominate AI chip market', time: '2시간 전', source: 'Wall Street Journal' },
];

const marketHours = {
  preMarket: { open: '04:00', close: '09:30', status: 'closed' },
  regular: { open: '09:30', close: '16:00', status: 'open' },
  afterHours: { open: '16:00', close: '20:00', status: 'closed' },
};

export default function OverseasPage() {
  const [selectedStock, setSelectedStock] = useState(overseasStocks[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [watchlist, setWatchlist] = useState<string[]>(['AAPL', 'MSFT', 'GOOGL']);
  
  // 패널 토글 상태 (오른쪽만 유지)
  const [rightPanelVisible, setRightPanelVisible] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // 로딩 상태
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);

  const formatPrice = (price: number, currency: string = 'USD') => {
    return `$${price.toFixed(2)}`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const getCurrentMarketStatus = () => {
    // 간단한 예시 - 실제로는 현재 시간과 비교해야 함
    return { status: 'open', session: 'regular' };
  };

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const filteredStocks = overseasStocks.filter(stock => 
    stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    stock.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const marketStatus = getCurrentMarketStatus();

  const handleFullscreenToggle = () => {
    setIsFullscreen(!isFullscreen);
  };

  // 로딩 효과
  useEffect(() => {
    // 프로그레스 시뮬레이션
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + Math.random() * 25
      })
    }, 120)

    // 로딩 완료
    const timer = setTimeout(() => {
      setLoadingProgress(100)
      setTimeout(() => {
        setIsLoading(false)
      }, 300)
    }, 900)

    return () => {
      clearTimeout(timer)
      clearInterval(progressInterval)
    }
  }, [])

  // ESC 키로 전체화면 종료
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };

    if (isFullscreen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isFullscreen]);

  // 로딩 화면 렌더링
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-8 max-w-md mx-auto px-6">
          {/* 로고 애니메이션 */}
          <div className="flex items-center justify-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg animate-pulse">
              <Globe className="w-8 h-8 text-white animate-pulse" />
            </div>
          </div>
          
          {/* 브랜드명 */}
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-foreground">
              해외 시장
            </h1>
            <p className="text-muted-foreground text-sm">
              글로벌 주식 데이터를 불러오는 중...
            </p>
          </div>
          
          {/* 세련된 프로그레스 바 */}
          <div className="space-y-3">
            <div className="w-full bg-muted rounded-full h-1 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-emerald-500 to-green-600 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${Math.min(loadingProgress, 100)}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {Math.min(Math.round(loadingProgress), 100)}% 완료
            </p>
          </div>
          
          {/* 로딩 메시지 */}
          <div className="text-xs text-muted-foreground space-y-1">
            <p>NASDAQ, NYSE 실시간 데이터 연결 중...</p>
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* 전체화면 모드 */}
      {isFullscreen ? (
        <div className="fixed inset-0 z-50 bg-background">
          <TradingViewChart 
            symbol={selectedStock.symbol}
            market="overseas"
            className="w-full h-full"
            onFullscreenToggle={handleFullscreenToggle}
          />
        </div>
      ) : (
        /* TradingView 스타일 레이아웃 - 2패널 (차트 + 정보) */
        <div className="flex h-[calc(100vh-128px)]">

        {/* 메인 차트 패널 */}
        <div className="flex-1 flex flex-col">
          {/* 차트 헤더 */}
          <div className="p-4 border-b border-border bg-card">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                
                <div>
                  <h1 className="text-xl font-bold flex items-center space-x-2">
                    <span>{selectedStock.symbol}</span>
                    <Badge variant="outline" className="text-xs">NASDAQ</Badge>
                  </h1>
                  <p className="text-sm text-muted-foreground">{selectedStock.name}</p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-2xl font-bold">{formatPrice(selectedStock.price)}</div>
                  <div className={`flex items-center space-x-1 ${
                    selectedStock.change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {selectedStock.change >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                    <span className="text-lg font-semibold">
                      {selectedStock.change >= 0 ? '+' : ''}{selectedStock.change.toFixed(2)}
                    </span>
                    <span className="text-lg font-semibold">
                      ({selectedStock.change >= 0 ? '+' : ''}{selectedStock.changePercent}%)
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Badge variant="outline" className="flex items-center space-x-1">
                  <Volume2 className="w-3 h-3" />
                  <span>{formatNumber(selectedStock.volume)}</span>
                </Badge>
                <Badge variant="outline" className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{marketStatus.status === 'open' ? '실시간' : '휴장'}</span>
                </Badge>
                <Badge variant="outline" className="flex items-center space-x-1">
                  <DollarSign className="w-3 h-3" />
                  <span>USD</span>
                </Badge>
                
                {/* 우측 패널 토글 버튼 */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRightPanelVisible(!rightPanelVisible)}
                  className="h-8 w-8 p-0"
                >
                  <ChevronLeft className={`w-4 h-4 transition-transform ${rightPanelVisible ? 'rotate-180' : ''}`} />
                </Button>
              </div>
            </div>
          </div>

          {/* 차트 영역 */}
          <div className="flex-1 p-4">
            <TradingViewChart 
              symbol={selectedStock.symbol}
              market="overseas"
              className="w-full h-full"
              onFullscreenToggle={handleFullscreenToggle}
            />
          </div>
        </div>

        {/* 우측 정보 패널 - 통합 정보 */}
        <div className={`${rightPanelVisible ? 'w-96' : 'w-0'} border-l border-border bg-card flex flex-col transition-all duration-300 overflow-hidden`}>
          
          {/* 종목 검색 */}
          <div className="p-4 border-b border-border">
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                placeholder="종목명 또는 심볼 검색"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 h-8"
              />
            </div>
          </div>

          {/* 시장 상태 */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold flex items-center">
                <Globe className="w-4 h-4 mr-2" />
                미국 시장
              </h3>
              <Badge 
                variant={marketStatus.status === 'open' ? 'default' : 'secondary'}
                className="flex items-center space-x-1"
              >
                <div className={`w-2 h-2 rounded-full ${
                  marketStatus.status === 'open' ? 'bg-green-500' : 'bg-gray-400'
                }`} />
                <span>{marketStatus.status === 'open' ? '개장' : '휴장'}</span>
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              정규장: 09:30 - 16:00 (EST)
            </p>
          </div>

          {/* 관심종목 */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold flex items-center">
                <Star className="w-4 h-4 mr-2" />
                관심종목
              </h3>
              <Badge variant="secondary" className="text-xs">
                {watchlist.length}
              </Badge>
            </div>
            
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {overseasStocks.filter(stock => watchlist.includes(stock.symbol)).map((stock) => (
                <div
                  key={stock.symbol}
                  className={`p-2 rounded-md cursor-pointer transition-colors ${
                    selectedStock.symbol === stock.symbol
                      ? 'bg-primary/10 border border-primary/20'
                      : 'hover:bg-muted/50'
                  }`}
                  onClick={() => setSelectedStock(stock)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium">{stock.symbol}</div>
                      <div className="text-xs text-muted-foreground truncate max-w-[120px]">{stock.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{formatPrice(stock.price)}</div>
                      <div className={`text-xs flex items-center ${
                        stock.change >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {stock.change >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {stock.change >= 0 ? '+' : ''}{stock.changePercent}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 인기 종목 */}
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold mb-3 flex items-center">
              <TrendingUp className="w-4 h-4 mr-2" />
              인기 종목
            </h3>
            
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {filteredStocks.slice(0, 5).map((stock) => (
                <div
                  key={stock.symbol}
                  className={`p-2 rounded-md cursor-pointer transition-colors ${
                    selectedStock.symbol === stock.symbol
                      ? 'bg-primary/10 border border-primary/20'
                      : 'hover:bg-muted/50'
                  }`}
                  onClick={() => setSelectedStock(stock)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div>
                        <div className="text-sm font-medium">{stock.symbol}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[120px]">{stock.name}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleWatchlist(stock.symbol);
                        }}
                      >
                        <Star className={`w-3 h-3 ${
                          watchlist.includes(stock.symbol) ? 'fill-yellow-400 text-yellow-400' : ''
                        }`} />
                      </Button>
                      
                      <div className="text-right">
                        <div className="text-sm font-medium">{formatPrice(stock.price)}</div>
                        <div className={`text-xs ${
                          stock.change >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {stock.change >= 0 ? '+' : ''}{stock.changePercent}%
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 주요 지수 */}
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold mb-3 flex items-center">
              <BarChart3 className="w-4 h-4 mr-2" />
              주요 지수
            </h3>
            
            <div className="space-y-3">
              {usIndices.map((index) => (
                <div key={index.symbol} className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium">{index.name}</div>
                    <div className="text-xs text-muted-foreground">{index.symbol}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{index.value.toFixed(2)}</div>
                    <div className={`text-xs flex items-center justify-end ${
                      index.change >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {index.change >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                      {index.change >= 0 ? '+' : ''}{index.changePercent}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 거래 시간 */}
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold mb-3 flex items-center">
              <Clock className="w-4 h-4 mr-2" />
              거래 시간
            </h3>
            
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">프리마켓</span>
                <span>04:00 - 09:30 EST</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">정규장</span>
                <div className="flex items-center space-x-1">
                  <span>09:30 - 16:00 EST</span>
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">애프터마켓</span>
                <span>16:00 - 20:00 EST</span>
              </div>
            </div>
          </div>

          {/* 글로벌 뉴스 */}
          <div className="p-4 flex-1 overflow-y-auto">
            <h3 className="text-sm font-semibold mb-3 flex items-center">
              <Activity className="w-4 h-4 mr-2" />
              글로벌 뉴스
            </h3>
            
            <div className="space-y-3">
              {globalNews.map((news) => (
                <div key={news.id} className="p-3 rounded-md bg-muted/30 hover:bg-muted/50 cursor-pointer transition-colors">
                  <h4 className="text-sm font-medium mb-1 leading-tight">{news.title}</h4>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{news.source}</span>
                    <span>{news.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        </div>
      )}
    </div>
  );
}