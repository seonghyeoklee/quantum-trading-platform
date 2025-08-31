/**
 * Trading Signals API Client
 * Java 백엔드의 TradingSignalController와 연동
 */

import { getApiBaseUrl, getKiwoomAdapterUrl } from '../api-config';

const API_BASE_URL = getApiBaseUrl();
const KIWOOM_ADAPTER_URL = getKiwoomAdapterUrl();

// 토큰 관리
const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('accessToken');
};

const getAuthHeaders = (): Record<string, string> => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

// API 호출 래퍼 함수 (디버깅 정보 포함)
const fetchWithLogging = async (url: string, options: RequestInit = {}): Promise<Response> => {
  console.log(`🔄 API 호출 시작: ${options.method || 'GET'} ${url}`);
  console.log(`🔧 Headers:`, options.headers);
  
  const startTime = Date.now();
  
  try {
    const response = await fetch(url, options);
    const endTime = Date.now();
    
    console.log(`✅ API 응답: ${response.status} ${response.statusText} (${endTime - startTime}ms)`);
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      console.error(`❌ API 에러 응답:`, errorText);
      throw new Error(`API 호출 실패: ${response.status} ${response.statusText}\n응답: ${errorText}`);
    }
    
    return response;
  } catch (error) {
    const endTime = Date.now();
    console.error(`❌ API 호출 실패: ${url} (${endTime - startTime}ms)`, error);
    throw error;
  }
};

// API 응답 타입
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  timestamp: string;
}

// 매매신호 데이터 타입
export interface TradingSignalDto {
  strategyName: string;
  symbol: string;
  signalType: 'BUY' | 'SELL' | 'HOLD' | 'CLOSE';
  strength: 'WEAK' | 'MODERATE' | 'STRONG';
  currentPrice: number;
  targetPrice?: number;
  stopLoss?: number;
  quantity?: number;
  quantityRatio?: number;
  confidence: number;
  reason: string;
  timestamp: string;
  validUntil?: string;
  dryRun: boolean;
  priority: number;
  strategyParams?: string;
  technicalIndicators?: string;
  additionalInfo?: string;
}

// 주문 실행 결과 타입
export interface OrderExecutionResultDto {
  status: 'SUCCESS' | 'PARTIAL_SUCCESS' | 'PENDING' | 'REJECTED' | 'FAILED' | 'TIMEOUT' | 'CANCELLED';
  message: string;
  originalSignal: TradingSignalDto;
  orderId?: string;
  kiwoomOrderNumber?: string;
  executedQuantity?: number;
  executedPrice?: number;
  totalAmount?: number;
  commission?: number;
  tax?: number;
  netAmount?: number;
  executedAt: string;
  processingTimeMs?: number;
  errorCode?: string;
  errorDetail?: string;
  dryRun: boolean;
  balanceUpdated: boolean;
  portfolioUpdated: boolean;
}

// 전략 통계 타입
export interface StrategyStats {
  strategyName: string;
  enabled: boolean;
  totalSignals: number;
  successfulSignals: number;
  failedSignals: number;
  successRate: number;
  averageProcessingTime: number;
  lastSignalTime?: string;
  activePositions: number;
  totalProfitLoss?: number;
}

// 시스템 상태 타입
export interface SystemStatus {
  executionMode: 'LIVE' | 'DRY_RUN';
  isKiwoomConnected: boolean;
  connectedStrategies: string[];
  enabledStrategies: string[];
  processingSignals: number;
  totalProcessedToday: number;
  successRateToday: number;
  lastHeartbeat: string;
  uptime: number;
}

// 매매신호 API 클래스
export class TradingSignalsApi {
  
  /**
   * Python 전략에서 매매신호를 Java 백엔드로 전송
   */
  static async receiveSignal(signal: TradingSignalDto): Promise<ApiResponse<OrderExecutionResultDto>> {
    const response = await fetchWithLogging(`${API_BASE_URL}/api/v1/trading/signals/receive`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(signal),
    });

    return await response.json();
  }

  /**
   * 최근 매매신호 조회
   */
  static async getRecentSignals(limit: number = 20): Promise<ApiResponse<TradingSignalDto[]>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/signals/recent?limit=${limit}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch recent signals: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 최근 주문 실행 결과 조회
   */
  static async getRecentExecutions(limit: number = 20): Promise<ApiResponse<OrderExecutionResultDto[]>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/executions/recent?limit=${limit}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch recent executions: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 전략별 통계 조회
   */
  static async getStrategyStats(strategyName: string): Promise<ApiResponse<StrategyStats>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/signals/stats/${encodeURIComponent(strategyName)}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch strategy stats: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 모든 전략 상태 조회
   */
  static async getAllStrategiesStatus(): Promise<ApiResponse<StrategyStats[]>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/signals/strategies/status`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch strategies status: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 전략 활성화/비활성화
   */
  static async setStrategyEnabled(strategyName: string, enabled: boolean): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/signals/strategies/${encodeURIComponent(strategyName)}/enabled?enabled=${enabled}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to update strategy status: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 매매신호 실행 모드 설정
   */
  static async setExecutionMode(dryRun: boolean): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/signals/execution-mode?dryRun=${dryRun}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to update execution mode: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 시스템 상태 조회
   */
  static async getSystemStatus(): Promise<ApiResponse<SystemStatus>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/signals/system/status`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch system status: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 테스트 매매신호 전송
   */
  static async sendTestSignal(signal: TradingSignalDto): Promise<ApiResponse<OrderExecutionResultDto>> {
    const response = await fetchWithLogging(`${API_BASE_URL}/api/v1/trading/signals/test`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(signal),
    });

    return await response.json();
  }
}

// Python Strategy Engine API (Kiwoom Adapter)
export class PythonStrategyApi {
  private static get PYTHON_API_URL() {
    return KIWOOM_ADAPTER_URL;
  }

  /**
   * 전략별 분석 실행
   */
  static async analyzeSymbol(symbol: string, strategy: string): Promise<TradingSignalDto | null> {
    const response = await fetch(`${this.PYTHON_API_URL}/api/v1/strategy/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol,
        strategy_name: strategy,
        dry_run: true,
      }),
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      throw new Error(`전략 분석 API 호출 실패: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    return result.signal || null;
  }

  /**
   * 백그라운드 전략 시작
   */
  static async startStrategy(strategy: string, symbols: string[], config?: any): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.PYTHON_API_URL}/api/v1/strategy/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strategy_name: strategy,
        symbols,
        config: config || {},
        java_callback_url: `${API_BASE_URL}/api/v1/trading/signals/receive`,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to start strategy: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 백그라운드 전략 중지
   */
  static async stopStrategy(strategy: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.PYTHON_API_URL}/api/v1/strategy/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strategy_name: strategy,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to stop strategy: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * 최근 생성된 신호 조회
   */
  static async getRecentSignals(limit: number = 20): Promise<TradingSignalDto[]> {
    const response = await fetch(`${this.PYTHON_API_URL}/api/v1/strategy/recent?limit=${limit}`, {
      method: 'GET',
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    if (!response.ok) {
      throw new Error(`최근 신호 조회 API 호출 실패: ${response.status} ${response.statusText}`);
    }

    const result = await response.json();
    return result.signals || [];
  }
}

// 유틸리티 함수들
export const TradingSignalUtils = {
  /**
   * 신호 유효성 검증
   */
  isValidSignal: (signal: TradingSignalDto): boolean => {
    return !!(
      signal.strategyName &&
      signal.symbol &&
      ['BUY', 'SELL', 'HOLD', 'CLOSE'].includes(signal.signalType) &&
      signal.currentPrice > 0 &&
      signal.confidence >= 0 && signal.confidence <= 1
    );
  },

  /**
   * 신호 우선순위 정렬
   */
  sortByPriority: (signals: TradingSignalDto[]): TradingSignalDto[] => {
    return signals.sort((a, b) => {
      // 우선순위 (낮을수록 높은 우선순위)
      if (a.priority !== b.priority) {
        return a.priority - b.priority;
      }
      // 신뢰도 (높을수록 우선)
      if (a.confidence !== b.confidence) {
        return b.confidence - a.confidence;
      }
      // 시간순 (최신순)
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    });
  },

  /**
   * 신호 만료 여부 확인
   */
  isExpired: (signal: TradingSignalDto): boolean => {
    if (!signal.validUntil) return false;
    return new Date(signal.validUntil) < new Date();
  },

  /**
   * 가격 포맷팅
   */
  formatPrice: (price: number): string => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  },

  /**
   * 수익률 계산
   */
  calculateProfitLoss: (buyPrice: number, sellPrice: number): number => {
    return ((sellPrice - buyPrice) / buyPrice) * 100;
  },

  /**
   * 신호 요약 텍스트 생성
   */
  getSummaryText: (signal: TradingSignalDto): string => {
    return `[${signal.strategyName}] ${signal.symbol} ${signal.signalType} (신뢰도: ${(signal.confidence * 100).toFixed(1)}%, 가격: ${TradingSignalUtils.formatPrice(signal.currentPrice)})`;
  },
};

export default TradingSignalsApi;