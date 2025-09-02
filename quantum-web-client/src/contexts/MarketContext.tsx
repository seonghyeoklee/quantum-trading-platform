'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'

export type MarketType = 'domestic' | 'overseas'

export type Exchange = 'NYSE' | 'NASDAQ' | 'AMEX' | 'LSE' | 'TSE' | 'HKSE'

export interface MarketState {
  currentMarket: MarketType
  selectedExchange: Exchange | null
  preferences: {
    defaultMarket: MarketType
    favoriteExchanges: Exchange[]
  }
}

export interface MarketContextType extends MarketState {
  switchMarket: (market: MarketType) => void
  setExchange: (exchange: Exchange | null) => void
  updatePreferences: (preferences: Partial<MarketState['preferences']>) => void
  isMarketOpen: (market: MarketType, exchange?: Exchange) => boolean
  getMarketDisplayName: (market: MarketType, exchange?: Exchange) => string
}

const MarketContext = createContext<MarketContextType | undefined>(undefined)

const STORAGE_KEY = 'quantum-market-preferences'

const DEFAULT_STATE: MarketState = {
  currentMarket: 'domestic',
  selectedExchange: null,
  preferences: {
    defaultMarket: 'domestic',
    favoriteExchanges: ['NYSE', 'NASDAQ']
  }
}

export function MarketProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<MarketState>(DEFAULT_STATE)

  // 로컬스토리지에서 설정 불러오기
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        setState(prev => ({
          ...prev,
          currentMarket: parsed.defaultMarket || 'domestic',
          selectedExchange: parsed.selectedExchange || null,
          preferences: {
            ...prev.preferences,
            ...parsed
          }
        }))
      }
    } catch (error) {
      console.error('MarketContext 설정 로드 실패:', error)
    }
  }, [])

  // 설정 변경 시 로컬스토리지에 저장
  const saveToStorage = (newState: MarketState) => {
    try {
      const toSave = {
        defaultMarket: newState.preferences.defaultMarket,
        selectedExchange: newState.selectedExchange,
        favoriteExchanges: newState.preferences.favoriteExchanges
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
    } catch (error) {
      console.error('MarketContext 설정 저장 실패:', error)
    }
  }

  const switchMarket = (market: MarketType) => {
    setState(prev => {
      const newState = {
        ...prev,
        currentMarket: market,
        // 국내로 전환 시 거래소 초기화
        selectedExchange: market === 'domestic' ? null : prev.selectedExchange
      }
      saveToStorage(newState)
      return newState
    })
  }

  const setExchange = (exchange: Exchange | null) => {
    setState(prev => {
      const newState = {
        ...prev,
        selectedExchange: exchange,
        // 거래소 선택 시 자동으로 해외 시장으로 전환
        currentMarket: exchange ? 'overseas' : prev.currentMarket
      }
      saveToStorage(newState)
      return newState
    })
  }

  const updatePreferences = (preferences: Partial<MarketState['preferences']>) => {
    setState(prev => {
      const newState = {
        ...prev,
        preferences: {
          ...prev.preferences,
          ...preferences
        }
      }
      saveToStorage(newState)
      return newState
    })
  }

  const isMarketOpen = (market: MarketType, exchange?: Exchange): boolean => {
    const now = new Date()
    const currentHour = now.getHours()

    if (market === 'domestic') {
      // 한국 시장: 오전 9시 ~ 오후 3시 30분 (KST)
      return currentHour >= 9 && currentHour < 15
    } else {
      // 해외 시장은 거래소별로 다름 (간단 구현)
      switch (exchange) {
        case 'NYSE':
        case 'NASDAQ':
        case 'AMEX':
          // 미국 시장: 오후 11시 30분 ~ 오전 6시 (KST, 서머타임 무시)
          return (currentHour >= 23 && currentHour <= 23) || (currentHour >= 0 && currentHour < 6)
        default:
          return false
      }
    }
  }

  const getMarketDisplayName = (market: MarketType, exchange?: Exchange): string => {
    if (market === 'domestic') {
      return '국내'
    } else {
      switch (exchange) {
        case 'NYSE': return '뉴욕증권거래소'
        case 'NASDAQ': return '나스닥'
        case 'AMEX': return '아메리칸거래소'
        case 'LSE': return '런던증권거래소'
        case 'TSE': return '도쿄증권거래소'
        case 'HKSE': return '홍콩증권거래소'
        default: return '해외'
      }
    }
  }

  const value: MarketContextType = {
    ...state,
    switchMarket,
    setExchange,
    updatePreferences,
    isMarketOpen,
    getMarketDisplayName
  }

  return (
    <MarketContext.Provider value={value}>
      {children}
    </MarketContext.Provider>
  )
}

export function useMarket() {
  const context = useContext(MarketContext)
  if (context === undefined) {
    throw new Error('useMarket must be used within a MarketProvider')
  }
  return context
}

// 편의 훅들
export function useCurrentMarket() {
  const { currentMarket } = useMarket()
  return currentMarket
}

export function useSelectedExchange() {
  const { selectedExchange } = useMarket()
  return selectedExchange
}

export function useMarketSwitch() {
  const { switchMarket, setExchange } = useMarket()
  return { switchMarket, setExchange }
}