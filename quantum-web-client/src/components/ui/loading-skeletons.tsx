'use client';

import { Skeleton } from "./skeleton";
import { Card, CardContent, CardHeader } from "./card";

// 개선된 시장 카드 스켈레톤
export function MarketCardSkeleton() {
  return (
    <Card className="relative overflow-hidden border animate-pulse">
      <div className="absolute inset-0 bg-gradient-to-br from-gray-50/30 via-white to-gray-50/20 dark:from-gray-950/10 dark:via-background dark:to-gray-950/5" />
      
      <CardHeader className="relative space-y-4 pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Skeleton className="w-14 h-14 rounded-xl" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-7 w-32" />
              <Skeleton className="h-4 w-40" />
            </div>
          </div>
          <Skeleton className="h-6 w-20 rounded-full" />
        </div>
      </CardHeader>
      
      <CardContent className="relative space-y-6">
        {/* 실시간 지수 스켈레톤 */}
        <div className="space-y-3">
          <Skeleton className="h-4 w-20" />
          
          {/* 지수 카드들 */}
          <div className="space-y-3">
            {[1, 2].map((index) => (
              <div key={index} className="bg-white/60 dark:bg-gray-800/30 rounded-lg p-4 border border-gray-100 dark:border-gray-700/50">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <Skeleton className="h-5 w-16" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <div className="text-right space-y-2">
                    <Skeleton className="h-6 w-20" />
                    <Skeleton className="h-4 w-16" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 거래시간 스켈레톤 */}
        <div className="bg-white/40 dark:bg-gray-800/20 rounded-lg p-3 border border-gray-100 dark:border-gray-700/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Skeleton className="w-8 h-8 rounded-lg" />
              <div className="space-y-2">
                <Skeleton className="h-3 w-12" />
                <Skeleton className="h-4 w-24" />
              </div>
            </div>
            <div className="text-right space-y-2">
              <Skeleton className="h-3 w-8" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
        </div>

        {/* 인기 종목 스켈레톤 */}
        <div className="space-y-3">
          <Skeleton className="h-4 w-24" />
          <div className="space-y-2">
            {[1, 2, 3].map((index) => (
              <div key={index} className="bg-white/40 dark:bg-gray-800/20 rounded-lg p-3 border border-gray-100 dark:border-gray-700/30">
                <div className="flex items-center justify-between">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-3 w-12" />
                  </div>
                  <div className="text-right space-y-2">
                    <Skeleton className="h-4 w-16" />
                    <Skeleton className="h-3 w-12" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA 버튼 스켈레톤 */}
        <Skeleton className="w-full h-12 rounded-md" />
      </CardContent>
    </Card>
  );
}

// 차트 스켈레톤
export function ChartSkeleton({ height = 400 }: { height?: number }) {
  return (
    <div className="w-full rounded-lg border border-border bg-card p-4">
      <div className="space-y-4">
        {/* 차트 헤더 */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-24" />
          </div>
          <div className="flex space-x-2">
            <Skeleton className="h-8 w-12" />
            <Skeleton className="h-8 w-12" />
            <Skeleton className="h-8 w-12" />
          </div>
        </div>
        
        {/* 차트 영역 */}
        <div className="relative">
          <Skeleton className="w-full rounded-lg" style={{ height: `${height}px` }} />
          
          {/* 차트 내부 요소들 */}
          <div className="absolute inset-4 space-y-4">
            {/* 가격 레이블들 */}
            <div className="flex justify-between">
              <Skeleton className="h-3 w-12" />
              <Skeleton className="h-3 w-16" />
            </div>
            
            {/* 차트 데이터 바들 */}
            <div className="flex items-end justify-between space-x-1 h-32">
              {Array.from({ length: 20 }).map((_, index) => (
                <Skeleton 
                  key={index} 
                  className="w-2" 
                  style={{ 
                    height: `${Math.random() * 80 + 20}%` 
                  }} 
                />
              ))}
            </div>
          </div>
        </div>

        {/* 차트 컨트롤 */}
        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            {['1D', '1W', '1M', '3M', '1Y'].map((period) => (
              <Skeleton key={period} className="h-8 w-8" />
            ))}
          </div>
          <div className="flex space-x-2">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-8 w-20" />
          </div>
        </div>
      </div>
    </div>
  );
}

// 주식 목록 스켈레톤
export function StockListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Skeleton className="w-10 h-10 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
            <div className="text-right space-y-2">
              <Skeleton className="h-5 w-16" />
              <Skeleton className="h-3 w-12" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// 뉴스 피드 스켈레톤
export function NewsFeedSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <div className="space-y-3">
            <div className="flex items-start space-x-3">
              <Skeleton className="w-12 h-12 rounded-lg flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <div className="flex items-center space-x-2">
                  <Skeleton className="h-3 w-16" />
                  <Skeleton className="h-3 w-12" />
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// 포트폴리오 스켈레톤
export function PortfolioSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-8 w-32" />
          </div>
          <Skeleton className="h-6 w-16" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 포트폴리오 차트 */}
        <Skeleton className="w-full h-40 rounded-lg" />
        
        {/* 자산 목록 */}
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Skeleton className="w-8 h-8 rounded-full" />
                <div className="space-y-1">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-3 w-12" />
                </div>
              </div>
              <div className="text-right space-y-1">
                <Skeleton className="h-4 w-12" />
                <Skeleton className="h-3 w-8" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// 테이블 스켈레톤
export function TableSkeleton({ 
  rows = 5, 
  columns = 4 
}: { 
  rows?: number; 
  columns?: number; 
}) {
  return (
    <div className="w-full">
      <div className="rounded-lg border border-border">
        {/* 테이블 헤더 */}
        <div className="border-b border-border bg-muted/50 p-4">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, index) => (
              <Skeleton key={index} className="h-4 w-20" />
            ))}
          </div>
        </div>
        
        {/* 테이블 로우들 */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="border-b border-border last:border-b-0 p-4">
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <Skeleton 
                  key={colIndex} 
                  className={`h-4 ${colIndex === 0 ? 'w-24' : 'w-16'}`}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// 대시보드 전체 스켈레톤
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* 헤더 스켈레톤 */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-10 w-32" />
      </div>

      {/* 메트릭 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Skeleton className="h-7 w-24" />
                <Skeleton className="h-3 w-32" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 차트와 리스트 영역 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartSkeleton />
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          <StockListSkeleton count={6} />
        </div>
      </div>
    </div>
  );
}

// 페이지 로딩 스켈레톤 (전체 화면)
export function PageLoadingSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* 페이지 헤더 */}
        <div className="text-center space-y-4">
          <Skeleton className="h-10 w-64 mx-auto" />
          <Skeleton className="h-5 w-96 mx-auto" />
        </div>

        {/* 메인 컨텐츠 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
          <MarketCardSkeleton />
          <MarketCardSkeleton />
        </div>

        {/* 기능 소개 섹션 */}
        <div className="mt-20 px-4">
          <div className="text-center mb-12 space-y-4">
            <Skeleton className="h-8 w-48 mx-auto" />
            <Skeleton className="h-5 w-80 mx-auto" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="bg-white/60 dark:bg-gray-800/30 rounded-2xl p-6 border border-gray-200 dark:border-gray-700/50">
                <div className="text-center space-y-4">
                  <Skeleton className="w-16 h-16 rounded-2xl mx-auto" />
                  <Skeleton className="h-6 w-32 mx-auto" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-4/5 mx-auto" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}