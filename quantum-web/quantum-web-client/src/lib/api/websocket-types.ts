// WebSocket 실시간 데이터 타입 정의

// WebSocket 연결 상태
export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';

// 실시간 시세 데이터
export interface RealtimeQuoteData {
  symbol: string;           // 종목코드 (6자리)
  name: string;            // 종목명
  currentPrice: number;    // 현재가
  change: number;          // 전일대비 등락
  changePercent: number;   // 등락률
  changeDirection: 'up' | 'down' | 'unchanged';  // 등락 방향
  volume: number;          // 거래량
  high: number;           // 고가
  low: number;            // 저가
  open: number;           // 시가
  previousClose: number;  // 전일종가
  timestamp: string;      // 시간 (YYYY-MM-DD HH:mm:ss)
}

// 실시간 캔들스틱 데이터 (차트용)
export interface RealtimeCandleData {
  symbol: string;
  time: string;           // 시간 (YYYY-MM-DD HH:mm:ss)
  open: number;          // 시가
  high: number;          // 고가  
  low: number;           // 저가
  close: number;         // 종가
  volume: number;        // 거래량
  isNew: boolean;        // 새로운 캔들인지 기존 캔들 업데이트인지
}

// 실시간 호가 데이터
export interface RealtimeOrderBookData {
  symbol: string;
  timestamp: string;
  asks: OrderBookLevel[];  // 매도 호가 (10단계)
  bids: OrderBookLevel[];  // 매수 호가 (10단계)
  totalAskVolume: number;  // 매도잔량
  totalBidVolume: number;  // 매수잔량
}

export interface OrderBookLevel {
  price: number;          // 호가
  volume: number;         // 잔량
  orderCount?: number;    // 주문건수 (선택적)
}

// 실시간 체결 내역
export interface RealtimeTradeData {
  id?: string;            // 고유 ID (React 키 생성용)
  symbol: string;
  timestamp: string;
  price: number;          // 체결가격
  volume: number;         // 체결수량
  tradeType: 'buy' | 'sell' | 'unknown';  // 매수/매도 구분
  changeFromPrevious: number;  // 직전 체결가 대비
}

// 주문체결 데이터 인터페이스 (키움 Type '00')
export interface RealtimeOrderExecutionData {
  id: string;             // 고유 ID
  accountNumber: string;  // 계좌번호
  orderNumber: string;    // 주문번호
  symbol: string;         // 종목코드
  symbolName: string;     // 종목명
  orderStatus: string;    // 주문상태 (접수, 체결, 취소 등)
  orderType: 'buy' | 'sell'; // 주문구분 (매수/매도)
  orderMethod: string;    // 매매구분 (시장가, 지정가 등)
  orderQuantity: number;  // 주문수량
  orderPrice: number;     // 주문가격
  remainingQuantity: number; // 미체결수량
  executedAmount: number; // 체결누계금액
  executedPrice?: number; // 체결가
  executedQuantity?: number; // 체결량
  currentPrice: number;   // 현재가
  askPrice: number;       // 매도호가
  bidPrice: number;       // 매수호가
  orderTime: string;      // 주문/체결시간
  timestamp: string;      // 수신시간
  rejectReason?: string;  // 거부사유
  commission: number;     // 수수료
  tax: number;            // 세금
}

// 주문상태 열거형
export type OrderStatus = 'received' | 'partial' | 'completed' | 'cancelled' | 'rejected';

// WebSocket 메시지 타입 (실제 키움 서버 형식)
export type WebSocketMessageType = 'quote' | 'candle' | 'orderbook' | 'trade' | 'subscribe' | 'unsubscribe' | 'error' | 'heartbeat' | 'kiwoom_realtime' | 'realtime_data';

export interface WebSocketMessage<T = any> {
  // 표준 형식
  type?: WebSocketMessageType;
  symbol?: string;
  data?: T;
  timestamp?: string;
  
  // 키움 서버 기존 형식 (레거시)
  event?: string;
  message?: string;
  info?: any;
  
  // 새로운 키움 API 형식
  trnm?: string;           // REG, REMOVE, REAL 등
  return_code?: number;    // 0: 성공, 기타: 실패
  return_msg?: string;     // 응답 메시지
  grp_no?: string;         // 그룹 번호
  command?: string;        // ping 등 명령어
  
  // 실시간 데이터용
  original_data?: {
    trnm?: string;
    data?: Array<{
      item: string;        // 종목코드
      type: string;        // 데이터 타입 (0A, 0B 등)
      name: string;        // 데이터 타입명
      values: { [key: string]: string };  // 실제 데이터 (키-값 형태)
    }>;
  };
}

// 실시간 구독 요청
export interface SubscribeRequest {
  type: 'subscribe';
  symbols: string[];      // 구독할 종목코드 목록
  dataTypes: ('quote' | 'candle' | 'orderbook' | 'trade')[];  // 구독할 데이터 타입
}

export interface UnsubscribeRequest {
  type: 'unsubscribe';
  symbols: string[];      // 구독 해제할 종목코드 목록
  dataTypes?: ('quote' | 'candle' | 'orderbook' | 'trade')[];  // 해제할 데이터 타입 (생략시 모든 타입)
}

// WebSocket 에러
export interface WebSocketError {
  type: 'error';
  code: string;
  message: string;
  timestamp: string;
}

// 실시간 데이터 이벤트 타입
export interface RealtimeDataEvent {
  quote?: RealtimeQuoteData;
  candle?: RealtimeCandleData;
  orderbook?: RealtimeOrderBookData;
  trade?: RealtimeTradeData;
}

// WebSocket Hook 옵션
export interface WebSocketOptions {
  url: string;
  reconnectInterval?: number;    // 재연결 간격 (ms, 기본값: 3000)
  maxReconnectAttempts?: number; // 최대 재연결 시도 횟수 (기본값: 5)
  heartbeatInterval?: number;    // 하트비트 간격 (ms, 기본값: 30000)
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
  onReconnecting?: (attempt: number) => void;
}

// WebSocket Hook 반환 타입
export interface WebSocketHookReturn {
  status: WebSocketStatus;
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (message: SubscribeRequest | UnsubscribeRequest | any) => void;
  subscribe: (symbols: string[], dataTypes?: ('quote' | 'candle' | 'orderbook' | 'trade')[], refresh?: boolean) => void;
  unsubscribe: (symbols: string[], dataTypes?: ('quote' | 'candle' | 'orderbook' | 'trade')[]) => void;
  reconnectAttempts: number;
}

// 차트 업데이트 타입
export interface ChartUpdateData {
  time: string | number;  // TradingView 시간 형식
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}