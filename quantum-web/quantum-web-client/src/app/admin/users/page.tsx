'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Users,
  UserPlus,
  Shield,
  Lock,
  Unlock,
  Edit,
  Trash2,
  Search,
  Filter,
  MoreHorizontal,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Mail,
  Calendar,
  Activity
} from 'lucide-react';

interface User {
  id: string;
  username: string;
  name: string;
  email: string;
  roles: string[];
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
  lastLogin: string | null;
  createdAt: string;
  loginCount: number;
  isOnline: boolean;
}

const mockUsers: User[] = [
  {
    id: 'USER-001',
    username: 'admin',
    name: '시스템 관리자',
    email: 'admin@quantum-trading.com',
    roles: ['ADMIN'],
    status: 'ACTIVE',
    lastLogin: '2024-01-15T11:30:00Z',
    createdAt: '2024-01-01T00:00:00Z',
    loginCount: 147,
    isOnline: true
  },
  {
    id: 'USER-002',
    username: 'manager1',
    name: '김매니저',
    email: 'manager1@quantum-trading.com',
    roles: ['MANAGER'],
    status: 'ACTIVE',
    lastLogin: '2024-01-15T10:15:00Z',
    createdAt: '2024-01-02T09:00:00Z',
    loginCount: 89,
    isOnline: true
  },
  {
    id: 'USER-003',
    username: 'trader1',
    name: '이트레이더',
    email: 'trader1@quantum-trading.com',
    roles: ['TRADER'],
    status: 'ACTIVE',
    lastLogin: '2024-01-15T09:45:00Z',
    createdAt: '2024-01-03T14:30:00Z',
    loginCount: 203,
    isOnline: false
  },
  {
    id: 'USER-004',
    username: 'analyst1',
    name: '박분석가',
    email: 'analyst1@quantum-trading.com',
    roles: ['TRADER', 'ANALYST'],
    status: 'INACTIVE',
    lastLogin: '2024-01-10T16:20:00Z',
    createdAt: '2024-01-05T11:00:00Z',
    loginCount: 45,
    isOnline: false
  }
];

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  const getStatusColor = (status: User['status']) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800';
      case 'INACTIVE':
        return 'bg-gray-100 text-gray-800';
      case 'SUSPENDED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-100 text-purple-800';
      case 'MANAGER':
        return 'bg-blue-100 text-blue-800';
      case 'TRADER':
        return 'bg-green-100 text-green-800';
      case 'ANALYST':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '없음';
    return new Date(dateString).toLocaleString('ko-KR');
  };

  const toggleUserStatus = (userId: string) => {
    setUsers(prev =>
      prev.map(user =>
        user.id === userId
          ? {
              ...user,
              status: user.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE'
            }
          : user
      )
    );
  };

  const activeUsers = users.filter(user => user.status === 'ACTIVE').length;
  const onlineUsers = users.filter(user => user.isOnline).length;
  const adminUsers = users.filter(user => user.roles.includes('ADMIN')).length;

  return (
    <ProtectedRoute requiredRoles={['ADMIN']}>
      <AdminLayout>
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">사용자 관리</h1>
              <p className="text-muted-foreground">
                시스템 사용자 계정과 권한을 관리하세요.
              </p>
            </div>
            <div className="flex gap-2 mt-4 sm:mt-0">
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                필터
              </Button>
              <Button>
                <UserPlus className="h-4 w-4 mr-2" />
                사용자 추가
              </Button>
            </div>
          </div>

          {/* 사용자 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">전체 사용자</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{users.length}</div>
                <p className="text-xs text-muted-foreground">등록된 사용자 수</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">활성 사용자</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{activeUsers}</div>
                <p className="text-xs text-muted-foreground">활성화된 계정</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">온라인</CardTitle>
                <Activity className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{onlineUsers}</div>
                <p className="text-xs text-muted-foreground">현재 접속 중</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">관리자</CardTitle>
                <Shield className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">{adminUsers}</div>
                <p className="text-xs text-muted-foreground">관리자 권한</p>
              </CardContent>
            </Card>
          </div>

          {/* 보안 알림 */}
          <Alert className="border-blue-200 bg-blue-50">
            <Shield className="h-4 w-4 text-blue-600" />
            <AlertDescription>
              <div className="flex items-center justify-between">
                <span>
                  보안을 위해 90일 이상 미접속 계정은 자동으로 비활성화됩니다.
                </span>
                <Button size="sm" variant="outline">
                  보안 정책 보기
                </Button>
              </div>
            </AlertDescription>
          </Alert>

          {/* 사용자 목록 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>사용자 목록</CardTitle>
                <div className="flex gap-2">
                  <div className="relative">
                    <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="사용자 검색..."
                      className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm"
                    />
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      {/* 사용자 아바타 */}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold ${
                        user.roles.includes('ADMIN') ? 'bg-purple-600' :
                        user.roles.includes('MANAGER') ? 'bg-blue-600' :
                        'bg-green-600'
                      }`}>
                        {user.name.charAt(0)}
                      </div>

                      {/* 온라인 상태 */}
                      {user.isOnline && (
                        <div className="w-3 h-3 bg-green-500 rounded-full border-2 border-white absolute ml-7 -mt-7" />
                      )}

                      {/* 사용자 정보 */}
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{user.name}</span>
                          <Badge className={getStatusColor(user.status)}>
                            {user.status}
                          </Badge>
                          {user.isOnline && (
                            <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                              온라인
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                          <span>@{user.username}</span>
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {user.email}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-2">
                          {user.roles.map((role) => (
                            <Badge key={role} className={getRoleColor(role)}>
                              {role}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* 사용자 통계 및 액션 */}
                    <div className="flex items-center gap-6">
                      <div className="text-right text-sm">
                        <div className="text-gray-600">
                          최근 접속: {formatDate(user.lastLogin)}
                        </div>
                        <div className="text-gray-500">
                          로그인 {user.loginCount}회
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleUserStatus(user.id)}
                        >
                          {user.status === 'ACTIVE' ? (
                            <>
                              <Lock className="h-4 w-4 mr-1" />
                              비활성화
                            </>
                          ) : (
                            <>
                              <Unlock className="h-4 w-4 mr-1" />
                              활성화
                            </>
                          )}
                        </Button>

                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4 mr-1" />
                          편집
                        </Button>

                        <Button variant="outline" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 권한 관리 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">권한 그룹</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-3">
                      <Shield className="h-5 w-5 text-purple-600" />
                      <div>
                        <div className="font-medium">ADMIN</div>
                        <div className="text-sm text-gray-600">모든 시스템 권한</div>
                      </div>
                    </div>
                    <Badge className="bg-purple-100 text-purple-800">
                      {adminUsers}명
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-3">
                      <Users className="h-5 w-5 text-blue-600" />
                      <div>
                        <div className="font-medium">MANAGER</div>
                        <div className="text-sm text-gray-600">포트폴리오 관리 권한</div>
                      </div>
                    </div>
                    <Badge className="bg-blue-100 text-blue-800">
                      {users.filter(u => u.roles.includes('MANAGER')).length}명
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-3">
                      <Activity className="h-5 w-5 text-green-600" />
                      <div>
                        <div className="font-medium">TRADER</div>
                        <div className="text-sm text-gray-600">거래 실행 권한</div>
                      </div>
                    </div>
                    <Badge className="bg-green-100 text-green-800">
                      {users.filter(u => u.roles.includes('TRADER')).length}명
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">보안 설정</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">비밀번호 복잡도 검사</div>
                      <div className="text-sm text-gray-600">강화된 비밀번호 정책 적용</div>
                    </div>
                    <input type="checkbox" className="rounded" defaultChecked />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">2단계 인증 강제</div>
                      <div className="text-sm text-gray-600">모든 사용자 2FA 필수</div>
                    </div>
                    <input type="checkbox" className="rounded" defaultChecked />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">자동 로그아웃</div>
                      <div className="text-sm text-gray-600">30분 비활성 시 자동 로그아웃</div>
                    </div>
                    <input type="checkbox" className="rounded" defaultChecked />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">접속 로그 기록</div>
                      <div className="text-sm text-gray-600">모든 로그인 활동 기록</div>
                    </div>
                    <input type="checkbox" className="rounded" defaultChecked />
                  </div>

                  <div className="pt-4 border-t">
                    <Button variant="outline" className="w-full">
                      보안 정책 상세 설정
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 최근 활동 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">최근 사용자 활동</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm">관리자가 로그인했습니다</span>
                  </div>
                  <span className="text-xs text-gray-500">5분 전</span>
                </div>

                <div className="flex items-center justify-between py-2 border-b">
                  <div className="flex items-center gap-3">
                    <UserPlus className="h-4 w-4 text-blue-600" />
                    <span className="text-sm">새로운 트레이더 계정이 생성되었습니다</span>
                  </div>
                  <span className="text-xs text-gray-500">1시간 전</span>
                </div>

                <div className="flex items-center justify-between py-2 border-b">
                  <div className="flex items-center gap-3">
                    <Lock className="h-4 w-4 text-orange-600" />
                    <span className="text-sm">박분석가 계정이 비활성화되었습니다</span>
                  </div>
                  <span className="text-xs text-gray-500">2시간 전</span>
                </div>

                <div className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-4 w-4 text-red-600" />
                    <span className="text-sm">비정상적인 로그인 시도가 감지되었습니다</span>
                  </div>
                  <span className="text-xs text-gray-500">3시간 전</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}