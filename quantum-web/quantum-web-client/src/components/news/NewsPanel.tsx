'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Search, ExternalLink, Clock, TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react';
import { NewsResponse, NewsSearchParams, NewsArticle, SentimentType, SortType } from '@/lib/api/news-types';
import newsApiClient from '@/lib/api/news-api';

interface NewsPanelProps {
  className?: string;
  selectedStock?: {
    code: string;
    name: string;
  } | null;
  onStockNewsSearch?: (stockCode: string, stockName: string) => void;
}

const getSentimentIcon = (sentiment: SentimentType) => {
  switch (sentiment) {
    case '긍정':
      return <TrendingUp className="w-4 h-4 text-green-600" />;
    case '부정':
      return <TrendingDown className="w-4 h-4 text-red-600" />;
    case '중립':
    default:
      return <Minus className="w-4 h-4 text-gray-600" />;
  }
};

const getSentimentColor = (sentiment: SentimentType) => {
  switch (sentiment) {
    case '긍정':
      return 'bg-green-100 text-green-800 border-green-200';
    case '부정':
      return 'bg-red-100 text-red-800 border-red-200';
    case '중립':
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const formatDate = (dateStr: string) => {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffHours < 1) {
      const diffMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
      return `${diffMinutes}분 전`;
    } else if (diffHours < 24) {
      return `${diffHours}시간 전`;
    } else {
      return date.toLocaleDateString('ko-KR');
    }
  } catch {
    return dateStr;
  }
};

export default function NewsPanel({ className, selectedStock, onStockNewsSearch }: NewsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [newsData, setNewsData] = useState<NewsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortType, setSortType] = useState<SortType>('date');
  const [sentimentFilter, setSentimentFilter] = useState<SentimentType | 'all'>('all');
  const [display, setDisplay] = useState(20);
  const [currentPage, setCurrentPage] = useState(1);

  // 선택된 종목이 변경되면 자동으로 뉴스 검색
  useEffect(() => {
    if (selectedStock) {
      const query = `${selectedStock.name} ${selectedStock.code}`;
      setSearchQuery(query);
      performSearch(query);
    }
  }, [selectedStock]);

  const performSearch = async (query?: string) => {
    const searchTerm = query || searchQuery;
    if (!searchTerm.trim()) {
      setError('검색어를 입력해주세요');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params: NewsSearchParams = {
        query: searchTerm,
        display,
        start: (currentPage - 1) * display + 1,
        sort: sortType,
      };

      if (sentimentFilter !== 'all') {
        params.sentiment = sentimentFilter as SentimentType;
      }

      const result = await newsApiClient.searchNews(params);
      setNewsData(result);

      if (!result.success || result.articles.length === 0) {
        setError(result.crawling_info?.error || '검색 결과가 없습니다');
      }
    } catch (err) {
      console.error('뉴스 검색 오류:', err);
      setError('뉴스를 가져오는 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setCurrentPage(1);
    performSearch();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleRefresh = () => {
    performSearch();
  };

  const filteredArticles = newsData?.articles || [];
  const hasMore = newsData && newsData.crawling_info.total_available && 
    (currentPage * display) < Math.min(newsData.crawling_info.total_available, 1000);

  const loadMore = () => {
    if (hasMore) {
      setCurrentPage(prev => prev + 1);
    }
  };

  // 페이지가 변경되면 검색 실행
  useEffect(() => {
    if (currentPage > 1 && searchQuery.trim()) {
      performSearch();
    }
  }, [currentPage]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* 검색 헤더 */}
      <div className="p-4 border-b border-border bg-background">
        <div className="flex flex-col space-y-4">
          {/* 제목 및 새로고침 */}
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">뉴스</h2>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
          </div>

          {/* 검색 입력 */}
          <div className="flex space-x-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="종목명, 키워드 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-9"
              />
            </div>
            <Button onClick={handleSearch} disabled={loading}>
              검색
            </Button>
          </div>

          {/* 필터 옵션 */}
          <div className="flex space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">정렬:</span>
              <Select value={sortType} onValueChange={(value: SortType) => setSortType(value)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="date">날짜순</SelectItem>
                  <SelectItem value="sim">정확도순</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium">감정:</span>
              <Select value={sentimentFilter} onValueChange={(value) => setSentimentFilter(value as SentimentType | 'all')}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="긍정">긍정</SelectItem>
                  <SelectItem value="부정">부정</SelectItem>
                  <SelectItem value="중립">중립</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 선택된 종목 표시 */}
          {selectedStock && (
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="text-xs">
                선택된 종목: {selectedStock.name} ({selectedStock.code})
              </Badge>
            </div>
          )}
        </div>
      </div>

      {/* 뉴스 목록 */}
      <div className="flex-1 overflow-auto p-4">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin mr-2" />
            <span>뉴스를 검색 중...</span>
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error}</p>
            <Button variant="outline" onClick={handleSearch}>
              다시 시도
            </Button>
          </div>
        )}

        {!loading && !error && newsData && (
          <>
            {/* 검색 정보 */}
            <div className="mb-4 p-3 bg-muted/50 rounded-lg">
              <div className="flex justify-between items-center text-sm text-muted-foreground">
                <span>검색어: <strong className="text-foreground">{newsData.query}</strong></span>
                <span>{newsData.articles.length}개 결과</span>
              </div>
              {newsData.crawling_info.total_available && (
                <div className="text-xs mt-1">
                  전체 {newsData.crawling_info.total_available.toLocaleString()}개 중 표시
                </div>
              )}
            </div>

            {/* 뉴스 기사 목록 */}
            <div className="space-y-4">
              {filteredArticles.map((article, index) => (
                <Card key={index} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center space-x-2">
                        {getSentimentIcon(article.sentiment)}
                        <Badge className={`text-xs ${getSentimentColor(article.sentiment)}`}>
                          {article.sentiment}
                        </Badge>
                      </div>
                      <div className="flex items-center text-xs text-muted-foreground">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatDate(article.date)}
                      </div>
                    </div>
                    
                    <h3 className="font-medium text-sm mb-2 leading-relaxed">
                      {article.title}
                    </h3>
                    
                    {article.content && (
                      <p className="text-xs text-muted-foreground mb-3 leading-relaxed">
                        {article.content}
                      </p>
                    )}
                    
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-muted-foreground">
                        출처: {article.source}
                      </span>
                      {article.link && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-xs"
                          onClick={() => window.open(article.link, '_blank')}
                        >
                          <ExternalLink className="w-3 h-3 mr-1" />
                          원문보기
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* 더보기 버튼 */}
            {hasMore && (
              <div className="text-center mt-6">
                <Button
                  variant="outline"
                  onClick={loadMore}
                  disabled={loading}
                >
                  {loading ? '로딩 중...' : '더 보기'}
                </Button>
              </div>
            )}

            {/* 하단 정보 */}
            {newsData.crawling_info && (
              <div className="mt-6 p-3 bg-muted/30 rounded-lg text-xs text-muted-foreground">
                <div>마지막 업데이트: {newsData.crawling_info.last_updated ? 
                  new Date(newsData.crawling_info.last_updated).toLocaleString('ko-KR') : '방금'}</div>
                {newsData.crawling_info.crawling_method && (
                  <div>데이터 제공: {newsData.crawling_info.crawling_method}</div>
                )}
              </div>
            )}
          </>
        )}

        {/* 초기 상태 */}
        {!loading && !error && !newsData && (
          <div className="text-center py-12">
            <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-medium mb-2">뉴스 검색</h3>
            <p className="text-sm text-muted-foreground mb-4">
              종목명이나 키워드를 입력하여 관련 뉴스를 검색해보세요
            </p>
            <p className="text-xs text-muted-foreground">
              감정 분석과 함께 최신 뉴스를 제공합니다
            </p>
          </div>
        )}
      </div>
    </div>
  );
}