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
import { 
  Settings, 
  Bell, 
  Palette,
  Globe,
  Save,
  Shield,
  Smartphone,
  Key
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