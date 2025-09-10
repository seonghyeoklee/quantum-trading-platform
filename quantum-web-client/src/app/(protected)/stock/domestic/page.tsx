'use client'

import { useEffect, useState } from 'react'
import Header from "@/components/layout/Header"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useMarket } from '@/contexts/MarketContext'
import dynamic from 'next/dynamic'

// TradingChart를 동적으로 로드 (SSR 방지)
const TradingChart = dynamic(
  () => import('@/components/chart/TradingChart'),
  { 
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-[400px] border border-border rounded-lg">
      <div className="text-sm text-muted-foreground">차트 로딩중...</div>
    </div>
  }
)

import { kisChartService } from '@/lib/services/kis-chart-service'
import { quantumApiClient } from '@/lib/services/quantum-api-client'
import { 
  TradingViewCandle 
} from '@/lib/services/kis-chart-service'
import { 
  Search, 
  Building2, 
  TrendingUp, 
  TrendingDown,
  Star,
  BarChart3,
  Filter,
  ArrowUpDown,
  Loader2,
  AlertCircle
} from "lucide-react"

export default function DomesticStockPage() {
  const { switchMarket } = useMarket()
  
  // State
  const [selectedSymbol, setSelectedSymbol] = useState('005930') // 삼성전자
  const [chartData, setChartData] = useState<TradingViewCandle[]>([])
  const [chartType, setChartType] = useState<'daily' | 'minute'>('daily')
  const [searchQuery, setSearchQuery] = useState('')
  
  // Loading states
  const [chartLoading, setChartLoading] = useState(false)
  
  // Error states
  const [chartError, setChartError] = useState<string | null>(null)

  // 페이지 진입 시 마켓 상태를 국내로 변경
  useEffect(() => {
    switchMarket('domestic')
  }, [switchMarket])

  // 차트 데이터 조회
  useEffect(() => {
    
    const loadChartData = async () => {
      if (!selectedSymbol) return
      
      try {
        setChartLoading(true)
        setChartError(null)
        console.log('📈 차트 데이터 조회:', selectedSymbol, chartType)
        
        const data = await kisChartService.getTradingViewCandles(selectedSymbol, chartType)
        setChartData(data)
        console.log('✅ 차트 데이터 조회 완료')
        
      } catch (error) {
        console.error('❌ 차트 데이터 조회 실패:', error)
        setChartError('차트 데이터를 불러올 수 없습니다')
      } finally {
        setChartLoading(false)
      }
    }

    loadChartData()
  }, [selectedSymbol, chartType])

  // 종목 선택
  const handleStockSelect = (symbol: string) => {
    setSelectedSymbol(symbol)
    setSearchQuery('')
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <Header />
      
      <main className="container mx-auto p-6">
        {/* 페이지 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold mb-2">해외 종목 - 실시간 차트</h1>
            <p className="text-muted-foreground">
              웹소켓을 이용한 실시간 해외 주식 차트를 테스트합니다
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
              실시간 연결
            </div>
          </div>
        </div>

        {/* 종목 선택 */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input 
                  placeholder="해외 종목코드를 입력하세요 (예: RBAQAAPL)"
                  className="pl-10"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && searchQuery.trim()) {
                      setSelectedSymbol(searchQuery.trim())
                    }
                  }}
                />
              </div>
              
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    if (searchQuery.trim()) {
                      setSelectedSymbol(searchQuery.trim())
                    }
                  }}
                  disabled={!searchQuery.trim()}
                >
                  <Search className="w-4 h-4 mr-2" />
                  변경
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    setSelectedSymbol('RBAQAAPL')
                    setSearchQuery('RBAQAAPL')
                  }}
                >
                  Apple
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    setSelectedSymbol('RBAQMSFT')
                    setSearchQuery('RBAQMSFT')
                  }}
                >
                  Microsoft
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    setSelectedSymbol('RBAQTSLA')
                    setSearchQuery('RBAQTSLA')
                  }}
                >
                  Tesla
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 차트 */}
        {selectedSymbol && (
          <div className="grid grid-cols-1 gap-6 mb-6">

            {/* 차트 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>차트 - {selectedSymbol}</span>
                  <div className="flex gap-2">
                    <Button
                      variant={chartType === 'daily' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setChartType('daily')}
                    >
                      일봉
                    </Button>
                    <Button
                      variant={chartType === 'minute' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setChartType('minute')}
                    >
                      분봉
                    </Button>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {chartLoading ? (
                  <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin mr-2" />
                    <span>차트 데이터를 불러오는 중...</span>
                  </div>
                ) : chartError ? (
                  <div className="flex items-center justify-center py-20 text-red-600">
                    <AlertCircle className="w-8 h-8 mr-2" />
                    <span>{chartError}</span>
                  </div>
                ) : chartData.length > 0 ? (
                  <TradingChart
                    data={chartData}
                    symbol={selectedSymbol}
                    chartType={chartType}
                    width={800}
                    height={400}
                  />
                ) : (
                  <div className="flex items-center justify-center py-20 text-muted-foreground">
                    <span>차트 데이터가 없습니다</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </main>
      </div>
    </ProtectedRoute>
  )
}