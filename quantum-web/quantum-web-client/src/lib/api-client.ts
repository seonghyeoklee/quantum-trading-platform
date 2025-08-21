import axios, { AxiosInstance, AxiosResponse, AxiosRequestConfig } from 'axios';

interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  user: {
    id: string;
    username: string;
    name: string;
    email: string;
    roles: string[];
  };
}

interface RefreshTokenResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
}

/**
 * API Client for Quantum Trading Platform
 * 
 * 백엔드 REST API와 통신하는 중앙화된 클라이언트
 * - HTTP 요청/응답 처리
 * - 에러 핸들링 및 재시도 로직
 * - JWT 인증 토큰 관리
 * - 요청/응답 인터셉터
 */
export class ApiClient {
  private client: AxiosInstance;
  private authToken: string | null = null;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080/api') {
    this.client = axios.create({
      baseURL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        
        // Add request ID for tracing
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error) => {
        // Don't handle 401 here - let AuthContext handle it
        console.error('API Error:', {
          status: error.response?.status,
          message: error.response?.data?.message || error.message,
          url: error.config?.url,
        });
        
        return Promise.reject(error);
      }
    );
  }

  // 인증 토큰 관리
  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  clearAuthToken() {
    this.authToken = null;
  }

  getAuthToken(): string | null {
    return this.authToken;
  }

  // 외부에서 응답 인터셉터 설정 (AuthContext용)
  setupResponseInterceptor(errorHandler: (error: any) => Promise<any>) {
    const interceptorId = this.client.interceptors.response.use(
      (response) => response,
      errorHandler
    );

    // 인터셉터 제거 함수 반환
    return () => {
      this.client.interceptors.response.eject(interceptorId);
    };
  }

  // 요청 재시도를 위한 메서드
  async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.client.request(config);
    return response.data;
  }

  private generateRequestId(): string {
    return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Generic request methods
  async get<T>(url: string, params?: object): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: object): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: object): Promise<T> {
    const response = await this.client.put(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete(url);
    return response.data;
  }

  // Authentication API methods
  async login(username: string, password: string): Promise<LoginResponse> {
    return this.post('/auth/login', { username, password });
  }

  async logout(): Promise<void> {
    return this.post('/auth/logout');
  }

  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    return this.post('/auth/refresh', { refreshToken });
  }

  async getCurrentUser(): Promise<any> {
    return this.get('/auth/me');
  }

  async getTokenInfo(): Promise<any> {
    return this.get('/auth/token/info');
  }

  // Chart API methods
  async getChartData(symbol: string, timeframe: string = '1d', limit: number = 100) {
    return this.get(`/charts/${symbol}`, { timeframe, limit });
  }

  async getTechnicalIndicators(symbol: string, timeframe: string = '1d') {
    return this.get(`/charts/${symbol}/indicators`, { timeframe });
  }

  // Portfolio API methods
  async getPortfolios(userId?: string, page: number = 0, size: number = 10) {
    return this.get('/portfolios', { userId, page, size });
  }

  async getPortfolio(portfolioId: string) {
    return this.get(`/portfolios/${portfolioId}`);
  }

  async getPositions(portfolioId: string, symbol?: string, minQuantity?: number) {
    return this.get(`/portfolios/${portfolioId}/positions`, { symbol, minQuantity });
  }

  async getPortfolioPnL(portfolioId: string, periodDays: number = 30, groupBy: string = 'daily') {
    return this.get(`/portfolios/${portfolioId}/pnl`, { periodDays, groupBy });
  }

  async getPortfolioPerformance(portfolioId: string, periodDays: number = 30, benchmark?: string) {
    return this.get(`/portfolios/${portfolioId}/performance`, { periodDays, benchmark });
  }

  async getRebalanceSuggestion(portfolioId: string, riskLevel: string = 'moderate') {
    return this.get(`/portfolios/${portfolioId}/rebalance`, { riskLevel });
  }

  // Trading API methods
  async getOrders(portfolioId: string, status?: string, page: number = 0, size: number = 10) {
    return this.get('/trading/orders', { portfolioId, status, page, size });
  }

  async getOrder(orderId: string) {
    return this.get(`/trading/orders/${orderId}`);
  }

  async createOrder(orderData: {
    portfolioId: string;
    symbol: string;
    side: 'BUY' | 'SELL';
    type: 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT';
    quantity: number;
    price?: number;
    stopPrice?: number;
  }) {
    return this.post('/trading/orders', orderData);
  }

  async cancelOrder(orderId: string) {
    return this.delete(`/trading/orders/${orderId}`);
  }

  async getTrades(portfolioId: string, symbol?: string, fromDate?: string, toDate?: string, 
                 page: number = 0, size: number = 10) {
    return this.get('/trading/trades', { 
      portfolioId, symbol, fromDate, toDate, page, size 
    });
  }

  // Market data API methods
  async getQuote(symbol: string) {
    return this.get(`/charts/quote/${symbol}`);
  }

  async searchSymbols(query: string, limit: number = 10) {
    return this.get('/charts/search', { query, limit });
  }
}

// Singleton instance
export const apiClient = new ApiClient();