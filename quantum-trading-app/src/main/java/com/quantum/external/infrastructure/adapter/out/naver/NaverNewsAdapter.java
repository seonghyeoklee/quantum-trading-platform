package com.quantum.external.infrastructure.adapter.out.naver;

import com.quantum.external.application.port.out.NewsApiPort;
import com.quantum.external.domain.news.News;
import com.quantum.external.infrastructure.adapter.out.naver.dto.NaverNewsResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * 네이버 뉴스 검색 API 어댑터
 *
 * API 스펙:
 * - 엔드포인트: https://openapi.naver.com/v1/search/news.json
 * - 인증: X-Naver-Client-Id, X-Naver-Client-Secret (헤더)
 * - 파라미터: query(필수), display(1-100), start(1-1000), sort(sim|date)
 * - Rate Limit: 일 25,000건
 */
@Component
public class NaverNewsAdapter implements NewsApiPort {

    private static final Logger log = LoggerFactory.getLogger(NaverNewsAdapter.class);
    private static final int DEFAULT_DISPLAY = 100;  // 최대 100개
    private static final int MAX_START = 1000;       // 최대 1000

    // RFC 1123 날짜 형식 파서 (예: Mon, 26 Sep 2016 07:50:00 +0900)
    private static final DateTimeFormatter RFC_1123_FORMATTER =
            DateTimeFormatter.ofPattern("EEE, dd MMM yyyy HH:mm:ss Z", Locale.ENGLISH);

    private final RestClient naverNewsRestClient;

    public NaverNewsAdapter(@Qualifier("naverNewsRestClient") RestClient naverNewsRestClient) {
        this.naverNewsRestClient = naverNewsRestClient;
    }

    @Override
    public List<News> searchNews(String keyword, LocalDate startDate, LocalDate endDate) {
        log.info("네이버 뉴스 검색 시작: keyword={}, startDate={}, endDate={}", keyword, startDate, endDate);

        try {
            // 네이버 뉴스 API 호출 (날짜순 정렬)
            NaverNewsResponse response = naverNewsRestClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/news.json")
                            .queryParam("query", keyword)
                            .queryParam("display", DEFAULT_DISPLAY)
                            .queryParam("start", 1)
                            .queryParam("sort", "date")  // 날짜순 정렬
                            .build())
                    .retrieve()
                    .body(NaverNewsResponse.class);

            if (response == null || response.items() == null) {
                log.warn("네이버 뉴스 API 응답이 비어있습니다: keyword={}", keyword);
                return List.of();
            }

            // News 도메인 객체로 변환 및 날짜 필터링
            List<News> newsList = new ArrayList<>();
            for (NaverNewsResponse.NewsItem item : response.items()) {
                try {
                    News news = convertToNews(item);

                    // 날짜 필터링 (startDate ~ endDate 범위)
                    if (isWithinDateRange(news.publishedDate(), startDate, endDate)) {
                        newsList.add(news);
                    }
                } catch (Exception e) {
                    log.warn("뉴스 항목 변환 실패: title={}, error={}", item.title(), e.getMessage());
                }
            }

            log.info("네이버 뉴스 검색 완료: keyword={}, total={}, filtered={}",
                    keyword, response.total(), newsList.size());

            return newsList;

        } catch (Exception e) {
            log.error("네이버 뉴스 API 호출 실패: keyword={}, error={}", keyword, e.getMessage(), e);
            return List.of();
        }
    }

    /**
     * NaverNewsResponse.NewsItem을 News 도메인 객체로 변환
     */
    private News convertToNews(NaverNewsResponse.NewsItem item) {
        // HTML 태그 제거 (<b>, </b>)
        String cleanTitle = removeHtmlTags(item.title());
        String cleanContent = removeHtmlTags(item.description());

        // RFC 1123 형식의 날짜를 LocalDateTime으로 변환
        LocalDateTime publishedDate = parseRfc1123Date(item.pubDate());

        // 출처 추출 (originalLink의 도메인)
        String source = extractSource(item.originalLink());

        return new News(
                cleanTitle,
                cleanContent,
                publishedDate,
                item.originalLink(),
                source
        );
    }

    /**
     * HTML 태그 제거
     */
    private String removeHtmlTags(String text) {
        if (text == null) {
            return "";
        }
        return text.replaceAll("<[^>]*>", "");
    }

    /**
     * RFC 1123 날짜 형식 파싱
     * 예: "Mon, 26 Sep 2016 07:50:00 +0900"
     */
    private LocalDateTime parseRfc1123Date(String dateString) {
        try {
            ZonedDateTime zonedDateTime = ZonedDateTime.parse(dateString, RFC_1123_FORMATTER);
            return zonedDateTime.toLocalDateTime();
        } catch (DateTimeParseException e) {
            log.warn("날짜 파싱 실패: dateString={}, error={}", dateString, e.getMessage());
            return LocalDateTime.now();  // 파싱 실패 시 현재 시간 반환
        }
    }

    /**
     * URL에서 출처(도메인) 추출
     */
    private String extractSource(String url) {
        if (url == null || url.isEmpty()) {
            return "알 수 없음";
        }

        try {
            // URL에서 도메인 추출 (예: https://www.yonhapnews.co.kr/... -> yonhapnews.co.kr)
            String domain = url.replaceAll("^https?://", "")
                              .replaceAll("/.*$", "");

            // www. 제거
            if (domain.startsWith("www.")) {
                domain = domain.substring(4);
            }

            return domain;
        } catch (Exception e) {
            return "알 수 없음";
        }
    }

    /**
     * 날짜 범위 검사
     */
    private boolean isWithinDateRange(LocalDateTime publishedDate, LocalDate startDate, LocalDate endDate) {
        LocalDate publishedLocalDate = publishedDate.toLocalDate();
        return !publishedLocalDate.isBefore(startDate) && !publishedLocalDate.isAfter(endDate);
    }
}

