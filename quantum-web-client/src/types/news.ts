/**
 * News API types for External Adapter integration
 */

export interface NewsItem {
  title: string;           // 뉴스 제목 (HTML 태그 제거됨)
  original_link: string;   // 원문 URL
  link: string;           // 네이버 뉴스 URL  
  description: string;     // 내용 요약 (HTML 태그 제거됨)
  pub_date: string;       // 게시 시간
}

export interface NewsSearchResponse {
  last_build_date: string; // 검색 결과 생성 시간
  total: number;          // 총 검색 결과 개수
  start: number;          // 검색 시작 위치
  display: number;        // 표시된 결과 개수
  items: NewsItem[];      // 뉴스 목록
  has_more?: boolean;     // 추가 결과 여부
  next_start?: number;    // 다음 페이지 시작 위치
}

export interface NewsSearchParams {
  query: string;          // 검색어
  display?: number;       // 결과 개수 (1-100)
  start?: number;         // 시작 위치 (1-1000)
  sort?: 'sim' | 'date';  // 정렬 방식
}

export interface NewsApiError {
  error: string;
  message: string;
  timestamp: number;
}

// 날짜별 뉴스 캐시 타입
export interface DateNewsCache {
  [date: string]: {
    items: NewsItem[];
    timestamp: number;
    total: number;
  };
}

// 뉴스 카테고리 타입
export type NewsCategory = 'general' | 'financial' | 'latest';

// 뉴스 필터 옵션
export interface NewsFilter {
  category: NewsCategory;
  keyword?: string;
  days_back?: number;
}