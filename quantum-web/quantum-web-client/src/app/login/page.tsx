'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { getApiBaseUrl } from '@/lib/api-config';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, LogIn, AlertCircle, Shield, TrendingUp } from 'lucide-react';
import TwoFactorLogin from '@/components/auth/TwoFactorLogin';

export default function LoginPage() {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [twoFactorRequired, setTwoFactorRequired] = useState(false);
  const [tempSessionToken, setTempSessionToken] = useState('');
  const [currentUsername, setCurrentUsername] = useState('');
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // 먼저 2FA 확인을 위해 직접 API 호출
      const apiBaseUrl = getApiBaseUrl();
      const loginUrl = `${apiBaseUrl}/api/v1/auth/login`;
      console.log('🔐 [Login] Attempting login to:', loginUrl);
      
      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        })
      });

      if (!response.ok) {
        console.error('❌ [Login] Login failed with status:', response.status);
        const errorData = await response.json();
        throw new Error(errorData.message || '로그인에 실패했습니다.');
      }

      const data = await response.json();
      console.log('✅ [Login] Login response received, requiresTwoFactor:', data.requiresTwoFactor);
      
      if (data.requiresTwoFactor) {
        // 2FA가 필요한 경우
        setTwoFactorRequired(true);
        setTempSessionToken(data.tempSessionToken);
        setCurrentUsername(data.user.username);
        setError('');
      } else {
        // 2FA가 필요하지 않은 경우 - AuthContext의 상태만 직접 업데이트
        if (data.accessToken) {
          localStorage.setItem('accessToken', data.accessToken);
          localStorage.setItem('refreshToken', data.refreshToken);
          localStorage.setItem('user', JSON.stringify(data.user));
          
          // AuthContext 상태 업데이트를 위해 페이지 새로고침 대신 네비게이션 사용
          router.push('/');
        }
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : '로그인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTwoFactorVerify = async (code: string, isBackupCode?: boolean) => {
    setIsLoading(true);
    setError('');

    try {
      const apiBaseUrl = getApiBaseUrl();
      const twoFactorUrl = `${apiBaseUrl}/api/v1/auth/2fa/verify-login`;
      console.log('🔐 [2FA] Attempting 2FA verification to:', twoFactorUrl);
      
      const response = await fetch(twoFactorUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          username: currentUsername,
          code: code,
          sessionToken: tempSessionToken,
          isBackupCode: isBackupCode || false
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '2FA 인증에 실패했습니다.');
      }

      const data = await response.json();
      
      if (data.success && data.data.accessToken) {
        // 인증 성공 시 토큰 저장 
        localStorage.setItem('accessToken', data.data.accessToken);
        localStorage.setItem('refreshToken', data.data.refreshToken || '');
        localStorage.setItem('user', JSON.stringify(data.data.user));
        
        // 메인 페이지로 리디렉트 (AuthContext가 자동으로 상태 업데이트)
        router.push('/');
      } else {
        throw new Error('인증에 실패했습니다.');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : '2FA 인증 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    setTwoFactorRequired(false);
    setTempSessionToken('');
    setCurrentUsername('');
    setError('');
    setFormData({ username: '', password: '' });
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        {/* 로고 헤더 */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-3">
            <div className="w-10 h-10 bg-primary rounded flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">Quantum Trading</h1>
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">
              {twoFactorRequired ? '2단계 인증' : '로그인'}
            </h2>
            <p className="text-sm text-muted-foreground">
              {twoFactorRequired ? '보안 코드를 입력하여 인증을 완료하세요' : '계정에 로그인하여 거래를 시작하세요'}
            </p>
          </div>
        </div>

        {twoFactorRequired ? (
          // 2FA 인증 화면
          <TwoFactorLogin
            username={currentUsername}
            onVerify={handleTwoFactorVerify}
            onBack={handleBackToLogin}
            loading={isLoading}
            error={error}
          />
        ) : (
          <>
            {/* 로그인 카드 */}
            <Card className="trading-card">
              <CardContent className="trading-card-content space-y-4">
                <form onSubmit={handleSubmit} className="space-y-4">
                  {/* 에러 메시지 */}
                  {error && (
                    <Alert className="border-destructive/50 text-destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}

                  {/* 사용자명 필드 */}
                  <div className="space-y-2">
                    <Label htmlFor="username" className="text-sm font-medium">
                      사용자명
                    </Label>
                    <Input
                      id="username"
                      name="username"
                      type="text"
                      placeholder="사용자명을 입력하세요"
                      value={formData.username}
                      onChange={handleInputChange}
                      className="h-10"
                      required
                      disabled={isLoading}
                    />
                  </div>

                  {/* 비밀번호 필드 */}
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-sm font-medium">
                      비밀번호
                    </Label>
                    <div className="relative">
                      <Input
                        id="password"
                        name="password"
                        type={showPassword ? "text" : "password"}
                        placeholder="비밀번호를 입력하세요"
                        value={formData.password}
                        onChange={handleInputChange}
                        className="h-10 pr-12"
                        required
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 flex items-center justify-center w-10 text-muted-foreground hover:text-foreground transition-colors"
                        disabled={isLoading}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* 로그인 버튼 */}
                  <Button
                    type="submit"
                    className="w-full h-10 bg-primary hover:bg-primary/90 text-primary-foreground font-medium mt-6"
                    disabled={isLoading || !formData.username || !formData.password}
                  >
                    {isLoading ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                        <span>로그인 중...</span>
                      </div>
                    ) : (
                      <div className="flex items-center space-x-2">
                        <LogIn className="w-4 h-4" />
                        <span>로그인</span>
                      </div>
                    )}
                  </Button>
                </form>

                {/* 추가 링크 */}
                <div className="text-center text-sm text-muted-foreground pt-4 border-t border-border">
                  <p>계정이 필요하시나요? <span className="text-primary font-medium hover:underline cursor-pointer">관리자에게 문의하세요</span></p>
                </div>
              </CardContent>
            </Card>

            {/* 보안 안내 */}
            <Card className="border border-border bg-muted/30">
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                    <Shield className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-foreground text-sm mb-1">보안 안내</h4>
                    <p className="text-muted-foreground text-sm leading-relaxed">
                      안전한 거래를 위해 개인 계정 정보를 타인과 공유하지 마세요.<br />
                      보안 강화를 위해 <span className="font-medium text-primary">2단계 인증</span> 설정을 권장합니다.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}