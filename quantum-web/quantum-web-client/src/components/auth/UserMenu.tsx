'use client';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import LogoutDialog from './LogoutDialog';
import { User, Settings, Shield, ChevronDown, Key } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function UserMenu() {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();

  // 로딩 중이면 스켈레톤 UI 표시 (사용자 정보가 없는 경우에만)
  if (isLoading && !user) {
    return (
      <div className="flex items-center space-x-3 px-3 py-2 animate-pulse">
        <div className="w-8 h-8 bg-muted rounded-full"></div>
        <div className="flex flex-col space-y-1">
          <div className="w-16 h-3 bg-muted rounded"></div>
          <div className="w-24 h-2 bg-muted rounded"></div>
        </div>
      </div>
    );
  }

  // 사용자 정보가 없으면 숨김
  if (!user) return null;

  const getUserInitials = (username: string) => {
    return username.substring(0, 2).toUpperCase();
  };

  const handleProfileClick = () => {
    router.push('/profile');
  };

  const handleSettingsClick = () => {
    router.push('/settings');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex items-center space-x-3 px-3 py-2 h-auto">
          <Avatar className="w-8 h-8">
            <AvatarImage src={user.avatar} alt={user.username} />
            <AvatarFallback className="bg-primary text-primary-foreground text-xs">
              {getUserInitials(user.username)}
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col items-start">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">{user.username}</span>
              <Badge variant="secondary" className="text-xs">
                {user.roles?.[0] || 'USER'}
              </Badge>
            </div>
            <span className="text-xs text-muted-foreground">{user.email}</span>
          </div>
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-64" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.username}</p>
            <p className="text-xs leading-none text-muted-foreground">{user.email}</p>
            <div className="flex flex-wrap gap-1 mt-2">
              {user.roles?.map((role) => (
                <Badge key={role} variant="outline" className="text-xs">
                  {role}
                </Badge>
              ))}
            </div>
          </div>
        </DropdownMenuLabel>
        
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={handleProfileClick} className="cursor-pointer">
          <User className="mr-2 h-4 w-4" />
          <span>내 정보</span>
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={handleSettingsClick} className="cursor-pointer">
          <Settings className="mr-2 h-4 w-4" />
          <span>설정</span>
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => router.push('/kiwoom-account')} className="cursor-pointer">
          <Key className="mr-2 h-4 w-4" />
          <span>키움증권 계좌</span>
        </DropdownMenuItem>
        
        {user.roles?.includes('ADMIN') && (
          <>
            <DropdownMenuItem onClick={() => router.push('/admin/dashboard')} className="cursor-pointer">
              <Shield className="mr-2 h-4 w-4" />
              <span>관리자 대시보드</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push('/admin/users')} className="cursor-pointer">
              <User className="mr-2 h-4 w-4" />
              <span>사용자 관리</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push('/admin/security/login-history')} className="cursor-pointer">
              <Shield className="mr-2 h-4 w-4" />
              <span>로그인 이력</span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push('/admin/security/metrics')} className="cursor-pointer">
              <Shield className="mr-2 h-4 w-4" />
              <span>보안 메트릭스</span>
            </DropdownMenuItem>
          </>
        )}
        
        <DropdownMenuSeparator />
        
        <LogoutDialog onLogout={logout}>
          <DropdownMenuItem 
            className="cursor-pointer text-destructive focus:text-destructive"
            onSelect={(e) => e.preventDefault()} // Prevent dropdown from closing
          >
            <span className="w-full">로그아웃</span>
          </DropdownMenuItem>
        </LogoutDialog>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}