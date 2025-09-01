'use client';

import { useAuth } from '@/contexts/AuthContext';
import { getApiBaseUrl } from '@/lib/api-config';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import Header from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Input } from '@/components/ui/input';
import { 
  Settings, 
  Bell, 
  Palette,
  Globe,
  Save,
  Shield,
  Smartphone,
  Key,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import TwoFactorSetup from '@/components/auth/TwoFactorSetup';

interface TwoFactorStatus {
  enabled: boolean;
  setupAt?: string;
  lastUsedAt?: string;
  remainingBackupCodes?: number;
}

interface TradingSettings {
  tradingMode: 'SANDBOX' | 'PRODUCTION';
  maxDailyAmount?: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  autoTradingEnabled: boolean;
  notificationsEnabled: boolean;
  lastModeChange?: string;
}

interface TradingConfigResponse {
  success: boolean;
  data?: TradingSettings;
  error?: string;
}

function SettingsPage() {
  const { user } = useAuth();
  const router = useRouter();
  
  // 설정 상태 (실제로는 백엔드와 연동 필요)
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    trading: true,
    marketing: false
  });

  const [preferences, setPreferences] = useState({
    language: 'ko',
    timezone: 'Asia/Seoul',
    currency: 'KRW'
  });

  // 2FA 관련 상태
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [twoFactorStatus, setTwoFactorStatus] = useState<TwoFactorStatus | null>(null);
  const [showTwoFactorSetup, setShowTwoFactorSetup] = useState(false);
  const [loading, setLoading] = useState(false);

  // 트레이딩 모드 관련 상태
  const [tradingSettings, setTradingSettings] = useState<TradingSettings>({
    tradingMode: 'SANDBOX',
    riskLevel: 'MEDIUM',
    autoTradingEnabled: false,
    notificationsEnabled: true
  });
  const [tradingLoading, setTradingLoading] = useState(false);
  const [totpCode, setTotpCode] = useState('');
  const [showTotpInput, setShowTotpInput] = useState(false);

  // 2FA 상태 조회
  useEffect(() => {
    const fetchTwoFactorStatus = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) return;

        const apiBaseUrl = getApiBaseUrl();
        console.log('🔒 [Settings] Checking 2FA status at:', `${apiBaseUrl}/api/v1/auth/2fa/status`);
        const response = await fetch(`${apiBaseUrl}/api/v1/auth/2fa/status`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setTwoFactorEnabled(data.data.enabled);
            setTwoFactorStatus(data.data);
          }
        }
      } catch (error) {
        console.error('2FA 상태 조회 실패:', error);
      }
    };

    fetchTwoFactorStatus();
  }, []);

  // 트레이딩 설정 조회
  useEffect(() => {
    const fetchTradingSettings = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) return;

        const apiBaseUrl = getApiBaseUrl();
        console.log('🔧 [Settings] Fetching trading settings from:', `${apiBaseUrl}/api/v1/trading/config/settings`);
        const response = await fetch(`${apiBaseUrl}/api/v1/trading/config/settings`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (response.ok) {
          const result: TradingConfigResponse = await response.json();
          if (result.success && result.data) {
            setTradingSettings(result.data);
            console.log('✅ [Settings] Trading settings loaded:', result.data);
          }
        } else {
          console.warn('⚠️ [Settings] Failed to load trading settings:', response.status);
        }
      } catch (error) {
        console.error('❌ [Settings] Error fetching trading settings:', error);
      }
    };

    fetchTradingSettings();
  }, []);

  // 2FA 비활성화
  const handleDisableTwoFactor = async () => {
    if (!confirm('2단계 인증을 비활성화하시겠습니까? 계정 보안이 약해질 수 있습니다.')) {
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const apiBaseUrl = getApiBaseUrl();
      console.log('❌ [Settings] Disabling 2FA at:', `${apiBaseUrl}/api/v1/auth/2fa/disable`);
      const response = await fetch(`${apiBaseUrl}/api/v1/auth/2fa/disable`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      const data = await response.json();
      if (data.success) {
        setTwoFactorEnabled(false);
        setTwoFactorStatus(null);
        alert('2단계 인증이 비활성화되었습니다.');
      } else {
        alert(`오류: ${data.error || '2FA 비활성화에 실패했습니다.'}`);
      }
    } catch (error) {
      alert('2FA 비활성화 중 오류가 발생했습니다.');
      console.error('2FA 비활성화 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  // 트레이딩 모드 변경
  const handleTradingModeChange = async (newMode: 'SANDBOX' | 'PRODUCTION') => {
    // 실전투자로 변경할 때 2FA 필요 여부 확인
    if (newMode === 'PRODUCTION' && twoFactorEnabled && !showTotpInput) {
      setShowTotpInput(true);
      return;
    }

    if (newMode === 'PRODUCTION' && twoFactorEnabled && !totpCode) {
      alert('실전투자 모드 전환을 위해 인증 코드를 입력해주세요.');
      return;
    }

    const confirmMessage = newMode === 'PRODUCTION' 
      ? '실전투자 모드로 전환하시겠습니까? 실제 자금이 투입됩니다.'
      : '모의투자 모드로 전환하시겠습니까?';

    if (!confirm(confirmMessage)) {
      setShowTotpInput(false);
      setTotpCode('');
      return;
    }

    setTradingLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) throw new Error('인증 토큰이 없습니다.');

      const apiBaseUrl = getApiBaseUrl();
      console.log(`🔄 [Settings] Changing trading mode to ${newMode}:`, `${apiBaseUrl}/api/v1/trading/config/mode`);
      
      const requestData: any = {
        tradingMode: newMode,
        changeReason: `사용자가 웹 UI에서 ${newMode === 'PRODUCTION' ? '실전투자' : '모의투자'} 모드로 변경`
      };

      if (newMode === 'PRODUCTION' && totpCode) {
        requestData.totpCode = totpCode;
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/trading/config/mode`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestData)
      });

      const result: TradingConfigResponse = await response.json();
      
      if (response.ok && result.success && result.data) {
        setTradingSettings(result.data);
        setShowTotpInput(false);
        setTotpCode('');
        alert(`트레이딩 모드가 ${newMode === 'PRODUCTION' ? '실전투자' : '모의투자'}로 변경되었습니다.`);
        console.log('✅ [Settings] Trading mode changed successfully:', result.data);
      } else {
        const errorMessage = result.error || '트레이딩 모드 변경에 실패했습니다.';
        alert(`오류: ${errorMessage}`);
        console.error('❌ [Settings] Trading mode change failed:', result);
      }
    } catch (error) {
      alert('트레이딩 모드 변경 중 오류가 발생했습니다.');
      console.error('❌ [Settings] Trading mode change error:', error);
    } finally {
      setTradingLoading(false);
      setShowTotpInput(false);
      setTotpCode('');
    }
  };

  // 트레이딩 설정 업데이트
  const handleTradingSettingsUpdate = async (updates: Partial<TradingSettings>) => {
    setTradingLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) throw new Error('인증 토큰이 없습니다.');

      const apiBaseUrl = getApiBaseUrl();
      console.log('🔧 [Settings] Updating trading settings:', updates);
      
      const response = await fetch(`${apiBaseUrl}/api/v1/trading/config/settings`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          ...tradingSettings,
          ...updates
        })
      });

      const result: TradingConfigResponse = await response.json();
      
      if (response.ok && result.success && result.data) {
        setTradingSettings(result.data);
        console.log('✅ [Settings] Trading settings updated:', result.data);
      } else {
        const errorMessage = result.error || '트레이딩 설정 업데이트에 실패했습니다.';
        alert(`오류: ${errorMessage}`);
      }
    } catch (error) {
      alert('트레이딩 설정 업데이트 중 오류가 발생했습니다.');
      console.error('❌ [Settings] Trading settings update error:', error);
    } finally {
      setTradingLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container max-w-6xl mx-auto py-8 px-4">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">설정</h1>
              <p className="text-muted-foreground">계정 및 애플리케이션 설정</p>
            </div>
            <Button variant="default" size="sm">
              <Save className="w-4 h-4 mr-2" />
              설정 저장
            </Button>
          </div>
        </div>

        <div className="grid gap-8">
          {/* 2FA 설정이 활성화된 경우 모달 */}
          {showTwoFactorSetup && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
              <div className="w-full max-w-md mx-4">
                <TwoFactorSetup
                  isEnabled={twoFactorEnabled}
                  onStatusChange={(enabled) => {
                    setShowTwoFactorSetup(false);
                    setTwoFactorEnabled(enabled);
                    if (enabled) {
                      // 상태 새로고침
                      window.location.reload();
                    }
                  }}
                />
              </div>
            </div>
          )}

          {/* 보안 설정 (2FA) */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Shield className="w-5 h-5 mr-2" />
                보안 설정
              </CardTitle>
              <CardDescription>
                계정 보안을 강화하고 2단계 인증을 관리합니다
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-sm font-medium flex items-center">
                    <Smartphone className="w-4 h-4 mr-2" />
                    2단계 인증 (2FA)
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Google Authenticator 등의 앱을 사용하여 추가 보안 계층을 제공합니다
                  </p>
                  {twoFactorEnabled && twoFactorStatus && (
                    <div className="flex items-center space-x-2 mt-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-xs text-green-600">
                        활성화됨 • 백업 코드 {twoFactorStatus.remainingBackupCodes || 0}개 남음
                      </span>
                      {twoFactorStatus.setupAt && (
                        <span className="text-xs text-muted-foreground">
                          • {new Date(twoFactorStatus.setupAt).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  )}
                </div>
                
                <div className="flex space-x-2">
                  {!twoFactorEnabled ? (
                    <Button
                      size="sm"
                      onClick={() => setShowTwoFactorSetup(true)}
                      disabled={loading}
                      className="bg-primary hover:bg-primary/90"
                    >
                      <Key className="w-4 h-4 mr-2" />
                      활성화
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={handleDisableTwoFactor}
                      disabled={loading}
                    >
                      비활성화
                    </Button>
                  )}
                </div>
              </div>

              {twoFactorEnabled && (
                <>
                  <Separator />
                  <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                    <div className="flex">
                      <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3" />
                      <div className="space-y-1">
                        <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                          2단계 인증이 활성화되었습니다
                        </h4>
                        <p className="text-xs text-blue-700 dark:text-blue-200">
                          로그인 시 비밀번호와 함께 인증 앱에서 생성된 6자리 코드가 필요합니다.
                          백업 코드는 안전한 곳에 보관하세요.
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* 트레이딩 모드 설정 */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <TrendingUp className="w-5 h-5 mr-2" />
                트레이딩 모드 설정
              </CardTitle>
              <CardDescription>
                모의투자와 실전투자 모드를 선택하고 거래 관련 설정을 관리합니다
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content space-y-6">
              {/* 현재 모드 표시 */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-sm font-medium flex items-center">
                    현재 트레이딩 모드
                  </Label>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      tradingSettings.tradingMode === 'PRODUCTION' ? 'bg-red-500' : 'bg-green-500'
                    }`}></div>
                    <span className={`text-sm font-medium ${
                      tradingSettings.tradingMode === 'PRODUCTION' 
                        ? 'text-red-600 dark:text-red-400' 
                        : 'text-green-600 dark:text-green-400'
                    }`}>
                      {tradingSettings.tradingMode === 'PRODUCTION' ? '실전투자' : '모의투자'}
                    </span>
                    {tradingSettings.lastModeChange && (
                      <span className="text-xs text-muted-foreground">
                        • {new Date(tradingSettings.lastModeChange).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {tradingSettings.tradingMode === 'PRODUCTION' 
                      ? '실제 자금으로 거래합니다. 주의해서 사용하세요.'
                      : '가상 자금으로 안전하게 거래를 연습할 수 있습니다.'
                    }
                  </p>
                </div>
                
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant={tradingSettings.tradingMode === 'SANDBOX' ? 'default' : 'outline'}
                    onClick={() => handleTradingModeChange('SANDBOX')}
                    disabled={tradingLoading || tradingSettings.tradingMode === 'SANDBOX'}
                  >
                    모의투자
                  </Button>
                  <Button
                    size="sm"
                    variant={tradingSettings.tradingMode === 'PRODUCTION' ? 'default' : 'outline'}
                    onClick={() => handleTradingModeChange('PRODUCTION')}
                    disabled={tradingLoading || tradingSettings.tradingMode === 'PRODUCTION'}
                    className={tradingSettings.tradingMode === 'PRODUCTION' ? 'bg-red-600 hover:bg-red-700' : ''}
                  >
                    <AlertTriangle className="w-4 h-4 mr-1" />
                    실전투자
                  </Button>
                </div>
              </div>

              {/* 2FA 코드 입력 (실전투자 모드 전환 시) */}
              {showTotpInput && (
                <>
                  <Separator />
                  <div className="bg-yellow-50 dark:bg-yellow-950/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                    <div className="space-y-3">
                      <div className="flex items-center">
                        <Shield className="w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2" />
                        <h4 className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                          실전투자 모드 전환 인증
                        </h4>
                      </div>
                      <p className="text-xs text-yellow-700 dark:text-yellow-200">
                        실전투자 모드로 전환하려면 Google Authenticator 앱에서 6자리 인증 코드를 입력해주세요.
                      </p>
                      <div className="flex space-x-2">
                        <Input
                          type="text"
                          placeholder="000000"
                          value={totpCode}
                          onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                          maxLength={6}
                          className="w-24 text-center"
                        />
                        <Button
                          size="sm"
                          onClick={() => handleTradingModeChange('PRODUCTION')}
                          disabled={tradingLoading || totpCode.length !== 6}
                        >
                          확인
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setShowTotpInput(false);
                            setTotpCode('');
                          }}
                        >
                          취소
                        </Button>
                      </div>
                    </div>
                  </div>
                </>
              )}

              <Separator />

              {/* 리스크 관리 설정 */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">리스크 관리</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="risk-level">리스크 레벨</Label>
                    <Select 
                      value={tradingSettings.riskLevel} 
                      onValueChange={(value: 'LOW' | 'MEDIUM' | 'HIGH') => 
                        handleTradingSettingsUpdate({ riskLevel: value })
                      }
                      disabled={tradingLoading}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="LOW">낮음 - 보수적</SelectItem>
                        <SelectItem value="MEDIUM">중간 - 균형</SelectItem>
                        <SelectItem value="HIGH">높음 - 공격적</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="max-daily-amount">일일 최대 거래금액</Label>
                    <Input
                      type="number"
                      placeholder="1000000"
                      value={tradingSettings.maxDailyAmount || ''}
                      onChange={(e) => handleTradingSettingsUpdate({ 
                        maxDailyAmount: e.target.value ? parseInt(e.target.value) : undefined 
                      })}
                      disabled={tradingLoading}
                    />
                    <p className="text-xs text-muted-foreground">
                      비워두면 제한 없음 (단위: 원)
                    </p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* 자동매매 설정 */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="auto-trading" className="text-sm font-medium">
                    자동매매 활성화
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    알고리즘 기반 자동 거래를 허용합니다
                  </p>
                </div>
                <Switch
                  id="auto-trading"
                  checked={tradingSettings.autoTradingEnabled}
                  onCheckedChange={(checked) => handleTradingSettingsUpdate({ autoTradingEnabled: checked })}
                  disabled={tradingLoading}
                />
              </div>

              <Separator />

              {/* 거래 알림 설정 */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="trading-notifications-config" className="text-sm font-medium">
                    거래 알림
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    주문 체결, 리스크 알림 등을 받습니다
                  </p>
                </div>
                <Switch
                  id="trading-notifications-config"
                  checked={tradingSettings.notificationsEnabled}
                  onCheckedChange={(checked) => handleTradingSettingsUpdate({ notificationsEnabled: checked })}
                  disabled={tradingLoading}
                />
              </div>

              {/* 실전투자 모드 경고 */}
              {tradingSettings.tradingMode === 'PRODUCTION' && (
                <>
                  <Separator />
                  <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                    <div className="flex">
                      <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-3" />
                      <div className="space-y-1">
                        <h4 className="text-sm font-medium text-red-900 dark:text-red-100">
                          실전투자 모드 활성화
                        </h4>
                        <p className="text-xs text-red-700 dark:text-red-200">
                          현재 실제 자금으로 거래가 진행됩니다. 모든 주문은 실제로 체결되며 손실이 발생할 수 있습니다.
                          거래 전에 반드시 리스크를 확인하세요.
                        </p>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* 알림 설정 */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Bell className="w-5 h-5 mr-2" />
                알림 설정
              </CardTitle>
              <CardDescription>
                받고 싶은 알림 유형을 선택하세요
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="email-notifications" className="text-sm font-medium">
                    이메일 알림
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    중요한 거래 및 시스템 알림을 이메일로 받습니다
                  </p>
                </div>
                <Switch
                  id="email-notifications"
                  checked={notifications.email}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, email: checked }))
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="push-notifications" className="text-sm font-medium">
                    푸시 알림
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    브라우저 푸시 알림을 받습니다
                  </p>
                </div>
                <Switch
                  id="push-notifications"
                  checked={notifications.push}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, push: checked }))
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="trading-notifications" className="text-sm font-medium">
                    거래 알림
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    주문 체결, 포지션 변경 등 거래 관련 알림을 받습니다
                  </p>
                </div>
                <Switch
                  id="trading-notifications"
                  checked={notifications.trading}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, trading: checked }))
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="marketing-notifications" className="text-sm font-medium">
                    마케팅 알림
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    새로운 기능, 이벤트 등 마케팅 정보를 받습니다
                  </p>
                </div>
                <Switch
                  id="marketing-notifications"
                  checked={notifications.marketing}
                  onCheckedChange={(checked) => 
                    setNotifications(prev => ({ ...prev, marketing: checked }))
                  }
                />
              </div>
            </CardContent>
          </Card>

          {/* 개인화 설정 */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Palette className="w-5 h-5 mr-2" />
                개인화 설정
              </CardTitle>
              <CardDescription>
                언어, 시간대, 테마 등을 설정합니다
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="language">언어</Label>
                  <Select value={preferences.language} onValueChange={(value) => 
                    setPreferences(prev => ({ ...prev, language: value }))
                  }>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ko">한국어</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="ja">日本語</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timezone">시간대</Label>
                  <Select value={preferences.timezone} onValueChange={(value) => 
                    setPreferences(prev => ({ ...prev, timezone: value }))
                  }>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Seoul">서울 (UTC+9)</SelectItem>
                      <SelectItem value="Asia/Tokyo">도쿄 (UTC+9)</SelectItem>
                      <SelectItem value="America/New_York">뉴욕 (UTC-5)</SelectItem>
                      <SelectItem value="Europe/London">런던 (UTC+0)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="currency">기본 통화</Label>
                  <Select value={preferences.currency} onValueChange={(value) => 
                    setPreferences(prev => ({ ...prev, currency: value }))
                  }>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="KRW">원화 (KRW)</SelectItem>
                      <SelectItem value="USD">미국 달러 (USD)</SelectItem>
                      <SelectItem value="JPY">일본 엔 (JPY)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

        </div>
      </main>
    </div>
  );
}

export default function ProtectedSettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsPage />
    </ProtectedRoute>
  );
}