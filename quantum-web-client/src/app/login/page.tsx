'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { BarChart3, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: 'admin@quantum.local',
    password: 'admin123'
  })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/')
    }
  }, [isAuthenticated, isLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login(formData.email, formData.password)
    } catch (err) {
      setError(err instanceof Error ? err.message : '로그인에 실패했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
    if (error) setError('')
  }

  // 로그인 상태일 때는 빈 화면 표시 (리디렉트 처리 중)
  if (isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo and Title */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-primary rounded-lg flex items-center justify-center">
              <BarChart3 className="w-8 h-8 text-primary-foreground" />
            </div>
          </div>
          <div className="space-y-2">
            <h1 className="text-3xl font-bold">Quantum Trading</h1>
            <p className="text-muted-foreground">지능형 주식 거래 플랫폼</p>
          </div>
        </div>

        {/* Login Form */}
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl">로그인</CardTitle>
            <CardDescription>
              계정 정보를 입력하여 로그인하세요
            </CardDescription>
          </CardHeader>
          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">이메일</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="이메일을 입력해주세요"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  disabled={isSubmitting}
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">비밀번호</Label>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="비밀번호를 입력해주세요"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    disabled={isSubmitting}
                    className="h-11 pr-10"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={isSubmitting}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col space-y-4">
              <Button
                type="submit"
                className="w-full h-11"
                disabled={isSubmitting || !formData.email || !formData.password}
              >
                {isSubmitting ? '로그인 중...' : '로그인'}
              </Button>
              
              <div className="text-center text-sm text-muted-foreground">
                <p>안전한 거래 환경</p>
                <p className="mt-1 text-xs">24시간 보안 인증</p>
              </div>
            </CardFooter>
          </form>
        </Card>

        {/* Development Info */}
        {process.env.NODE_ENV === 'development' && (
          <Card className="border-dashed">
            <CardContent className="pt-6">
              <div className="text-center space-y-2">
                <h3 className="font-semibold text-sm">데모 계정</h3>
                <div className="text-xs text-muted-foreground space-y-1">
                  <p><strong>이메일:</strong> admin@quantum.local</p>
                  <p><strong>비밀번호:</strong> admin123</p>
                  <p className="mt-2 text-orange-600">⚠️ 테스트 환경용</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}