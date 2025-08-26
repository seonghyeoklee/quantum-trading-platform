'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  WebSocketStatus,
  WebSocketMessage,
  WebSocketOptions,
  WebSocketHookReturn,
  SubscribeRequest,
  UnsubscribeRequest,
} from '@/lib/api/websocket-types';

const DEFAULT_OPTIONS: Partial<WebSocketOptions> = {
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000,
};

export default function useWebSocket(options: WebSocketOptions): WebSocketHookReturn {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isManualDisconnectRef = useRef(false);
  const messageQueueRef = useRef<any[]>([]);

  const config = { ...DEFAULT_OPTIONS, ...options };

  // WebSocket 연결
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    console.log(`WebSocket 연결 시도: ${config.url}`);
    isManualDisconnectRef.current = false;
    setStatus('connecting');
    setError(null);

    try {
      const ws = new WebSocket(config.url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket 연결 성공');
        setStatus('connected');
        setError(null);
        reconnectAttemptsRef.current = 0;
        setReconnectAttempts(0);

        // 대기열에 있는 메시지들 전송
        messageQueueRef.current.forEach(message => {
          ws.send(JSON.stringify(message));
        });
        messageQueueRef.current = [];

        // 하트비트 시작
        if (config.heartbeatInterval && config.heartbeatInterval > 0) {
          heartbeatIntervalRef.current = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'heartbeat', timestamp: new Date().toISOString() }));
            }
          }, config.heartbeatInterval);
        }

        config.onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          console.log('📨 Raw WebSocket 메시지 수신:', event.data);
          
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('📋 파싱된 메시지:', {
            type: message.type,
            trnm: message.trnm,
            command: message.command,
            return_code: message.return_code,
            dataKeys: Object.keys(message.data || message.original_data || {}),
            timestamp: message.timestamp
          });

          // 키움 서버 응답 처리
          if (message.trnm) {
            switch (message.trnm) {
              case 'REG':
                console.log(`✅ 구독 ${message.return_code === 0 ? '성공' : '실패'}:`, message.return_msg);
                if (message.return_code === 0) {
                  console.log('📊 구독된 종목:', message.data);
                }
                break;
                
              case 'REMOVE':
                console.log(`✅ 구독 해지 ${message.return_code === 0 ? '성공' : '실패'}:`, message.return_msg);
                break;
                
              case 'REAL':
                console.log('🔥 실시간 데이터 수신 (REAL)');
                // 실시간 데이터는 그대로 전달
                break;
                
              default:
                console.log('❓ 알 수 없는 키움 trnm:', message.trnm, message);
            }
          }
          
          // 하트비트 메시지는 무시
          if (message.type === 'heartbeat' || message.command === 'ping') {
            console.log('💓 하트비트/Ping 메시지 수신');
            return;
          }

          setLastMessage(message);
        } catch (err) {
          console.error('❌ WebSocket 메시지 파싱 오류:', err);
          console.error('❌ 파싱 실패한 데이터:', event.data);
          setError(new Error('메시지 파싱 실패'));
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket 연결 종료:', event.code, event.reason);
        
        // 하트비트 정리
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        if (!isManualDisconnectRef.current) {
          setStatus('disconnected');
          config.onDisconnect?.();

          // 자동 재연결
          if (reconnectAttemptsRef.current < (config.maxReconnectAttempts || 5)) {
            setStatus('reconnecting');
            reconnectAttemptsRef.current += 1;
            setReconnectAttempts(reconnectAttemptsRef.current);

            console.log(`재연결 시도 ${reconnectAttemptsRef.current}/${config.maxReconnectAttempts}`);
            config.onReconnecting?.(reconnectAttemptsRef.current);

            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, config.reconnectInterval);
          } else {
            console.log('최대 재연결 시도 횟수 초과');
            setStatus('error');
            setError(new Error('최대 재연결 시도 횟수를 초과했습니다.'));
          }
        } else {
          setStatus('disconnected');
          config.onDisconnect?.();
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket 에러:', event);
        const wsError = new Error('WebSocket 연결 오류');
        setError(wsError);
        setStatus('error');
        config.onError?.(wsError);
      };

    } catch (err) {
      console.error('WebSocket 생성 오류:', err);
      const initError = new Error('WebSocket 초기화 실패');
      setError(initError);
      setStatus('error');
      config.onError?.(initError);
    }
  }, [config.url, config.reconnectInterval, config.maxReconnectAttempts, config.heartbeatInterval]);

  // WebSocket 연결 해제
  const disconnect = useCallback(() => {
    console.log('WebSocket 수동 연결 해제');
    isManualDisconnectRef.current = true;

    // 재연결 타이머 정리
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // 하트비트 정리
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }

    // WebSocket 연결 정리
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setStatus('disconnected');
    setError(null);
    reconnectAttemptsRef.current = 0;
    setReconnectAttempts(0);
  }, []);

  // 메시지 전송
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const messageStr = JSON.stringify(message);
      console.log('📤 WebSocket 메시지 전송:', {
        type: message.type,
        symbols: message.symbols,
        dataTypes: message.dataTypes,
        messageStr: messageStr
      });
      wsRef.current.send(messageStr);
    } else {
      console.log('⚠️ WebSocket 연결되지 않음. 메시지 대기열에 추가:', {
        type: message.type,
        wsReadyState: wsRef.current?.readyState,
        queueLength: messageQueueRef.current.length
      });
      messageQueueRef.current.push(message);
    }
  }, []);

  // 종목 구독 - 새로운 키움 API 형식
  const subscribe = useCallback((symbols: string[], dataTypes: ('quote' | 'candle' | 'orderbook' | 'trade')[] = ['quote'], refresh: boolean = false) => {
    // 키움 서버 데이터 타입 매핑
    const kiwoomTypes = dataTypes.map(type => {
      switch (type) {
        case 'quote': return '0B';      // 주식체결 (실시간 체결가, 거래량)
        case 'candle': return '0B';     // 주식체결 (캔들 생성용)
        case 'orderbook': return '0A';  // 주식호가 (매수/매도 호가)
        case 'trade': return '0B';      // 주식체결 (거래 내역)
        default: return '0B';
      }
    });

    // REG 명령어로 종목 구독
    const subscribeMsg = {
      command: 'REG',
      grp_no: '1',
      refresh: refresh ? '1' : '0',  // '0': 기존해지, '1': 기존유지
      data: [{
        item: symbols,
        type: [...new Set(kiwoomTypes)]  // 중복 제거
      }]
    };
    
    console.log('📤 키움 REG 구독 메시지:', {
      원본타입: dataTypes,
      키움타입: kiwoomTypes,
      종목: symbols,
      메시지: subscribeMsg
    });
    
    sendMessage(subscribeMsg);
  }, [sendMessage]);

  // 종목 구독 해제 - 새로운 키움 API 형식
  const unsubscribe = useCallback((symbols?: string[], dataTypes?: ('quote' | 'candle' | 'orderbook' | 'trade')[]) => {
    let unsubscribeMsg;

    if (!symbols || symbols.length === 0) {
      // 전체 구독 해지
      unsubscribeMsg = {
        command: 'REMOVE',
        grp_no: '1',
        data: []  // 빈 배열 = 전체 해지
      };
      console.log('📤 키움 전체 구독 해지:', unsubscribeMsg);
    } else {
      // 특정 종목만 해지
      const kiwoomTypes = dataTypes?.map(type => {
        switch (type) {
          case 'quote': return '0B';
          case 'candle': return '0B'; 
          case 'orderbook': return '0A';
          case 'trade': return '0B';
          default: return '0B';
        }
      }) || ['0B'];  // 기본값

      unsubscribeMsg = {
        command: 'REMOVE',
        grp_no: '1',
        data: [{
          item: symbols,
          type: [...new Set(kiwoomTypes)]
        }]
      };
      
      console.log('📤 키움 특정 종목 구독 해지:', {
        종목: symbols,
        타입: dataTypes,
        키움타입: kiwoomTypes,
        메시지: unsubscribeMsg
      });
    }

    sendMessage(unsubscribeMsg);
  }, [sendMessage]);

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    isConnected: status === 'connected',
    lastMessage,
    error,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    reconnectAttempts,
  };
}