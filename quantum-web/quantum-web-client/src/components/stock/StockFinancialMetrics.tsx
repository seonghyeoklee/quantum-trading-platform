'use client';

import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  PieChart,
  Calculator,
  Building,
  ArrowUpRight,
  ArrowDownRight,
  Info
} from 'lucide-react';
import { StockBasicInfo } from '@/lib/api/stock-info-types';
import { 
  PERTooltip,
  PBRTooltip,
  ROETooltip,
  EPSTooltip,
  BPSTooltip,
  EVEBITDATooltip
} from '@/components/ui/TermTooltip';

interface StockFinancialMetricsProps {
  stockInfo: StockBasicInfo | null;
  loading: boolean;
  className?: string;
}

export default function StockFinancialMetrics({ 
  stockInfo, 
  loading, 
  className 
}: StockFinancialMetricsProps) {
  
  // 숫자 포맷 함수들
  const formatNumber = (num: number, decimals: number = 2) => {
    if (num === 0) return '0';
    return num.toFixed(decimals);
  };

  const formatCurrency = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num);
  };

  const formatLargeNumber = (num: number) => {
    if (num >= 10000) {
      return `${(num / 10000).toFixed(1)}조`;
    } else if (num >= 100) {
      return `${num.toLocaleString('ko-KR')}억`;
    } else {
      return `${num.toFixed(1)}억`;
    }
  };

  // 지표 평가 함수들
  const evaluatePER = (per: number) => {
    if (per <= 0) return { status: 'negative', text: '손실', color: 'text-red-600' };
    if (per < 10) return { status: 'good', text: '저평가', color: 'text-blue-600' };
    if (per < 15) return { status: 'fair', text: '적정', color: 'text-green-600' };
    if (per < 25) return { status: 'high', text: '고평가', color: 'text-orange-600' };
    return { status: 'very-high', text: '매우높음', color: 'text-red-600' };
  };

  const evaluatePBR = (pbr: number) => {
    if (pbr <= 0) return { status: 'negative', text: '음수', color: 'text-red-600' };
    if (pbr < 1) return { status: 'good', text: '저평가', color: 'text-blue-600' };
    if (pbr < 2) return { status: 'fair', text: '적정', color: 'text-green-600' };
    if (pbr < 3) return { status: 'high', text: '고평가', color: 'text-orange-600' };
    return { status: 'very-high', text: '매우높음', color: 'text-red-600' };
  };

  const evaluateROE = (roe: number) => {
    if (roe <= 0) return { status: 'negative', text: '손실', color: 'text-red-600' };
    if (roe < 5) return { status: 'low', text: '낮음', color: 'text-orange-600' };
    if (roe < 10) return { status: 'fair', text: '보통', color: 'text-yellow-600' };
    if (roe < 15) return { status: 'good', text: '양호', color: 'text-green-600' };
    return { status: 'excellent', text: '우수', color: 'text-blue-600' };
  };

  // 로딩 스켈레톤
  if (loading) {
    return (
      <div className={`space-y-4 ${className || ''}`}>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="border rounded-lg p-4 bg-background">
              <div className="animate-pulse space-y-3">
                <div className="flex items-center space-x-2">
                  <div className="w-5 h-5 bg-muted rounded"></div>
                  <div className="h-4 bg-muted rounded w-20"></div>
                </div>
                <div className="h-6 bg-muted rounded w-16"></div>
                <div className="h-3 bg-muted rounded w-12"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!stockInfo) {
    return (
      <div className={`${className || ''}`}>
        <div className="border rounded-lg p-6 bg-background">
          <div className="text-center text-muted-foreground">
            재무 지표를 표시하려면 종목을 선택해주세요
          </div>
        </div>
      </div>
    );
  }

  const perEval = evaluatePER(stockInfo.per);
  const pbrEval = evaluatePBR(stockInfo.pbr);
  const roeEval = evaluateROE(stockInfo.roe);

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {/* 주요 재무 지표 */}
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2" />
          주요 재무 지표
        </h3>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* PER */}
          <div className="border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <PERTooltip>
                <div className="flex items-center space-x-2 cursor-help">
                  <Calculator className="w-4 h-4 text-blue-600" />
                  <span className="font-medium text-sm">PER</span>
                </div>
              </PERTooltip>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {stockInfo.per > 0 ? `${formatNumber(stockInfo.per)}배` : 'N/A'}
              </div>
              <div className={`text-xs font-medium ${perEval.color}`}>
                {perEval.text}
              </div>
            </div>
          </div>

          {/* PBR */}
          <div className="border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <PBRTooltip>
                <div className="flex items-center space-x-2 cursor-help">
                  <Building className="w-4 h-4 text-green-600" />
                  <span className="font-medium text-sm">PBR</span>
                </div>
              </PBRTooltip>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {stockInfo.pbr > 0 ? `${formatNumber(stockInfo.pbr)}배` : 'N/A'}
              </div>
              <div className={`text-xs font-medium ${pbrEval.color}`}>
                {pbrEval.text}
              </div>
            </div>
          </div>

          {/* ROE */}
          <div className="border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <ROETooltip>
                <div className="flex items-center space-x-2 cursor-help">
                  <TrendingUp className="w-4 h-4 text-purple-600" />
                  <span className="font-medium text-sm">ROE</span>
                </div>
              </ROETooltip>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {formatNumber(stockInfo.roe)}%
              </div>
              <div className={`text-xs font-medium ${roeEval.color}`}>
                {roeEval.text}
              </div>
            </div>
          </div>

          {/* EPS */}
          <div className="border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <EPSTooltip>
                <div className="flex items-center space-x-2 cursor-help">
                  <DollarSign className="w-4 h-4 text-indigo-600" />
                  <span className="font-medium text-sm">EPS</span>
                </div>
              </EPSTooltip>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {formatCurrency(stockInfo.eps)}원
              </div>
              <div className="text-xs text-muted-foreground">
                주당순이익
              </div>
            </div>
          </div>

          {/* BPS */}
          <div className="border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <BPSTooltip>
                <div className="flex items-center space-x-2 cursor-help">
                  <PieChart className="w-4 h-4 text-teal-600" />
                  <span className="font-medium text-sm">BPS</span>
                </div>
              </BPSTooltip>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {formatCurrency(stockInfo.bps)}원
              </div>
              <div className="text-xs text-muted-foreground">
                주당순자산
              </div>
            </div>
          </div>

          {/* EV/EBITDA */}
          <div className="border rounded-lg p-4 bg-background hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <EVEBITDATooltip>
                <div className="flex items-center space-x-2 cursor-help">
                  <BarChart3 className="w-4 h-4 text-orange-600" />
                  <span className="font-medium text-sm">EV/EBITDA</span>
                </div>
              </EVEBITDATooltip>
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {stockInfo.evEbitda > 0 ? `${formatNumber(stockInfo.evEbitda)}배` : 'N/A'}
              </div>
              <div className="text-xs text-muted-foreground">
                기업가치배수
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 재무 성과 */}
      <div>
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <DollarSign className="w-5 h-5 mr-2" />
          재무 성과 (연간)
        </h3>
        
        <div className="grid md:grid-cols-3 gap-4">
          {/* 매출액 */}
          <div className="border rounded-lg p-4 bg-background">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-sm">매출액</span>
              <ArrowUpRight className="w-4 h-4 text-green-600" />
            </div>
            <div className="space-y-1">
              <div className="text-xl font-bold">
                {formatLargeNumber(stockInfo.revenue)}
              </div>
              <div className="text-xs text-muted-foreground">
                연간 총 매출
              </div>
            </div>
          </div>

          {/* 영업이익 */}
          <div className="border rounded-lg p-4 bg-background">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-sm">영업이익</span>
              {stockInfo.operatingProfit > 0 ? (
                <ArrowUpRight className="w-4 h-4 text-green-600" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-red-600" />
              )}
            </div>
            <div className="space-y-1">
              <div className="text-xl font-bold">
                {formatLargeNumber(stockInfo.operatingProfit)}
              </div>
              <div className="text-xs text-muted-foreground">
                영업활동 수익
              </div>
            </div>
          </div>

          {/* 당기순이익 */}
          <div className="border rounded-lg p-4 bg-background">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-sm">당기순이익</span>
              {stockInfo.netIncome > 0 ? (
                <ArrowUpRight className="w-4 h-4 text-green-600" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-red-600" />
              )}
            </div>
            <div className="space-y-1">
              <div className="text-xl font-bold">
                {formatLargeNumber(stockInfo.netIncome)}
              </div>
              <div className="text-xs text-muted-foreground">
                최종 순이익
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 지표 해석 가이드 */}
      <div className="border rounded-lg p-4 bg-muted/20">
        <h4 className="font-semibold mb-3 text-sm flex items-center">
          <Info className="w-4 h-4 mr-2" />
          지표 해석 가이드
        </h4>
        <div className="grid md:grid-cols-2 gap-4 text-xs space-y-2 md:space-y-0">
          <div>
            <div className="font-medium mb-1">PER (주가수익률)</div>
            <div className="text-muted-foreground">
              10 미만: 저평가, 10-15: 적정, 15-25: 고평가, 25 이상: 매우높음
            </div>
          </div>
          <div>
            <div className="font-medium mb-1">PBR (주가순자산률)</div>
            <div className="text-muted-foreground">
              1 미만: 저평가, 1-2: 적정, 2-3: 고평가, 3 이상: 매우높음
            </div>
          </div>
          <div>
            <div className="font-medium mb-1">ROE (자기자본이익률)</div>
            <div className="text-muted-foreground">
              5% 미만: 낮음, 5-10%: 보통, 10-15%: 양호, 15% 이상: 우수
            </div>
          </div>
          <div>
            <div className="font-medium mb-1">결산월</div>
            <div className="text-muted-foreground">
              {stockInfo.settlementMonth}월 결산
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}