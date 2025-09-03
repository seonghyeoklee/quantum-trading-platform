'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, ApiError } from '@/lib/api';

interface User {
  id: number;
  email: string;
  name: string;
  last_login_at?: string;
}


interface AuthContextType {
  // 기존 JWT 관련
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  
  hasKISAccount: boolean;
  isKISSetupRequired: boolean;
  isKISSetupCompleted: boolean;
  setupKISAccount: (appKey: string, appSecret: string, accountNumber: string, accountAlias: string, environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  checkKISAccountExists: (environment?: 'LIVE' | 'SANDBOX') => Promise<boolean>;
  skipKISSetup: () => void;
  forceKISSetup: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasKISAccount, setHasKISAccount] = useState(false);
  const [isKISSetupRequired, setIsKISSetupRequired] = useState(false);
  const [isKISSetupCompleted, setIsKISSetupCompleted] = useState(false);
  const router = useRouter();

  const isAuthenticated = !!user;

  useEffect(() => {
    // API 클라이언트에 토큰 만료 핸들러 설정
    apiClient.setTokenExpiredHandler(() => {
      tryRefreshToken().catch(() => {
        clearAuth();
        router.push('/login');
      });
    });

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
          setUser(userData);
        } catch (parseError) {
          console.warn('Failed to parse cached user data:', parseError);
        }
      }

      // KIS 계정 설정 상태는 서버에서 확인
      // 클라이언트에서는 토큰 관리하지 않음

      // 최신 사용자 정보로 업데이트
      await refreshUser();
      
      // KIS 설정 상태 확인
      await checkKISSetupStatus();
    } catch (error) {
      console.error('Failed to check existing auth:', error);
      clearAuth();
    }
  };

  const login = async (email: string, password: string) => {
    try {
      // 1. JWT 로그인 (기존)
      const response = await apiClient.post('/api/v1/auth/login', 
        { email, password }, 
        false // 로그인은 인증이 필요하지 않음
      );

      const data = response.data;
      
      // JWT 토큰 저장
      if (data.accessToken) {
        localStorage.setItem('accessToken', data.accessToken);
        localStorage.setItem('refreshToken', data.refreshToken);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        setUser(data.user);
        
        // 2. KIS 설정 상태 확인 (직접 확인하여 즉시 라우팅)
        const setupSkipped = localStorage.getItem('kisSetupSkipped');
        const sandboxExists = await checkKISAccountExists('SANDBOX');
        const liveExists = await checkKISAccountExists('LIVE');
        const kisAccountExists = sandboxExists || liveExists;
        
        // 상태 업데이트
        setHasKISAccount(kisAccountExists);
        setIsKISSetupCompleted(kisAccountExists);
        
        const needsKISSetup = !kisAccountExists && !setupSkipped;
        setIsKISSetupRequired(needsKISSetup);
        
        // KIS 토큰은 서버에서 관리됨
        console.log('KIS 계정 설정은 서버에서 처리됩니다.');
        
        setIsLoading(false);

        console.log('🚀 로그인 후 라우팅 결정:', {
          kisAccountExists,
          needsKISSetup,
          setupSkipped: !!setupSkipped
        });

        // 4. KIS 설정이 필요한 경우 설정 페이지로, 아니면 원래 페이지로
        // 로그인 직후라는 플래그 설정 (ProtectedRoute에서 중복 리다이렉트 방지용)
        sessionStorage.setItem('loginRedirect', 'true');
        
        if (needsKISSetup) {
          console.log('📝 KIS 설정 페이지로 이동');
          router.push('/kis-setup');
        } else {
          const returnUrl = localStorage.getItem('returnUrl') || '/';
          localStorage.removeItem('returnUrl');
          console.log(`🏠 메인 화면으로 이동: ${returnUrl}`);
          router.push(returnUrl);
        }
      }
    } catch (error) {
      console.error('Login failed:', error);
      setIsLoading(false);
      if (error instanceof ApiError) {
        throw new Error(error.message);
      }
      throw error;
    }
  };

  const logout = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      
      if (token) {
        await apiClient.post('/api/v1/auth/logout', {}, true);
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

      const response = await apiClient.get('/api/v1/auth/me', true);
      const userData = response.data;
      
      // 사용자 정보를 캐시에 저장
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      
      if (error instanceof ApiError && error.status === 401) {
        // 토큰 만료, 리프레시 시도
        try {
          await tryRefreshToken();
          return;
        } catch (refreshError) {
          console.error('Token refresh failed, redirecting to login');
          clearAuth();
          return;
        }
      }
      
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

      const response = await apiClient.post('/api/v1/auth/refresh', 
        { refreshToken }, 
        false // 리프레시는 인증이 필요하지 않음
      );

      const data = response.data;
      
      // 새로운 토큰 저장
      localStorage.setItem('accessToken', data.accessToken);
      if (data.refreshToken) {
        localStorage.setItem('refreshToken', data.refreshToken);
      }

      // 사용자 정보 업데이트
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
        setUser(data.user);
      }

      setIsLoading(false);
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
    // KIS 관련 상태 초기화 (서버 중심 관리)
    localStorage.removeItem('kisSetupSkipped');
    setUser(null);
    setHasKISAccount(false);
    setIsKISSetupRequired(false);
    setIsKISSetupCompleted(false);
    setIsLoading(false);
  };



  // KIS 계정 설정
  const setupKISAccount = async (appKey: string, appSecret: string, accountNumber: string, accountAlias: string, environment: 'LIVE' | 'SANDBOX') => {
    try {
      const response = await apiClient.post('/api/v1/kis-accounts/setup', {
        appKey,
        appSecret,
        accountNumber,
        accountAlias,
        environment
      }, true);

      if (response.data?.success) {
        // 설정 완료 상태 업데이트
        setHasKISAccount(true);
        setIsKISSetupCompleted(true);
        setIsKISSetupRequired(false);
        
        // KIS 계정 설정은 서버에서 처리
        
        // 메인 페이지로 이동
        const returnUrl = localStorage.getItem('returnUrl') || '/';
        localStorage.removeItem('returnUrl');
        router.push(returnUrl);
      }
    } catch (error) {
      console.error('KIS account setup failed:', error);
      throw error;
    }
  };



  // KIS 계정 존재 여부 확인
  const checkKISAccountExists = async (environment: 'LIVE' | 'SANDBOX' = 'SANDBOX'): Promise<boolean> => {
    try {
      const response = await apiClient.get(`/api/v1/kis-accounts/me/exists?environment=${environment}`, true);
      
      return response.data?.hasAccount || false;
    } catch (error) {
      console.error(`KIS account exists check failed for ${environment}:`, error);
      return false;
    }
  };

  // KIS 설정 상태 확인
  const checkKISSetupStatus = async () => {
    try {
      // KIS 설정을 건너뛰기로 했는지 확인
      const setupSkipped = localStorage.getItem('kisSetupSkipped');
      
      // 두 환경 모두에서 KIS 계정 존재 여부 확인
      const sandboxExists = await checkKISAccountExists('SANDBOX');
      const liveExists = await checkKISAccountExists('LIVE');
      
      // 하나라도 설정되어 있으면 계정이 있다고 판단
      const exists = sandboxExists || liveExists;
      
      setHasKISAccount(exists);
      setIsKISSetupCompleted(exists);
      
      // KIS 계정이 없고 설정을 건너뛰지 않았다면 설정 필요
      if (!exists && !setupSkipped) {
        setIsKISSetupRequired(true);
      } else {
        setIsKISSetupRequired(false);
      }
    } catch (error) {
      console.error('Failed to check KIS setup status:', error);
      setIsKISSetupRequired(false);
      setIsKISSetupCompleted(false);
    }
  };

  // KIS 설정 건너뛰기
  const skipKISSetup = () => {
    localStorage.setItem('kisSetupSkipped', 'true');
    setIsKISSetupRequired(false);
    
    // 원래 가려던 페이지로 이동
    const returnUrl = localStorage.getItem('returnUrl') || '/';
    localStorage.removeItem('returnUrl');
    router.push(returnUrl);
  };

  // KIS 설정 강제 시작
  const forceKISSetup = () => {
    localStorage.removeItem('kisSetupSkipped');
    setIsKISSetupRequired(true);
    router.push('/kis-setup');
  };

  const value: AuthContextType = {
    // 기존 JWT 관련
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    refreshUser,
    
    hasKISAccount,
    isKISSetupRequired,
    isKISSetupCompleted,
    setupKISAccount,
    checkKISAccountExists,
    skipKISSetup,
    forceKISSetup,
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