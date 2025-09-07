'use client';

import React from 'react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { ExternalLink, Clock, Newspaper } from 'lucide-react';
import { NewsItem } from '@/types/news';
import { cn } from '@/lib/utils';

interface NewsCardProps {
  news: NewsItem;
  className?: string;
  compact?: boolean;
  showDescription?: boolean;
}

export default function NewsCard({ 
  news, 
  className, 
  compact = false, 
  showDescription = true 
}: NewsCardProps) {
  const handleClick = () => {
    // 원문 링크로 새 탭에서 열기
    if (news.original_link) {
      window.open(news.original_link, '_blank', 'noopener,noreferrer');
    } else if (news.link) {
      window.open(news.link, '_blank', 'noopener,noreferrer');
    }
  };

  // 발행 시간 파싱
  const getPublishDate = () => {
    try {
      // 네이버 API 날짜 형식: "Mon, 07 Jan 2025 12:00:00 +0900"
      const date = new Date(news.pub_date);
      if (isNaN(date.getTime())) {
        return news.pub_date;
      }
      return format(date, 'MM월 dd일 HH:mm', { locale: ko });
    } catch {
      return news.pub_date;
    }
  };

  if (compact) {
    return (
      <div
        className={cn(
          "group cursor-pointer p-3 rounded-lg transition-all duration-200",
          "hover:bg-accent/50 hover:shadow-sm border border-transparent hover:border-primary/20",
          "active:scale-[0.98] active:bg-accent/70",
          className
        )}
        onClick={handleClick}
      >
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            <div className="w-6 h-6 bg-primary/10 rounded-md flex items-center justify-center group-hover:bg-primary/20 transition-colors">
              <Newspaper className="w-3 h-3 text-primary" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground line-clamp-2 leading-snug group-hover:text-primary transition-colors">
              {news.title}
            </p>
            <div className="flex items-center gap-1.5 mt-2">
              <Clock className="w-3 h-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">
                {getPublishDate()}
              </span>
            </div>
          </div>
          <div className="flex-shrink-0 ml-2">
            <ExternalLink className="w-3.5 h-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:text-primary transition-all duration-200" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "group cursor-pointer p-4 rounded-xl transition-all duration-200",
        "bg-card hover:bg-card/80 border border-border hover:border-primary/30",
        "hover:shadow-lg hover:-translate-y-0.5",
        className
      )}
      onClick={handleClick}
    >
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <div className="flex-shrink-0 mt-0.5">
            <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
              <Newspaper className="w-4 h-4 text-primary" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-foreground line-clamp-2 leading-relaxed">
              {news.title}
            </h3>
          </div>
        </div>
        <ExternalLink className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-all duration-200 flex-shrink-0 group-hover:text-primary" />
      </div>

      {/* 설명 */}
      {showDescription && news.description && (
        <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed mb-3">
          {news.description}
        </p>
      )}

      {/* 메타데이터 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="w-3 h-3" />
          <span>{getPublishDate()}</span>
        </div>
        
        <div className="flex items-center gap-2">
          {news.original_link && (
            <span className="text-xs text-primary/60 bg-primary/10 px-2 py-1 rounded">
              원문보기
            </span>
          )}
        </div>
      </div>
    </div>
  );
}