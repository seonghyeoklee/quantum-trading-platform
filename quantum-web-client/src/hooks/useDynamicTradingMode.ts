'use client';

// 서버 중심 KIS 관리로 인해 더 이상 사용되지 않는 Hook
// Trading Mode는 서버에서 관리됩니다

export function useDynamicTradingMode() {
  return {
    // 기본값만 반환 (서버 중심 관리)
    displayMode: 'SANDBOX' as const,
    apiMode: 'SANDBOX' as const,
    isProduction: false,
    isSandbox: true,
  };
}