'use client'

import { useEffect } from 'react'
import Header from "@/components/layout/Header"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useMarket } from '@/contexts/MarketContext'
import { 
  Search, 
  Building2, 
  TrendingUp, 
  TrendingDown,
  Star,
  BarChart3,
  Filter,
  ArrowUpDown
} from "lucide-react"

export default function DomesticStockPage() {
  const { switchMarket } = useMarket()

  // 페이지 진입 시 마켓 상태를 국내로 변경
  useEffect(() => {
    switchMarket('domestic')
  }, [])

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Header />
      
      <main className="container mx-auto p-6">
        {/* 페이지 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold mb-2">국내 종목</h1>
            <p className="text-muted-foreground">
              한국 주식 시장의 종목 정보와 실시간 데이터를 확인하세요
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
              장 마감
            </div>
            <div className="text-sm text-muted-foreground">
              16:00 기준
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
                  placeholder="종목명 또는 종목코드를 입력하세요 (예: 삼성전자, 005930)"
                  className="pl-10"
                />
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-2" />
                  필터
                </Button>
                <Button variant="outline" size="sm">
                  <ArrowUpDown className="w-4 h-4 mr-2" />
                  정렬
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 주요 지수 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">KOSPI</p>
                  <p className="text-2xl font-bold">2,647.82</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center text-red-600">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    <span className="font-semibold">+32.45</span>
                  </div>
                  <div className="text-sm text-red-600">+1.23%</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">KOSDAQ</p>
                  <p className="text-2xl font-bold">742.15</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center text-blue-600">
                    <TrendingDown className="w-4 h-4 mr-1" />
                    <span className="font-semibold">-6.23</span>
                  </div>
                  <div className="text-sm text-blue-600">-0.84%</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">KRX 300</p>
                  <p className="text-2xl font-bold">1,245.67</p>
                </div>
                <div className="text-right">
                  <div className="flex items-center text-red-600">
                    <TrendingUp className="w-4 h-4 mr-1" />
                    <span className="font-semibold">+5.32</span>
                  </div>
                  <div className="text-sm text-red-600">+0.43%</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 인기 종목 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                인기 종목
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: '삼성전자', code: '005930', price: '71,900', change: '+1,200', changeRate: '+1.69%', isUp: true },
                  { name: 'SK하이닉스', code: '000660', price: '135,500', change: '-2,500', changeRate: '-1.81%', isUp: false },
                  { name: 'LG에너지솔루션', code: '373220', price: '412,000', change: '+8,000', changeRate: '+1.98%', isUp: true },
                  { name: '삼성바이오로직스', code: '207940', price: '891,000', change: '+15,000', changeRate: '+1.71%', isUp: true },
                  { name: 'NAVER', code: '035420', price: '189,500', change: '-3,000', changeRate: '-1.56%', isUp: false }
                ].map((stock, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="p-1 h-auto">
                        <Star className="w-4 h-4" />
                      </Button>
                      <div>
                        <div className="font-medium text-sm">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.code}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-sm">{stock.price}</div>
                      <div className={`text-xs ${stock.isUp ? 'text-red-600' : 'text-blue-600'}`}>
                        {stock.change} ({stock.changeRate})
                      </div>
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
                {[
                  { name: '셀트리온', code: '068270', price: '163,500', change: '+14,800', changeRate: '+9.95%' },
                  { name: '카카오', code: '035720', price: '45,250', change: '+3,750', changeRate: '+9.03%' },
                  { name: 'LG화학', code: '051910', price: '543,000', change: '+39,000', changeRate: '+7.74%' },
                  { name: '현대차', code: '005380', price: '198,500', change: '+13,500', changeRate: '+7.30%' },
                  { name: 'POSCO홀딩스', code: '005490', price: '387,000', change: '+25,500', changeRate: '+7.05%' }
                ].map((stock, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="p-1 h-auto">
                        <Star className="w-4 h-4" />
                      </Button>
                      <div>
                        <div className="font-medium text-sm">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.code}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-sm">{stock.price}</div>
                      <div className="text-xs text-red-600">
                        {stock.change} ({stock.changeRate})
                      </div>
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
                <Building2 className="w-5 h-5 text-primary" />
                거래량 상위
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: '삼성전자', code: '005930', volume: '24,567,832', price: '71,900', changeRate: '+1.69%', isUp: true },
                  { name: 'SK하이닉스', code: '000660', volume: '8,945,621', price: '135,500', changeRate: '-1.81%', isUp: false },
                  { name: '카카오뱅크', code: '323410', volume: '7,234,567', price: '28,350', changeRate: '+2.34%', isUp: true },
                  { name: 'NAVER', code: '035420', volume: '5,678,432', price: '189,500', changeRate: '-1.56%', isUp: false },
                  { name: 'LG에너지솔루션', code: '373220', volume: '4,567,891', price: '412,000', changeRate: '+1.98%', isUp: true }
                ].map((stock, idx) => (
                  <div key={idx} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" className="p-1 h-auto">
                        <Star className="w-4 h-4" />
                      </Button>
                      <div>
                        <div className="font-medium text-sm">{stock.name}</div>
                        <div className="text-xs text-muted-foreground">{stock.volume}주</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-sm">{stock.price}</div>
                      <div className={`text-xs ${stock.isUp ? 'text-red-600' : 'text-blue-600'}`}>
                        {stock.changeRate}
                      </div>
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