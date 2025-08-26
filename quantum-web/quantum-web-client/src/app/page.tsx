'use client';

import { useState, useRef } from 'react';
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Header from "@/components/layout/Header";
import { Button } from "@/components/ui/button"
import ChartContainer, { ChartContainerRef } from "@/components/chart/ChartContainer"
import ProgramTradingRanking from "@/components/trading/ProgramTradingRanking"
import { KiwoomStockInfo } from "@/lib/api/kiwoom-types";

function TradingDashboard() {
  const [selectedStock, setSelectedStock] = useState<KiwoomStockInfo | null>(null);
  const chartContainerRef = useRef<ChartContainerRef>(null);

  // 차트 컨테이너에서 종목 선택 이벤트를 받기 위한 핸들러
  const handleStockSelection = (stockOrCode: KiwoomStockInfo | string, stockName?: string) => {
    if (typeof stockOrCode === 'string') {
      // ProgramTradingRanking에서 온 데이터 (stockCode, stockName)
      console.log('프로그램 매매 랭킹에서 종목 선택:', stockOrCode, stockName);
      
      // ChartContainer의 selectStock 함수를 호출하여 차트에서 해당 종목을 선택
      if (chartContainerRef.current) {
        chartContainerRef.current.selectStock(stockOrCode, stockName || stockOrCode);
      }
      
      const mockStock: KiwoomStockInfo = {
        stockCode: stockOrCode,
        stockName: stockName || stockOrCode,
        currentPrice: 0,
        changeAmount: 0,
        changeRate: 0,
        volume: 0,
        marketCap: '0',
        sector: '',
        description: '',
        peRatio: 0,
        pbRatio: 0,
        eps: 0,
        bps: 0,
        dividendYield: 0,
        roe: 0,
        debtRatio: 0,
        quickRatio: 0,
        currentRatio: 0,
        evEbitda: 0,
        priceToSales: 0,
        priceToBook: 0
      };
      setSelectedStock(mockStock);
    } else {
      // ChartContainer에서 온 데이터
      console.log('차트 컨테이너에서 종목 선택 감지:', stockOrCode);
      setSelectedStock(stockOrCode);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Main Content - TradingView Style */}
      <main className="flex flex-1 overflow-hidden min-h-0" style={{ height: 'calc(100vh - 64px)' }}>
        {/* Left Sidebar - Watchlist */}
        <div className="w-80 border-r border-border bg-sidebar flex flex-col">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">관심종목</h3>
              <Button 
                variant="outline" 
                size="sm" 
                className="text-xs h-6 px-2"
                onClick={() => window.location.href = '/stock'}
              >
                종목검색
              </Button>
            </div>
            <div className="text-center py-8 text-muted-foreground">
              <div className="text-sm mb-2">관심종목이 없습니다</div>
              <div className="text-xs">
                종목 검색에서 관심종목을 추가해보세요
              </div>
            </div>
          </div>
          
          {/* Portfolio Section */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">포트폴리오</h3>
            </div>
            <div className="text-center py-6 text-muted-foreground">
              <div className="text-sm mb-2">포트폴리오가 없습니다</div>
              <div className="text-xs">
                거래를 시작해보세요
              </div>
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="p-4">
            <h3 className="font-semibold text-sm mb-3">빠른 이동</h3>
            <div className="space-y-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full"
                onClick={() => window.location.href = '/stock'}
              >
                종목 분석
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="w-full"
                onClick={() => window.location.href = '/glossary'}
              >
                용어 사전
              </Button>
            </div>
          </div>
        </div>

        {/* Central Area - Chart Only */}
        <div className="flex-1 flex flex-col bg-background overflow-hidden">
          {/* 차트 영역 - 완전한 기능 */}
          <div className="flex-1 h-full">
            <ChartContainer 
              ref={chartContainerRef}
              className="h-full" 
              onStockSelect={handleStockSelection}
            />
          </div>
        </div>

        {/* Right Sidebar - Market Data */}
        <div className="w-96 border-l border-border bg-sidebar flex flex-col">
          {/* 실시간 프로그램 매매 랭킹 */}
          <div className="flex-1 flex flex-col">
            <ProgramTradingRanking 
              className="flex-1"
              onStockClick={handleStockSelection}
              maxItems={50}
              autoRefresh={true}
              refreshInterval={30000}
            />
          </div>
          
          <div className="p-4 border-t border-border">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">주요 지수</h3>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium">KOSPI</div>
                  <div className="text-xs text-muted-foreground">한국 종합주가지수</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">2,647.82</div>
                  <div className="text-xs text-red-600">+1.23%</div>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium">KOSDAQ</div>
                  <div className="text-xs text-muted-foreground">코스닥 지수</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">742.15</div>
                  <div className="text-xs text-blue-600">-0.84%</div>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-sm font-medium">USD/KRW</div>
                  <div className="text-xs text-muted-foreground">원달러 환율</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">1,347.50</div>
                  <div className="text-xs text-red-600">+0.32%</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}

export default function ProtectedTradingDashboard() {
  return (
    <ProtectedRoute>
      <TradingDashboard />
    </ProtectedRoute>
  );
}
