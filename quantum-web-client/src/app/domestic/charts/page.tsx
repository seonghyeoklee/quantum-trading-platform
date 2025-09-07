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
  Building2,
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

// Mock 국내 주식 데이터 (한국 스타일 - 상승:빨강, 하락:파랑)
const domesticStocks = [
  { symbol: '005930', name: '삼성전자', price: 68900, change: 1800, changePercent: 2.68, volume: 12345678, market: 'KOSPI' },
  { symbol: '000660', name: 'SK하이닉스', price: 89200, change: -2100, changePercent: -2.30, volume: 8765432, market: 'KOSPI' },
  { symbol: '035420', name: 'NAVER', price: 196500, change: 4500, changePercent: 2.34, volume: 3456789, market: 'KOSPI' },
  { symbol: '051910', name: 'LG화학', price: 432000, change: -8000, changePercent: -1.82, volume: 1234567, market: 'KOSPI' },
  { symbol: '006400', name: '삼성SDI', price: 156700, change: 12300, changePercent: 8.52, volume: 6789012, market: 'KOSPI' },
  { symbol: '035720', name: '카카오', price: 45800, change: 1200, changePercent: 2.69, volume: 4567890, market: 'KOSPI' },
  { symbol: '207940', name: '삼성바이오로직스', price: 789000, change: -15000, changePercent: -1.87, volume: 567890, market: 'KOSPI' },
  { symbol: '068270', name: '셀트리온', price: 156800, change: 6700, changePercent: 4.46, volume: 2345678, market: 'KOSPI' },
  { symbol: '096770', name: 'SK이노베이션', price: 89600, change: -1400, changePercent: -1.54, volume: 1876543, market: 'KOSPI' },
  { symbol: '323410', name: '카카오뱅크', price: 25900, change: 700, changePercent: 2.78, volume: 8901234, market: 'KOSDAQ' },
];

const koreanIndices = [
  { name: 'KOSPI', symbol: 'KS11', value: 2456.78, change: 18.45, changePercent: 0.76 },
  { name: 'KOSDAQ', symbol: 'KQ11', value: 845.32, change: -5.23, changePercent: -0.61 },
  { name: 'KRX 300', symbol: 'KRX300', value: 1234.56, change: 8.90, changePercent: 0.73 },
  { name: 'KOSPI 200', symbol: 'KS200', value: 325.67, change: 2.45, changePercent: 0.76 },
];

const domesticNews = [
  { id: 1, title: '삼성전자, 3분기 영업이익 예상치 상회... 반도체 회복 신호', time: '10분 전', source: '연합뉴스' },
  { id: 2, title: 'SK하이닉스 HBM 공급량 확대, AI 반도체 수요 급증', time: '25분 전', source: '조선비즈' },
  { id: 3, title: 'NAVER 클라우드 사업 성장세 가속, 클로바X 확산 기대', time: '45분 전', source: '매일경제' },
  { id: 4, title: '한국은행 기준금리 동결, 경기 불확실성 고려', time: '1시간 전', source: '한국경제' },
  { id: 5, title: '카카오 플랫폼 통합 가속화, 시너지 효과 기대', time: '1시간 30분 전', source: '아이뉴스24' },
];

const marketHours = {
  preMarket: { open: '08:00', close: '09:00', status: 'closed' },
  regular: { open: '09:00', close: '15:30', status: 'open' },
  afterHours: { open: '15:30', close: '16:00', status: 'closed' },
};

export default function DomesticChartsPage() {
  const [selectedStock, setSelectedStock] = useState(domesticStocks[0]);
  const [searchQuery, setSearchQuery] = useState('');
  const [watchlist, setWatchlist] = useState<string[]>(['005930', '000660', '035420']);
  
  // 패널 토글 상태 (오른쪽만 유지)
  const [rightPanelVisible, setRightPanelVisible] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // 로딩 상태
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);

  const formatPrice = (price: number) => {
    return `${price.toLocaleString()}원`;
  };

  const formatNumber = (num: number) => {
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(1)}억`;
    } else if (num >= 10000) {
      return `${(num / 10000).toFixed(0)}만`;
    }
    return num.toLocaleString();
  };

  const getCurrentMarketStatus = () => {
    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const currentTime = currentHour * 100 + currentMinute;
    
    if (currentTime >= 900 && currentTime < 1530) {
      return { status: 'open', session: 'regular' };
    } else if (currentTime >= 800 && currentTime < 900) {
      return { status: 'premarket', session: 'premarket' };
    } else if (currentTime >= 1530 && currentTime < 1600) {
      return { status: 'afterhours', session: 'afterhours' };
    } else {
      return { status: 'closed', session: 'closed' };
    }
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
    stock.symbol.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const marketStatus = getCurrentMarketStatus();

  const handleFullscreenToggle = () => {
    setIsFullscreen(!isFullscreen);
  };

  // 로딩 효과
  useEffect(() => {
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + Math.random() * 25
      })
    }, 120)

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
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg animate-pulse">
              <Building2 className="w-8 h-8 text-white animate-pulse" />
            </div>
          </div>
          
          {/* 브랜드명 */}
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-foreground">
              국내 차트
            </h1>
            <p className="text-muted-foreground text-sm">
              한국 주식시장 데이터를 불러오는 중...
            </p>
          </div>
          
          {/* 프로그레스 바 */}
          <div className="space-y-3">
            <div className="w-full bg-muted rounded-full h-1 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${Math.min(loadingProgress, 100)}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {Math.min(Math.round(loadingProgress), 100)}% 완료
            </p>
          </div>
          
          {/* 로딩 메시지 */}
          <div className="text-xs text-muted-foreground space-y-1">
            <p>KOSPI, KOSDAQ 실시간 데이터 연결 중...</p>
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
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
            market="domestic"
            className="w-full h-full"
            onFullscreenToggle={handleFullscreenToggle}
          />
        </div>
      ) : (
        /* TradingView 스타일 레이아웃 - 2패널 (차트 + 정보) */
        <div className="flex h-[calc(100vh-64px)]">

        {/* 메인 차트 패널 */}
        <div className="flex-1 flex flex-col">
          {/* 차트 헤더 */}
          <div className="p-4 border-b border-border bg-card">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                
                <div>
                  <h1 className="text-xl font-bold flex items-center space-x-2">
                    <span>{selectedStock.symbol}</span>
                    <Badge variant="outline" className="text-xs">{selectedStock.market}</Badge>
                  </h1>
                  <p className="text-sm text-muted-foreground">{selectedStock.name}</p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-2xl font-bold">{formatPrice(selectedStock.price)}</div>
                  <div className={`flex items-center space-x-1 ${
                    selectedStock.change >= 0 ? 'text-red-600' : 'text-blue-600'
                  }`}>
                    {selectedStock.change >= 0 ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                    <span className="text-lg font-semibold">
                      {selectedStock.change >= 0 ? '+' : ''}{selectedStock.change.toLocaleString()}
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
                  <span>KRW</span>
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
                <Building2 className="w-4 h-4 mr-2" />
                한국 시장
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
              정규장: 09:00 - 15:30 (KST)
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

          {/* 주요 지수 */}
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold mb-3 flex items-center">
              <BarChart3 className="w-4 h-4 mr-2" />
              주요 지수
            </h3>
            
            <div className="space-y-3">
              {koreanIndices.map((index) => (
                <div key={index.symbol} className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium">{index.name}</div>
                    <div className="text-xs text-muted-foreground">{index.symbol}</div>
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

          {/* 거래 시간 */}
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold mb-3 flex items-center">
              <Clock className="w-4 h-4 mr-2" />
              거래 시간
            </h3>
            
            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">동시호가</span>
                <span>08:00 - 09:00 KST</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">정규장</span>
                <div className="flex items-center space-x-1">
                  <span>09:00 - 15:30 KST</span>
                  <div className={`w-2 h-2 rounded-full ${
                    marketStatus.status === 'open' ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">시간외종가</span>
                <span>15:30 - 16:00 KST</span>
              </div>
            </div>
          </div>

          {/* 국내 뉴스 */}
          <div className="p-4 flex-1 overflow-y-auto">
            <h3 className="text-sm font-semibold mb-3 flex items-center">
              <Activity className="w-4 h-4 mr-2" />
              국내 뉴스
            </h3>
            
            <div className="space-y-3">
              {domesticNews.map((news) => (
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