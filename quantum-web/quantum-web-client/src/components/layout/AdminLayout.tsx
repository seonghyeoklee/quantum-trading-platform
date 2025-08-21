'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { 
  LayoutDashboard, 
  TrendingUp, 
  PieChart, 
  Settings, 
  Users, 
  LogOut, 
  Menu, 
  X,
  Shield,
  BarChart3,
  Wallet,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface AdminLayoutProps {
  children: React.ReactNode;
}

interface MenuItem {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: string[];
  badge?: string;
}

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: '대시보드',
    href: '/dashboard',
    icon: LayoutDashboard,
    roles: ['ADMIN', 'MANAGER', 'TRADER'],
  },
  {
    id: 'charts',
    label: '차트 분석',
    href: '/charts',
    icon: TrendingUp,
    roles: ['ADMIN', 'MANAGER', 'TRADER'],
    badge: 'Live',
  },
  {
    id: 'portfolio',
    label: '포트폴리오',
    href: '/portfolio',
    icon: PieChart,
    roles: ['ADMIN', 'MANAGER'],
  },
  {
    id: 'trading',
    label: '거래 관리',
    href: '/trading',
    icon: BarChart3,
    roles: ['ADMIN', 'MANAGER', 'TRADER'],
  },
  {
    id: 'accounts',
    label: '계좌 관리',
    href: '/accounts',
    icon: Wallet,
    roles: ['ADMIN', 'MANAGER'],
  },
  {
    id: 'risk',
    label: '리스크 관리',
    href: '/risk',
    icon: AlertTriangle,
    roles: ['ADMIN', 'MANAGER'],
  },
  {
    id: 'users',
    label: '사용자 관리',
    href: '/admin/users',
    icon: Users,
    roles: ['ADMIN'],
  },
  {
    id: 'settings',
    label: '시스템 설정',
    href: '/admin/settings',
    icon: Settings,
    roles: ['ADMIN'],
  },
];

export const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const { user, logout, hasAnyRole } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // 현재 경로 확인
  const currentPath = typeof window !== 'undefined' ? window.location.pathname : '';

  // 사용자가 접근 가능한 메뉴 항목만 필터링
  const accessibleMenuItems = menuItems.filter(item => 
    hasAnyRole(item.roles)
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:inset-0
      `}>
        <div className="flex flex-col h-full">
          {/* Logo & Title */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-gray-900">Quantum Trading</span>
                <span className="text-xs text-gray-500">Admin Panel</span>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden p-1 rounded-md hover:bg-gray-100"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* User Info */}
          <div className="p-4 border-b">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-sm font-semibold text-blue-600">
                  {user?.name?.charAt(0) || user?.username?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user?.name || user?.username}
                </p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {user?.roles?.map((role) => (
                    <Badge 
                      key={role} 
                      variant="secondary" 
                      className="text-xs"
                    >
                      {role.replace('ROLE_', '')}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Menu */}
          <nav className="flex-1 p-4 space-y-2">
            {accessibleMenuItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPath === item.href || 
                              (item.href !== '/dashboard' && currentPath.startsWith(item.href));
              
              return (
                <a
                  key={item.id}
                  href={item.href}
                  className={`
                    flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors
                    ${isActive 
                      ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-600' 
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                  onClick={() => setSidebarOpen(false)}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <Badge variant="outline" className="text-xs">
                      {item.badge}
                    </Badge>
                  )}
                </a>
              );
            })}
          </nav>

          {/* Logout Button */}
          <div className="p-4 border-t">
            <Button
              variant="outline"
              className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50"
              onClick={handleLogout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              로그아웃
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-md hover:bg-gray-100"
              >
                <Menu className="w-5 h-5" />
              </button>

              {/* Page Title */}
              <div className="flex-1 lg:flex-initial">
                <h1 className="text-lg font-semibold text-gray-900">
                  {accessibleMenuItems.find(item => 
                    currentPath === item.href || 
                    (item.href !== '/dashboard' && currentPath.startsWith(item.href))
                  )?.label || '대시보드'}
                </h1>
              </div>

              {/* Header Actions */}
              <div className="flex items-center space-x-4">
                {/* Connection Status */}
                <div className="hidden sm:flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-gray-600">실시간 연결됨</span>
                </div>

                {/* User Menu */}
                <div className="flex items-center space-x-2 text-sm text-gray-700">
                  <span className="hidden sm:inline">{user?.name || user?.username}</span>
                  <Badge variant="outline" className="hidden sm:inline-flex">
                    {user?.roles?.[0]?.replace('ROLE_', '') || 'USER'}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;