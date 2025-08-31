/**
 * 뉴스 API 관련 타입 정의
 */

export interface NewsArticle {
  title: string;
  link?: string;
  content?: string;
  source: string;
  date: string;
  sentiment: '긍정' | '부정' | '중립';
  category?: string;
}

export interface NewsResponse {
  success: boolean;
  query: string;
  total_count: number;
  articles: NewsArticle[];
  category_stats: Record<string, number>;
  crawling_info: {
    error?: string;
    crawling_method?: string;
    api_version?: string;
    search_method?: string;
    search_query?: string;
    parameters?: {
      display: number;
      start: number;
      sort: string;
    };
    total_available?: number;
    collected_count?: number;
    last_updated?: string;
  };
}

export interface NewsSearchParams {
  query: string;
  display?: number;  // 1~100, 기본: 20
  start?: number;    // 1~1000, 기본: 1
  sort?: 'sim' | 'date';  // sim: 정확도순, date: 날짜순
  sentiment?: '긍정' | '부정' | '중립';
}

export interface NewsApiInfo {
  success: boolean;
  api_info: {
    service: string;
    version: string;
    daily_limit: number;
    max_display: number;
    max_start: number;
  };
  parameters: Record<string, string>;
  sort_options: Record<string, string>;
  sentiment_types: string[];
  supported_stocks: Record<string, string>;
  usage_examples: Record<string, string>;
}

export type SentimentType = '긍정' | '부정' | '중립';
export type SortType = 'sim' | 'date';