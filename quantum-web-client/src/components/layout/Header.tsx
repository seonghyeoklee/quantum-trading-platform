'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { useMarket } from '@/contexts/MarketContext';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import UserMenu from "@/components/auth/UserMenu";
import { KISEnvironmentToggle } from "@/components/kis/KISEnvironmentToggle";
import { MarketIndicator } from "@/components/market/MarketIndicator";
import { 
  BarChart3, 
  Search,
  Bell,
  Globe,
  TrendingUp,
  TrendingDown,
  Home,
  Building,
  Menu,
  X,
  Settings,
  AlertCircle
} from "lucide-react";

interface HeaderProps {
  className?: string;
}

export default function Header({ className }: HeaderProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { currentMarket } = useMarket();
  const { hasKISAccount, isKISSetupRequired, forceKISSetup } = useAuth();

  // 현재 페이지 확인 - MVP 1.0 핵심 페이지만
  const isHomePage = pathname === '/';
  const isDomesticStockPage = pathname === '/stock/domestic';
  const isOverseasStockPage = pathname === '/stock/overseas';
  const isAnyStockPage = isDomesticStockPage || isOverseasStockPage;
  const isProfilePage = pathname === '/profile';
  const isSettingsPage = pathname === '/settings';

  return (
    <header className={`border-b border-border bg-card sticky top-0 z-50 ${className || ''}`}>
      {/* Top Navigation */}
      <div className="px-4 py-2 border-b border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 md:space-x-6">
            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
            
            <a 
              href="/" 
              className="flex items-center space-x-2 cursor-pointer hover:opacity-80 hover:scale-105 transition-all duration-200 active:scale-95"
            >
              <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-bold text-sm sm:text-lg">Quantum Trading</span>
            </a>
            
            {/* Navigation Menu - MVP 1.0 핵심 메뉴만 */}
            <nav className="hidden md:flex items-center space-x-6">
              <a 
                href="/" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isHomePage ? 'text-primary font-medium' : ''
                }`}
              >
                <Home className="w-4 h-4" />
                <span className="text-sm">차트</span>
              </a>
              
              <a 
                href="/stock/domestic" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isDomesticStockPage ? 'text-primary font-medium' : ''
                }`}
              >
                <Building className="w-4 h-4" />
                <span className="text-sm">국내종목</span>
              </a>
              
              <a 
                href="/stock/overseas" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isOverseasStockPage ? 'text-primary font-medium' : ''
                }`}
              >
                <Globe className="w-4 h-4" />
                <span className="text-sm">해외종목</span>
              </a>

              {/* 향후 구현 예정 메뉴들 (주석 처리) */}
              {/* 
              <a 
                href="/strategies" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors`}
              >
                <Bot className="w-4 h-4" />
                <span className="text-sm">전략</span>
              </a>

              <a 
                href="/auto-trading" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors`}
              >
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">자동매매</span>
              </a>

              <a 
                href="/trading-test" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors`}
              >
                <Activity className="w-4 h-4" />
                <span className="text-sm">통합테스트</span>
              </a>
              
              <a 
                href="/kiwoom-account" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors`}
              >
                <Building className="w-4 h-4" />
                <span className="text-sm">키움설정</span>
              </a>

              <a 
                href="/glossary" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors`}
              >
                <BookOpen className="w-4 h-4" />
                <span className="text-sm">용어사전</span>
              </a>
              */}
            </nav>
          </div>

          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* KIS 설정 상태 표시 */}
            {isKISSetupRequired && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={forceKISSetup}
                className="hidden sm:flex items-center space-x-1 text-orange-600 border-orange-200 hover:bg-orange-50"
              >
                <AlertCircle className="w-4 h-4" />
                <span className="text-xs">KIS 설정 필요</span>
              </Button>
            )}
            
            {!hasKISAccount && !isKISSetupRequired && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={forceKISSetup}
                className="hidden sm:flex items-center space-x-1 text-muted-foreground hover:text-primary"
              >
                <Settings className="w-4 h-4" />
                <span className="text-xs">KIS 연결</span>
              </Button>
            )}

            {/* Search - Mobile Icon Only */}
            <Button variant="ghost" size="sm" className="md:hidden">
              <Search className="w-5 h-5" />
            </Button>
            
            {/* Search - Desktop */}
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input 
                type="text" 
                placeholder="종목, 지표, 아이디어 검색..." 
                className="pl-10 pr-4 py-2 w-48 lg:w-64 text-sm border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            
            {/* Notifications */}
            <Button variant="ghost" size="sm" className="relative">
              <Bell className="w-4 h-4" />
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-destructive rounded-full"></div>
            </Button>
            
            <ThemeToggle />
            
            {/* User Menu */}
            <div className="pl-3 border-l border-border">
              <UserMenu />
            </div>
          </div>
        </div>
      </div>
      
      {/* Market Summary Bar */}
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
          
          {/* Trading Mode & Market Indicators */}
          <div className="flex items-center space-x-4">
            {/* Market Indicator */}
            <MarketIndicator variant="compact" showStatus={hasKISAccount} />
            
            {/* KIS Environment */}
            <div className="flex items-center space-x-2">
              {hasKISAccount ? (
                <KISEnvironmentToggle variant="compact" showStatus={false} />
              ) : (
                <div className="flex items-center space-x-1 px-2 py-1 bg-orange-100 text-orange-600 text-xs rounded">
                  <AlertCircle className="w-3 h-3" />
                  <span>KIS 미연결</span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              <Globe className="w-4 h-4" />
              <span>{hasKISAccount ? '실시간 데이터' : '제한된 데이터'}</span>
            {isDomesticStockPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">국내 종목</span>
              </>
            )}
            {isOverseasStockPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">해외 종목</span>
              </>
            )}
            {isProfilePage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">프로필 설정</span>
              </>
            )}
            {isSettingsPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">시스템 설정</span>
              </>
            )}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation - MVP 1.0 핵심 메뉴만 */}
      <div className="md:hidden px-4 py-2 border-b border-border bg-muted/50">
        <div className="flex items-center justify-between">
          <div className="flex space-x-4 overflow-x-auto">
            <a 
              href="/" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isHomePage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <Home className="w-3 h-3" />
              <span className="text-xs">차트</span>
            </a>
            <a 
              href="/stock/domestic" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isDomesticStockPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <Building className="w-3 h-3" />
              <span className="text-xs">국내종목</span>
            </a>
            <a 
              href="/stock/overseas" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isOverseasStockPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <Globe className="w-3 h-3" />
              <span className="text-xs">해외종목</span>
            </a>
          </div>
          
          {/* Mobile Search Button */}
          <Button variant="ghost" size="sm">
            <Search className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}