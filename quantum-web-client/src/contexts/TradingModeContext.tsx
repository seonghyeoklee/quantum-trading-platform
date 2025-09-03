'use client';

// 서버 중심 KIS 관리로 인해 더 이상 사용되지 않는 Context
// Trading Mode는 서버에서 관리됩니다

import { createContext, useContext, ReactNode } from 'react';

export type TradingMode = 'SANDBOX' | 'REAL';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface TradingSettings {
  tradingMode: TradingMode;
  maxDailyAmount?: number;
  riskLevel: RiskLevel;
  autoTradingEnabled: boolean;
  notificationsEnabled: boolean;
  lastModeChange?: string;
}

interface TradingModeContextType {
  settings: TradingSettings;
  loading: boolean;
  error: string | null;
  isProduction: boolean;
  isSandbox: boolean;
  refreshSettings: () => Promise<void>;
  updateSettings: (updates: Partial<TradingSettings>) => Promise<boolean>;
}

const defaultSettings: TradingSettings = {
  tradingMode: 'SANDBOX',
  riskLevel: 'MEDIUM',
  autoTradingEnabled: false,
  notificationsEnabled: true
};

const TradingModeContext = createContext<TradingModeContextType | undefined>(undefined);

export function TradingModeProvider({ children }: { children: ReactNode }) {
  // 서버 중심 관리로 인해 기본값만 제공
  const value: TradingModeContextType = {
    settings: defaultSettings,
    loading: false,
    error: null,
    isProduction: false,
    isSandbox: true,
    refreshSettings: async () => {},
    updateSettings: async () => true
  };

  return (
    <TradingModeContext.Provider value={value}>
      {children}
    </TradingModeContext.Provider>
  );
}

export function useTradingMode() {
  const context = useContext(TradingModeContext);
  if (context === undefined) {
    throw new Error('useTradingMode must be used within a TradingModeProvider');
  }
  return context;
}