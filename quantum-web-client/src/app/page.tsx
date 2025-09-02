'use client'

import { useState } from 'react'
import Header from "@/components/layout/Header"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { useMarket } from '@/contexts/MarketContext'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TradingChart } from "@/components/chart/TradingChart"
import { Button } from "@/components/ui/button"
import { KISConnectionBanner } from "@/components/kis/KISConnectionBanner"
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  Activity, 
  Star, 
  Building2, 
  ChevronRight,
  ChevronLeft,
  X,
  Globe
} from "lucide-react"

export default function Home() {
  const [showMobileSidebar, setShowMobileSidebar] = useState<'left' | 'right' | null>(null)
  const { currentMarket, switchMarket, getMarketDisplayName } = useMarket()
  const { hasKISAccount } = useAuth()

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Header />
        
        {/* KIS Connection Banner */}
        {!hasKISAccount && (
          <div className="p-4 border-b border-border">
            <KISConnectionBanner variant="compact" />
          </div>
        )}
      
      {/* Main Content - 3-Panel Layout */}
      <main className="flex flex-col lg:flex-row flex-1 overflow-hidden min-h-0" style={{ height: 'calc(100vh - 128px)' }}>
        
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
            <div className="text-center py-8 text-muted-foreground">
              <Star className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <div className="text-sm mb-2">
                {currentMarket === 'domestic' ? '국내 관심종목이 없습니다' : '해외 관심종목이 없습니다'}
              </div>
              <div className="text-xs">
                {currentMarket === 'domestic' ? '국내 종목을 추가해보세요' : '해외 종목을 추가해보세요'}
              </div>
            </div>
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
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>차트 분석</CardTitle>
                </CardHeader>
                <CardContent className="h-full pb-4">
                  <TradingChart />
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Market Data */}
        <div className="hidden lg:flex w-80 border-l border-border bg-card flex-col">
          <div className="p-4 border-b border-border">
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
              
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium">KOSDAQ</div>
                  <div className="text-xs text-muted-foreground">코스닥 지수</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">742.15</div>
                  <div className="text-xs text-blue-600">-0.84%</div>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
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
              
              <div className="text-center py-8 text-muted-foreground">
                <Star className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <div className="text-sm mb-2">
                  {currentMarket === 'domestic' ? '국내 관심종목이 없습니다' : '해외 관심종목이 없습니다'}
                </div>
                <div className="text-xs">
                  {currentMarket === 'domestic' ? '국내 종목을 추가해보세요' : '해외 종목을 추가해보세요'}
                </div>
              </div>
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
    </ProtectedRoute>
  )
}