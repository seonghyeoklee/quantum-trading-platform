'use client';

import { useState, useEffect } from 'react';
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import Header from "@/components/layout/Header";
import { getApiBaseUrl } from '@/lib/api-config';
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { CheckCircle2, AlertCircle, Lock, RefreshCw, Loader2, BookOpen, Zap, Shield, AlertTriangle, Info, HelpCircle, Settings, TrendingUp, ExternalLink } from "lucide-react";

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
  const [testing, setTesting] = useState(false);
  // 4개 키 필드로 확장
  const [realAppKey, setRealAppKey] = useState('');
  const [realAppSecret, setRealAppSecret] = useState('');
  const [mockAppKey, setMockAppKey] = useState('');
  const [mockAppSecret, setMockAppSecret] = useState('');
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
      
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/v1/kiwoom-accounts/me`, {
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

  // Register new account - 4개 키 지원
  const registerAccount = async () => {
    // 최소 1개 키 쌍은 완전히 입력되어야 함
    const hasRealKeys = realAppKey && realAppSecret;
    const hasMockKeys = mockAppKey && mockAppSecret;
    
    if (!hasRealKeys && !hasMockKeys) {
      setError('REAL 또는 SANDBOX 키 쌍 중 최소 하나는 완전히 입력해주세요');
      return;
    }

    setRegistering(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/v1/kiwoom-accounts/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          realAppKey: realAppKey || null,
          realAppSecret: realAppSecret || null,
          mockAppKey: mockAppKey || null,
          mockAppSecret: mockAppSecret || null,
          // 기존 호환성을 위한 필드 (REAL 키를 기본으로 사용)
          clientId: realAppKey || mockAppKey,
          clientSecret: realAppSecret || mockAppSecret
        })
      });

      if (response.ok) {
        await response.json();
        setSuccess('키움증권 계정이 성공적으로 등록되었습니다');
        setRealAppKey('');
        setRealAppSecret('');
        setMockAppKey('');
        setMockAppSecret('');
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

  // Update credentials - 4개 키 지원
  const updateCredentials = async () => {
    const hasRealKeys = realAppKey && realAppSecret;
    const hasMockKeys = mockAppKey && mockAppSecret;
    
    if (!hasRealKeys && !hasMockKeys) {
      setError('REAL 또는 SANDBOX 키 쌍 중 최소 하나는 완전히 입력해주세요');
      return;
    }

    setUpdating(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/v1/kiwoom-accounts/me/credentials`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          realAppKey: realAppKey || null,
          realAppSecret: realAppSecret || null,
          mockAppKey: mockAppKey || null,
          mockAppSecret: mockAppSecret || null,
          // 기존 호환성을 위한 필드
          clientId: realAppKey || mockAppKey,
          clientSecret: realAppSecret || mockAppSecret
        })
      });

      if (response.ok) {
        setSuccess('인증 정보가 성공적으로 업데이트되었습니다');
        setRealAppKey('');
        setRealAppSecret('');
        setMockAppKey('');
        setMockAppSecret('');
        await fetchAccountInfo();
      } else {
        const data = await response.json();
        setError(data.message || '인증 정보 업데이트에 실패했습니다');
      }
    } catch {
      setError('서버 연결 오류가 발생했습니다');
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
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/v1/kiwoom-accounts/me/token`, {
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

  // Test connection with provided credentials - 4개 키 지원
  const testConnection = async () => {
    const hasRealKeys = realAppKey && realAppSecret;
    const hasMockKeys = mockAppKey && mockAppSecret;
    
    if (!hasRealKeys && !hasMockKeys) {
      setError('REAL 또는 SANDBOX 키 쌍 중 최소 하나는 완전히 입력해주세요');
      return;
    }

    setTesting(true);
    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/v1/kiwoom-accounts/test-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          realAppKey: realAppKey || null,
          realAppSecret: realAppSecret || null,
          mockAppKey: mockAppKey || null,
          mockAppSecret: mockAppSecret || null,
          // 기존 호환성을 위한 필드
          clientId: realAppKey || mockAppKey,
          clientSecret: realAppSecret || mockAppSecret
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSuccess('✅ 키움증권 API 연결 테스트가 성공했습니다!');
        } else {
          setError(data.message || '연결 테스트에 실패했습니다');
        }
      } else {
        const data = await response.json();
        setError(data.message || '연결 테스트 중 오류가 발생했습니다');
      }
    } catch {
      setError('서버 연결 오류가 발생했습니다');
    } finally {
      setTesting(false);
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
              <div className="space-y-8">
                {/* REAL 키 섹션 */}
                <div className="p-6 rounded-xl border-2 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20">
                  <div className="flex items-center space-x-3 mb-4">
                    <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                    <h3 className="text-lg font-semibold text-red-800 dark:text-red-300">REAL API 키</h3>
                    <Badge variant="destructive" className="text-xs">PRODUCTION</Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="real-app-key" className="text-sm font-semibold text-red-700 dark:text-red-300">
                        REAL App Key
                      </Label>
                      <Input
                        id="real-app-key"
                        type="text"
                        placeholder="REAL App Key를 입력하세요"
                        value={realAppKey}
                        onChange={(e) => setRealAppKey(e.target.value)}
                        className="h-12 text-sm border-red-300 dark:border-red-700 focus:border-red-500"
                      />
                      <p className="text-xs text-red-600 dark:text-red-400">
                        실제 자금으로 거래하는 키 (32자 이상, 테스트 표시자 없음)
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="real-app-secret" className="text-sm font-semibold text-red-700 dark:text-red-300">
                        REAL App Secret
                      </Label>
                      <Input
                        id="real-app-secret"
                        type="password"
                        placeholder="REAL App Secret을 입력하세요"
                        value={realAppSecret}
                        onChange={(e) => setRealAppSecret(e.target.value)}
                        className="h-12 text-sm border-red-300 dark:border-red-700 focus:border-red-500"
                      />
                      <p className="text-xs text-red-600 dark:text-red-400">
                        실전투자용 시크릿 키 (Base64 형식, 고보안)
                      </p>
                    </div>
                  </div>
                </div>

                {/* SANDBOX 키 섹션 */}
                <div className="p-6 rounded-xl border-2 border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/20">
                  <div className="flex items-center space-x-3 mb-4">
                    <Shield className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <h3 className="text-lg font-semibold text-green-800 dark:text-green-300">SANDBOX API 키</h3>
                    <Badge variant="secondary" className="text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">SANDBOX</Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="mock-app-key" className="text-sm font-semibold text-green-700 dark:text-green-300">
                        SANDBOX App Key
                      </Label>
                      <Input
                        id="mock-app-key"
                        type="text"
                        placeholder="SANDBOX App Key를 입력하세요"
                        value={mockAppKey}
                        onChange={(e) => setMockAppKey(e.target.value)}
                        className="h-12 text-sm border-green-300 dark:border-green-700 focus:border-green-500"
                      />
                      <p className="text-xs text-green-600 dark:text-green-400">
                        가상 자금 연습용 키 (_TEST, _SB, _DEMO 등 포함)
                      </p>
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="mock-app-secret" className="text-sm font-semibold text-green-700 dark:text-green-300">
                        SANDBOX App Secret
                      </Label>
                      <Input
                        id="mock-app-secret"
                        type="password"
                        placeholder="SANDBOX App Secret을 입력하세요"
                        value={mockAppSecret}
                        onChange={(e) => setMockAppSecret(e.target.value)}
                        className="h-12 text-sm border-green-300 dark:border-green-700 focus:border-green-500"
                      />
                      <p className="text-xs text-green-600 dark:text-green-400">
                        SANDBOX 시크릿 키 (테스트 접미사 포함)
                      </p>
                    </div>
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
                
                {/* Connection Test Button */}
                <div className="flex justify-end">
                  <Button 
                    onClick={testConnection} 
                    disabled={testing || (!(realAppKey && realAppSecret) && !(mockAppKey && mockAppSecret))}
                    variant="outline"
                    size="sm"
                    className="h-9 text-xs"
                  >
                    {testing ? (
                      <>
                        <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                        테스트 중...
                      </>
                    ) : (
                      <>
                        <Zap className="w-3 h-3 mr-2" />
                        연결 테스트
                      </>
                    )}
                  </Button>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 pt-2">
                  {!accountInfo?.hasAccount ? (
                    <Button 
                      onClick={registerAccount} 
                      disabled={registering || (!(realAppKey && realAppSecret) && !(mockAppKey && mockAppSecret))}
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
                        disabled={updating || (!(realAppKey && realAppSecret) && !(mockAppKey && mockAppSecret))}
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

        {/* 통합 가이드 카드 */}
        <Card className="shadow-lg border-0 bg-gradient-to-br from-card to-card/80">
          <CardHeader className="pb-6">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <HelpCircle className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <CardTitle className="text-xl">키움증권 연동 완벽 가이드</CardTitle>
                <CardDescription className="text-base mt-1">
                  API 키 발급부터 자동매매 시작까지 모든 정보를 한 곳에 모았습니다.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <Accordion type="single" collapsible className="w-full space-y-2">
              
              {/* 1. 단계별 설정 가이드 */}
              <AccordionItem value="setup-guide" className="border border-blue-200/50 dark:border-blue-800/50 rounded-lg">
                <AccordionTrigger className="px-4 py-3 hover:no-underline">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                      <Settings className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-blue-800 dark:text-blue-200">📋 단계별 설정 가이드</h3>
                      <p className="text-sm text-blue-600/80 dark:text-blue-400/80">API 키 발급부터 완료까지 4단계 설정</p>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      
                      {/* 1단계: API 키 발급 */}
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">1</div>
                          <h4 className="font-semibold text-blue-800 dark:text-blue-200">API 키 발급</h4>
                        </div>
                        <div className="pl-8 space-y-2">
                          <p className="text-sm text-muted-foreground">
                            <a href="https://openapi.kiwoom.com/main/home" target="_blank" rel="noopener noreferrer" 
                               className="text-blue-600 hover:text-blue-800 hover:underline font-medium inline-flex items-center">
                              키움증권 Open API 센터
                              <ExternalLink className="w-3 h-3 ml-1" />
                            </a>에서 새로운 앱을 등록하고:
                          </p>
                          <ul className="text-sm text-muted-foreground space-y-1 pl-4">
                            <li>• <strong>실전투자용</strong>: App Key + App Secret 발급</li>
                            <li>• <strong>모의투자용</strong>: App Key + App Secret 발급 (선택)</li>
                          </ul>
                        </div>
                      </div>

                      {/* 2단계: 키 입력 및 테스트 */}
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">2</div>
                          <h4 className="font-semibold text-blue-800 dark:text-blue-200">키 입력 및 테스트</h4>
                        </div>
                        <div className="pl-8 space-y-2">
                          <p className="text-sm text-muted-foreground">위의 API 인증 정보 섹션에서:</p>
                          <ul className="text-sm text-muted-foreground space-y-1 pl-4">
                            <li>• 실전투자 또는 모의투자 키를 입력</li>
                            <li>• "연결 테스트" 버튼으로 유효성 확인</li>
                            <li>• 최소 1개 키 쌍 (App Key + Secret) 필요</li>
                          </ul>
                        </div>
                      </div>

                      {/* 3단계: 계정 등록 */}
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">3</div>
                          <h4 className="font-semibold text-blue-800 dark:text-blue-200">계정 등록</h4>
                        </div>
                        <div className="pl-8 space-y-2">
                          <p className="text-sm text-muted-foreground">
                            {accountInfo?.hasAccount 
                              ? '"인증 정보 업데이트" 버튼을 클릭하여 새 키를 저장하세요.' 
                              : '"키움증권 계정 등록하기" 버튼을 클릭하여 계정을 생성하세요.'}
                          </p>
                          <ul className="text-sm text-muted-foreground space-y-1 pl-4">
                            <li>• 모든 키는 AES-256-GCM으로 암호화 저장</li>
                            <li>• 거래 모드는 키 패턴에 따라 자동 결정</li>
                          </ul>
                        </div>
                      </div>

                      {/* 4단계: 자동매매 시작 */}
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs font-bold flex items-center justify-center">4</div>
                          <h4 className="font-semibold text-blue-800 dark:text-blue-200">자동매매 시작</h4>
                        </div>
                        <div className="pl-8 space-y-2">
                          <p className="text-sm text-muted-foreground">설정 완료 후 이용 가능한 기능들:</p>
                          <ul className="text-sm text-muted-foreground space-y-1 pl-4">
                            <li>• 실시간 주식 시세 조회</li>
                            <li>• 자동매매 전략 실행</li>
                            <li>• 포트폴리오 관리 및 모니터링</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* 2. 거래 모드 자동 탐지 */}
              <AccordionItem value="trading-mode" className="border border-orange-200/50 dark:border-orange-800/50 rounded-lg">
                <AccordionTrigger className="px-4 py-3 hover:no-underline">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                      <TrendingUp className="w-4 h-4 text-orange-600 dark:text-orange-400" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-orange-800 dark:text-orange-200">🔄 거래 모드 자동 탐지</h3>
                      <p className="text-sm text-orange-600/80 dark:text-orange-400/80">API 키 패턴으로 실전투자/모의투자 자동 결정</p>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="space-y-6">
                    
                    {/* 실전투자 vs 모의투자 비교 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* 실전투자 모드 */}
                      <div className="p-4 rounded-lg border-2 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/20">
                        <div className="flex items-center space-x-2 mb-3">
                          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                          <h4 className="font-semibold text-red-800 dark:text-red-300">실전투자 모드</h4>
                        </div>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-start space-x-2">
                            <div className="w-1 h-1 rounded-full bg-red-500 mt-2 flex-shrink-0"></div>
                            <span className="text-red-700 dark:text-red-400">실제 자금으로 거래, 실제 손익 발생</span>
                          </div>
                          <div className="flex items-start space-x-2">
                            <div className="w-1 h-1 rounded-full bg-red-500 mt-2 flex-shrink-0"></div>
                            <span className="text-red-700 dark:text-red-400">표준 키움증권 형식 (32자 이상)</span>
                          </div>
                          <div className="flex items-start space-x-2">
                            <div className="w-1 h-1 rounded-full bg-red-500 mt-2 flex-shrink-0"></div>
                            <span className="text-red-700 dark:text-red-400">테스트 표시자 없음</span>
                          </div>
                        </div>
                      </div>

                      {/* 모의투자 모드 */}
                      <div className="p-4 rounded-lg border-2 border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/20">
                        <div className="flex items-center space-x-2 mb-3">
                          <Shield className="w-5 h-5 text-green-600 dark:text-green-400" />
                          <h4 className="font-semibold text-green-800 dark:text-green-300">모의투자 모드</h4>
                        </div>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-start space-x-2">
                            <div className="w-1 h-1 rounded-full bg-green-500 mt-2 flex-shrink-0"></div>
                            <span className="text-green-700 dark:text-green-400">가상 자금으로 안전한 연습</span>
                          </div>
                          <div className="flex items-start space-x-2">
                            <div className="w-1 h-1 rounded-full bg-green-500 mt-2 flex-shrink-0"></div>
                            <span className="text-green-700 dark:text-green-400">_TEST, _SB, _DEMO 등 포함</span>
                          </div>
                          <div className="flex items-start space-x-2">
                            <div className="w-1 h-1 rounded-full bg-green-500 mt-2 flex-shrink-0"></div>
                            <span className="text-green-700 dark:text-green-400">테스트 접두사/접미사 있음</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 자동 탐지 로직 */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <h4 className="font-semibold text-blue-800 dark:text-blue-300 mb-3 flex items-center">
                        <Info className="w-4 h-4 mr-2" />
                        자동 모드 탐지 우선순위
                      </h4>
                      <ol className="text-sm text-blue-700 dark:text-blue-400 space-y-1 list-decimal list-inside">
                        <li>실전투자 키만 있으면 → <strong>실전투자 모드</strong></li>
                        <li>모의투자 키만 있으면 → <strong>모의투자 모드</strong></li>
                        <li>양쪽 모두 있으면 → <strong>실전투자 모드 우선</strong></li>
                        <li>키 패턴을 실시간 분석하여 UI가 자동 전환됩니다</li>
                      </ol>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* 3. 입력 가이드 & 팁 */}
              <AccordionItem value="input-tips" className="border border-green-200/50 dark:border-green-800/50 rounded-lg">
                <AccordionTrigger className="px-4 py-3 hover:no-underline">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                      <BookOpen className="w-4 h-4 text-green-600 dark:text-green-400" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-green-800 dark:text-green-200">💡 입력 가이드 & 팁</h3>
                      <p className="text-sm text-green-600/80 dark:text-green-400/80">키 입력 규칙, 연결 테스트, 문제해결</p>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="space-y-4">
                    
                    {/* 입력 규칙 */}
                    <div className="p-4 bg-green-50 dark:bg-green-950/20 rounded-lg">
                      <h4 className="font-semibold text-green-800 dark:text-green-300 mb-2">✅ 입력 규칙</h4>
                      <ul className="text-sm text-green-700 dark:text-green-400 space-y-1">
                        <li>• <strong>최소 1개 키 쌍</strong>은 완전히 입력해주세요 (App Key + App Secret)</li>
                        <li>• App Key는 10~100자, App Secret은 20~200자 사이여야 합니다</li>
                        <li>• 실전투자와 모의투자 키를 모두 입력해도 됩니다</li>
                        <li>• 입력 후 반드시 "연결 테스트"로 유효성을 확인하세요</li>
                      </ul>
                    </div>

                    {/* 문제해결 */}
                    <div className="p-4 bg-amber-50 dark:bg-amber-950/20 rounded-lg">
                      <h4 className="font-semibold text-amber-800 dark:text-amber-300 mb-2">🔧 문제해결</h4>
                      <ul className="text-sm text-amber-700 dark:text-amber-400 space-y-1">
                        <li>• <strong>연결 테스트 실패</strong>: 키 형식을 다시 확인하세요</li>
                        <li>• <strong>토큰 만료</strong>: "API 토큰 갱신" 버튼을 클릭하세요</li>
                        <li>• <strong>등록 실패</strong>: 이미 사용 중인 키인지 확인하세요</li>
                        <li>• <strong>모드 변경</strong>: 다른 종류의 키로 교체 후 업데이트하세요</li>
                      </ul>
                    </div>

                    {/* 추가 팁 */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      <h4 className="font-semibold text-blue-800 dark:text-blue-300 mb-2">💡 유용한 팁</h4>
                      <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                        <li>• 처음 사용하시는 경우 모의투자 키부터 시작하세요</li>
                        <li>• 실전투자 전환 전 충분한 연습을 권장합니다</li>
                        <li>• API 키는 정기적으로 갱신하는 것이 좋습니다</li>
                        <li>• 키는 본인만 사용하고 타인과 공유하지 마세요</li>
                      </ul>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* 4. 보안 & 개인정보 */}
              <AccordionItem value="security" className="border border-purple-200/50 dark:border-purple-800/50 rounded-lg">
                <AccordionTrigger className="px-4 py-3 hover:no-underline">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                      <Lock className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-purple-800 dark:text-purple-200">🔒 보안 & 개인정보</h3>
                      <p className="text-sm text-purple-600/80 dark:text-purple-400/80">암호화 방식, 데이터 보호 정책</p>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="space-y-4">
                    
                    {/* 암호화 정보 */}
                    <div className="p-4 bg-purple-50 dark:bg-purple-950/20 rounded-lg">
                      <h4 className="font-semibold text-purple-800 dark:text-purple-300 mb-2">🔐 암호화 보안</h4>
                      <ul className="text-sm text-purple-700 dark:text-purple-400 space-y-1">
                        <li>• <strong>AES-256-GCM 암호화</strong>: 모든 API 키는 군사급 암호화로 저장</li>
                        <li>• <strong>개별 솔트</strong>: 각 사용자별로 고유한 암호화 키 사용</li>
                        <li>• <strong>전송 보안</strong>: HTTPS로 모든 데이터 전송 암호화</li>
                        <li>• <strong>접근 제한</strong>: 사용자 본인만 복호화하여 사용 가능</li>
                      </ul>
                    </div>

                    {/* 데이터 보호 */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      <h4 className="font-semibold text-blue-800 dark:text-blue-300 mb-2">🛡️ 데이터 보호</h4>
                      <ul className="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                        <li>• API 키는 평문으로 저장되지 않습니다</li>
                        <li>• 로그에 민감한 정보가 기록되지 않습니다</li>
                        <li>• 정기적인 보안 감사를 실시합니다</li>
                        <li>• 계정 삭제 시 모든 데이터가 완전히 제거됩니다</li>
                      </ul>
                    </div>

                    {/* 사용자 권장사항 */}
                    <div className="p-4 bg-orange-50 dark:bg-orange-950/20 rounded-lg">
                      <h4 className="font-semibold text-orange-800 dark:text-orange-300 mb-2">⚠️ 사용자 권장사항</h4>
                      <ul className="text-sm text-orange-700 dark:text-orange-400 space-y-1">
                        <li>• API 키를 타인과 공유하지 마세요</li>
                        <li>• 공용 컴퓨터에서 로그인 후 반드시 로그아웃하세요</li>
                        <li>• 강력한 비밀번호를 사용하고 정기적으로 변경하세요</li>
                        <li>• 의심스러운 활동 발견 시 즉시 키를 변경하세요</li>
                      </ul>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

            </Accordion>
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