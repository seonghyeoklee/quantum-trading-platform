export function getApiBaseUrl(): string {
  // 개발 환경에서는 프로덕션 스타일 도메인 구조 사용
  if (process.env.NODE_ENV === 'development') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://api.quantum-trading.com:8080';
  }
  
  // 프로덕션 환경에서는 HTTPS 사용
  return process.env.NEXT_PUBLIC_API_URL || 'https://api.quantum-trading.com';
}

export function getClientBaseUrl(): string {
  // 개발 환경에서는 프로덕션 스타일 도메인 구조 사용
  if (process.env.NODE_ENV === 'development') {
    return process.env.NEXT_PUBLIC_CLIENT_URL || 'http://quantum-trading.com:3000';
  }
  
  // 프로덕션 환경에서는 HTTPS 사용
  return process.env.NEXT_PUBLIC_CLIENT_URL || 'https://quantum-trading.com';
}