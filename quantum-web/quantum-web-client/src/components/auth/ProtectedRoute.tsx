'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';

interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  lastLoginAt: string;
}

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export default function ProtectedRoute({ children, requiredRoles = [] }: ProtectedRouteProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    checkAuth();
  }, [pathname]);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        redirectToLogin();
        return;
      }

      // 백엔드에서 사용자 정보 조회
      const response = await fetch('http://localhost:8080/api/v1/auth/me', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        // 토큰이 유효하지 않은 경우
        if (response.status === 401) {
          await tryRefreshToken();
          return;
        }
        throw new Error('인증에 실패했습니다.');
      }

      const userData = await response.json();
      setUser(userData);

      // 권한 확인
      if (requiredRoles.length > 0) {
        const hasRequiredRole = requiredRoles.some(role => 
          userData.roles?.includes(role)
        );
        
        if (!hasRequiredRole) {
          router.push('/unauthorized');
          return;
        }
      }

      setIsLoading(false);
    } catch (error) {
      console.error('Authentication check failed:', error);
      redirectToLogin();
    }
  };

  const tryRefreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!refreshToken) {
        redirectToLogin();
        return;
      }

      const response = await fetch('http://localhost:8080/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ refreshToken }),
      });

      if (!response.ok) {
        redirectToLogin();
        return;
      }

      const data = await response.json();
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);

      // 다시 인증 확인
      await checkAuth();
    } catch (error) {
      console.error('Token refresh failed:', error);
      redirectToLogin();
    }
  };

  const redirectToLogin = () => {
    // 로그인 후 돌아올 페이지 저장
    const returnUrl = pathname !== '/login' ? pathname : '/';
    localStorage.setItem('returnUrl', returnUrl);
    
    // 토큰 정리
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">인증 확인 중...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // 리디렉트 중
  }

  return <>{children}</>;
}