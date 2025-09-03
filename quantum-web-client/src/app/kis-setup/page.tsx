'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { MarketIndicator } from '@/components/market/MarketIndicator';
import { 
  Shield, 
  AlertCircle, 
  Info, 
  ExternalLink, 
  CheckCircle, 
  ArrowRight, 
  TestTube,
  Zap,
  Check,
  DollarSign,
  AlertTriangle,
  Building2
} from 'lucide-react';

export default function KISSetupPage() {
  const { setupKISAccount, skipKISSetup, checkKISAccountExists } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    sandbox: {
      appKey: '',
      appSecret: '',
      accountNumber: '',
      accountAlias: ''
    },
    live: {
      appKey: '',
      appSecret: '',
      accountNumber: '',
      accountAlias: ''
    },
    selectedEnvironments: {
      SANDBOX: false,
      LIVE: false
    }
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [environmentStatus, setEnvironmentStatus] = useState<{
    SANDBOX: boolean;
    LIVE: boolean;
  }>({ SANDBOX: false, LIVE: false });

  // 환경별 KIS 계정 상태 확인
  useEffect(() => {
    const checkEnvironmentStatus = async () => {
      try {
        const [sandboxExists, liveExists] = await Promise.all([
          checkKISAccountExists('SANDBOX'),
          checkKISAccountExists('LIVE')
        ]);
        
        setEnvironmentStatus({
          SANDBOX: sandboxExists,
          LIVE: liveExists
        });
      } catch (error) {
        console.error('Failed to check environment status:', error);
      }
    };

    checkEnvironmentStatus();
  }, [checkKISAccountExists]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const selectedEnvironments = Object.entries(formData.selectedEnvironments)
        .filter(([_, selected]) => selected)
        .map(([env, _]) => env as 'LIVE' | 'SANDBOX');

      if (selectedEnvironments.length === 0) {
        setError('최소 하나의 환경을 선택해주세요.');
        setIsLoading(false);
        return;
      }

      let successCount = 0;
      const failedEnvironments: string[] = [];

      // 선택된 각 환경에 대해 순차적으로 설정
      for (const environment of selectedEnvironments) {
        try {
          const envConfig = environment === 'SANDBOX' ? formData.sandbox : formData.live;
          
          await setupKISAccount(
            envConfig.appKey,
            envConfig.appSecret,
            envConfig.accountNumber,
            envConfig.accountAlias,
            environment
          );
          successCount++;
        } catch (envError) {
          console.error(`Failed to setup ${environment}:`, envError);
          failedEnvironments.push(environment);
        }
      }

      if (successCount > 0) {
        // 최소 하나의 환경이라도 성공했다면 성공으로 처리
        if (failedEnvironments.length > 0) {
          setError(`일부 환경 설정에 실패했습니다: ${failedEnvironments.join(', ')}`);
        }
        // 성공한 경우 페이지를 리디렉션하거나 성공 메시지 표시
      } else {
        // 모든 환경 설정이 실패한 경우
        setError('모든 환경 설정에 실패했습니다. 입력 정보를 확인해주세요.');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'KIS 계정 설정에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const validateStep = (step: number) => {
    const errors: Record<string, string> = {};
    
    if (step === 1) {
      // 환경 선택 검증
      if (!Object.values(formData.selectedEnvironments).some(env => env)) {
        errors.environments = '최소 하나의 환경을 선택해주세요';
      }
    }
    
    if (step === 2) {
      // 선택된 환경에 따른 키 검증
      if (formData.selectedEnvironments.SANDBOX) {
        if (!formData.sandbox.appKey) errors['sandbox.appKey'] = '모의투자 App Key를 입력해주세요';
        if (!formData.sandbox.appSecret) errors['sandbox.appSecret'] = '모의투자 App Secret을 입력해주세요';
      }
      if (formData.selectedEnvironments.LIVE) {
        if (!formData.live.appKey) errors['live.appKey'] = '실전투자 App Key를 입력해주세요';
        if (!formData.live.appSecret) errors['live.appSecret'] = '실전투자 App Secret을 입력해주세요';
      }
    }
    
    if (step === 3) {
      // 선택된 환경에 따른 계좌정보 검증
      if (formData.selectedEnvironments.SANDBOX) {
        if (!formData.sandbox.accountNumber) errors['sandbox.accountNumber'] = '모의투자 계좌번호를 입력해주세요';
        if (!formData.sandbox.accountAlias) errors['sandbox.accountAlias'] = '모의투자 계좌별명을 입력해주세요';
        if (formData.sandbox.accountNumber && !/^\d{8}-\d{2}$/.test(formData.sandbox.accountNumber)) {
          errors['sandbox.accountNumber'] = '올바른 계좌번호 형식이 아닙니다 (예: 12345678-01)';
        }
      }
      if (formData.selectedEnvironments.LIVE) {
        if (!formData.live.accountNumber) errors['live.accountNumber'] = '실전투자 계좌번호를 입력해주세요';
        if (!formData.live.accountAlias) errors['live.accountAlias'] = '실전투자 계좌별명을 입력해주세요';
        if (formData.live.accountNumber && !/^\d{8}-\d{2}$/.test(formData.live.accountNumber)) {
          errors['live.accountNumber'] = '올바른 계좌번호 형식이 아닙니다 (예: 12345678-01)';
        }
      }
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleSkip = () => {
    skipKISSetup();
  };

  const totalSteps = 4; // 환경선택 → API인증 → 계좌정보 → 확인
  const progress = (currentStep / totalSteps) * 100;

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-4">
      <div className="w-full max-w-4xl space-y-6">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-2">
            <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-primary-foreground" />
            </div>
            <h1 className="text-3xl font-bold">KIS 계정 설정</h1>
          </div>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            실시간 주식 데이터 조회와 자동매매를 위해 한국투자증권 API 계정을 연결해주세요
          </p>
          
          {/* Progress */}
          <div className="max-w-md mx-auto space-y-2">
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>진행 상황</span>
              <span>{currentStep}/{totalSteps} 단계</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </div>

        {/* Step Indicators */}
        <div className="flex justify-center space-x-4">
          {[
            { step: 1, title: '환경 선택', icon: TestTube },
            { step: 2, title: 'API 인증', icon: Shield },
            { step: 3, title: '계좌 정보', icon: Building2 },
            { step: 4, title: '설정 완료', icon: CheckCircle }
          ].map(({ step, title, icon: Icon }) => (
            <div
              key={step}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
                step === currentStep
                  ? 'bg-primary text-primary-foreground'
                  : step < currentStep
                  ? 'bg-primary/20 text-primary'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {step < currentStep ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Icon className="w-4 h-4" />
              )}
              <span className="text-sm font-medium">{title}</span>
            </div>
          ))}
        </div>

        {/* Step Content */}
        <Card className="border-2">
          <CardContent className="p-6">
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Step 1: 환경 선택 */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <TestTube className="w-12 h-12 text-purple-600 mx-auto" />
                  <h2 className="text-xl font-semibold">거래 환경 선택</h2>
                  <p className="text-muted-foreground">
                    설정할 환경을 먼저 선택해주세요. 각 환경마다 별도의 API 키가 필요합니다.
                  </p>
                </div>

                <Alert className="border-amber-200 bg-amber-50 dark:bg-amber-950/20">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  <AlertDescription className="text-amber-800 dark:text-amber-200">
                    <strong>중요:</strong> 모의투자와 실전투자는 <strong>다른 API 키</strong>를 사용합니다. 
                    각 환경별로 별도의 App Key와 App Secret이 필요합니다.
                  </AlertDescription>
                </Alert>

                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div 
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.selectedEnvironments.SANDBOX 
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                          : 'border-border hover:border-primary'
                      } ${environmentStatus.SANDBOX ? 'opacity-75' : ''}`}
                      onClick={() => !environmentStatus.SANDBOX && setFormData({
                        ...formData, 
                        selectedEnvironments: {
                          ...formData.selectedEnvironments,
                          SANDBOX: !formData.selectedEnvironments.SANDBOX
                        }
                      })}
                    >
                      <div className="flex items-center space-x-2">
                        <div className={`w-5 h-5 border-2 rounded ${
                          formData.selectedEnvironments.SANDBOX 
                            ? 'border-blue-500 bg-blue-500' 
                            : 'border-gray-300'
                        }`}>
                          {formData.selectedEnvironments.SANDBOX && (
                            <Check className="w-3 h-3 text-white mx-auto mt-0.5" />
                          )}
                        </div>
                        <h3 className="font-semibold flex items-center">
                          모의투자 (SANDBOX)
                          <Badge className="ml-2 bg-blue-100 text-blue-700">권장</Badge>
                          {environmentStatus.SANDBOX && (
                            <Badge className="ml-2 bg-green-100 text-green-700">설정됨</Badge>
                          )}
                        </h3>
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        {environmentStatus.SANDBOX 
                          ? '이미 설정된 환경입니다' 
                          : '가상 투자로 안전하게 테스트할 수 있습니다'
                        }
                      </p>
                      <div className="mt-3 space-y-1">
                        <div className="flex items-center space-x-2 text-sm">
                          <Shield className="w-4 h-4 text-green-500" />
                          <span>실제 돈 사용 안함</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <TestTube className="w-4 h-4 text-blue-500" />
                          <span>전략 테스트 가능</span>
                        </div>
                      </div>
                    </div>

                    <div 
                      className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                        formData.selectedEnvironments.LIVE 
                          ? 'border-red-500 bg-red-50 dark:bg-red-900/20' 
                          : 'border-border hover:border-primary'
                      } ${environmentStatus.LIVE ? 'opacity-75' : ''}`}
                      onClick={() => !environmentStatus.LIVE && setFormData({
                        ...formData, 
                        selectedEnvironments: {
                          ...formData.selectedEnvironments,
                          LIVE: !formData.selectedEnvironments.LIVE
                        }
                      })}
                    >
                      <div className="flex items-center space-x-2">
                        <div className={`w-5 h-5 border-2 rounded ${
                          formData.selectedEnvironments.LIVE 
                            ? 'border-red-500 bg-red-500' 
                            : 'border-gray-300'
                        }`}>
                          {formData.selectedEnvironments.LIVE && (
                            <Check className="w-3 h-3 text-white mx-auto mt-0.5" />
                          )}
                        </div>
                        <h3 className="font-semibold flex items-center">
                          실전투자 (LIVE)
                          {environmentStatus.LIVE && (
                            <Badge className="ml-2 bg-green-100 text-green-700">설정됨</Badge>
                          )}
                        </h3>
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        {environmentStatus.LIVE 
                          ? '이미 설정된 환경입니다' 
                          : '실제 계좌로 거래를 진행합니다'
                        }
                      </p>
                      <div className="mt-3 space-y-1">
                        <div className="flex items-center space-x-2 text-sm">
                          <DollarSign className="w-4 h-4 text-green-500" />
                          <span>실제 돈 사용</span>
                        </div>
                        <div className="flex items-center space-x-2 text-sm">
                          <AlertTriangle className="w-4 h-4 text-orange-500" />
                          <span>신중한 사용 필요</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {validationErrors.environments && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{validationErrors.environments}</AlertDescription>
                    </Alert>
                  )}
                </div>

                <Alert className="border-primary/20 bg-primary/10">
                  <Info className="h-4 w-4 text-primary" />
                  <AlertDescription className="text-foreground">
                    아직 KIS API 계정이 없으시나요? {' '}
                    <a 
                      href="https://apiportal.koreainvestment.com" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-primary hover:underline font-medium"
                    >
                      여기서 계정을 생성하세요 <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </AlertDescription>
                </Alert>
              </div>
            )}

            {/* Step 2: API 인증 */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <Shield className="w-12 h-12 text-blue-600 mx-auto" />
                  <h2 className="text-xl font-semibold">API 인증 정보</h2>
                  <p className="text-muted-foreground">
                    선택한 환경별로 API 키를 입력해주세요
                  </p>
                </div>

                {/* 모의투자 API 키 입력 */}
                {formData.selectedEnvironments.SANDBOX && (
                  <div className="space-y-4 p-4 border border-blue-200 rounded-lg bg-blue-50/30 dark:bg-blue-950/20">
                    <div className="flex items-center space-x-2">
                      <TestTube className="w-5 h-5 text-blue-600" />
                      <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200">모의투자 API 인증</h3>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="sandboxAppKey" className="text-sm font-medium">모의투자 App Key *</Label>
                        <Input
                          id="sandboxAppKey"
                          type="text"
                          placeholder="SANDBOX_APP_KEY_HERE"
                          value={formData.sandbox.appKey}
                          onChange={(e) => setFormData({
                            ...formData,
                            sandbox: { ...formData.sandbox, appKey: e.target.value }
                          })}
                          className={validationErrors['sandbox.appKey'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['sandbox.appKey'] && (
                          <p className="text-sm text-red-600">{validationErrors['sandbox.appKey']}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="sandboxAppSecret" className="text-sm font-medium">모의투자 App Secret *</Label>
                        <Input
                          id="sandboxAppSecret"
                          type="password"
                          placeholder="SANDBOX_SECRET_HERE"
                          value={formData.sandbox.appSecret}
                          onChange={(e) => setFormData({
                            ...formData,
                            sandbox: { ...formData.sandbox, appSecret: e.target.value }
                          })}
                          className={validationErrors['sandbox.appSecret'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['sandbox.appSecret'] && (
                          <p className="text-sm text-red-600">{validationErrors['sandbox.appSecret']}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* 실전투자 API 키 입력 */}
                {formData.selectedEnvironments.LIVE && (
                  <div className="space-y-4 p-4 border border-red-200 rounded-lg bg-red-50/30 dark:bg-red-950/20">
                    <div className="flex items-center space-x-2">
                      <Zap className="w-5 h-5 text-red-600" />
                      <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">실전투자 API 인증</h3>
                    </div>
                    
                    <Alert variant="destructive" className="mb-4">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>주의:</strong> 실전투자 키는 실제 돈과 연결됩니다. 절대 다른 사람과 공유하지 마세요.
                      </AlertDescription>
                    </Alert>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="liveAppKey" className="text-sm font-medium">실전투자 App Key *</Label>
                        <Input
                          id="liveAppKey"
                          type="text"
                          placeholder="LIVE_APP_KEY_HERE"
                          value={formData.live.appKey}
                          onChange={(e) => setFormData({
                            ...formData,
                            live: { ...formData.live, appKey: e.target.value }
                          })}
                          className={validationErrors['live.appKey'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['live.appKey'] && (
                          <p className="text-sm text-red-600">{validationErrors['live.appKey']}</p>
                        )}
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="liveAppSecret" className="text-sm font-medium">실전투자 App Secret *</Label>
                        <Input
                          id="liveAppSecret"
                          type="password"
                          placeholder="LIVE_SECRET_HERE"
                          value={formData.live.appSecret}
                          onChange={(e) => setFormData({
                            ...formData,
                            live: { ...formData.live, appSecret: e.target.value }
                          })}
                          className={validationErrors['live.appSecret'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['live.appSecret'] && (
                          <p className="text-sm text-red-600">{validationErrors['live.appSecret']}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    모든 API 키는 암호화되어 안전하게 저장되며, 절대 제3자와 공유되지 않습니다.
                  </AlertDescription>
                </Alert>
              </div>
            )}

            {/* Step 3: 계좌 정보 */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <Building2 className="w-12 h-12 text-green-600 mx-auto" />
                  <h2 className="text-xl font-semibold">계좌 정보</h2>
                  <p className="text-muted-foreground">
                    선택한 환경별로 계좌 정보를 입력해주세요
                  </p>
                </div>

                {/* 모의투자 계좌 정보 입력 */}
                {formData.selectedEnvironments.SANDBOX && (
                  <div className="space-y-4 p-4 border border-blue-200 rounded-lg bg-blue-50/30 dark:bg-blue-950/20">
                    <div className="flex items-center space-x-2">
                      <TestTube className="w-5 h-5 text-blue-600" />
                      <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200">모의투자 계좌 정보</h3>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="sandboxAccountNumber" className="text-sm font-medium">모의투자 계좌번호 *</Label>
                        <Input
                          id="sandboxAccountNumber"
                          type="text"
                          placeholder="12345678-01"
                          value={formData.sandbox.accountNumber}
                          onChange={(e) => setFormData({
                            ...formData,
                            sandbox: { ...formData.sandbox, accountNumber: e.target.value }
                          })}
                          className={validationErrors['sandbox.accountNumber'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['sandbox.accountNumber'] && (
                          <p className="text-sm text-red-600">{validationErrors['sandbox.accountNumber']}</p>
                        )}
                        <p className="text-xs text-muted-foreground">형식: 계좌번호-01 (8자리-2자리)</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="sandboxAccountAlias" className="text-sm font-medium">모의투자 계좌별명 *</Label>
                        <Input
                          id="sandboxAccountAlias"
                          type="text"
                          placeholder="모의투자 메인 계좌"
                          value={formData.sandbox.accountAlias}
                          onChange={(e) => setFormData({
                            ...formData,
                            sandbox: { ...formData.sandbox, accountAlias: e.target.value }
                          })}
                          className={validationErrors['sandbox.accountAlias'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['sandbox.accountAlias'] && (
                          <p className="text-sm text-red-600">{validationErrors['sandbox.accountAlias']}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* 실전투자 계좌 정보 입력 */}
                {formData.selectedEnvironments.LIVE && (
                  <div className="space-y-4 p-4 border border-red-200 rounded-lg bg-red-50/30 dark:bg-red-950/20">
                    <div className="flex items-center space-x-2">
                      <Zap className="w-5 h-5 text-red-600" />
                      <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">실전투자 계좌 정보</h3>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="liveAccountNumber" className="text-sm font-medium">실전투자 계좌번호 *</Label>
                        <Input
                          id="liveAccountNumber"
                          type="text"
                          placeholder="12345678-01"
                          value={formData.live.accountNumber}
                          onChange={(e) => setFormData({
                            ...formData,
                            live: { ...formData.live, accountNumber: e.target.value }
                          })}
                          className={validationErrors['live.accountNumber'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['live.accountNumber'] && (
                          <p className="text-sm text-red-600">{validationErrors['live.accountNumber']}</p>
                        )}
                        <p className="text-xs text-muted-foreground">형식: 계좌번호-01 (8자리-2자리)</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="liveAccountAlias" className="text-sm font-medium">실전투자 계좌별명 *</Label>
                        <Input
                          id="liveAccountAlias"
                          type="text"
                          placeholder="실전투자 메인 계좌"
                          value={formData.live.accountAlias}
                          onChange={(e) => setFormData({
                            ...formData,
                            live: { ...formData.live, accountAlias: e.target.value }
                          })}
                          className={validationErrors['live.accountAlias'] ? 'border-red-500' : ''}
                        />
                        {validationErrors['live.accountAlias'] && (
                          <p className="text-sm text-red-600">{validationErrors['live.accountAlias']}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Market Preview */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <MarketIndicator variant="detailed" showStatus={true} showTime={true} />
                </div>

              </div>
            )}

            {/* Step 4: 설정 완료 */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <div className="text-center space-y-2">
                  <CheckCircle className="w-12 h-12 text-green-600 mx-auto" />
                  <h2 className="text-xl font-semibold">설정 완료</h2>
                  <p className="text-muted-foreground">
                    선택한 환경의 설정 내용을 확인해주세요
                  </p>
                </div>

                {/* 설정 요약 */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">설정 요약</h3>
                  
                  {/* 모의투자 설정 요약 */}
                  {formData.selectedEnvironments.SANDBOX && (
                    <div className="p-4 border border-blue-200 rounded-lg bg-blue-50/30 dark:bg-blue-950/20">
                      <div className="flex items-center space-x-2 mb-3">
                        <TestTube className="w-5 h-5 text-blue-600" />
                        <h4 className="text-md font-semibold text-blue-800 dark:text-blue-200">모의투자 환경</h4>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <strong>App Key:</strong> {formData.sandbox.appKey.slice(0, 8)}...
                        </div>
                        <div>
                          <strong>계좌번호:</strong> {formData.sandbox.accountNumber}
                        </div>
                        <div>
                          <strong>App Secret:</strong> ****
                        </div>
                        <div>
                          <strong>계좌별명:</strong> {formData.sandbox.accountAlias}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* 실전투자 설정 요약 */}
                  {formData.selectedEnvironments.LIVE && (
                    <div className="p-4 border border-red-200 rounded-lg bg-red-50/30 dark:bg-red-950/20">
                      <div className="flex items-center space-x-2 mb-3">
                        <Zap className="w-5 h-5 text-red-600" />
                        <h4 className="text-md font-semibold text-red-800 dark:text-red-200">실전투자 환경</h4>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <strong>App Key:</strong> {formData.live.appKey.slice(0, 8)}...
                        </div>
                        <div>
                          <strong>계좌번호:</strong> {formData.live.accountNumber}
                        </div>
                        <div>
                          <strong>App Secret:</strong> ****
                        </div>
                        <div>
                          <strong>계좌별명:</strong> {formData.live.accountAlias}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Final Security Notice */}
                <Alert className="border-primary/20 bg-primary/10">
                  <Shield className="h-4 w-4 text-primary" />
                  <AlertDescription className="text-foreground">
                    <strong>설정 완료 후:</strong> 언제든지 환경을 전환하거나 계좌 정보를 수정할 수 있습니다.
                    설정된 정보는 최고 수준의 보안으로 보호됩니다.
                  </AlertDescription>
                </Alert>
              </div>
            )}
          </CardContent>

          <CardFooter className="bg-muted/30 flex justify-between">
            <div className="flex space-x-2">
              {currentStep > 1 && (
                <Button variant="outline" onClick={prevStep}>
                  이전
                </Button>
              )}
              <Button variant="ghost" onClick={handleSkip}>
                나중에 설정
              </Button>
            </div>

            <div className="flex space-x-2">
              {currentStep < totalSteps ? (
                <Button onClick={nextStep}>
                  다음
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <form onSubmit={handleSubmit} className="inline">
                  <Button 
                    type="submit" 
                    disabled={isLoading || Object.values(formData.selectedEnvironments).every(env => !env)}
                    className="bg-green-600 hover:bg-green-700 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                        설정 중...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        선택한 환경 설정
                      </>
                    )}
                  </Button>
                </form>
              )}
            </div>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">설정을 건너뛰면?</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium text-green-600 mb-2">✅ 사용 가능한 기능</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• 기본 차트 보기</li>
                  <li>• 종목 검색</li>
                  <li>• 과거 데이터 분석</li>
                  <li>• 전략 백테스팅</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-orange-600 mb-2">⚠️ 제한되는 기능</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>• 실시간 시세 조회</li>
                  <li>• 자동매매 실행</li>
                  <li>• 주문 관리</li>
                  <li>• 계좌 정보 조회</li>
                </ul>
              </div>
            </div>
            <Separator />
            <p className="text-sm text-muted-foreground">
              언제든지 설정 메뉴에서 KIS 계정을 연결할 수 있습니다.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}