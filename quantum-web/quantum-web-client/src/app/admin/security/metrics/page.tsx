'use client';

import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import AdminLayout from '@/components/layout/AdminLayout';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Shield, 
  TrendingUp,
  TrendingDown,
  Globe,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Filter,
  Users,
  Activity,
  Eye,
  Download,
  BarChart3,
  PieChart,
  Calendar,
  MapPin
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { ko } from 'date-fns/locale';

interface SecurityMetrics {
  totalLogins: number;
  successfulLogins: number;
  failedLogins: number;
  uniqueUsers: number;
  uniqueIPs: number;
  successRate: number;
  topFailureReasons: { reason: string; count: number }[];
  hourlyDistribution: { hour: number; count: number }[];
  ipAnalysis: { 
    ip: string; 
    attempts: number; 
    successes: number; 
    failures: number; 
    lastAttempt: string;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  }[];
  userActivity: {
    username: string;
    totalAttempts: number;
    successfulLogins: number;
    failedAttempts: number;
    lastLogin: string;
    accountStatus: 'ACTIVE' | 'LOCKED' | 'INACTIVE';
  }[];
  securityAlerts: {
    id: string;
    type: 'BRUTE_FORCE' | 'SUSPICIOUS_IP' | 'ACCOUNT_LOCKOUT' | 'MULTIPLE_FAILURES';
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    description: string;
    timestamp: string;
    resolved: boolean;
  }[];
}

interface DateRange {
  start: string;
  end: string;
}

function SecurityMetricsPage() {
  const { hasRole } = useAuth();
  const router = useRouter();
  
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState<DateRange>({
    start: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });
  const [filterPeriod, setFilterPeriod] = useState('7days');

  useEffect(() => {
    fetchSecurityMetrics();
  }, [dateRange]);

  const fetchSecurityMetrics = async () => {
    try {
      setLoading(true);
      setError('');
      
      // In real implementation, this would call the backend API
      // const response = await apiClient.admin.getSecurityMetrics({
      //   startDate: dateRange.start,
      //   endDate: dateRange.end
      // });
      
      // For now, using comprehensive dummy data
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      
      setMetrics({
        totalLogins: 1247,
        successfulLogins: 1089,
        failedLogins: 158,
        uniqueUsers: 34,
        uniqueIPs: 67,
        successRate: 87.3,
        topFailureReasons: [
          { reason: '잘못된 비밀번호', count: 89 },
          { reason: '계정 잠금', count: 34 },
          { reason: '잘못된 사용자명', count: 23 },
          { reason: '토큰 만료', count: 12 }
        ],
        hourlyDistribution: [
          { hour: 0, count: 12 }, { hour: 1, count: 8 }, { hour: 2, count: 5 },
          { hour: 3, count: 3 }, { hour: 4, count: 2 }, { hour: 5, count: 4 },
          { hour: 6, count: 15 }, { hour: 7, count: 28 }, { hour: 8, count: 45 },
          { hour: 9, count: 89 }, { hour: 10, count: 102 }, { hour: 11, count: 87 },
          { hour: 12, count: 76 }, { hour: 13, count: 95 }, { hour: 14, count: 108 },
          { hour: 15, count: 94 }, { hour: 16, count: 82 }, { hour: 17, count: 91 },
          { hour: 18, count: 67 }, { hour: 19, count: 45 }, { hour: 20, count: 32 },
          { hour: 21, count: 28 }, { hour: 22, count: 19 }, { hour: 23, count: 15 }
        ],
        ipAnalysis: [
          {
            ip: '192.168.1.100',
            attempts: 45,
            successes: 42,
            failures: 3,
            lastAttempt: new Date().toISOString(),
            riskLevel: 'LOW'
          },
          {
            ip: '203.0.113.15',
            attempts: 23,
            successes: 8,
            failures: 15,
            lastAttempt: new Date(Date.now() - 3600000).toISOString(),
            riskLevel: 'HIGH'
          },
          {
            ip: '192.168.1.101',
            attempts: 38,
            successes: 35,
            failures: 3,
            lastAttempt: new Date(Date.now() - 1800000).toISOString(),
            riskLevel: 'LOW'
          },
          {
            ip: '10.0.0.25',
            attempts: 19,
            successes: 12,
            failures: 7,
            lastAttempt: new Date(Date.now() - 7200000).toISOString(),
            riskLevel: 'MEDIUM'
          }
        ],
        userActivity: [
          {
            username: 'admin',
            totalAttempts: 89,
            successfulLogins: 87,
            failedAttempts: 2,
            lastLogin: new Date().toISOString(),
            accountStatus: 'ACTIVE'
          },
          {
            username: 'trader1',
            totalAttempts: 156,
            successfulLogins: 154,
            failedAttempts: 2,
            lastLogin: new Date(Date.now() - 1800000).toISOString(),
            accountStatus: 'ACTIVE'
          },
          {
            username: 'manager1',
            totalAttempts: 67,
            successfulLogins: 65,
            failedAttempts: 2,
            lastLogin: new Date(Date.now() - 3600000).toISOString(),
            accountStatus: 'ACTIVE'
          },
          {
            username: 'test_user',
            totalAttempts: 23,
            successfulLogins: 5,
            failedAttempts: 18,
            lastLogin: new Date(Date.now() - 86400000).toISOString(),
            accountStatus: 'LOCKED'
          }
        ],
        securityAlerts: [
          {
            id: '1',
            type: 'BRUTE_FORCE',
            severity: 'HIGH',
            description: 'IP 203.0.113.15에서 15회 연속 로그인 실패 감지',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            resolved: false
          },
          {
            id: '2',
            type: 'ACCOUNT_LOCKOUT',
            severity: 'MEDIUM',
            description: '사용자 test_user 계정이 잠금 상태로 변경됨',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            resolved: false
          },
          {
            id: '3',
            type: 'SUSPICIOUS_IP',
            severity: 'MEDIUM',
            description: '새로운 IP 주소에서 관리자 계정 로그인 시도',
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            resolved: true
          }
        ]
      });
      
    } catch (err: any) {
      console.error('Failed to fetch security metrics:', err);
      setError('보안 메트릭스를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodChange = (period: string) => {
    setFilterPeriod(period);
    const end = new Date();
    let start: Date;
    
    switch (period) {
      case '1day':
        start = subDays(end, 1);
        break;
      case '7days':
        start = subDays(end, 7);
        break;
      case '30days':
        start = subDays(end, 30);
        break;
      case '90days':
        start = subDays(end, 90);
        break;
      default:
        start = subDays(end, 7);
    }
    
    setDateRange({
      start: format(start, 'yyyy-MM-dd'),
      end: format(end, 'yyyy-MM-dd')
    });
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'LOW': return 'text-bull';
      case 'MEDIUM': return 'text-warning-amber';
      case 'HIGH': return 'text-destructive';
      default: return 'text-muted-foreground';
    }
  };

  const getRiskLevelBadge = (level: string) => {
    switch (level) {
      case 'LOW': return <Badge variant="default" className="bg-bull text-white text-xs">낮음</Badge>;
      case 'MEDIUM': return <Badge variant="secondary" className="text-xs">보통</Badge>;
      case 'HIGH': return <Badge variant="destructive" className="text-xs">높음</Badge>;
      default: return <Badge variant="outline" className="text-xs">알 수 없음</Badge>;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'LOW': return <Badge variant="outline" className="text-xs">낮음</Badge>;
      case 'MEDIUM': return <Badge variant="secondary" className="text-xs">보통</Badge>;
      case 'HIGH': return <Badge variant="destructive" className="text-xs">높음</Badge>;
      case 'CRITICAL': return <Badge variant="destructive" className="bg-destructive text-white text-xs">긴급</Badge>;
      default: return <Badge variant="outline" className="text-xs">알 수 없음</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE': return <Badge variant="default" className="bg-bull text-white text-xs">활성</Badge>;
      case 'LOCKED': return <Badge variant="destructive" className="text-xs">잠금</Badge>;
      case 'INACTIVE': return <Badge variant="outline" className="text-xs">비활성</Badge>;
      default: return <Badge variant="outline" className="text-xs">알 수 없음</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'PPP p', { locale: ko });
    } catch {
      return dateString;
    }
  };

  const exportData = async () => {
    if (!metrics) return;
    
    const data = {
      exportDate: new Date().toISOString(),
      dateRange,
      summary: {
        totalLogins: metrics.totalLogins,
        successRate: metrics.successRate,
        uniqueUsers: metrics.uniqueUsers,
        uniqueIPs: metrics.uniqueIPs
      },
      securityAlerts: metrics.securityAlerts,
      ipAnalysis: metrics.ipAnalysis,
      topFailureReasons: metrics.topFailureReasons
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `security-metrics-${format(new Date(), 'yyyy-MM-dd')}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
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
    <>
      <Button 
        variant="outline" 
        size="sm" 
        onClick={exportData}
        disabled={loading || !metrics}
      >
        <Download className="w-4 h-4 mr-2" />
        내보내기
      </Button>
      <Button 
        variant="outline" 
        size="sm" 
        onClick={fetchSecurityMetrics}
        disabled={loading}
      >
        <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
        새로고침
      </Button>
    </>
  );

  return (
    <AdminLayout 
      title="보안 메트릭스"
      subtitle="상세 보안 분석 및 위험 평가"
      actions={headerActions}
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-8">
          {/* Filters */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Filter className="w-5 h-5 mr-2" />
                분석 기간
              </CardTitle>
              <CardDescription>
                보안 메트릭스 분석 기간을 선택하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>기간 선택</Label>
                  <Select value={filterPeriod} onValueChange={handlePeriodChange}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1day">최근 1일</SelectItem>
                      <SelectItem value="7days">최근 7일</SelectItem>
                      <SelectItem value="30days">최근 30일</SelectItem>
                      <SelectItem value="90days">최근 90일</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="startDate">시작일</Label>
                  <Input
                    id="startDate"
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="endDate">종료일</Label>
                  <Input
                    id="endDate"
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                  />
                </div>
                
                <div className="flex items-end">
                  <Button onClick={fetchSecurityMetrics} disabled={loading} className="w-full">
                    <Activity className="w-4 h-4 mr-2" />
                    분석 실행
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">보안 메트릭스 분석 중...</p>
            </div>
          ) : error ? (
            <Card className="trading-card border-destructive/50">
              <CardContent className="trading-card-content text-center py-12">
                <XCircle className="w-12 h-12 mx-auto mb-4 text-destructive" />
                <p className="text-destructive">{error}</p>
              </CardContent>
            </Card>
          ) : metrics ? (
            <>
              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="trading-card">
                  <CardContent className="trading-card-content">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">총 로그인 시도</p>
                        <p className="text-3xl font-bold">{metrics.totalLogins}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          성공 {metrics.successfulLogins} + 실패 {metrics.failedLogins}
                        </p>
                      </div>
                      <Activity className="w-10 h-10 text-primary" />
                    </div>
                  </CardContent>
                </Card>

                <Card className="trading-card">
                  <CardContent className="trading-card-content">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">성공률</p>
                        <div className="flex items-center space-x-2">
                          <p className={`text-3xl font-bold ${metrics.successRate >= 90 ? 'text-bull' : metrics.successRate >= 70 ? 'text-warning-amber' : 'text-destructive'}`}>
                            {metrics.successRate.toFixed(1)}%
                          </p>
                          {metrics.successRate >= 80 ? (
                            <TrendingUp className="w-4 h-4 text-bull" />
                          ) : (
                            <TrendingDown className="w-4 h-4 text-destructive" />
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {metrics.successRate >= 90 ? '매우 양호' : metrics.successRate >= 70 ? '양호' : '주의 필요'}
                        </p>
                      </div>
                      <CheckCircle className={`w-10 h-10 ${metrics.successRate >= 90 ? 'text-bull' : metrics.successRate >= 70 ? 'text-warning-amber' : 'text-destructive'}`} />
                    </div>
                  </CardContent>
                </Card>

                <Card className="trading-card">
                  <CardContent className="trading-card-content">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">활성 사용자</p>
                        <p className="text-3xl font-bold text-chart-1">{metrics.uniqueUsers}</p>
                        <p className="text-xs text-muted-foreground mt-1">고유 사용자</p>
                      </div>
                      <Users className="w-10 h-10 text-chart-1" />
                    </div>
                  </CardContent>
                </Card>

                <Card className="trading-card">
                  <CardContent className="trading-card-content">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">접속 IP</p>
                        <p className="text-3xl font-bold text-chart-6">{metrics.uniqueIPs}</p>
                        <p className="text-xs text-muted-foreground mt-1">고유 IP 주소</p>
                      </div>
                      <Globe className="w-10 h-10 text-chart-6" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Security Alerts */}
              <Card className="trading-card">
                <CardHeader className="trading-card-header">
                  <CardTitle className="flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2" />
                    보안 알림
                  </CardTitle>
                  <CardDescription>
                    감지된 보안 위험 및 알림 현황
                  </CardDescription>
                </CardHeader>
                <CardContent className="trading-card-content">
                  {metrics.securityAlerts.length === 0 ? (
                    <div className="text-center py-8">
                      <CheckCircle className="w-12 h-12 mx-auto mb-4 text-bull" />
                      <p className="text-muted-foreground">현재 보안 알림이 없습니다</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {metrics.securityAlerts.map((alert) => (
                        <div 
                          key={alert.id}
                          className={`p-4 rounded-lg border ${alert.resolved ? 'bg-muted/30 border-border' : alert.severity === 'CRITICAL' ? 'bg-destructive/10 border-destructive/50' : alert.severity === 'HIGH' ? 'bg-destructive/5 border-destructive/30' : 'bg-warning-amber/5 border-warning-amber/30'}`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-2">
                                {getSeverityBadge(alert.severity)}
                                <Badge variant="outline" className="text-xs">
                                  {alert.type.replace('_', ' ')}
                                </Badge>
                                {alert.resolved && (
                                  <Badge variant="default" className="bg-bull text-white text-xs">
                                    해결됨
                                  </Badge>
                                )}
                              </div>
                              <p className="text-sm font-medium mb-1">{alert.description}</p>
                              <p className="text-xs text-muted-foreground">
                                {formatDate(alert.timestamp)}
                              </p>
                            </div>
                            {!alert.resolved && (
                              <Button variant="outline" size="sm">
                                조치하기
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* IP Analysis and User Activity */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* IP 위험도 분석 */}
                <Card className="trading-card">
                  <CardHeader className="trading-card-header">
                    <CardTitle className="flex items-center">
                      <MapPin className="w-5 h-5 mr-2" />
                      IP 위험도 분석
                    </CardTitle>
                    <CardDescription>
                      IP 주소별 접속 패턴 및 위험도 평가
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="trading-card-content p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="border-b border-border bg-muted/30">
                          <tr>
                            <th className="text-left p-4 font-medium">IP 주소</th>
                            <th className="text-left p-4 font-medium">시도</th>
                            <th className="text-left p-4 font-medium">성공률</th>
                            <th className="text-left p-4 font-medium">위험도</th>
                          </tr>
                        </thead>
                        <tbody>
                          {metrics.ipAnalysis.map((ip, index) => (
                            <tr key={index} className="border-b border-border hover:bg-muted/20">
                              <td className="p-4">
                                <code className="text-sm bg-muted px-2 py-1 rounded">
                                  {ip.ip}
                                </code>
                              </td>
                              <td className="p-4">
                                <div className="text-sm">
                                  총 {ip.attempts}회
                                  <div className="text-xs text-muted-foreground">
                                    성공 {ip.successes} / 실패 {ip.failures}
                                  </div>
                                </div>
                              </td>
                              <td className="p-4">
                                <span className={`text-sm font-medium ${(ip.successes / ip.attempts * 100) >= 80 ? 'text-bull' : 'text-destructive'}`}>
                                  {((ip.successes / ip.attempts) * 100).toFixed(1)}%
                                </span>
                              </td>
                              <td className="p-4">
                                {getRiskLevelBadge(ip.riskLevel)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                {/* 사용자 활동 분석 */}
                <Card className="trading-card">
                  <CardHeader className="trading-card-header">
                    <CardTitle className="flex items-center">
                      <Users className="w-5 h-5 mr-2" />
                      사용자 활동 분석
                    </CardTitle>
                    <CardDescription>
                      사용자별 로그인 패턴 및 계정 상태
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="trading-card-content p-0">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="border-b border-border bg-muted/30">
                          <tr>
                            <th className="text-left p-4 font-medium">사용자</th>
                            <th className="text-left p-4 font-medium">활동</th>
                            <th className="text-left p-4 font-medium">상태</th>
                          </tr>
                        </thead>
                        <tbody>
                          {metrics.userActivity.map((user, index) => (
                            <tr key={index} className="border-b border-border hover:bg-muted/20">
                              <td className="p-4">
                                <div className="font-medium">{user.username}</div>
                                <div className="text-xs text-muted-foreground">
                                  최종 로그인: {formatDate(user.lastLogin)}
                                </div>
                              </td>
                              <td className="p-4">
                                <div className="text-sm">
                                  총 {user.totalAttempts}회 시도
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  성공 {user.successfulLogins} / 실패 {user.failedAttempts}
                                </div>
                              </td>
                              <td className="p-4">
                                {getStatusBadge(user.accountStatus)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Failure Reasons Analysis */}
              <Card className="trading-card">
                <CardHeader className="trading-card-header">
                  <CardTitle className="flex items-center">
                    <PieChart className="w-5 h-5 mr-2" />
                    실패 원인 분석
                  </CardTitle>
                  <CardDescription>
                    로그인 실패 원인별 통계
                  </CardDescription>
                </CardHeader>
                <CardContent className="trading-card-content">
                  <div className="space-y-4">
                    {metrics.topFailureReasons.map((reason, index) => {
                      const percentage = (reason.count / metrics.failedLogins) * 100;
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{reason.reason}</span>
                            <div className="text-right">
                              <span className="text-sm font-medium">{reason.count}건</span>
                              <span className="text-xs text-muted-foreground ml-2">
                                ({percentage.toFixed(1)}%)
                              </span>
                            </div>
                          </div>
                          <div className="w-full bg-muted rounded-full h-2">
                            <div 
                              className="bg-destructive h-2 rounded-full transition-all duration-300" 
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>
      </div>
    </AdminLayout>
  );
}

export default function ProtectedSecurityMetricsPage() {
  return (
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <SecurityMetricsPage />
    </ProtectedRoute>
  );
}