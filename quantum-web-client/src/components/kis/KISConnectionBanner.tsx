'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Shield, 
  AlertCircle, 
  CheckCircle, 
  Settings, 
  TrendingUp, 
  BarChart3,
  Clock,
  ExternalLink
} from 'lucide-react';

interface KISConnectionBannerProps {
  variant?: 'compact' | 'full';
  showDismiss?: boolean;
}

export function KISConnectionBanner({ variant = 'full', showDismiss = false }: KISConnectionBannerProps) {
  const { hasKISAccount, isKISSetupRequired, forceKISSetup, skipKISSetup, kisTokens } = useAuth();

  if (hasKISAccount && kisTokens.sandbox) {
    return null; // KIS 연결이 완료되면 배너 숨김
  }

  if (variant === 'compact') {
    return (
      <Alert className="border-orange-200 bg-orange-50">
        <AlertCircle className="h-4 w-4 text-orange-600" />
        <AlertDescription className="flex items-center justify-between">
          <span className="text-orange-800">
            실시간 데이터 조회를 위해 KIS 계정 연결이 필요합니다
          </span>
          <Button 
            size="sm" 
            variant="outline"
            onClick={forceKISSetup}
            className="ml-4 border-orange-300 text-orange-700 hover:bg-orange-100"
          >
            연결하기
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50">
      <CardContent className="p-6">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          
          <div className="flex-1 space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <span>KIS 계정 연결</span>
                <div className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded">
                  필수 설정
                </div>
              </h3>
              <p className="text-gray-600 mt-1">
                한국투자증권 API를 연결하여 실시간 주식 데이터를 조회하고 자동매매 기능을 이용하세요
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <BarChart3 className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <div className="font-medium text-sm">실시간 시세</div>
                  <div className="text-xs text-gray-500">국내/해외 주식 실시간 조회</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-blue-600" />
                </div>
                <div>
                  <div className="font-medium text-sm">자동매매</div>
                  <div className="text-xs text-gray-500">전략 기반 자동 주문 실행</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <Clock className="w-4 h-4 text-purple-600" />
                </div>
                <div>
                  <div className="font-medium text-sm">계좌 관리</div>
                  <div className="text-xs text-gray-500">잔고 및 주문 내역 조회</div>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Button 
                onClick={forceKISSetup}
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                <Settings className="w-4 h-4 mr-2" />
                KIS 계정 연결하기
              </Button>
              
              <Button 
                variant="outline" 
                onClick={skipKISSetup}
                className="border-gray-300"
              >
                나중에 설정
              </Button>
              
              <Button 
                variant="ghost" 
                asChild
                className="text-orange-600 hover:text-orange-700"
              >
                <a 
                  href="https://apiportal.koreainvestment.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center"
                >
                  API 계정 생성 <ExternalLink className="w-4 h-4 ml-1" />
                </a>
              </Button>
            </div>

            <Alert className="border-blue-200 bg-blue-50">
              <Shield className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-800">
                <strong>보안 안내:</strong> API 키는 암호화되어 안전하게 저장되며, 절대 제3자와 공유되지 않습니다.
                모의투자 환경에서 먼저 테스트해보는 것을 권장합니다.
              </AlertDescription>
            </Alert>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default KISConnectionBanner;