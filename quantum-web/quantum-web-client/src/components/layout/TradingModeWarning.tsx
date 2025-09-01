'use client';

import { useTradingMode } from '@/contexts/TradingModeContext';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, Info, Shield } from 'lucide-react';

interface TradingModeWarningProps {
  className?: string;
  showTitle?: boolean;
}

export default function TradingModeWarning({ 
  className = "", 
  showTitle = true 
}: TradingModeWarningProps) {
  const { isProduction, loading } = useTradingMode();

  if (loading) {
    return null;
  }

  return (
    <div className={`${isProduction ? 'trading-mode-production' : 'trading-mode-sandbox'} ${className}`}>
      <Alert className={isProduction ? 'trading-mode-warning' : 'trading-mode-info'}>
        <div className="flex items-center space-x-2">
          {isProduction ? (
            <AlertTriangle className="h-4 w-4" />
          ) : (
            <Shield className="h-4 w-4" />
          )}
          {showTitle && (
            <AlertTitle>
              {isProduction ? '실전투자 모드 활성화' : '모의투자 모드 활성화'}
            </AlertTitle>
          )}
        </div>
        <AlertDescription className="mt-2">
          {isProduction ? (
            <>
              <strong>실제 자금</strong>으로 거래가 실행됩니다. 
              모든 주문과 거래는 <strong>실제 시장</strong>에서 처리되며 
              <strong>실제 손익이 발생</strong>합니다.
              <br />
              신중하게 검토한 후 진행하시기 바랍니다.
            </>
          ) : (
            <>
              <strong>가상 자금</strong>으로 거래 연습이 진행됩니다. 
              모든 주문과 거래는 <strong>시뮬레이션</strong>으로 처리되며 
              <strong>실제 손익은 발생하지 않습니다</strong>.
              <br />
              안심하고 다양한 전략을 테스트해보세요.
            </>
          )}
        </AlertDescription>
      </Alert>
    </div>
  );
}