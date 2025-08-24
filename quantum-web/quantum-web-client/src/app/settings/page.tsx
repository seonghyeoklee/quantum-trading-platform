'use client';

import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import UserLayout from '@/components/layout/UserLayout';
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
  Save
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

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

  if (!user) return null;

  const settingsActions = (
    <Button variant="default" size="sm">
      <Save className="w-4 h-4 mr-2" />
      설정 저장
    </Button>
  );

  return (
    <UserLayout 
      title="설정"
      subtitle="계정 및 애플리케이션 설정"
      actions={settingsActions}
    >
        <div className="grid gap-8">
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

          {/* 저장 버튼 */}
          <div className="flex justify-end space-x-4">
            <Button variant="outline" onClick={() => router.back()}>
              취소
            </Button>
            <Button className="bg-primary hover:bg-primary/90">
              설정 저장
            </Button>
          </div>
        </div>
    </UserLayout>
  );
}

export default function ProtectedSettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsPage />
    </ProtectedRoute>
  );
}