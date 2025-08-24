'use client';

import { useAuth } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import UserMenu from "@/components/auth/UserMenu";
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"
import ChartContainer from "@/components/chart/ChartContainer"
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3,
  Search,
  Bell,
  Globe,
  ChevronDown
} from "lucide-react"

function TradingDashboard() {

  return (
    <div className="min-h-screen bg-background">
      {/* TradingView-style Navigation Header */}
      <header className="border-b border-border bg-card sticky top-0 z-50">
        {/* Top Navigation */}
        <div className="px-4 py-2 border-b border-border/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-primary rounded flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="font-bold text-lg">Quantum Trading</span>
              </div>
              
              {/* Navigation Menu */}
              <nav className="hidden md:flex items-center space-x-6">
                <div className="flex items-center space-x-1 cursor-pointer hover:text-primary">
                  <span className="text-sm font-medium">차트</span>
                  <ChevronDown className="w-3 h-3" />
                </div>
                <div className="flex items-center space-x-1 cursor-pointer hover:text-primary">
                  <span className="text-sm font-medium">아이디어</span>
                  <ChevronDown className="w-3 h-3" />
                </div>
                <div className="flex items-center space-x-1 cursor-pointer hover:text-primary">
                  <span className="text-sm font-medium">종목</span>
                  <ChevronDown className="w-3 h-3" />
                </div>
                <div className="flex items-center space-x-1 cursor-pointer hover:text-primary">
                  <span className="text-sm font-medium">브로커</span>
                  <ChevronDown className="w-3 h-3" />
                </div>
                <div className="flex items-center space-x-1 cursor-pointer hover:text-primary">
                  <span className="text-sm font-medium">더보기</span>
                  <ChevronDown className="w-3 h-3" />
                </div>
              </nav>
            </div>

            <div className="flex items-center space-x-3">
              {/* Search */}
              <div className="relative hidden md:block">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="종목, 지표, 아이디어 검색..." 
                  className="pl-10 pr-4 py-2 w-64 text-sm border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
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
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-muted-foreground">KOSPI</span>
              <span className="font-medium">2,647.82</span>
              <span className="text-bull flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                +1.23%
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-muted-foreground">KOSDAQ</span>
              <span className="font-medium">742.15</span>
              <span className="text-bear flex items-center">
                <TrendingDown className="w-3 h-3 mr-1" />
                -0.84%
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-muted-foreground">USD/KRW</span>
              <span className="font-medium">1,347.50</span>
              <span className="text-bull flex items-center">
                <TrendingUp className="w-3 h-3 mr-1" />
                +0.32%
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-muted-foreground" />
              <span className="text-muted-foreground text-xs">실시간 데이터</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - TradingView Style */}
      <main className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Watchlist */}
        <div className="w-80 border-r border-border bg-sidebar flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-sm mb-3">워치리스트</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <span className="text-xs font-medium text-primary">S</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium">삼성전자</div>
                    <div className="text-xs text-muted-foreground">005930</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">71,400</div>
                  <div className="text-xs text-bear">-1.2%</div>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <span className="text-xs font-medium text-green-700">N</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium">NAVER</div>
                    <div className="text-xs text-muted-foreground">035420</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">198,500</div>
                  <div className="text-xs text-bull">+2.1%</div>
                </div>
              </div>
              
              <div className="flex items-center justify-between p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-700">K</span>
                  </div>
                  <div>
                    <div className="text-sm font-medium">카카오</div>
                    <div className="text-xs text-muted-foreground">035720</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">45,250</div>
                  <div className="text-xs text-bull">+0.8%</div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Portfolio Section */}
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-sm mb-3">포트폴리오</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">총 자산</span>
                <span className="text-sm font-medium">₩12,345,678</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">일 수익</span>
                <span className="text-sm font-medium text-bull">+₩234,567</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">수익률</span>
                <span className="text-sm font-medium text-bull">+1.9%</span>
              </div>
            </div>
          </div>
          
          {/* Quick Actions */}
          <div className="p-4">
            <h3 className="font-semibold text-sm mb-3">빠른 거래</h3>
            <div className="space-y-2">
              <Button size="sm" className="w-full btn-buy">매수 주문</Button>
              <Button size="sm" className="w-full btn-sell">매도 주문</Button>
              <Button variant="outline" size="sm" className="w-full">주문 내역</Button>
            </div>
          </div>
        </div>

        {/* Central Chart Area */}
        <div className="flex-1 flex flex-col bg-background">
          <ChartContainer className="flex-1" />
        </div>

        {/* Right Sidebar - Market Data */}
        <div className="w-80 border-l border-border bg-sidebar flex flex-col">
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-sm mb-3">시장 동향</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm">상승</span>
                <span className="text-sm font-medium text-bull">1,247</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">하락</span>
                <span className="text-sm font-medium text-bear">854</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">보합</span>
                <span className="text-sm font-medium text-muted-foreground">23</span>
              </div>
            </div>
          </div>
          
          <div className="p-4 border-b border-border">
            <h3 className="font-semibold text-sm mb-3">인기 종목</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div>
                  <div className="text-sm font-medium">테슬라</div>
                  <div className="text-xs text-muted-foreground">TSLA</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">$248.42</div>
                  <div className="text-xs text-bull">+3.2%</div>
                </div>
              </div>
              
              <div className="flex justify-between items-center p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div>
                  <div className="text-sm font-medium">애플</div>
                  <div className="text-xs text-muted-foreground">AAPL</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">$189.84</div>
                  <div className="text-xs text-bear">-1.1%</div>
                </div>
              </div>
              
              <div className="flex justify-between items-center p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div>
                  <div className="text-sm font-medium">마이크로소프트</div>
                  <div className="text-xs text-muted-foreground">MSFT</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">$378.85</div>
                  <div className="text-xs text-bull">+0.8%</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="p-4">
            <h3 className="font-semibold text-sm mb-3">시장 뉴스</h3>
            <div className="space-y-3">
              <div className="p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div className="text-sm font-medium mb-1">금리 인상 기대 증시</div>
                <div className="text-xs text-muted-foreground">15분 전</div>
              </div>
              <div className="p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div className="text-sm font-medium mb-1">삼성전자 실적 발표</div>
                <div className="text-xs text-muted-foreground">1시간 전</div>
              </div>
              <div className="p-2 rounded hover:bg-muted/50 cursor-pointer">
                <div className="text-sm font-medium mb-1">코스피 상승 마감</div>
                <div className="text-xs text-muted-foreground">2시간 전</div>
              </div>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}

export default function ProtectedTradingDashboard() {
  return (
    <ProtectedRoute>
      <TradingDashboard />
    </ProtectedRoute>
  );
}
