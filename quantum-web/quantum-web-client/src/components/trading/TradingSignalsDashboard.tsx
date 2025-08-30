'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, TrendingUp, TrendingDown, Activity, Play, Pause, RefreshCw } from 'lucide-react';
import { 
  TradingSignalsApi, 
  PythonStrategyApi, 
  TradingSignalDto, 
  OrderExecutionResultDto, 
  StrategyStats,
  SystemStatus,
  TradingSignalUtils
} from '@/lib/api/trading-signals';

// Use imported types from API client

export default function TradingSignalsDashboard() {
  const [signals, setSignals] = useState<TradingSignalDto[]>([]);
  const [executionResults, setExecutionResults] = useState<OrderExecutionResultDto[]>([]);
  const [strategies, setStrategies] = useState<StrategyStats[]>([]);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // Initial data load
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadSignals(),
        loadExecutionResults(),
        loadStrategies(),
        loadSystemStatus(),
      ]);
    } catch (error) {
      console.error('Failed to load initial data:', error);
      // Fall back to mock data on error for development
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  const loadSignals = async () => {
    try {
      // Try to get signals from both Python strategy engine and Java backend
      const [pythonSignals, javaResponse] = await Promise.allSettled([
        PythonStrategyApi.getRecentSignals(20),
        TradingSignalsApi.getRecentSignals(20)
      ]);

      let allSignals: TradingSignalDto[] = [];

      if (pythonSignals.status === 'fulfilled') {
        allSignals = [...allSignals, ...pythonSignals.value];
      }

      if (javaResponse.status === 'fulfilled' && javaResponse.value.success && javaResponse.value.data) {
        allSignals = [...allSignals, ...javaResponse.value.data];
      }

      // Remove duplicates and sort by priority
      const uniqueSignals = allSignals.reduce((acc, signal) => {
        const key = `${signal.symbol}-${signal.strategyName}-${signal.timestamp}`;
        if (!acc.has(key)) {
          acc.set(key, signal);
        }
        return acc;
      }, new Map());

      const sortedSignals = TradingSignalUtils.sortByPriority(Array.from(uniqueSignals.values()));
      setSignals(sortedSignals.slice(0, 20)); // Keep only top 20
    } catch (error) {
      console.error('Failed to load signals:', error);
      setSignals([]);
    }
  };

  const loadExecutionResults = async () => {
    try {
      const response = await TradingSignalsApi.getRecentExecutions(20);
      if (response.success && response.data) {
        setExecutionResults(response.data);
      }
    } catch (error) {
      console.error('Failed to load execution results:', error);
      setExecutionResults([]);
    }
  };

  const loadStrategies = async () => {
    try {
      const response = await TradingSignalsApi.getAllStrategiesStatus();
      if (response.success && response.data) {
        setStrategies(response.data);
      }
    } catch (error) {
      console.error('Failed to load strategies:', error);
      setStrategies([]);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const response = await TradingSignalsApi.getSystemStatus();
      if (response.success && response.data) {
        setSystemStatus(response.data);
      }
    } catch (error) {
      console.error('Failed to load system status:', error);
      setSystemStatus(null);
    }
  };

  const loadMockData = () => {
    // Fallback mock data for development
    const mockSignals: TradingSignalDto[] = [
      {
        strategyName: 'RSI_STRATEGY',
        symbol: '005930',
        signalType: 'BUY',
        strength: 'STRONG',
        currentPrice: 71500,
        targetPrice: 75000,
        stopLoss: 68000,
        quantity: 10,
        confidence: 0.87,
        reason: 'RSI 과매도 구간 (RSI: 28.5) 진입, 반등 신호 감지',
        timestamp: new Date(Date.now() - 5000).toISOString(),
        dryRun: false,
        priority: 1,
        technicalIndicators: '{"rsi": 28.5, "sma_5": 71200, "sma_20": 72800}'
      },
      {
        strategyName: 'MOVING_AVERAGE_CROSSOVER',
        symbol: '000660',
        signalType: 'SELL',
        strength: 'MODERATE',
        currentPrice: 145000,
        stopLoss: 148000,
        confidence: 0.72,
        reason: '5일선이 20일선 아래로 데드크로스, 매도 신호',
        timestamp: new Date(Date.now() - 15000).toISOString(),
        dryRun: true,
        priority: 2,
        technicalIndicators: '{"sma_5": 144500, "sma_20": 146200, "rsi": 58.3}'
      }
    ];

    const mockStrategies: StrategyStats[] = [
      {
        strategyName: 'RSI_STRATEGY',
        enabled: true,
        totalSignals: 24,
        successfulSignals: 18,
        failedSignals: 6,
        successRate: 0.75,
        averageProcessingTime: 1250,
        lastSignalTime: new Date(Date.now() - 5000).toISOString(),
        activePositions: 3,
        totalProfitLoss: 125000
      }
    ];

    const mockSystemStatus: SystemStatus = {
      executionMode: 'DRY_RUN',
      isKiwoomConnected: true,
      connectedStrategies: ['RSI_STRATEGY', 'MOVING_AVERAGE_CROSSOVER'],
      enabledStrategies: ['RSI_STRATEGY'],
      processingSignals: 1,
      totalProcessedToday: 42,
      successRateToday: 0.71,
      lastHeartbeat: new Date().toISOString(),
      uptime: 3600000
    };

    setSignals(mockSignals);
    setStrategies(mockStrategies);
    setSystemStatus(mockSystemStatus);
  };

  // Auto refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refreshData();
      }, 10000); // Refresh every 10 seconds
      setRefreshInterval(interval);
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh]);

  const refreshData = async () => {
    setLoading(true);
    try {
      console.log('Refreshing trading signals data...');
      
      // Load fresh data from all sources
      await Promise.allSettled([
        loadSignals(),
        loadExecutionResults(),
        loadStrategies(),
        loadSystemStatus(),
      ]);
      
    } catch (error) {
      console.error('Failed to refresh data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSignalIcon = (signalType: string) => {
    switch (signalType) {
      case 'BUY': return <TrendingUp className="h-4 w-4" />;
      case 'SELL': return <TrendingDown className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getSignalColor = (signalType: string) => {
    switch (signalType) {
      case 'BUY': return 'text-green-600 bg-green-50 border-green-200';
      case 'SELL': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS': return 'bg-green-100 text-green-800 border-green-200';
      case 'REJECTED': return 'bg-red-100 text-red-800 border-red-200';
      case 'PENDING': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'FAILED': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatPrice = (price: number) => {
    return TradingSignalUtils.formatPrice(price).replace('₩', '');
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ko-KR');
  };

  return (
    <div className="space-y-6">
      {/* System Status Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              자동매매 시스템 상태
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                {autoRefresh ? '자동새로고침 중지' : '자동새로고침 시작'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={refreshData}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                새로고침
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {systemStatus && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-sm text-muted-foreground">실행 모드</div>
                <Badge variant={systemStatus.executionMode === 'LIVE' ? 'destructive' : 'secondary'}>
                  {systemStatus.executionMode === 'LIVE' ? '실투자' : '모의투자'}
                </Badge>
              </div>
              <div className="text-center">
                <div className="text-sm text-muted-foreground">키움 연결</div>
                <Badge variant={systemStatus.isKiwoomConnected ? 'default' : 'destructive'}>
                  {systemStatus.isKiwoomConnected ? '연결됨' : '연결 끊김'}
                </Badge>
              </div>
              <div className="text-center">
                <div className="text-sm text-muted-foreground">오늘 처리</div>
                <div className="text-lg font-semibold">{systemStatus.totalProcessedToday}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-muted-foreground">성공률</div>
                <div className="text-lg font-semibold">
                  {(systemStatus.successRateToday * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Live Trading Signals */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              실시간 매매신호
              {signals.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {signals.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {signals.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <div>현재 활성화된 매매신호가 없습니다</div>
                <div className="text-sm">전략 엔진이 신호를 분석 중입니다</div>
              </div>
            ) : (
              signals.map((signal, index) => (
                <div
                  key={`${signal.symbol}-${signal.strategyName}-${index}`}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge className={getSignalColor(signal.signalType)}>
                        {getSignalIcon(signal.signalType)}
                        {signal.signalType}
                      </Badge>
                      <Badge variant="outline">
                        {signal.strength}
                      </Badge>
                      {signal.dryRun && (
                        <Badge variant="secondary">모의투자</Badge>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {formatTimestamp(signal.timestamp)}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div>
                      <div className="text-sm font-medium">{signal.symbol}</div>
                      <div className="text-sm text-muted-foreground">
                        {signal.strategyName}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold">
                        ₩{formatPrice(signal.currentPrice)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        신뢰도: {(signal.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {(signal.targetPrice || signal.stopLoss) && (
                    <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                      {signal.targetPrice && (
                        <div>
                          <span className="text-muted-foreground">목표가: </span>
                          <span className="font-medium">₩{formatPrice(signal.targetPrice)}</span>
                        </div>
                      )}
                      {signal.stopLoss && (
                        <div>
                          <span className="text-muted-foreground">손절가: </span>
                          <span className="font-medium">₩{formatPrice(signal.stopLoss)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="text-sm text-muted-foreground">
                    <strong>분석:</strong> {signal.reason}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Order Execution Results */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              주문 처리 결과
              {executionResults.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {executionResults.length}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {executionResults.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <AlertCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <div>최근 주문 처리 결과가 없습니다</div>
              </div>
            ) : (
              executionResults.map((result, index) => (
                <div
                  key={`${result.originalSignal.symbol}-${result.executedAt}-${index}`}
                  className="border rounded-lg p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <Badge className={getStatusColor(result.status)}>
                      {result.status}
                    </Badge>
                    <div className="text-sm text-muted-foreground">
                      {formatTimestamp(result.executedAt)}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div>
                      <div className="text-sm font-medium">
                        {result.originalSignal.symbol}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {result.originalSignal.signalType} 신호
                      </div>
                    </div>
                    {result.executedPrice && result.executedQuantity && (
                      <div className="text-right">
                        <div className="text-sm font-medium">
                          {result.executedQuantity}주
                        </div>
                        <div className="text-sm text-muted-foreground">
                          @₩{formatPrice(result.executedPrice)}
                        </div>
                      </div>
                    )}
                  </div>

                  {result.totalAmount && (
                    <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                      <div>
                        <span className="text-muted-foreground">총 금액: </span>
                        <span className="font-medium">₩{formatPrice(result.totalAmount)}</span>
                      </div>
                      {result.netAmount && (
                        <div>
                          <span className="text-muted-foreground">순 금액: </span>
                          <span className="font-medium">₩{formatPrice(result.netAmount)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="text-sm text-muted-foreground">
                    {result.message}
                  </div>

                  {result.processingTimeMs && (
                    <div className="text-xs text-muted-foreground mt-2">
                      처리 시간: {result.processingTimeMs}ms
                    </div>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Strategy Status */}
      <Card>
        <CardHeader>
          <CardTitle>전략 상태</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map((strategy) => (
              <div
                key={strategy.strategyName}
                className="border rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="font-medium">{strategy.strategyName}</div>
                  <Badge variant={strategy.enabled ? 'default' : 'secondary'}>
                    {strategy.enabled ? '활성화' : '비활성화'}
                  </Badge>
                </div>

                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-muted-foreground">총 신호</div>
                    <div className="font-semibold">{strategy.totalSignals}</div>
                  </div>
                  <div className="text-center">
                    <div className="text-muted-foreground">성공률</div>
                    <div className="font-semibold">
                      {(strategy.successRate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-muted-foreground">활성 포지션</div>
                    <div className="font-semibold">{strategy.activePositions}</div>
                  </div>
                </div>

                {strategy.lastSignalTime && (
                  <div className="text-xs text-muted-foreground mt-2">
                    마지막 신호: {formatTimestamp(strategy.lastSignalTime)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}