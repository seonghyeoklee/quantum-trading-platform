'use client';

import React, { useState, useEffect } from 'react';
import { 
  Newspaper, 
  Search, 
  Filter, 
  RefreshCw, 
  TrendingUp,
  Building2,
  Calendar,
  Clock,
  ExternalLink,
  Loader2
} from 'lucide-react';
import { useNews, useTodayNews } from '@/hooks/useNews';
import { NewsCategory } from '@/types/news';
import NewsList from './NewsList';
import NewsCard from './NewsCard';
import { cn } from '@/lib/utils';

const CATEGORY_LABELS: Record<NewsCategory, string> = {
  general: '일반 뉴스',
  financial: '금융 뉴스',
  latest: '최신 뉴스'
};

const POPULAR_KEYWORDS = [
  '삼성전자', 'SK하이닉스', 'LG에너지솔루션', 'NAVER', '카카오',
  '현대차', 'POSCO홀딩스', '셀트리온', 'LG화학', 'KB금융'
];

export default function DomesticNewsClient() {
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory>('financial');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedKeyword, setSelectedKeyword] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  // 메인 뉴스 훅
  const {
    news: mainNews,
    isLoading: mainLoading,
    error: mainError,
    loadNews,
    loadLatestNews,
    loadFinancialNews,
    refresh: refreshMain,
    clearNews
  } = useNews();

  // 오늘 뉴스 훅 (사이드바용)
  const {
    news: todayNews,
    isLoading: todayLoading,
    error: todayError,
    refresh: refreshToday
  } = useTodayNews();

  // 카테고리 변경 핸들러
  const handleCategoryChange = async (category: NewsCategory) => {
    setSelectedCategory(category);
    clearNews();
    
    try {
      switch (category) {
        case 'financial':
          await loadFinancialNews('주식', 7);
          break;
        case 'latest':
          await loadLatestNews('경제', 20);
          break;
        default:
          await loadNews('경제 뉴스', { display: 20 });
      }
    } catch (error) {
      console.error('뉴스 로드 실패:', error);
    }
  };

  // 검색 핸들러
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    clearNews();
    try {
      await loadNews(searchQuery, { display: 20 });
    } catch (error) {
      console.error('뉴스 검색 실패:', error);
    }
  };

  // 키워드 클릭 핸들러
  const handleKeywordClick = async (keyword: string) => {
    setSelectedKeyword(keyword);
    setSearchQuery(keyword);
    clearNews();
    
    try {
      await loadFinancialNews(keyword, 7);
    } catch (error) {
      console.error('키워드 뉴스 로드 실패:', error);
    }
  };

  // 초기 로드
  useEffect(() => {
    handleCategoryChange('financial');
  }, []);

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-primary/10 rounded-xl">
                <Newspaper className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-foreground tracking-tight">
                  국내 뉴스
                </h1>
                <p className="text-muted-foreground mt-1">
                  실시간 금융 및 경제 뉴스
                </p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSearch(!showSearch)}
              className={cn(
                "p-2 rounded-lg transition-all duration-200",
                showSearch 
                  ? "bg-primary text-primary-foreground" 
                  : "bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground"
              )}
              title="검색"
            >
              <Search className="w-5 h-5" />
            </button>
            
            <button
              onClick={refreshMain}
              disabled={mainLoading}
              className={cn(
                "p-2 rounded-lg transition-all duration-200",
                "bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                mainLoading && "animate-spin"
              )}
              title="새로고침"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 검색 바 */}
        {showSearch && (
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="뉴스 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className={cn(
                  "w-full pl-10 pr-4 py-3 text-sm rounded-lg",
                  "bg-card border border-border",
                  "focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary",
                  "placeholder:text-muted-foreground"
                )}
              />
            </div>
            <button
              onClick={handleSearch}
              disabled={!searchQuery.trim() || mainLoading}
              className={cn(
                "px-4 py-3 bg-primary text-primary-foreground rounded-lg",
                "hover:bg-primary/90 transition-all duration-200",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              검색
            </button>
          </div>
        )}

        {/* 카테고리 필터 */}
        <div className="flex flex-wrap gap-2">
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
            <button
              key={key}
              onClick={() => handleCategoryChange(key as NewsCategory)}
              disabled={mainLoading}
              className={cn(
                "px-4 py-2 rounded-lg transition-all duration-200 text-sm font-medium",
                selectedCategory === key
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground",
                "disabled:opacity-50 disabled:cursor-not-allowed"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        {/* 인기 키워드 */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">인기 종목</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {POPULAR_KEYWORDS.map((keyword) => (
              <button
                key={keyword}
                onClick={() => handleKeywordClick(keyword)}
                disabled={mainLoading}
                className={cn(
                  "px-3 py-1.5 text-xs rounded-full transition-all duration-200",
                  selectedKeyword === keyword
                    ? "bg-primary/20 text-primary border border-primary/30"
                    : "bg-muted/50 hover:bg-muted text-muted-foreground hover:text-foreground border border-transparent",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {keyword}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="space-y-6">
        {/* 로딩 상태 */}
        {mainLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-3 text-muted-foreground">
              <Loader2 className="w-6 h-6 animate-spin" />
              <span>뉴스를 불러오는 중...</span>
            </div>
          </div>
        )}

        {/* 에러 상태 */}
        {mainError && !mainLoading && (
          <div className="text-center py-12">
            <div className="text-destructive mb-4">{mainError}</div>
            <button
              onClick={refreshMain}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* 뉴스 목록 */}
        {!mainLoading && !mainError && mainNews.length > 0 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-foreground">
                {CATEGORY_LABELS[selectedCategory]}
                {selectedKeyword && ` - ${selectedKeyword}`}
              </h2>
              <span className="text-sm text-muted-foreground">
                총 {mainNews.length}개 뉴스
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {mainNews.map((item, index) => (
                <NewsCard
                  key={`${item.link}-${index}`}
                  news={item}
                  compact={false}
                  showDescription={true}
                />
              ))}
            </div>
          </div>
        )}

        {/* 빈 상태 */}
        {!mainLoading && !mainError && mainNews.length === 0 && (
          <div className="text-center py-12">
            <Newspaper className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
            <p className="text-muted-foreground">뉴스가 없습니다</p>
          </div>
        )}
      </div>
    </div>
  );
}