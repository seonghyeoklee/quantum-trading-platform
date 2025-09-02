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

interface KISTokenInfo {
  token: string;
  environment: 'LIVE' | 'SANDBOX';
  expiresAt: string;
  issuedAt: string;
  appKey: string;
  appSecret: string; // 암호화 저장
}

interface AuthContextType {
  // 기존 JWT 관련
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  
  // 새로운 KIS 토큰 관련
  kisTokens: {
    live?: KISTokenInfo;
    sandbox?: KISTokenInfo;
  };
  hasKISAccount: boolean;
  isKISSetupRequired: boolean;
  isKISSetupCompleted: boolean;
  setupKISAccount: (appKey: string, appSecret: string, accountNumber: string, accountAlias: string, environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  checkKISAccountExists: (environment?: 'LIVE' | 'SANDBOX') => Promise<boolean>;
  refreshKISToken: (environment: 'LIVE' | 'SANDBOX') => Promise<void>;
  getActiveKISToken: () => string | null;
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
  const [kisTokens, setKisTokens] = useState<{ live?: KISTokenInfo; sandbox?: KISTokenInfo }>({});
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

      // 캐시된 KIS 토큰 정보 복원
      const loadKISTokensFromStorage = () => {
        const loadedTokens: { live?: KISTokenInfo; sandbox?: KISTokenInfo } = {};
        
        try {
          const liveToken = localStorage.getItem('kisToken_LIVE');
          if (liveToken) {
            loadedTokens.live = JSON.parse(liveToken);
          }
          
          const sandboxToken = localStorage.getItem('kisToken_SANDBOX');
          if (sandboxToken) {
            loadedTokens.sandbox = JSON.parse(sandboxToken);
          }
          
          setKisTokens(loadedTokens);
          setHasKISAccount(Object.keys(loadedTokens).length > 0);
        } catch (parseError) {
          console.warn('Failed to parse cached KIS tokens:', parseError);
        }
      };

      loadKISTokensFromStorage();

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
        
        // 2. KIS 설정 상태 확인
        await checkKISSetupStatus();
        
        // 3. KIS 계정이 설정되어 있다면 토큰 확인 및 발급
        if (hasKISAccount) {
          await checkAndIssueKISTokens();
        }
        
        setIsLoading(false);

        // 4. KIS 설정이 필요한 경우 설정 페이지로, 아니면 원래 페이지로
        if (isKISSetupRequired) {
          router.push('/kis-setup');
        } else {
          const returnUrl = localStorage.getItem('returnUrl') || '/';
          localStorage.removeItem('returnUrl');
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
    // KIS 토큰도 제거
    localStorage.removeItem('kisToken_LIVE');
    localStorage.removeItem('kisToken_SANDBOX');
    localStorage.removeItem('kisSetupSkipped');
    setUser(null);
    setKisTokens({});
    setHasKISAccount(false);
    setIsKISSetupRequired(false);
    setIsKISSetupCompleted(false);
    setIsLoading(false);
  };

  // KIS 토큰 확인 및 발급 로직
  const checkAndIssueKISTokens = async () => {
    try {
      // 3-1. 사용자 KIS 계정 정보 확인
      const kisAccount = await apiClient.get('/api/v1/kis-accounts/me', true);
      
      if (kisAccount.data) {
        
        // 3-2. 각 환경별로 토큰 확인 및 발급
        const environments: ('LIVE' | 'SANDBOX')[] = ['LIVE', 'SANDBOX'];
        const newTokens: { live?: KISTokenInfo; sandbox?: KISTokenInfo } = {};
        
        for (const env of environments) {
          const envKey = env.toLowerCase() as 'live' | 'sandbox';
          if (kisAccount.data[envKey]) {
            const tokenInfo = await checkAndRefreshKISToken(env, kisAccount.data[envKey]);
            if (tokenInfo) {
              // 3-3. 클라이언트에 토큰 저장
              newTokens[envKey] = tokenInfo;
            }
          }
        }
        
        setKisTokens(newTokens);
        setHasKISAccount(true);
      } else {
        setHasKISAccount(false);
      }
    } catch (error) {
      console.error('KIS token check failed:', error);
      setHasKISAccount(false);
    }
  };

  // KIS 토큰 검증 및 발급
  const checkAndRefreshKISToken = async (environment: 'LIVE' | 'SANDBOX', accountInfo: any): Promise<KISTokenInfo | null> => {
    try {
      // 4-1. 기존 토큰 확인
      const existingToken = localStorage.getItem(`kisToken_${environment}`);
      
      if (existingToken) {
        const tokenData = JSON.parse(existingToken);
        const now = new Date();
        const expiryTime = new Date(tokenData.expiresAt);
        
        // 4-2. 토큰이 유효하면 그대로 사용
        if (now < expiryTime) {
          return tokenData;
        }
      }
      
      // 4-3. 토큰이 없거나 만료되면 새로 발급
      const tokenData = await apiClient.post('/api/v1/kis-accounts/me/token', {
        environment: environment
      }, true);
      
      if (tokenData.data?.success) {
        const newTokenInfo: KISTokenInfo = {
          token: tokenData.data.token,
          environment: environment,
          expiresAt: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(), // 6시간
          issuedAt: new Date().toISOString(),
          appKey: accountInfo.appKey,
          appSecret: accountInfo.appSecret // 이미 서버에서 암호화됨
        };
        
        // 4-4. localStorage에 저장
        localStorage.setItem(`kisToken_${environment}`, JSON.stringify(newTokenInfo));
        
        return newTokenInfo;
      }
    } catch (error) {
      console.error(`Failed to refresh KIS token for ${environment}:`, error);
      return null;
    }
    
    return null;
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
        
        // 설정 후 토큰 발급 시도
        await checkAndIssueKISTokens();
        
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

  // KIS 토큰 갱신
  const refreshKISToken = async (environment: 'LIVE' | 'SANDBOX') => {
    try {
      const tokenData = await apiClient.post('/api/v1/kis-accounts/me/token', {
        environment: environment
      }, true);
      
      if (tokenData.data?.success) {
        const newTokenInfo: KISTokenInfo = {
          token: tokenData.data.token,
          environment: environment,
          expiresAt: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(),
          issuedAt: new Date().toISOString(),
          appKey: kisTokens[environment.toLowerCase() as 'live' | 'sandbox']?.appKey || '',
          appSecret: kisTokens[environment.toLowerCase() as 'live' | 'sandbox']?.appSecret || ''
        };
        
        localStorage.setItem(`kisToken_${environment}`, JSON.stringify(newTokenInfo));
        
        setKisTokens(prev => ({
          ...prev,
          [environment.toLowerCase()]: newTokenInfo
        }));
      }
    } catch (error) {
      console.error(`Failed to refresh KIS token for ${environment}:`, error);
      throw error;
    }
  };

  // 활성 KIS 토큰 반환 (기본적으로 SANDBOX 우선)
  const getActiveKISToken = (): string | null => {
    // SANDBOX 토큰을 우선으로 반환 (개발/테스트 환경)
    if (kisTokens.sandbox?.token) {
      const now = new Date();
      const expiryTime = new Date(kisTokens.sandbox.expiresAt);
      if (now < expiryTime) {
        return kisTokens.sandbox.token;
      }
    }
    
    // SANDBOX가 없거나 만료되면 LIVE 토큰 확인
    if (kisTokens.live?.token) {
      const now = new Date();
      const expiryTime = new Date(kisTokens.live.expiresAt);
      if (now < expiryTime) {
        return kisTokens.live.token;
      }
    }
    
    return null;
  };

  // KIS 계정 존재 여부 확인
  const checkKISAccountExists = async (environment: 'LIVE' | 'SANDBOX' = 'SANDBOX'): Promise<boolean> => {
    try {
      const response = await apiClient.get(`/api/v1/kis-accounts/me/exists?environment=${environment}`, true);
      
      return response.data?.exists || false;
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
    
    // 새로운 KIS 토큰 관련
    kisTokens,
    hasKISAccount,
    isKISSetupRequired,
    isKISSetupCompleted,
    setupKISAccount,
    checkKISAccountExists,
    refreshKISToken,
    getActiveKISToken,
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