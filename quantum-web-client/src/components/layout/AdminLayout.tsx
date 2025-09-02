'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/theme-toggle';
import { 
  Shield, 
  Users, 
  BarChart3, 
  Menu,
  X,
  Home,
  Settings,
  Activity,
  Globe,
  Clock,
  AlertTriangle,
  Eye,
  RefreshCw,
  ChevronRight,
  User
} from 'lucide-react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';

interface AdminLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

interface MenuItem {
  id: string;
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: '대시보드',
    href: '/admin/dashboard',
    icon: <BarChart3 className="w-5 h-5" />
  },
  {
    id: 'users',
    label: '사용자 관리',
    href: '/admin/users',
    icon: <Users className="w-5 h-5" />
  },
  {
    id: 'security',
    label: '보안 관리',
    href: '/admin/security',
    icon: <Shield className="w-5 h-5" />,
    children: [
      {
        id: 'login-history',
        label: '로그인 이력',
        href: '/admin/security/login-history',
        icon: <Clock className="w-4 h-4" />
      },
      {
        id: 'security-metrics',
        label: '보안 메트릭스',
        href: '/admin/security/metrics',
        icon: <Activity className="w-4 h-4" />
      }
    ]
  },
  {
    id: 'settings',
    label: '시스템 설정',
    href: '/admin/settings',
    icon: <Settings className="w-5 h-5" />
  }
];

export default function AdminLayout({ children, title, subtitle, actions }: AdminLayoutProps) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState<string[]>(['security']); // 기본으로 보안 메뉴 확장

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const toggleMenu = (menuId: string) => {
    setExpandedMenus(prev => 
      prev.includes(menuId) 
        ? prev.filter(id => id !== menuId)
        : [...prev, menuId]
    );
  };

  const isActiveMenu = (href: string) => {
    return pathname === href || pathname.startsWith(href + '/');
  };

  const handleLogout = () => {
    if (confirm('정말 로그아웃 하시겠습니까?')) {
      logout();
      router.push('/login');
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="p-6 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <Shield className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <h2 className="text-lg font-bold">관리자</h2>
                  <p className="text-xs text-muted-foreground">Admin Panel</p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={toggleSidebar}
                className="lg:hidden"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Navigation Menu */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {menuItems.map((item) => (
              <div key={item.id}>
                <div className="relative">
                  {item.children ? (
                    <Button
                      variant="ghost"
                      className={`w-full justify-between text-left ${isActiveMenu(item.href) ? 'bg-primary/10 text-primary' : 'hover:bg-muted/50'}`}
                      onClick={() => toggleMenu(item.id)}
                    >
                      <div className="flex items-center space-x-3">
                        {item.icon}
                        <span>{item.label}</span>
                      </div>
                      <ChevronRight className={`w-4 h-4 transition-transform ${expandedMenus.includes(item.id) ? 'rotate-90' : ''}`} />
                    </Button>
                  ) : (
                    <Link href={item.href}>
                      <Button
                        variant="ghost"
                        className={`w-full justify-start ${isActiveMenu(item.href) ? 'bg-primary/10 text-primary' : 'hover:bg-muted/50'}`}
                        onClick={() => setSidebarOpen(false)}
                      >
                        <div className="flex items-center space-x-3">
                          {item.icon}
                          <span>{item.label}</span>
                        </div>
                        {item.badge && (
                          <Badge variant="secondary" className="ml-auto text-xs">
                            {item.badge}
                          </Badge>
                        )}
                      </Button>
                    </Link>
                  )}
                </div>
                
                {/* Submenu */}
                {item.children && expandedMenus.includes(item.id) && (
                  <div className="ml-4 mt-2 space-y-1">
                    {item.children.map((child) => (
                      <Link key={child.id} href={child.href}>
                        <Button
                          variant="ghost"
                          size="sm"
                          className={`w-full justify-start text-sm ${isActiveMenu(child.href) ? 'bg-primary/10 text-primary' : 'hover:bg-muted/50'}`}
                          onClick={() => setSidebarOpen(false)}
                        >
                          <div className="flex items-center space-x-2">
                            {child.icon}
                            <span>{child.label}</span>
                          </div>
                          {child.badge && (
                            <Badge variant="secondary" className="ml-auto text-xs">
                              {child.badge}
                            </Badge>
                          )}
                        </Button>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* User Info */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-primary" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{user?.username}</p>
                  <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                </div>
              </div>
              <Badge variant="secondary" className="text-xs">
                {user?.roles?.[0] || 'ADMIN'}
              </Badge>
            </div>
            
            <div className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
                onClick={() => router.push('/')}
              >
                <Home className="w-4 h-4 mr-2" />
                메인으로
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start text-destructive border-destructive/50 hover:bg-destructive/10"
                onClick={handleLogout}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                로그아웃
              </Button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:ml-64">
        {/* Top Header */}
        <header className="sticky top-0 z-40 bg-card border-b border-border">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleSidebar}
                className="lg:hidden"
              >
                <Menu className="w-5 h-5" />
              </Button>
              
              <div>
                <h1 className="text-xl font-bold">{title}</h1>
                {subtitle && (
                  <p className="text-sm text-muted-foreground">{subtitle}</p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {actions}
              <ThemeToggle />
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={toggleSidebar}
        />
      )}
    </div>
  );
}