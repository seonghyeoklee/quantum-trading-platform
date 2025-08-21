'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, TrendingDown, PieChart, Activity, RefreshCw } from 'lucide-react';
import { useWebSocket } from '@/lib/websocket';
import { apiClient } from '@/lib/api-client';

const Chart = dynamic(() => import('react-apexcharts'), { 
  ssr: false,
  loading: () => <div className="h-80 flex items-center justify-center">Loading chart...</div>
});

interface PortfolioChartProps {
  portfolioId: string;
  height?: number;
}

interface PortfolioData {
  portfolioId: string;
  totalValue: number;
  cashBalance: number;
  unrealizedPnL: number;
  realizedPnL: number;
  updateTime: string;
}

interface PnLDataPoint {
  date: string;
  portfolioValue: number;
  dailyPnL: number;
  cumulativePnL: number;
}

interface PositionData {
  symbol: string;
  symbolName: string;
  marketValue: number;
  weightPercent: number;
  unrealizedPnL: number;
  unrealizedPnLPercent: number;
}

export const PortfolioChart: React.FC<PortfolioChartProps> = ({
  portfolioId,
  height = 350,
}) => {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [pnlHistory, setPnlHistory] = useState<PnLDataPoint[]>([]);
  const [positions, setPositions] = useState<PositionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'performance' | 'allocation' | 'pnl'>('performance');

  const { subscribeToPortfolio, isConnected } = useWebSocket();

  // 초기 데이터 로드
  useEffect(() => {
    const loadPortfolioData = async () => {
      try {
        setLoading(true);
        
        // 포트폴리오 기본 정보, P&L 히스토리, 포지션 데이터 병렬 로드
        const [portfolioResponse, pnlResponse, positionsResponse] = await Promise.all([
          apiClient.getPortfolio(portfolioId),
          apiClient.getPortfolioPnL(portfolioId, 30, 'daily'),
          apiClient.getPositions(portfolioId)
        ]);

        setPortfolioData(portfolioResponse);
        setPnlHistory(pnlResponse.dataPoints || []);
        setPositions(positionsResponse.slice(0, 8)); // 상위 8개 포지션만 표시
        
      } catch (error) {
        console.error('Failed to load portfolio data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadPortfolioData();
  }, [portfolioId]);

  // WebSocket 실시간 포트폴리오 업데이트 구독
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = subscribeToPortfolio(portfolioId, (data) => {
      if (data.type === 'PORTFOLIO_UPDATE') {
        setPortfolioData(prev => ({
          ...prev,
          ...data.data,
        }));
      }
    });

    return unsubscribe;
  }, [portfolioId, isConnected, subscribeToPortfolio]);

  const refreshData = async () => {
    setRefreshing(true);
    try {
      const [portfolioResponse, pnlResponse, positionsResponse] = await Promise.all([
        apiClient.getPortfolio(portfolioId),
        apiClient.getPortfolioPnL(portfolioId, 30, 'daily'),
        apiClient.getPositions(portfolioId)
      ]);

      setPortfolioData(portfolioResponse);
      setPnlHistory(pnlResponse.dataPoints || []);
      setPositions(positionsResponse.slice(0, 8));
    } catch (error) {
      console.error('Failed to refresh portfolio data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // 성과 차트 옵션
  const performanceChartOptions = {
    chart: {
      type: 'area',
      height: height,
      toolbar: { show: false },
      zoom: { enabled: false },
    },
    dataLabels: { enabled: false },
    stroke: {
      curve: 'smooth',
      width: 2,
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.3,
        stops: [0, 90, 100]
      }
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeFormatter: {
          day: 'dd MMM'
        }
      }
    },
    yaxis: {
      labels: {
        formatter: (value: number) => `₩${(value / 1000000).toFixed(1)}M`
      }
    },
    tooltip: {
      x: {
        format: 'dd MMM yyyy'
      },
      y: {
        formatter: (value: number) => `₩${value.toLocaleString()}`
      }
    },
    grid: {
      borderColor: '#e7e7e7',
    },
    colors: ['#3B82F6']
  };

  const performanceChartSeries = [{
    name: 'Portfolio Value',
    data: pnlHistory.map(point => ({
      x: new Date(point.date).getTime(),
      y: point.portfolioValue
    }))
  }];

  // 자산 배분 차트 옵션
  const allocationChartOptions = {
    chart: {
      type: 'donut',
      height: height,
    },
    labels: [...positions.map(p => p.symbolName), '현금'],
    colors: [
      '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', 
      '#EC4899', '#06B6D4', '#84CC16', '#6B7280'
    ],
    plotOptions: {
      pie: {
        donut: {
          size: '60%',
          labels: {
            show: true,
            total: {
              show: true,
              label: 'Total Value',
              formatter: () => `₩${portfolioData?.totalValue.toLocaleString() || 0}`
            }
          }
        }
      }
    },
    dataLabels: {
      enabled: true,
      formatter: (val: number) => `${val.toFixed(1)}%`
    },
    legend: {
      position: 'bottom'
    }
  };

  const allocationChartSeries = [
    ...positions.map(p => p.marketValue),
    portfolioData?.cashBalance || 0
  ];

  // P&L 차트 옵션
  const pnlChartOptions = {
    chart: {
      type: 'bar',
      height: height,
      toolbar: { show: false },
    },
    plotOptions: {
      bar: {
        colors: {
          ranges: [{
            from: -Infinity,
            to: 0,
            color: '#EF4444'
          }, {
            from: 0,
            to: Infinity,
            color: '#10B981'
          }]
        }
      }
    },
    dataLabels: { enabled: false },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeFormatter: {
          day: 'dd MMM'
        }
      }
    },
    yaxis: {
      labels: {
        formatter: (value: number) => `₩${(value / 1000).toFixed(0)}K`
      }
    },
    tooltip: {
      x: {
        format: 'dd MMM yyyy'
      },
      y: {
        formatter: (value: number) => `₩${value.toLocaleString()}`
      }
    }
  };

  const pnlChartSeries = [{
    name: 'Daily P&L',
    data: pnlHistory.map(point => ({
      x: new Date(point.date).getTime(),
      y: point.dailyPnL
    }))
  }];

  const formatCurrency = (value: number) => `₩${value.toLocaleString()}`;
  const formatPercent = (value: number) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* 포트폴리오 요약 */}
      {portfolioData && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">포트폴리오 현황</CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant={isConnected ? "default" : "secondary"}>
                  <Activity size={12} className="mr-1" />
                  {isConnected ? "실시간" : "연결 중"}
                </Badge>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={refreshData}
                  disabled={refreshing}
                >
                  <RefreshCw size={14} className={`mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                  새로고침
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">총 자산</p>
                <p className="text-2xl font-bold">{formatCurrency(portfolioData.totalValue)}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">평가손익</p>
                <div className={`flex items-center gap-1 ${
                  portfolioData.unrealizedPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {portfolioData.unrealizedPnL >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  <span className="text-lg font-semibold">
                    {formatCurrency(portfolioData.unrealizedPnL)}
                  </span>
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">실현손익</p>
                <div className={`text-lg font-semibold ${
                  portfolioData.realizedPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(portfolioData.realizedPnL)}
                </div>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">현금 잔고</p>
                <p className="text-lg font-semibold">{formatCurrency(portfolioData.cashBalance)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 차트 탭 */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="performance">성과 추이</TabsTrigger>
              <TabsTrigger value="allocation">자산 배분</TabsTrigger>
              <TabsTrigger value="pnl">일별 손익</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)}>
            <TabsContent value="performance">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">포트폴리오 가치 추이</h3>
                  <span className="text-sm text-muted-foreground">최근 30일</span>
                </div>
                <Chart
                  options={performanceChartOptions}
                  series={performanceChartSeries}
                  type="area"
                  height={height}
                />
              </div>
            </TabsContent>
            
            <TabsContent value="allocation">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">자산 배분</h3>
                  <Chart
                    options={allocationChartOptions}
                    series={allocationChartSeries}
                    type="donut"
                    height={height}
                  />
                </div>
                <div>
                  <h3 className="text-lg font-semibold mb-4">보유 종목</h3>
                  <div className="space-y-3">
                    {positions.map((position, index) => (
                      <div key={position.symbol} className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <div className="font-semibold">{position.symbolName}</div>
                          <div className="text-sm text-muted-foreground">{position.symbol}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">{formatCurrency(position.marketValue)}</div>
                          <div className="text-sm">
                            <span className="text-muted-foreground">{position.weightPercent.toFixed(1)}%</span>
                            <span className={`ml-2 ${
                              position.unrealizedPnLPercent >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {formatPercent(position.unrealizedPnLPercent)}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="pnl">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">일별 손익 현황</h3>
                  <span className="text-sm text-muted-foreground">최근 30일</span>
                </div>
                <Chart
                  options={pnlChartOptions}
                  series={pnlChartSeries}
                  type="bar"
                  height={height}
                />
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default PortfolioChart;