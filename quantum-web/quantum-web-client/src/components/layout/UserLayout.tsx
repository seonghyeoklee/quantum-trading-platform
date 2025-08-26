'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/theme-toggle';
import LogoutDialog from '@/components/auth/LogoutDialog';
import { 
  ArrowLeft,
  Home,
  Settings,
  Shield,
  User,
  LogOut,
  BarChart3,
  Bell,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Globe
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import UserInfo from './UserInfo';

interface UserLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  showAdminAccess?: boolean;
  actions?: React.ReactNode;
}

export default function UserLayout({ 
  children, 
  title, 
  subtitle, 
  showAdminAccess = true,
  actions 
}: UserLayoutProps) {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const getQuickActions = () => {
    const buttons = [];
    
    // 설정 버튼 (현재 페이지가 설정이 아닐 때만)
    if (!title.includes('설정')) {
      buttons.push(
        <Button 
          key="settings"
          variant="outline" 
          size="sm" 
          onClick={() => router.push('/settings')}
        >
          <Settings className="w-4 h-4 mr-2" />
          설정
        </Button>
      );
    }

    // 프로필 버튼 (현재 페이지가 프로필이 아닐 때만)
    if (!title.includes('내 정보')) {
      buttons.push(
        <Button 
          key="profile"
          variant="outline" 
          size="sm" 
          onClick={() => router.push('/profile')}
        >
          <User className="w-4 h-4 mr-2" />
          내 정보
        </Button>
      );
    }

    // 관리자 접근 버튼 (관리자이고 설정에서 활성화된 경우)
    if (showAdminAccess && user?.roles?.includes('ADMIN')) {
      buttons.push(
        <Button 
          key="admin"
          variant="outline" 
          size="sm" 
          onClick={() => router.push('/admin/dashboard')}
        >
          <Shield className="w-4 h-4 mr-2" />
          관리자
        </Button>
      );
    }

    return buttons;
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card sticky top-0 z-50">
        {/* Top Navigation - 메인 헤더와 동일한 구조 유지 */}
        <div className="px-4 py-2 border-b border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="font-bold text-lg">Quantum Trading</span>
              </div>
              
              {/* 간단한 네비게이션 힌트 */}
              <nav className="hidden md:flex items-center space-x-4 text-sm text-muted-foreground">
                <span>사용자 관리</span>
              </nav>
            </div>

            <div className="flex items-center space-x-3">
              {/* 알림 */}
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="w-4 h-4" />
                <div className="absolute -top-1 -right-1 w-2 h-2 bg-destructive rounded-full"></div>
              </Button>
              
              <ThemeToggle />
              
              {/* 사용자 정보 */}
              <div className="pl-3 border-l border-border">
                <div className="hidden md:flex items-center space-x-2 mr-2">
                  <UserInfo />
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Market Summary Bar - 일관성을 위해 유지하되 사용자 컨텍스트로 조정 */}
        <div className="px-4 py-2 bg-muted border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-muted-foreground">KOSPI</span>
                <span className="font-medium">2,647.82</span>
                <span className="text-red-600 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  +1.23%
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-muted-foreground">KOSDAQ</span>
                <span className="font-medium">742.15</span>
                <span className="text-blue-600 flex items-center">
                  <TrendingDown className="w-3 h-3 mr-1" />
                  -0.84%
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-muted-foreground">USD/KRW</span>
                <span className="font-medium">1,347.50</span>
                <span className="text-red-600 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  +0.32%
                </span>
              </div>
            </div>
            
            {/* 페이지 컨텍스트 표시 */}
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              <Globe className="w-4 h-4" />
              <span>실시간 데이터</span>
              <span>•</span>
              <span className="text-primary font-medium">{title}</span>
            </div>
          </div>
        </div>

        {/* Page Navigation Bar - 개선된 네비게이션 */}
        <div className="px-4 py-3 bg-muted/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* 브레드크럼 스타일 네비게이션 */}
              <div className="flex items-center space-x-2 text-sm">
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => router.push('/')}
                  className="h-auto p-1 hover:bg-transparent hover:text-primary"
                >
                  <Home className="w-4 h-4" />
                </Button>
                <ChevronRight className="w-3 h-3 text-muted-foreground" />
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => router.back()}
                  className="h-auto p-1 hover:bg-transparent hover:text-primary text-muted-foreground hover:text-primary"
                >
                  <ArrowLeft className="w-3 h-3 mr-1" />
                  뒤로
                </Button>
                <ChevronRight className="w-3 h-3 text-muted-foreground" />
                <span className="font-medium text-foreground">{title}</span>
              </div>
              
              {subtitle && (
                <div className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                  {subtitle}
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* 커스텀 액션 버튼들 */}
              {actions}
              
              {/* 기본 액션 버튼들 */}
              {getQuickActions()}
              
              {/* 로그아웃 버튼 */}
              <LogoutDialog onLogout={handleLogout}>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="text-destructive border-destructive/50 hover:bg-destructive/10"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  <span className="hidden sm:inline">로그아웃</span>
                </Button>
              </LogoutDialog>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8 max-w-6xl">
        {children}
      </main>
    </div>
  );
}