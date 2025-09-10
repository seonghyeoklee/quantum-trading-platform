'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Shield, 
  AlertCircle, 
  Info,
  ArrowRight,
  Check,
  Loader2
} from 'lucide-react';

export default function KISSetupPage() {
  const { setupKISAccount, skipKISSetup } = useAuth();
  const [selectedEnvironment, setSelectedEnvironment] = useState<'SANDBOX' | 'LIVE'>('SANDBOX');
  const [formData, setFormData] = useState({
    appKey: '',
    appSecret: '',
    accountNumber: '',
    accountAlias: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [retryCount, setRetryCount] = useState(0);
  const [showRetry, setShowRetry] = useState(false);

  const loadingSteps = [
    { message: 'API 키 검증 중...', progress: 25 },
    { message: '계좌 정보 확인 중...', progress: 50 },
    { message: '설정 저장 중...', progress: 75 },
    { message: '완료 처리 중...', progress: 100 }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await executeKISSetup();
  };

  const executeKISSetup = async () => {
    setIsLoading(true);
    setError(null);
    setShowRetry(false);
    setLoadingStep(0);

    try {
      // Step 1: API 키 검증
      setLoadingStep(0);
      setLoadingMessage(loadingSteps[0].message);
      await new Promise(resolve => setTimeout(resolve, 800)); // 시각적 피드백을 위한 딜레이

      // Step 2: 계좌 정보 확인
      setLoadingStep(1);
      setLoadingMessage(loadingSteps[1].message);
      await new Promise(resolve => setTimeout(resolve, 600));

      // Step 3: 설정 저장
      setLoadingStep(2);
      setLoadingMessage(loadingSteps[2].message);
      await new Promise(resolve => setTimeout(resolve, 400));

      // 실제 API 호출
      await setupKISAccount(
        formData.appKey,
        formData.appSecret,
        formData.accountNumber,
        formData.accountAlias,
        selectedEnvironment
      );

      // Step 4: 완료 처리
      setLoadingStep(3);
      setLoadingMessage(loadingSteps[3].message);
      await new Promise(resolve => setTimeout(resolve, 500));

      // 성공 시 재시도 카운터 리셋
      setRetryCount(0);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'KIS 계정 설정에 실패했습니다.';
      setError(errorMessage);
      setShowRetry(true);
    } finally {
      setIsLoading(false);
      setLoadingStep(0);
      setLoadingMessage('');
    }
  };

  const handleRetry = async () => {
    const newRetryCount = retryCount + 1;
    setRetryCount(newRetryCount);
    await executeKISSetup();
  };

  const isFormValid = formData.appKey && formData.appSecret && formData.accountNumber && formData.accountAlias;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-primary rounded-xl flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold mb-2">KIS 계정 연결</h1>
          <p className="text-muted-foreground">
            한국투자증권 API 키를 입력해서 실시간 거래를 시작하세요
          </p>
        </div>

        <Card className="relative">
          {/* Loading Overlay */}
          {isLoading && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center rounded-lg">
              <div className="bg-card border rounded-lg p-8 shadow-lg max-w-sm w-full mx-4">
                <div className="text-center space-y-6">
                  {/* Animated Spinner */}
                  <div className="relative">
                    <div className="w-16 h-16 border-4 border-muted rounded-full"></div>
                    <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin absolute top-0 left-0"></div>
                    <Shield className="w-6 h-6 text-primary absolute top-5 left-5" />
                  </div>

                  {/* Progress Bar */}
                  <div className="space-y-3">
                    <div className="text-sm font-medium text-foreground">
                      {loadingMessage}
                    </div>
                    <Progress 
                      value={loadingSteps[loadingStep]?.progress || 0} 
                      className="h-2"
                    />
                    <div className="text-xs text-muted-foreground">
                      {loadingSteps[loadingStep]?.progress || 0}% 완료
                    </div>
                  </div>

                  {/* Loading Steps */}
                  <div className="space-y-2">
                    {loadingSteps.map((step, index) => (
                      <div
                        key={index}
                        className={`flex items-center gap-2 text-xs ${
                          index < loadingStep
                            ? 'text-green-600'
                            : index === loadingStep
                            ? 'text-primary'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {index < loadingStep ? (
                          <Check className="w-3 h-3" />
                        ) : index === loadingStep ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <div className="w-3 h-3 border border-muted-foreground rounded-full" />
                        )}
                        <span>{step.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>API 정보 입력</span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedEnvironment('SANDBOX')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    selectedEnvironment === 'SANDBOX'
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  }`}
                >
                  모의투자
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedEnvironment('LIVE')}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    selectedEnvironment === 'LIVE'
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'
                  }`}
                >
                  실전투자
                </button>
              </div>
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-6">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-3">
                    <div>{error}</div>
                    {showRetry && (
                      <div className="flex items-center gap-3">
                        <Button 
                          onClick={handleRetry} 
                          size="sm" 
                          variant="outline"
                          disabled={isLoading}
                          className="border-red-300 text-red-800 hover:bg-red-50"
                        >
                          다시 시도 {retryCount > 0 && `(${retryCount + 1}번째)`}
                        </Button>
                        <span className="text-xs text-muted-foreground">
                          네트워크 문제일 수 있습니다
                        </span>
                      </div>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {selectedEnvironment === 'SANDBOX' && (
              <div className="flex items-start gap-3 p-4 border border-blue-200 rounded-lg bg-blue-50/50 dark:bg-blue-950/20">
                <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  <strong>모의투자:</strong> 가상 투자로 안전하게 테스트할 수 있습니다. 실제 돈이 사용되지 않아요.
                </p>
              </div>
            )}

            {selectedEnvironment === 'LIVE' && (
              <div className="flex items-start gap-3 p-4 border border-red-200 rounded-lg bg-red-50/50 dark:bg-red-950/20">
                <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-800 dark:text-red-200">
                  <strong>실전투자:</strong> 실제 돈과 연결됩니다. 신중하게 입력해주세요.
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="appKey">
                  App Key *
                  <Badge variant="secondary" className="ml-2 text-xs">
                    {selectedEnvironment === 'SANDBOX' ? '모의투자' : '실전투자'}
                  </Badge>
                </Label>
                <Input
                  id="appKey"
                  type="text"
                  placeholder="KIS API App Key를 입력하세요"
                  value={formData.appKey}
                  onChange={(e) => setFormData(prev => ({ ...prev, appKey: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="appSecret">App Secret *</Label>
                <Input
                  id="appSecret"
                  type="password"
                  placeholder="KIS API App Secret을 입력하세요"
                  value={formData.appSecret}
                  onChange={(e) => setFormData(prev => ({ ...prev, appSecret: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="accountNumber">계좌번호 *</Label>
                <Input
                  id="accountNumber"
                  type="text"
                  placeholder="12345678-01"
                  value={formData.accountNumber}
                  onChange={(e) => setFormData(prev => ({ ...prev, accountNumber: e.target.value }))}
                  required
                />
                <p className="text-xs text-muted-foreground">형식: 계좌번호-01 (8자리-2자리)</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="accountAlias">계좌별명 *</Label>
                <Input
                  id="accountAlias"
                  type="text"
                  placeholder="메인 계좌"
                  value={formData.accountAlias}
                  onChange={(e) => setFormData(prev => ({ ...prev, accountAlias: e.target.value }))}
                  required
                />
              </div>

              <div className="flex items-start gap-3 p-4 border rounded-lg bg-muted/50">
                <Shield className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-muted-foreground">
                  모든 정보는 암호화되어 안전하게 저장됩니다. 제3자와 공유되지 않아요.
                </p>
              </div>

              <div className="flex justify-between pt-4">
                <Button type="button" variant="ghost" onClick={skipKISSetup}>
                  나중에 설정
                </Button>

                <Button 
                  type="submit" 
                  disabled={!isFormValid || isLoading}
                  className={selectedEnvironment === 'SANDBOX' ? 'bg-blue-600 hover:bg-blue-700' : 'bg-red-600 hover:bg-red-700'}
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                      설정 중...
                    </>
                  ) : (
                    <>
                      <Check className="w-4 h-4 mr-2" />
                      {selectedEnvironment === 'SANDBOX' ? '모의투자' : '실전투자'} 설정
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="mt-6">
          <CardContent className="pt-6">
            <div className="text-center">
              <p className="text-sm text-muted-foreground mb-4">
                아직 KIS API 계정이 없으신가요?
              </p>
              <Button variant="outline" asChild>
                <a 
                  href="https://apiportal.koreainvestment.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center"
                >
                  KIS API 계정 만들기
                  <ArrowRight className="w-4 h-4 ml-2" />
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}