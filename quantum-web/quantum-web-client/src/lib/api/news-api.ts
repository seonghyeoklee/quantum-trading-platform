import { getKiwoomAdapterUrl } from '@/lib/api-config';
import { NewsResponse, NewsSearchParams, NewsApiInfo } from './news-types';

/**
 * 뉴스 API 클라이언트
 * Kiwoom Adapter의 네이버 뉴스 API (포트 10201)를 호출
 */
class NewsApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getKiwoomAdapterUrl();
  }

  /**
   * 뉴스 검색 API 호출
   */
  async searchNews(params: NewsSearchParams): Promise<NewsResponse> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('query', params.query);
      
      if (params.display) {
        queryParams.append('display', params.display.toString());
      }
      if (params.start) {
        queryParams.append('start', params.start.toString());
      }
      if (params.sort) {
        queryParams.append('sort', params.sort);
      }
      if (params.sentiment) {
        queryParams.append('sentiment', params.sentiment);
      }

      console.log('🔍 [NewsAPI] Searching news:', `${this.baseUrl}/api/v1/news/search?${queryParams.toString()}`);
      
      const response = await fetch(`${this.baseUrl}/api/v1/news/search?${queryParams.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`News API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📰 [NewsAPI] Search result:', data);
      
      return data;
    } catch (error) {
      console.error('❌ [NewsAPI] Search failed:', error);
      throw error;
    }
  }

  /**
   * 뉴스 API 정보 조회
   */
  async getNewsInfo(): Promise<NewsApiInfo> {
    try {
      console.log('ℹ️ [NewsAPI] Getting news info:', `${this.baseUrl}/api/v1/news/info`);
      
      const response = await fetch(`${this.baseUrl}/api/v1/news/info`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`News API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('📋 [NewsAPI] API info:', data);
      
      return data;
    } catch (error) {
      console.error('❌ [NewsAPI] Get info failed:', error);
      throw error;
    }
  }

  /**
   * 종목 관련 뉴스 검색 (편의 메서드)
   */
  async searchStockNews(stockCode: string, stockName?: string, options?: Omit<NewsSearchParams, 'query'>): Promise<NewsResponse> {
    const query = stockName ? `${stockName} ${stockCode}` : stockCode;
    return this.searchNews({
      query,
      ...options
    });
  }

  /**
   * 최신 뉴스 검색 (날짜순 정렬)
   */
  async searchLatestNews(query: string, display: number = 20): Promise<NewsResponse> {
    return this.searchNews({
      query,
      display,
      sort: 'date'
    });
  }

  /**
   * 감정별 뉴스 검색
   */
  async searchNewsBySentiment(query: string, sentiment: '긍정' | '부정' | '중립', display: number = 20): Promise<NewsResponse> {
    return this.searchNews({
      query,
      display,
      sentiment,
      sort: 'date'
    });
  }
}

// 싱글톤 인스턴스 생성
const newsApiClient = new NewsApiClient();

export default newsApiClient;

// 개별 함수들도 export (편의성을 위해)
export const searchNews = (params: NewsSearchParams) => newsApiClient.searchNews(params);
export const getNewsInfo = () => newsApiClient.getNewsInfo();
export const searchStockNews = (stockCode: string, stockName?: string, options?: Omit<NewsSearchParams, 'query'>) => 
  newsApiClient.searchStockNews(stockCode, stockName, options);
export const searchLatestNews = (query: string, display?: number) => 
  newsApiClient.searchLatestNews(query, display);
export const searchNewsBySentiment = (query: string, sentiment: '긍정' | '부정' | '중립', display?: number) => 
  newsApiClient.searchNewsBySentiment(query, sentiment, display);