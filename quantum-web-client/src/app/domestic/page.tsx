'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import Header from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Search,
  Star,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Building2,
  Globe,
  Activity,
  Clock,
  Volume2,
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

// Mock 데이터
const domesticStocks = [
  { symbol: '005930', name: '삼성전자', price: 75200, change: 1200, changePercent: 1.62, volume: 15234567 },
  { symbol: '000660', name: 'SK하이닉스', price: 123000, change: -2000, changePercent: -1.60, volume: 8765432 },
  { symbol: '035420', name: 'NAVER', price: 198500, change: 3500, changePercent: 1.79, volume: 3456789 },
  { symbol: '051910', name: 'LG화학', price: 456000, change: -8000, changePercent: -1.72, volume: 1234567 },
  { symbol: '035720', name: '카카오', price: 89600, change: 2100, changePercent: 2.40, volume: 9876543 },
  { symbol: '006400', name: '삼성SDI', price: 234000, change: 5500, changePercent: 2.41, volume: 2345678 },
  { symbol: '005490', name: 'POSCO홀딩스', price: 312000, change: -1500, changePercent: -0.48, volume: 1876543 },
  { symbol: '068270', name: '셀트리온', price: 189000, change: 4200, changePercent: 2.27, volume: 4567890 },
];

const marketIndices = [
  { name: 'KOSPI', value: 2647.82, change: 32.15, changePercent: 1.23 },
  { name: 'KOSDAQ', value: 742.15, change: -6.28, changePercent: -0.84 },
  { name: 'KPI200', value: 348.92, change: 4.23, changePercent: 1.23 },
];

const marketNews = [
  { id: 1, title: '삼성전자, 3분기 실적 시장 예상치 상회', time: '15분 전', source: '연합뉴스' },
  { id: 2, title: 'KOSPI, 외국인 순매수에 상승 마감', time: '32분 전', source: '한국경제' },
  { id: 3, title: 'SK하이닉스, 메모리 반도체 가격 상승 기대', time: '1시간 전', source: '매일경제' },
  { id: 4, title: '카카오, 플랫폼 사업 확장 계획 발표', time: '1시간 전', source: 'ZDNet' },
  { id: 5, title: 'LG화학, 배터리 사업 투자 확대', time: '2시간 전', source: '전자신문' },
];

export default function DomesticPage() {
  const [selectedStock, setSelectedStock] = useState(domesticStocks[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [watchlist, setWatchlist] = useState<string[]>(['005930', '000660']);
  
  // 패널 토글 상태 (오른쪽만 유지)
  const [rightPanelVisible, setRightPanelVisible] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatPrice = (price: number) => {
    return `₩${formatNumber(price)}`;
  };

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const filteredStocks = domesticStocks.filter(stock => 
    stock.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    stock.symbol.includes(searchQuery)
  );

  const handleFullscreenToggle = () => {
    setIsFullscreen(!isFullscreen);
  };

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

  return (
    <div className="min-h-screen bg-background">
      {!isFullscreen && <Header />}
      
      {/* 전체화면 모드 */}
      {isFullscreen ? (
        <div className="fixed inset-0 z-50 bg-background">
          <TradingViewChart 
            symbol={selectedStock.symbol}
            market="domestic"
            className="w-full h-full"
            onFullscreenToggle={handleFullscreenToggle}
          />
        </div>
      ) : (
        /* TradingView 스타일 레이아웃 - 2패널 (차트 + 정보) */
        <div className="flex h-[calc(100vh-128px)] relative"> {/* 헤더 높이 제외 */}

          {/* 메인 차트 패널 */}
          <div className="flex-1 flex flex-col">
            {/* 차트 헤더 */}
            <div className="p-4 border-b border-border bg-card">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div>
                    <h1 className="text-xl font-bold">{selectedStock.name}</h1>
                    <p className="text-sm text-muted-foreground">{selectedStock.symbol}</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-2xl font-bold">{formatPrice(selectedStock.price)}</div>
                    <div className={`flex items-center space-x-1 ${
                      selectedStock.change >= 0 ? 'text-red-600' : 'text-blue-600'
                    }`}>
                      {selectedStock.change >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                      <span className="text-lg font-semibold">
                        {selectedStock.change >= 0 ? '+' : ''}{formatNumber(selectedStock.change)}
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
                    <span>실시간</span>
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
                market="domestic"
                className="w-full h-full"
                onFullscreenToggle={handleFullscreenToggle}
              />
            </div>
          </div>

          {/* 우측 패널 접힌 상태에서 토글 버튼 */}
          {!rightPanelVisible && (
            <div className="absolute top-1/2 right-0 z-20 -translate-y-1/2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setRightPanelVisible(true)}
                className="h-12 w-6 p-0 bg-background/80 backdrop-blur-sm border border-border rounded-l-md rounded-r-none hover:bg-background"
              >
                <ChevronLeft className="w-4 h-4 rotate-180" />
              </Button>
            </div>
          )}

          {/* 우측 정보 패널 - 통합 정보 */}
          <div className={`${rightPanelVisible ? 'w-96' : 'w-0'} border-l border-border bg-card flex flex-col transition-all duration-300 overflow-hidden`}>
            
            {/* 종목 검색 */}
            <div className="p-4 border-b border-border">
              <div className="relative mb-3">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input 
                  placeholder="종목명 또는 코드 검색"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 h-8"
                />
              </div>
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
                {domesticStocks.filter(stock => watchlist.includes(stock.symbol)).map((stock) => (
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
                        <div className="text-sm font-medium">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium">{formatPrice(stock.price)}</div>
                        <div className={`text-xs flex items-center ${
                          stock.change >= 0 ? 'text-red-600' : 'text-blue-600'
                        }`}>
                          {stock.change >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                          {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent}%
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
                          <div className="text-sm font-medium">{stock.name}</div>
                          <div className="text-xs text-muted-foreground">{stock.symbol}</div>
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
                            stock.change >= 0 ? 'text-red-600' : 'text-blue-600'
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

            {/* 시장 지수 */}
            <div className="p-4 border-b border-border">
              <h3 className="text-sm font-semibold mb-3 flex items-center">
                <BarChart3 className="w-4 h-4 mr-2" />
                주요 지수
              </h3>
              
              <div className="space-y-3">
                {marketIndices.map((index) => (
                  <div key={index.name} className="flex justify-between items-center">
                    <div>
                      <div className="text-sm font-medium">{index.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{index.value.toFixed(2)}</div>
                      <div className={`text-xs flex items-center justify-end ${
                        index.change >= 0 ? 'text-red-600' : 'text-blue-600'
                      }`}>
                        {index.change >= 0 ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {index.change >= 0 ? '+' : ''}{index.changePercent}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 시장 뉴스 */}
            <div className="p-4 flex-1 overflow-y-auto">
              <h3 className="text-sm font-semibold mb-3 flex items-center">
                <Activity className="w-4 h-4 mr-2" />
                시장 뉴스
              </h3>
              
              <div className="space-y-3">
                {marketNews.map((news) => (
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