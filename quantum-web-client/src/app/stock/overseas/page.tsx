'use client'

import { useState, useEffect } from 'react'
import Header from "@/components/layout/Header"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useMarket } from '@/contexts/MarketContext'
import { 
  Search, 
  Globe, 
  TrendingUp, 
  TrendingDown,
  Star,
  BarChart3,
  Filter,
  ArrowUpDown,
  Clock
} from "lucide-react"

export default function OverseasStockPage() {
  const { switchMarket, setExchange, selectedExchange } = useMarket()
  const [currentExchange, setCurrentExchange] = useState(selectedExchange || 'NYSE')

  // 페이지 진입 시 마켓 상태를 해외로 변경
  useEffect(() => {
    switchMarket('overseas')
    if (!selectedExchange) {
      setExchange('NYSE')
      setCurrentExchange('NYSE')
    }
  }, [])

  const handleExchangeChange = (exchange: string) => {
    setCurrentExchange(exchange)
    setExchange(exchange as 'NYSE' | 'NASDAQ' | 'AMEX' | 'LSE' | 'TSE' | 'HKSE')
  }

  const getExchangeStatus = (exchange: string) => {
    // 간단한 시간 기반 상태 (실제로는 더 복잡한 로직 필요)
    const now = new Date()
    const currentHour = now.getHours()
    
    switch (exchange) {
      case 'NYSE':
      case 'NASDAQ':
        // 미국 시장 시간 (대략적)
        const isUsOpen = (currentHour >= 23 && currentHour <= 23) || (currentHour >= 0 && currentHour < 6)
        return isUsOpen ? { status: '장 중', color: 'bg-green-100 text-green-800' } : { status: '장 마감', color: 'bg-gray-100 text-gray-800' }
      default:
        return { status: '장 마감', color: 'bg-gray-100 text-gray-800' }
    }
  }

  const exchangeStatus = getExchangeStatus(currentExchange)

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Header />
      
      <main className="container mx-auto p-6">
        {/* 페이지 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold mb-2">해외 종목</h1>
            <p className="text-muted-foreground">
              글로벌 주식 시장의 종목 정보와 실시간 데이터를 확인하세요
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <Select value={currentExchange} onValueChange={handleExchangeChange}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NYSE">뉴욕증권거래소</SelectItem>
                <SelectItem value="NASDAQ">나스닥</SelectItem>
                <SelectItem value="AMEX">아메리칸거래소</SelectItem>
                <SelectItem value="LSE">런던증권거래소</SelectItem>
                <SelectItem value="TSE">도쿄증권거래소</SelectItem>
              </SelectContent>
            </Select>
            
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1 text-sm rounded-full ${exchangeStatus.color}`}>
                {exchangeStatus.status}
              </div>
              <div className="flex items-center text-sm text-muted-foreground">
                <Clock className="w-4 h-4 mr-1" />
                실시간
              </div>
            </div>
          </div>
        </div>

        {/* 검색 및 필터 */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input 
                  placeholder="종목명 또는 심볼을 입력하세요 (예: Apple, AAPL)"
                  className="pl-10"
                />
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  섹터
                </Button>
                <Button variant="outline" size="sm">
                  <ArrowUpDown className="w-4 h-4 mr-2" />
                  정렬
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 주요 지수 - 선택된 거래소에 따라 다름 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {currentExchange === 'NYSE' || currentExchange === 'NASDAQ' ? (
            <>
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">S&P 500</p>
                      <p className="text-2xl font-bold">4,327.78</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center text-red-600">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        <span className="font-semibold">+12.45</span>
                      </div>
                      <div className="text-sm text-red-600">+0.29%</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">NASDAQ</p>
                      <p className="text-2xl font-bold">13,567.98</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center text-blue-600">
                        <TrendingDown className="w-4 h-4 mr-1" />
                        <span className="font-semibold">-23.67</span>
                      </div>
                      <div className="text-sm text-blue-600">-0.17%</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Dow Jones</p>
                      <p className="text-2xl font-bold">34,789.65</p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center text-red-600">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        <span className="font-semibold">+89.34</span>
                      </div>
                      <div className="text-sm text-red-600">+0.26%</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card className="col-span-3">
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">{currentExchange} 지수 정보</p>
                  <p className="text-muted-foreground">
                    {currentExchange} 거래소의 주요 지수 데이터를 준비 중입니다
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 인기 종목 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                인기 종목 ({currentExchange})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(currentExchange === 'NYSE' || currentExchange === 'NASDAQ' ? [
                  { name: 'Apple Inc.', symbol: 'AAPL', price: '$175.43', change: '+$2.67', changeRate: '+1.54%', isUp: true },
                  { name: 'Microsoft Corp.', symbol: 'MSFT', price: '$334.89', change: '-$1.23', changeRate: '-0.37%', isUp: false },
                  { name: 'Tesla Inc.', symbol: 'TSLA', price: '$248.56', change: '+$8.34', changeRate: '+3.47%', isUp: true },
                  { name: 'NVIDIA Corp.', symbol: 'NVDA', price: '$421.78', change: '+$12.45', changeRate: '+3.04%', isUp: true },
                  { name: 'Amazon.com Inc.', symbol: 'AMZN', price: '$142.67', change: '-$0.98', changeRate: '-0.68%', isUp: false }
                ] : [
                  { name: '해당 거래소 데이터 준비 중', symbol: '---', price: '---', change: '---', changeRate: '---', isUp: true }
                ]).map((stock, idx) => (
                  <div key={`${stock.symbol}-${idx}`} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="p-1 h-auto">
                        <Star className="w-4 h-4" />
                      </Button>
                      <div>
                        <div className="font-medium text-sm">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-sm">{stock.price}</div>
                      {stock.change !== '---' && (
                        <div className={`text-xs ${stock.isUp ? 'text-red-600' : 'text-blue-600'}`}>
                          {stock.change} ({stock.changeRate})
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 상승률 상위 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-red-600" />
                상승률 상위
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(currentExchange === 'NYSE' || currentExchange === 'NASDAQ' ? [
                  { name: 'GameStop Corp.', symbol: 'GME', price: '$18.67', change: '+$3.45', changeRate: '+22.69%' },
                  { name: 'AMC Entertainment', symbol: 'AMC', price: '$4.23', change: '+$0.76', changeRate: '+21.90%' },
                  { name: 'Palantir Technologies', symbol: 'PLTR', price: '$15.89', change: '+$2.34', changeRate: '+17.27%' },
                  { name: 'Advanced Micro Devices', symbol: 'AMD', price: '$102.45', change: '+$12.67', changeRate: '+14.12%' },
                  { name: 'Intel Corp.', symbol: 'INTC', price: '$43.56', change: '+$4.23', changeRate: '+10.75%' }
                ] : [
                  { name: '해당 거래소 데이터 준비 중', symbol: '---', price: '---', change: '---', changeRate: '---' }
                ]).map((stock, idx) => (
                  <div key={`${stock.symbol}-${idx}`} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="p-1 h-auto">
                        <Star className="w-4 h-4" />
                      </Button>
                      <div>
                        <div className="font-medium text-sm">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-sm">{stock.price}</div>
                      {stock.change !== '---' && (
                        <div className="text-xs text-red-600">
                          {stock.change} ({stock.changeRate})
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 거래량 상위 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary" />
                거래량 상위
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {(currentExchange === 'NYSE' || currentExchange === 'NASDAQ' ? [
                  { name: 'Apple Inc.', symbol: 'AAPL', volume: '89.5M', price: '$175.43', changeRate: '+1.54%', isUp: true },
                  { name: 'Tesla Inc.', symbol: 'TSLA', volume: '67.8M', price: '$248.56', changeRate: '+3.47%', isUp: true },
                  { name: 'NVIDIA Corp.', symbol: 'NVDA', volume: '45.2M', price: '$421.78', changeRate: '+3.04%', isUp: true },
                  { name: 'Microsoft Corp.', symbol: 'MSFT', volume: '34.7M', price: '$334.89', changeRate: '-0.37%', isUp: false },
                  { name: 'Amazon.com Inc.', symbol: 'AMZN', volume: '28.9M', price: '$142.67', changeRate: '-0.68%', isUp: false }
                ] : [
                  { name: '해당 거래소 데이터 준비 중', symbol: '---', volume: '---', price: '---', changeRate: '---', isUp: true }
                ]).map((stock, idx) => (
                  <div key={`${stock.symbol}-${idx}`} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="p-1 h-auto">
                        <Star className="w-4 h-4" />
                      </Button>
                      <div>
                        <div className="font-medium text-sm">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.volume}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-sm">{stock.price}</div>
                      {stock.changeRate !== '---' && (
                        <div className={`text-xs ${stock.isUp ? 'text-red-600' : 'text-blue-600'}`}>
                          {stock.changeRate}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
      </div>
    </ProtectedRoute>
  )
}