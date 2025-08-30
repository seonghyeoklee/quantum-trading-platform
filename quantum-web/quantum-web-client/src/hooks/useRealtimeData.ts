'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  RealtimeQuoteData, 
  RealtimeCandleData, 
  RealtimeOrderBookData, 
  RealtimeTradeData,
  RealtimeOrderExecutionData
} from '@/lib/api/websocket-types';

// 실시간 데이터 성능 최적화를 위한 Hook
export function useRealtimeData(symbol: string) {
  const [quote, setQuote] = useState<RealtimeQuoteData | null>(null);
  const [candle, setCandle] = useState<RealtimeCandleData | null>(null);
  const [orderBook, setOrderBook] = useState<RealtimeOrderBookData | null>(null);
  const [trades, setTrades] = useState<RealtimeTradeData[]>([]);
  const [orderExecutions, setOrderExecutions] = useState<RealtimeOrderExecutionData[]>([]);

  // 데이터 업데이트 throttling을 위한 ref들
  const lastQuoteUpdateRef = useRef<number>(0);
  const lastCandleUpdateRef = useRef<number>(0);
  const lastOrderBookUpdateRef = useRef<number>(0);
  const lastTradeUpdateRef = useRef<number>(0);
  const lastOrderExecutionUpdateRef = useRef<number>(0);

  // Throttling 간격 (ms)
  const QUOTE_THROTTLE = 100;      // 100ms - 시세는 자주 업데이트
  const CANDLE_THROTTLE = 500;     // 500ms - 캔들은 적당히
  const ORDERBOOK_THROTTLE = 200;  // 200ms - 호가는 중간
  const TRADE_THROTTLE = 50;       // 50ms - 체결은 즉시
  const ORDER_EXECUTION_THROTTLE = 0; // 0ms - 주문체결은 실시간

  // Throttled 업데이트 함수들
  const updateQuote = useCallback((data: RealtimeQuoteData) => {
    if (data.symbol !== symbol) return;
    
    const now = Date.now();
    if (now - lastQuoteUpdateRef.current >= QUOTE_THROTTLE) {
      setQuote(data);
      lastQuoteUpdateRef.current = now;
    }
  }, [symbol]);

  const updateCandle = useCallback((data: RealtimeCandleData) => {
    if (data.symbol !== symbol) return;
    
    const now = Date.now();
    if (now - lastCandleUpdateRef.current >= CANDLE_THROTTLE) {
      setCandle(data);
      lastCandleUpdateRef.current = now;
    }
  }, [symbol]);

  const updateOrderBook = useCallback((data: RealtimeOrderBookData) => {
    if (data.symbol !== symbol) return;
    
    const now = Date.now();
    if (now - lastOrderBookUpdateRef.current >= ORDERBOOK_THROTTLE) {
      setOrderBook(data);
      lastOrderBookUpdateRef.current = now;
    }
  }, [symbol]);

  const updateTrade = useCallback((data: RealtimeTradeData) => {
    if (data.symbol !== symbol) return;
    
    const now = Date.now();
    if (now - lastTradeUpdateRef.current >= TRADE_THROTTLE) {
      setTrades(prev => {
        // 메모리 누수 방지: 최근 100개만 유지
        const newTrades = [...prev, data];
        return newTrades.slice(-100);
      });
      lastTradeUpdateRef.current = now;
    }
  }, [symbol]);

  const updateOrderExecution = useCallback((data: RealtimeOrderExecutionData) => {
    // 주문체결은 계좌별로 필터링 (계좌 필터 기능 추가 가능)
    const now = Date.now();
    if (now - lastOrderExecutionUpdateRef.current >= ORDER_EXECUTION_THROTTLE) {
      setOrderExecutions(prev => {
        // 메모리 누수 방지: 최근 200개만 유지 (주문체결은 더 많이 보관)
        const newExecutions = [...prev, data];
        return newExecutions.slice(-200);
      });
      lastOrderExecutionUpdateRef.current = now;
    }
  }, []);

  // 데이터 초기화
  const clearData = useCallback(() => {
    setQuote(null);
    setCandle(null);
    setOrderBook(null);
    setTrades([]);
    setOrderExecutions([]);
  }, []);

  return {
    quote,
    candle,
    orderBook,
    trades,
    orderExecutions,
    updateQuote,
    updateCandle,
    updateOrderBook,
    updateTrade,
    updateOrderExecution,
    clearData
  };
}

// WebSocket 메시지 처리 최적화를 위한 Hook
export function useMessageProcessor() {
  const messageQueueRef = useRef<any[]>([]);
  const processingRef = useRef<boolean>(false);
  
  const processMessages = useCallback(() => {
    if (processingRef.current || messageQueueRef.current.length === 0) {
      return;
    }
    
    processingRef.current = true;
    
    // 배치로 메시지 처리
    const batch = messageQueueRef.current.splice(0, 10); // 한 번에 최대 10개
    
    try {
      batch.forEach(handler => {
        if (typeof handler === 'function') {
          handler();
        }
      });
    } catch (error) {
      console.error('메시지 배치 처리 오류:', error);
    } finally {
      processingRef.current = false;
      
      // 대기 중인 메시지가 더 있으면 재귀 처리
      if (messageQueueRef.current.length > 0) {
        requestAnimationFrame(processMessages);
      }
    }
  }, []);
  
  const addMessage = useCallback((handler: () => void) => {
    messageQueueRef.current.push(handler);
    
    if (!processingRef.current) {
      requestAnimationFrame(processMessages);
    }
  }, [processMessages]);
  
  return { addMessage };
}

// 연결 상태 관리를 위한 Hook
export function useConnectionHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean>(true);
  const [lastActivity, setLastActivity] = useState<number>(Date.now());
  const [latency, setLatency] = useState<number>(0);
  
  const activityTimeoutRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const pingTimeRef = useRef<number>(0);
  
  const recordActivity = useCallback(() => {
    setLastActivity(Date.now());
    setIsHealthy(true);
    
    // 30초 후 비활성 상태로 간주
    if (activityTimeoutRef.current) {
      clearTimeout(activityTimeoutRef.current);
    }
    
    activityTimeoutRef.current = setTimeout(() => {
      setIsHealthy(false);
    }, 30000);
  }, []);
  
  const startPing = useCallback(() => {
    pingTimeRef.current = Date.now();
  }, []);
  
  const recordPong = useCallback(() => {
    if (pingTimeRef.current > 0) {
      const currentLatency = Date.now() - pingTimeRef.current;
      setLatency(currentLatency);
      pingTimeRef.current = 0;
    }
  }, []);
  
  useEffect(() => {
    return () => {
      if (activityTimeoutRef.current) {
        clearTimeout(activityTimeoutRef.current);
      }
    };
  }, []);
  
  return {
    isHealthy,
    lastActivity,
    latency,
    recordActivity,
    startPing,
    recordPong
  };
}