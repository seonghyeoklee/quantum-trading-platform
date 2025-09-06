'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { 
  Calendar,
  TrendingUp, 
  Building2,
  Clock,
  ArrowRight
} from 'lucide-react';

const quickLinks = [
  {
    href: '/domestic/calendar',
    title: '휴장일 달력',
    description: 'KIS API 기반 영업일 정보',
    icon: Calendar,
    color: 'bg-blue-50 text-blue-600 border-blue-200'
  },
  {
    href: '/domestic/charts',
    title: '실시간 차트', 
    description: '국내 주식 차트 분석',
    icon: TrendingUp,
    color: 'bg-green-50 text-green-600 border-green-200'
  },
  {
    href: '/domestic/stocks',
    title: '종목 정보',
    description: '종목별 상세 데이터',
    icon: Building2,
    color: 'bg-purple-50 text-purple-600 border-purple-200'
  }
];

export default function DomesticMainPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const loadingDuration = 900; // 0.9초
    const updateInterval = 50; // 50ms마다 업데이트
    const totalSteps = loadingDuration / updateInterval;

    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + (100 / totalSteps);
        if (newProgress >= 100) {
          clearInterval(interval);
          setTimeout(() => setIsLoading(false), 100);
          return 100;
        }
        return newProgress;
      });
    }, updateInterval);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center">
        <div className="text-center space-y-6">
          {/* 아이콘과 그라데이션 */}
          <div className="relative">
            <div className="w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-xl">
              <Building2 className="w-10 h-10 text-white animate-pulse" />
            </div>
            <div className="absolute inset-0 w-20 h-20 mx-auto bg-gradient-to-br from-blue-500/20 to-blue-600/20 rounded-2xl animate-ping" />
          </div>
          
          {/* 로딩 텍스트 */}
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-gray-900">
              국내 주식 데이터를 불러오는 중...
            </h2>
            <p className="text-sm text-gray-500">
              한국 증권시장 실시간 정보 연결 중
            </p>
          </div>

          {/* 프로그레스 바 */}
          <div className="w-64 mx-auto">
            <div className="bg-gray-200 rounded-full h-2 overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-75 ease-out rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="text-xs text-gray-400 mt-2 text-center">
              {Math.round(progress)}%
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          국내 시장
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          한국 주식시장의 종합적인 정보와 실시간 데이터를 제공합니다.
        </p>
      </div>

      {/* 시장 상태 카드 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              시장 운영 시간
            </h2>
            <div className="flex items-center gap-2 text-gray-600">
              <Clock className="h-5 w-5" />
              <span>평일 09:00 - 15:30 (KST)</span>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-green-600 font-medium">정규장 운영중</span>
            </div>
            <div className="text-sm text-gray-500">
              {new Date().toLocaleString('ko-KR')}
            </div>
          </div>
        </div>
      </div>

      {/* 빠른 링크 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {quickLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Link
              key={link.href}
              href={link.href}
              className="group bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg border ${link.color}`}>
                  <Icon className="h-6 w-6" />
                </div>
                <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-gray-600 transition-colors" />
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                {link.title}
              </h3>
              <p className="text-gray-600 text-sm">
                {link.description}
              </p>
            </Link>
          );
        })}
      </div>

      {/* 최근 업데이트 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          최근 업데이트
        </h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
            <Calendar className="h-5 w-5 text-blue-500 mt-0.5" />
            <div>
              <div className="font-medium text-gray-900">KIS 휴장일 달력</div>
              <div className="text-sm text-gray-600">
                한국투자증권 API 연동으로 실시간 휴장일 정보 제공
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}