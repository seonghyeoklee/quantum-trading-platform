package com.quantum.external.application.service;

import com.quantum.external.application.port.in.SearchNewsUseCase;
import com.quantum.external.application.port.out.NewsApiPort;
import com.quantum.external.domain.news.News;
import com.quantum.external.domain.news.NewsAnalysisResult;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

/**
 * 뉴스 서비스
 * TODO: 비즈니스 로직 구현
 */
@Service
public class NewsService implements SearchNewsUseCase {

    private final NewsApiPort newsApiPort;

    public NewsService(NewsApiPort newsApiPort) {
        this.newsApiPort = newsApiPort;
    }

    @Override
    public List<News> searchNews(String keyword, LocalDate startDate, LocalDate endDate) {
        // TODO: 뉴스 검색 로직 구현
        return newsApiPort.searchNews(keyword, startDate, endDate);
    }

    @Override
    public NewsAnalysisResult analyzeStockNews(String stockCode, int recentDays) {
        // TODO: 뉴스 분석 로직 구현
        // 1. 최근 N일 뉴스 수집
        // 2. 키워드 매칭으로 감정 분석
        // 3. 호재/악재 점수 계산
        throw new UnsupportedOperationException("뉴스 분석 로직 구현 필요");
    }
}
