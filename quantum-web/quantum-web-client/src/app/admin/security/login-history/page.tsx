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
  Search, 
  Calendar, 
  Clock,
  User,
  CheckCircle,
  XCircle,
  RefreshCw,
  Filter,
  Download,
  Globe
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface LoginHistoryEntry {
  id: string;
  userId: string;
  username: string;
  loginTime: string;
  ipAddress: string;
  userAgent: string;
  success: boolean;
  failureReason?: string;
  sessionId?: string;
  location?: string;
}

function LoginHistoryPage() {
  const { hasRole } = useAuth();
  const router = useRouter();
  const [loginHistory, setLoginHistory] = useState<LoginHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // 필터 상태
  const [filters, setFilters] = useState({
    username: '',
    success: 'all', // 'all', 'success', 'failure', 'locked'
    dateFrom: '',
    dateTo: '',
    limit: '50'
  });

  useEffect(() => {
    fetchLoginHistory();
  }, []);

  const fetchLoginHistory = async () => {
    try {
      setLoading(true);
      setError('');
      
      // 필터 파라미터 생성
      const params = new URLSearchParams();
      if (filters.username) params.append('username', filters.username);
      if (filters.success !== 'all') params.append('success', filters.success);
      if (filters.dateFrom) params.append('dateFrom', filters.dateFrom);
      if (filters.dateTo) params.append('dateTo', filters.dateTo);
      if (filters.limit) params.append('limit', filters.limit);

      const response = await apiClient.admin.getLoginHistory(Object.fromEntries(params));
      setLoginHistory(response.data || []);
    } catch (err) {
      console.error('Failed to fetch login history:', err);
      setError('로그인 이력을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'PPP p', { locale: ko });
    } catch {
      return dateString;
    }
  };

  const getStatusBadge = (success: boolean, failureReason?: string) => {
    if (success) {
      return (
        <Badge variant="default" className="bg-bull text-white">
          <CheckCircle className="w-3 h-3 mr-1" />
          성공
        </Badge>
      );
    } else {
      return (
        <Badge variant="destructive">
          <XCircle className="w-3 h-3 mr-1" />
          실패
        </Badge>
      );
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleSearch = () => {
    fetchLoginHistory();
  };

  const handleReset = () => {
    setFilters({
      username: '',
      success: 'all',
      dateFrom: '',
      dateTo: '',
      limit: '50'
    });
  };

  const exportData = async () => {
    try {
      const csvData = loginHistory.map(entry => ({
        날짜시간: formatDate(entry.loginTime),
        사용자명: entry.username,
        상태: entry.success ? '성공' : '실패',
        IP주소: entry.ipAddress,
        위치: entry.location || 'N/A',
        실패사유: entry.failureReason || '',
        세션ID: entry.sessionId || ''
      }));

      const csv = [
        Object.keys(csvData[0]).join(','),
        ...csvData.map(row => Object.values(row).map(val => `"${val}"`).join(','))
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `login-history-${format(new Date(), 'yyyy-MM-dd')}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
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
      onClick={exportData}
      disabled={loading || loginHistory.length === 0}
    >
      <Download className="w-4 h-4 mr-2" />
      내보내기
    </Button>
  );

  return (
    <AdminLayout 
      title="로그인 이력"
      subtitle="사용자 로그인 시도 및 보안 이력 관리"
      actions={headerActions}
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-6">
          {/* Filters */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Filter className="w-5 h-5 mr-2" />
                필터
              </CardTitle>
              <CardDescription>
                조회할 로그인 이력의 조건을 설정하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username">사용자명</Label>
                  <Input
                    id="username"
                    placeholder="사용자명 검색"
                    value={filters.username}
                    onChange={(e) => handleFilterChange('username', e.target.value)}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="success">상태</Label>
                  <Select value={filters.success} onValueChange={(value) => handleFilterChange('success', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">전체</SelectItem>
                      <SelectItem value="true">성공만</SelectItem>
                      <SelectItem value="false">실패만</SelectItem>
                      <SelectItem value="locked">계정 잠금</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="dateFrom">시작일</Label>
                  <Input
                    id="dateFrom"
                    type="date"
                    value={filters.dateFrom}
                    onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="dateTo">종료일</Label>
                  <Input
                    id="dateTo"
                    type="date"
                    value={filters.dateTo}
                    onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="limit">개수</Label>
                  <Select value={filters.limit} onValueChange={(value) => handleFilterChange('limit', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="20">20개</SelectItem>
                      <SelectItem value="50">50개</SelectItem>
                      <SelectItem value="100">100개</SelectItem>
                      <SelectItem value="200">200개</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="flex space-x-2 mt-4">
                <Button onClick={handleSearch} disabled={loading}>
                  <Search className="w-4 h-4 mr-2" />
                  검색
                </Button>
                <Button variant="outline" onClick={handleReset}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  초기화
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>로그인 이력</CardTitle>
                  <CardDescription>
                    {loading ? '로딩 중...' : `총 ${loginHistory.length}개의 기록`}
                  </CardDescription>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={fetchLoginHistory}
                  disabled={loading}
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="trading-card-content p-0">
              {error && (
                <div className="p-6 text-center text-destructive">
                  {error}
                </div>
              )}
              
              {loading ? (
                <div className="p-6 text-center">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                  <p className="text-muted-foreground">로딩 중...</p>
                </div>
              ) : loginHistory.length === 0 ? (
                <div className="p-6 text-center">
                  <Clock className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">로그인 이력이 없습니다</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-border bg-muted/30">
                      <tr>
                        <th className="text-left p-4 font-medium">날짜/시간</th>
                        <th className="text-left p-4 font-medium">사용자</th>
                        <th className="text-left p-4 font-medium">상태</th>
                        <th className="text-left p-4 font-medium">IP 주소</th>
                        <th className="text-left p-4 font-medium">위치</th>
                        <th className="text-left p-4 font-medium">세션 ID</th>
                        <th className="text-left p-4 font-medium">실패 사유</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loginHistory.map((entry) => (
                        <tr 
                          key={entry.id}
                          className="border-b border-border hover:bg-muted/20 transition-colors"
                        >
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <Calendar className="w-4 h-4 text-muted-foreground" />
                              <span className="text-sm">{formatDate(entry.loginTime)}</span>
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <User className="w-4 h-4 text-muted-foreground" />
                              <span className="font-medium">{entry.username}</span>
                            </div>
                          </td>
                          <td className="p-4">
                            {getStatusBadge(entry.success, entry.failureReason)}
                          </td>
                          <td className="p-4">
                            <code className="text-xs bg-muted px-2 py-1 rounded">
                              {entry.ipAddress}
                            </code>
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-1">
                              <Globe className="w-4 h-4 text-muted-foreground" />
                              <span className="text-sm text-muted-foreground">
                                {entry.location || 'N/A'}
                              </span>
                            </div>
                          </td>
                          <td className="p-4">
                            {entry.sessionId ? (
                              <code className="text-xs bg-muted px-2 py-1 rounded">
                                {entry.sessionId.substring(0, 12)}...
                              </code>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                          <td className="p-4">
                            {entry.failureReason ? (
                              <span className="text-xs text-destructive">
                                {entry.failureReason}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminLayout>
  );
}

export default function ProtectedLoginHistoryPage() {
  return (
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <LoginHistoryPage />
    </ProtectedRoute>
  );
}