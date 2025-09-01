'use client';

import { useTradingMode } from '@/contexts/TradingModeContext';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  AlertTriangle, 
  Play, 
  Pause,
  Settings,
  Loader2 
} from 'lucide-react';
import { useRouter } from 'next/navigation';

interface TradingModeIndicatorProps {
  showQuickToggle?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function TradingModeIndicator({ 
  showQuickToggle = false, 
  size = 'md' 
}: TradingModeIndicatorProps) {
  const { settings, loading, isProduction, isSandbox } = useTradingMode();
  const router = useRouter();

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-muted-foreground">모드 확인 중...</span>
      </div>
    );
  }

  const handleSettingsClick = () => {
    router.push('/settings');
  };

  const sizeClasses = {
    sm: {
      badge: 'text-xs px-2 py-1',
      icon: 'h-3 w-3',
      text: 'text-xs'
    },
    md: {
      badge: 'text-sm px-3 py-1',
      icon: 'h-4 w-4',
      text: 'text-sm'
    },
    lg: {
      badge: 'text-base px-4 py-2',
      icon: 'h-5 w-5',
      text: 'text-base'
    }
  };

  const classes = sizeClasses[size];

  return (
    <div className={`flex items-center space-x-3 ${isProduction ? 'trading-mode-production' : 'trading-mode-sandbox'}`}>
      {/* 모드 표시 배지 */}
      <div className="flex items-center space-x-2">
        <Badge 
          className={`${classes.badge} flex items-center space-x-1.5 font-medium trading-mode-badge`}
        >
          {isProduction ? (
            <>
              <AlertTriangle className={`${classes.icon} text-white`} />
              <span>REAL</span>
            </>
          ) : (
            <>
              <Play className={`${classes.icon} text-white`} />
              <span>SANDBOX</span>
            </>
          )}
        </Badge>

        {/* 자동매매 상태 */}
        {settings.autoTradingEnabled && (
          <Badge variant="outline" className={`${classes.badge} flex items-center space-x-1`}>
            <TrendingUp className={`${classes.icon}`} />
            <span>자동매매</span>
          </Badge>
        )}
      </div>

      {/* 모드 설명 텍스트 */}
      <div className={`${classes.text} text-muted-foreground hidden sm:block`}>
        {isProduction ? (
          <span className="text-red-600 dark:text-red-400 font-medium">
            실제 자금으로 거래
          </span>
        ) : (
          <span className="text-green-600 dark:text-green-400 font-medium">
            가상 자금으로 연습
          </span>
        )}
      </div>

      {/* 빠른 설정 버튼 */}
      {showQuickToggle && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSettingsClick}
          className="flex items-center space-x-1"
        >
          <Settings className="h-4 w-4" />
          <span className="hidden md:inline">설정</span>
        </Button>
      )}
    </div>
  );
}

// 컴팩트 버전 (헤더용)
export function CompactTradingModeIndicator() {
  const { settings, loading, isProduction } = useTradingMode();

  if (loading) {
    return (
      <div className="flex items-center space-x-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-xs text-muted-foreground">확인중</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-2 ${isProduction ? 'trading-mode-production' : 'trading-mode-sandbox'}`}>
      <div className={`w-2 h-2 rounded-full trading-mode-indicator`}></div>
      <span className={`text-xs font-medium ${
        isProduction 
          ? 'text-red-600 dark:text-red-400' 
          : 'text-green-600 dark:text-green-400'
      }`}>
        {isProduction ? 'REAL' : 'SANDBOX'}
      </span>
      {settings.autoTradingEnabled && (
        <TrendingUp className="h-3 w-3 text-blue-500" />
      )}
    </div>
  );
}