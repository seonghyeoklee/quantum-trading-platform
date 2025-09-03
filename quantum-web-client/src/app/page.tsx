'use client'

import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import Header from "@/components/layout/Header"
import { CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { 
  BarChart3, 
  Activity, 
  Star, 
  Building2, 
  ChevronRight,
  ChevronLeft,
  X,
  Globe,
  Loader2,
  AlertCircle,

} from "lucide-react"
import { quantumApiClient } from '@/lib/services/quantum-api-client'

// Dynamic import for InfiniteChart to avoid SSR issues  
const InfiniteChart = dynamic(() => import('@/components/chart/InfiniteChart'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <Loader2 className="w-6 h-6 animate-spin" />
    </div>
  )
})

export default function Home() {
  const [showMobileSidebar, setShowMobileSidebar] = useState<'left' | 'right' | null>(null)
  const [currentMarket, setCurrentMarket] = useState<'domestic' | 'overseas'>('domestic')
  
  // 차트 설정
  const [selectedSymbol, setSelectedSymbol] = useState('005930')
  
  // 실시간 시장지수 상태
  const [indices, setIndices] = useState<any>(null) // eslint-disable-line @typescript-eslint/no-explicit-any
  const [indicesLoading, setIndicesLoading] = useState(true)
  const [indicesError, setIndicesError] = useState<string | null>(null)
  
  // 인기 종목 목록
  const popularStocks = [
    { symbol: '005930', name: '삼성전자' },
    { symbol: '000660', name: 'SK하이닉스' },
    { symbol: '035420', name: 'NAVER' },
    { symbol: '051910', name: 'LG화학' },
    { symbol: '035720', name: '카카오' },
    { symbol: '006400', name: '삼성SDI' },
    { symbol: '005490', name: 'POSCO홀딩스' },
    { symbol: '068270', name: '셀트리온' }
  ]

  // 시장지수 데이터 로딩
  useEffect(() => {
    const loadIndices = async () => {
      try {
        setIndicesLoading(true)
        setIndicesError(null)
        console.log('📊 실시간 시장지수 조회 시작')
        
        const data = await quantumApiClient.getMajorIndices()
        setIndices(data)
        console.log('✅ 실시간 시장지수 조회 완료:', data)
        
      } catch (error) {
        console.error('❌ 실시간 시장지수 조회 실패:', error)
        setIndicesError('시장지수 로딩 실패')
      } finally {
        setIndicesLoading(false)
      }
    }

    loadIndices()
    
    // 30초마다 지수 데이터 새로고침
    const interval = setInterval(loadIndices, 30000)
    
    return () => clearInterval(interval)
  }, [])

  // 종목 변경 핸들러
  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol)
  }

  // 마켓 전환 핸들러
  const switchMarket = (market: 'domestic' | 'overseas') => {
    setCurrentMarket(market)
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* Main Content - 3-Panel Layout */}
      <main className="flex flex-col lg:flex-row flex-1 overflow-hidden min-h-0" style={{ height: 'calc(100vh - 64px)' }}>
        
        {/* Left Sidebar - Watchlist */}
        <div className="hidden lg:flex w-80 border-r border-border bg-card flex-col">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">관심종목</h3>
              <Button variant="outline" size="sm" className="text-xs h-6 px-2">
                추가
              </Button>
            </div>
            
            {/* Market Type Tabs */}
            <div className="flex bg-muted rounded-lg p-1 mb-3">
              <button
                onClick={() => switchMarket('domestic')}
                className={`flex-1 text-xs px-3 py-1 rounded-md transition-colors flex items-center justify-center gap-1 ${
                  currentMarket === 'domestic'
                    ? 'bg-background shadow-sm text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Building2 className="w-3 h-3" />
                국내
              </button>
              <button
                onClick={() => switchMarket('overseas')}
                className={`flex-1 text-xs px-3 py-1 rounded-md transition-colors flex items-center justify-center gap-1 ${
                  currentMarket === 'overseas'
                    ? 'bg-background shadow-sm text-foreground font-medium'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Globe className="w-3 h-3" />
                해외
              </button>
            </div>

            {currentMarket === 'domestic' ? (
              <div className="space-y-2">
                <div className="text-xs text-muted-foreground mb-3 px-1">인기 종목</div>
                {popularStocks.map((stock) => (
                  <div 
                    key={stock.symbol}
                    className={`flex items-center justify-between p-2 rounded-md cursor-pointer transition-colors ${
                      selectedSymbol === stock.symbol 
                        ? 'bg-primary/10 border border-primary/20' 
                        : 'hover:bg-muted/50'
                    }`}
                    onClick={() => handleSymbolChange(stock.symbol)}
                  >
                    <div>
                      <div className="text-sm font-medium">{stock.name}</div>
                      <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                    </div>
                    {selectedSymbol === stock.symbol && (
                      <div className="w-2 h-2 bg-primary rounded-full" />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Star className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <div className="text-sm mb-2">해외 관심종목이 없습니다</div>
                <div className="text-xs">해외 종목을 추가해보세요</div>
              </div>
            )}
          </div>
          
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-sm mb-3">포트폴리오</h3>
            <div className="text-center py-6 text-muted-foreground">
              <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <div className="text-sm mb-2">포트폴리오가 비어있습니다</div>
              <div className="text-xs">거래를 시작해보세요</div>
            </div>
          </div>
          
          <div className="p-4">
            <h3 className="font-semibold text-sm mb-3">빠른 메뉴</h3>
            <div className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Building2 className="w-4 h-4 mr-2" />
                종목 검색
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                <Activity className="w-4 h-4 mr-2" />
                매매 신호
              </Button>
            </div>
          </div>
        </div>

        {/* Center Panel - Main Chart */}
        <div className="flex-1 flex flex-col bg-background">
          <div className="flex-1 p-4">
            <div className="h-full">
              {/* 종목 선택 컨트롤 */}
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-muted-foreground">종목 선택:</span>
                  <Select value={selectedSymbol} onValueChange={handleSymbolChange}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {popularStocks.map((stock) => (
                        <SelectItem key={stock.symbol} value={stock.symbol}>
                          {stock.name} ({stock.symbol})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {/* Infinite History 차트 */}
              <InfiniteChart
                symbol={selectedSymbol}
                stockName={popularStocks.find(s => s.symbol === selectedSymbol)?.name}
                height={500}
                className="h-full"
              />
            </div>
          </div>
        </div>

        {/* Right Sidebar - Market Data */}
        <div className="hidden lg:flex w-80 border-l border-border bg-card flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-sm mb-3">주요 지수</h3>
            
            {indicesLoading ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                <span className="text-xs text-muted-foreground">지수 로딩 중...</span>
              </div>
            ) : indicesError ? (
              <div className="flex items-center justify-center py-6 text-red-600">
                <AlertCircle className="w-4 h-4 mr-2" />
                <span className="text-xs">{indicesError}</span>
              </div>
            ) : indices ? (
              <div className="space-y-3">
                {/* KOSPI */}
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium">KOSPI</div>
                    <div className="text-xs text-muted-foreground">한국 종합주가지수</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{indices.kospi.value.toFixed(2)}</div>
                    <div className={`text-xs ${indices.kospi.sign === '2' ? 'text-red-600' : indices.kospi.sign === '4' ? 'text-blue-600' : 'text-gray-600'}`}>
                      {indices.kospi.changePercent >= 0 ? '+' : ''}{indices.kospi.changePercent.toFixed(2)}%
                      <span className="ml-1">
                        ({indices.kospi.change >= 0 ? '+' : ''}{indices.kospi.change.toFixed(2)})
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* KOSDAQ */}
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium">KOSDAQ</div>
                    <div className="text-xs text-muted-foreground">코스닥 지수</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">{indices.kosdaq.value.toFixed(2)}</div>
                    <div className={`text-xs ${indices.kosdaq.sign === '2' ? 'text-red-600' : indices.kosdaq.sign === '4' ? 'text-blue-600' : 'text-gray-600'}`}>
                      {indices.kosdaq.changePercent >= 0 ? '+' : ''}{indices.kosdaq.changePercent.toFixed(2)}%
                      <span className="ml-1">
                        ({indices.kosdaq.change >= 0 ? '+' : ''}{indices.kosdaq.change.toFixed(2)})
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* 원달러 환율 - 임시 고정값 */}
                <div className="flex justify-between items-center pt-2 mt-2 border-t border-border/50">
                  <div>
                    <div className="text-sm font-medium">USD/KRW</div>
                    <div className="text-xs text-muted-foreground">원달러 환율</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">1,347.50</div>
                    <div className="text-xs text-red-600">+0.32%</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <span className="text-xs">지수 데이터를 불러올 수 없습니다</span>
              </div>
            )}
          </div>
          
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-sm mb-3">오늘의 수익</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">총 수익률</span>
                <span className="text-sm font-medium">+0.00%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">실현손익</span>
                <span className="text-sm font-medium">₩0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">평가손익</span>
                <span className="text-sm font-medium">₩0</span>
              </div>
            </div>
          </div>
          
          <div className="p-4">
            <h3 className="font-semibold text-sm mb-3">거래 현황</h3>
            <div className="text-center py-6 text-muted-foreground">
              <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <div className="text-sm mb-2">진행 중인 거래가 없습니다</div>
              <div className="text-xs">거래를 시작해보세요</div>
            </div>
          </div>
        </div>
      </main>
      
      {/* Mobile Floating Buttons */}
      <div className="lg:hidden fixed bottom-4 left-4 right-4 flex justify-between z-30">
        <Button 
          variant="default" 
          size="sm"
          onClick={() => setShowMobileSidebar('left')}
          className="shadow-lg"
        >
          <ChevronRight className="w-4 h-4 mr-1" />
          관심종목
        </Button>
        <Button 
          variant="default" 
          size="sm"
          onClick={() => setShowMobileSidebar('right')}
          className="shadow-lg"
        >
          시장정보
          <ChevronLeft className="w-4 h-4 ml-1" />
        </Button>
      </div>
      
      {/* Mobile Sidebar Overlays */}
      {showMobileSidebar === 'left' && (
        <div className="lg:hidden fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="fixed left-0 top-0 bottom-0 w-80 bg-card border-r border-border overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h3 className="font-semibold">관심종목</h3>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowMobileSidebar(null)}
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
            <div className="p-4">
              {/* Mobile Market Type Tabs */}
              <div className="flex bg-muted rounded-lg p-1 mb-4">
                <button
                  onClick={() => switchMarket('domestic')}
                  className={`flex-1 text-xs px-3 py-2 rounded-md transition-colors flex items-center justify-center gap-1 ${
                    currentMarket === 'domestic'
                      ? 'bg-background shadow-sm text-foreground font-medium'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Building2 className="w-3 h-3" />
                  국내
                </button>
                <button
                  onClick={() => switchMarket('overseas')}
                  className={`flex-1 text-xs px-3 py-2 rounded-md transition-colors flex items-center justify-center gap-1 ${
                    currentMarket === 'overseas'
                      ? 'bg-background shadow-sm text-foreground font-medium'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Globe className="w-3 h-3" />
                  해외
                </button>
              </div>
              
              {currentMarket === 'domestic' ? (
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground mb-3 px-1">인기 종목</div>
                  {popularStocks.map((stock) => (
                    <div 
                      key={stock.symbol}
                      className={`flex items-center justify-between p-3 rounded-md cursor-pointer transition-colors ${
                        selectedSymbol === stock.symbol 
                          ? 'bg-primary/10 border border-primary/20' 
                          : 'hover:bg-muted/50'
                      }`}
                      onClick={() => {
                        handleSymbolChange(stock.symbol)
                        setShowMobileSidebar(null) // 모바일에서는 선택 후 사이드바 닫기
                      }}
                    >
                      <div>
                        <div className="text-sm font-medium">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                      </div>
                      {selectedSymbol === stock.symbol && (
                        <div className="w-2 h-2 bg-primary rounded-full" />
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Star className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <div className="text-sm mb-2">해외 관심종목이 없습니다</div>
                  <div className="text-xs">해외 종목을 추가해보세요</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {showMobileSidebar === 'right' && (
        <div className="lg:hidden fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="fixed right-0 top-0 bottom-0 w-80 bg-card border-l border-border overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h3 className="font-semibold">시장 정보</h3>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowMobileSidebar(null)}
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-sm mb-3">주요 지수</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium">KOSPI</div>
                    <div className="text-xs text-muted-foreground">한국 종합주가지수</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">2,647.82</div>
                    <div className="text-xs text-red-600">+1.23%</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}