// WebSocket 관련 유틸리티 함수들

import { WebSocketMessage, RealtimeQuoteData, RealtimeCandleData, RealtimeOrderBookData, RealtimeTradeData } from '@/lib/api/websocket-types';

// WebSocket URL 검증
export function validateWebSocketUrl(url: string): boolean {
  try {
    const parsedUrl = new URL(url);
    return parsedUrl.protocol === 'ws:' || parsedUrl.protocol === 'wss:';
  } catch {
    return false;
  }
}

// 메시지 검증
export function validateMessage(message: any): message is WebSocketMessage {
  return (
    typeof message === 'object' &&
    message !== null &&
    typeof message.type === 'string' &&
    message.data !== undefined &&
    typeof message.timestamp === 'string'
  );
}

// 실시간 시세 데이터 검증
export function validateQuoteData(data: any): data is RealtimeQuoteData {
  return (
    typeof data === 'object' &&
    data !== null &&
    typeof data.symbol === 'string' &&
    typeof data.name === 'string' &&
    typeof data.currentPrice === 'number' &&
    typeof data.change === 'number' &&
    typeof data.changePercent === 'number' &&
    ['up', 'down', 'unchanged'].includes(data.changeDirection) &&
    typeof data.volume === 'number' &&
    typeof data.high === 'number' &&
    typeof data.low === 'number' &&
    typeof data.open === 'number' &&
    typeof data.previousClose === 'number' &&
    typeof data.timestamp === 'string'
  );
}

// 실시간 캔들 데이터 검증
export function validateCandleData(data: any): data is RealtimeCandleData {
  return (
    typeof data === 'object' &&
    data !== null &&
    typeof data.symbol === 'string' &&
    typeof data.time === 'string' &&
    typeof data.open === 'number' &&
    typeof data.high === 'number' &&
    typeof data.low === 'number' &&
    typeof data.close === 'number' &&
    typeof data.volume === 'number' &&
    typeof data.isNew === 'boolean'
  );
}

// 실시간 호가 데이터 검증
export function validateOrderBookData(data: any): data is RealtimeOrderBookData {
  return (
    typeof data === 'object' &&
    data !== null &&
    typeof data.symbol === 'string' &&
    typeof data.timestamp === 'string' &&
    Array.isArray(data.asks) &&
    Array.isArray(data.bids) &&
    typeof data.totalAskVolume === 'number' &&
    typeof data.totalBidVolume === 'number' &&
    data.asks.every((level: any) => 
      typeof level.price === 'number' && typeof level.volume === 'number'
    ) &&
    data.bids.every((level: any) => 
      typeof level.price === 'number' && typeof level.volume === 'number'
    )
  );
}

// 실시간 체결 데이터 검증
export function validateTradeData(data: any): data is RealtimeTradeData {
  return (
    typeof data === 'object' &&
    data !== null &&
    typeof data.symbol === 'string' &&
    typeof data.timestamp === 'string' &&
    typeof data.price === 'number' &&
    typeof data.volume === 'number' &&
    ['buy', 'sell', 'unknown'].includes(data.tradeType) &&
    typeof data.changeFromPrevious === 'number'
  );
}

// WebSocket 연결 상태 설명 가져오기
export function getConnectionStatusDescription(status: string): string {
  switch (status) {
    case 'connecting':
      return '서버에 연결을 시도하고 있습니다';
    case 'connected':
      return '실시간 데이터를 수신하고 있습니다';
    case 'disconnected':
      return '서버와의 연결이 끊어졌습니다';
    case 'error':
      return '연결 중 오류가 발생했습니다';
    case 'reconnecting':
      return '서버에 재연결을 시도하고 있습니다';
    default:
      return '알 수 없는 상태입니다';
  }
}

// 재연결 지연 계산 (백오프 전략)
export function calculateReconnectDelay(attempt: number, baseDelay: number = 1000): number {
  // 지수 백오프: 1초, 2초, 4초, 8초, 16초, 최대 30초
  const delay = Math.min(baseDelay * Math.pow(2, attempt - 1), 30000);
  
  // 지터 추가 (±25% 랜덤)
  const jitter = delay * 0.25 * (Math.random() * 2 - 1);
  
  return Math.max(1000, delay + jitter);
}

// 메시지 크기 제한 검사
export function isMessageSizeValid(message: string, maxSize: number = 64 * 1024): boolean {
  const byteLength = new Blob([message]).size;
  return byteLength <= maxSize;
}

// 종목코드 정규화
export function normalizeSymbol(symbol: string): string {
  // 6자리 종목코드로 정규화
  return symbol.replace(/[^0-9]/g, '').padStart(6, '0');
}

// 데이터 타입별 캐시 키 생성
export function getCacheKey(type: string, symbol: string, additionalParams?: Record<string, any>): string {
  let key = `${type}:${symbol}`;
  
  if (additionalParams) {
    const sortedParams = Object.keys(additionalParams)
      .sort()
      .map(k => `${k}=${additionalParams[k]}`)
      .join('&');
    key += `:${sortedParams}`;
  }
  
  return key;
}

// 메시지 압축 해제 (실제 구현은 압축 라이브러리에 따라 달라짐)
export function decompressMessage(compressedData: any): any {
  // 현재는 그대로 반환, 실제로는 압축 해제 로직 구현
  return compressedData;
}

// 오류 메시지 사용자 친화적으로 변환
export function getUserFriendlyErrorMessage(error: Error | string): string {
  const errorMessage = typeof error === 'string' ? error : error.message;
  
  if (errorMessage.includes('ECONNREFUSED')) {
    return '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.';
  }
  
  if (errorMessage.includes('timeout')) {
    return '서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.';
  }
  
  if (errorMessage.includes('WebSocket')) {
    return '실시간 연결에 문제가 발생했습니다. 페이지를 새로고침해주세요.';
  }
  
  if (errorMessage.includes('JSON')) {
    return '데이터 형식에 오류가 있습니다. 관리자에게 문의해주세요.';
  }
  
  return errorMessage || '알 수 없는 오류가 발생했습니다.';
}

// 성능 메트릭 수집
export interface PerformanceMetrics {
  messagesReceived: number;
  messagesProcessed: number;
  averageLatency: number;
  errorCount: number;
  connectionUptime: number;
}

export class WebSocketPerformanceMonitor {
  private startTime: number;
  private metrics: PerformanceMetrics;
  private latencyHistory: number[];
  
  constructor() {
    this.startTime = Date.now();
    this.metrics = {
      messagesReceived: 0,
      messagesProcessed: 0,
      averageLatency: 0,
      errorCount: 0,
      connectionUptime: 0
    };
    this.latencyHistory = [];
  }
  
  recordMessageReceived() {
    this.metrics.messagesReceived++;
  }
  
  recordMessageProcessed() {
    this.metrics.messagesProcessed++;
  }
  
  recordLatency(latency: number) {
    this.latencyHistory.push(latency);
    
    // 최근 100개만 유지
    if (this.latencyHistory.length > 100) {
      this.latencyHistory = this.latencyHistory.slice(-100);
    }
    
    // 평균 레이턴시 계산
    this.metrics.averageLatency = this.latencyHistory.reduce((sum, l) => sum + l, 0) / this.latencyHistory.length;
  }
  
  recordError() {
    this.metrics.errorCount++;
  }
  
  getMetrics(): PerformanceMetrics {
    this.metrics.connectionUptime = Date.now() - this.startTime;
    return { ...this.metrics };
  }
  
  reset() {
    this.startTime = Date.now();
    this.metrics = {
      messagesReceived: 0,
      messagesProcessed: 0,
      averageLatency: 0,
      errorCount: 0,
      connectionUptime: 0
    };
    this.latencyHistory = [];
  }
}