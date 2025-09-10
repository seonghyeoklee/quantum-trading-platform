'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import StockSelector, { DomesticStock } from '@/components/stock/StockSelector';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight, BarChart3, TrendingUp, Building2, Zap } from 'lucide-react';

export default function StocksPage() {
  const router = useRouter();
  const [selectedStock, setSelectedStock] = useState<DomesticStock | null>(null);

  const handleStockSelect = (stock: DomesticStock) => {
    setSelectedStock(stock);
  };

  const handleViewChart = () => {
    if (selectedStock) {
      router.push(`/stocks/${selectedStock.stockCode}`);
    }
  };


  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">국내 주식 종목</h1>
          <p className="text-muted-foreground mt-1">
            KOSPI/KOSDAQ 상장 종목을 검색하고 차트를 확인하세요
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 종목 선택기 */}
        <div className="lg:col-span-2">
          <StockSelector
            onStockSelect={handleStockSelect}
            showSearch={true}
            showFilter={true}
            pageSize={25}
            title="종목 목록"
            placeholder="종목명 또는 종목코드를 입력하세요 (예: 삼성전자, 005930)"
          />
        </div>

        {/* 사이드 패널 */}
        <div className="space-y-4">
          {/* 선택된 종목 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <BarChart3 className="w-5 h-5 text-primary" />
                선택된 종목
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedStock ? (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-lg">{selectedStock.stockName}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-sm text-muted-foreground">
                        {selectedStock.stockCode}
                      </span>
                      <Badge 
                        variant="secondary"
                        className={
                          selectedStock.marketType === 'KOSPI' 
                            ? 'text-red-600' 
                            : 'text-blue-600'
                        }
                      >
                        {selectedStock.marketType}
                      </Badge>
                    </div>
                    {selectedStock.sectorCode && (
                      <p className="text-sm text-muted-foreground mt-1">
                        업종: {selectedStock.sectorCode}
                      </p>
                    )}
                    {selectedStock.listingDate && (
                      <p className="text-sm text-muted-foreground">
                        상장일: {new Date(selectedStock.listingDate).toLocaleDateString('ko-KR')}
                      </p>
                    )}
                  </div>
                  
                  <Button 
                    onClick={handleViewChart} 
                    className="w-full"
                    size="lg"
                  >
                    <BarChart3 className="w-4 h-4 mr-2" />
                    차트 보기
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="w-12 h-12 mx-auto text-muted-foreground/50 mb-3" />
                  <p className="text-muted-foreground">
                    종목을 선택하면<br />상세 정보가 표시됩니다
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 빠른 액세스 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="w-5 h-5 text-primary" />
                빠른 액세스
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button 
                variant="outline" 
                className="w-full justify-start"
                onClick={() => router.push('/dashboard')}
              >
                <Building2 className="w-4 h-4 mr-2" />
                대시보드로 이동
              </Button>
            </CardContent>
          </Card>

          {/* 시장 현황 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">시장 현황</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <span className="text-sm font-medium">KOSPI</span>
                  </div>
                  <Badge variant="secondary" className="text-red-600">
                    대형주 위주
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                    <span className="text-sm font-medium">KOSDAQ</span>
                  </div>
                  <Badge variant="secondary" className="text-blue-600">
                    성장주 위주
                  </Badge>
                </div>
                
                <div className="mt-4 pt-3 border-t text-center">
                  <p className="text-xs text-muted-foreground">
                    실시간 데이터는 차트에서 확인하세요
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}