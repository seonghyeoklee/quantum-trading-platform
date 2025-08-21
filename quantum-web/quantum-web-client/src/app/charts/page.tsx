'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StockChart, PortfolioChart, TechnicalIndicatorChart } from '@/components/charts';

export default function ChartsPage() {
  return (
    <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'TRADER']}>
      <AdminLayout>
        <div className="space-y-6">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">차트 대시보드</h1>
        <p className="text-muted-foreground">
          실시간 주식 차트, 포트폴리오 분석, 기술적 지표를 확인하세요.
        </p>
      </div>

      <Tabs defaultValue="stock" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="stock">주식 차트</TabsTrigger>
          <TabsTrigger value="portfolio">포트폴리오</TabsTrigger>
          <TabsTrigger value="technical">기술적 지표</TabsTrigger>
        </TabsList>

        <TabsContent value="stock" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>실시간 주식 차트</CardTitle>
            </CardHeader>
            <CardContent>
              <StockChart
                symbol="005930"
                symbolName="삼성전자"
                height={400}
                showOrderBook={true}
                showTrades={true}
              />
            </CardContent>
          </Card>

          {/* 추가 주식 차트들 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">SK하이닉스</CardTitle>
              </CardHeader>
              <CardContent>
                <StockChart
                  symbol="000660"
                  symbolName="SK하이닉스"
                  height={300}
                  showOrderBook={false}
                  showTrades={false}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">NAVER</CardTitle>
              </CardHeader>
              <CardContent>
                <StockChart
                  symbol="035420"
                  symbolName="NAVER"
                  height={300}
                  showOrderBook={false}
                  showTrades={false}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="portfolio" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>포트폴리오 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <PortfolioChart
                portfolioId="PORTFOLIO-123"
                height={350}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="technical" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>기술적 지표 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <TechnicalIndicatorChart
                symbol="005930"
                symbolName="삼성전자"
                timeframe="1d"
              />
            </CardContent>
          </Card>

          {/* 다른 종목들의 기술적 지표 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">SK하이닉스 기술적 지표</CardTitle>
              </CardHeader>
              <CardContent>
                <TechnicalIndicatorChart
                  symbol="000660"
                  symbolName="SK하이닉스"
                  timeframe="1d"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">NAVER 기술적 지표</CardTitle>
              </CardHeader>
              <CardContent>
                <TechnicalIndicatorChart
                  symbol="035420"
                  symbolName="NAVER"
                  timeframe="1d"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* WebSocket 연결 상태 표시 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">시스템 상태</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">WebSocket</div>
              <div className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-semibold text-green-600">Connected</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">실시간 데이터</div>
              <div className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-semibold text-blue-600">Streaming</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">API 서버</div>
              <div className="flex items-center justify-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-semibold text-green-600">Online</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 사용 가이드 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">차트 사용 가이드</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div className="space-y-2">
              <div className="font-semibold">주식 차트</div>
              <ul className="space-y-1 text-muted-foreground">
                <li>• 실시간 시세 데이터</li>
                <li>• 캔들스틱/라인 차트</li>
                <li>• 호가창 정보</li>
                <li>• 최근 거래 내역</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <div className="font-semibold">포트폴리오 차트</div>
              <ul className="space-y-1 text-muted-foreground">
                <li>• 포트폴리오 가치 추이</li>
                <li>• 자산 배분 도넛 차트</li>
                <li>• 일별 손익 히스토리</li>
                <li>• 실시간 업데이트</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <div className="font-semibold">기술적 지표</div>
              <ul className="space-y-1 text-muted-foreground">
                <li>• 이동평균선 (MA, EMA)</li>
                <li>• MACD, RSI, Stochastic</li>
                <li>• 볼린저 밴드</li>
                <li>• 맞춤형 지표 설정</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}