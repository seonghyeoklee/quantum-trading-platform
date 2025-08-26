'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { StockBasicInfo, StockInfoState } from '@/lib/api/stock-info-types';
import { stockInfoService } from '@/lib/api/stock-info-service';

// 종목 정보 훅 옵션
interface UseStockBasicInfoOptions {
  autoRefresh?: boolean;         // 자동 갱신 여부 (기본값: false)
  refreshInterval?: number;      // 갱신 간격 (밀리초, 기본값: 5분)
  onError?: (error: string) => void; // 에러 콜백
  onSuccess?: (data: StockBasicInfo) => void; // 성공 콜백
}

// 종목 정보 관리 훅
export function useStockBasicInfo(
  symbol: string,
  options: UseStockBasicInfoOptions = {}
) {
  const {
    autoRefresh = false,
    refreshInterval = 5 * 60 * 1000, // 5분
    onError,
    onSuccess
  } = options;

  const [state, setState] = useState<StockInfoState>({
    data: null,
    loading: false,
    error: null,
    lastUpdated: null
  });

  const refreshTimerRef = useRef<NodeJS.Timeout>();
  const isUnmountedRef = useRef(false);

  // 종목 정보 조회 함수
  const fetchStockInfo = useCallback(async (showLoading = true) => {
    if (!symbol || symbol.length !== 6) {
      setState(prev => ({
        ...prev,
        data: null,
        error: '올바른 종목코드를 입력해주세요 (6자리)',
        loading: false
      }));
      return;
    }

    if (showLoading) {
      setState(prev => ({ ...prev, loading: true, error: null }));
    }

    try {
      console.log('🔍 종목 정보 조회 시작:', symbol);
      const stockInfo = await stockInfoService.getStockBasicInfo(symbol);
      
      if (isUnmountedRef.current) return; // 컴포넌트가 언마운트된 경우 상태 업데이트 방지

      setState({
        data: stockInfo,
        loading: false,
        error: null,
        lastUpdated: stockInfo.lastUpdated
      });

      console.log('✅ 종목 정보 조회 완료:', symbol, stockInfo);
      onSuccess?.(stockInfo);

    } catch (error: any) {
      if (isUnmountedRef.current) return;

      const errorMessage = error.message || '종목 정보 조회에 실패했습니다';
      console.error('❌ 종목 정보 조회 실패:', symbol, error);
      
      setState({
        data: null,
        loading: false,
        error: errorMessage,
        lastUpdated: null
      });

      onError?.(errorMessage);
    }
  }, [symbol, onError, onSuccess]);

  // 수동 새로고침
  const refresh = useCallback(() => {
    fetchStockInfo(true);
  }, [fetchStockInfo]);

  // 자동 갱신 설정
  useEffect(() => {
    if (autoRefresh && state.data && !state.loading) {
      console.log('⏰ 자동 갱신 타이머 설정:', symbol, refreshInterval / 1000, '초');
      
      refreshTimerRef.current = setTimeout(() => {
        fetchStockInfo(false); // 백그라운드 갱신 (로딩 표시 안함)
      }, refreshInterval);

      return () => {
        if (refreshTimerRef.current) {
          clearTimeout(refreshTimerRef.current);
        }
      };
    }
  }, [autoRefresh, state.data, state.loading, symbol, refreshInterval, fetchStockInfo]);

  // 초기 데이터 로딩 및 symbol 변경 시 재조회
  useEffect(() => {
    if (symbol) {
      fetchStockInfo(true);
    } else {
      setState({
        data: null,
        loading: false,
        error: null,
        lastUpdated: null
      });
    }
  }, [symbol, fetchStockInfo]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      isUnmountedRef.current = true;
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    };
  }, []);

  return {
    ...state,
    refresh,
    isAutoRefreshing: autoRefresh && !state.loading && !!state.data,
  };
}

// 여러 종목 정보를 관리하는 훅
export function useMultipleStockInfo(symbols: string[]) {
  const [stocksData, setStocksData] = useState<{ [symbol: string]: StockInfoState }>({});
  const [globalLoading, setGlobalLoading] = useState(false);

  const fetchMultipleStockInfo = useCallback(async () => {
    if (symbols.length === 0) {
      setStocksData({});
      return;
    }

    setGlobalLoading(true);
    
    // 각 종목별로 초기 상태 설정
    const initialStates: { [symbol: string]: StockInfoState } = {};
    symbols.forEach(symbol => {
      initialStates[symbol] = {
        data: null,
        loading: true,
        error: null,
        lastUpdated: null
      };
    });
    setStocksData(initialStates);

    try {
      console.log('📊 여러 종목 정보 배치 조회:', symbols);
      const stockInfos = await stockInfoService.getMultipleStockInfo(symbols);

      // 성공한 결과를 상태에 반영
      const updatedStates: { [symbol: string]: StockInfoState } = {};
      
      symbols.forEach(symbol => {
        const stockInfo = stockInfos.find(info => info.symbol === symbol);
        
        if (stockInfo) {
          updatedStates[symbol] = {
            data: stockInfo,
            loading: false,
            error: null,
            lastUpdated: stockInfo.lastUpdated
          };
        } else {
          updatedStates[symbol] = {
            data: null,
            loading: false,
            error: '종목 정보를 찾을 수 없습니다',
            lastUpdated: null
          };
        }
      });

      setStocksData(updatedStates);
      console.log('✅ 여러 종목 정보 조회 완료:', stockInfos.length, '개');

    } catch (error: any) {
      console.error('❌ 여러 종목 정보 조회 실패:', error);
      
      // 모든 종목에 에러 상태 설정
      const errorStates: { [symbol: string]: StockInfoState } = {};
      symbols.forEach(symbol => {
        errorStates[symbol] = {
          data: null,
          loading: false,
          error: error.message || '종목 정보 조회에 실패했습니다',
          lastUpdated: null
        };
      });
      setStocksData(errorStates);
    } finally {
      setGlobalLoading(false);
    }
  }, [symbols]);

  useEffect(() => {
    fetchMultipleStockInfo();
  }, [fetchMultipleStockInfo]);

  return {
    stocksData,
    globalLoading,
    refresh: fetchMultipleStockInfo,
    getStockInfo: (symbol: string) => stocksData[symbol] || {
      data: null,
      loading: false,
      error: '종목을 찾을 수 없습니다',
      lastUpdated: null
    }
  };
}

// 즐겨찾기 종목 관리 훅 (향후 확장용)
export function useFavoriteStocks() {
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    // localStorage에서 즐겨찾기 목록 로드
    const saved = localStorage.getItem('favorite-stocks');
    if (saved) {
      try {
        setFavorites(JSON.parse(saved));
      } catch (error) {
        console.error('즐겨찾기 로드 실패:', error);
      }
    }
  }, []);

  const addFavorite = useCallback((symbol: string) => {
    setFavorites(prev => {
      if (prev.includes(symbol)) return prev;
      const updated = [...prev, symbol];
      localStorage.setItem('favorite-stocks', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const removeFavorite = useCallback((symbol: string) => {
    setFavorites(prev => {
      const updated = prev.filter(s => s !== symbol);
      localStorage.setItem('favorite-stocks', JSON.stringify(updated));
      return updated;
    });
  }, []);

  const isFavorite = useCallback((symbol: string) => {
    return favorites.includes(symbol);
  }, [favorites]);

  return {
    favorites,
    addFavorite,
    removeFavorite,
    isFavorite
  };
}

// 캐시 관리 훅
export function useStockInfoCache() {
  const invalidateCache = useCallback((symbol?: string) => {
    stockInfoService.invalidateCache(symbol);
    console.log('🗑️ 종목 캐시 무효화:', symbol || '전체');
  }, []);

  const getCacheStatus = useCallback(() => {
    return stockInfoService.getCacheStatus();
  }, []);

  const preloadPopularStocks = useCallback(async () => {
    console.log('🚀 인기 종목 프리로딩 시작');
    await stockInfoService.preloadPopularStocks();
  }, []);

  return {
    invalidateCache,
    getCacheStatus,
    preloadPopularStocks
  };
}