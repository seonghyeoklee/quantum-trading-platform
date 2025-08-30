import { getApiBaseUrl } from './api-config';

interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

class ApiClient {
  private get baseURL() {
    return `${getApiBaseUrl()}/api/v1`;
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('accessToken');

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      credentials: 'include',
      ...options,
    };

    try {
      const response = await fetch(url, config);

      // 401 에러 시 자동 토큰 갱신 시도
      if (response.status === 401 && token) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // 토큰 갱신 성공 시 원래 요청 재시도
          const newToken = localStorage.getItem('accessToken');
          if (newToken) {
            config.headers = {
              ...config.headers,
              Authorization: `Bearer ${newToken}`,
            };
            const retryResponse = await fetch(url, config);
            if (!retryResponse.ok) {
              throw new Error(`HTTP error! status: ${retryResponse.status}`);
            }
            return await retryResponse.json();
          }
        }
        // 토큰 갱신 실패 시 로그인 페이지로 리다이렉트
        this.handleAuthError();
        throw new Error('Authentication failed');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  private async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) return false;

      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ refreshToken }),
      });

      if (!response.ok) return false;

      const data = await response.json();
      localStorage.setItem('accessToken', data.accessToken);
      localStorage.setItem('refreshToken', data.refreshToken);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  private handleAuthError(): void {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    
    // 현재 페이지 URL 저장
    const returnUrl = window.location.pathname;
    if (returnUrl !== '/login') {
      localStorage.setItem('returnUrl', returnUrl);
    }
    
    // 로그인 페이지로 리다이렉트
    window.location.href = '/login';
  }

  // GET 요청
  async get<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  // POST 요청
  async post<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // PUT 요청
  async put<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // DELETE 요청
  async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // PATCH 요청
  async patch<T = any>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  // 인증 관련 API
  auth = {
    login: (credentials: { username: string; password: string }) =>
      this.post('/auth/login', credentials),
    
    logout: () =>
      this.post('/auth/logout'),
    
    getMe: () =>
      this.get('/auth/me'),
    
    refresh: (refreshToken: string) =>
      this.post('/auth/refresh', { refreshToken }),
  };

  // 거래 관련 API
  trading = {
    getOrders: (params?: any) =>
      this.get(`/trading/orders${params ? `?${new URLSearchParams(params)}` : ''}`),
    
    createOrder: (orderData: any) =>
      this.post('/trading/orders', orderData),
    
    cancelOrder: (orderId: string) =>
      this.delete(`/trading/orders/${orderId}`),
    
    getOrderHistory: (params?: any) =>
      this.get(`/trading/orders/history${params ? `?${new URLSearchParams(params)}` : ''}`),
  };

  // 포트폴리오 관련 API
  portfolio = {
    getPortfolio: () =>
      this.get('/portfolio'),
    
    getPositions: () =>
      this.get('/portfolio/positions'),
    
    getPerformance: (period?: string) =>
      this.get(`/portfolio/performance${period ? `?period=${period}` : ''}`),
  };

  // 차트 관련 API
  chart = {
    getChartData: (symbol: string, params?: any) =>
      this.get(`/chart/${symbol}${params ? `?${new URLSearchParams(params)}` : ''}`),
    
    getMarketData: () =>
      this.get('/chart/market-data'),
  };

  // 관리자 관련 API (ADMIN 권한 필요)
  admin = {
    // 사용자 관리
    getUsers: (params?: any) =>
      this.get(`/admin/users${params ? `?${new URLSearchParams(params)}` : ''}`),
    
    getUserById: (userId: string) =>
      this.get(`/admin/users/${userId}`),
    
    updateUser: (userId: string, userData: any) =>
      this.put(`/admin/users/${userId}`, userData),
    
    deleteUser: (userId: string) =>
      this.delete(`/admin/users/${userId}`),
    
    searchUsers: (searchTerm: string, params?: any) =>
      this.get(`/admin/users/search${params ? `?searchTerm=${searchTerm}&${new URLSearchParams(params)}` : `?searchTerm=${searchTerm}`}`),
    
    getUsersByStatus: (status: string, params?: any) =>
      this.get(`/admin/users/status/${status}${params ? `?${new URLSearchParams(params)}` : ''}`),
    
    getUsersByRole: (role: string, params?: any) =>
      this.get(`/admin/users/role/${role}${params ? `?${new URLSearchParams(params)}` : ''}`),
    
    // 보안 관리
    getLoginHistory: (params?: any) =>
      this.get(`/auth/login-history${params ? `?${new URLSearchParams(params)}` : ''}`),
    
    getUserLoginHistory: (userId: string, params?: any) =>
      this.get(`/auth/login-history/user/${userId}${params ? `?${new URLSearchParams(params)}` : ''}`),
    
    getLoginStats: () =>
      this.get('/auth/login-stats'),
    
    unlockAccount: (userId: string, reason?: string) =>
      this.post('/auth/unlock-account', { userId, reason }),
    
    // 시스템 설정
    getSystemSettings: () =>
      this.get('/admin/settings'),
    
    updateSystemSettings: (settings: any) =>
      this.put('/admin/settings', settings),
  };
}

// 싱글톤 인스턴스
const apiClient = new ApiClient();

export default apiClient;

// 타입 정의
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: {
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
  };
}

export interface User {
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

export interface Order {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
  quantity: number;
  price?: number;
  stopPrice?: number;
  status: 'PENDING' | 'SUBMITTED' | 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELLED' | 'REJECTED';
  createdAt: string;
  updatedAt: string;
}

export interface Portfolio {
  id: string;
  totalValue: number;
  cashBalance: number;
  positions: Position[];
  performance: {
    totalReturn: number;
    totalReturnPercent: number;
    todayReturn: number;
    todayReturnPercent: number;
  };
}

export interface Position {
  symbol: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  marketValue: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
}

export interface ChartData {
  symbol: string;
  data: {
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }[];
}