'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  PlayCircle,
  PauseCircle, 
  StopCircle,
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Clock,
  Target,
  AlertCircle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';
import { AutoTradingStatus, AutoTradingConfig } from '@/lib/types/trading-strategy';

interface TradingMonitorProps {
  config: AutoTradingConfig;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
}

export default function TradingMonitor({ config, onStop, onPause, onResume }: TradingMonitorProps) {
  const [status, setStatus] = useState<AutoTradingStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // 목업 데이터 생성
  useEffect(() => {
    const generateMockStatus = (): AutoTradingStatus => ({
      id: 'trading-' + Date.now(),
      config,
      status: Math.random() > 0.3 ? 'running' : 'paused',
      created_at: new Date().toISOString(),
      started_at: new Date(Date.now() - 3600000).toISOString(), // 1시간 전
      
      performance: {
        total_trades: Math.floor(Math.random() * 20) + 5,
        winning_trades: Math.floor(Math.random() * 15) + 3,
        losing_trades: Math.floor(Math.random() * 8) + 1,
        total_return: (Math.random() - 0.3) * 200000,
        total_return_percent: (Math.random() - 0.3) * 15,
        max_drawdown: Math.random() * 8,
        sharpe_ratio: Math.random() * 2 + 0.5,
        current_positions: [
          {
            symbol: config.symbol,
            quantity: Math.floor(Math.random() * 100) + 10,
            avg_price: Math.floor(Math.random() * 10000) + 60000,
            current_price: Math.floor(Math.random() * 10000) + 60000,
            unrealized_pnl: (Math.random() - 0.5) * 50000,
            unrealized_pnl_percent: (Math.random() - 0.5) * 8
          }
        ]
      },
      
      recent_trades: Array.from({ length: 5 }, (_, i) => ({
        id: 'trade-' + i,
        symbol: config.symbol,
        side: Math.random() > 0.5 ? 'buy' : 'sell',
        quantity: Math.floor(Math.random() * 50) + 10,
        price: Math.floor(Math.random() * 10000) + 60000,
        amount: Math.floor(Math.random() * 1000000) + 500000,
        fee: Math.floor(Math.random() * 5000) + 1000,
        executed_at: new Date(Date.now() - Math.random() * 86400000).toISOString(),
        pnl: (Math.random() - 0.5) * 30000,
        pnl_percent: (Math.random() - 0.5) * 5
      }))
    });

    setLoading(true);
    const timer = setTimeout(() => {
      setStatus(generateMockStatus());
      setLoading(false);
    }, 1000);

    // 실시간 업데이트 시뮬레이션
    const interval = setInterval(() => {
      setStatus(prev => prev ? generateMockStatus() : null);
    }, 5000);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [config]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'paused': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'stopped': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'error': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return PlayCircle;
      case 'paused': return PauseCircle;
      case 'stopped': return StopCircle;
      case 'error': return AlertCircle;
      default: return Activity;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running': return '실행 중';
      case 'paused': return '일시정지';
      case 'stopped': return '정지됨';
      case 'error': return '오류';
      default: return status;
    }
  };

  if (loading || !status) {
    return (
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="p-8">
          <div className="flex flex-col items-center space-y-4">
            <div className="relative">
              <RefreshCw className="w-12 h-12 animate-spin text-primary" />
              <div className="absolute inset-0 w-12 h-12 border-4 border-primary/20 rounded-full animate-pulse"></div>
            </div>
            <div className="text-center space-y-2">
              <div className="text-lg font-semibold">🚀 자동매매 시스템 초기화</div>
              <div className="text-sm text-muted-foreground max-w-md">
                실시간 매매 데이터를 로딩하고 모니터링 시스템을 준비하고 있습니다
              </div>
            </div>
            <div className="flex items-center space-x-4 text-xs text-muted-foreground">
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>포지션 확인</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{animationDelay: '0.5s'}}></div>
                <span>거래 내역</span>
              </div>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
                <span>성과 분석</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const StatusIcon = getStatusIcon(status.status);
  const winRate = status.performance.total_trades > 0 
    ? (status.performance.winning_trades / status.performance.total_trades) * 100 
    : 0;

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">자동매매 모니터링</h2>
          <p className="text-muted-foreground">실시간 매매 성과와 상태를 확인하세요</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Badge className={`${getStatusColor(status.status)} flex items-center gap-2`}>
            <StatusIcon className="w-4 h-4" />
            {getStatusText(status.status)}
          </Badge>
          
          <div className="flex space-x-2">
            {status.status === 'running' && (
              <Button variant="outline" onClick={onPause}>
                <PauseCircle className="w-4 h-4 mr-2" />
                일시정지
              </Button>
            )}
            
            {status.status === 'paused' && (
              <Button variant="outline" onClick={onResume}>
                <PlayCircle className="w-4 h-4 mr-2" />
                재개
              </Button>
            )}
            
            <Button variant="destructive" onClick={onStop}>
              <StopCircle className="w-4 h-4 mr-2" />
              정지
            </Button>
          </div>
        </div>
      </div>

      {/* 성과 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">총 수익</p>
                <p className={`text-2xl font-bold ${status.performance.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {status.performance.total_return >= 0 ? '+' : ''}{status.performance.total_return.toLocaleString()}원
                </p>
                <p className="text-xs text-muted-foreground">
                  {status.performance.total_return_percent >= 0 ? '+' : ''}{status.performance.total_return_percent.toFixed(2)}%
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">승률</p>
                <p className="text-2xl font-bold">{winRate.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">
                  {status.performance.winning_trades}승 {status.performance.losing_trades}패
                </p>
              </div>
              <Target className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">총 거래</p>
                <p className="text-2xl font-bold">{status.performance.total_trades}</p>
                <p className="text-xs text-muted-foreground">건</p>
              </div>
              <BarChart3 className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">샤프 지수</p>
                <p className="text-2xl font-bold">{status.performance.sharpe_ratio.toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">위험 대비 수익</p>
              </div>
              <Activity className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="positions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="positions">현재 포지션</TabsTrigger>
          <TabsTrigger value="trades">최근 거래</TabsTrigger>
          <TabsTrigger value="settings">설정 정보</TabsTrigger>
        </TabsList>

        {/* 현재 포지션 */}
        <TabsContent value="positions">
          <Card>
            <CardHeader>
              <CardTitle>현재 포지션</CardTitle>
              <CardDescription>보유 중인 포지션 현황</CardDescription>
            </CardHeader>
            <CardContent>
              {status.performance.current_positions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  현재 보유 중인 포지션이 없습니다.
                </div>
              ) : (
                <div className="space-y-4">
                  {status.performance.current_positions.map((position, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <div className="font-semibold">{position.symbol}</div>
                          <Badge variant="outline">{position.quantity}주</Badge>
                        </div>
                        <div className="mt-1 text-sm text-muted-foreground">
                          평균단가: {position.avg_price.toLocaleString()}원 | 
                          현재가: {position.current_price.toLocaleString()}원
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-semibold ${position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {position.unrealized_pnl >= 0 ? '+' : ''}{position.unrealized_pnl.toLocaleString()}원
                        </div>
                        <div className={`text-sm ${position.unrealized_pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {position.unrealized_pnl_percent >= 0 ? '+' : ''}{position.unrealized_pnl_percent.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 최근 거래 */}
        <TabsContent value="trades">
          <Card>
            <CardHeader>
              <CardTitle>최근 거래 내역</CardTitle>
              <CardDescription>최근 실행된 매매 거래들</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {status.recent_trades.map((trade) => (
                  <div key={trade.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Badge className={trade.side === 'buy' ? 'bg-blue-100 text-blue-800' : 'bg-red-100 text-red-800'}>
                        {trade.side === 'buy' ? '매수' : '매도'}
                      </Badge>
                      <div>
                        <div className="font-medium">{trade.symbol}</div>
                        <div className="text-sm text-muted-foreground">
                          {trade.quantity}주 × {trade.price.toLocaleString()}원
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-sm text-muted-foreground">
                        {new Date(trade.executed_at).toLocaleString()}
                      </div>
                      {trade.pnl !== undefined && (
                        <div className={`text-sm font-medium ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toLocaleString()}원
                          ({trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent?.toFixed(2)}%)
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 설정 정보 */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>현재 자동매매 설정</CardTitle>
              <CardDescription>적용 중인 전략과 리스크 설정</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground">전략</div>
                    <div className="font-medium">{config.strategy_id}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">투자 자본</div>
                    <div className="font-medium">{config.capital.toLocaleString()}원</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">최대 포지션 크기</div>
                    <div className="font-medium">{config.max_position_size}%</div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <div className="text-sm text-muted-foreground">손절 기준</div>
                    <div className="font-medium text-red-600">-{config.stop_loss_percent}%</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">익절 기준</div>
                    <div className="font-medium text-green-600">+{config.take_profit_percent}%</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">거래 시간</div>
                    <div className="font-medium">
                      {config.start_time || '09:00'} ~ {config.end_time || '15:30'}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}