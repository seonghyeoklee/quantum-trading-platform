'use client';

import { useState, useEffect, useMemo } from 'react';
import { Check, X, Clock, TrendingUp, TrendingDown, AlertCircle, DollarSign } from 'lucide-react';
import { RealtimeOrderExecutionData } from '@/lib/api/websocket-types';

interface OrderExecutionHistoryProps {
  orderExecutions: RealtimeOrderExecutionData[];
  className?: string;
  maxItems?: number; // 최대 표시 개수 (기본값: 50)
}

export default function OrderExecutionHistory({ 
  orderExecutions, 
  className, 
  maxItems = 50 
}: OrderExecutionHistoryProps) {
  const [animatedOrders, setAnimatedOrders] = useState<Set<string>>(new Set());

  // 최신 주문체결 내역만 표시 (시간 역순 정렬)
  const displayOrders = useMemo(() => {
    return [...orderExecutions]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, maxItems);
  }, [orderExecutions, maxItems]);

  // 새로운 주문체결 내역 애니메이션 (성능 최적화)
  useEffect(() => {
    if (displayOrders.length > 0) {
      const latestOrder = displayOrders[0]; // 시간 역순이므로 최신이 첫 번째
      const orderId = latestOrder.id;
      
      // 이미 애니메이션 중인 주문은 스킵
      if (!animatedOrders.has(orderId)) {
        setAnimatedOrders(prev => new Set(prev).add(orderId));
        
        // 2초 후 애니메이션 제거
        const timer = setTimeout(() => {
          setAnimatedOrders(prev => {
            const newSet = new Set(prev);
            newSet.delete(orderId);
            return newSet;
          });
        }, 2000);
        
        return () => clearTimeout(timer);
      }
    }
  }, [displayOrders.length, animatedOrders]);

  // 가격 포맷 함수
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  // 수량 포맷 함수
  const formatQuantity = (quantity: number) => {
    return quantity.toLocaleString('ko-KR');
  };

  // 시간 포맷 함수 (HH:mm:ss)
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // 주문 상태에 따른 색상 및 아이콘
  const getOrderStatusInfo = (status: string) => {
    switch (status) {
      case '접수':
        return { 
          color: 'text-blue-600', 
          bgColor: 'bg-blue-50 dark:bg-blue-900/10',
          icon: <Clock className="w-3 h-3" />,
          text: '접수'
        };
      case '체결':
        return { 
          color: 'text-green-600', 
          bgColor: 'bg-green-50 dark:bg-green-900/10',
          icon: <Check className="w-3 h-3" />,
          text: '체결'
        };
      case '취소':
      case '거부':
        return { 
          color: 'text-red-600', 
          bgColor: 'bg-red-50 dark:bg-red-900/10',
          icon: <X className="w-3 h-3" />,
          text: status
        };
      default:
        return { 
          color: 'text-gray-600', 
          bgColor: 'bg-gray-50 dark:bg-gray-900/10',
          icon: <AlertCircle className="w-3 h-3" />,
          text: status || '대기'
        };
    }
  };

  // 주문 타입 색상
  const getOrderTypeColor = (orderType: 'buy' | 'sell') => {
    return orderType === 'buy' ? 'text-red-600' : 'text-blue-600';
  };

  // 주문 타입 아이콘
  const getOrderTypeIcon = (orderType: 'buy' | 'sell') => {
    return orderType === 'buy' 
      ? <TrendingUp className="w-3 h-3" />
      : <TrendingDown className="w-3 h-3" />;
  };

  if (!orderExecutions || orderExecutions.length === 0) {
    return (
      <div className={`border rounded-lg bg-background ${className || ''}`}>
        <div className="p-3 border-b border-border bg-muted/50">
          <h3 className="font-semibold text-sm">주문체결 내역</h3>
        </div>
        <div className="p-4 text-center text-sm text-muted-foreground">
          주문체결 내역이 없습니다
        </div>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg bg-background ${className || ''}`}>
      {/* 헤더 */}
      <div className="p-3 border-b border-border bg-muted/50">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">주문체결 내역</h3>
          <div className="text-xs text-muted-foreground">
            최근 {displayOrders.length}건
          </div>
        </div>
      </div>

      {/* 컬럼 헤더 */}
      <div className="px-3 py-2 border-b border-border bg-muted/20">
        <div className="grid grid-cols-8 gap-2 text-xs font-medium text-muted-foreground">
          <div className="text-center">시간</div>
          <div className="text-left">종목</div>
          <div className="text-center">구분</div>
          <div className="text-center">상태</div>
          <div className="text-right">수량</div>
          <div className="text-right">가격</div>
          <div className="text-right">체결가</div>
          <div className="text-right">미체결</div>
        </div>
      </div>

      {/* 주문체결 내역 리스트 */}
      <div className="max-h-96 overflow-y-auto">
        {displayOrders.map((order) => {
          const isAnimated = animatedOrders.has(order.id);
          const statusInfo = getOrderStatusInfo(order.orderStatus);
          
          return (
            <div 
              key={order.id}
              className={`
                grid grid-cols-8 gap-2 items-center px-3 py-2 text-xs border-b border-border/50 last:border-b-0
                hover:bg-muted/50 transition-all duration-500
                ${isAnimated ? 'bg-yellow-50 dark:bg-yellow-900/10 border-l-4 border-l-yellow-400' : ''}
              `}
            >
              {/* 체결 시간 */}
              <div className="text-center text-muted-foreground">
                {formatTime(order.timestamp)}
              </div>

              {/* 종목 정보 */}
              <div className="text-left">
                <div className="font-medium">{order.symbolName}</div>
                <div className="text-muted-foreground">{order.symbol}</div>
              </div>

              {/* 주문 구분 */}
              <div className={`flex items-center justify-center ${getOrderTypeColor(order.orderType)}`}>
                <span className="mr-1">{getOrderTypeIcon(order.orderType)}</span>
                <span className="text-xs font-medium">
                  {order.orderType === 'buy' ? '매수' : '매도'}
                </span>
              </div>

              {/* 주문 상태 */}
              <div className="flex items-center justify-center">
                <div className={`flex items-center px-2 py-1 rounded-full ${statusInfo.bgColor}`}>
                  <span className={`mr-1 ${statusInfo.color}`}>
                    {statusInfo.icon}
                  </span>
                  <span className={`text-xs font-medium ${statusInfo.color}`}>
                    {statusInfo.text}
                  </span>
                </div>
              </div>

              {/* 주문 수량 */}
              <div className="text-right font-mono">
                {formatQuantity(order.orderQuantity)}
              </div>

              {/* 주문 가격 */}
              <div className="text-right font-mono">
                {order.orderPrice > 0 ? formatPrice(order.orderPrice) : order.orderMethod}
              </div>

              {/* 체결 가격 */}
              <div className="text-right font-mono">
                {order.executedPrice ? (
                  <span className="text-green-600 font-medium">
                    {formatPrice(order.executedPrice)}
                  </span>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </div>

              {/* 미체결 수량 */}
              <div className="text-right font-mono">
                {order.remainingQuantity > 0 ? (
                  <span className="text-orange-600">
                    {formatQuantity(order.remainingQuantity)}
                  </span>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 통계 정보 */}
      <div className="p-3 border-t border-border bg-muted/20">
        <div className="grid grid-cols-3 gap-4 text-xs">
          <div className="space-y-1">
            <div className="text-muted-foreground">총 주문 건수</div>
            <div className="font-medium">{orderExecutions.length.toLocaleString('ko-KR')}건</div>
          </div>
          <div className="space-y-1">
            <div className="text-muted-foreground">체결 완료</div>
            <div className="font-medium text-green-600">
              {orderExecutions.filter(order => order.orderStatus === '체결').length}건
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-muted-foreground">미체결</div>
            <div className="font-medium text-orange-600">
              {orderExecutions.filter(order => order.remainingQuantity > 0).length}건
            </div>
          </div>
        </div>

        {/* 매수/매도 비율 */}
        {orderExecutions.length > 0 && (
          <div className="mt-3">
            <div className="text-xs text-muted-foreground mb-2">주문 구분</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="text-center">
                <div className="text-red-600 font-medium">
                  {orderExecutions.filter(order => order.orderType === 'buy').length}
                </div>
                <div className="text-muted-foreground">매수</div>
              </div>
              <div className="text-center">
                <div className="text-blue-600 font-medium">
                  {orderExecutions.filter(order => order.orderType === 'sell').length}
                </div>
                <div className="text-muted-foreground">매도</div>
              </div>
            </div>
          </div>
        )}

        {/* 수수료 및 세금 정보 */}
        {orderExecutions.some(order => order.commission > 0 || order.tax > 0) && (
          <div className="mt-3 pt-3 border-t border-border">
            <div className="flex items-center text-xs text-muted-foreground mb-2">
              <DollarSign className="w-3 h-3 mr-1" />
              <span>비용 정보</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="text-center">
                <div className="font-medium">
                  {formatPrice(orderExecutions.reduce((sum, order) => sum + order.commission, 0))}
                </div>
                <div className="text-muted-foreground">총 수수료</div>
              </div>
              <div className="text-center">
                <div className="font-medium">
                  {formatPrice(orderExecutions.reduce((sum, order) => sum + order.tax, 0))}
                </div>
                <div className="text-muted-foreground">총 세금</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}