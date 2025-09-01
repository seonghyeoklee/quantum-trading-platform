'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { getApiBaseUrl } from '@/lib/api-client';

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
  const [settings, setSettings] = useState<TradingSettings>(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshSettings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setSettings(defaultSettings);
        return;
      }

      const apiBaseUrl = getApiBaseUrl();
      console.log('🔧 [TradingMode] Fetching trading mode status from:', `${apiBaseUrl}/api/v1/trading-mode/status`);
      
      // 자동 모드 탐지 API 호출
      const response = await fetch(`${apiBaseUrl}/api/v1/trading-mode/status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          // API 키 기반 자동 탐지된 거래 모드를 설정에 반영
          const detectedMode = result.data.tradingMode === 'PRODUCTION' ? 'PRODUCTION' : 'SANDBOX';
          const updatedSettings: TradingSettings = {
            ...defaultSettings,
            tradingMode: detectedMode,
            lastModeChange: new Date().toISOString()
          };
          
          setSettings(updatedSettings);
          console.log('✅ [TradingMode] Auto-detected mode:', detectedMode, 'Data:', result.data);
        } else {
          console.warn('⚠️ [TradingMode] No trading mode data received');
          setSettings(defaultSettings);
        }
      } else if (response.status === 401) {
        console.warn('⚠️ [TradingMode] Unauthorized - using default settings');
        setSettings(defaultSettings);
      } else {
        throw new Error(`Failed to load trading mode: ${response.status}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('❌ [TradingMode] Error fetching settings:', errorMessage);
      setError(errorMessage);
      setSettings(defaultSettings);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateSettings = useCallback(async (updates: Partial<TradingSettings>): Promise<boolean> => {
    // 거래 모드는 API 키에 따라 자동 결정되므로, 로컬에서만 업데이트
    // 거래 모드 변경은 키움계좌 설정에서 API 키를 변경해야 함
    console.log('ℹ️ [TradingMode] 거래 모드는 API 키에 따라 자동 결정됩니다:', updates);
    
    if (updates.tradingMode && updates.tradingMode !== settings.tradingMode) {
      setError('거래 모드는 키움증권 API 키에 따라 자동으로 결정됩니다. 키움계좌 설정에서 API 키를 변경해주세요.');
      return false;
    }
    
    // 다른 설정들은 로컬에서 업데이트
    const updatedSettings = { ...settings, ...updates };
    setSettings(updatedSettings);
    console.log('✅ [TradingMode] Local settings updated:', updatedSettings);
    return true;
  }, [settings]);


  // 사용자가 로그인할 때마다 설정 새로고침
  useEffect(() => {
    refreshSettings();
  }, [refreshSettings]);

  // 주기적으로 설정 새로고침 (5분마다)
  useEffect(() => {
    const interval = setInterval(refreshSettings, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [refreshSettings]);

  const value: TradingModeContextType = {
    settings,
    loading,
    error,
    isProduction: settings.tradingMode === 'REAL',
    isSandbox: settings.tradingMode === 'SANDBOX',
    refreshSettings,
    updateSettings
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