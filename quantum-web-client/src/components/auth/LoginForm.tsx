'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Eye, EyeOff, AlertCircle } from 'lucide-react';

interface LoginFormProps {
  onLogin: (credentials: { username: string; password: string }) => Promise<void>;
  isLoading: boolean;
  error: string;
}

export default function LoginForm({ onLogin, isLoading, error }: LoginFormProps) {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onLogin(formData);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
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
          className="h-11 bg-input border-border focus:ring-2 focus:ring-primary focus:border-primary"
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
            className="h-11 bg-input border-border focus:ring-2 focus:ring-primary focus:border-primary pr-11"
            required
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 flex items-center justify-center w-11 text-muted-foreground hover:text-foreground transition-colors"
            disabled={isLoading}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* 로그인 버튼 */}
      <Button
        type="submit"
        className="w-full h-11 bg-primary hover:bg-primary/90 text-primary-foreground font-medium transition-colors"
        disabled={isLoading || !formData.username || !formData.password}
      >
        {isLoading ? (
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            <span>로그인 중...</span>
          </div>
        ) : (
          '로그인'
        )}
      </Button>
    </form>
  );
}