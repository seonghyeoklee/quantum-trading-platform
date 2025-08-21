'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertTriangle,
  Shield,
  TrendingDown,
  Activity,
  BarChart3,
  RefreshCw,
  Settings,
  CheckCircle,
  XCircle,
  AlertCircle,
  Target,
  Zap,
  Eye
} from 'lucide-react';

interface RiskMetric {
  id: string;
  name: string;
  value: number;
  threshold: number;
  status: 'safe' | 'warning' | 'danger';
  description: string;
}

interface RiskAlert {
  id: string;
  type: 'POSITION_SIZE' | 'CONCENTRATION' | 'VOLATILITY' | 'CORRELATION' | 'DRAWDOWN';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  title: string;
  description: string;
  timestamp: string;
  isRead: boolean;
}

const mockRiskMetrics: RiskMetric[] = [
  {
    id: 'var',
    name: 'VaR (99%)',
    value: 2.3,
    threshold: 5.0,
    status: 'safe',
    description: '99% 신뢰수준에서 하루 최대 예상 손실'
  },
  {
    id: 'concentration',
    name: '집중도 위험',
    value: 45.7,
    threshold: 40.0,
    status: 'warning',
    description: '단일 종목 최대 비중'
  },
  {
    id: 'leverage',
    name: '레버리지',
    value: 1.2,
    threshold: 2.0,
    status: 'safe',
    description: '총 투자금액 대비 자산 비율'
  },
  {
    id: 'correlation',
    name: '포트폴리오 상관관계',
    value: 0.68,
    threshold: 0.8,
    status: 'warning',
    description: '종목 간 평균 상관관계'
  },
  {
    id: 'volatility',
    name: '포트폴리오 변동성',
    value: 18.5,
    threshold: 25.0,
    status: 'safe',
    description: '연환산 포트폴리오 변동성'
  },
  {
    id: 'drawdown',
    name: '최대 낙폭',
    value: 3.2,
    threshold: 10.0,
    status: 'safe',
    description: '최고점 대비 최대 하락폭'
  }
];

const mockAlerts: RiskAlert[] = [
  {
    id: 'ALERT-001',
    type: 'CONCENTRATION',
    severity: 'MEDIUM',
    title: '집중도 위험 임계치 근접',
    description: '삼성전자 비중이 45.7%로 위험 임계치(40%)를 초과했습니다.',
    timestamp: '2024-01-15T10:30:00Z',
    isRead: false
  },
  {
    id: 'ALERT-002',
    type: 'CORRELATION',
    severity: 'LOW',
    title: '종목 간 상관관계 증가',
    description: '기술주 종목들 간의 상관관계가 0.68로 증가했습니다.',
    timestamp: '2024-01-15T09:15:00Z',
    isRead: false
  },
  {
    id: 'ALERT-003',
    type: 'VOLATILITY',
    severity: 'LOW',
    title: '변동성 증가 감지',
    description: 'SK하이닉스의 변동성이 전일 대비 15% 증가했습니다.',
    timestamp: '2024-01-15T08:45:00Z',
    isRead: true
  }
];

export default function RiskPage() {
  const [alerts, setAlerts] = useState<RiskAlert[]>(mockAlerts);
  const [selectedTab, setSelectedTab] = useState('metrics');

  const getStatusColor = (status: RiskMetric['status']) => {
    switch (status) {
      case 'safe':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'danger':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityColor = (severity: RiskAlert['severity']) => {
    switch (severity) {
      case 'LOW':
        return 'bg-blue-100 text-blue-800';
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800';
      case 'HIGH':
        return 'bg-orange-100 text-orange-800';
      case 'CRITICAL':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: RiskAlert['severity']) => {
    switch (severity) {
      case 'LOW':
        return <AlertCircle className="h-4 w-4" />;
      case 'MEDIUM':
        return <AlertTriangle className="h-4 w-4" />;
      case 'HIGH':
        return <XCircle className="h-4 w-4" />;
      case 'CRITICAL':
        return <Zap className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const markAsRead = (alertId: string) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId ? { ...alert, isRead: true } : alert
      )
    );
  };

  const unreadCount = alerts.filter(alert => !alert.isRead).length;
  const criticalCount = alerts.filter(alert => alert.severity === 'CRITICAL').length;
  const highCount = alerts.filter(alert => alert.severity === 'HIGH').length;

  return (
    <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
      <AdminLayout>
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">리스크 관리</h1>
              <p className="text-muted-foreground">
                포트폴리오의 위험 요소를 모니터링하고 관리하세요.
              </p>
            </div>
            <div className="flex gap-2 mt-4 sm:mt-0">
              <Button variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </Button>
              <Button variant="outline">
                <Settings className="h-4 w-4 mr-2" />
                설정
              </Button>
            </div>
          </div>

          {/* 리스크 개요 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">전체 리스크 등급</CardTitle>
                <Shield className="h-4 w-4 text-yellow-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-yellow-600">중간</div>
                <p className="text-xs text-muted-foreground">포트폴리오 전체</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">활성 알림</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{unreadCount}</div>
                <p className="text-xs text-muted-foreground">미확인 위험 알림</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">VaR (99%)</CardTitle>
                <TrendingDown className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">2.3%</div>
                <p className="text-xs text-muted-foreground">일일 최대 예상 손실</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">모니터링 지표</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockRiskMetrics.length}</div>
                <p className="text-xs text-muted-foreground">실시간 추적 중</p>
              </CardContent>
            </Card>
          </div>

          {/* 중요 알림 */}
          {unreadCount > 0 && (
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertDescription>
                <div className="flex items-center justify-between">
                  <span>
                    {unreadCount}개의 새로운 위험 알림이 있습니다. 즉시 확인하세요.
                  </span>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => setSelectedTab('alerts')}
                  >
                    알림 확인
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          <Tabs value={selectedTab} onValueChange={setSelectedTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="metrics">리스크 지표</TabsTrigger>
              <TabsTrigger value="alerts">
                위험 알림 {unreadCount > 0 && (
                  <Badge variant="destructive" className="ml-2 text-xs">
                    {unreadCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="limits">한도 관리</TabsTrigger>
            </TabsList>

            <TabsContent value="metrics" className="space-y-6">
              {/* 리스크 지표 */}
              <Card>
                <CardHeader>
                  <CardTitle>포트폴리오 리스크 지표</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {mockRiskMetrics.map((metric) => (
                      <div
                        key={metric.id}
                        className="p-4 border rounded-lg space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{metric.name}</span>
                          <Badge className={getStatusColor(metric.status)}>
                            {metric.status.toUpperCase()}
                          </Badge>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-2xl font-bold">
                              {metric.value}%
                            </span>
                            <span className="text-sm text-gray-500">
                              한도: {metric.threshold}%
                            </span>
                          </div>
                          
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                metric.status === 'safe' ? 'bg-green-500' :
                                metric.status === 'warning' ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`}
                              style={{
                                width: `${Math.min((metric.value / metric.threshold) * 100, 100)}%`
                              }}
                            />
                          </div>
                        </div>
                        
                        <div className="text-xs text-gray-600">
                          {metric.description}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 위험 분포 */}
              <Card>
                <CardHeader>
                  <CardTitle>위험 분포 분석</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                    <div className="text-center">
                      <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                      <p className="text-sm text-gray-600">위험 분포 차트 구현 예정</p>
                      <p className="text-xs text-gray-500">업종별, 종목별 위험 기여도</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="alerts" className="space-y-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>위험 알림</CardTitle>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        모두 읽음 처리
                      </Button>
                      <Button variant="outline" size="sm">
                        <Settings className="h-4 w-4 mr-2" />
                        알림 설정
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {alerts.map((alert) => (
                      <div
                        key={alert.id}
                        className={`p-4 rounded-lg border ${
                          !alert.isRead ? 'bg-blue-50 border-blue-200' : 'bg-gray-50'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-full ${getSeverityColor(alert.severity)}`}>
                            {getSeverityIcon(alert.severity)}
                          </div>
                          
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{alert.title}</span>
                              <Badge className={getSeverityColor(alert.severity)}>
                                {alert.severity}
                              </Badge>
                              {!alert.isRead && (
                                <Badge variant="outline" className="text-xs">
                                  새 알림
                                </Badge>
                              )}
                            </div>
                            
                            <p className="text-sm text-gray-600">
                              {alert.description}
                            </p>
                            
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-xs text-gray-500">
                                {new Date(alert.timestamp).toLocaleString('ko-KR')}
                              </span>
                              
                              <div className="flex gap-2">
                                {!alert.isRead && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => markAsRead(alert.id)}
                                  >
                                    <Eye className="h-4 w-4 mr-1" />
                                    확인
                                  </Button>
                                )}
                                <Button size="sm" variant="outline">
                                  상세보기
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {alerts.length === 0 && (
                      <div className="text-center py-12">
                        <CheckCircle className="h-12 w-12 mx-auto mb-4 text-green-500" />
                        <p className="text-gray-600">현재 활성화된 위험 알림이 없습니다.</p>
                        <p className="text-sm text-gray-500">모든 리스크 지표가 안전 범위 내에 있습니다.</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="limits" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>리스크 한도 설정</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <h4 className="font-medium">포지션 한도</h4>
                        
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">단일 종목 최대 비중</span>
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                className="w-16 p-1 text-sm border rounded text-right"
                                defaultValue={40}
                              />
                              <span className="text-sm text-gray-500">%</span>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-sm">업종별 최대 비중</span>
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                className="w-16 p-1 text-sm border rounded text-right"
                                defaultValue={60}
                              />
                              <span className="text-sm text-gray-500">%</span>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-sm">최대 레버리지</span>
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                step="0.1"
                                className="w-16 p-1 text-sm border rounded text-right"
                                defaultValue={2.0}
                              />
                              <span className="text-sm text-gray-500">배</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h4 className="font-medium">손실 한도</h4>
                        
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">일일 최대 손실 (VaR)</span>
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                className="w-16 p-1 text-sm border rounded text-right"
                                defaultValue={5}
                              />
                              <span className="text-sm text-gray-500">%</span>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-sm">최대 낙폭 한도</span>
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                className="w-16 p-1 text-sm border rounded text-right"
                                defaultValue={10}
                              />
                              <span className="text-sm text-gray-500">%</span>
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-sm">포트폴리오 변동성 한도</span>
                            <div className="flex items-center gap-2">
                              <input
                                type="number"
                                className="w-16 p-1 text-sm border rounded text-right"
                                defaultValue={25}
                              />
                              <span className="text-sm text-gray-500">%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="pt-4 border-t">
                      <div className="flex gap-2">
                        <Button>
                          <Target className="h-4 w-4 mr-2" />
                          설정 저장
                        </Button>
                        <Button variant="outline">
                          기본값으로 복원
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>자동 위험 관리</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">자동 손절매</div>
                        <div className="text-sm text-gray-600">
                          설정된 손실 한도 도달 시 자동으로 포지션 청산
                        </div>
                      </div>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">리밸런싱 알림</div>
                        <div className="text-sm text-gray-600">
                          포트폴리오 비중 이탈 시 리밸런싱 제안
                        </div>
                      </div>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <div className="font-medium">실시간 모니터링</div>
                        <div className="text-sm text-gray-600">
                          리스크 지표 실시간 추적 및 알림
                        </div>
                      </div>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}