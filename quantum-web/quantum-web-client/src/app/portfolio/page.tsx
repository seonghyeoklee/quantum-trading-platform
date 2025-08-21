'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  PieChart, 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Wallet,
  Activity,
  BarChart3,
  RefreshCw
} from 'lucide-react';

export default function PortfolioPage() {
  return (
    <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
      <AdminLayout>
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">포트폴리오 관리</h1>
              <p className="text-muted-foreground">
                포트폴리오 성과와 자산 배분을 관리하고 모니터링하세요.
              </p>
            </div>
            <div className="mt-4 sm:mt-0">
              <Button variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </Button>
            </div>
          </div>

          {/* 포트폴리오 개요 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">총 자산 가치</CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₩15,750,000</div>
                <p className="text-xs text-muted-foreground">
                  전일 대비
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">일일 손익</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">+₩125,000</div>
                <p className="text-xs text-green-600">+0.8%</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">보유 종목 수</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">12</div>
                <p className="text-xs text-muted-foreground">
                  활성 포지션
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">현금 잔고</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₩2,500,000</div>
                <p className="text-xs text-muted-foreground">
                  투자 가능 금액
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 자산 배분과 보유 종목 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 자산 배분 차트 */}
            <Card>
              <CardHeader>
                <CardTitle>자산 배분</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <PieChart className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <p className="text-sm text-gray-600">포트폴리오 차트 구현 예정</p>
                    <p className="text-xs text-gray-500">ApexCharts 도넛 차트</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 보유 종목 */}
            <Card>
              <CardHeader>
                <CardTitle>주요 보유 종목</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* 삼성전자 */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">삼성전자</span>
                        <Badge variant="secondary" className="text-xs">005930</Badge>
                      </div>
                      <div className="text-sm text-gray-600">100주 보유</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">₩7,200,000</div>
                      <div className="text-sm text-green-600">+1.2%</div>
                    </div>
                  </div>

                  {/* SK하이닉스 */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">SK하이닉스</span>
                        <Badge variant="secondary" className="text-xs">000660</Badge>
                      </div>
                      <div className="text-sm text-gray-600">50주 보유</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">₩4,500,000</div>
                      <div className="text-sm text-red-600">-0.8%</div>
                    </div>
                  </div>

                  {/* NAVER */}
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">NAVER</span>
                        <Badge variant="secondary" className="text-xs">035420</Badge>
                      </div>
                      <div className="text-sm text-gray-600">30주 보유</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">₩1,550,000</div>
                      <div className="text-sm text-green-600">+2.1%</div>
                    </div>
                  </div>

                  <Button variant="outline" className="w-full mt-4">
                    전체 보유 종목 보기
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 포트폴리오 성과 */}
          <Card>
            <CardHeader>
              <CardTitle>포트폴리오 성과 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-600">총 수익률</div>
                  <div className="text-2xl font-bold text-green-600">+8.5%</div>
                  <div className="text-xs text-gray-500">시작 대비</div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-600">연간 수익률</div>
                  <div className="text-2xl font-bold text-green-600">+12.3%</div>
                  <div className="text-xs text-gray-500">연환산 기준</div>
                </div>

                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-600">최대 낙폭</div>
                  <div className="text-2xl font-bold text-red-600">-3.2%</div>
                  <div className="text-xs text-gray-500">최고점 대비</div>
                </div>
              </div>

              <div className="mt-6 h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p className="text-sm text-gray-600">포트폴리오 성과 차트 구현 예정</p>
                  <p className="text-xs text-gray-500">ApexCharts 라인 차트</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 리밸런싱 제안 */}
          <Card>
            <CardHeader>
              <CardTitle>리밸런싱 제안</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-start gap-3">
                    <Activity className="h-5 w-5 text-blue-600 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-medium text-blue-900">포트폴리오 리밸런싱 권장</div>
                      <div className="text-sm text-blue-700 mt-1">
                        현재 삼성전자 비중이 45.7%로 과도합니다. 
                        리스크 분산을 위해 일부 매도를 고려해보세요.
                      </div>
                      <div className="mt-3">
                        <Button size="sm" variant="outline">
                          리밸런싱 계획 보기
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-start gap-3">
                    <TrendingUp className="h-5 w-5 text-green-600 mt-0.5" />
                    <div className="flex-1">
                      <div className="font-medium text-green-900">투자 기회 알림</div>
                      <div className="text-sm text-green-700 mt-1">
                        현재 현금 비중이 15.9%입니다. 
                        시장 상황이 좋다면 추가 투자를 고려해보세요.
                      </div>
                      <div className="mt-3">
                        <Button size="sm" variant="outline">
                          투자 추천 보기
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}