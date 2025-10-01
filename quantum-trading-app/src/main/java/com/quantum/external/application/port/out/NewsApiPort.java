package com.quantum.external.application.port.out;

import com.quantum.external.domain.news.News;

import java.time.LocalDate;
import java.util.List;

/**
 * 뉴스 API 포트 (외부 시스템 추상화)
 * 구현체: NaverNewsAdapter, GoogleNewsAdapter 등
 */
public interface NewsApiPort {

    /**
     * 키워드로 뉴스 검색
     *
     * @param keyword 검색 키워드 (종목명, 종목코드 등)
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 뉴스 목록
     */
    List<News> searchNews(String keyword, LocalDate startDate, LocalDate endDate);
}
