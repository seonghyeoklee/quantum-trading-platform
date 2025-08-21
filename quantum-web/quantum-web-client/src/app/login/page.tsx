'use client';

import { LoginForm } from '@/components/auth/LoginForm';
import { useAuth } from '@/contexts/AuthContext';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      // 이미 로그인된 경우 대시보드로 리다이렉트
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // 로딩 중이거나 로그인된 상태라면 로딩 표시
  if (isLoading || isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">
            {isAuthenticated ? '대시보드로 이동 중...' : '인증 상태 확인 중...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <LoginForm 
      onSuccess={() => router.push('/dashboard')}
    />
  );
}