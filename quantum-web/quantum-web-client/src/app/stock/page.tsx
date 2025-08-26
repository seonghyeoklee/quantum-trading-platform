'use client';

import { useState } from 'react';
import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Header from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import StockSearch from "@/components/chart/StockSearch";
import StockBasicInfoComponent from "@/components/stock/StockBasicInfo";
import StockFinancialMetrics from "@/components/stock/StockFinancialMetrics";
import { useStockBasicInfo } from "@/hooks/useStockBasicInfo";
import { KiwoomStockInfo } from "@/lib/api/kiwoom-types";
import { 
  TrendingUp,
  Calculator
} from "lucide-react";

function StockInfoDashboard() {
  const [currentSymbol, setCurrentSymbol] = useState('');

  // 종목 정보 훅 사용
  const { data, loading, error, refresh } = useStockBasicInfo(currentSymbol, {
    autoRefresh: true,
    refreshInterval: 5 * 60 * 1000 // 5분 자동 갱신
  });

  // 종목 선택 핸들러
  const handleStockSelect = (stock: KiwoomStockInfo) => {
    console.log('선택된 종목:', stock);
    setCurrentSymbol(stock.code);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* 종목 검색 섹션 */}
        <div className="mb-8">
          <StockSearch
            onStockSelect={handleStockSelect}
            className="w-full"
          />
        </div>

        {/* 종목 정보 표시 영역 */}
        <div className="space-y-6">
          {/* 기본 정보 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5" />
                <span>종목 기본 정보</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <StockBasicInfoComponent 
                stockInfo={data}
                loading={loading}
                error={error}
                onRefresh={refresh}
              />
            </CardContent>
          </Card>

          {/* 재무 지표 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Calculator className="w-5 h-5" />
                <span>재무 지표</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <StockFinancialMetrics 
                stockInfo={data}
                loading={loading}
              />
            </CardContent>
          </Card>
        </div>

        {/* 도움말 */}
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">사용법 안내</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground space-y-2">
              <p>• <strong>종목 검색:</strong> 위의 검색창에 6자리 종목코드를 입력하세요 (예: 005930)</p>
              <p>• <strong>자동 갱신:</strong> 종목 정보는 5분마다 자동으로 갱신됩니다</p>
              <p>• <strong>수동 새로고침:</strong> 기본 정보 카드의 새로고침 버튼을 클릭하세요</p>
              <p>• <strong>인기 종목:</strong> 위의 버튼들로 주요 종목을 빠르게 조회할 수 있습니다</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function ProtectedStockInfoDashboard() {
  return (
    <ProtectedRoute>
      <StockInfoDashboard />
    </ProtectedRoute>
  );
}