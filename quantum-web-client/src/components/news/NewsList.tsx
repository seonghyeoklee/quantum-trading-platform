'use client';

import React, { useState } from 'react';
import { RefreshCw, AlertCircle, Newspaper, Filter, Search } from 'lucide-react';
import { NewsItem, NewsCategory } from '@/types/news';
import NewsCard from './NewsCard';
import { cn } from '@/lib/utils';

interface NewsListProps {
  news: NewsItem[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  className?: string;
  compact?: boolean;
  showFilters?: boolean;
  selectedCategory?: NewsCategory;
  onCategoryChange?: (category: NewsCategory) => void;
}

const CATEGORY_LABELS: Record<NewsCategory, string> = {
  general: '일반',
  financial: '금융',
  latest: '최신'
};

export default function NewsList({ 
  news, 
  isLoading = false, 
  error = null, 
  onRefresh,
  className,
  compact = false,
  showFilters = false,
  selectedCategory = 'general',
  onCategoryChange
}: NewsListProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // 검색 필터링
  const filteredNews = news.filter(item => {
    if (!searchQuery) return true;
    return item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
           item.description.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleCategoryClick = (category: NewsCategory) => {
    if (onCategoryChange) {
      onCategoryChange(category);
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Newspaper className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-foreground">
              관련 뉴스
            </h3>
            <p className="text-sm text-muted-foreground">
              {news.length}개 뉴스
            </p>
          </div>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className={cn(
              "p-2 rounded-lg transition-all duration-200",
              "hover:bg-primary/10 hover:text-primary",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              isLoading && "animate-spin"
            )}
            title="새로고침"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* 필터 및 검색 */}
      {showFilters && (
        <div className="space-y-3 mb-4">
          {/* 카테고리 필터 */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <div className="flex gap-1">
              {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => handleCategoryClick(key as NewsCategory)}
                  className={cn(
                    "px-3 py-1.5 text-sm rounded-lg transition-all duration-200",
                    selectedCategory === key
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* 검색 */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="뉴스 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                "w-full pl-10 pr-4 py-2 text-sm rounded-lg",
                "bg-muted border border-border",
                "focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary",
                "placeholder:text-muted-foreground"
              )}
            />
          </div>
        </div>
      )}

      {/* 뉴스 목록 */}
      <div className="flex-1 overflow-hidden">
        {/* 로딩 상태 */}
        {isLoading && (
          <div className="flex items-center justify-center h-32">
            <div className="flex items-center gap-2 text-muted-foreground">
              <RefreshCw className="w-5 h-5 animate-spin" />
              <span className="text-sm">뉴스를 불러오는 중...</span>
            </div>
          </div>
        )}

        {/* 에러 상태 */}
        {error && !isLoading && (
          <div className="flex items-center justify-center h-32">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        {/* 빈 상태 */}
        {!isLoading && !error && filteredNews.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
            <Newspaper className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">
              {searchQuery ? '검색 결과가 없습니다' : '뉴스가 없습니다'}
            </p>
          </div>
        )}

        {/* 뉴스 목록 */}
        {!isLoading && !error && filteredNews.length > 0 && (
          <div className={cn(
            "h-full overflow-y-auto space-y-2",
            !compact && "space-y-3"
          )}>
            {filteredNews.map((item, index) => (
              <NewsCard
                key={`${item.link}-${index}`}
                news={item}
                compact={compact}
                showDescription={!compact}
              />
            ))}
          </div>
        )}
      </div>

      {/* 푸터 정보 */}
      {!isLoading && !error && filteredNews.length > 0 && (
        <div className="mt-4 pt-3 border-t border-border">
          <p className="text-xs text-muted-foreground text-center">
            {searchQuery ? `"${searchQuery}" 검색 결과 ${filteredNews.length}개` : `총 ${filteredNews.length}개 뉴스`}
            <span className="ml-2">• 네이버 뉴스 제공</span>
          </p>
        </div>
      )}
    </div>
  );
}