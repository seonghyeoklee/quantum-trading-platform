"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getKiwoomAdapterUrl } from '@/lib/api-config';
import { 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  TrendingUp, 
  TrendingDown,
  Zap,
  RefreshCw
} from 'lucide-react';

const API_BASE = getKiwoomAdapterUrl();
console.log('🚀 [Conditional Order Monitor] Using API_BASE:', API_BASE);

interface ConditionalOrder {
  order_id: string;
  symbol: string;
  condition_type: string;
  condition_value: number;
  action: string;
  status: string;
  created_at: string;
  triggered_at?: string;
  completed_at?: string;
  executed_price?: number;
  executed_quantity?: number;
  memo: string;
}

interface CurrentPrice {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  timestamp: string;
}

interface Props {
  userId: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function ConditionalOrderMonitor({ 
  userId, 
  autoRefresh = true, 
  refreshInterval = 5000 
}: Props) {
  const [orders, setOrders] = useState<ConditionalOrder[]>([]);
  const [prices, setPrices] = useState<Record<string, CurrentPrice>>({});
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // 주문 목록 새로고침
  const refreshOrders = async () => {
    try {
      setLoading(true);
      const url = `${API_BASE}/api/v1/conditional/orders/${userId}`;
      console.log('📡 [API Call] Fetching orders from:', url);
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setOrders(data.orders || []);
        setLastUpdate(new Date().toLocaleTimeString());
        console.log('✅ [API Call] Orders fetched successfully:', data.orders?.length || 0, 'orders');
      } else {
        console.error('❌ [API Call] Failed to fetch orders, status:', response.status);
      }
    } catch (error) {
      console.error('❌ [API Call] 주문 목록 새로고침 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 현재가 정보 가져오기 (실제 API 호출)
  const refreshPrices = async () => {
    const symbols = [...new Set(orders.map(order => order.symbol))];
    
    try {
      if (symbols.length === 0) return;

      const response = await fetch(`${API_BASE}/api/v1/market/prices`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbols })
      });

      if (!response.ok) {
        throw new Error(`현재가 조회 API 호출 실패: ${response.status} ${response.statusText}`);
      }

      const priceData: Record<string, CurrentPrice> = await response.json();
      setPrices(priceData);
    } catch (error) {
      console.error('현재가 정보 로드 실패:', error);
      // 에러 시 빈 객체로 설정하여 UI에서 가격 정보를 표시하지 않음
      setPrices({});
    }
  };

  // 주문 취소
  const cancelOrder = async (orderId: string) => {
    if (!confirm('이 주문을 취소하시겠습니까?')) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/conditional/order/${orderId}/cancel?user_id=${userId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        await refreshOrders();
      } else {
        alert('주문 취소에 실패했습니다.');
      }
    } catch (error) {
      console.error('주문 취소 실패:', error);
      alert('주문 취소 중 오류가 발생했습니다.');
    }
  };

  // 조건 만족 여부 확인
  const checkConditionStatus = (order: ConditionalOrder) => {
    const currentPrice = prices[order.symbol]?.price;
    if (!currentPrice) return { satisfied: false, distance: 0 };

    let satisfied = false;
    let distance = 0;

    switch (order.condition_type) {
      case 'price_below':
        satisfied = currentPrice <= order.condition_value;
        distance = ((currentPrice - order.condition_value) / order.condition_value) * 100;
        break;
      case 'price_above':
        satisfied = currentPrice >= order.condition_value;
        distance = ((order.condition_value - currentPrice) / order.condition_value) * 100;
        break;
      default:
        distance = 0;
    }

    return { satisfied, distance: Math.abs(distance) };
  };

  // 상태 뱃지 컴포넌트
  const StatusBadge = ({ status }: { status: string }) => {
    const config = {
      active: { variant: 'secondary' as const, icon: Clock, text: '활성', color: 'text-blue-600' },
      triggered: { variant: 'default' as const, icon: Zap, text: '실행됨', color: 'text-orange-600' },
      completed: { variant: 'default' as const, icon: CheckCircle, text: '완료', color: 'text-green-600' },
      cancelled: { variant: 'destructive' as const, icon: AlertCircle, text: '취소', color: 'text-red-600' }
    };

    const statusConfig = config[status as keyof typeof config] || config.active;
    const Icon = statusConfig.icon;

    return (
      <Badge variant={statusConfig.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {statusConfig.text}
      </Badge>
    );
  };

  // 조건 만족도 표시
  const ConditionProgress = ({ order }: { order: ConditionalOrder }) => {
    const { satisfied, distance } = checkConditionStatus(order);
    const currentPrice = prices[order.symbol]?.price;
    
    if (!currentPrice) {
      return <div className="text-xs text-muted-foreground">가격 정보 없음</div>;
    }

    return (
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span>현재가: {currentPrice.toLocaleString()}원</span>
          <span className={satisfied ? 'text-green-600 font-medium' : 'text-muted-foreground'}>
            {satisfied ? '조건 만족 ✓' : `${distance.toFixed(1)}% 차이`}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-1">
          <div 
            className={`h-1 rounded-full transition-all duration-300 ${
              satisfied ? 'bg-green-500' : distance < 5 ? 'bg-yellow-500' : 'bg-gray-400'
            }`}
            style={{ width: satisfied ? '100%' : `${Math.max(10, 100 - distance)}%` }}
          />
        </div>
      </div>
    );
  };

  // 조건/실행 설명 함수들
  const getConditionDescription = (conditionType: string, value: number) => {
    switch (conditionType) {
      case 'price_above': return `${value.toLocaleString()}원 이상`;
      case 'price_below': return `${value.toLocaleString()}원 이하`;
      case 'rsi_above': return `RSI ${value} 이상`;
      case 'rsi_below': return `RSI ${value} 이하`;
      case 'ma_cross_up': return '골든크로스';
      case 'ma_cross_down': return '데드크로스';
      default: return `${value}`;
    }
  };

  const getActionDescription = (action: string) => {
    switch (action) {
      case 'buy': return '매수';
      case 'sell': return '매도';
      case 'buy_percent': return '비율 매수';
      case 'sell_percent': return '비율 매도';
      default: return action;
    }
  };

  // 초기 로드 및 자동 새로고침
  useEffect(() => {
    refreshOrders();
    refreshPrices();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        refreshOrders();
        refreshPrices();
      }, refreshInterval);
      
      return () => clearInterval(interval);
    }
  }, [userId, autoRefresh, refreshInterval]);

  const activeOrders = orders.filter(order => order.status === 'active');
  const completedOrders = orders.filter(order => order.status === 'completed');

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">조건부 주문 모니터</h3>
          <p className="text-sm text-muted-foreground">
            실시간으로 조건을 확인하고 자동 실행합니다
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-xs text-muted-foreground">
            마지막 업데이트: {lastUpdate}
          </div>
          <Button variant="outline" size="sm" onClick={refreshOrders} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* 요약 통계 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-blue-600">{activeOrders.length}</div>
            <p className="text-sm text-muted-foreground">활성 주문</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold text-green-600">{completedOrders.length}</div>
            <p className="text-sm text-muted-foreground">완료 주문</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="text-2xl font-bold">{Object.keys(prices).length}</div>
            <p className="text-sm text-muted-foreground">모니터링 종목</p>
          </CardContent>
        </Card>
      </div>

      {/* 활성 주문 목록 */}
      {activeOrders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              활성 조건부 주문
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeOrders.map((order) => (
              <div key={order.order_id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <strong className="text-lg">{order.symbol}</strong>
                    <StatusBadge status={order.status} />
                    {order.action === 'buy' ? (
                      <Badge variant="outline" className="text-blue-600">
                        <TrendingUp className="h-3 w-3 mr-1" />
                        매수
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-red-600">
                        <TrendingDown className="h-3 w-3 mr-1" />
                        매도
                      </Badge>
                    )}
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => cancelOrder(order.order_id)}
                  >
                    취소
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <p className="text-sm font-medium">조건</p>
                    <p className="text-sm text-muted-foreground">
                      {getConditionDescription(order.condition_type, order.condition_value)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">실행</p>
                    <p className="text-sm text-muted-foreground">
                      {getActionDescription(order.action)}
                    </p>
                  </div>
                </div>

                {/* 조건 만족도 진행 바 */}
                <ConditionProgress order={order} />

                <div className="text-xs text-muted-foreground">
                  생성: {new Date(order.created_at).toLocaleString()}
                  {order.memo && ` • ${order.memo}`}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 완료된 주문 목록 */}
      {completedOrders.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              완료된 주문
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {completedOrders.slice(-5).map((order) => (
              <div key={order.order_id} className="border rounded-lg p-3 bg-green-50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <strong>{order.symbol}</strong>
                    <StatusBadge status={order.status} />
                  </div>
                  <div className="text-sm text-green-600 font-medium">
                    {order.executed_price?.toLocaleString()}원 체결
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {getConditionDescription(order.condition_type, order.condition_value)} → {getActionDescription(order.action)}
                </div>
                <div className="text-xs text-muted-foreground">
                  실행: {order.completed_at ? new Date(order.completed_at).toLocaleString() : '알 수 없음'}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 주문이 없는 경우 */}
      {orders.length === 0 && !loading && (
        <Card>
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">조건부 주문이 없습니다</h3>
            <p className="text-muted-foreground">
              조건부 주문을 생성하여 자동매매를 시작해보세요
            </p>
          </CardContent>
        </Card>
      )}

      {/* 실시간 알림 */}
      {autoRefresh && (
        <Alert>
          <Zap className="h-4 w-4" />
          <AlertDescription>
            실시간으로 조건을 모니터링하고 있습니다. 
            조건이 만족되면 자동으로 주문이 실행됩니다.
            ({refreshInterval / 1000}초마다 업데이트)
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}