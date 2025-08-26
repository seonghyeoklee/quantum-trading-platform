'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Shield, 
  Smartphone, 
  Key, 
  AlertTriangle,
  RefreshCw,
  ArrowLeft,
  Clock
} from 'lucide-react';

interface TwoFactorLoginProps {
  username: string;
  onVerify: (code: string, isBackupCode?: boolean) => Promise<void>;
  onBack: () => void;
  loading?: boolean;
  error?: string;
}

export default function TwoFactorLogin({ 
  username, 
  onVerify, 
  onBack, 
  loading = false, 
  error = '' 
}: TwoFactorLoginProps) {
  const [codes, setCodes] = useState(['', '', '', '', '', '']);
  const [backupCode, setBackupCode] = useState('');
  const [useBackupCode, setUseBackupCode] = useState(false);
  const [localError, setLocalError] = useState('');
  const [timeRemaining, setTimeRemaining] = useState(30);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // 30초 카운트다운 타이머
  useEffect(() => {
    if (timeRemaining > 0) {
      const timer = setTimeout(() => setTimeRemaining(prev => prev - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      setTimeRemaining(30); // 리셋
    }
  }, [timeRemaining]);

  // 외부 error가 발생하면 코드 초기화 (2FA 인증 실패 시)
  useEffect(() => {
    if (error && !useBackupCode) {
      setCodes(['', '', '', '', '', '']);
      setTimeout(() => {
        inputRefs.current[0]?.focus();
      }, 100);
    } else if (error && useBackupCode) {
      setBackupCode('');
    }
  }, [error, useBackupCode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');

    if (useBackupCode) {
      if (!backupCode.trim()) {
        setLocalError('백업 코드를 입력해주세요.');
        return;
      }
      try {
        await onVerify(backupCode.trim(), true);
      } catch (error) {
        // 백업 코드 실패 시 초기화
        setBackupCode('');
      }
    } else {
      const fullCode = codes.join('');
      if (fullCode.length !== 6) {
        setLocalError('6자리 인증 코드를 모두 입력해주세요.');
        return;
      }
      try {
        await onVerify(fullCode);
      } catch (error) {
        // 인증 코드 실패 시 초기화하고 첫 번째 입력으로 포커스
        setCodes(['', '', '', '', '', '']);
        setTimeout(() => {
          inputRefs.current[0]?.focus();
        }, 100);
      }
    }
  };

  const handleCodeChange = (index: number, value: string) => {
    // 숫자만 허용
    if (value && !/^\d$/.test(value)) return;
    
    const newCodes = [...codes];
    newCodes[index] = value;
    setCodes(newCodes);
    setLocalError('');

    // 자동으로 다음 입력으로 포커스 이동
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // 모든 코드가 입력되면 자동 제출
    if (newCodes.every(code => code) && !loading) {
      const fullCode = newCodes.join('');
      onVerify(fullCode).catch(() => {
        // 자동 제출 실패 시에도 초기화하고 첫 번째 입력으로 포커스
        setCodes(['', '', '', '', '', '']);
        setTimeout(() => {
          inputRefs.current[0]?.focus();
        }, 100);
      });
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !codes[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pastedData) {
      const newCodes = pastedData.split('').concat(Array(6 - pastedData.length).fill(''));
      setCodes(newCodes as string[]);
      
      // 마지막 입력된 위치로 포커스
      const nextIndex = Math.min(pastedData.length, 5);
      inputRefs.current[nextIndex]?.focus();
    }
  };

  const handleBackupCodeChange = (value: string) => {
    setBackupCode(value);
    setLocalError('');
  };

  const displayError = error || localError;

  return (
    <Card className="w-full max-w-md mx-auto trading-card">
      <CardHeader className="text-center trading-card-header">
        <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <Shield className="w-8 h-8 text-primary" />
        </div>
        <CardTitle className="text-xl">2단계 인증</CardTitle>
        <CardDescription>
          <span className="font-medium text-foreground">{username}</span>님의 보안을 위해<br />
          인증 코드를 입력해주세요
        </CardDescription>
      </CardHeader>

      <CardContent className="trading-card-content">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 에러 메시지 */}
          {displayError && (
            <Alert variant="destructive" className="border-destructive/50">
              <AlertTriangle className="w-4 h-4" />
              <AlertDescription>{displayError}</AlertDescription>
            </Alert>
          )}

          {!useBackupCode ? (
            /* 개선된 6자리 코드 입력 */
            <div className="space-y-6">
              <div className="text-center space-y-3">
                <div className="flex items-center justify-center space-x-2">
                  <Smartphone className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">
                    인증 앱에서 6자리 코드 확인
                  </span>
                </div>
                
                <div className="flex items-center justify-center space-x-2 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  <span>코드 갱신까지 {timeRemaining}초</span>
                </div>
              </div>

              {/* 6자리 개별 입력 박스 */}
              <div className="space-y-4">
                <div className="flex justify-center space-x-3">
                  {codes.map((code, index) => (
                    <Input
                      key={index}
                      ref={el => inputRefs.current[index] = el}
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]"
                      value={code}
                      onChange={(e) => handleCodeChange(index, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(index, e)}
                      onPaste={index === 0 ? handlePaste : undefined}
                      className="w-12 h-14 text-center text-xl font-mono border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                      maxLength={1}
                      autoComplete="one-time-code"
                      autoFocus={index === 0}
                      disabled={loading}
                    />
                  ))}
                </div>

                <div className="text-center space-y-2">
                  <p className="text-xs text-muted-foreground">
                    Google Authenticator, Authy, Microsoft Authenticator 등에서 생성된 코드
                  </p>
                  <p className="text-xs text-primary">
                    💡 코드를 복사해서 붙여넣기 할 수 있습니다
                  </p>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full h-12 bg-primary hover:bg-primary/90"
                disabled={loading || codes.some(code => !code)}
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>인증 중...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Shield className="w-4 h-4" />
                    <span>로그인 완료</span>
                  </div>
                )}
              </Button>

              <Separator />

              <div className="text-center">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setUseBackupCode(true)}
                  className="text-muted-foreground hover:text-foreground"
                  disabled={loading}
                >
                  <Key className="w-4 h-4 mr-2" />
                  백업 코드로 로그인
                </Button>
              </div>
            </div>
          ) : (
            /* 개선된 백업 코드 입력 */
            <div className="space-y-6">
              <div className="text-center space-y-3">
                <div className="flex items-center justify-center space-x-2">
                  <Key className="w-5 h-5 text-primary" />
                  <span className="text-sm font-medium">
                    백업 코드로 로그인
                  </span>
                </div>
                <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                  <p className="text-xs text-amber-700 dark:text-amber-200">
                    ⚠️ 백업 코드는 일회용입니다. 사용 후 새로운 백업 코드를 생성하세요.
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <Label htmlFor="backup-code" className="sr-only">
                  백업 코드
                </Label>
                <Input
                  id="backup-code"
                  type="text"
                  placeholder="12345678"
                  value={backupCode}
                  onChange={(e) => handleBackupCodeChange(e.target.value)}
                  className="text-center font-mono tracking-wider h-14 text-lg border-2 focus:border-primary focus:ring-2 focus:ring-primary/20"
                  maxLength={8}
                  autoComplete="one-time-code"
                  autoFocus
                  disabled={loading}
                />
                <div className="text-center space-y-2">
                  <p className="text-xs text-muted-foreground">
                    2FA 설정 시 다운로드한 8자리 백업 코드 중 하나를 입력하세요
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400">
                    ⚠️ 백업 코드를 분실한 경우 관리자에게 문의하세요
                  </p>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full h-12 bg-amber-600 hover:bg-amber-700 text-white"
                disabled={loading || !backupCode.trim()}
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>인증 중...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Key className="w-4 h-4" />
                    <span>백업 코드로 로그인</span>
                  </div>
                )}
              </Button>

              <div className="text-center">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setUseBackupCode(false);
                    setBackupCode('');
                    setCodes(['', '', '', '', '', '']);
                  }}
                  className="text-muted-foreground hover:text-foreground"
                  disabled={loading}
                >
                  <Smartphone className="w-4 h-4 mr-2" />
                  인증 앱 코드로 돌아가기
                </Button>
              </div>
            </div>
          )}

          <Separator className="my-6" />

          {/* 뒤로 가기 */}
          <div className="text-center">
            <Button
              type="button"
              variant="outline"
              onClick={onBack}
              disabled={loading}
              className="w-full h-11 border-border hover:bg-muted"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              다른 계정으로 로그인
            </Button>
            
            <p className="text-xs text-muted-foreground mt-3">
              로그인에 문제가 있나요? 관리자에게 문의하세요.
            </p>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}