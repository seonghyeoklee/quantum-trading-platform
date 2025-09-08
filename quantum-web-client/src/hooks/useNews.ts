'use client';

import { useState, useEffect, useCallback } from 'react';
import { format } from 'date-fns';
import { NewsItem, NewsSearchResponse, NewsCategory } from '@/types/news';
import newsApi from '@/lib/services/news-api';

interface UseNewsOptions {
  autoLoad?: boolean;
  category?: NewsCategory;
}

interface UseNewsReturn {
  news: NewsItem[];
  isLoading: boolean;
  error: string | null;
  hasMore: boolean;
  total: number;
  loadNews: (query: string, options?: { category?: NewsCategory; display?: number }) => Promise<void>;
  loadNewsForDate: (date: Date, category?: NewsCategory) => Promise<void>;
  loadLatestNews: (keyword: string, count?: number) => Promise<void>;
  loadFinancialNews: (symbol: string, daysBack?: number) => Promise<void>;
  refresh: () => Promise<void>;
  clearNews: () => void;
}

export function useNews(options: UseNewsOptions = {}): UseNewsReturn {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [lastOptions, setLastOptions] = useState<any>(null);

  const { autoLoad = false, category = 'general' } = options;

  // 뉴스 품질 필터링 함수 (임시로 비활성화)
  const filterNewsQuality = useCallback((newsItems: NewsItem[]): NewsItem[] => {
    // 임시로 비활성화 - 모든 뉴스를 통과시킴
    return newsItems || [];
  }, []);

  // API 호출 처리 함수
  const handleApiCall = useCallback(async (
    apiCall: () => Promise<NewsSearchResponse>
  ): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('🔥 API 호출 시작');
      const response = await apiCall();
      console.log('🔥 API 응답 받음:', response.items?.length, '개 뉴스');
      
      // 필터링 없이 바로 설정 (임시)
      setNews(response.items || []);
      setHasMore(response.has_more || false);
      setTotal(response.total || response.items?.length || 0);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '뉴스를 불러오는 중 오류가 발생했습니다';
      setError(errorMessage);
      console.error('🔥 뉴스 API 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadNews = useCallback(async (
    query: string, 
    options: { category?: NewsCategory; display?: number } = {}
  ): Promise<void> => {
    setLastQuery(query);
    setLastOptions(options);

    console.log('🔥 loadNews 호출:', query);
    await handleApiCall(() => newsApi.searchNews({
      query,
      display: options.display || 10,
      sort: 'date'
    }));
  }, [handleApiCall]);

  const loadNewsForDate = useCallback(async (
    date: Date, 
    newsCategory: NewsCategory = category
  ): Promise<void> => {
    const dateString = format(date, 'yyyy-MM-dd');
    setLastQuery(`date:${dateString}`);
    setLastOptions({ category: newsCategory });

    console.log('🔥 loadNewsForDate 호출:', dateString, newsCategory);
    await handleApiCall(() => newsApi.getNewsForDate(dateString, newsCategory));
  }, [category, handleApiCall]);

  const loadLatestNews = useCallback(async (
    keyword: string, 
    count: number = 10
  ): Promise<void> => {
    setLastQuery(`latest:${keyword}`);
    setLastOptions({ count });

    console.log('🔥 loadLatestNews 호출:', keyword, count);
    await handleApiCall(() => newsApi.getLatestNews(keyword, count));
  }, [handleApiCall]);

  const loadFinancialNews = useCallback(async (
    symbol: string, 
    daysBack: number = 7
  ): Promise<void> => {
    setLastQuery(`financial:${symbol}`);
    setLastOptions({ daysBack });

    console.log('🔥 loadFinancialNews 호출:', symbol, daysBack);
    await handleApiCall(() => newsApi.getFinancialNews(symbol, daysBack));
  }, [handleApiCall]);

  const refresh = useCallback(async (): Promise<void> => {
    if (!lastQuery) return;

    console.log('🔥 refresh 호출:', lastQuery);
    // 캐시 클리어
    newsApi.clearCache();

    if (lastQuery.startsWith('date:')) {
      const dateString = lastQuery.replace('date:', '');
      const date = new Date(dateString);
      await loadNewsForDate(date, lastOptions?.category);
    } else if (lastQuery.startsWith('latest:')) {
      const keyword = lastQuery.replace('latest:', '');
      await loadLatestNews(keyword, lastOptions?.count);
    } else if (lastQuery.startsWith('financial:')) {
      const symbol = lastQuery.replace('financial:', '');
      await loadFinancialNews(symbol, lastOptions?.daysBack);
    } else {
      await loadNews(lastQuery, lastOptions);
    }
  }, [lastQuery, lastOptions, loadNewsForDate, loadLatestNews, loadFinancialNews, loadNews]);

  const clearNews = useCallback((): void => {
    console.log('🔥 clearNews 호출');
    setNews([]);
    setError(null);
    setHasMore(false);
    setTotal(0);
    setLastQuery('');
    setLastOptions(null);
  }, []);

  // 자동 로드
  useEffect(() => {
    if (autoLoad) {
      console.log('🔥 자동 로드 실행');
      loadLatestNews('경제', 10);
    }
  }, [autoLoad, loadLatestNews]);

  return {
    news,
    isLoading,
    error,
    hasMore,
    total,
    loadNews,
    loadNewsForDate,
    loadLatestNews,
    loadFinancialNews,
    refresh,
    clearNews
  };
}

// 오늘 뉴스용 특별 훅 - 품질 필터링 적용
export function useTodayNews() {
  const [todayNews, setTodayNews] = useState<NewsItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTodayNews = useCallback(async (keywords?: string[]) => {
    try {
      setIsLoading(true);
      setError(null);

      console.log('🔥 오늘 뉴스 로드 시작');
      const response = await newsApi.getTodayNews(keywords);
      console.log('🔥 오늘 뉴스 응답:', response.items?.length, '개');
      
      // 임시로 필터링 없이 설정
      setTodayNews(response.items || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '오늘 뉴스를 불러오는 중 오류가 발생했습니다';
      setError(errorMessage);
      console.error('🔥 오늘 뉴스 로드 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 자동 로드
  useEffect(() => {
    console.log('🔥 useTodayNews 자동 로드');
    loadTodayNews();
  }, [loadTodayNews]);

  return {
    news: todayNews,
    isLoading,
    error,
    refresh: loadTodayNews,
    clear: () => setTodayNews([])
  };
}