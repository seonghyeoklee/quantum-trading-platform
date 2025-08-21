'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, Shield, AlertCircle, Loader2 } from 'lucide-react';

interface LoginFormProps {
  onSuccess?: () => void;
  redirectTo?: string;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, redirectTo = '/dashboard' }) => {
  const { login, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // 입력 시 에러 메시지 클리어
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting) return;
    
    // 유효성 검사
    if (!formData.username.trim()) {
      setError('사용자명을 입력해주세요.');
      return;
    }
    
    if (!formData.password) {
      setError('비밀번호를 입력해주세요.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      await login(formData.username.trim(), formData.password);
      
      if (onSuccess) {
        onSuccess();
      } else {
        // 기본 리다이렉트
        window.location.href = redirectTo;
      }
      
    } catch (err: any) {
      console.error('Login error:', err);
      
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('로그인 중 오류가 발생했습니다. 다시 시도해주세요.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* 헤더 */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
            <Shield className="h-6 w-6 text-blue-600" />
          </div>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">
            관리자 로그인
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Quantum Trading Platform에 로그인하세요
          </p>
        </div>

        {/* 로그인 폼 */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="text-center">로그인 정보 입력</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-6" onSubmit={handleSubmit}>
              {/* 에러 메시지 */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* 사용자명 */}
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                  사용자명
                </label>
                <div className="mt-1">
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    required
                    value={formData.username}
                    onChange={handleChange}
                    className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="사용자명을 입력하세요"
                    disabled={isSubmitting || isLoading}
                  />
                </div>
              </div>

              {/* 비밀번호 */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  비밀번호
                </label>
                <div className="mt-1 relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className="appearance-none relative block w-full px-3 py-2 pr-10 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="비밀번호를 입력하세요"
                    disabled={isSubmitting || isLoading}
                  />
                  <button
                    type="button"
                    onClick={togglePasswordVisibility}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    disabled={isSubmitting || isLoading}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                    )}
                  </button>
                </div>
              </div>

              {/* 로그인 버튼 */}
              <div>
                <Button
                  type="submit"
                  className="w-full flex justify-center items-center"
                  disabled={isSubmitting || isLoading}
                >
                  {isSubmitting || isLoading ? (
                    <>
                      <Loader2 className="animate-spin h-4 w-4 mr-2" />
                      로그인 중...
                    </>
                  ) : (
                    '로그인'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* 테스트 계정 정보 */}
        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-sm">테스트 계정</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs text-gray-600">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="font-semibold">관리자</div>
                <div>admin / password</div>
                <div className="text-xs text-blue-600">모든 권한</div>
              </div>
              <div>
                <div className="font-semibold">매니저</div>
                <div>manager / password</div>
                <div className="text-xs text-green-600">포트폴리오 관리</div>
              </div>
              <div>
                <div className="font-semibold">트레이더</div>
                <div>trader / password</div>
                <div className="text-xs text-orange-600">거래 전용</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 보안 안내 */}
        <div className="text-center text-xs text-gray-500">
          <p>이 시스템은 승인된 관리자만 접근할 수 있습니다.</p>
          <p>모든 접근 기록은 보안 목적으로 로깅됩니다.</p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;