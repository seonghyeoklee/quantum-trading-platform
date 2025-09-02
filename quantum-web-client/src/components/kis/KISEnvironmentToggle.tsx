'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TestTube, 
  Zap, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw
} from 'lucide-react';

interface KISEnvironmentToggleProps {
  variant?: 'toggle' | 'buttons' | 'compact';
  showStatus?: boolean;
}

export function KISEnvironmentToggle({ variant = 'toggle', showStatus = true }: KISEnvironmentToggleProps) {
  const { hasKISAccount, kisTokens, refreshKISToken } = useAuth();
  const [currentEnvironment, setCurrentEnvironment] = useState<'LIVE' | 'SANDBOX'>('SANDBOX');
  const [isRefreshing, setIsRefreshing] = useState(false);

  if (!hasKISAccount) {
    return null;
  }

  const sandboxToken = kisTokens.sandbox;
  const liveToken = kisTokens.live;
  const activeToken = currentEnvironment === 'SANDBOX' ? sandboxToken : liveToken;

  const handleEnvironmentChange = async (environment: 'LIVE' | 'SANDBOX') => {
    setCurrentEnvironment(environment);
    
    // 해당 환경의 토큰이 없거나 만료되었으면 새로 발급
    const token = environment === 'SANDBOX' ? sandboxToken : liveToken;
    if (!token || new Date(token.expiresAt) <= new Date()) {
      setIsRefreshing(true);
      try {
        await refreshKISToken(environment);
      } catch (error) {
        console.error(`Failed to refresh ${environment} token:`, error);
      } finally {
        setIsRefreshing(false);
      }
    }
  };

  const isTokenValid = (token: any) => {
    if (!token) return false;
    return new Date(token.expiresAt) > new Date();
  };

  if (variant === 'compact') {
    return (
      <div className="flex items-center space-x-2">
        <Badge 
          variant={currentEnvironment === 'SANDBOX' ? 'secondary' : 'destructive'}
          className="text-xs"
        >
          {currentEnvironment === 'SANDBOX' ? '모의투자' : '실전투자'}
        </Badge>
        {showStatus && (
          <div className={`w-2 h-2 rounded-full ${
            isTokenValid(activeToken) ? 'bg-green-500' : 'bg-red-500'
          }`} />
        )}
      </div>
    );
  }

  if (variant === 'buttons') {
    return (
      <div className="space-y-3">
        <div className="flex space-x-2">
          <Button
            variant={currentEnvironment === 'SANDBOX' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleEnvironmentChange('SANDBOX')}
            className="flex-1"
            disabled={isRefreshing}
          >
            <TestTube className="w-4 h-4 mr-2" />
            모의투자
            {isTokenValid(sandboxToken) && (
              <CheckCircle className="w-3 h-3 ml-2 text-green-500" />
            )}
          </Button>
          
          <Button
            variant={currentEnvironment === 'LIVE' ? 'default' : 'outline'}
            size="sm"
            onClick={() => handleEnvironmentChange('LIVE')}
            className="flex-1"
            disabled={isRefreshing}
          >
            <Zap className="w-4 h-4 mr-2" />
            실전투자
            {isTokenValid(liveToken) && (
              <CheckCircle className="w-3 h-3 ml-2 text-green-500" />
            )}
          </Button>
        </div>
        
        {showStatus && (
          <div className="text-xs text-muted-foreground flex items-center space-x-2">
            {isRefreshing ? (
              <>
                <RefreshCw className="w-3 h-3 animate-spin" />
                <span>토큰 갱신 중...</span>
              </>
            ) : activeToken ? (
              <>
                <div className={`w-2 h-2 rounded-full ${
                  isTokenValid(activeToken) ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <span>
                  {isTokenValid(activeToken) 
                    ? `토큰 유효 (${new Date(activeToken.expiresAt).toLocaleTimeString()}까지)`
                    : '토큰 만료됨'
                  }
                </span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-gray-400" />
                <span>토큰 없음</span>
              </>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="font-medium">거래 환경</span>
            <Badge 
              variant={currentEnvironment === 'SANDBOX' ? 'secondary' : 'destructive'}
              className="text-xs"
            >
              {currentEnvironment === 'SANDBOX' ? '모의투자' : '실전투자'}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {currentEnvironment === 'SANDBOX' 
              ? '가상 자금으로 안전하게 테스트할 수 있습니다' 
              : '실제 자금이 사용되는 환경입니다'
            }
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <TestTube className={`w-4 h-4 ${currentEnvironment === 'SANDBOX' ? 'text-blue-600' : 'text-gray-400'}`} />
            <Switch
              checked={currentEnvironment === 'LIVE'}
              onCheckedChange={(checked) => 
                handleEnvironmentChange(checked ? 'LIVE' : 'SANDBOX')
              }
              disabled={isRefreshing}
            />
            <Zap className={`w-4 h-4 ${currentEnvironment === 'LIVE' ? 'text-red-600' : 'text-gray-400'}`} />
          </div>
        </div>
      </div>

      {currentEnvironment === 'LIVE' && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>주의:</strong> 실전투자 모드에서는 실제 자금이 사용됩니다. 
            모의투자에서 충분히 테스트한 후 사용하시기 바랍니다.
          </AlertDescription>
        </Alert>
      )}

      {showStatus && activeToken && (
        <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              isTokenValid(activeToken) ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <div>
              <div className="font-medium text-sm">
                {isTokenValid(activeToken) ? '연결됨' : '연결 끊어짐'}
              </div>
              <div className="text-xs text-muted-foreground">
                {isTokenValid(activeToken) 
                  ? `${new Date(activeToken.expiresAt).toLocaleString()}까지 유효`
                  : '토큰이 만료되었습니다'
                }
              </div>
            </div>
          </div>
          
          {!isTokenValid(activeToken) && (
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => handleEnvironmentChange(currentEnvironment)}
              disabled={isRefreshing}
            >
              {isRefreshing ? (
                <>
                  <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                  갱신 중
                </>
              ) : (
                <>
                  <RefreshCw className="w-3 h-3 mr-1" />
                  토큰 갱신
                </>
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

export default KISEnvironmentToggle;