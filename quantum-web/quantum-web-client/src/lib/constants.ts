// API URL 상수
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:10101';
export const KIWOOM_ADAPTER_URL = process.env.KIWOOM_ADAPTER_URL || 'http://localhost:10201';

// API 엔드포인트들
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    ME: '/api/v1/auth/me',
    REFRESH: '/api/v1/auth/refresh',
    TWO_FACTOR: {
      STATUS: '/api/v1/auth/2fa/status',
      SETUP: '/api/v1/auth/2fa/setup',
      VERIFY: '/api/v1/auth/2fa/verify',
      VERIFY_LOGIN: '/api/v1/auth/2fa/verify-login',
      DISABLE: '/api/v1/auth/2fa/disable',
    }
  }
} as const;