'use client';

import { useParams, useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import ChartContainer from '@/components/chart/ChartContainer';
import { ArrowLeft, BarChart3, Building2, Calendar, Info, TrendingUp } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface StockDetail {
  stockCode: string;
  stockName: string;
  marketType: 'KOSPI' | 'KOSDAQ';
  isinCode?: string;
  sectorCode?: string;
  listingDate?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  summary: string;
}

export default function StockDetailPage() {
  const params = useParams();
  const router = useRouter();
  const stockCode = params.stockCode as string;
  
  const [stockDetail, setStockDetail] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 종목 상세 정보 조회
  const fetchStockDetail = async (code: string) => {
    setLoading(true);
    setError(null);

    try {
      const endpoint = `/api/v1/stocks/domestic/${code}`;
      const response = await apiClient.get<StockDetail>(endpoint, false);
      
      if (response.data) {
        setStockDetail(response.data);
      } else {
        throw new Error('종목 데이터를 받을 수 없습니다.');
      }
      
    } catch (err) {
      console.error('종목 상세 조회 실패:', err);
      if (err instanceof Error && err.message.includes('404')) {
        setError('종목을 찾을 수 없습니다.');
      } else {
        setError(err instanceof Error ? err.message : '종목 상세 조회에 실패했습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (stockCode && typeof stockCode === 'string') {
      // 종목코드 형식 검증
      if (!/^[A-Z0-9]{6}$/.test(stockCode)) {
        setError('유효하지 않은 종목코드 형식입니다.');
        setLoading(false);
        return;
      }
      
      fetchStockDetail(stockCode);
    }
  }, [stockCode]);

  // 뒤로가기
  const handleGoBack = () => {
    router.push('/stocks');
  };

  // 다른 종목 보기
  const handleSelectAnotherStock = () => {
    router.push('/stocks');
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" onClick={handleGoBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            뒤로가기
          </Button>
        </div>
        
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground">종목 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" onClick={handleGoBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            뒤로가기
          </Button>
        </div>
        
        <div className="text-center py-12">
          <Building2 className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
          <h2 className="text-2xl font-semibold mb-2">종목 정보를 찾을 수 없습니다</h2>
          <p className="text-muted-foreground mb-6">{error}</p>
          <div className="space-x-3">
            <Button onClick={handleGoBack}>
              종목 목록으로 돌아가기
            </Button>
            <Button variant="outline" onClick={() => fetchStockDetail(stockCode)}>
              다시 시도
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!stockDetail) {
    return null;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={handleGoBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            뒤로가기
          </Button>
          
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-bold">{stockDetail.stockName}</h1>
              <Badge 
                variant="secondary"
                className={
                  stockDetail.marketType === 'KOSPI' 
                    ? 'text-red-600' 
                    : 'text-blue-600'
                }
              >
                {stockDetail.marketType}
              </Badge>
            </div>
            <p className="text-muted-foreground">{stockDetail.stockCode}</p>
          </div>
        </div>
        
        <Button variant="outline" onClick={handleSelectAnotherStock}>
          <TrendingUp className="w-4 h-4 mr-2" />
          다른 종목 보기
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 차트 영역 */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-primary" />
                {stockDetail.stockName} 차트
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer 
                stockCode={stockCode}
                stockName={stockDetail.stockName}
              />
            </CardContent>
          </Card>
        </div>

        {/* 종목 정보 사이드패널 */}
        <div className="space-y-4">
          {/* 기본 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Info className="w-5 h-5 text-primary" />
                기본 정보
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-sm font-medium text-muted-foreground">종목코드</label>
                <p className="font-mono text-sm mt-1">{stockDetail.stockCode}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">종목명</label>
                <p className="mt-1">{stockDetail.stockName}</p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">시장구분</label>
                <div className="mt-1">
                  <Badge 
                    variant="secondary"
                    className={
                      stockDetail.marketType === 'KOSPI' 
                        ? 'text-red-600' 
                        : 'text-blue-600'
                    }
                  >
                    {stockDetail.marketType}
                  </Badge>
                </div>
              </div>

              {stockDetail.sectorCode && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">업종코드</label>
                  <p className="mt-1 text-sm">{stockDetail.sectorCode}</p>
                </div>
              )}

              {stockDetail.isinCode && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">ISIN 코드</label>
                  <p className="font-mono text-sm mt-1">{stockDetail.isinCode}</p>
                </div>
              )}

              {stockDetail.listingDate && (
                <div>
                  <label className="text-sm font-medium text-muted-foreground">상장일</label>
                  <div className="flex items-center gap-2 mt-1">
                    <Calendar className="w-4 h-4 text-muted-foreground" />
                    <p className="text-sm">
                      {new Date(stockDetail.listingDate).toLocaleDateString('ko-KR')}
                    </p>
                  </div>
                </div>
              )}

              <div>
                <label className="text-sm font-medium text-muted-foreground">상태</label>
                <div className="mt-1">
                  <Badge variant={stockDetail.isActive ? "default" : "secondary"}>
                    {stockDetail.isActive ? "활성" : "비활성"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 요약 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">요약</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {stockDetail.summary}
              </p>
            </CardContent>
          </Card>

          {/* 마지막 업데이트 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">업데이트 정보</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <label className="text-sm font-medium text-muted-foreground">생성일</label>
                <p className="text-sm mt-1">
                  {new Date(stockDetail.createdAt).toLocaleString('ko-KR')}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">수정일</label>
                <p className="text-sm mt-1">
                  {new Date(stockDetail.updatedAt).toLocaleString('ko-KR')}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}