package com.quantum.external.infrastructure.adapter.out.naver;

import com.quantum.external.application.port.out.NewsApiPort;
import com.quantum.external.domain.news.News;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.util.List;

/**
 * 네이버 뉴스 검색 API 어댑터
 * TODO: 네이버 뉴스 API 스펙 확인 후 구현
 *
 * 참고 사항:
 * - API 엔드포인트: https://openapi.naver.com/v1/search/news.json
 * - 인증 방식: Client ID / Client Secret (헤더)
 * - 요청 파라미터: query, display, start, sort
 * - 응답 구조: JSON (items 배열)
 * - Rate Limit: 일 25,000건
 */
@Component
public class NaverNewsAdapter implements NewsApiPort {

    private static final Logger log = LoggerFactory.getLogger(NaverNewsAdapter.class);

    private final RestClient restClient;

    public NaverNewsAdapter(RestClient restClient) {
        this.restClient = restClient;
    }

    @Override
    public List<News> searchNews(String keyword, LocalDate startDate, LocalDate endDate) {
        log.info("네이버 뉴스 검색 시작: keyword={}, startDate={}, endDate={}", keyword, startDate, endDate);

        // TODO: 네이버 뉴스 API 호출 구현
        // 1. API 키 설정 확인 (application-secrets.yml)
        // 2. RestClient로 API 호출
        // 3. 응답 JSON 파싱
        // 4. News 도메인 객체로 변환
        // 5. 날짜 필터링 적용

        throw new UnsupportedOperationException("네이버 뉴스 API 구현 필요 - API 스펙 확인 필요");
    }
}
