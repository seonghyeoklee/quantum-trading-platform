package com.quantum.external.application.port.in;

import com.quantum.external.domain.news.News;
import com.quantum.external.domain.news.NewsAnalysisResult;

import java.time.LocalDate;
import java.util.List;

/**
 * 뉴스 검색 Use Case
 */
public interface SearchNewsUseCase {

    /**
     * 키워드로 뉴스 검색
     */
    List<News> searchNews(String keyword, LocalDate startDate, LocalDate endDate);

    /**
     * 종목 뉴스 분석
     */
    NewsAnalysisResult analyzeStockNews(String stockCode, int recentDays);
}
