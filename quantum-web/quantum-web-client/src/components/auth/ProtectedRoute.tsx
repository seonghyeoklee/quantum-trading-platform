'use client';

import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2, Shield, AlertTriangle } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string | string[];
  fallback?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  fallback
}) => {
  const { user, isAuthenticated, isLoading, hasRole, hasAnyRole } = useAuth();

  // 로딩 중
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-96">
          <CardContent className="flex flex-col items-center justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">로딩 중</h3>
            <p className="text-sm text-gray-600 text-center">
              사용자 정보를 확인하고 있습니다...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 인증되지 않음
  if (!isAuthenticated) {
    if (fallback) {
      return <>{fallback}</>;
    }
    
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-96">
          <CardContent className="flex flex-col items-center justify-center p-8">
            <Shield className="h-12 w-12 text-red-600 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">인증 필요</h3>
            <p className="text-sm text-gray-600 text-center mb-4">
              이 페이지에 접근하려면 로그인이 필요합니다.
            </p>
            <button
              onClick={() => window.location.href = '/login'}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              로그인 페이지로 이동
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // 권한 확인
  if (requiredRoles) {
    const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
    const hasRequiredRole = hasAnyRole(roles);

    if (!hasRequiredRole) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <Card className="w-96">
            <CardContent className="flex flex-col items-center justify-center p-8">
              <AlertTriangle className="h-12 w-12 text-amber-600 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">접근 권한 없음</h3>
              <p className="text-sm text-gray-600 text-center mb-4">
                이 페이지에 접근할 권한이 없습니다.
              </p>
              <div className="text-xs text-gray-500 text-center mb-4">
                <p>필요 권한: {roles.join(', ')}</p>
                <p>현재 권한: {user?.roles?.join(', ') || '없음'}</p>
              </div>
              <button
                onClick={() => window.history.back()}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                이전 페이지로
              </button>
            </CardContent>
          </Card>
        </div>
      );
    }
  }

  // 인증되고 권한도 있음 - 컴포넌트 렌더링
  return <>{children}</>;
};

// 편의 컴포넌트들
export const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRoles="ADMIN">
    {children}
  </ProtectedRoute>
);

export const ManagerRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRoles={["ADMIN", "MANAGER"]}>
    {children}
  </ProtectedRoute>
);

export const TraderRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ProtectedRoute requiredRoles={["ADMIN", "MANAGER", "TRADER"]}>
    {children}
  </ProtectedRoute>
);

export default ProtectedRoute;