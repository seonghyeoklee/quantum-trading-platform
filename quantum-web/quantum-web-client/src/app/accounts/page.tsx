'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Wallet,
  CreditCard,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Plus,
  ArrowUpRight,
  ArrowDownLeft,
  Building,
  Shield,
  AlertTriangle
} from 'lucide-react';

interface Account {
  id: string;
  accountNumber: string;
  broker: string;
  type: 'STOCK' | 'FUTURES' | 'OPTIONS';
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
  balance: number;
  availableBalance: number;
  totalAssets: number;
  marginUsed: number;
  marginAvailable: number;
}

const mockAccounts: Account[] = [
  {
    id: 'ACC-001',
    accountNumber: '1234-5678-90',
    broker: 'KB증권',
    type: 'STOCK',
    status: 'ACTIVE',
    balance: 2500000,
    availableBalance: 2500000,
    totalAssets: 15750000,
    marginUsed: 0,
    marginAvailable: 5000000
  },
  {
    id: 'ACC-002',
    accountNumber: '9876-5432-10',
    broker: '한국투자증권',
    type: 'STOCK',
    status: 'ACTIVE',
    balance: 1200000,
    availableBalance: 800000,
    totalAssets: 8500000,
    marginUsed: 400000,
    marginAvailable: 2000000
  }
];

export default function AccountsPage() {
  const formatCurrency = (amount: number) => `₩${amount.toLocaleString()}`;

  const getStatusColor = (status: Account['status']) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800';
      case 'INACTIVE':
        return 'bg-gray-100 text-gray-800';
      case 'SUSPENDED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type: Account['type']) => {
    switch (type) {
      case 'STOCK':
        return 'bg-blue-100 text-blue-800';
      case 'FUTURES':
        return 'bg-purple-100 text-purple-800';
      case 'OPTIONS':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const totalBalance = mockAccounts.reduce((sum, acc) => sum + acc.balance, 0);
  const totalAssets = mockAccounts.reduce((sum, acc) => sum + acc.totalAssets, 0);
  const totalAvailable = mockAccounts.reduce((sum, acc) => sum + acc.availableBalance, 0);

  return (
    <ProtectedRoute requiredRoles={['ADMIN', 'MANAGER']}>
      <AdminLayout>
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">계좌 관리</h1>
              <p className="text-muted-foreground">
                연결된 브로커 계좌들을 관리하고 모니터링하세요.
              </p>
            </div>
            <div className="flex gap-2 mt-4 sm:mt-0">
              <Button variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </Button>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                계좌 추가
              </Button>
            </div>
          </div>

          {/* 계좌 요약 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">총 자산</CardTitle>
                <Wallet className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(totalAssets)}</div>
                <p className="text-xs text-muted-foreground">모든 계좌 합계</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">현금 잔고</CardTitle>
                <CreditCard className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(totalBalance)}</div>
                <p className="text-xs text-muted-foreground">투자 가능 현금</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">가용 잔고</CardTitle>
                <TrendingUp className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatCurrency(totalAvailable)}</div>
                <p className="text-xs text-muted-foreground">즉시 거래 가능</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">연결 계좌</CardTitle>
                <Building className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{mockAccounts.length}</div>
                <p className="text-xs text-muted-foreground">활성 브로커 계좌</p>
              </CardContent>
            </Card>
          </div>

          {/* 계좌 목록 */}
          <Card>
            <CardHeader>
              <CardTitle>브로커 계좌 목록</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockAccounts.map((account) => (
                  <div
                    key={account.id}
                    className="p-6 bg-gray-50 rounded-lg border"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                          <Building className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{account.broker}</span>
                            <Badge className={getStatusColor(account.status)}>
                              {account.status}
                            </Badge>
                            <Badge className={getTypeColor(account.type)}>
                              {account.type}
                            </Badge>
                          </div>
                          <div className="text-sm text-gray-600">
                            계좌번호: {account.accountNumber}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          설정
                        </Button>
                        <Button variant="outline" size="sm">
                          거래 내역
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="space-y-1">
                        <div className="text-xs text-gray-500">총 자산</div>
                        <div className="font-semibold">{formatCurrency(account.totalAssets)}</div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-gray-500">현금 잔고</div>
                        <div className="font-semibold">{formatCurrency(account.balance)}</div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-gray-500">가용 잔고</div>
                        <div className="font-semibold text-green-600">
                          {formatCurrency(account.availableBalance)}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-gray-500">증거금 사용</div>
                        <div className="font-semibold">
                          {formatCurrency(account.marginUsed)}
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <div className="text-xs text-gray-500">증거금 한도</div>
                        <div className="font-semibold text-blue-600">
                          {formatCurrency(account.marginAvailable)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 계좌 관리 기능 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <ArrowUpRight className="h-5 w-5 mr-2 text-green-600" />
                  입금 관리
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      입금 계좌 선택
                    </label>
                    <select className="w-full p-2 border border-gray-300 rounded-md">
                      <option value="">계좌를 선택하세요</option>
                      {mockAccounts.map(account => (
                        <option key={account.id} value={account.id}>
                          {account.broker} - {account.accountNumber}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      입금 금액
                    </label>
                    <input
                      type="number"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="입금할 금액을 입력하세요"
                    />
                  </div>

                  <Button className="w-full">
                    입금 신청
                  </Button>
                  
                  <div className="text-xs text-gray-500">
                    • 입금은 영업일 기준 1-2일 소요됩니다
                    • 최소 입금 금액: 10,000원
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <ArrowDownLeft className="h-5 w-5 mr-2 text-blue-600" />
                  출금 관리
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      출금 계좌 선택
                    </label>
                    <select className="w-full p-2 border border-gray-300 rounded-md">
                      <option value="">계좌를 선택하세요</option>
                      {mockAccounts.map(account => (
                        <option key={account.id} value={account.id}>
                          {account.broker} - {account.accountNumber}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      출금 금액
                    </label>
                    <input
                      type="number"
                      className="w-full p-2 border border-gray-300 rounded-md"
                      placeholder="출금할 금액을 입력하세요"
                    />
                  </div>

                  <Button className="w-full" variant="outline">
                    출금 신청
                  </Button>
                  
                  <div className="text-xs text-gray-500">
                    • 출금은 영업일 기준 1-2일 소요됩니다
                    • 최소 출금 금액: 10,000원
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 보안 및 알림 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center">
                <Shield className="h-5 w-5 mr-2" />
                보안 및 알림 설정
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">보안 설정</h4>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">2단계 인증</span>
                    </div>
                    <Badge className="bg-green-100 text-green-800">활성</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium">API 키 암호화</span>
                    </div>
                    <Badge className="bg-green-100 text-green-800">활성</Badge>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">알림 설정</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">대량 거래 알림</span>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm">잔고 부족 알림</span>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm">계좌 상태 변경 알림</span>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </AdminLayout>
    </ProtectedRoute>
  );
}