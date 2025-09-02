'use client';

import { useAuth } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import Header from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { 
  User, 
  Mail, 
  Shield, 
  Calendar, 
  Clock, 
  Settings,
  Edit,
  Key
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useEffect, useState } from 'react';

function ProfilePage() {
  const { user } = useAuth();
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!user) return null;

  const getUserInitials = (name: string) => {
    if (name.includes('@')) {
      // 이메일인 경우 @ 앞의 처음 두 글자
      return name.split('@')[0].substring(0, 2).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const formatDate = (dateString: string) => {
    // 클라이언트에서만 날짜 포맷팅 (하이드레이션 문제 방지)
    if (!mounted) {
      return dateString; // 서버 사이드에서는 원본 문자열 반환
    }
    
    try {
      return format(new Date(dateString), 'PPP p', { locale: ko });
    } catch {
      return dateString;
    }
  };


  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container max-w-6xl mx-auto py-8 px-4">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">내 정보</h1>
              <p className="text-muted-foreground">개인 정보 및 계정 설정</p>
            </div>
            <Button variant="outline" size="sm">
              <Edit className="w-4 h-4 mr-2" />
              정보 수정
            </Button>
          </div>
        </div>

        <div className="grid gap-8">
          {/* Profile Overview Card */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Avatar className="w-20 h-20">
                    <AvatarFallback className="bg-primary text-primary-foreground text-xl">
                      {getUserInitials(user.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-2xl">{user.name}</CardTitle>
                    <CardDescription className="text-base">{user.email}</CardDescription>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <Badge variant="default" className="text-xs">
                        관리자
                      </Badge>
                    </div>
                  </div>
                </div>
                <Button variant="outline" size="sm">
                  <Edit className="w-4 h-4 mr-2" />
                  편집
                </Button>
              </div>
            </CardHeader>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Basic Information */}
            <Card className="trading-card">
              <CardHeader className="trading-card-header">
                <CardTitle className="flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  기본 정보
                </CardTitle>
                <CardDescription>
                  계정의 기본 정보입니다
                </CardDescription>
              </CardHeader>
              <CardContent className="trading-card-content space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <User className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">사용자명</span>
                  </div>
                  <span className="text-sm font-medium">{user.name}</span>
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">이메일</span>
                  </div>
                  <span className="text-sm font-medium">{user.email}</span>
                </div>
                
                <Separator />
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Key className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm">계정 ID</span>
                  </div>
                  <span className="text-sm font-medium text-muted-foreground">{user.id}</span>
                </div>
              </CardContent>
            </Card>

            {/* Role & Permissions */}
            <Card className="trading-card">
              <CardHeader className="trading-card-header">
                <CardTitle className="flex items-center">
                  <Shield className="w-5 h-5 mr-2" />
                  권한 정보
                </CardTitle>
                <CardDescription>
                  현재 계정의 권한 및 역할 정보입니다
                </CardDescription>
              </CardHeader>
              <CardContent className="trading-card-content space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Badge variant="default" className="text-xs">
                        관리자
                      </Badge>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    시스템 관리자 - 모든 권한
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Login Activity */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                로그인 기록
              </CardTitle>
              <CardDescription>
                최근 로그인 정보입니다
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Calendar className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">마지막 로그인</span>
                </div>
                <span className="text-sm font-medium">
                  {formatDate(user.last_login_at || new Date().toISOString())}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* User Preferences */}
          <Card className="trading-card">
            <CardHeader className="trading-card-header">
              <CardTitle className="flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                사용자 설정
              </CardTitle>
              <CardDescription>
                개인 맞춤 설정 정보입니다
              </CardDescription>
            </CardHeader>
            <CardContent className="trading-card-content space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">언어</span>
                <Badge variant="outline" className="text-xs">
                  한국어
                </Badge>
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <span className="text-sm">시간대</span>
                <Badge variant="outline" className="text-xs">
                  Asia/Seoul
                </Badge>
              </div>
              
              <Separator />
              
              <div className="flex items-center justify-between">
                <span className="text-sm">테마</span>
                <Badge variant="outline" className="text-xs">
                  System
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default function ProtectedProfilePage() {
  return (
    <ProtectedRoute>
      <ProfilePage />
    </ProtectedRoute>
  );
}