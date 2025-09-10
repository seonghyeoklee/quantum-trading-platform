'use client';

import { 
  Clock,
  Activity
} from 'lucide-react';

const marketStats = [
  { label: 'KOSPI', value: '2,450.23', change: '+12.45', changePercent: '+0.51%', isPositive: true },
  { label: 'KOSDAQ', value: '845.67', change: '-3.21', changePercent: '-0.38%', isPositive: false },
  { label: 'KRX', value: '1,234.56', change: '+8.90', changePercent: '+0.73%', isPositive: true },
];

export default function DomesticMainPage() {
  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-foreground mb-2">
          국내 시장 대시보드
        </h1>
        <p className="text-muted-foreground">
          한국 주식시장의 종합적인 정보와 실시간 데이터를 한눈에 확인하세요.
        </p>
      </div>

      {/* 시장 지수 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {marketStats.map((stat) => (
          <div key={stat.label} className="bg-card rounded-xl border border-border p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-muted-foreground">{stat.label}</h3>
              <Activity className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <div className="text-2xl font-bold text-foreground">{stat.value}</div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium ${
                  stat.isPositive ? 'text-green-600' : 'text-red-600'
                }`}>
                  {stat.change}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  stat.isPositive 
                    ? 'bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-400' 
                    : 'bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400'
                }`}>
                  {stat.changePercent}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 시장 상태 카드 */}
      <div className="bg-card rounded-xl border border-border p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/10 rounded-xl">
              <Clock className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-1">
                시장 운영 상태
              </h3>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>평일 09:00 - 15:30 (KST)</span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-green-600 font-medium">정규장 운영중</span>
            </div>
            <div className="text-xs text-muted-foreground">
              {new Date().toLocaleString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}