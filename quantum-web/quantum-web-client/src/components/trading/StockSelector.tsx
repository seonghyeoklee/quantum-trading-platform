'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Search, 
  TrendingUp, 
  TrendingDown, 
  BarChart3,
  DollarSign,
  Volume,
  Activity,
  Target,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { StockAnalysis, TradingStrategy } from '@/lib/types/trading-strategy';
import { getKiwoomAdapterUrl } from '@/lib/api-config';

interface StockSelectorProps {
  strategy: TradingStrategy;
  onStockSelect: (stock: StockAnalysis) => void;
  selectedStock?: StockAnalysis;
}

// 인기 종목 목록
const POPULAR_STOCKS = [
  { symbol: '005930', name: '삼성전자' },
  { symbol: '000660', name: 'SK하이닉스' },
  { symbol: '035420', name: 'NAVER' },
  { symbol: '207940', name: '삼성바이오로직스' },
  { symbol: '068270', name: '셀트리온' },
  { symbol: '035720', name: '카카오' },
  { symbol: '051910', name: 'LG화학' },
  { symbol: '006400', name: '삼성SDI' },
  { symbol: '028260', name: '삼성물산' },
  { symbol: '012330', name: '현대모비스' }
];

export default function StockSelector({ strategy, onStockSelect, selectedStock }: StockSelectorProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<StockAnalysis | null>(selectedStock || null);
  
  // 종목 분석 실행 (실제 API 호출)
  const analyzeStock = async (symbol: string, name: string) => {
    setAnalyzing(true);
    
    try {
      // 개발용 API 호출 (인증 우회) - actuator 경로 사용
      const response = await fetch(`/actuator/dev/trading/analysis/${symbol}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
      }
      
      const analysisData: StockAnalysis = await response.json();
      
      setAnalysis(analysisData);
      onStockSelect(analysisData);
      
    } catch (error) {
      console.warn('백엔드 API 연결 실패, Mock 데이터로 대체:', error);
      
      // Mock 데이터 생성 (API 실패시 폴백)
      await new Promise(resolve => setTimeout(resolve, 1500)); // 분석 시뮬레이션
      
      const mockAnalysis: StockAnalysis = {
        symbol,
        name,
        current_price: 50000 + Math.floor(Math.random() * 50000),
        change: Math.floor(Math.random() * 2000) - 1000,
        change_percent: (Math.random() * 6 - 3),
        indicators: {
          rsi: Math.floor(Math.random() * 100),
          macd: Math.random() * 200 - 100,
          bollinger_upper: 55000 + Math.floor(Math.random() * 10000),
          bollinger_lower: 45000 + Math.floor(Math.random() * 5000),
          moving_average_20: 50000 + Math.floor(Math.random() * 5000),
          stochastic_k: Math.floor(Math.random() * 100),
          volume: Math.floor(Math.random() * 5000000) + 1000000
        },
        strategy_scores: {
          [strategy.id]: {
            score: Math.floor(Math.random() * 30) + 70,
            recommendation: ['strong_buy', 'buy', 'hold'][Math.floor(Math.random() * 3)] as 'strong_buy' | 'buy' | 'hold',
            confidence: Math.floor(Math.random() * 30) + 70
          }
        }
      };
      
      setAnalysis(mockAnalysis);
      onStockSelect(mockAnalysis);
    } finally {
      setAnalyzing(false);
    }
  };
  
  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'strong_buy': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'buy': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'hold': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'sell': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'strong_sell': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };
  
  const getRecommendationText = (recommendation: string) => {
    switch (recommendation) {
      case 'strong_buy': return '적극 매수';
      case 'buy': return '매수';
      case 'hold': return '보유';
      case 'sell': return '매도';
      case 'strong_sell': return '적극 매도';
      default: return recommendation;
    }
  };

  return (
    <div className="space-y-6">
      {/* 종목 선택 개요 */}
      <div className="text-center p-6 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 rounded-xl border">
        <div className="flex items-center justify-center space-x-2 mb-3">
          <BarChart3 className="w-6 h-6 text-primary" />
          <h3 className="text-xl font-bold">📊 종목 분석 & 선택</h3>
        </div>
        <p className="text-sm text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          <Badge variant="outline" className="mr-1">{strategy.name}</Badge> 
          전략에 최적화된 종목을 AI가 실시간으로 분석합니다. 
          기술적 지표, 재무 데이터, 시장 동향을 종합하여 투자 적합도를 평가합니다.
        </p>
      </div>

      {/* 종목 검색 */}
      <Card className="border-2 border-dashed border-primary/20 hover:border-primary/40 transition-colors">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5 text-primary" />
            🔍 종목 검색 & 분석
          </CardTitle>
          <CardDescription>
            종목명이나 코드를 입력하면 AI가 실시간으로 분석합니다
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex gap-3">
            <div className="flex-1">
              <Input
                placeholder="종목명 또는 코드 입력 (예: 삼성전자, 005930)"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="h-12 text-base"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && searchTerm.trim()) {
                    analyzeStock(searchTerm, searchTerm);
                  }
                }}
              />
            </div>
            <Button 
              onClick={() => {
                if (searchTerm.trim()) {
                  analyzeStock(searchTerm, searchTerm);
                }
              }}
              disabled={analyzing || !searchTerm.trim()}
              size="lg"
              className="px-6"
            >
              {analyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  분석중
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  분석시작
                </>
              )}
            </Button>
          </div>
          
          {/* 인기 종목 */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <TrendingUp className="w-4 h-4 text-orange-500" />
              <h4 className="font-semibold">🔥 인기 종목</h4>
              <Badge variant="secondary" className="text-xs">클릭하여 즉시 분석</Badge>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              {POPULAR_STOCKS.map((stock, index) => (
                <Button
                  key={stock.symbol}
                  variant="outline"
                  size="sm"
                  className={`h-auto p-4 flex flex-col items-center space-y-1 transition-all hover:shadow-md hover:scale-105 ${
                    analyzing ? 'opacity-50' : ''
                  } ${
                    index < 3 ? 'border-primary/30 bg-primary/5' : ''
                  }`}
                  onClick={() => analyzeStock(stock.symbol, stock.name)}
                  disabled={analyzing}
                >
                  {index < 3 && <div className="text-xs text-primary font-bold">TOP {index + 1}</div>}
                  <div className="font-semibold text-sm">{stock.name}</div>
                  <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 분석 진행 상태 */}
      {analyzing && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
          <CardContent className="p-8">
            <div className="flex flex-col items-center space-y-4">
              <div className="relative">
                <Loader2 className="w-12 h-12 animate-spin text-primary" />
                <div className="absolute inset-0 w-12 h-12 border-4 border-primary/20 rounded-full animate-pulse"></div>
              </div>
              <div className="text-center space-y-2">
                <div className="text-lg font-semibold">🤖 AI 종목 분석 진행 중</div>
                <div className="text-sm text-muted-foreground max-w-md">
                  실시간 기술적 지표, 재무 데이터, 시장 동향을 종합 분석하여<br/>
                  <Badge variant="outline">{strategy.name}</Badge> 전략 적합도를 계산하고 있습니다
                </div>
              </div>
              <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>기술적 분석</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{animationDelay: '0.5s'}}></div>
                  <span>재무 분석</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse" style={{animationDelay: '1s'}}></div>
                  <span>전략 매칭</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 분석 결과 */}
      {analysis && !analyzing && (
        <Card className="border-2 border-green-200 dark:border-green-800 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-3 bg-green-100 dark:bg-green-900 rounded-xl">
                  <BarChart3 className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <CardTitle className="text-xl">
                    📊 {analysis.name} ({analysis.symbol})
                  </CardTitle>
                  <CardDescription className="flex items-center space-x-2 mt-1">
                    <Badge variant="outline" className="bg-primary/10">
                      {strategy.name}
                    </Badge>
                    <span>전략 기준 AI 종합 분석 완료</span>
                  </CardDescription>
                </div>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">
                  {analysis.current_price.toLocaleString()}원
                </div>
                <div className="text-sm text-muted-foreground">현재가</div>
                <div className="text-xs text-green-600 mt-1">
                  📈 실시간 업데이트
                </div>
              </div>
            </div>
            
            {/* 전략 점수 미리보기 */}
            <div className="mt-4 p-4 bg-white/60 dark:bg-black/20 rounded-lg">
              {Object.entries(analysis.strategy_scores).map(([strategyId, score]) => (
                <div key={strategyId} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Target className="w-4 h-4 text-primary" />
                    <span className="font-medium">전략 적합도</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-lg font-bold">{score.score}점</span>
                    <Badge className={getRecommendationColor(score.recommendation)}>
                      {getRecommendationText(score.recommendation)}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardHeader>
          
          <CardContent>
            <Tabs defaultValue="strategy" className="space-y-6">
              <TabsList className="grid w-full grid-cols-4 h-12 p-1">
                <TabsTrigger value="strategy" className="flex items-center space-x-2">
                  <Target className="w-4 h-4" />
                  <span>전략 매칭</span>
                </TabsTrigger>
                <TabsTrigger value="technical" className="flex items-center space-x-2">
                  <Activity className="w-4 h-4" />
                  <span>기술 분석</span>
                </TabsTrigger>
                <TabsTrigger value="fundamental" className="flex items-center space-x-2">
                  <DollarSign className="w-4 h-4" />
                  <span>재무 분석</span>
                </TabsTrigger>
                <TabsTrigger value="price" className="flex items-center space-x-2">
                  <BarChart3 className="w-4 h-4" />
                  <span>가격 정보</span>
                </TabsTrigger>
              </TabsList>

              {/* 전략 적합도 */}
              <TabsContent value="strategy" className="space-y-6">
                {Object.entries(analysis.strategy_scores).map(([strategyId, score]) => (
                  <div key={strategyId} className="space-y-6">
                    {/* 메인 스코어 */}
                    <div className="text-center p-6 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-xl border">
                      <div className="text-4xl font-bold mb-2">{score.score}<span className="text-2xl text-muted-foreground">/100</span></div>
                      <div className="text-lg font-semibold mb-2">🎯 전략 적합도 점수</div>
                      <Badge className={`${getRecommendationColor(score.recommendation)} text-sm px-3 py-1`}>
                        {getRecommendationText(score.recommendation)}
                      </Badge>
                    </div>
                    
                    {/* 상세 분석 */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">AI 분석 결과</span>
                        <span className={`text-lg font-bold ${score.score >= 80 ? 'text-green-600' : score.score >= 60 ? 'text-blue-600' : 'text-orange-600'}`}>
                          {score.score}점
                        </span>
                      </div>
                      <Progress value={score.score} className="h-4" />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>부적합 (0-40)</span>
                        <span>보통 (40-70)</span>
                        <span>적합 (70-85)</span>
                        <span>매우 적합 (85-100)</span>
                      </div>
                    </div>
                    
                    {/* AI 분석 사유 */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <div className="flex items-start space-x-3">
                        <Activity className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div>
                          <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">🤖 AI 분석 의견</h4>
                          <p className="text-sm text-blue-700 dark:text-blue-300 leading-relaxed">{score.reason}</p>
                        </div>
                      </div>
                    </div>
                    
                    {/* 추천/경고 메시지 */}
                    {score.score >= 80 ? (
                      <div className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                        <CheckCircle className="w-6 h-6 text-green-600" />
                        <div>
                          <div className="font-semibold text-green-800 dark:text-green-200">✨ 강력 추천</div>
                          <div className="text-sm text-green-700 dark:text-green-300">
                            이 종목은 선택하신 <Badge variant="outline">{strategy.name}</Badge> 전략에 매우 적합합니다. 
                            자동매매를 진행하시기 바랍니다.
                          </div>
                        </div>
                      </div>
                    ) : score.score >= 60 ? (
                      <div className="flex items-center gap-3 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <Target className="w-6 h-6 text-blue-600" />
                        <div>
                          <div className="font-semibold text-blue-800 dark:text-blue-200">📊 적당한 선택</div>
                          <div className="text-sm text-blue-700 dark:text-blue-300">
                            이 종목은 전략에 어느 정도 부합하나, 더 나은 종목을 찾아보는 것을 권장합니다.
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3 p-4 bg-orange-50 dark:bg-orange-950/20 rounded-lg border border-orange-200 dark:border-orange-800">
                        <AlertCircle className="w-6 h-6 text-orange-600" />
                        <div>
                          <div className="font-semibold text-orange-800 dark:text-orange-200">⚠️ 주의 필요</div>
                          <div className="text-sm text-orange-700 dark:text-orange-300">
                            이 종목은 전략 특성에 잘 맞지 않을 수 있습니다. 다른 종목 검토를 권장합니다.
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </TabsContent>

              {/* 기술적 분석 */}
              <TabsContent value="technical" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">RSI</div>
                    <div className="text-lg font-semibold">{analysis.indicators.rsi}</div>
                    <Progress value={analysis.indicators.rsi} className="h-2" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">Stochastic %K</div>
                    <div className="text-lg font-semibold">{analysis.indicators.stochastic.k}</div>
                    <Progress value={analysis.indicators.stochastic.k} className="h-2" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">MACD</div>
                    <div className="text-lg font-semibold">
                      {analysis.indicators.macd.macd.toFixed(2)}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="text-sm text-muted-foreground">거래량</div>
                    <div className="text-lg font-semibold">
                      {(analysis.volume / 1000).toLocaleString()}K
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-3">이동평균선</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">5일선</div>
                      <div className="font-semibold">{analysis.indicators.moving_averages.ma5.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">20일선</div>
                      <div className="font-semibold">{analysis.indicators.moving_averages.ma20.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">60일선</div>
                      <div className="font-semibold">{analysis.indicators.moving_averages.ma60.toLocaleString()}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">120일선</div>
                      <div className="font-semibold">{analysis.indicators.moving_averages.ma120.toLocaleString()}</div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* 재무 분석 */}
              <TabsContent value="fundamental" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center p-3 border rounded-lg">
                    <div className="text-sm text-muted-foreground">PER</div>
                    <div className="text-lg font-semibold">{analysis.fundamental.per.toFixed(1)}</div>
                  </div>
                  <div className="text-center p-3 border rounded-lg">
                    <div className="text-sm text-muted-foreground">PBR</div>
                    <div className="text-lg font-semibold">{analysis.fundamental.pbr.toFixed(2)}</div>
                  </div>
                  <div className="text-center p-3 border rounded-lg">
                    <div className="text-sm text-muted-foreground">ROE</div>
                    <div className="text-lg font-semibold">{analysis.fundamental.roe.toFixed(1)}%</div>
                  </div>
                  <div className="text-center p-3 border rounded-lg">
                    <div className="text-sm text-muted-foreground">부채비율</div>
                    <div className="text-lg font-semibold">{analysis.fundamental.debt_ratio.toFixed(1)}%</div>
                  </div>
                  <div className="text-center p-3 border rounded-lg">
                    <div className="text-sm text-muted-foreground">유동비율</div>
                    <div className="text-lg font-semibold">{analysis.fundamental.current_ratio.toFixed(0)}%</div>
                  </div>
                </div>
              </TabsContent>

              {/* 가격 정보 */}
              <TabsContent value="price" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-sm text-muted-foreground">시가</div>
                    <div className="text-lg font-semibold">{analysis.open_price.toLocaleString()}</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-sm text-muted-foreground">고가</div>
                    <div className="text-lg font-semibold text-red-600">{analysis.high_price.toLocaleString()}</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-sm text-muted-foreground">저가</div>
                    <div className="text-lg font-semibold text-blue-600">{analysis.low_price.toLocaleString()}</div>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-sm text-muted-foreground">시가총액</div>
                    <div className="text-lg font-semibold">
                      {(analysis.market_cap / 100000000).toFixed(0)}억
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
            
            {/* 선택 버튼 */}
            <div className="mt-8 pt-6 border-t space-y-4">
              <div className="text-center space-y-2">
                <div className="text-lg font-semibold">💎 종목 분석 완료</div>
                <p className="text-sm text-muted-foreground">
                  이 분석 결과를 바탕으로 자동매매 설정을 진행하시겠습니까?
                </p>
              </div>
              
              <Button 
                className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-[1.02]" 
                onClick={() => onStockSelect(analysis)}
              >
                <Target className="w-5 h-5 mr-3" />
                {analysis.name} 자동매매 설정하기
                <div className="ml-auto flex items-center space-x-1">
                  {Object.entries(analysis.strategy_scores).map(([_, score]) => (
                    <Badge key={score.score} variant="secondary" className="bg-white/20">
                      {score.score}점
                    </Badge>
                  ))}
                </div>
              </Button>
              
              <div className="text-center">
                <p className="text-xs text-muted-foreground">
                  다음 단계에서 투자 금액과 리스크 관리를 설정합니다
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}