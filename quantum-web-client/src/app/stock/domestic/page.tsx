'use client'

import { useState } from 'react'
import Header from "@/components/layout/Header"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useMarket } from '@/contexts/MarketContext'
import LiveChartContainer from '@/components/chart/LiveChartContainer'

export default function DomesticStockPage() {
  const { currentMarket } = useMarket()
  const [selectedSymbol, setSelectedSymbol] = useState('005930')
  
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

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Header />
        
        <main className="max-w-7xl mx-auto p-6 space-y-6">
          {/* 페이지 헤더 */}
          <div className="space-y-2">
            <h1 className="text-3xl font-bold">국내 주식</h1>
            <p className="text-muted-foreground">
              국내 주식 종목의 실시간 차트와 현재가를 확인할 수 있습니다.
            </p>
          </div>

          {/* 종목 선택 */}
          <Card>
            <CardHeader>
              <CardTitle>종목 선택</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium">종목:</span>
                <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                  <SelectTrigger className="w-64">
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
            </CardContent>
          </Card>

          {/* 실시간 차트 */}
          <LiveChartContainer
            symbol={selectedSymbol}
            stockName={popularStocks.find(s => s.symbol === selectedSymbol)?.name}
            height={600}
          />
        </main>
      </div>
    </ProtectedRoute>
  )
}