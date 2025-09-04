'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Header from "@/components/layout/Header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
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
    router.push(`/${market}`)
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      {/* 메인 컨텐츠 - 시장 선택 랜딩 페이지 */}
      <main className="container mx-auto px-4 py-8">
        {/* 헤로 섹션 */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="w-16 h-16 bg-primary rounded-lg flex items-center justify-center">
              <BarChart3 className="w-8 h-8 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-4">Quantum Trading Platform</h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            전문적인 차트 분석과 실시간 데이터로 국내외 주식 투자를 시작하세요
          </p>
        </div>

        {/* 시장 선택 카드 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
          
          {/* 국내 시장 카드 */}
          <Card className="relative overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer group"
                onClick={() => handleMarketSelect('domestic')}>
            <CardHeader className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                  <Building2 className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <CardTitle className="text-2xl flex items-center space-x-2">
                    <span>🇰🇷 국내 시장</span>
                    <Badge variant={marketData.domestic.status === 'open' ? 'default' : 'secondary'}>
                      {marketData.domestic.status === 'open' ? '개장' : '휴장'}
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    KOSPI · KOSDAQ · 한국 주식
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* 주요 지수 */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium">KOSPI</div>
                    <div className="text-xs text-muted-foreground">한국 종합주가지수</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">{marketData.domestic.kospi.value.toFixed(2)}</div>
                    <div className={`text-sm flex items-center ${
                      marketData.domestic.kospi.changePercent >= 0 ? 'text-red-600' : 'text-blue-600'
                    }`}>
                      {marketData.domestic.kospi.changePercent >= 0 ? 
                        <TrendingUp className="w-4 h-4 mr-1" /> : 
                        <TrendingDown className="w-4 h-4 mr-1" />
                      }
                      {marketData.domestic.kospi.changePercent >= 0 ? '+' : ''}{marketData.domestic.kospi.changePercent}%
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium">KOSDAQ</div>
                    <div className="text-xs text-muted-foreground">코스닥 지수</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">{marketData.domestic.kosdaq.value.toFixed(2)}</div>
                    <div className={`text-sm flex items-center ${
                      marketData.domestic.kosdaq.changePercent >= 0 ? 'text-red-600' : 'text-blue-600'
                    }`}>
                      {marketData.domestic.kosdaq.changePercent >= 0 ? 
                        <TrendingUp className="w-4 h-4 mr-1" /> : 
                        <TrendingDown className="w-4 h-4 mr-1" />
                      }
                      {marketData.domestic.kosdaq.changePercent >= 0 ? '+' : ''}{marketData.domestic.kosdaq.changePercent}%
                    </div>
                  </div>
                </div>
              </div>

              {/* 거래시간 */}
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">거래시간</span>
                </div>
                <span>{marketData.domestic.openTime} - {marketData.domestic.closeTime}</span>
              </div>

              {/* 인기 종목 */}
              <div>
                <h4 className="text-sm font-medium mb-3">인기 종목</h4>
                <div className="space-y-2">
                  {popularStocks.domestic.map((stock) => (
                    <div key={stock.symbol} className="flex items-center justify-between text-sm">
                      <div>
                        <span className="font-medium">{stock.name}</span>
                        <span className="text-muted-foreground ml-2">{stock.symbol}</span>
                      </div>
                      <div className="text-right">
                        <div>₩{stock.price.toLocaleString()}</div>
                        <div className={`text-xs ${stock.change >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                          {stock.change >= 0 ? '+' : ''}{stock.change}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA 버튼 */}
              <Button 
                className="w-full group-hover:bg-primary/90 transition-colors"
                onClick={() => handleMarketSelect('domestic')}
              >
                국내 시장 거래하기
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </CardContent>
          </Card>

          {/* 해외 시장 카드 */}
          <Card className="relative overflow-hidden hover:shadow-lg transition-all duration-300 cursor-pointer group"
                onClick={() => handleMarketSelect('overseas')}>
            <CardHeader className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                  <Globe className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <CardTitle className="text-2xl flex items-center space-x-2">
                    <span>🇺🇸 해외 시장</span>
                    <Badge variant={marketData.overseas.status === 'open' ? 'default' : 'secondary'}>
                      {marketData.overseas.status === 'open' ? '개장' : '휴장'}
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    S&P 500 · NASDAQ · 미국 주식
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* 주요 지수 */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium">S&P 500</div>
                    <div className="text-xs text-muted-foreground">미국 대형주 지수</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">{marketData.overseas.sp500.value.toFixed(2)}</div>
                    <div className={`text-sm flex items-center ${
                      marketData.overseas.sp500.changePercent >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {marketData.overseas.sp500.changePercent >= 0 ? 
                        <TrendingUp className="w-4 h-4 mr-1" /> : 
                        <TrendingDown className="w-4 h-4 mr-1" />
                      }
                      {marketData.overseas.sp500.changePercent >= 0 ? '+' : ''}{marketData.overseas.sp500.changePercent}%
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium">NASDAQ</div>
                    <div className="text-xs text-muted-foreground">나스닥 지수</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold">{marketData.overseas.nasdaq.value.toFixed(2)}</div>
                    <div className={`text-sm flex items-center ${
                      marketData.overseas.nasdaq.changePercent >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {marketData.overseas.nasdaq.changePercent >= 0 ? 
                        <TrendingUp className="w-4 h-4 mr-1" /> : 
                        <TrendingDown className="w-4 h-4 mr-1" />
                      }
                      {marketData.overseas.nasdaq.changePercent >= 0 ? '+' : ''}{marketData.overseas.nasdaq.changePercent}%
                    </div>
                  </div>
                </div>
              </div>

              {/* 거래시간 */}
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-1">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">거래시간</span>
                </div>
                <span>{marketData.overseas.openTime} - {marketData.overseas.closeTime} {marketData.overseas.timezone}</span>
              </div>

              {/* 인기 종목 */}
              <div>
                <h4 className="text-sm font-medium mb-3">인기 종목</h4>
                <div className="space-y-2">
                  {popularStocks.overseas.map((stock) => (
                    <div key={stock.symbol} className="flex items-center justify-between text-sm">
                      <div>
                        <span className="font-medium">{stock.symbol}</span>
                        <span className="text-muted-foreground ml-2">{stock.name}</span>
                      </div>
                      <div className="text-right">
                        <div>${stock.price.toFixed(2)}</div>
                        <div className={`text-xs ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {stock.change >= 0 ? '+' : ''}{stock.change}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA 버튼 */}
              <Button 
                className="w-full group-hover:bg-primary/90 transition-colors"
                onClick={() => handleMarketSelect('overseas')}
              >
                해외 시장 거래하기
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* 하단 기능 소개 */}
        <div className="mt-16 text-center">
          <h2 className="text-2xl font-bold mb-8">전문적인 트레이딩 도구</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">고급 차트 분석</h3>
              <p className="text-muted-foreground">TradingView 스타일의 전문 차트와 기술 지표</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Activity className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">실시간 데이터</h3>
              <p className="text-muted-foreground">실시간 주가, 뉴스, 시장 지표 업데이트</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                <DollarSign className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold mb-2">다중 시장 지원</h3>
              <p className="text-muted-foreground">국내외 주식, 지수, 환율 통합 관리</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}