'use client'

import { useState, useEffect } from 'react'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useMarket } from '@/contexts/MarketContext'
import { Search, Building2, Globe, Star, Plus } from 'lucide-react'

interface StockSearchResult {
  symbol: string
  name: string
  exchange?: string
  price?: string
  change?: string
  changeRate?: string
  isUp?: boolean
}

interface StockSearchInputProps {
  onSelectStock?: (stock: StockSearchResult) => void
  placeholder?: string
  className?: string
}

export function StockSearchInput({ 
  onSelectStock, 
  placeholder, 
  className 
}: StockSearchInputProps) {
  const { currentMarket, selectedExchange } = useMarket()
  const [searchTerm, setSearchTerm] = useState('')
  const [results, setResults] = useState<StockSearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)

  const getDefaultPlaceholder = () => {
    if (currentMarket === 'domestic') {
      return '종목명 또는 종목코드 검색 (예: 삼성전자, 005930)'
    } else {
      return `${selectedExchange || '해외'} 종목 검색 (예: Apple, AAPL)`
    }
  }

  // 모의 검색 데이터 (향후 KIS API로 대체)
  const getMockSearchResults = (query: string): StockSearchResult[] => {
    if (currentMarket === 'domestic') {
      const domesticStocks: StockSearchResult[] = [
        { symbol: '005930', name: '삼성전자', price: '71,900', change: '+1,200', changeRate: '+1.69%', isUp: true },
        { symbol: '000660', name: 'SK하이닉스', price: '135,500', change: '-2,500', changeRate: '-1.81%', isUp: false },
        { symbol: '035420', name: 'NAVER', price: '189,500', change: '-3,000', changeRate: '-1.56%', isUp: false },
        { symbol: '035720', name: '카카오', price: '45,250', change: '+3,750', changeRate: '+9.03%', isUp: true },
        { symbol: '207940', name: '삼성바이오로직스', price: '891,000', change: '+15,000', changeRate: '+1.71%', isUp: true }
      ]
      
      return domesticStocks.filter(stock => 
        stock.name.toLowerCase().includes(query.toLowerCase()) ||
        stock.symbol.includes(query)
      )
    } else {
      const overseasStocks: StockSearchResult[] = [
        { symbol: 'AAPL', name: 'Apple Inc.', exchange: selectedExchange || 'NASDAQ', price: '$175.43', change: '+$2.67', changeRate: '+1.54%', isUp: true },
        { symbol: 'MSFT', name: 'Microsoft Corp.', exchange: selectedExchange || 'NASDAQ', price: '$334.89', change: '-$1.23', changeRate: '-0.37%', isUp: false },
        { symbol: 'TSLA', name: 'Tesla Inc.', exchange: selectedExchange || 'NASDAQ', price: '$248.56', change: '+$8.34', changeRate: '+3.47%', isUp: true },
        { symbol: 'NVDA', name: 'NVIDIA Corp.', exchange: selectedExchange || 'NASDAQ', price: '$421.78', change: '+$12.45', changeRate: '+3.04%', isUp: true },
        { symbol: 'AMZN', name: 'Amazon.com Inc.', exchange: selectedExchange || 'NASDAQ', price: '$142.67', change: '-$0.98', changeRate: '-0.68%', isUp: false }
      ]
      
      return overseasStocks.filter(stock => 
        stock.name.toLowerCase().includes(query.toLowerCase()) ||
        stock.symbol.toLowerCase().includes(query.toLowerCase())
      )
    }
  }

  // 검색 실행
  const performSearch = async (query: string) => {
    if (query.length < 2) {
      setResults([])
      setShowResults(false)
      return
    }

    setIsLoading(true)
    
    try {
      // 실제 구현에서는 여기에서 KIS API 호출
      // const response = await searchStocks(query, currentMarket, selectedExchange)
      
      // 현재는 모의 데이터 사용
      await new Promise(resolve => setTimeout(resolve, 300)) // 네트워크 지연 시뮬레이션
      const mockResults = getMockSearchResults(query)
      
      setResults(mockResults)
      setShowResults(true)
    } catch (error) {
      console.error('종목 검색 실패:', error)
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  // 검색어 변경 처리 (디바운싱)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      performSearch(searchTerm)
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchTerm, currentMarket, selectedExchange])

  // 종목 선택 처리
  const handleSelectStock = (stock: StockSearchResult) => {
    onSelectStock?.(stock)
    setSearchTerm('')
    setShowResults(false)
  }

  // 관심종목 추가 처리
  const handleAddToWatchlist = (stock: StockSearchResult, e: React.MouseEvent) => {
    e.stopPropagation()
    // 실제 구현에서는 여기에서 관심종목 추가 로직
    console.log('관심종목 추가:', stock)
  }

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={placeholder || getDefaultPlaceholder()}
          className="pl-10"
          onFocus={() => searchTerm.length >= 2 && setShowResults(true)}
          onBlur={() => {
            // 결과 선택을 위해 약간의 지연
            setTimeout(() => setShowResults(false), 200)
          }}
        />
        
        {currentMarket === 'domestic' ? (
          <Building2 className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        ) : (
          <Globe className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        )}
      </div>

      {/* 검색 결과 드롭다운 */}
      {showResults && (
        <Card className="absolute top-full left-0 right-0 mt-1 z-50 max-h-80 overflow-y-auto">
          <CardContent className="p-2">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                <span className="ml-2 text-sm text-muted-foreground">검색 중...</span>
              </div>
            ) : results.length > 0 ? (
              <div className="space-y-1">
                {results.map((stock, idx) => (
                  <div
                    key={`${stock.symbol}-${idx}`}
                    className="flex items-center justify-between p-2 hover:bg-muted rounded-md cursor-pointer transition-colors"
                    onClick={() => handleSelectStock(stock)}
                  >
                    <div className="flex items-center flex-1 min-w-0">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{stock.name}</span>
                          {stock.exchange && (
                            <span className="text-xs px-1 py-0.5 bg-muted rounded text-muted-foreground">
                              {stock.exchange}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                      </div>
                      
                      {stock.price && (
                        <div className="text-right mr-2">
                          <div className="font-semibold text-sm">{stock.price}</div>
                          {stock.change && stock.changeRate && (
                            <div className={`text-xs ${stock.isUp ? 'text-red-600' : 'text-blue-600'}`}>
                              {stock.change} ({stock.changeRate})
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-1 ml-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="p-1 h-auto"
                        onClick={(e) => handleAddToWatchlist(stock, e)}
                        title="관심종목에 추가"
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="p-1 h-auto"
                        onClick={(e) => handleAddToWatchlist(stock, e)}
                        title="즐겨찾기"
                      >
                        <Star className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : searchTerm.length >= 2 ? (
              <div className="text-center py-4 text-muted-foreground">
                <div className="text-sm">&lsquo;{searchTerm}&rsquo;에 대한 검색 결과가 없습니다</div>
                <div className="text-xs mt-1">
                  {currentMarket === 'domestic' 
                    ? '종목명 또는 종목코드를 정확히 입력해주세요' 
                    : '영문 종목명 또는 심볼을 입력해주세요'
                  }
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      )}
    </div>
  )
}