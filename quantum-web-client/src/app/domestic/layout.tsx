'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  Calendar,
  TrendingUp,
  Building2,
  DollarSign,
  Newspaper,
  Clock
} from 'lucide-react';

interface DomesticLayoutProps {
  children: ReactNode;
}

// 국내 시장 네비게이션 메뉴
const domesticNavItems = [
  {
    href: '/domestic/calendar',
    label: '달력',
    icon: Calendar,
    description: 'KIS 휴장일 정보'
  },
  {
    href: '/domestic/charts', 
    label: '차트',
    icon: TrendingUp,
    description: '실시간 차트'
  },
  {
    href: '/domestic/stocks',
    label: '종목',
    icon: Building2, 
    description: '종목 정보'
  },
  {
    href: '/domestic/trading',
    label: '거래',
    icon: DollarSign,
    description: '주식 거래'
  },
  {
    href: '/domestic/news',
    label: '뉴스', 
    icon: Newspaper,
    description: '시장 뉴스'
  }
];

function DomesticNavigation() {
  const pathname = usePathname();
  
  return (
    <nav className="w-64 bg-card border-r border-border min-h-screen">
      <div className="p-6">
        {/* 국내 시장 헤더 */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <h2 className="text-lg font-bold text-foreground">국내 시장</h2>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>09:00 - 15:30 (KST)</span>
          </div>
        </div>

        {/* 네비게이션 메뉴 */}
        <div className="space-y-2">
          {domesticNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-3 rounded-lg transition-all duration-200 group",
                  pathname === item.href 
                    ? "bg-primary/10 border border-primary/20 shadow-sm text-primary" 
                    : "hover:bg-muted/50 hover:shadow-sm"
                )}
              >
                <Icon className={cn(
                  "h-5 w-5 transition-colors",
                  pathname === item.href 
                    ? "text-primary" 
                    : "text-muted-foreground group-hover:text-foreground"
                )} />
                <div className="flex-1">
                  <div className={cn(
                    "font-medium",
                    pathname === item.href 
                      ? "text-primary" 
                      : "text-foreground"
                  )}>{item.label}</div>
                  <div className="text-xs text-muted-foreground">{item.description}</div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

    </nav>
  );
}

export default function DomesticLayout({ children }: DomesticLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <DomesticNavigation />
        
        {/* 메인 컨텐츠 - 달력용 넓은 공간 */}
        <main className="flex-1 p-4">
          <div className="w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}