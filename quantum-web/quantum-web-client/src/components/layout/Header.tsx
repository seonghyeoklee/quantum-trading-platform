'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import UserMenu from "@/components/auth/UserMenu";
import { CompactTradingModeIndicator } from "@/components/layout/TradingModeIndicator";
import TradingModeToggle from "@/components/layout/TradingModeToggle";
import { 
  BarChart3, 
  Search,
  Bell,
  Globe,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  Home,
  Building,
  BookOpen,
  Bot,
  Activity,
  Menu,
  X
} from "lucide-react";

interface HeaderProps {
  className?: string;
}

export default function Header({ className }: HeaderProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // 현재 페이지 확인
  const isHomePage = pathname === '/';
  const isStockPage = pathname === '/stock';
  const isGlossaryPage = pathname === '/glossary';
  const isStrategiesPage = pathname === '/strategies' || pathname?.startsWith('/strategies/');
  const isTradingTestPage = pathname === '/trading-test';
  const isAutoTradingPage = pathname === '/auto-trading';
  const isKiwoomAccountPage = pathname === '/kiwoom-account';

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
            
            {/* Navigation Menu */}
            <nav className="hidden md:flex items-center space-x-6">
              <a 
                href="/" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isHomePage ? 'text-primary font-medium' : ''
                }`}
              >
                <Home className="w-4 h-4" />
                <span className="text-sm">차트</span>
                <ChevronDown className="w-3 h-3" />
              </a>
              
              
              <a 
                href="/stock" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isStockPage ? 'text-primary font-medium' : ''
                }`}
              >
                <Building className="w-4 h-4" />
                <span className="text-sm">종목</span>
                <ChevronDown className="w-3 h-3" />
              </a>
              
              <a 
                href="/strategies" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isStrategiesPage ? 'text-primary font-medium' : ''
                }`}
              >
                <Bot className="w-4 h-4" />
                <span className="text-sm">전략</span>
                <ChevronDown className="w-3 h-3" />
              </a>

              <a 
                href="/auto-trading" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isAutoTradingPage ? 'text-primary font-medium' : ''
                }`}
              >
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">자동매매</span>
              </a>

              <a 
                href="/trading-test" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isTradingTestPage ? 'text-primary font-medium' : ''
                }`}
              >
                <Activity className="w-4 h-4" />
                <span className="text-sm">통합테스트</span>
              </a>
              
              <a 
                href="/kiwoom-account" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isKiwoomAccountPage ? 'text-primary font-medium' : ''
                }`}
              >
                <Building className="w-4 h-4" />
                <span className="text-sm">키움설정</span>
              </a>
              
              <div className="flex items-center space-x-1 cursor-pointer hover:text-primary">
                <span className="text-sm font-medium">더보기</span>
                <ChevronDown className="w-3 h-3" />
              </div>

              {/* 용어 사전 링크 */}
              <a 
                href="/glossary" 
                className={`flex items-center space-x-1 cursor-pointer hover:text-primary transition-colors ${
                  isGlossaryPage ? 'text-primary font-medium' : ''
                }`}
              >
                <BookOpen className="w-4 h-4" />
                <span className="text-sm">용어사전</span>
              </a>
            </nav>
          </div>

          <div className="flex items-center space-x-2 sm:space-x-3">
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
          
          {/* Trading Mode & Current Page Indicator */}
          <div className="flex items-center space-x-4">
            <TradingModeToggle />
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              <Globe className="w-4 h-4" />
              <span>실시간 데이터</span>
            {isStockPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">종목 정보</span>
              </>
            )}
            {isGlossaryPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">용어 사전</span>
              </>
            )}
            {isStrategiesPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">자동매매 전략</span>
              </>
            )}
            {isAutoTradingPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">자동매매</span>
              </>
            )}
            {isTradingTestPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">통합 테스트</span>
              </>
            )}
            {isKiwoomAccountPage && (
              <>
                <span>•</span>
                <span className="text-primary font-medium">키움증권 설정</span>
              </>
            )}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation - 작은 화면에서만 표시 */}
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
              href="/stock" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isStockPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <Building className="w-3 h-3" />
              <span className="text-xs">종목</span>
            </a>
            <a 
              href="/strategies" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isStrategiesPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <Bot className="w-3 h-3" />
              <span className="text-xs">전략</span>
            </a>
            <a 
              href="/auto-trading" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isAutoTradingPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <TrendingUp className="w-3 h-3" />
              <span className="text-xs">자동매매</span>
            </a>
            <a 
              href="/glossary" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isGlossaryPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <BookOpen className="w-3 h-3" />
              <span className="text-xs">용어사전</span>
            </a>
            <a 
              href="/trading-test" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isTradingTestPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <Activity className="w-3 h-3" />
              <span className="text-xs">통합테스트</span>
            </a>
            <a 
              href="/kiwoom-account" 
              className={`flex items-center space-x-1 px-3 py-1 rounded whitespace-nowrap ${
                isKiwoomAccountPage ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
              }`}
            >
              <Building className="w-3 h-3" />
              <span className="text-xs">키움설정</span>
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