/**
 * API 설정 및 동적 호스트 감지 유틸리티
 * Tailscale VPN 환경에서 외부 접근을 위한 동적 URL 생성
 */

// 환경별 기본 포트 설정
const DEFAULT_PORTS = {
  WEB_API: 10101,
  KIWOOM_ADAPTER: 10201,
} as const;

// Tailscale IP (환경변수로 설정 가능)
const TAILSCALE_IP = process.env.NEXT_PUBLIC_TAILSCALE_IP || '100.68.90.21';

/**
 * 브라우저에서 현재 호스트 감지
 */
function getCurrentHost(): string {
  // 서버사이드 렌더링 중일 때는 기본값 반환
  if (typeof window === 'undefined') {
    return 'localhost';
  }

  const hostname = window.location.hostname;
  
  // Tailscale IP로 접근하고 있는 경우
  if (hostname === TAILSCALE_IP) {
    return TAILSCALE_IP;
  }
  
  // localhost나 127.0.0.1이 아닌 경우 (예: 다른 네트워크 IP)
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return hostname;
  }
  
  return 'localhost';
}

/**
 * API 베이스 URL 생성
 */
export function getApiBaseUrl(): string {
  // 환경변수 우선 사용
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  const host = getCurrentHost();
  const port = DEFAULT_PORTS.WEB_API;
  const protocol = host === 'localhost' || host === '127.0.0.1' ? 'http' : 'http';
  
  return `${protocol}://${host}:${port}`;
}

/**
 * Kiwoom Adapter URL 생성
 */
export function getKiwoomAdapterUrl(): string {
  // 환경변수 우선 사용
  if (process.env.NEXT_PUBLIC_KIWOOM_ADAPTER_URL) {
    return process.env.NEXT_PUBLIC_KIWOOM_ADAPTER_URL;
  }

  const host = getCurrentHost();
  const port = DEFAULT_PORTS.KIWOOM_ADAPTER;
  const protocol = host === 'localhost' || host === '127.0.0.1' ? 'http' : 'http';
  
  return `${protocol}://${host}:${port}`;
}

/**
 * WebSocket URL 생성 (향후 사용을 위해)
 */
export function getWebSocketUrl(port: number): string {
  const host = getCurrentHost();
  const protocol = host === 'localhost' || host === '127.0.0.1' ? 'ws' : 'ws';
  
  return `${protocol}://${host}:${port}`;
}

/**
 * 현재 환경 정보 반환 (디버깅용)
 */
export function getEnvironmentInfo() {
  return {
    host: getCurrentHost(),
    apiBaseUrl: getApiBaseUrl(),
    kiwoomAdapterUrl: getKiwoomAdapterUrl(),
    isTailscale: getCurrentHost() === TAILSCALE_IP,
    isSSR: typeof window === 'undefined',
  };
}

// 상수 내보내기 (기존 호환성 유지)
export const API_BASE_URL = getApiBaseUrl();
export const KIWOOM_ADAPTER_URL = getKiwoomAdapterUrl();

// API 엔드포인트들 (기존과 동일)
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