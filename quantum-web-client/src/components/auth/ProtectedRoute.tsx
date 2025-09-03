'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
  requireKISSetup?: boolean; // KIS 설정 필수 여부
}

export default function ProtectedRoute({ children, requiredRoles = [], requireKISSetup = false }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated, isKISSetupRequired, hasKISAccount } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    checkAuth();
  }, [isAuthenticated, isKISSetupRequired, hasKISAccount, pathname]);

  const checkAuth = () => {
    // 로딩 중이면 대기
    if (isLoading) return;

    // 인증되지 않았으면 로그인 페이지로
    if (!isAuthenticated) {
      redirectToLogin();
      return;
    }

    // 권한 확인
    if (requiredRoles.length > 0 && user) {
      const hasRequiredRole = requiredRoles.some(role => 
        user.roles?.includes(role)
      );
      
      if (!hasRequiredRole) {
        router.push('/unauthorized');
        return;
      }
    }

    // KIS 설정이 필요한 페이지인데 설정이 안되어 있으면
    if (requireKISSetup && !hasKISAccount) {
      router.push('/kis-setup');
      return;
    }

    // KIS 설정이 필요한 상태면 설정 페이지로 (단, 로그인 직후가 아닌 경우에만)
    // 로그인 직후에는 AuthContext.login()에서 이미 라우팅을 처리했으므로 중복 리다이렉트 방지
    if (isKISSetupRequired && pathname !== '/kis-setup' && pathname !== '/login') {
      // 세션 스토리지로 로그인 직후인지 확인 (로그인 후 첫 페이지 로드에서는 리다이렉트 하지 않음)
      const isLoginRedirect = sessionStorage.getItem('loginRedirect');
      if (isLoginRedirect) {
        sessionStorage.removeItem('loginRedirect');
        return; // 로그인 직후이므로 리다이렉트하지 않음
      }
      
      console.log('🔄 KIS 설정이 필요하여 설정 페이지로 리다이렉트');
      router.push('/kis-setup');
      return;
    }
  };

  const redirectToLogin = () => {
    const returnUrl = pathname !== '/login' ? pathname : '/';
    localStorage.setItem('returnUrl', returnUrl);
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

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}