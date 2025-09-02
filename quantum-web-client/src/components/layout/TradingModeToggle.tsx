'use client';

import { useState } from 'react';
import { useTradingMode } from '@/contexts/TradingModeContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  AlertTriangle, 
  Shield, 
  Loader2,
  Info,
  ExternalLink
} from 'lucide-react';

export default function TradingModeToggle() {
  const { settings, isProduction, loading } = useTradingMode();
  const { user } = useAuth();
  const [showInfoDialog, setShowInfoDialog] = useState(false);

  if (loading) {
    return (
      <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-muted">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span className="text-xs text-muted-foreground">확인중</span>
      </div>
    );
  }

  const handleModeClick = () => {
    setShowInfoDialog(true);
  };

  const handleGoToSettings = () => {
    setShowInfoDialog(false);
    window.location.href = '/kiwoom-account';
  };

  return (
    <>
      <button
        onClick={handleModeClick}
        className={`
          flex items-center space-x-1.5 px-4 py-1.5 rounded-full transition-all duration-200 
          hover:scale-105 focus:outline-none focus:ring-2 focus:ring-offset-2
          border-2 font-bold text-xs shadow-md hover:shadow-lg cursor-pointer
          ${isProduction 
            ? 'bg-red-500 hover:bg-red-600 text-white border-red-700 focus:ring-red-300 shadow-red-200 dark:shadow-red-800 animate-pulse' 
            : 'bg-green-500 hover:bg-green-600 text-white border-green-700 focus:ring-green-300 shadow-green-200 dark:shadow-green-800'
          }
        `}
        title="거래 모드 정보를 확인하세요"
      >
        {isProduction ? (
          <AlertTriangle className="h-3 w-3" />
        ) : (
          <Shield className="h-3 w-3" />
        )}
        <span className="text-xs font-bold">
          {isProduction ? 'REAL' : 'SANDBOX'}
        </span>
        <Info className="h-3 w-3 opacity-75" />
      </button>

      {/* 거래 모드 정보 다이얼로그 */}
      <Dialog open={showInfoDialog} onOpenChange={setShowInfoDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              {isProduction ? (
                <AlertTriangle className="h-5 w-5 text-red-500" />
              ) : (
                <Shield className="h-5 w-5 text-green-500" />
              )}
              <span>
                현재 거래 모드: {isProduction ? 'REAL' : 'SANDBOX'}
              </span>
            </DialogTitle>
            <DialogDescription className="space-y-4">
              <div className={`p-4 border rounded-lg ${
                isProduction 
                  ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
                  : 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
              }`}>
                <div className={`font-medium mb-2 ${
                  isProduction 
                    ? 'text-red-800 dark:text-red-300' 
                    : 'text-green-800 dark:text-green-300'
                }`}>
                  {isProduction ? '⚠️ REAL 모드 활성화' : '✅ SANDBOX 모드 활성화'}
                </div>
                <ul className={`text-sm space-y-1 ${
                  isProduction 
                    ? 'text-red-700 dark:text-red-400'
                    : 'text-green-700 dark:text-green-400'
                }`}>
                  {isProduction ? (
                    <>
                      <li>• 실제 자금으로 거래가 실행됩니다</li>
                      <li>• 모든 주문이 실제 시장에서 체결됩니다</li>
                      <li>• 실제 손익이 발생합니다</li>
                    </>
                  ) : (
                    <>
                      <li>• 가상 자금으로 거래 연습</li>
                      <li>• 시뮬레이션으로 주문 처리</li>
                      <li>• 실제 손익 발생 없음</li>
                    </>
                  )}
                </ul>
              </div>
              
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg dark:bg-blue-900/20 dark:border-blue-800">
                <div className="font-medium text-blue-800 dark:text-blue-300 mb-2">
                  ℹ️ 거래 모드는 어떻게 결정되나요?
                </div>
                <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                  <li>• 키움증권 API 키 패턴을 자동으로 분석합니다</li>
                  <li>• 실전투자용 키와 모의투자용 키를 구분합니다</li>
                  <li>• 모드 변경은 키움계좌 설정에서 API 키를 변경해야 합니다</li>
                </ul>
              </div>
              
              <div className="flex justify-center">
                <Button 
                  onClick={handleGoToSettings} 
                  className="flex items-center space-x-2"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>키움계좌 설정으로 이동</span>
                </Button>
              </div>
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </>
  );
}