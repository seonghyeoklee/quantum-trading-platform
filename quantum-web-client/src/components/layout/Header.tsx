'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
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
  AlertCircle,
  ChevronDown,
  Calendar,
  Building2,
  DollarSign,
  Newspaper,
  Brain
} from "lucide-react";

interface HeaderProps {
  className?: string;
}

export default function Header({ className }: HeaderProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { currentMarket } = useMarket();
  const { hasKISAccount, isKISSetupRequired, forceKISSetup } = useAuth();

  // 현재 페이지 확인 - 새로운 구조
  const isHomePage = pathname === '/';
  const isDomesticPage = pathname === '/domestic' || pathname.startsWith('/domestic/');
  const isOverseasPage = pathname === '/overseas' || pathname.startsWith('/overseas/');
  const isStocksPage = pathname === '/stocks' || pathname.startsWith('/stocks/');
  const isProfilePage = pathname === '/profile';
  const isSettingsPage = pathname === '/settings';
  const isDinoTestPage = pathname === '/domestic/dino-tests' || pathname.startsWith('/domestic/dino-tests/');

  // ESC 키로 모바일 메뉴 닫기
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMobileMenuOpen(false);
      }
    };

    if (mobileMenuOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // 스크롤 방지
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [mobileMenuOpen]);

  return (
    <header className={`border-b border-border bg-card/95 backdrop-blur-lg sticky top-0 z-40 ${className || ''}`}>
      {/* 헤더 메인 영역 */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between w-full">
          {/* 좌측: 로고 및 주요 네비게이션 */}
          <div className="flex items-center space-x-8">
            {/* 모바일 메뉴 버튼 */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden hover-scale click-scale"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
            
            {/* 로고 - 더 세련된 디자인 */}
            <Link 
              href="/" 
              className="flex items-center space-x-3 cursor-pointer group"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary via-primary to-primary/90 rounded-lg flex items-center justify-center shadow-sm group-hover:shadow-md transition-all duration-200">
                <BarChart3 className="w-4 h-4 text-white" />
              </div>
              <div className="hidden sm:block">
                <div className="font-semibold text-lg text-foreground">
                  Quantum Trading
                </div>
              </div>
            </Link>
            
            {/* 깔끔한 네비게이션 메뉴 */}
            <nav className="hidden lg:flex items-center space-x-1">
              <Link 
                href="/" 
                className={`px-4 py-2 text-sm font-medium transition-all duration-200 rounded-lg ${
                  isHomePage 
                    ? 'text-primary bg-primary/10' 
                    : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
                }`}
              >
                홈
              </Link>
              
              {/* 국내시장 드롭다운 */}
              <div className="relative group">
                <Link 
                  href="/domestic" 
                  className={`flex items-center gap-1 px-4 py-2 text-sm font-medium transition-all duration-200 rounded-lg ${
                    isDomesticPage 
                      ? 'text-primary bg-primary/10' 
                      : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
                  }`}
                >
                  국내시장
                  <ChevronDown className="w-3 h-3 transition-transform group-hover:rotate-180" />
                </Link>
                
                {/* 드롭다운 메뉴 */}
                <div className="absolute top-full left-0 mt-1 w-48 bg-card border border-border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-2">
                    <Link 
                      href="/domestic"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Home className="w-4 h-4" />
                      대시보드
                    </Link>
                    <Link 
                      href="/domestic/calendar"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Calendar className="w-4 h-4" />
                      달력
                    </Link>
                    <Link 
                      href="/domestic/charts"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <TrendingUp className="w-4 h-4" />
                      차트
                    </Link>
                    <Link 
                      href="/domestic/stocks"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Building2 className="w-4 h-4" />
                      종목 목록
                    </Link>
                    <Link 
                      href="/domestic/trading"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <DollarSign className="w-4 h-4" />
                      거래
                    </Link>
                    <Link 
                      href="/domestic/news"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Newspaper className="w-4 h-4" />
                      뉴스
                    </Link>
                    
                    {/* 분석 섹션 구분선 */}
                    <div className="mx-4 my-2 border-t border-border"></div>
                    <div className="px-4 py-1">
                      <span className="text-xs text-muted-foreground font-medium">분석 도구</span>
                    </div>
                    
                    <Link 
                      href="/domestic/dino-tests"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Brain className="w-4 h-4" />
                      DINO 테스트
                    </Link>
                  </div>
                </div>
              </div>
              
              {/* 해외시장 드롭다운 */}
              <div className="relative group">
                <Link 
                  href="/overseas" 
                  className={`flex items-center gap-1 px-4 py-2 text-sm font-medium transition-all duration-200 rounded-lg ${
                    isOverseasPage 
                      ? 'text-primary bg-primary/10' 
                      : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
                  }`}
                >
                  해외시장
                  <ChevronDown className="w-3 h-3 transition-transform group-hover:rotate-180" />
                </Link>
                
                {/* 드롭다운 메뉴 */}
                <div className="absolute top-full left-0 mt-1 w-48 bg-card border border-border rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-2">
                    <Link 
                      href="/overseas"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Home className="w-4 h-4" />
                      대시보드
                    </Link>
                    <Link 
                      href="/overseas/stocks"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <Building2 className="w-4 h-4" />
                      종목 목록
                    </Link>
                    <Link 
                      href="/overseas/trading"
                      className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                    >
                      <DollarSign className="w-4 h-4" />
                      거래
                    </Link>
                  </div>
                </div>
              </div>

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

          {/* 우측: 액션 버튼들 */}
          <div className="flex items-center space-x-3">
            {/* KIS 설정 상태 표시 */}
            {isKISSetupRequired && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={forceKISSetup}
                className="hidden sm:flex items-center space-x-2 text-orange-600 border-orange-200 hover:bg-orange-50 transition-colors"
              >
                <AlertCircle className="w-4 h-4" />
                <span className="text-xs font-medium">KIS 설정 필요</span>
              </Button>
            )}
            
            {!hasKISAccount && !isKISSetupRequired && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={forceKISSetup}
                className="hidden sm:flex items-center space-x-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Settings className="w-4 h-4" />
                <span className="text-xs font-medium">KIS 연결</span>
              </Button>
            )}

            {/* Search - Desktop */}
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input 
                type="text" 
                placeholder="종목 검색..." 
                className="pl-10 pr-4 py-2 w-56 text-sm border border-input rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary transition-all duration-150"
              />
            </div>
            
            {/* Search - Mobile Icon Only */}
            <Button 
              variant="ghost" 
              size="sm" 
              className="md:hidden"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Search className="w-5 h-5" />
            </Button>
            
            {/* Notifications */}
            <Button variant="ghost" size="sm" className="relative">
              <Bell className="w-4 h-4" />
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
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
            {isDomesticPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">국내 시장</span>
              </>
            )}
            {isOverseasPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">해외 시장</span>
              </>
            )}
            {isProfilePage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">프로필 설정</span>
              </>
            )}
            {isStocksPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">종목 목록</span>
              </>
            )}
            {isSettingsPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">시스템 설정</span>
              </>
            )}
            {isDinoTestPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">DINO 분석</span>
              </>
            )}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu - 토글 가능한 드롭다운 메뉴 */}
      {mobileMenuOpen && (
        <>
          {/* 배경 오버레이 */}
          <div 
            className="fixed inset-0 bg-black/20 z-50 md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
          
          {/* 메뉴 컨텐츠 */}
          <div className="fixed top-0 left-0 right-0 z-[60] md:hidden bg-white border-b border-border shadow-xl animate-in slide-in-from-top duration-200">
            <div className="px-4 py-3 space-y-2 max-h-screen overflow-y-auto">
              {/* 메뉴 헤더 */}
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
                    <BarChart3 className="w-4 h-4 text-primary-foreground" />
                  </div>
                  <span className="font-bold text-lg">Quantum Trading</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2"
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>
              
              {/* 모바일 검색창 */}
              <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="종목, 지표, 아이디어 검색..." 
                  className="pl-10 pr-4 py-2 w-full text-sm border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              
              {/* 모바일 네비게이션 링크 */}
              <div className="space-y-1">
                <Link 
                  href="/" 
                  className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                    isHomePage 
                      ? 'bg-primary/10 text-primary font-medium' 
                      : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
                  }`}
                  onClick={(e) => setMobileMenuOpen(false)}
                >
                  <Home className="w-5 h-5" />
                  <span>홈</span>
                </Link>
                
                <Link 
                  href="/domestic" 
                  className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                    isDomesticPage 
                      ? 'bg-primary/10 text-primary font-medium' 
                      : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
                  }`}
                  onClick={(e) => setMobileMenuOpen(false)}
                >
                  <Building className="w-5 h-5" />
                  <span>국내시장</span>
                </Link>
                
                <Link 
                  href="/overseas" 
                  className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                    isOverseasPage 
                      ? 'bg-primary/10 text-primary font-medium' 
                      : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
                  }`}
                  onClick={(e) => setMobileMenuOpen(false)}
                >
                  <Globe className="w-5 h-5" />
                  <span>해외시장</span>
                </Link>

                {/* KIS 설정 링크 (모바일) */}
                {(isKISSetupRequired || !hasKISAccount) && (
                  <button 
                    onClick={() => {
                      forceKISSetup();
                      setMobileMenuOpen(false);
                    }}
                    className="flex items-center space-x-3 p-3 rounded-lg w-full text-left transition-colors hover:bg-gray-50"
                  >
                    <Settings className="w-5 h-5" />
                    <span>KIS 설정</span>
                    {isKISSetupRequired && (
                      <div className="ml-auto">
                        <AlertCircle className="w-4 h-4 text-orange-600" />
                      </div>
                    )}
                  </button>
                )}
              </div>
              
              {/* 모바일 빠른 액세스 */}
              <div className="mt-4 pt-4 border-t border-border">
                <div className="text-xs text-muted-foreground mb-2">빠른 액세스</div>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="justify-start"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Bell className="w-4 h-4 mr-2" />
                    알림
                  </Button>
                  <Button
                    variant="ghost" 
                    size="sm"
                    className="justify-start"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    설정
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Mobile Bottom Navigation - 일관성 있는 색상 시스템 */}
      <div className="md:hidden px-4 py-2 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between">
          <div className="flex space-x-2 overflow-x-auto">
            <Link 
              href="/" 
              className={`flex items-center space-x-1 px-3 py-1 rounded-md whitespace-nowrap transition-colors ${
                isHomePage 
                  ? 'bg-primary/10 text-primary' 
                  : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
              }`}
            >
              <Home className="w-3 h-3" />
              <span className="text-xs font-medium">홈</span>
            </Link>
            <Link 
              href="/domestic" 
              className={`flex items-center space-x-1 px-3 py-1 rounded-md whitespace-nowrap transition-colors ${
                isDomesticPage 
                  ? 'bg-primary/10 text-primary' 
                  : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
              }`}
            >
              <Building className="w-3 h-3" />
              <span className="text-xs font-medium">국내시장</span>
            </Link>
            <Link 
              href="/overseas" 
              className={`flex items-center space-x-1 px-3 py-1 rounded-md whitespace-nowrap transition-colors ${
                isOverseasPage 
                  ? 'bg-primary/10 text-primary' 
                  : 'text-muted-foreground hover:text-primary hover:bg-primary/5'
              }`}
            >
              <Globe className="w-3 h-3" />
              <span className="text-xs font-medium">해외시장</span>
            </Link>
          </div>
          
          {/* Mobile Search Button */}
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Search className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}