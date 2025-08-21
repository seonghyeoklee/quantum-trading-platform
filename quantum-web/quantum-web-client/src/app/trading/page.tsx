'use client';

import React, { useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Plus,
  RefreshCw,
  Filter,
  Search
} from 'lucide-react';

interface Order {
  id: string;
  symbol: string;
  symbolName: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  status: 'PENDING' | 'SUBMITTED' | 'FILLED' | 'CANCELLED' | 'REJECTED';
  quantity: number;
  price?: number;
  filledQuantity: number;
  averagePrice?: number;
  createdAt: string;
  updatedAt: string;
}

const mockOrders: Order[] = [
  {
    id: 'ORDER-001',
    symbol: '005930',
    symbolName: '삼성전자',
    side: 'BUY',
    type: 'LIMIT',
    status: 'FILLED',
    quantity: 100,
    price: 72000,
    filledQuantity: 100,
    averagePrice: 71950,
    createdAt: '2024-01-15T09:30:00Z',
    updatedAt: '2024-01-15T09:35:00Z'
  },
  {
    id: 'ORDER-002',
    symbol: '000660',
    symbolName: 'SK하이닉스',
    side: 'SELL',
    type: 'MARKET',
    status: 'PENDING',
    quantity: 50,
    filledQuantity: 0,
    createdAt: '2024-01-15T10:15:00Z',
    updatedAt: '2024-01-15T10:15:00Z'
  },
  {
    id: 'ORDER-003',
    symbol: '035420',
    symbolName: 'NAVER',
    side: 'BUY',
    type: 'LIMIT',
    status: 'SUBMITTED',
    quantity: 30,
    price: 185000,
    filledQuantity: 0,
    createdAt: '2024-01-15T11:00:00Z',
    updatedAt: '2024-01-15T11:00:00Z'
  }
];

export default function TradingPage() {
  const [orders, setOrders] = useState<Order[]>(mockOrders);
  const [filter, setFilter] = useState<'all' | 'active' | 'filled' | 'cancelled'>('all');

  const getStatusIcon = (status: Order['status']) => {
    switch (status) {
      case 'FILLED':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'PENDING':
      case 'SUBMITTED':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'CANCELLED':
        return <XCircle className="h-4 w-4 text-gray-600" />;
      case 'REJECTED':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: Order['status']) => {
    switch (status) {
      case 'FILLED':
        return 'bg-green-100 text-green-800';
      case 'PENDING':
      case 'SUBMITTED':
        return 'bg-blue-100 text-blue-800';
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-800';
      case 'REJECTED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSideColor = (side: Order['side']) => {
    return side === 'BUY' ? 'text-red-600' : 'text-blue-600';
  };

  const formatCurrency = (amount: number) => `₩${amount.toLocaleString()}`;
  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR');
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    if (filter === 'active') return ['PENDING', 'SUBMITTED'].includes(order.status);
    if (filter === 'filled') return order.status === 'FILLED';
    if (filter === 'cancelled') return ['CANCELLED', 'REJECTED'].includes(order.status);
    return true;
  });

  return (
    <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER', 'TRADER']}>
      <AdminLayout>
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">거래 관리</h1>
              <p className="text-muted-foreground">
                주문 생성, 취소 및 거래 내역을 관리하세요.
              </p>
            </div>
            <div className="flex gap-2 mt-4 sm:mt-0">
              <Button variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </Button>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                새 주문
              </Button>
            </div>
          </div>

          {/* 거래 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">활성 주문</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {orders.filter(o => ['PENDING', 'SUBMITTED'].includes(o.status)).length}
                </div>
                <p className="text-xs text-muted-foreground">대기 중인 주문</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">체결 완료</CardTitle>
                <CheckCircle className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {orders.filter(o => o.status === 'FILLED').length}
                </div>
                <p className="text-xs text-muted-foreground">오늘 체결된 주문</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">총 거래량</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">180</div>
                <p className="text-xs text-muted-foreground">오늘 거래된 주식 수</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">거래 금액</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">₩13.2M</div>
                <p className="text-xs text-muted-foreground">오늘 총 거래액</p>
              </CardContent>
            </Card>
          </div>

          {/* 주문 관리 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>주문 내역</CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    필터
                  </Button>
                  <Button variant="outline" size="sm">
                    <Search className="h-4 w-4 mr-2" />
                    검색
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs value={filter} onValueChange={(value) => setFilter(value as any)}>
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="all">전체</TabsTrigger>
                  <TabsTrigger value="active">활성</TabsTrigger>
                  <TabsTrigger value="filled">체결</TabsTrigger>
                  <TabsTrigger value="cancelled">취소</TabsTrigger>
                </TabsList>

                <TabsContent value={filter} className="space-y-4 mt-6">
                  <div className="space-y-3">
                    {filteredOrders.map((order) => (
                      <div
                        key={order.id}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border"
                      >
                        <div className="flex items-center gap-4">
                          {getStatusIcon(order.status)}
                          
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{order.symbolName}</span>
                              <Badge variant="secondary" className="text-xs">
                                {order.symbol}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <span className={getSideColor(order.side)}>
                                {order.side === 'BUY' ? '매수' : '매도'}
                              </span>
                              <span>•</span>
                              <span>{order.type}</span>
                              <span>•</span>
                              <span>{order.quantity}주</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <div className="font-medium">
                              {order.price ? formatCurrency(order.price) : '시장가'}
                            </div>
                            {order.averagePrice && (
                              <div className="text-sm text-gray-600">
                                체결: {formatCurrency(order.averagePrice)}
                              </div>
                            )}
                          </div>

                          <div className="text-right">
                            <Badge className={getStatusColor(order.status)}>
                              {order.status}
                            </Badge>
                            <div className="text-xs text-gray-500 mt-1">
                              {order.filledQuantity}/{order.quantity}
                            </div>
                          </div>

                          <div className="text-right min-w-24">
                            <div className="text-xs text-gray-500">
                              생성: {formatTime(order.createdAt).split(' ')[1]}
                            </div>
                            {order.updatedAt !== order.createdAt && (
                              <div className="text-xs text-gray-500">
                                수정: {formatTime(order.updatedAt).split(' ')[1]}
                              </div>
                            )}
                          </div>

                          <div className="flex gap-2">
                            {['PENDING', 'SUBMITTED'].includes(order.status) && (
                              <Button variant="outline" size="sm">
                                취소
                              </Button>
                            )}
                            <Button variant="outline" size="sm">
                              상세
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}

                    {filteredOrders.length === 0 && (
                      <div className="text-center py-12">
                        <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                        <p className="text-gray-600">해당 조건의 주문이 없습니다.</p>
                      </div>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* 빠른 거래 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
                  빠른 매수
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      종목 선택
                    </label>
                    <select className="w-full p-2 border border-gray-300 rounded-md">
                      <option value="">종목을 선택하세요</option>
                      <option value="005930">삼성전자 (005930)</option>
                      <option value="000660">SK하이닉스 (000660)</option>
                      <option value="035420">NAVER (035420)</option>
                    </select>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        수량
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 rounded-md"
                        placeholder="주식 수"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        가격
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 rounded-md"
                        placeholder="원"
                      />
                    </div>
                  </div>

                  <Button className="w-full bg-red-600 hover:bg-red-700">
                    매수 주문
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <TrendingDown className="h-5 w-5 mr-2 text-blue-600" />
                  빠른 매도
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      보유 종목
                    </label>
                    <select className="w-full p-2 border border-gray-300 rounded-md">
                      <option value="">매도할 종목을 선택하세요</option>
                      <option value="005930">삼성전자 (100주 보유)</option>
                      <option value="000660">SK하이닉스 (50주 보유)</option>
                      <option value="035420">NAVER (30주 보유)</option>
                    </select>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        수량
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 rounded-md"
                        placeholder="주식 수"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        가격
                      </label>
                      <input
                        type="number"
                        className="w-full p-2 border border-gray-300 rounded-md"
                        placeholder="원"
                      />
                    </div>
                  </div>

                  <Button className="w-full bg-blue-600 hover:bg-blue-700">
                    매도 주문
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}