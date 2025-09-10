'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MarketCardSkeleton, PageLoadingSkeleton } from "@/components/ui/loading-skeletons"
import { 
  BarChart3, 
  Building2, 
  Globe,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Clock,
  Activity,
  DollarSign
} from "lucide-react"

export default function Home() {
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [loadingProgress, setLoadingProgress] = useState(0)
  
  // 부드러운 로딩 경험
  useEffect(() => {
    // 프로그레스 시뮬레이션
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + Math.random() * 30
      })
    }, 100)

    // 로딩 완료
    const timer = setTimeout(() => {
      setLoadingProgress(100)
      setTimeout(() => {
        setIsLoading(false)
      }, 300) // 부드러운 페이드아웃
    }, 800) // 더 빠른 로딩

    return () => {
      clearTimeout(timer)
      clearInterval(progressInterval)
    }
  }, [])
  
  // Mock 시장 데이터
  const marketData = {
    domestic: {
      kospi: { value: 2647.82, change: 32.15, changePercent: 1.23 },
      kosdaq: { value: 742.15, change: -6.28, changePercent: -0.84 },
      status: 'open', // open, closed, pre-market, after-hours
      openTime: '09:00',
      closeTime: '15:30',
    },
    overseas: {
      sp500: { value: 4234.87, change: 28.45, changePercent: 0.68 },
      nasdaq: { value: 14567.92, change: -45.23, changePercent: -0.31 },
      status: 'open',
      openTime: '09:30',
      closeTime: '16:00',
      timezone: 'EST'
    }
  }

  const popularStocks = {
    domestic: [
      { symbol: '005930', name: '삼성전자', price: 75200, change: 1.62 },
      { symbol: '000660', name: 'SK하이닉스', price: 123000, change: -1.60 },
      { symbol: '035420', name: 'NAVER', price: 198500, change: 1.79 },
    ],
    overseas: [
      { symbol: 'AAPL', name: 'Apple Inc.', price: 189.25, change: 1.15 },
      { symbol: 'MSFT', name: 'Microsoft Corp.', price: 334.89, change: -0.96 },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 138.12, change: 1.37 },
    ]
  }

  const handleMarketSelect = (market: 'domestic' | 'overseas') => {
    // (protected) 라우트 그룹 내부에서 상대 경로로 이동
    router.push(`./${market}`)
  }

  // 개선된 로딩 상태 렌더링
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-8 max-w-md mx-auto px-6">
          {/* 로고 애니메이션 */}
          <div className="flex items-center justify-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-br from-primary to-primary/80 rounded-xl flex items-center justify-center shadow-lg animate-pulse">
              <BarChart3 className="w-8 h-8 text-white animate-pulse" />
            </div>
          </div>
          
          {/* 브랜드명 */}
          <div className="space-y-2">
            <h1 className="text-2xl font-bold text-foreground">
              Quantum Trading
            </h1>
            <p className="text-muted-foreground text-sm">
              시장 데이터를 불러오는 중...
            </p>
          </div>
          
          {/* 세련된 프로그레스 바 */}
          <div className="space-y-3">
            <div className="w-full bg-muted rounded-full h-1 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-primary to-primary/80 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${Math.min(loadingProgress, 100)}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              {Math.min(Math.round(loadingProgress), 100)}% 완료
            </p>
          </div>
          
          {/* 로딩 메시지 */}
          <div className="text-xs text-muted-foreground space-y-1">
            <p>실시간 주식 데이터 연결 중...</p>
            <div className="flex justify-center space-x-1">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">      
      {/* 메인 컨텐츠 - 시장 선택 랜딩 페이지 */}
      <main className="container mx-auto px-3 sm:px-4 py-6 sm:py-8">
        {/* 헤로 섹션 - 부드러운 페이드인 */}
        <div className="text-center mb-8 sm:mb-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center justify-center mb-4 sm:mb-6">
            <div className="w-12 h-12 sm:w-16 sm:h-16 bg-primary rounded-xl flex items-center justify-center shadow-lg">
              <BarChart3 className="w-6 h-6 sm:w-8 sm:h-8 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-3 sm:mb-4 text-foreground px-2">
            Quantum Trading Platform
          </h1>
          <p className="text-sm sm:text-lg lg:text-xl text-muted-foreground mb-6 sm:mb-8 max-w-2xl mx-auto px-4">
            전문적인 차트 분석과 실시간 데이터로<br className="sm:hidden" />
            <span className="sm:inline"> </span>국내외 주식 투자를 시작하세요
          </p>
        </div>

        {/* 시장 선택 카드 - 부드러운 스태거 애니메이션 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8 max-w-6xl mx-auto">
          
          {/* 국내 시장 카드 */}
          <div className="animate-in fade-in slide-in-from-left-8 duration-700 delay-200">
            <Card className="relative overflow-hidden cursor-pointer group border hover:border-primary/30 transition-all duration-300 hover:shadow-lg"
                  onClick={() => handleMarketSelect('domestic')}>
            {/* 그라디언트 배경 효과 */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-white to-indigo-50/30 dark:from-blue-950/20 dark:via-background dark:to-indigo-950/10" />
            
            {/* 카드 헤더 개선 - 모바일 최적화 */}
            <CardHeader className="relative space-y-3 sm:space-y-4 pb-3 sm:pb-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3 sm:space-x-4 flex-1 min-w-0">
                  <div className="relative flex-shrink-0">
                    <div className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-blue-500/25 transition-all duration-300 hover-bounce">
                      <Building2 className="w-6 h-6 sm:w-7 sm:h-7 text-white transition-transform group-hover:scale-110" />
                    </div>
                    {/* 상태 표시 점 - 애니메이션 개선 */}
                    <div className={`absolute -top-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 rounded-full border-2 border-white transition-all duration-300 ${
                      marketData.domestic.status === 'open' 
                        ? 'bg-emerald-500 animate-bounce-subtle animate-glow' 
                        : 'bg-gray-400'
                    }`} />
                  </div>
                  <div className="space-y-1 min-w-0 flex-1">
                    <CardTitle className="text-lg sm:text-xl lg:text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-200 bg-clip-text text-transparent">
                      🇰🇷 국내 시장
                    </CardTitle>
                    <CardDescription className="text-xs sm:text-sm text-muted-foreground font-medium">
                      KOSPI · KOSDAQ · 한국거래소
                    </CardDescription>
                  </div>
                </div>
                <Badge 
                  variant={marketData.domestic.status === 'open' ? 'default' : 'secondary'}
                  className={`ml-2 flex-shrink-0 text-xs ${
                    marketData.domestic.status === 'open' 
                      ? 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400' 
                      : ''
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full mr-1 sm:mr-2 ${
                    marketData.domestic.status === 'open' ? 'bg-emerald-500' : 'bg-gray-400'
                  }`} />
                  <span className="hidden sm:inline">{marketData.domestic.status === 'open' ? '실시간 거래중' : '시장 휴장'}</span>
                  <span className="sm:hidden">{marketData.domestic.status === 'open' ? '거래중' : '휴장'}</span>
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="relative space-y-4 sm:space-y-6">
              {/* 주요 지수 - 모바일 최적화 */}
              <div className="space-y-3">
                <h3 className="text-xs sm:text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3 sm:mb-4">
                  실시간 지수
                </h3>
                
                {/* KOSPI - 모바일 최적화 */}
                <div className="bg-white/60 dark:bg-gray-800/30 rounded-lg p-3 sm:p-4 border border-gray-100 dark:border-gray-700/50 hover:shadow-md transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="font-semibold text-base sm:text-lg">KOSPI</div>
                      <div className="text-xs text-muted-foreground">한국종합주가지수</div>
                    </div>
                    <div className="text-right space-y-1">
                      <div className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">
                        {marketData.domestic.kospi.value.toLocaleString()}
                      </div>
                      <div className={`text-xs sm:text-sm font-medium flex items-center justify-end ${
                        marketData.domestic.kospi.changePercent >= 0 
                          ? 'text-red-600 dark:text-red-400' 
                          : 'text-blue-600 dark:text-blue-400'
                      }`}>
                        {marketData.domestic.kospi.changePercent >= 0 ? 
                          <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 mr-1" /> : 
                          <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                        }
                        <span>
                          {marketData.domestic.kospi.changePercent >= 0 ? '+' : ''}
                          {marketData.domestic.kospi.change.toFixed(2)} ({marketData.domestic.kospi.changePercent}%)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* KOSDAQ - 모바일 최적화 */}
                <div className="bg-white/60 dark:bg-gray-800/30 rounded-lg p-3 sm:p-4 border border-gray-100 dark:border-gray-700/50 hover:shadow-md transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="font-semibold text-base sm:text-lg">KOSDAQ</div>
                      <div className="text-xs text-muted-foreground">코스닥지수</div>
                    </div>
                    <div className="text-right space-y-1">
                      <div className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">
                        {marketData.domestic.kosdaq.value.toLocaleString()}
                      </div>
                      <div className={`text-xs sm:text-sm font-medium flex items-center justify-end ${
                        marketData.domestic.kosdaq.changePercent >= 0 
                          ? 'text-red-600 dark:text-red-400' 
                          : 'text-blue-600 dark:text-blue-400'
                      }`}>
                        {marketData.domestic.kosdaq.changePercent >= 0 ? 
                          <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 mr-1" /> : 
                          <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                        }
                        <span>
                          {marketData.domestic.kosdaq.changePercent >= 0 ? '+' : ''}
                          {marketData.domestic.kosdaq.change.toFixed(2)} ({marketData.domestic.kosdaq.changePercent}%)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 거래시간 개선 */}
              <div className="bg-white/40 dark:bg-gray-800/20 rounded-lg p-3 border border-gray-100 dark:border-gray-700/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/40 rounded-lg flex items-center justify-center">
                      <Clock className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground font-medium">거래시간</div>
                      <div className="text-sm font-semibold">{marketData.domestic.openTime} - {marketData.domestic.closeTime} KST</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">현재</div>
                    <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                      {new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              </div>

              {/* 인기 종목 개선 */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                  오늘의 인기 종목
                </h4>
                <div className="space-y-2">
                  {popularStocks.domestic.map((stock) => (
                    <div key={stock.symbol} className="bg-white/40 dark:bg-gray-800/20 rounded-lg p-3 border border-gray-100 dark:border-gray-700/30 hover:shadow-md hover:scale-[1.01] transition-all duration-200">
                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <div className="font-semibold text-sm">{stock.name}</div>
                          <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                        </div>
                        <div className="text-right space-y-1">
                          <div className="font-bold">₩{stock.price.toLocaleString()}</div>
                          <div className={`text-xs font-medium flex items-center justify-end ${
                            stock.change >= 0 
                              ? 'text-red-600 dark:text-red-400' 
                              : 'text-blue-600 dark:text-blue-400'
                          }`}>
                            {stock.change >= 0 ? 
                              <TrendingUp className="w-3 h-3 mr-1" /> : 
                              <TrendingDown className="w-3 h-3 mr-1" />
                            }
                            {stock.change >= 0 ? '+' : ''}{stock.change}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA 버튼 개선 */}
              <Button 
                size="lg"
                className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group"
                onClick={() => handleMarketSelect('domestic')}
              >
                <Building2 className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" />
                국내 시장 거래하기
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </CardContent>
            </Card>
          </div>

          {/* 해외 시장 카드 */}
          <div className="animate-in fade-in slide-in-from-right-8 duration-700 delay-300">
            <Card className="relative overflow-hidden cursor-pointer group border hover:border-primary/30 transition-all duration-300 hover:shadow-lg"
                  onClick={() => handleMarketSelect('overseas')}>
            {/* 그라디언트 배경 효과 */}
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-50/50 via-white to-green-50/30 dark:from-emerald-950/20 dark:via-background dark:to-green-950/10" />
            
            {/* 카드 헤더 개선 - 모바일 최적화 */}
            <CardHeader className="relative space-y-3 sm:space-y-4 pb-3 sm:pb-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3 sm:space-x-4 flex-1 min-w-0">
                  <div className="relative flex-shrink-0">
                    <div className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-emerald-500/25 transition-all duration-300 hover-bounce">
                      <Globe className="w-6 h-6 sm:w-7 sm:h-7 text-white transition-transform group-hover:scale-110" />
                    </div>
                    {/* 상태 표시 점 - 애니메이션 개선 */}
                    <div className={`absolute -top-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 rounded-full border-2 border-white transition-all duration-300 ${
                      marketData.overseas.status === 'open' 
                        ? 'bg-emerald-500 animate-bounce-subtle animate-glow' 
                        : 'bg-gray-400'
                    }`} />
                  </div>
                  <div className="space-y-1 min-w-0 flex-1">
                    <CardTitle className="text-lg sm:text-xl lg:text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 dark:from-white dark:to-gray-200 bg-clip-text text-transparent">
                      🇺🇸 해외 시장
                    </CardTitle>
                    <CardDescription className="text-xs sm:text-sm text-muted-foreground font-medium">
                      S&P 500 · NASDAQ · 뉴욕증권거래소
                    </CardDescription>
                  </div>
                </div>
                <Badge 
                  variant={marketData.overseas.status === 'open' ? 'default' : 'secondary'}
                  className={`ml-2 flex-shrink-0 text-xs ${
                    marketData.overseas.status === 'open' 
                      ? 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400' 
                      : ''
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full mr-1 sm:mr-2 ${
                    marketData.overseas.status === 'open' ? 'bg-emerald-500' : 'bg-gray-400'
                  }`} />
                  <span className="hidden sm:inline">{marketData.overseas.status === 'open' ? '실시간 거래중' : '시장 휴장'}</span>
                  <span className="sm:hidden">{marketData.overseas.status === 'open' ? '거래중' : '휴장'}</span>
                </Badge>
              </div>
            </CardHeader>
            
            <CardContent className="relative space-y-4 sm:space-y-6">
              {/* 주요 지수 - 모바일 최적화 */}
              <div className="space-y-3">
                <h3 className="text-xs sm:text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3 sm:mb-4">
                  실시간 지수
                </h3>
                
                {/* S&P 500 - 모바일 최적화 */}
                <div className="bg-white/60 dark:bg-gray-800/30 rounded-lg p-3 sm:p-4 border border-gray-100 dark:border-gray-700/50 hover:shadow-md transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="font-semibold text-base sm:text-lg">S&P 500</div>
                      <div className="text-xs text-muted-foreground">미국 대형주 지수</div>
                    </div>
                    <div className="text-right space-y-1">
                      <div className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">
                        {marketData.overseas.sp500.value.toLocaleString()}
                      </div>
                      <div className={`text-xs sm:text-sm font-medium flex items-center justify-end ${
                        marketData.overseas.sp500.changePercent >= 0 
                          ? 'text-emerald-600 dark:text-emerald-400' 
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {marketData.overseas.sp500.changePercent >= 0 ? 
                          <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 mr-1" /> : 
                          <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                        }
                        <span>
                          {marketData.overseas.sp500.changePercent >= 0 ? '+' : ''}
                          {marketData.overseas.sp500.change.toFixed(2)} ({marketData.overseas.sp500.changePercent}%)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* NASDAQ - 모바일 최적화 */}
                <div className="bg-white/60 dark:bg-gray-800/30 rounded-lg p-3 sm:p-4 border border-gray-100 dark:border-gray-700/50 hover:shadow-md transition-all duration-200">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="font-semibold text-base sm:text-lg">NASDAQ</div>
                      <div className="text-xs text-muted-foreground">나스닥 종합지수</div>
                    </div>
                    <div className="text-right space-y-1">
                      <div className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">
                        {marketData.overseas.nasdaq.value.toLocaleString()}
                      </div>
                      <div className={`text-xs sm:text-sm font-medium flex items-center justify-end ${
                        marketData.overseas.nasdaq.changePercent >= 0 
                          ? 'text-emerald-600 dark:text-emerald-400' 
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {marketData.overseas.nasdaq.changePercent >= 0 ? 
                          <TrendingUp className="w-3 h-3 sm:w-4 sm:h-4 mr-1" /> : 
                          <TrendingDown className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                        }
                        <span>
                          {marketData.overseas.nasdaq.changePercent >= 0 ? '+' : ''}
                          {marketData.overseas.nasdaq.change.toFixed(2)} ({marketData.overseas.nasdaq.changePercent}%)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 거래시간 개선 */}
              <div className="bg-white/40 dark:bg-gray-800/20 rounded-lg p-3 border border-gray-100 dark:border-gray-700/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-emerald-100 dark:bg-emerald-900/40 rounded-lg flex items-center justify-center">
                      <Clock className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground font-medium">거래시간</div>
                      <div className="text-sm font-semibold">{marketData.overseas.openTime} - {marketData.overseas.closeTime} {marketData.overseas.timezone}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">현재 (EST)</div>
                    <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                      {new Date().toLocaleTimeString('en-US', { 
                        timeZone: 'America/New_York',
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {/* 인기 종목 개선 */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                  오늘의 인기 종목
                </h4>
                <div className="space-y-2">
                  {popularStocks.overseas.map((stock) => (
                    <div key={stock.symbol} className="bg-white/40 dark:bg-gray-800/20 rounded-lg p-3 border border-gray-100 dark:border-gray-700/30 hover:shadow-md hover:scale-[1.01] transition-all duration-200">
                      <div className="flex items-center justify-between">
                        <div className="space-y-1">
                          <div className="font-semibold text-sm">{stock.symbol}</div>
                          <div className="text-xs text-muted-foreground">{stock.name}</div>
                        </div>
                        <div className="text-right space-y-1">
                          <div className="font-bold">${stock.price.toFixed(2)}</div>
                          <div className={`text-xs font-medium flex items-center justify-end ${
                            stock.change >= 0 
                              ? 'text-emerald-600 dark:text-emerald-400' 
                              : 'text-red-600 dark:text-red-400'
                          }`}>
                            {stock.change >= 0 ? 
                              <TrendingUp className="w-3 h-3 mr-1" /> : 
                              <TrendingDown className="w-3 h-3 mr-1" />
                            }
                            {stock.change >= 0 ? '+' : ''}{stock.change}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA 버튼 개선 */}
              <Button 
                size="lg"
                className="w-full bg-gradient-to-r from-emerald-600 to-green-700 hover:from-emerald-700 hover:to-green-800 text-white shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all duration-300 group"
                onClick={() => handleMarketSelect('overseas')}
              >
                <Globe className="w-4 h-4 mr-2 group-hover:scale-110 transition-transform" />
                해외 시장 거래하기
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </CardContent>
            </Card>
          </div>
        </div>

      </main>
    </div>
  )
}