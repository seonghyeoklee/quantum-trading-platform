'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiClient } from '@/lib/api-client';
import { storage } from '@/lib/utils';

interface User {
  id: string;
  username: string;
  name: string;
  email: string;
  roles: string[];
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);

  const isAuthenticated = !!user && !!token;

  // 토큰에서 사용자 정보 로드
  const loadUserFromToken = async (accessToken: string) => {
    try {
      // API client에 토큰 설정
      apiClient.setAuthToken(accessToken);
      
      // 사용자 정보 조회
      const userInfo = await apiClient.getCurrentUser();
      
      setUser(userInfo);
      setToken(accessToken);
      
      return userInfo;
    } catch (error) {
      console.error('Failed to load user from token:', error);
      // 토큰이 유효하지 않으면 제거
      clearAuth();
      throw error;
    }
  };

  // 인증 정보 초기화
  const clearAuth = () => {
    setUser(null);
    setToken(null);
    storage.remove('access_token');
    storage.remove('refresh_token');
    apiClient.clearAuthToken();
  };

  // 클라이언트 측 하이드레이션 확인
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  // 컴포넌트 마운트 시 저장된 토큰으로 자동 로그인 시도
  useEffect(() => {
    const initAuth = async () => {
      // 하이드레이션이 완료된 후에만 실행
      if (!isHydrated) return;
      
      try {
        const storedToken = storage.get<string>('access_token');
        
        if (storedToken) {
          await loadUserFromToken(storedToken);
        }
      } catch (error) {
        console.warn('Auto-login failed:', error);
        clearAuth();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [isHydrated]);

  // 로그인
  const login = async (username: string, password: string) => {
    try {
      setIsLoading(true);
      
      const response = await apiClient.login(username, password);
      
      // 토큰 저장
      storage.set('access_token', response.accessToken);
      storage.set('refresh_token', response.refreshToken);
      
      // 사용자 정보 설정
      setUser(response.user);
      setToken(response.accessToken);
      
      // API client에 토큰 설정
      apiClient.setAuthToken(response.accessToken);
      
      console.log('Login successful:', response.user.username);
      
    } catch (error) {
      clearAuth();
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 로그아웃
  const logout = async () => {
    try {
      // 서버에 로그아웃 요청
      if (token) {
        await apiClient.logout();
      }
    } catch (error) {
      console.warn('Logout request failed:', error);
    } finally {
      clearAuth();
      console.log('Logout completed');
    }
  };

  // 토큰 갱신
  const refreshToken = async () => {
    try {
      const storedRefreshToken = storage.get<string>('refresh_token');
      
      if (!storedRefreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await apiClient.refreshToken(storedRefreshToken);
      
      // 새 토큰 저장
      storage.set('access_token', response.accessToken);
      storage.set('refresh_token', response.refreshToken);
      
      // API client에 새 토큰 설정
      setToken(response.accessToken);
      apiClient.setAuthToken(response.accessToken);
      
      console.log('Token refreshed successfully');
      
    } catch (error) {
      console.error('Token refresh failed:', error);
      clearAuth();
      throw error;
    }
  };

  // 역할 확인
  const hasRole = (role: string): boolean => {
    if (!user || !user.roles) return false;
    
    return user.roles.some(userRole => 
      userRole === role || 
      userRole === `ROLE_${role}` ||
      userRole.replace('ROLE_', '') === role
    );
  };

  // 여러 역할 중 하나라도 있는지 확인
  const hasAnyRole = (roles: string[]): boolean => {
    return roles.some(role => hasRole(role));
  };

  // API 응답 인터셉터 설정 (토큰 만료 처리)
  useEffect(() => {
    const interceptor = apiClient.setupResponseInterceptor(
      async (error) => {
        if (error.response?.status === 401 && token) {
          try {
            // 토큰 갱신 시도
            await refreshToken();
            // 원래 요청 재시도
            return apiClient.request(error.config);
          } catch (refreshError) {
            // 갱신 실패 시 로그아웃
            clearAuth();
            throw refreshError;
          }
        }
        return Promise.reject(error);
      }
    );

    return () => {
      // 인터셉터 정리
      if (interceptor) {
        interceptor();
      }
    };
  }, [token]);

  const contextValue: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshToken,
    hasRole,
    hasAnyRole,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

// 편의 훅들

export const useRequireAuth = () => {
  const { isAuthenticated, isLoading } = useAuth();
  
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // 로그인 페이지로 리다이렉트
      window.location.href = '/login';
    }
  }, [isAuthenticated, isLoading]);
  
  return { isAuthenticated, isLoading };
};

export const useRequireRole = (requiredRoles: string | string[]) => {
  const { hasRole, hasAnyRole, isAuthenticated, isLoading } = useAuth();
  
  const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  const hasRequiredRole = hasAnyRole(roles);
  
  useEffect(() => {
    if (!isLoading && isAuthenticated && !hasRequiredRole) {
      // 권한 없음 페이지로 리다이렉트
      window.location.href = '/unauthorized';
    }
  }, [isAuthenticated, isLoading, hasRequiredRole]);
  
  return { hasRequiredRole, isLoading };
};