'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/theme-toggle';
import { 
  ArrowLeft,
  Home,
  Settings,
  Shield,
  User,
  LogOut
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

  const handleLogout = () => {
    if (confirm('정말 로그아웃 하시겠습니까?')) {
      logout();
      router.push('/login');
    }
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
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-4">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => router.back()}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>뒤로</span>
            </Button>
            <div>
              <h1 className="text-xl font-bold">{title}</h1>
              {subtitle && (
                <p className="text-sm text-muted-foreground">{subtitle}</p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* 사용자 정보 표시 (작은 화면에서는 숨김) */}
            <div className="hidden md:flex items-center space-x-2 mr-2">
              <UserInfo />
            </div>

            {/* 커스텀 액션 버튼들 */}
            {actions}
            
            {/* 기본 액션 버튼들 */}
            {getQuickActions()}
            
            {/* 홈 버튼 */}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => router.push('/')}
            >
              <Home className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">홈</span>
            </Button>

            {/* 로그아웃 버튼 */}
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleLogout}
              className="text-destructive border-destructive/50 hover:bg-destructive/10"
            >
              <LogOut className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">로그아웃</span>
            </Button>

            <ThemeToggle />
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