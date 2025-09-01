"use client";

import React, { useState } from 'react';
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Header from "@/components/layout/Header";
import TradingModeWarning from "@/components/layout/TradingModeWarning";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  ChevronLeft, 
  ChevronRight, 
  Target, 
  TrendingUp, 
  Activity, 
  CheckCircle,
  Rocket
} from 'lucide-react';
import StrategySelector from '@/components/trading/StrategySelector';
import StockSelector from '@/components/trading/StockSelector';
import TradingConfigurer from '@/components/trading/TradingConfigurer';
import TradingMonitor from '@/components/trading/TradingMonitor';
import { TradingStrategy, StockAnalysis, AutoTradingConfig } from '@/lib/types/trading-strategy';

type AutoTradingStep = 'strategy' | 'stock' | 'config' | 'monitor';

interface StepInfo {
  id: AutoTradingStep;
  title: string;
  description: string;
  icon: React.ComponentType<any>;
}

const STEPS: StepInfo[] = [
  {
    id: 'strategy',
    title: '전략 선택',
    description: '자동매매 전략을 선택하세요',
    icon: Target
  },
  {
    id: 'stock',
    title: '종목 분석',
    description: '매매할 종목을 선택하고 분석합니다',
    icon: TrendingUp
  },
  {
    id: 'config',
    title: '매매 설정',
    description: '투자금액과 리스크를 설정합니다',
    icon: Activity
  },
  {
    id: 'monitor',
    title: '실시간 모니터링',
    description: '자동매매를 시작하고 모니터링합니다',
    icon: CheckCircle
  }
];

function AutoTradingDashboard() {
  const [currentStep, setCurrentStep] = useState<AutoTradingStep>('strategy');
  const [selectedStrategy, setSelectedStrategy] = useState<TradingStrategy | null>(null);
  const [selectedStock, setSelectedStock] = useState<StockAnalysis | null>(null);
  const [tradingConfig, setTradingConfig] = useState<AutoTradingConfig | null>(null);
  const [isTrading, setIsTrading] = useState(false);

  const getCurrentStepIndex = () => STEPS.findIndex(step => step.id === currentStep);
  const getProgressPercentage = () => ((getCurrentStepIndex() + 1) / STEPS.length) * 100;

  const handleStrategySelect = (strategy: TradingStrategy) => {
    setSelectedStrategy(strategy);
    setCurrentStep('stock');
  };

  const handleStockSelect = (stock: StockAnalysis) => {
    setSelectedStock(stock);
    setCurrentStep('config');
  };

  const handleConfigComplete = (config: AutoTradingConfig) => {
    setTradingConfig(config);
    setIsTrading(true);
    setCurrentStep('monitor');
  };

  const handleTradingStop = () => {
    setIsTrading(false);
    setCurrentStep('strategy');
    setSelectedStrategy(null);
    setSelectedStock(null);
    setTradingConfig(null);
  };

  const handleTradingPause = () => {
    console.log('자동매매 일시정지');
  };

  const handleTradingResume = () => {
    console.log('자동매매 재개');
  };

  const canGoBack = () => {
    return getCurrentStepIndex() > 0 && !isTrading;
  };

  const handleGoBack = () => {
    const currentIndex = getCurrentStepIndex();
    if (currentIndex > 0) {
      const prevStep = STEPS[currentIndex - 1];
      setCurrentStep(prevStep.id);
      
      if (prevStep.id === 'stock') {
        setTradingConfig(null);
      } else if (prevStep.id === 'strategy') {
        setSelectedStock(null);
        setTradingConfig(null);
      }
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto px-4 py-6 max-w-7xl space-y-6">
        {/* Trading Mode Warning */}
        <TradingModeWarning />

        {/* 헤더 */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center gap-3">
            <Rocket className="w-8 h-8 text-primary" />
            <h1 className="text-3xl font-bold">AI 자동매매 시스템</h1>
          </div>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            전략 선택부터 실시간 모니터링까지, 완전 자동화된 스마트 매매를 시작하세요
          </p>
        </div>

        {/* 진행 상태 */}
        <Card className="card">
          <CardContent className="p-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">진행 상황</span>
                <span className="text-sm text-muted-foreground">
                  {getCurrentStepIndex() + 1} / {STEPS.length}
                </span>
              </div>
              
              <Progress value={getProgressPercentage()} className="w-full" />
              
              <div className="flex items-center justify-between">
                {STEPS.map((step, index) => {
                  const isActive = step.id === currentStep;
                  const isCompleted = getCurrentStepIndex() > index;
                  const StepIcon = step.icon;
                  
                  return (
                    <div key={step.id} className="flex flex-col items-center space-y-2 flex-1">
                      <div className={`
                        w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors
                        ${isActive 
                          ? 'border-primary bg-primary text-primary-foreground' 
                          : isCompleted 
                          ? 'border-green-500 bg-green-500 text-white'
                          : 'border-muted bg-background text-muted-foreground'
                        }
                      `}>
                        <StepIcon className="w-4 h-4" />
                      </div>
                      <div className="text-center">
                        <div className={`text-xs font-medium ${isActive ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-muted-foreground'}`}>
                          {step.title}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 네비게이션 */}
        {(canGoBack() || getCurrentStepIndex() > 0) && (
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handleGoBack}
              disabled={!canGoBack()}
              className="flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              이전 단계
            </Button>
            <div></div>
          </div>
        )}

        {/* 현재 단계 컨텐츠 */}
        <div className="space-y-6">
          {currentStep === 'strategy' && (
            <div className="space-y-4">
              <Card className="card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    자동매매 전략 선택
                  </CardTitle>
                  <CardDescription>
                    AI가 분석한 다양한 전략 중에서 투자 성향에 맞는 전략을 선택하세요
                  </CardDescription>
                </CardHeader>
              </Card>
              <StrategySelector onStrategySelect={handleStrategySelect} />
            </div>
          )}

          {currentStep === 'stock' && selectedStrategy && (
            <div className="space-y-4">
              <Card className="card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    종목 선택 및 분석
                  </CardTitle>
                  <CardDescription>
                    선택한 <Badge variant="outline">{selectedStrategy.name}</Badge> 전략에 적합한 종목을 찾고 분석합니다
                  </CardDescription>
                </CardHeader>
              </Card>
              <StockSelector strategy={selectedStrategy} onStockSelect={handleStockSelect} />
            </div>
          )}

          {currentStep === 'config' && selectedStrategy && selectedStock && (
            <div className="space-y-4">
              <Card className="card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    자동매매 설정
                  </CardTitle>
                  <CardDescription>
                    <Badge variant="outline">{selectedStock.name}</Badge> 종목에 
                    <Badge variant="outline" className="ml-1">{selectedStrategy.name}</Badge> 전략을 적용할 세부 설정을 진행합니다
                  </CardDescription>
                </CardHeader>
              </Card>
              <TradingConfigurer 
                strategy={selectedStrategy} 
                stock={selectedStock} 
                onConfigComplete={handleConfigComplete} 
              />
            </div>
          )}

          {currentStep === 'monitor' && selectedStrategy && selectedStock && tradingConfig && (
            <div className="space-y-4">
              <Card className="card">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    실시간 모니터링
                  </CardTitle>
                  <CardDescription>
                    <Badge variant="outline">{selectedStock.name}</Badge> 자동매매가 실행 중입니다. 
                    실시간 성과와 포지션을 모니터링하세요
                  </CardDescription>
                </CardHeader>
              </Card>
              <TradingMonitor 
                config={tradingConfig}
                onStop={handleTradingStop}
                onPause={handleTradingPause}
                onResume={handleTradingResume}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ProtectedAutoTradingPage() {
  return (
    <ProtectedRoute>
      <AutoTradingDashboard />
    </ProtectedRoute>
  );
}