'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  Shield, 
  Smartphone, 
  Key, 
  AlertTriangle,
  CheckCircle,
  Copy,
  RefreshCw,
  QrCode,
  Download,
  ArrowLeft,
  ArrowRight,
  Info,
  Zap,
  Timer,
  Eye,
  EyeOff
} from 'lucide-react';
import QRCode from 'react-qr-code';
import apiClient from '@/lib/api-client';

interface TwoFactorSetupProps {
  isEnabled?: boolean;
  onStatusChange?: (enabled: boolean) => void;
}

interface TotpSetupResponse {
  secretKey: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

export default function TwoFactorSetup({ isEnabled = false, onStatusChange }: TwoFactorSetupProps) {
  const [setupData, setSetupData] = useState<TotpSetupResponse | null>(null);
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [step, setStep] = useState<'overview' | 'setup' | 'verify' | 'complete'>('overview');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [showSecretKey, setShowSecretKey] = useState(false);

  // 2FA 설정 초기화
  const initSetup = async () => {
    try {
      setLoading(true);
      setError('');

      const response = await apiClient.post('/auth/2fa/setup');
      setSetupData(response.data);
      setStep('setup');
    } catch (err: any) {
      console.error('Failed to initialize 2FA setup:', err);
      setError('2FA 설정을 초기화하는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 인증 코드 검증 및 2FA 활성화
  const verifyAndEnable = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('6자리 인증 코드를 입력해주세요.');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await apiClient.post('/auth/2fa/verify', {
        secretKey: setupData?.secretKey,
        verificationCode: verificationCode.trim()
      });

      if (response.success) {
        setBackupCodes(response.data.backupCodes || []);
        setStep('complete');
        setSuccess('2FA가 성공적으로 활성화되었습니다!');
        onStatusChange?.(true);
      } else {
        setError('인증 코드가 올바르지 않습니다. 다시 시도해주세요.');
      }
    } catch (err: any) {
      console.error('Failed to verify 2FA code:', err);
      setError('인증 코드 검증에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 2FA 비활성화
  const disableTwoFactor = async () => {
    if (!confirm('정말로 2단계 인증을 비활성화하시겠습니까?\n보안이 약화될 수 있습니다.')) {
      return;
    }

    try {
      setLoading(true);
      setError('');

      await apiClient.post('/auth/2fa/disable');
      setSuccess('2단계 인증이 비활성화되었습니다.');
      onStatusChange?.(false);
      setStep('overview');
    } catch (err: any) {
      console.error('Failed to disable 2FA:', err);
      setError('2FA 비활성화에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 백업 코드 복사
  const copyBackupCodes = () => {
    const codesText = backupCodes.join('\n');
    navigator.clipboard.writeText(codesText);
    setSuccess('백업 코드가 클립보드에 복사되었습니다.');
  };

  // 백업 코드 다운로드
  const downloadBackupCodes = () => {
    const codesText = backupCodes.join('\n');
    const blob = new Blob([codesText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'quantum-trading-backup-codes.txt';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // QR URL 복사
  const copyQrUrl = () => {
    if (setupData?.qrCodeUrl) {
      navigator.clipboard.writeText(setupData.qrCodeUrl);
      setSuccess('QR 코드 URL이 복사되었습니다.');
    }
  };

  // 인증 코드 입력 시 자동 진행
  useEffect(() => {
    if (verificationCode.length === 6 && step === 'verify') {
      const timer = setTimeout(() => {
        verifyAndEnable();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [verificationCode]);

  return (
    <Card className="max-w-3xl mx-auto shadow-xl border-0 bg-gradient-to-br from-background via-background to-muted/30">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <Shield className="w-6 h-6 text-primary" />
          <div>
            <CardTitle>2단계 인증 (2FA)</CardTitle>
            <CardDescription>
              계정 보안을 강화하기 위해 Google Authenticator 또는 유사한 앱을 사용하세요
            </CardDescription>
          </div>
          {isEnabled && (
            <Badge variant="default" className="bg-bull text-white">
              <CheckCircle className="w-3 h-3 mr-1" />
              활성화됨
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* 에러/성공 메시지 */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="border-bull/50 bg-bull/10">
            <CheckCircle className="w-4 h-4 text-bull" />
            <AlertDescription className="text-bull">{success}</AlertDescription>
          </Alert>
        )}

        {/* 단계별 UI */}
        {step === 'overview' && (
          <div className="space-y-6">
            <div className="text-center space-y-4">
              <div className="w-20 h-20 bg-gradient-to-br from-primary/20 to-primary/10 rounded-full flex items-center justify-center mx-auto">
                <div className="relative">
                  <Smartphone className="w-10 h-10 text-primary" />
                  {isEnabled && (
                    <CheckCircle className="absolute -top-1 -right-1 w-5 h-5 text-bull bg-background rounded-full" />
                  )}
                </div>
              </div>
              
              <div>
                <h3 className="text-xl font-bold mb-3">
                  {isEnabled ? '2단계 인증 활성화됨' : '보안 강화하기'}
                </h3>
                <p className="text-muted-foreground text-base leading-relaxed max-w-md mx-auto">
                  {isEnabled 
                    ? '🛡️ 계정이 2단계 인증으로 안전하게 보호되고 있습니다'
                    : '📱 모바일 앱의 6자리 코드로 계정을 더욱 안전하게 보호하세요'
                  }
                </p>
              </div>

              {/* 보안 레벨 표시 */}
              <div className="bg-gradient-to-r from-primary/10 to-bull/10 p-4 rounded-lg border">
                <div className="flex items-center justify-center space-x-2">
                  <Shield className="w-5 h-5 text-primary" />
                  <span className="font-medium">
                    보안 레벨: <span className={isEnabled ? 'text-bull' : 'text-amber-600'}>
                      {isEnabled ? '높음' : '보통'}
                    </span>
                  </span>
                  <div className="flex space-x-1">
                    <div className={`w-2 h-2 rounded-full ${isEnabled ? 'bg-bull' : 'bg-primary'}`}></div>
                    <div className={`w-2 h-2 rounded-full ${isEnabled ? 'bg-bull' : 'bg-muted'}`}></div>
                    <div className={`w-2 h-2 rounded-full ${isEnabled ? 'bg-bull' : 'bg-muted'}`}></div>
                  </div>
                </div>
              </div>

              <div className="flex justify-center space-x-3">
                {isEnabled ? (
                  <>
                    <Button variant="outline" onClick={() => setStep('setup')} className="min-w-[120px]">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      재설정
                    </Button>
                    <Button 
                      variant="destructive" 
                      onClick={disableTwoFactor}
                      disabled={loading}
                      className="min-w-[120px]"
                    >
                      {loading && <RefreshCw className="w-4 h-4 mr-2 animate-spin" />}
                      {!loading && <Shield className="w-4 h-4 mr-2" />}
                      비활성화
                    </Button>
                  </>
                ) : (
                  <Button 
                    onClick={initSetup} 
                    disabled={loading}
                    className="min-w-[200px] h-12 text-base font-semibold"
                    size="lg"
                  >
                    {loading ? (
                      <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                    ) : (
                      <Zap className="w-5 h-5 mr-2" />
                    )}
                    2FA 설정 시작하기
                  </Button>
                )}
              </div>
            </div>

            {/* 지원 앱 안내 */}
            <Separator />
            <div>
              <h4 className="font-semibold mb-4 text-center">📱 지원되는 인증 앱</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                  <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-red-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">G</span>
                  </div>
                  <span className="font-medium">Google Authenticator</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                  <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">A</span>
                  </div>
                  <span className="font-medium">Authy</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-sm">M</span>
                  </div>
                  <span className="font-medium">Microsoft Authenticator</span>
                </div>
                <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors">
                  <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                    <Key className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-medium">기타 TOTP 앱</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 'setup' && setupData && (
          <div className="space-y-6">
            {/* 진행 상태 표시 */}
            <div className="flex items-center justify-center space-x-2 mb-6">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-bold">1</div>
                <span className="text-primary font-medium">QR 스캔</span>
              </div>
              <div className="w-8 h-px bg-muted"></div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-muted text-muted-foreground rounded-full flex items-center justify-center text-sm">2</div>
                <span className="text-muted-foreground">인증 확인</span>
              </div>
              <div className="w-8 h-px bg-muted"></div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-muted text-muted-foreground rounded-full flex items-center justify-center text-sm">3</div>
                <span className="text-muted-foreground">완료</span>
              </div>
            </div>

            <div className="text-center">
              <h3 className="text-xl font-bold mb-2">📱 QR 코드 스캔</h3>
              <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                인증 앱을 열고 아래 QR 코드를 스캔해주세요
              </p>

              {/* QR 코드 */}
              <div className="bg-white p-6 rounded-xl inline-block border-2 border-primary/20 shadow-lg">
                <QRCode
                  value={setupData.qrCodeUrl}
                  size={220}
                  style={{ height: "auto", maxWidth: "100%", width: "100%" }}
                />
              </div>

              {/* QR 코드 액션 */}
              <div className="flex justify-center space-x-3 mt-6">
                <Button variant="outline" size="sm" onClick={copyQrUrl} className="min-w-[100px]">
                  <Copy className="w-4 h-4 mr-2" />
                  URL 복사
                </Button>
                <Button variant="outline" size="sm" onClick={() => setStep('verify')} className="min-w-[140px]">
                  <Key className="w-4 h-4 mr-2" />
                  수동 입력으로 진행
                </Button>
              </div>
            </div>

            {/* 수동 입력을 위한 시크릿 키 */}
            <div className="bg-gradient-to-r from-muted/50 to-muted/30 p-5 rounded-xl border">
              <div className="flex items-center justify-between mb-3">
                <Label className="font-semibold flex items-center">
                  <Key className="w-4 h-4 mr-2" />
                  수동 입력용 시크릿 키
                </Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSecretKey(!showSecretKey)}
                >
                  {showSecretKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
              <div className="flex items-center space-x-3">
                <code className="bg-background px-3 py-2 rounded-lg text-sm flex-1 font-mono break-all border">
                  {showSecretKey ? setupData.secretKey : '•'.repeat(32)}
                </code>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => {
                    navigator.clipboard.writeText(setupData.secretKey);
                    setSuccess('시크릿 키가 복사되었습니다.');
                  }}
                  className="shrink-0"
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                💡 QR 코드를 스캔할 수 없는 경우에만 사용하세요
              </p>
            </div>

            <div className="text-center">
              <Button onClick={() => setStep('verify')} size="lg" className="min-w-[200px]">
                <ArrowRight className="w-5 h-5 mr-2" />
                다음: 인증 코드 입력
              </Button>
            </div>
          </div>
        )}

        {step === 'verify' && (
          <div className="space-y-6">
            {/* 진행 상태 표시 */}
            <div className="flex items-center justify-center space-x-2 mb-6">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-bull text-white rounded-full flex items-center justify-center text-sm font-bold">✓</div>
                <span className="text-bull font-medium">QR 스캔</span>
              </div>
              <div className="w-8 h-px bg-primary"></div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-bold">2</div>
                <span className="text-primary font-medium">인증 확인</span>
              </div>
              <div className="w-8 h-px bg-muted"></div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-muted text-muted-foreground rounded-full flex items-center justify-center text-sm">3</div>
                <span className="text-muted-foreground">완료</span>
              </div>
            </div>

            <div className="text-center">
              <h3 className="text-xl font-bold mb-2">🔐 인증 코드 입력</h3>
              <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
                인증 앱에서 생성된 6자리 코드를 입력하세요
              </p>
            </div>

            <div className="max-w-sm mx-auto space-y-4">
              <div className="space-y-2">
                <Label htmlFor="verification-code" className="text-center block font-semibold">
                  인증 코드
                </Label>
                <Input
                  id="verification-code"
                  type="text"
                  placeholder="000000"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center text-2xl font-mono tracking-[0.5em] h-14 border-2 focus:border-primary"
                  maxLength={6}
                  autoComplete="off"
                  autoFocus
                />
                {verificationCode.length === 6 && (
                  <p className="text-center text-sm text-bull flex items-center justify-center">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    코드가 자동으로 검증됩니다
                  </p>
                )}
              </div>

              {/* TOTP 타이머 힌트 */}
              <div className="bg-blue-50 dark:bg-blue-950/30 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="flex items-center justify-center space-x-2 text-blue-700 dark:text-blue-300">
                  <Timer className="w-4 h-4" />
                  <span className="text-sm">인증 코드는 30초마다 새로 생성됩니다</span>
                </div>
              </div>
            </div>

            <div className="flex justify-center space-x-4">
              <Button variant="outline" onClick={() => setStep('setup')} className="min-w-[100px]">
                <ArrowLeft className="w-4 h-4 mr-2" />
                이전
              </Button>
              <Button 
                onClick={verifyAndEnable}
                disabled={loading || verificationCode.length !== 6}
                className="min-w-[140px]"
              >
                {loading && <RefreshCw className="w-4 h-4 mr-2 animate-spin" />}
                {!loading && <Shield className="w-4 h-4 mr-2" />}
                인증 및 활성화
              </Button>
            </div>
          </div>
        )}

        {step === 'complete' && (
          <div className="space-y-6">
            {/* 완료 상태 표시 */}
            <div className="flex items-center justify-center space-x-2 mb-6">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-bull text-white rounded-full flex items-center justify-center text-sm font-bold">✓</div>
                <span className="text-bull font-medium">QR 스캔</span>
              </div>
              <div className="w-8 h-px bg-bull"></div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-bull text-white rounded-full flex items-center justify-center text-sm font-bold">✓</div>
                <span className="text-bull font-medium">인증 확인</span>
              </div>
              <div className="w-8 h-px bg-bull"></div>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-bull text-white rounded-full flex items-center justify-center text-sm font-bold">✓</div>
                <span className="text-bull font-medium">완료</span>
              </div>
            </div>

            <div className="text-center">
              <div className="relative">
                <div className="w-20 h-20 bg-gradient-to-br from-bull/20 to-bull/10 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-12 h-12 text-bull" />
                  {/* 성공 효과 */}
                  <div className="absolute inset-0 bg-bull/20 rounded-full animate-ping"></div>
                </div>
              </div>
              <h3 className="text-2xl font-bold text-bull mb-3">
                🎉 2단계 인증 활성화 완료!
              </h3>
              <p className="text-muted-foreground text-base">
                축하합니다! 계정이 이제 강력한 보안층으로 보호됩니다.
              </p>
            </div>

            {/* 백업 코드 */}
            {backupCodes.length > 0 && (
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 p-5 rounded-xl border border-amber-200 dark:border-amber-800">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-bold flex items-center text-amber-800 dark:text-amber-200">
                    <Key className="w-5 h-5 mr-2" />
                    🔑 백업 코드
                  </h4>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm" onClick={copyBackupCodes} className="bg-white/80">
                      <Copy className="w-4 h-4 mr-1" />
                      복사
                    </Button>
                    <Button variant="outline" size="sm" onClick={downloadBackupCodes} className="bg-white/80">
                      <Download className="w-4 h-4 mr-1" />
                      다운로드
                    </Button>
                  </div>
                </div>
                <div className="bg-amber-100 dark:bg-amber-900/30 p-3 rounded-lg mb-4 border border-amber-200 dark:border-amber-700">
                  <div className="flex items-start space-x-2">
                    <Info className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
                    <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                      <strong>중요:</strong> 휴대폰 분실 시 이 백업 코드로 로그인할 수 있습니다. 
                      <span className="underline">안전한 곳에 보관</span>하고 타인과 공유하지 마세요.
                    </p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {backupCodes.map((code, index) => (
                    <div key={index} className="bg-white dark:bg-gray-800 px-3 py-2 rounded-lg border border-amber-200 dark:border-amber-700">
                      <code className="font-mono text-sm text-center block">
                        {code}
                      </code>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-center space-y-4">
              <div className="bg-gradient-to-r from-bull/10 to-primary/10 p-4 rounded-lg border">
                <p className="text-sm text-muted-foreground mb-2">
                  ✨ 이제 로그인할 때 인증 앱의 6자리 코드가 필요합니다
                </p>
                <div className="flex items-center justify-center space-x-2 text-bull">
                  <Shield className="w-4 h-4" />
                  <span className="font-medium">보안 레벨: 높음</span>
                </div>
              </div>
              <Button onClick={() => setStep('overview')} size="lg" className="min-w-[150px]">
                <CheckCircle className="w-5 h-5 mr-2" />
                설정 완료
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}