import { getApiBaseUrl } from './api-config';

interface ApiRequestOptions {
  method?: string;
  headers?: Record<string, string>;
  body?: unknown;
  requireAuth?: boolean;
}

interface ApiResponse<T = unknown> {
  data?: T;
  message?: string;
  status: number;
  ok: boolean;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class ApiClient {
  private baseUrl: string;
  private onTokenExpired?: () => void;
  private refreshPromise?: Promise<void>;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || getApiBaseUrl();
  }

  setTokenExpiredHandler(handler: () => void) {
    this.onTokenExpired = handler;
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('accessToken');
  }

  private async tryRefreshToken(): Promise<void> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    
    try {
      await this.refreshPromise;
    } finally {
      this.refreshPromise = undefined;
    }
  }

  private async performTokenRefresh(): Promise<void> {
    const refreshToken = localStorage.getItem('refreshToken');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ refreshToken })
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      if (data.accessToken) {
        localStorage.setItem('accessToken', data.accessToken);
        if (data.refreshToken) {
          localStorage.setItem('refreshToken', data.refreshToken);
        }
        if (data.user) {
          localStorage.setItem('user', JSON.stringify(data.user));
        }
      } else {
        throw new Error('No new token received');
      }
    } catch (error) {
      // 토큰 리프레시 실패 시 기존 토큰 제거
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      throw error;
    }
  }

  private async makeRequest<T>(
    endpoint: string,
    options: ApiRequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const { method = 'GET', headers = {}, body, requireAuth = true } = options;

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    // 인증이 필요한 경우 토큰 추가
    if (requireAuth) {
      const token = this.getToken();
      if (token) {
        requestHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const requestConfig: RequestInit = {
      method,
      headers: requestHeaders,
      credentials: 'include',
    };

    if (body && method !== 'GET') {
      requestConfig.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, requestConfig);
      
      // 토큰 만료 시 자동 리프레시 시도
      if (response.status === 401 && requireAuth) {
        try {
          // 토큰 리프레시 시도
          await this.tryRefreshToken();
          
          // 새로운 토큰으로 요청 재시도
          const newToken = this.getToken();
          if (newToken) {
            requestHeaders['Authorization'] = `Bearer ${newToken}`;
            const retryConfig = { ...requestConfig, headers: requestHeaders };
            const retryResponse = await fetch(`${this.baseUrl}${endpoint}`, retryConfig);
            
            let retryData: unknown;
            const retryContentType = retryResponse.headers.get('content-type');
            
            if (retryContentType && retryContentType.includes('application/json')) {
              retryData = await retryResponse.json();
            } else {
              retryData = await retryResponse.text();
            }

            if (!retryResponse.ok) {
              const errorMessage = (retryData as { message?: string })?.message || `HTTP error! status: ${retryResponse.status}`;
              throw new ApiError(errorMessage, retryResponse.status, retryData);
            }

            return {
              data: retryData,
              status: retryResponse.status,
              ok: retryResponse.ok,
              message: (retryData as { message?: string })?.message,
            };
          }
        } catch (refreshError) {
          // 토큰 리프레시 실패 시 기존 핸들러 호출
          if (this.onTokenExpired) {
            this.onTokenExpired();
          }
          throw new ApiError('Token refresh failed', 401, refreshError);
        }
      }

      let data: unknown;
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMessage = (data as { message?: string })?.message || `HTTP error! status: ${response.status}`;
        throw new ApiError(errorMessage, response.status, data);
      }

      return {
        data,
        status: response.status,
        ok: response.ok,
        message: (data as { message?: string })?.message,
      };
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // 네트워크 에러 등
      throw new ApiError(
        error instanceof Error ? error.message : 'Unknown error occurred',
        0,
        error
      );
    }
  }

  // GET 요청
  async get<T>(endpoint: string, requireAuth = true): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'GET', requireAuth });
  }

  // POST 요청
  async post<T>(
    endpoint: string,
    body?: unknown,
    requireAuth = true
  ): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { 
      method: 'POST', 
      body, 
      requireAuth 
    });
  }

  // PUT 요청
  async put<T>(
    endpoint: string,
    body?: unknown,
    requireAuth = true
  ): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { 
      method: 'PUT', 
      body, 
      requireAuth 
    });
  }

  // DELETE 요청
  async delete<T>(endpoint: string, requireAuth = true): Promise<ApiResponse<T>> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE', requireAuth });
  }
}

// 기본 API 클라이언트 인스턴스
export const apiClient = new ApiClient();

export { ApiError };