'use client';

import React, { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  Users, 
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw
} from 'lucide-react';

interface DashboardStats {
  totalPortfolioValue: number;
  dailyPnL: number;
  dailyPnLPercent: number;
  activeOrders: number;
  totalPositions: number;
  connectedUsers: number;
  systemStatus: 'healthy' | 'warning' | 'error';
}

export default function DashboardPage() {
  const { user, hasRole } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalPortfolioValue: 15750000,
    dailyPnL: 125000,
    dailyPnLPercent: 0.8,
    activeOrders: 8,
    totalPositions: 12,
    connectedUsers: 3,
    systemStatus: 'healthy'
  });
  const [isLoading, setIsLoading] = useState(false);

  const refreshDashboard = async () => {
    setIsLoading(true);
    try {
      // 실제로는 API에서 데이터를 가져옴
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock data update
      setStats(prev => ({
        ...prev,
        dailyPnL: prev.dailyPnL + (Math.random() - 0.5) * 10000,
        activeOrders: Math.floor(Math.random() * 20) + 5,
        connectedUsers: Math.floor(Math.random() * 10) + 1,
      }));
    } catch (error) {
      console.error('Failed to refresh dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // 페이지 로드 시 데이터 초기 로드
    // refreshDashboard();
    
    // 30초마다 자동 갱신
    const interval = setInterval(() => {
      refreshDashboard();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (amount: number) => `₩${amount.toLocaleString()}`;
  const formatPercent = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;

  return (
    <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'TRADER']}>
      <AdminLayout>
        <div className="space-y-6">
          {/* 헤더 섹션 */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                대시보드
              </h1>
              <p className="text-gray-600 mt-1">
                안녕하세요, {user?.name || user?.username}님! 
                현재 시스템 상태를 확인하세요.
              </p>
            </div>
            <div className="flex items-center space-x-3 mt-4 sm:mt-0">
              <Badge 
                variant={stats.systemStatus === 'healthy' ? 'default' : 'destructive'}
                className="flex items-center gap-1"
              >
                {stats.systemStatus === 'healthy' ? (
                  <CheckCircle className="h-3 w-3" />
                ) : (
                  <AlertTriangle className="h-3 w-3" />
                )}
                {stats.systemStatus === 'healthy' ? '시스템 정상' : '시스템 점검'}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={refreshDashboard}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                새로고침
              </Button>
            </div>
          </div>

          {/* 메인 통계 카드들 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  총 포트폴리오 가치
                </CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatCurrency(stats.totalPortfolioValue)}
                </div>
                <p className="text-xs text-muted-foreground">
                  전일 대비
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  일일 손익
                </CardTitle>
                {stats.dailyPnL >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${
                  stats.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(stats.dailyPnL)}
                </div>
                <p className={`text-xs ${
                  stats.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatPercent(stats.dailyPnLPercent)}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  활성 주문
                </CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.activeOrders}</div>
                <p className="text-xs text-muted-foreground">
                  {stats.totalPositions}개 포지션 보유
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  접속 사용자
                </CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.connectedUsers}</div>
                <p className="text-xs text-muted-foreground">
                  현재 활성 세션
                </p>
              </CardContent>
            </Card>
          </div>

          {/* 주요 기능 바로가기 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
                  실시간 차트 분석
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  실시간 주식 차트와 기술적 지표를 확인하세요.
                </p>
                <Button 
                  className="w-full" 
                  onClick={() => window.location.href = '/charts'}
                >
                  차트 보기
                </Button>
              </CardContent>
            </Card>

            {(hasRole('ADMIN') || hasRole('MANAGER')) && (
              <Card className="hover:shadow-md transition-shadow cursor-pointer">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center">
                    <Activity className="h-5 w-5 mr-2 text-green-600" />
                    포트폴리오 관리
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">
                    포트폴리오 성과와 자산 배분을 관리하세요.
                  </p>
                  <Button 
                    className="w-full" 
                    onClick={() => window.location.href = '/portfolio'}
                  >
                    포트폴리오 보기
                  </Button>
                </CardContent>
              </Card>
            )}

            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <BarChart3 className="h-5 w-5 mr-2 text-purple-600" />
                  거래 관리
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  주문 생성, 취소 및 거래 내역을 확인하세요.
                </p>
                <Button 
                  className="w-full" 
                  onClick={() => window.location.href = '/trading'}
                >
                  거래 보기
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* 시스템 상태 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Activity className="h-5 w-5 mr-2" />
                시스템 상태
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <div>
                    <p className="font-medium">WebSocket 연결</p>
                    <p className="text-sm text-gray-600">실시간 데이터 스트리밍</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <div>
                    <p className="font-medium">API 서버</p>
                    <p className="text-sm text-gray-600">모든 서비스 정상</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                  <div>
                    <p className="font-medium">데이터베이스</p>
                    <p className="text-sm text-gray-600">응답시간 < 50ms</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 최근 활동 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Clock className="h-5 w-5 mr-2" />
                최근 활동
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm">삼성전자 100주 매수 주문 체결</span>
                  </div>
                  <span className="text-xs text-gray-500">2분 전</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b">
                  <div className="flex items-center space-x-3">
                    <Activity className="h-4 w-4 text-blue-600" />
                    <span className="text-sm">포트폴리오 리밸런싱 완료</span>
                  </div>
                  <span className="text-xs text-gray-500">15분 전</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <div className="flex items-center space-x-3">
                    <TrendingUp className="h-4 w-4 text-purple-600" />
                    <span className="text-sm">새로운 기술적 지표 알림 설정</span>
                  </div>
                  <span className="text-xs text-gray-500">1시간 전</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}