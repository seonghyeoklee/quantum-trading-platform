'use client';

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Clock,
  PlayCircle,
  StopCircle,
  CheckCircle2,
  AlertCircle,
  Loader2
} from "lucide-react";

// 백테스팅 가능 종목 리스트
const AVAILABLE_SYMBOLS = [
  { code: '005930', name: '삼성전자', sector: 'IT' },
  { code: '035720', name: '카카오', sector: 'IT' },
  { code: '009540', name: 'HD한국조선해양', sector: '조선' },
  { code: '012450', name: '한화에어로스페이스', sector: '방산' },
  { code: '010060', name: 'OCI', sector: '원자력' }
];

interface BacktestingRequest {
  symbols: string[];
  periods: number[];
  initial_cash: number;
  commission: number;
}

interface BacktestingResult {
  symbol: string;
  name: string;
  optimal_days: number;
  return: number;
  initial: number;
  final: number;
}

interface BacktestingStatus {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_stock: string | null;
  message: string;
  results: BacktestingResult[] | null;
}

export default function BacktestingPage() {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['005930', '035720']);
  const [initialCash, setInitialCash] = useState(10000000);
  const [commission, setCommission] = useState(0.00015);
  const [periods] = useState([1, 2, 3, 5, 7]);
  
  const [isRunning, setIsRunning] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<BacktestingStatus | null>(null);
  const [results, setResults] = useState<BacktestingResult[] | null>(null);

  // 백테스팅 시작
  const startBacktesting = async () => {
    try {
      setIsRunning(true);
      setResults(null);
      
      const request: BacktestingRequest = {
        symbols: selectedSymbols,
        periods,
        initial_cash: initialCash,
        commission
      };

      const response = await fetch('/api/kis/backtesting/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setCurrentTaskId(data.task_id);
      
      // 진행 상황 폴링 시작
      pollStatus(data.task_id);
      
    } catch (error) {
      console.error('백테스팅 시작 실패:', error);
      setIsRunning(false);
      alert('백테스팅 시작에 실패했습니다.');
    }
  };

  // 상태 폴링
  const pollStatus = async (taskId: string) => {
    try {
      const response = await fetch(`/api/kis/backtesting/status/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const statusData: BacktestingStatus = await response.json();
      setStatus(statusData);

      if (statusData.status === 'completed') {
        setResults(statusData.results);
        setIsRunning(false);
      } else if (statusData.status === 'failed') {
        setIsRunning(false);
        alert(`백테스팅 실패: ${statusData.message}`);
      } else if (statusData.status === 'running' || statusData.status === 'pending') {
        // 2초 후 다시 폴링
        setTimeout(() => pollStatus(taskId), 2000);
      }

    } catch (error) {
      console.error('상태 조회 실패:', error);
      setIsRunning(false);
    }
  };

  // 종목 선택 핸들러
  const handleSymbolToggle = (symbolCode: string) => {
    setSelectedSymbols(prev => 
      prev.includes(symbolCode) 
        ? prev.filter(s => s !== symbolCode)
        : [...prev, symbolCode]
    );
  };

  // 상태별 아이콘
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-2">
          골든크로스 백테스팅
        </h1>
        <p className="text-muted-foreground">
          SMA5와 SMA20을 활용한 골든크로스 전략의 백테스팅을 실행합니다.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 설정 패널 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              백테스팅 설정
            </CardTitle>
            <CardDescription>
              백테스팅할 종목과 설정을 선택하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* 종목 선택 */}
            <div>
              <Label className="text-sm font-medium mb-3 block">테스트 종목 선택</Label>
              <div className="grid grid-cols-1 gap-2">
                {AVAILABLE_SYMBOLS.map((symbol) => (
                  <div key={symbol.code} className="flex items-center space-x-2 p-2 border rounded-md">
                    <Checkbox
                      id={symbol.code}
                      checked={selectedSymbols.includes(symbol.code)}
                      onCheckedChange={() => handleSymbolToggle(symbol.code)}
                    />
                    <Label
                      htmlFor={symbol.code}
                      className="flex-1 flex items-center justify-between cursor-pointer"
                    >
                      <span>{symbol.name} ({symbol.code})</span>
                      <Badge variant="secondary" className="text-xs">
                        {symbol.sector}
                      </Badge>
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            {/* 설정값 */}
            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label htmlFor="initial_cash">초기 자금 (원)</Label>
                <Input
                  id="initial_cash"
                  type="number"
                  value={initialCash}
                  onChange={(e) => setInitialCash(parseInt(e.target.value))}
                  min={1000000}
                  step={1000000}
                />
              </div>
              <div>
                <Label htmlFor="commission">수수료 (%)</Label>
                <Input
                  id="commission"
                  type="number"
                  value={commission * 100}
                  onChange={(e) => setCommission(parseFloat(e.target.value) / 100)}
                  min={0}
                  max={1}
                  step={0.001}
                />
              </div>
            </div>

            {/* 확정 기간 정보 */}
            <div>
              <Label className="text-sm font-medium mb-2 block">확정 기간</Label>
              <div className="flex gap-2 flex-wrap">
                {periods.map((period) => (
                  <Badge key={period} variant="outline">
                    {period}일
                  </Badge>
                ))}
              </div>
            </div>

            {/* 실행 버튼 */}
            <Button 
              onClick={startBacktesting} 
              disabled={isRunning || selectedSymbols.length === 0}
              className="w-full"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  백테스팅 실행 중...
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4 mr-2" />
                  백테스팅 시작
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* 진행 상황 패널 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {status && getStatusIcon(status.status)}
              진행 상황
            </CardTitle>
            <CardDescription>
              백테스팅 실행 상태를 실시간으로 확인합니다
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {status ? (
              <>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>진행률</span>
                    <span>{status.progress}%</span>
                  </div>
                  <Progress value={status.progress} />
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">상태:</span>
                    <Badge variant={
                      status.status === 'completed' ? 'default' :
                      status.status === 'failed' ? 'destructive' :
                      status.status === 'running' ? 'secondary' : 'outline'
                    }>
                      {status.status === 'pending' && '대기 중'}
                      {status.status === 'running' && '실행 중'}
                      {status.status === 'completed' && '완료'}
                      {status.status === 'failed' && '실패'}
                    </Badge>
                  </div>
                  
                  {status.current_stock && (
                    <div className="text-sm">
                      <span className="font-medium">현재 종목:</span> {status.current_stock}
                    </div>
                  )}
                  
                  <div className="text-sm text-muted-foreground">
                    {status.message}
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                백테스팅을 시작하면 진행 상황이 여기에 표시됩니다
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 결과 패널 */}
      {results && results.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              백테스팅 결과
            </CardTitle>
            <CardDescription>
              각 종목별 최적 확정 기간과 수익률을 확인하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">종목명</th>
                    <th className="text-left py-2">종목코드</th>
                    <th className="text-center py-2">최적 확정기간</th>
                    <th className="text-right py-2">수익률</th>
                    <th className="text-right py-2">초기자금</th>
                    <th className="text-right py-2">최종자금</th>
                  </tr>
                </thead>
                <tbody>
                  {results
                    .sort((a, b) => b.return - a.return)
                    .map((result) => (
                    <tr key={result.symbol} className="border-b last:border-b-0">
                      <td className="py-3 font-medium">{result.name}</td>
                      <td className="py-3 text-muted-foreground">{result.symbol}</td>
                      <td className="py-3 text-center">
                        <Badge variant="outline">{result.optimal_days}일</Badge>
                      </td>
                      <td className="py-3 text-right">
                        <div className={`flex items-center justify-end gap-1 ${
                          result.return >= 0 ? 'text-red-600' : 'text-blue-600'
                        }`}>
                          {result.return >= 0 ? (
                            <TrendingUp className="w-4 h-4" />
                          ) : (
                            <TrendingDown className="w-4 h-4" />
                          )}
                          {result.return >= 0 ? '+' : ''}{result.return.toFixed(2)}%
                        </div>
                      </td>
                      <td className="py-3 text-right text-muted-foreground">
                        {result.initial.toLocaleString()}원
                      </td>
                      <td className="py-3 text-right font-medium">
                        {result.final.toLocaleString()}원
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* 요약 통계 */}
            <div className="mt-6 p-4 bg-muted/50 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">
                    {results.length}
                  </div>
                  <div className="text-sm text-muted-foreground">분석 종목</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {results.filter(r => r.return > 0).length}
                  </div>
                  <div className="text-sm text-muted-foreground">수익 종목</div>
                </div>
                <div>
                  <div className={`text-2xl font-bold ${
                    (results.reduce((sum, r) => sum + r.return, 0) / results.length) >= 0 
                      ? 'text-red-600' : 'text-blue-600'
                  }`}>
                    {((results.reduce((sum, r) => sum + r.return, 0) / results.length)).toFixed(2)}%
                  </div>
                  <div className="text-sm text-muted-foreground">평균 수익률</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}