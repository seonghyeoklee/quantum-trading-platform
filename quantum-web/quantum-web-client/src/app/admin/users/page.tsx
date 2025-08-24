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
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  Users, 
  Search, 
  Filter,
  RefreshCw,
  UserPlus,
  Settings,
  Shield,
  Eye,
  Lock,
  Unlock,
  MoreHorizontal,
  Calendar,
  Mail,
  Activity
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface User {
  id: string;
  username: string;
  name?: string;
  email?: string;
  roles: string[];
  status: 'ACTIVE' | 'INACTIVE' | 'LOCKED' | 'PENDING';
  lastLoginAt?: string;
  createdAt: string;
  failedAttempts?: number;
  isLocked: boolean;
}

interface UserPageData {
  content: User[];
  totalElements: number;
  totalPages: number;
  number: number;
  size: number;
  first: boolean;
  last: boolean;
}

function UsersManagementPage() {
  const { hasRole } = useAuth();
  const router = useRouter();
  
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [totalUsers, setTotalUsers] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  
  // 필터 및 검색 상태
  const [filters, setFilters] = useState({
    searchTerm: '',
    status: 'all', // 'all', 'ACTIVE', 'INACTIVE', 'LOCKED'
    role: 'all', // 'all', 'ADMIN', 'MANAGER', 'TRADER'
    page: 0,
    size: 20
  });

  useEffect(() => {
    fetchUsers();
  }, [filters]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError('');
      
      let response;
      
      // 검색어가 있는 경우
      if (filters.searchTerm.trim()) {
        const params = {
          page: filters.page,
          size: filters.size
        };
        response = await apiClient.admin.searchUsers(filters.searchTerm, params);
      }
      // 상태별 필터
      else if (filters.status !== 'all') {
        const params = {
          page: filters.page,
          size: filters.size
        };
        response = await apiClient.admin.getUsersByStatus(filters.status, params);
      }
      // 권한별 필터  
      else if (filters.role !== 'all') {
        const params = {
          page: filters.page,
          size: filters.size
        };
        response = await apiClient.admin.getUsersByRole(filters.role, params);
      }
      // 전체 사용자
      else {
        const params = {
          page: filters.page,
          size: filters.size
        };
        response = await apiClient.admin.getUsers(params);
      }

      const userData = response.data as UserPageData;
      setUsers(userData.content || []);
      setTotalUsers(userData.totalElements || 0);
      setTotalPages(userData.totalPages || 0);
      setCurrentPage(userData.number || 0);
      
    } catch (err: any) {
      console.error('Failed to fetch users:', err);
      setError('사용자 목록을 불러오는데 실패했습니다.');
      
      // 임시 더미 데이터 (백엔드 연동 전까지)
      setUsers([
        {
          id: 'USER-101',
          username: 'admin',
          name: '시스템 관리자',
          email: 'admin@quantum.com',
          roles: ['ADMIN', 'MANAGER', 'TRADER'],
          status: 'ACTIVE',
          lastLoginAt: '2025-01-23T16:30:00Z',
          createdAt: '2025-01-01T00:00:00Z',
          failedAttempts: 0,
          isLocked: false
        },
        {
          id: 'USER-102',
          username: 'trader1',
          name: '김트레이더',
          email: 'trader1@quantum.com',
          roles: ['TRADER'],
          status: 'ACTIVE',
          lastLoginAt: '2025-01-23T15:45:00Z',
          createdAt: '2025-01-15T00:00:00Z',
          failedAttempts: 0,
          isLocked: false
        },
        {
          id: 'USER-103',
          username: 'manager1',
          name: '박매니저',
          email: 'manager1@quantum.com',
          roles: ['MANAGER', 'TRADER'],
          status: 'ACTIVE',
          lastLoginAt: '2025-01-23T14:20:00Z',
          createdAt: '2025-01-10T00:00:00Z',
          failedAttempts: 2,
          isLocked: false
        },
        {
          id: 'USER-104',
          username: 'user_locked',
          name: '잠긴사용자',
          email: 'locked@quantum.com',
          roles: ['TRADER'],
          status: 'LOCKED',
          lastLoginAt: '2025-01-20T10:00:00Z',
          createdAt: '2025-01-05T00:00:00Z',
          failedAttempts: 5,
          isLocked: true
        }
      ]);
      setTotalUsers(4);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 0 }));
  };

  const handleSearch = () => {
    setFilters(prev => ({ ...prev, page: 0 }));
    fetchUsers();
  };

  const handleReset = () => {
    setFilters({
      searchTerm: '',
      status: 'all',
      role: 'all',
      page: 0,
      size: 20
    });
  };

  const handlePageChange = (newPage: number) => {
    setFilters(prev => ({ ...prev, page: newPage }));
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'PPP p', { locale: ko });
    } catch {
      return dateString;
    }
  };

  const getStatusBadge = (status: string, isLocked: boolean) => {
    if (isLocked) {
      return <Badge variant="destructive">잠김</Badge>;
    }
    
    switch (status) {
      case 'ACTIVE':
        return <Badge variant="default" className="bg-bull text-white">활성</Badge>;
      case 'INACTIVE':
        return <Badge variant="secondary">비활성</Badge>;
      case 'LOCKED':
        return <Badge variant="destructive">잠금</Badge>;
      case 'PENDING':
        return <Badge variant="outline">대기</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getRoleBadges = (roles: string[]) => {
    return roles.map(role => {
      const variant = role === 'ADMIN' ? 'destructive' : 
                    role === 'MANAGER' ? 'default' : 'secondary';
      return (
        <Badge key={role} variant={variant} className="text-xs">
          {role}
        </Badge>
      );
    });
  };

  const getUserInitials = (username: string, name?: string) => {
    if (name) {
      return name.substring(0, 2).toUpperCase();
    }
    return username.substring(0, 2).toUpperCase();
  };

  const handleViewUser = (userId: string) => {
    router.push(`/admin/users/${userId}`);
  };

  const handleUnlockAccount = async (userId: string, username: string) => {
    try {
      await apiClient.admin.unlockAccount(userId, '관리자에 의한 계정 잠금 해제');
      alert(`${username} 계정이 잠금 해제되었습니다.`);
      fetchUsers(); // 목록 새로고침
    } catch (err) {
      console.error('Failed to unlock account:', err);
      alert('계정 잠금 해제에 실패했습니다.');
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
    <>
      <Button 
        variant="outline" 
        size="sm" 
        onClick={handleSearch}
        disabled={loading}
      >
        <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
        새로고침
      </Button>
      <Button variant="default" size="sm">
        <UserPlus className="w-4 h-4 mr-2" />
        사용자 추가
      </Button>
    </>
  );

  return (
    <AdminLayout 
      title="사용자 관리"
      subtitle="전체 사용자 목록 및 권한 관리"
      actions={headerActions}
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-6">
          {/* 통계 요약 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="trading-card">
              <CardContent className="trading-card-content">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">전체 사용자</p>
                    <p className="text-2xl font-bold">{totalUsers}</p>
                  </div>
                  <Users className="w-8 h-8 text-primary" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="trading-card">
              <CardContent className="trading-card-content">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">활성 사용자</p>
                    <p className="text-2xl font-bold text-bull">
                      {users.filter(u => u.status === 'ACTIVE').length}
                    </p>
                  </div>
                  <Activity className="w-8 h-8 text-bull" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="trading-card">
              <CardContent className="trading-card-content">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">관리자</p>
                    <p className="text-2xl font-bold text-chart-1">
                      {users.filter(u => u.roles.includes('ADMIN')).length}
                    </p>
                  </div>
                  <Shield className="w-8 h-8 text-chart-1" />
                </div>
              </CardContent>
            </Card>
            
            <Card className="trading-card">
              <CardContent className="trading-card-content">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">잠긴 계정</p>
                    <p className="text-2xl font-bold text-destructive">
                      {users.filter(u => u.isLocked).length}
                    </p>
                  </div>
                  <Lock className="w-8 h-8 text-destructive" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 필터 및 검색 */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Filter className="w-5 h-5 mr-2" />
                필터 & 검색
              </CardTitle>
              <CardDescription>
                사용자를 검색하고 필터링하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="searchTerm">검색</Label>
                  <Input
                    id="searchTerm"
                    placeholder="사용자명, 이름, 이메일"
                    value={filters.searchTerm}
                    onChange={(e) => handleFilterChange('searchTerm', e.target.value)}
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="status">상태</Label>
                  <Select value={filters.status} onValueChange={(value) => handleFilterChange('status', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">전체</SelectItem>
                      <SelectItem value="ACTIVE">활성</SelectItem>
                      <SelectItem value="INACTIVE">비활성</SelectItem>
                      <SelectItem value="LOCKED">잠김</SelectItem>
                      <SelectItem value="PENDING">대기</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="role">권한</Label>
                  <Select value={filters.role} onValueChange={(value) => handleFilterChange('role', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">전체</SelectItem>
                      <SelectItem value="ADMIN">관리자</SelectItem>
                      <SelectItem value="MANAGER">매니저</SelectItem>
                      <SelectItem value="TRADER">트레이더</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="size">개수</Label>
                  <Select value={filters.size.toString()} onValueChange={(value) => handleFilterChange('size', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10개</SelectItem>
                      <SelectItem value="20">20개</SelectItem>
                      <SelectItem value="50">50개</SelectItem>
                      <SelectItem value="100">100개</SelectItem>
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
                <Button 
                  variant="ghost" 
                  onClick={fetchUsers}
                  disabled={loading}
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 사용자 목록 */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>사용자 목록</CardTitle>
                  <CardDescription>
                    {loading ? '로딩 중...' : `${totalUsers}명의 사용자 중 ${users.length}명 표시`}
                  </CardDescription>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={fetchUsers}
                  disabled={loading}
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="trading-card-content p-0">
              {error && !users.length && (
                <div className="p-6 text-center text-muted-foreground">
                  <p className="text-destructive">{error}</p>
                  <p className="text-sm mt-2">임시 데이터로 표시 중입니다.</p>
                </div>
              )}
              
              {loading ? (
                <div className="p-6 text-center">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                  <p className="text-muted-foreground">로딩 중...</p>
                </div>
              ) : users.length === 0 ? (
                <div className="p-6 text-center">
                  <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">사용자가 없습니다</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="border-b border-border bg-muted/30">
                      <tr>
                        <th className="text-left p-4 font-medium">사용자</th>
                        <th className="text-left p-4 font-medium">상태</th>
                        <th className="text-left p-4 font-medium">권한</th>
                        <th className="text-left p-4 font-medium">마지막 로그인</th>
                        <th className="text-left p-4 font-medium">실패 시도</th>
                        <th className="text-left p-4 font-medium">작업</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr 
                          key={user.id}
                          className="border-b border-border hover:bg-muted/20 transition-colors"
                        >
                          <td className="p-4">
                            <div className="flex items-center space-x-3">
                              <Avatar className="w-10 h-10">
                                <AvatarImage src="" alt={user.username} />
                                <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                                  {getUserInitials(user.username, user.name)}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <p className="font-medium">{user.name || user.username}</p>
                                <p className="text-sm text-muted-foreground">@{user.username}</p>
                                {user.email && (
                                  <p className="text-xs text-muted-foreground flex items-center">
                                    <Mail className="w-3 h-3 mr-1" />
                                    {user.email}
                                  </p>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="p-4">
                            {getStatusBadge(user.status, user.isLocked)}
                          </td>
                          <td className="p-4">
                            <div className="flex flex-wrap gap-1">
                              {getRoleBadges(user.roles)}
                            </div>
                          </td>
                          <td className="p-4">
                            {user.lastLoginAt ? (
                              <div className="flex items-center space-x-1">
                                <Calendar className="w-4 h-4 text-muted-foreground" />
                                <span className="text-sm">{formatDate(user.lastLoginAt)}</span>
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-sm">없음</span>
                            )}
                          </td>
                          <td className="p-4">
                            {user.failedAttempts && user.failedAttempts > 0 ? (
                              <Badge variant="outline" className="text-xs">
                                {user.failedAttempts}회
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground text-sm">0회</span>
                            )}
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleViewUser(user.id)}
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              {user.isLocked && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleUnlockAccount(user.id, user.username)}
                                  className="text-bull hover:text-bull"
                                >
                                  <Unlock className="w-4 h-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                              >
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 0}
              >
                이전
              </Button>
              
              <span className="text-sm text-muted-foreground">
                {currentPage + 1} / {totalPages} 페이지
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages - 1}
              >
                다음
              </Button>
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}

export default function ProtectedUsersManagementPage() {
  return (
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <UsersManagementPage />
    </ProtectedRoute>
  );
}