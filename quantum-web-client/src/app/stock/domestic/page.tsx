'use client'

import { useEffect, useState } from 'react'
import Header from "@/components/layout/Header"
import ProtectedRoute from "@/components/auth/ProtectedRoute"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useMarket } from '@/contexts/MarketContext'
import dynamic from 'next/dynamic'

// KISChart를 동적으로 로드 (SSR 방지)
const KISChart = dynamic(
  () => import('@/components/chart/KISChart'),
  { 
    ssr: false,
    loading: () => <div className="flex items-center justify-center h-[400px] border border-border rounded-lg">
      <div className="text-sm text-muted-foreground">차트 로딩중...</div>
    </div>
  }
)
import { kisDomesticClient } from '@/lib/services/kis-domestic-client'
import { kisChartService } from '@/lib/services/kis-chart-service'
import { 
  KISDomesticIndices, 
  KISDomesticPrice, 
  KISDomesticSearchResult,
  TradingViewCandle 
} from '@/lib/types/kis-domestic-types'
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
  const [indices, setIndices] = useState<KISDomesticIndices | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState('005930') // 삼성전자
  const [stockPrice, setStockPrice] = useState<KISDomesticPrice | null>(null)
  const [chartData, setChartData] = useState<TradingViewCandle[]>([])
  const [chartType, setChartType] = useState<'daily' | 'minute'>('daily')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<KISDomesticSearchResult | null>(null)
  
  // Loading states
  const [indicesLoading, setIndicesLoading] = useState(true)
  const [stockLoading, setStockLoading] = useState(false)
  const [chartLoading, setChartLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  
  // Error states
  const [indicesError, setIndicesError] = useState<string | null>(null)
  const [stockError, setStockError] = useState<string | null>(null)
  const [chartError, setChartError] = useState<string | null>(null)

  // 페이지 진입 시 마켓 상태를 국내로 변경
  useEffect(() => {
    switchMarket('domestic')
  }, [switchMarket])

  // 시장지수 조회
  useEffect(() => {
    const loadIndices = async () => {
      try {
        setIndicesLoading(true)
        setIndicesError(null)
        console.log('📊 국내 시장지수 조회 시작')
        
        const data = await kisDomesticClient.getDomesticIndices()
        setIndices(data)
        console.log('✅ 국내 시장지수 조회 완료')
        
      } catch (error) {
        console.error('❌ 국내 시장지수 조회 실패:', error)
        setIndicesError('시장지수를 불러올 수 없습니다')
      } finally {
        setIndicesLoading(false)
      }
    }

    loadIndices()
  }, [])

  // 선택된 종목 현재가 조회
  useEffect(() => {
    const loadStockPrice = async () => {
      if (!selectedSymbol) return
      
      try {
        setStockLoading(true)
        setStockError(null)
        console.log('💰 종목 현재가 조회:', selectedSymbol)
        
        const data = await kisDomesticClient.getDomesticPrice(selectedSymbol)
        setStockPrice(data)
        console.log('✅ 종목 현재가 조회 완료')
        
      } catch (error) {
        console.error('❌ 종목 현재가 조회 실패:', error)
        setStockError('종목 정보를 불러올 수 없습니다')
      } finally {
        setStockLoading(false)
      }
    }

    loadStockPrice()
  }, [selectedSymbol])

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

  // 종목 검색
  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    try {
      setSearchLoading(true)
      console.log('🔍 종목 검색:', searchQuery)
      
      const data = await kisDomesticClient.searchDomestic(searchQuery.trim())
      setSearchResults(data)
      console.log('✅ 종목 검색 완료')
      
    } catch (error) {
      console.error('❌ 종목 검색 실패:', error)
    } finally {
      setSearchLoading(false)
    }
  }

  // 종목 선택
  const handleStockSelect = (symbol: string) => {
    setSelectedSymbol(symbol)
    setSearchResults(null) // 검색 결과 닫기
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
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
              
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleSearch}
                  disabled={searchLoading}
                >
                  {searchLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Search className="w-4 h-4 mr-2" />
                  )}
                  검색
                </Button>
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

            {/* 검색 결과 */}
            {searchResults && (
              <div className="mt-4 border rounded-lg p-4 bg-muted/50">
                <h3 className="font-medium mb-3">검색 결과 ({searchResults.total}개)</h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {searchResults.items.map((item, idx) => (
                    <div 
                      key={idx}
                      className="flex items-center justify-between p-2 hover:bg-background rounded cursor-pointer"
                      onClick={() => handleStockSelect(item.symbol)}
                    >
                      <div>
                        <div className="font-medium">{item.name}</div>
                        <div className="text-xs text-muted-foreground">{item.symbol} • {item.market}</div>
                      </div>
                      {item.price && (
                        <div className="text-right">
                          <div className="font-medium">{item.price.toLocaleString()}원</div>
                          {item.changePercent && (
                            <div className={`text-xs ${item.changePercent >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                              {item.changePercent >= 0 ? '+' : ''}{item.changePercent.toFixed(2)}%
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 시장지수 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {indicesLoading ? (
            <Card className="col-span-3">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center">
                  <Loader2 className="w-6 h-6 animate-spin mr-2" />
                  <span>시장지수를 불러오는 중...</span>
                </div>
              </CardContent>
            </Card>
          ) : indicesError ? (
            <Card className="col-span-3">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center text-red-600">
                  <AlertCircle className="w-6 h-6 mr-2" />
                  <span>{indicesError}</span>
                </div>
              </CardContent>
            </Card>
          ) : indices ? (
            <>
              {/* KOSPI */}
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">KOSPI</p>
                      <p className="text-2xl font-bold">{indices.kospi.value.toFixed(2)}</p>
                    </div>
                    <div className="text-right">
                      <div className={`flex items-center ${indices.kospi.change >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                        {indices.kospi.change >= 0 ? (
                          <TrendingUp className="w-4 h-4 mr-1" />
                        ) : (
                          <TrendingDown className="w-4 h-4 mr-1" />
                        )}
                        <span className="font-semibold">
                          {indices.kospi.change >= 0 ? '+' : ''}{indices.kospi.change.toFixed(2)}
                        </span>
                      </div>
                      <div className={`text-sm ${indices.kospi.changePercent >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                        {indices.kospi.changePercent >= 0 ? '+' : ''}{indices.kospi.changePercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* KOSDAQ */}
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">KOSDAQ</p>
                      <p className="text-2xl font-bold">{indices.kosdaq.value.toFixed(2)}</p>
                    </div>
                    <div className="text-right">
                      <div className={`flex items-center ${indices.kosdaq.change >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                        {indices.kosdaq.change >= 0 ? (
                          <TrendingUp className="w-4 h-4 mr-1" />
                        ) : (
                          <TrendingDown className="w-4 h-4 mr-1" />
                        )}
                        <span className="font-semibold">
                          {indices.kosdaq.change >= 0 ? '+' : ''}{indices.kosdaq.change.toFixed(2)}
                        </span>
                      </div>
                      <div className={`text-sm ${indices.kosdaq.changePercent >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                        {indices.kosdaq.changePercent >= 0 ? '+' : ''}{indices.kosdaq.changePercent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* KOSPI200 또는 KRX300 */}
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        {indices.kospi200?.name || indices.krx300?.name || 'KRX 300'}
                      </p>
                      <p className="text-2xl font-bold">
                        {(indices.kospi200?.value || indices.krx300?.value || 1245.67).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center text-red-600">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        <span className="font-semibold">
                          +{(indices.kospi200?.change || indices.krx300?.change || 5.32).toFixed(2)}
                        </span>
                      </div>
                      <div className="text-sm text-red-600">
                        +{(indices.kospi200?.changePercent || indices.krx300?.changePercent || 0.43).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>

        {/* 선택된 종목 정보 및 차트 */}
        {selectedSymbol && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* 종목 정보 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>종목 정보</span>
                  <Button variant="ghost" size="sm">
                    <Star className="w-4 h-4" />
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {stockLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin mr-2" />
                    <span>종목 정보 로딩 중...</span>
                  </div>
                ) : stockError ? (
                  <div className="flex items-center justify-center py-8 text-red-600">
                    <AlertCircle className="w-6 h-6 mr-2" />
                    <span>{stockError}</span>
                  </div>
                ) : stockPrice ? (
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-bold text-lg">{stockPrice.name}</h3>
                      <p className="text-sm text-muted-foreground">{stockPrice.symbol}</p>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>현재가</span>
                        <span className="font-bold text-lg">{stockPrice.price.toLocaleString()}원</span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span>전일대비</span>
                        <div className={`${stockPrice.change >= 0 ? 'text-red-600' : 'text-blue-600'}`}>
                          <span className="font-medium">
                            {stockPrice.change >= 0 ? '+' : ''}{stockPrice.change.toLocaleString()}원
                          </span>
                          <span className="ml-2">
                            ({stockPrice.changePercent >= 0 ? '+' : ''}{stockPrice.changePercent.toFixed(2)}%)
                          </span>
                        </div>
                      </div>

                      <div className="flex justify-between">
                        <span>거래량</span>
                        <span>{stockPrice.volume.toLocaleString()}주</span>
                      </div>

                      <div className="flex justify-between">
                        <span>고가</span>
                        <span>{stockPrice.high.toLocaleString()}원</span>
                      </div>

                      <div className="flex justify-between">
                        <span>저가</span>
                        <span>{stockPrice.low.toLocaleString()}원</span>
                      </div>

                      <div className="flex justify-between">
                        <span>시가</span>
                        <span>{stockPrice.open.toLocaleString()}원</span>
                      </div>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>

            {/* 차트 */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>차트</span>
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
                  <KISChart
                    data={chartData}
                    symbol={selectedSymbol}
                    chartType={chartType}
                    width={600}
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