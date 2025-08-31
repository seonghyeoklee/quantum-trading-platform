'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Settings, 
  DollarSign, 
  Shield, 
  Target,
  Clock,
  PlayCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Loader2
} from 'lucide-react';
import { TradingStrategy, StockAnalysis, AutoTradingConfig } from '@/lib/types/trading-strategy';

interface TradingConfigurerProps {
  strategy: TradingStrategy;
  stock: StockAnalysis;
  onConfigComplete: (config: AutoTradingConfig) => void;
}

export default function TradingConfigurer({ strategy, stock, onConfigComplete }: TradingConfigurerProps) {
  const [config, setConfig] = useState<Partial<AutoTradingConfig>>({
    strategy_id: strategy.id,
    symbol: stock.symbol,
    capital: 1000000,
    max_position_size: 30,
    stop_loss_percent: 5,
    take_profit_percent: 10,
    parameters: strategy.parameters.reduce((acc, param) => {
      acc[param.name] = param.default_value;
      return acc;
    }, {} as any),
    is_active: false
  });

  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateConfig = (): boolean => {
    const newErrors: string[] = [];

    if (!config.capital || config.capital < strategy.min_capital) {
      newErrors.push(`최소 투자금은 ${(strategy.min_capital / 10000).toLocaleString()}만원 이상이어야 합니다.`);
    }

    if (!config.max_position_size || config.max_position_size < 1 || config.max_position_size > 100) {
      newErrors.push('최대 포지션 크기는 1% ~ 100% 사이여야 합니다.');
    }

    if (!config.stop_loss_percent || config.stop_loss_percent < 1 || config.stop_loss_percent > 20) {
      newErrors.push('손절 기준은 1% ~ 20% 사이여야 합니다.');
    }

    if (!config.take_profit_percent || config.take_profit_percent < 1 || config.take_profit_percent > 50) {
      newErrors.push('익절 기준은 1% ~ 50% 사이여야 합니다.');
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleStartTrading = async () => {
    if (!validateConfig()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // 자동매매 설정을 백엔드로 전송 (개발용 인증 우회) - actuator 경로 사용
      const response = await fetch('/actuator/dev/trading/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // 백엔드 DTO에 맞는 필드명 사용
          strategyName: strategy.name,
          symbol: config.symbol,
          capital: config.capital,
          maxPositionSize: config.max_position_size,
          stopLossPercent: config.stop_loss_percent,
          takeProfitPercent: config.take_profit_percent
        }),
      });

      if (!response.ok) {
        throw new Error(`자동매매 설정 저장 실패: ${response.status} ${response.statusText}`);
      }

      const savedConfig = await response.json();
      console.log('✅ 자동매매 설정이 백엔드에 저장되었습니다:', savedConfig);
      
      // 성공 시 다음 단계로 이동
      onConfigComplete(savedConfig as AutoTradingConfig);
      
    } catch (error) {
      console.error('❌ 자동매매 설정 저장 실패:', error);
      
      // API 실패 시 일단 로컬에서 진행 (개발 중)
      console.log('⚠️ 백엔드 연결 실패, 로컬 설정으로 진행합니다.');
      const localConfig = {
        ...config,
        id: 'local-' + Date.now(),
        created_at: new Date().toISOString(),
        is_active: true
      };
      onConfigComplete(localConfig as AutoTradingConfig);
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateParameter = (paramName: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters,
        [paramName]: value
      }
    }));
  };

  const calculateMaxLoss = () => {
    return (config.capital || 0) * (config.max_position_size || 0) / 100 * (config.stop_loss_percent || 0) / 100;
  };

  const calculateMaxProfit = () => {
    return (config.capital || 0) * (config.max_position_size || 0) / 100 * (config.take_profit_percent || 0) / 100;
  };

  return (
    <div className="space-y-6">
      {/* 설정 개요 */}
      <div className="text-center p-6 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20 rounded-xl border">
        <div className="flex items-center justify-center space-x-2 mb-3">
          <Settings className="w-6 h-6 text-primary" />
          <h3 className="text-xl font-bold">⚙️ 자동매매 설정</h3>
        </div>
        <div className="flex items-center justify-center space-x-2 mb-2">
          <Badge variant="outline" className="bg-primary/10">{strategy.name}</Badge>
          <span className="text-muted-foreground">×</span>
          <Badge variant="outline" className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">{stock.name}</Badge>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          투자 금액, 리스크 관리, 전략 파라미터를 설정하여 개인화된 자동매매 시스템을 구축합니다.
        </p>
      </div>

      {/* 에러 메시지 */}
      {errors.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1">
              {errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* 기본 설정 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            투자 설정
          </CardTitle>
          <CardDescription>
            투자 금액과 포지션 크기를 설정하세요
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="capital">투자 자본금 (원)</Label>
              <Input
                id="capital"
                type="number"
                value={config.capital || ''}
                onChange={(e) => setConfig(prev => ({ ...prev, capital: parseInt(e.target.value) || 0 }))}
                placeholder="1000000"
                min={strategy.min_capital}
              />
              <p className="text-xs text-muted-foreground">
                최소 투자금: {(strategy.min_capital / 10000).toLocaleString()}만원
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="position-size">최대 포지션 크기 (%)</Label>
              <div className="space-y-3">
                <Slider
                  value={[config.max_position_size || 30]}
                  onValueChange={([value]) => setConfig(prev => ({ ...prev, max_position_size: value }))}
                  max={100}
                  min={1}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>1%</span>
                  <span className="font-medium">{config.max_position_size}%</span>
                  <span>100%</span>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                한 번에 투자할 최대 금액: {((config.capital || 0) * (config.max_position_size || 0) / 100).toLocaleString()}원
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 리스크 관리 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            리스크 관리
          </CardTitle>
          <CardDescription>
            손절과 익절 기준을 설정하세요
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <Label className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-red-500" />
                손절 기준 (%)
              </Label>
              <div className="space-y-3">
                <Slider
                  value={[config.stop_loss_percent || 5]}
                  onValueChange={([value]) => setConfig(prev => ({ ...prev, stop_loss_percent: value }))}
                  max={20}
                  min={1}
                  step={0.5}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>1%</span>
                  <span className="font-medium text-red-600">{config.stop_loss_percent}%</span>
                  <span>20%</span>
                </div>
              </div>
              <div className="p-3 bg-red-50 dark:bg-red-950/20 rounded-lg">
                <p className="text-sm text-red-700 dark:text-red-300">
                  최대 손실: {calculateMaxLoss().toLocaleString()}원
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <Label className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                익절 기준 (%)
              </Label>
              <div className="space-y-3">
                <Slider
                  value={[config.take_profit_percent || 10]}
                  onValueChange={([value]) => setConfig(prev => ({ ...prev, take_profit_percent: value }))}
                  max={50}
                  min={1}
                  step={0.5}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-muted-foreground">
                  <span>1%</span>
                  <span className="font-medium text-green-600">{config.take_profit_percent}%</span>
                  <span>50%</span>
                </div>
              </div>
              <div className="p-3 bg-green-50 dark:bg-green-950/20 rounded-lg">
                <p className="text-sm text-green-700 dark:text-green-300">
                  예상 수익: {calculateMaxProfit().toLocaleString()}원
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 전략 매개변수 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            전략 매개변수
          </CardTitle>
          <CardDescription>
            {strategy.name} 전략의 세부 설정을 조정하세요
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {strategy.parameters.map((param) => (
            <div key={param.name} className="space-y-3">
              <div>
                <Label htmlFor={param.name}>{param.label}</Label>
                <p className="text-xs text-muted-foreground">{param.description}</p>
              </div>

              {param.type === 'number' && (
                <div className="space-y-2">
                  <Input
                    id={param.name}
                    type="number"
                    value={config.parameters?.[param.name] || param.default_value}
                    onChange={(e) => updateParameter(param.name, parseFloat(e.target.value) || param.default_value)}
                    min={param.min_value}
                    max={param.max_value}
                  />
                  {param.min_value !== undefined && param.max_value !== undefined && (
                    <p className="text-xs text-muted-foreground">
                      범위: {param.min_value} ~ {param.max_value}
                    </p>
                  )}
                </div>
              )}

              {param.type === 'boolean' && (
                <div className="flex items-center space-x-2">
                  <Switch
                    id={param.name}
                    checked={config.parameters?.[param.name] || param.default_value}
                    onCheckedChange={(checked) => updateParameter(param.name, checked)}
                  />
                  <Label htmlFor={param.name} className="text-sm">
                    {config.parameters?.[param.name] ? '활성화' : '비활성화'}
                  </Label>
                </div>
              )}

              {param.type === 'select' && param.options && (
                <select
                  id={param.name}
                  value={config.parameters?.[param.name] || param.default_value}
                  onChange={(e) => updateParameter(param.name, e.target.value)}
                  className="w-full p-2 border border-input rounded-md bg-background"
                >
                  {param.options.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* 시간 설정 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            거래 시간 설정
          </CardTitle>
          <CardDescription>
            자동매매 실행 시간을 설정하세요 (선택사항)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start-time">시작 시간</Label>
              <Input
                id="start-time"
                type="time"
                value={config.start_time || '09:00'}
                onChange={(e) => setConfig(prev => ({ ...prev, start_time: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end-time">종료 시간</Label>
              <Input
                id="end-time"
                type="time"
                value={config.end_time || '15:30'}
                onChange={(e) => setConfig(prev => ({ ...prev, end_time: e.target.value }))}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            설정하지 않으면 장중 내내 모니터링합니다 (09:00-15:30)
          </p>
        </CardContent>
      </Card>

      {/* 설정 요약 및 시작 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            설정 요약
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-muted/30 rounded-lg">
            <div>
              <div className="text-sm text-muted-foreground">전략</div>
              <div className="font-medium">{strategy.name}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">종목</div>
              <div className="font-medium">{stock.name} ({stock.symbol})</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">투자 자본</div>
              <div className="font-medium">{(config.capital || 0).toLocaleString()}원</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">최대 투자금액</div>
              <div className="font-medium">
                {((config.capital || 0) * (config.max_position_size || 0) / 100).toLocaleString()}원
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">손절/익절</div>
              <div className="font-medium">
                -{config.stop_loss_percent}% / +{config.take_profit_percent}%
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">거래 시간</div>
              <div className="font-medium">
                {config.start_time || '09:00'} ~ {config.end_time || '15:30'}
              </div>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="text-center space-y-2">
              <div className="text-lg font-semibold">🚀 자동매매 준비 완료</div>
              <p className="text-sm text-muted-foreground">
                설정을 검토하고 자동매매를 시작하세요
              </p>
            </div>

            <Button 
              className="w-full h-16 text-xl font-bold bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none" 
              onClick={handleStartTrading}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-6 h-6 mr-3 animate-spin" />
                  💾 백엔드에 저장 중...
                </>
              ) : (
                <>
                  <PlayCircle className="w-6 h-6 mr-3" />
                  🎯 자동매매 시작하기
                  <div className="ml-auto text-sm font-normal opacity-90">
                    {stock.name}
                  </div>
                </>
              )}
            </Button>
            
            {/* 예상 수익/손실 표시 */}
            <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-sm">
              <div className="flex items-center space-x-2">
                <TrendingDown className="w-4 h-4 text-red-500" />
                <span>최대 예상 손실</span>
                <span className="font-semibold text-red-600">
                  -{calculateMaxLoss().toLocaleString()}원
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span>최대 예상 수익</span>
                <span className="font-semibold text-green-600">
                  +{calculateMaxProfit().toLocaleString()}원
                </span>
              </div>
            </div>
            
            <div className="text-center p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">
                ⚠️ <strong>주의사항:</strong> 자동매매는 시장 변동성에 따라 손실이 발생할 수 있습니다. 
                설정된 손절/익절 기준을 반드시 확인하고 시작하시기 바랍니다.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}