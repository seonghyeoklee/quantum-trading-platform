'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Building2, Globe, ArrowRight, Shield, Zap, TrendingUp } from "lucide-react";

export default function PublicHomePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // 로그인된 사용자는 대시보드로 리다이렉트
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  // 로딩 중이거나 로그인된 사용자는 아무것도 표시하지 않음
  if (isLoading || isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-muted-foreground">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6">
            <div className="w-16 h-16 bg-primary rounded-xl flex items-center justify-center shadow-lg">
              <BarChart3 className="w-8 h-8 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-4xl lg:text-6xl font-bold mb-4">
            Quantum Trading Platform
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            전문적인 알고리즘 트레이딩 플랫폼으로 국내외 주식 투자를 시작하세요
          </p>
          <div className="space-x-4">
            <Button size="lg" onClick={() => router.push('/login')} className="px-8 py-3">
              로그인하기
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => router.push('/register')} className="px-8 py-3">
              회원가입
            </Button>
          </div>
        </div>

        {/* Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <Card className="text-center">
            <CardHeader>
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Building2 className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <CardTitle>국내 시장</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                KOSPI, KOSDAQ 실시간 거래<br />
                한국투자증권 API 연동
              </p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Globe className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <CardTitle>해외 시장</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                NYSE, NASDAQ 거래<br />
                실시간 해외 주식 투자
              </p>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <CardTitle>고급 분석</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                AI 기반 시장 분석<br />
                실시간 차트 및 지표
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Security & Performance Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <CardTitle>보안 우선</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                JWT 기반 인증과 서버 사이드 토큰 관리로 최고 수준의 보안을 제공합니다.
              </p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• 다중 환경 지원 (실전/모의투자)</li>
                <li>• 안전한 API 키 관리</li>
                <li>• 실시간 보안 모니터링</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/20 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                </div>
                <CardTitle>고성능 시스템</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                마이크로서비스 아키텍처와 실시간 데이터 처리로 최적의 성능을 보장합니다.
              </p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• WebSocket 실시간 데이터</li>
                <li>• Spring Boot + FastAPI</li>
                <li>• Apache Airflow 분석 파이프라인</li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="text-center bg-gradient-to-r from-primary/10 via-primary/5 to-primary/10 rounded-2xl p-12">
          <h2 className="text-3xl font-bold mb-4">지금 시작하세요</h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            전문 트레이더들이 사용하는 고급 도구와 실시간 데이터로 투자의 새로운 경험을 시작하세요.
          </p>
          <Button size="lg" onClick={() => router.push('/login')} className="px-12 py-4 text-lg">
            플랫폼 시작하기
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </main>
    </div>
  );
}