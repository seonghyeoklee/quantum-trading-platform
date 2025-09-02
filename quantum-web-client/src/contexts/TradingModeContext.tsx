'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { getApiBaseUrl } from '@/lib/api-config';

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
          const detectedMode = result.data.tradingMode === 'PRODUCTION' ? 'REAL' : 'SANDBOX';
          const updatedSettings: TradingSettings = {
            ...defaultSettings,
            tradingMode: detectedMode,
            lastModeChange: new Date().toISOString()
          };
          
          setSettings(updatedSettings);
        } else {
          setSettings(defaultSettings);
        }
      } else if (response.status === 401) {
        setSettings(defaultSettings);
      } else {
        throw new Error(`Failed to load trading mode: ${response.status}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      console.error('Error fetching trading settings:', errorMessage);
      setError(errorMessage);
      setSettings(defaultSettings);
    } finally {
      setLoading(false);
    }
  }, []);

  const updateSettings = useCallback(async (updates: Partial<TradingSettings>): Promise<boolean> => {
    if (updates.tradingMode && updates.tradingMode !== settings.tradingMode) {
      setError('거래 모드는 키움증권 API 키에 따라 자동으로 결정됩니다. 키움계좌 설정에서 API 키를 변경해주세요.');
      return false;
    }
    
    const updatedSettings = { ...settings, ...updates };
    setSettings(updatedSettings);
    return true;
  }, [settings]);


  useEffect(() => {
    refreshSettings();
  }, [refreshSettings]);

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