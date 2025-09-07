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

  const handleApiCall = useCallback(async (
    apiCall: () => Promise<NewsSearchResponse>
  ): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiCall();
      
      setNews(response.items);
      setHasMore(response.has_more || false);
      setTotal(response.total);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '뉴스를 불러오는 중 오류가 발생했습니다';
      setError(errorMessage);
      console.error('뉴스 API 오류:', err);
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

    await handleApiCall(() => newsApi.getNewsForDate(dateString, newsCategory));
  }, [category, handleApiCall]);

  const loadLatestNews = useCallback(async (
    keyword: string, 
    count: number = 10
  ): Promise<void> => {
    setLastQuery(`latest:${keyword}`);
    setLastOptions({ count });

    await handleApiCall(() => newsApi.getLatestNews(keyword, count));
  }, [handleApiCall]);

  const loadFinancialNews = useCallback(async (
    symbol: string, 
    daysBack: number = 7
  ): Promise<void> => {
    setLastQuery(`financial:${symbol}`);
    setLastOptions({ daysBack });

    await handleApiCall(() => newsApi.getFinancialNews(symbol, daysBack));
  }, [handleApiCall]);

  const refresh = useCallback(async (): Promise<void> => {
    if (!lastQuery) return;

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

// 오늘 뉴스용 특별 훅
export function useTodayNews() {
  const [todayNews, setTodayNews] = useState<NewsItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTodayNews = useCallback(async (keywords?: string[]) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await newsApi.getTodayNews(keywords);
      setTodayNews(response.items);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '오늘 뉴스를 불러오는 중 오류가 발생했습니다';
      setError(errorMessage);
      console.error('오늘 뉴스 로드 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 자동 로드
  useEffect(() => {
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