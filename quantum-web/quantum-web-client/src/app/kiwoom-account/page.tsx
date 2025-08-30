'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Header from "@/components/layout/Header";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, AlertCircle, Lock, RefreshCw, Loader2, BookOpen } from "lucide-react";

interface KiwoomAccountInfo {
  hasAccount: boolean;
  kiwoomAccountId?: string;
  assignedAt?: string;
  credentialsUpdatedAt?: string;
  isActive?: boolean;
  hasValidToken?: boolean;
  tokenExpiresAt?: string;
}

function KiwoomAccountManagement() {
  const [accountInfo, setAccountInfo] = useState<KiwoomAccountInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch account information
  const fetchAccountInfo = async () => {
    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      if (!token) {
        setError('로그인이 필요합니다');
        setLoading(false);
        return;
      }
      
      const response = await fetch('/api/kiwoom-accounts/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAccountInfo(data);
      } else {
        setError('Failed to fetch account information');
      }
    } catch {
      setError('Error connecting to server');
    } finally {
      setLoading(false);
    }
  };

  // Register new account
  const registerAccount = async () => {
    if (!clientId || !clientSecret) {
      setError('App Key와 App Secret 모두 입력해주세요');
      return;
    }

    setRegistering(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      const response = await fetch('/api/kiwoom-accounts/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          clientId,
          clientSecret
        })
      });

      if (response.ok) {
        await response.json();
        setSuccess('키움증권 계정이 성공적으로 등록되었습니다');
        setClientId('');
        setClientSecret('');
        await fetchAccountInfo();
      } else {
        const data = await response.json();
        setError(data.message || '계정 등록에 실패했습니다');
      }
    } catch {
      setError('서버 연결 오류가 발생했습니다');
    } finally {
      setRegistering(false);
    }
  };

  // Update credentials
  const updateCredentials = async () => {
    if (!clientId || !clientSecret) {
      setError('Please provide both Client ID and Client Secret');
      return;
    }

    setUpdating(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      const response = await fetch('/api/kiwoom-accounts/me/credentials', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          clientId,
          clientSecret
        })
      });

      if (response.ok) {
        setSuccess('Credentials updated successfully');
        setClientId('');
        setClientSecret('');
        await fetchAccountInfo();
      } else {
        const data = await response.json();
        setError(data.message || 'Failed to update credentials');
      }
    } catch {
      setError('Error connecting to server');
    } finally {
      setUpdating(false);
    }
  };

  // Get new token
  const getNewToken = async () => {
    setUpdating(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      const response = await fetch('/api/kiwoom-accounts/me/token', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.hasToken) {
          setSuccess('Token refreshed successfully');
          await fetchAccountInfo();
        } else {
          setError(data.message || 'No valid token available');
        }
      } else {
        setError('Failed to refresh token');
      }
    } catch {
      setError('Error connecting to server');
    } finally {
      setUpdating(false);
    }
  };

  useEffect(() => {
    fetchAccountInfo();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="flex items-center justify-center h-96">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container max-w-5xl mx-auto py-8 px-4">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">키움증권 계좌 관리</h1>
              <p className="text-muted-foreground">키움증권 Open API를 통한 자동매매를 위한 계좌 설정을 관리합니다.</p>
            </div>
          </div>
        </div>

        {/* Account Status Card */}
        <Card className="mb-8 shadow-lg border-0 bg-gradient-to-br from-card to-card/80">
          <CardHeader className="pb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-primary" />
              </div>
              <div>
                <CardTitle className="text-xl">계좌 연결 상태</CardTitle>
                <CardDescription className="text-base mt-1">
                  현재 키움증권 계좌 연결 상태를 확인합니다.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="space-y-6">
              {accountInfo?.hasAccount ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 계좌 정보 */}
                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-muted/30 border">
                      <div className="text-sm font-medium text-muted-foreground mb-1">계좌 ID</div>
                      <div className="font-mono text-sm bg-background px-2 py-1 rounded border">
                        {accountInfo.kiwoomAccountId}
                      </div>
                    </div>
                    
                    {accountInfo.assignedAt && (
                      <div className="p-4 rounded-lg bg-muted/30 border">
                        <div className="text-sm font-medium text-muted-foreground mb-1">연결 시작일</div>
                        <div className="text-sm">
                          {new Date(accountInfo.assignedAt).toLocaleDateString('ko-KR', {
                            year: 'numeric',
                            month: 'long', 
                            day: 'numeric',
                            weekday: 'long'
                          })}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 상태 정보 */}
                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-muted/30 border">
                      <div className="text-sm font-medium text-muted-foreground mb-2">연결 상태</div>
                      <Badge variant={accountInfo.isActive ? "default" : "secondary"} className="text-sm">
                        {accountInfo.isActive ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            활성 상태
                          </>
                        ) : (
                          <>
                            <AlertCircle className="w-3 h-3 mr-1" />
                            비활성 상태
                          </>
                        )}
                      </Badge>
                    </div>
                    
                    <div className="p-4 rounded-lg bg-muted/30 border">
                      <div className="text-sm font-medium text-muted-foreground mb-2">API 토큰 상태</div>
                      <div className="space-y-2">
                        <Badge variant={accountInfo.hasValidToken ? "default" : "destructive"} className="text-sm">
                          {accountInfo.hasValidToken ? (
                            <>
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              유효함
                            </>
                          ) : (
                            <>
                              <AlertCircle className="w-3 h-3 mr-1" />
                              만료됨
                            </>
                          )}
                        </Badge>
                        {accountInfo.tokenExpiresAt && (
                          <div className="text-xs text-muted-foreground">
                            만료일: {new Date(accountInfo.tokenExpiresAt).toLocaleDateString('ko-KR')}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <Alert className="border-amber-200 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-800">
                  <AlertCircle className="h-4 w-4 text-amber-600" />
                  <AlertDescription className="text-amber-800 dark:text-amber-200">
                    키움증권 계좌가 연결되어 있지 않습니다. 아래에서 API 키를 등록하여 자동매매를 시작하세요.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>

        {/* API Credentials Card - 항상 표시 */}
        <Card className="mb-8 shadow-lg border-0 bg-gradient-to-br from-card to-card/80">
            <CardHeader className="pb-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <Lock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <CardTitle className="text-xl">API 인증 정보</CardTitle>
                  <CardDescription className="text-base mt-1">
                    {accountInfo?.hasAccount 
                      ? "키움증권 Open API 인증 정보를 업데이트합니다."
                      : "키움증권 Open API에서 발급받은 App Key와 App Secret을 입력하세요."}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-2">
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="client-id" className="text-sm font-semibold">
                      App Key (Client ID)
                    </Label>
                    <Input
                      id="client-id"
                      type="text"
                      placeholder="키움증권에서 발급받은 App Key를 입력하세요"
                      value={clientId}
                      onChange={(e) => setClientId(e.target.value)}
                      className="h-12 text-sm"
                    />
                    <p className="text-xs text-muted-foreground">
                      키움증권 Open API 센터에서 발급받은 앱 키를 입력하세요
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="client-secret" className="text-sm font-semibold">
                      App Secret (Client Secret)
                    </Label>
                    <Input
                      id="client-secret"
                      type="password"
                      placeholder="키움증권에서 발급받은 App Secret을 입력하세요"
                      value={clientSecret}
                      onChange={(e) => setClientSecret(e.target.value)}
                      className="h-12 text-sm"
                    />
                    <p className="text-xs text-muted-foreground">
                      보안을 위해 암호화되어 저장됩니다
                    </p>
                  </div>
                </div>
                
                {/* Messages */}
                {error && (
                  <Alert variant="destructive" className="border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-800 dark:text-red-200">
                      {error}
                    </AlertDescription>
                  </Alert>
                )}
                
                {success && (
                  <Alert className="border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-800">
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800 dark:text-green-200">
                      {success}
                    </AlertDescription>
                  </Alert>
                )}
                
                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 pt-2">
                  {!accountInfo?.hasAccount ? (
                    <Button 
                      onClick={registerAccount} 
                      disabled={registering || !clientId || !clientSecret}
                      size="lg"
                      className="h-12 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium shadow-lg"
                    >
                      {registering ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          등록 중...
                        </>
                      ) : (
                        <>
                          <Lock className="w-4 h-4 mr-2" />
                          키움증권 계정 등록하기
                        </>
                      )}
                    </Button>
                  ) : (
                    <>
                      <Button 
                        onClick={updateCredentials} 
                        disabled={updating || !clientId || !clientSecret}
                        size="lg"
                        className="h-12 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white font-medium shadow-lg"
                      >
                        {updating ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            업데이트 중...
                          </>
                        ) : (
                          <>
                            <Lock className="w-4 h-4 mr-2" />
                            인증 정보 업데이트
                          </>
                        )}
                      </Button>
                      
                      <Button 
                        onClick={getNewToken} 
                        variant="outline"
                        size="lg"
                        disabled={updating}
                        className="h-12 border-2 border-primary/20 hover:border-primary/40 hover:bg-primary/5"
                      >
                        {updating ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            처리 중...
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            API 토큰 갱신
                          </>
                        )}
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

        {/* Instructions Card */}
        <Card className="shadow-lg border-0 bg-gradient-to-br from-card to-card/80">
          <CardHeader className="pb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <CardTitle className="text-xl">설정 가이드</CardTitle>
                <CardDescription className="text-base mt-1">
                  키움증권 API 연동을 위한 단계별 설정 방법입니다.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* API 키 발급 단계 */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">1</div>
                    <h3 className="font-semibold">API 키 발급</h3>
                  </div>
                  <div className="pl-8 space-y-2">
                    <p className="text-sm text-muted-foreground">
                      <a href="https://openapi.kiwoom.com/main/home" target="_blank" rel="noopener noreferrer" 
                         className="text-blue-600 hover:text-blue-800 hover:underline font-medium inline-flex items-center">
                        키움증권 Open API 센터
                        <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>에서 새로운 앱을 등록하고 App Key와 App Secret을 발급받으세요.
                    </p>
                  </div>
                </div>

                {/* 계정 등록 단계 */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">2</div>
                    <h3 className="font-semibold">계정 등록</h3>
                  </div>
                  <div className="pl-8 space-y-2">
                    <p className="text-sm text-muted-foreground">
                      발급받은 App Key와 App Secret을 위의 입력란에 입력한 후 
                      {accountInfo?.hasAccount ? ' "인증 정보 업데이트"' : ' "키움증권 계정 등록하기"'} 버튼을 클릭하세요.
                    </p>
                  </div>
                </div>

                {/* 토큰 관리 단계 */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">3</div>
                    <h3 className="font-semibold">토큰 관리</h3>
                  </div>
                  <div className="pl-8 space-y-2">
                    <p className="text-sm text-muted-foreground">
                      API 토큰이 만료된 경우 &ldquo;API 토큰 갱신&rdquo; 버튼을 클릭하여 새로운 토큰을 발급받으세요.
                    </p>
                  </div>
                </div>

                {/* 자동매매 시작 */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center">4</div>
                    <h3 className="font-semibold">자동매매 시작</h3>
                  </div>
                  <div className="pl-8 space-y-2">
                    <p className="text-sm text-muted-foreground">
                      모든 설정이 완료되면 플랫폼의 자동매매 기능을 사용할 수 있습니다.
                    </p>
                  </div>
                </div>
              </div>

              {/* Security Notice */}
              <div className="mt-8 p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800">
                <div className="flex items-center space-x-2 mb-2">
                  <Lock className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800 dark:text-blue-200">보안 정보</span>
                </div>
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  모든 API 키는 AES-256-GCM 암호화를 통해 안전하게 저장되며, 
                  사용자 본인만이 접근할 수 있도록 보호됩니다.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default function ProtectedKiwoomAccountPage() {
  return (
    <ProtectedRoute>
      <KiwoomAccountManagement />
    </ProtectedRoute>
  );
}