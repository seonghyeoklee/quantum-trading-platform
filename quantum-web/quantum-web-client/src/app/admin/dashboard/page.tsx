'use client';

import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/layout/AdminLayout';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Users,
  Shield,
  Activity,
  Globe,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  Calendar,
  BarChart3
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface LoginStats {
  successCount: number;
  failureCount: number;
  totalAttempts: number;
  uniqueIps: number;
  successRate: number;
}

interface RecentLogin {
  id: string;
  username: string;
  success: boolean;
  attemptTime: string;
  ipAddress: string;
  failureReason?: string;
}

function AdminDashboard() {
  const { hasRole } = useAuth();
  const router = useRouter();
  
  const [stats, setStats] = useState<LoginStats | null>(null);
  const [recentLogins, setRecentLogins] = useState<RecentLogin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError('');

      // 로그인 통계 가져오기
      const statsResponse = await apiClient.admin.getLoginStats();
      setStats(statsResponse.data);

      // 최근 로그인 이력 가져오기 (최근 10건)
      const historyResponse = await apiClient.admin.getLoginHistory({ 
        page: 0, 
        size: 10 
      });
      
      if (historyResponse.data && historyResponse.data.content) {
        setRecentLogins(historyResponse.data.content);
      }

    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err);
      setError('대시보드 데이터를 불러오는데 실패했습니다.');
      
      // 임시 더미 데이터
      setStats({
        successCount: 45,
        failureCount: 8,
        totalAttempts: 53,
        uniqueIps: 12,
        successRate: 84.91
      });

      setRecentLogins([
        {
          id: '1',
          username: 'admin',
          success: true,
          attemptTime: new Date().toISOString(),
          ipAddress: '192.168.1.100'
        },
        {
          id: '2',
          username: 'trader1',
          success: true,
          attemptTime: new Date(Date.now() - 300000).toISOString(),
          ipAddress: '192.168.1.101'
        },
        {
          id: '3',
          username: 'unknown_user',
          success: false,
          attemptTime: new Date(Date.now() - 600000).toISOString(),
          ipAddress: '203.0.113.1',
          failureReason: '잘못된 사용자명'
        },
        {
          id: '4',
          username: 'manager1',
          success: true,
          attemptTime: new Date(Date.now() - 900000).toISOString(),
          ipAddress: '192.168.1.102'
        },
        {
          id: '5',
          username: 'locked_user',
          success: false,
          attemptTime: new Date(Date.now() - 1200000).toISOString(),
          ipAddress: '203.0.113.5',
          failureReason: '계정 잠금'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'HH:mm:ss', { locale: ko });
    } catch {
      return dateString;
    }
  };

  const formatFullDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'PPP p', { locale: ko });
    } catch {
      return dateString;
    }
  };

  const getStatusIcon = (success: boolean) => {
    return success ? (
      <CheckCircle className="w-4 h-4 text-bull" />
    ) : (
      <XCircle className="w-4 h-4 text-destructive" />
    );
  };

  const getStatusBadge = (success: boolean) => {
    return success ? (
      <Badge variant="default" className="bg-bull text-white text-xs">성공</Badge>
    ) : (
      <Badge variant="destructive" className="text-xs">실패</Badge>
    );
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 90) return 'text-bull';
    if (rate >= 70) return 'text-warning-amber';
    return 'text-destructive';
  };

  const getTrendIcon = (rate: number) => {
    return rate >= 80 ? (
      <TrendingUp className="w-4 h-4 text-bull" />
    ) : (
      <TrendingDown className="w-4 h-4 text-destructive" />
    );
  };

  if (!hasRole('ADMIN')) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-destructive">접근 권한이 없습니다</CardTitle>
            <CardDescription>
              관리자 권한이 필요한 페이지입니다.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push('/')} className="w-full">
              홈으로 돌아가기
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const headerActions = (
    <Button 
      variant="outline" 
      size="sm" 
      onClick={fetchDashboardData}
      disabled={loading}
    >
      <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
      새로고침
    </Button>
  );

  return (
    <AdminLayout 
      title="관리자 대시보드"
      subtitle="시스템 현황 및 보안 모니터링"
      actions={headerActions}
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-8">
          
          {/* 오늘의 로그인 통계 */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold">오늘의 로그인 통계</h2>
                <p className="text-muted-foreground">
                  {format(new Date(), 'PPP', { locale: ko })} 기준
                </p>
              </div>
              {error && (
                <div className="text-sm text-muted-foreground">
                  <AlertTriangle className="w-4 h-4 inline mr-1" />
                  임시 데이터 표시 중
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* 총 로그인 시도 */}
              <Card className="trading-card">
                <CardContent className="trading-card-content">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">총 로그인 시도</p>
                      <p className="text-3xl font-bold">{stats?.totalAttempts || 0}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        성공 {stats?.successCount || 0} + 실패 {stats?.failureCount || 0}
                      </p>
                    </div>
                    <Activity className="w-10 h-10 text-primary" />
                  </div>
                </CardContent>
              </Card>

              {/* 성공률 */}
              <Card className="trading-card">
                <CardContent className="trading-card-content">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">성공률</p>
                      <div className="flex items-center space-x-2">
                        <p className={`text-3xl font-bold ${getSuccessRateColor(stats?.successRate || 0)}`}>
                          {stats?.successRate?.toFixed(1) || 0}%
                        </p>
                        {getTrendIcon(stats?.successRate || 0)}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {stats?.successRate && stats.successRate >= 90 ? '매우 양호' : 
                         stats?.successRate && stats.successRate >= 70 ? '양호' : '주의 필요'}
                      </p>
                    </div>
                    <CheckCircle className={`w-10 h-10 ${getSuccessRateColor(stats?.successRate || 0)}`} />
                  </div>
                </CardContent>
              </Card>

              {/* 실패한 로그인 */}
              <Card className="trading-card">
                <CardContent className="trading-card-content">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">실패한 로그인</p>
                      <p className="text-3xl font-bold text-destructive">
                        {stats?.failureCount || 0}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {stats?.failureCount && stats.failureCount > 10 ? '주의 필요' :
                         stats?.failureCount && stats.failureCount > 5 ? '모니터링 중' : '정상'}
                      </p>
                    </div>
                    <XCircle className="w-10 h-10 text-destructive" />
                  </div>
                </CardContent>
              </Card>

              {/* 고유 IP */}
              <Card className="trading-card">
                <CardContent className="trading-card-content">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">고유 IP 주소</p>
                      <p className="text-3xl font-bold text-chart-6">
                        {stats?.uniqueIps || 0}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        다양한 위치에서 접속
                      </p>
                    </div>
                    <Globe className="w-10 h-10 text-chart-6" />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* 최근 로그인 활동 */}
            <Card className="trading-card">
              <CardHeader className="trading-card-header">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center">
                      <Clock className="w-5 h-5 mr-2" />
                      최근 로그인 활동
                    </CardTitle>
                    <CardDescription>
                      최근 10건의 로그인 시도 내역
                    </CardDescription>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => router.push('/admin/security/login-history')}
                  >
                    <Eye className="w-4 h-4 mr-1" />
                    전체보기
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="trading-card-content p-0">
                {loading ? (
                  <div className="p-6 text-center">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                    <p className="text-muted-foreground">로딩 중...</p>
                  </div>
                ) : recentLogins.length === 0 ? (
                  <div className="p-6 text-center">
                    <Clock className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">최근 로그인 활동이 없습니다</p>
                  </div>
                ) : (
                  <div className="max-h-96 overflow-y-auto">
                    {recentLogins.map((login) => (
                      <div 
                        key={login.id}
                        className="flex items-center justify-between p-4 border-b border-border last:border-b-0 hover:bg-muted/20 transition-colors"
                      >
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(login.success)}
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="font-medium">{login.username}</span>
                              {getStatusBadge(login.success)}
                            </div>
                            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                              <span>{login.ipAddress}</span>
                              {!login.success && login.failureReason && (
                                <>
                                  <span>•</span>
                                  <span className="text-destructive">{login.failureReason}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm">{formatDate(login.attemptTime)}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatFullDate(login.attemptTime)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 빠른 작업 */}
            <Card className="trading-card">
              <CardHeader className="trading-card-header">
                <CardTitle className="flex items-center">
                  <Shield className="w-5 h-5 mr-2" />
                  빠른 작업
                </CardTitle>
                <CardDescription>
                  자주 사용하는 관리 기능들
                </CardDescription>
              </CardHeader>
              <CardContent className="trading-card-content space-y-4">
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => router.push('/admin/users')}
                >
                  <Users className="w-4 h-4 mr-2" />
                  사용자 관리
                </Button>
                
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => router.push('/admin/security/login-history')}
                >
                  <Shield className="w-4 h-4 mr-2" />
                  로그인 이력 조회
                </Button>
                
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={() => router.push('/admin/security/metrics')}
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  보안 메트릭스
                </Button>
                
                <Button 
                  variant="outline" 
                  className="w-full justify-start"
                  onClick={fetchDashboardData}
                  disabled={loading}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  통계 새로고침
                </Button>

                <div className="pt-4 border-t border-border">
                  <h4 className="text-sm font-medium mb-3 text-muted-foreground">시스템 상태</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">보안 수준</span>
                      <Badge variant="default" className="bg-bull text-white">
                        높음
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">모니터링 상태</span>
                      <Badge variant="default" className="bg-chart-1 text-white">
                        활성
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">자동 백업</span>
                      <Badge variant="secondary">
                        활성화
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 보안 알림 */}
          {stats && stats.failureCount > 10 && (
            <Card className="trading-card border-destructive/50">
              <CardHeader className="trading-card-header bg-destructive/10">
                <CardTitle className="flex items-center text-destructive">
                  <AlertTriangle className="w-5 h-5 mr-2" />
                  보안 경고
                </CardTitle>
                <CardDescription>
                  오늘 {stats.failureCount}건의 로그인 실패가 감지되었습니다.
                </CardDescription>
              </CardHeader>
              <CardContent className="trading-card-content">
                <div className="flex items-center justify-between">
                  <p className="text-sm">
                    비정상적인 로그인 시도가 감지되었습니다. 보안 점검을 권장합니다.
                  </p>
                  <Button 
                    variant="destructive" 
                    size="sm"
                    onClick={() => router.push('/admin/security/login-history')}
                  >
                    상세 조회
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}

export default function ProtectedAdminDashboard() {
  return (
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <AdminDashboard />
    </ProtectedRoute>
  );
}