'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, ArrowLeft, Shield } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function UnauthorizedPage() {
  const { user, logout } = useAuth();

  const handleGoBack = () => {
    window.history.back();
  };

  const handleGoToDashboard = () => {
    window.location.href = '/dashboard';
  };

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-8 h-8 text-amber-600" />
          </div>
          <CardTitle className="text-xl text-gray-900">접근 권한이 없습니다</CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="text-center text-sm text-gray-600">
            <p className="mb-2">
              요청하신 페이지에 접근할 권한이 없습니다.
            </p>
            <p>
              필요한 권한이 있다고 생각되시면 관리자에게 문의해주세요.
            </p>
          </div>

          {user && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">현재 로그인:</span>
                <span className="font-medium">{user.name || user.username}</span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">사용자 권한:</span>
                <div className="flex flex-wrap gap-1">
                  {user.roles && user.roles.length > 0 ? (
                    user.roles.map((role, index) => (
                      <span 
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                      >
                        {role.replace('ROLE_', '')}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-400 text-xs">권한 없음</span>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <Button 
              onClick={handleGoBack}
              variant="outline"
              className="w-full"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              이전 페이지로 돌아가기
            </Button>
            
            <Button 
              onClick={handleGoToDashboard}
              className="w-full"
            >
              <Shield className="w-4 h-4 mr-2" />
              대시보드로 이동
            </Button>

            <div className="pt-2 border-t">
              <Button 
                onClick={handleLogout}
                variant="outline"
                className="w-full text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200"
              >
                다른 계정으로 로그인
              </Button>
            </div>
          </div>

          <div className="text-center text-xs text-gray-500">
            <p>문제가 지속되면 시스템 관리자에게 연락하세요.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}