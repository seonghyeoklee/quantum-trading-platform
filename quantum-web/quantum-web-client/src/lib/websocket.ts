import { Client, IMessage } from '@stomp/stompjs';
import SockJS from 'sockjs-client';

/**
 * WebSocket Client for Real-time Data
 * 
 * Spring Boot WebSocket 서버와의 실시간 통신을 위한 클라이언트
 */
export class WebSocketClient {
  private client: Client;
  private subscriptions: Map<string, () => void> = new Map();

  constructor(private baseUrl: string = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8080/api/v1') {
    this.client = new Client({
      webSocketFactory: () => new SockJS(`${this.baseUrl}/ws`),
      debug: (str) => {
        if (process.env.NODE_ENV === 'development') {
          console.log('[WebSocket]', str);
        }
      },
      reconnectDelay: 5000,
      heartbeatIncoming: 4000,
      heartbeatOutgoing: 4000,
    });

    this.client.onConnect = (frame) => {
      console.log('[WebSocket] Connected:', frame);
    };

    this.client.onDisconnect = (frame) => {
      console.log('[WebSocket] Disconnected:', frame);
    };

    this.client.onStompError = (frame) => {
      console.error('[WebSocket] STOMP Error:', frame.headers['message']);
      console.error('[WebSocket] Details:', frame.body);
    };
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.client.onConnect = () => {
        console.log('[WebSocket] Connected');
        resolve();
      };

      this.client.onStompError = (frame) => {
        console.error('[WebSocket] Connection failed:', frame);
        reject(new Error(frame.headers['message'] || 'Connection failed'));
      };

      this.client.activate();
    });
  }

  disconnect(): void {
    this.subscriptions.forEach((unsubscribe) => unsubscribe());
    this.subscriptions.clear();
    this.client.deactivate();
  }

  /**
   * Subscribe to real-time quote updates
   */
  subscribeToQuotes(symbol: string, callback: (data: any) => void): () => void {
    const destination = `/topic/quotes/${symbol}`;
    const subscription = this.client.subscribe(destination, (message: IMessage) => {
      try {
        const data = JSON.parse(message.body);
        callback(data);
      } catch (error) {
        console.error('[WebSocket] Failed to parse quote data:', error);
      }
    });

    const unsubscribe = () => subscription.unsubscribe();
    this.subscriptions.set(`quotes-${symbol}`, unsubscribe);
    return unsubscribe;
  }

  /**
   * Subscribe to real-time trade updates
   */
  subscribeToTrades(symbol: string, callback: (data: any) => void): () => void {
    const destination = `/topic/trades/${symbol}`;
    const subscription = this.client.subscribe(destination, (message: IMessage) => {
      try {
        const data = JSON.parse(message.body);
        callback(data);
      } catch (error) {
        console.error('[WebSocket] Failed to parse trade data:', error);
      }
    });

    const unsubscribe = () => subscription.unsubscribe();
    this.subscriptions.set(`trades-${symbol}`, unsubscribe);
    return unsubscribe;
  }

  /**
   * Subscribe to order updates for a specific portfolio
   */
  subscribeToOrderUpdates(portfolioId: string, callback: (data: any) => void): () => void {
    const destination = `/topic/orders/${portfolioId}`;
    const subscription = this.client.subscribe(destination, (message: IMessage) => {
      try {
        const data = JSON.parse(message.body);
        callback(data);
      } catch (error) {
        console.error('[WebSocket] Failed to parse order update:', error);
      }
    });

    const unsubscribe = () => subscription.unsubscribe();
    this.subscriptions.set(`orders-${portfolioId}`, unsubscribe);
    return unsubscribe;
  }

  /**
   * Subscribe to portfolio updates
   */
  subscribeToPortfolioUpdates(portfolioId: string, callback: (data: any) => void): () => void {
    const destination = `/topic/portfolio/${portfolioId}`;
    const subscription = this.client.subscribe(destination, (message: IMessage) => {
      try {
        const data = JSON.parse(message.body);
        callback(data);
      } catch (error) {
        console.error('[WebSocket] Failed to parse portfolio update:', error);
      }
    });

    const unsubscribe = () => subscription.unsubscribe();
    this.subscriptions.set(`portfolio-${portfolioId}`, unsubscribe);
    return unsubscribe;
  }

  /**
   * Send a message to the server
   */
  sendMessage(destination: string, body: object = {}): void {
    if (this.client.connected) {
      this.client.publish({
        destination,
        body: JSON.stringify(body),
      });
    } else {
      console.warn('[WebSocket] Not connected. Message not sent:', { destination, body });
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.client.connected;
  }
}

// Singleton instance
export const wsClient = new WebSocketClient();