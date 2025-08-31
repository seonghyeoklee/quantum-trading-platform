'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBaseUrl } from '@/lib/api-config';

interface User {
  id: string;
  username: string;
  email: string;
  roles: string[];
  lastLoginAt: string;
  preferences?: {
    language: string;
    timezone: string;
    theme: string;
  };
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isAuthenticated = !!user;

  useEffect(() => {
    // 페이지 로드 시 기존 인증 상태 확인
    checkExistingAuth();
  }, []);

  const checkExistingAuth = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setIsLoading(false);
        return;
      }

      // 캐시된 사용자 정보가 있으면 먼저 설정
      const cachedUser = localStorage.getItem('user');
      if (cachedUser) {
        try {
          const userData = JSON.parse(cachedUser);
          console.log('Loading cached user data:', userData);
          setUser(userData);
        } catch (parseError) {
          console.warn('Failed to parse cached user data:', parseError);
        }
      }

      // 최신 사용자 정보로 업데이트
      await refreshUser();
    } catch (error) {
      console.error('Failed to check existing auth:', error);
      clearAuth();
    }
  };

  const login = async (username: string, password: string) => {
    try {
      const apiBaseUrl = getApiBaseUrl();
      console.log('🔐 [AuthContext] Login attempt to:', `${apiBaseUrl}/api/v1/auth/login`);
      const response = await fetch(`${apiBaseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || '로그인에 실패했습니다.');
      }

      const data = await response.json();
      
      // JWT 토큰 저장
      if (data.accessToken) {
        localStorage.setItem('accessToken', data.accessToken);
        localStorage.setItem('refreshToken', data.refreshToken);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        console.log('Setting user from login response:', data.user);
        // 사용자 정보 설정 및 로딩 상태 해제
        setUser(data.user);
        setIsLoading(false);

        // 페이지 이동
        const returnUrl = localStorage.getItem('returnUrl') || '/';
        localStorage.removeItem('returnUrl');
        router.push(returnUrl);
      }
    } catch (error) {
      console.error('Login failed:', error);
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      if (token) {
        // 백엔드에 로그아웃 요청
        const apiBaseUrl = getApiBaseUrl();
        console.log('🚪 [AuthContext] Logout attempt to:', `${apiBaseUrl}/api/v1/auth/logout`);
        await fetch(`${apiBaseUrl}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });
      }
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      // 클라이언트 상태 정리
      clearAuth();
      router.push('/login');
    }
  };

  const refreshUser = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        throw new Error('No access token found');
      }

      console.log('Fetching user data from /api/v1/auth/me...');

      const apiBaseUrl = getApiBaseUrl();
      console.log('👤 [AuthContext] Fetching user info from:', `${apiBaseUrl}/api/v1/auth/me`);
      const response = await fetch(`${apiBaseUrl}/api/v1/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 401) {
          // 토큰 만료, 리프레시 시도
          await tryRefreshToken();
          return;
        }
        throw new Error('Failed to fetch user data');
      }

      const userData = await response.json();
      console.log('User data fetched successfully:', userData);
      console.log('Setting user state and isLoading to false...');
      setUser(userData);
      setIsLoading(false);
      console.log('User state updated, should trigger re-render');
    } catch (error) {
      console.error('Failed to refresh user:', error);
      clearAuth();
      throw error;
    }
  };

  const tryRefreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!refreshToken) {
        throw new Error('No refresh token found');
      }

      const apiBaseUrl = getApiBaseUrl();
      console.log('🔄 [AuthContext] Token refresh attempt to:', `${apiBaseUrl}/api/v1/auth/refresh`);
      const response = await fetch(`${apiBaseUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);

      // 사용자 정보 다시 가져오기
      await refreshUser();
    } catch (error) {
      console.error('Token refresh failed:', error);
      clearAuth();
      throw error;
    }
  };

  const clearAuth = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    setUser(null);
    setIsLoading(false);
  };

  const hasRole = (role: string): boolean => {
    return user?.roles?.includes(role) || false;
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return roles.some(role => hasRole(role));
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
    hasRole,
    hasAnyRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}