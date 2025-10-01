package com.quantum.external.infrastructure.adapter.out.naver.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * 네이버 뉴스 검색 API 응답
 */
public record NaverNewsResponse(
        @JsonProperty("lastBuildDate")
        String lastBuildDate,

        @JsonProperty("total")
        int total,

        @JsonProperty("start")
        int start,

        @JsonProperty("display")
        int display,

        @JsonProperty("items")
        List<NewsItem> items
) {
    public record NewsItem(
            @JsonProperty("title")
            String title,               // 뉴스 제목 (검색어는 <b> 태그로 감싸져 있음)

            @JsonProperty("originallink")
            String originalLink,        // 기사 원문 URL

            @JsonProperty("link")
            String link,                // 네이버 뉴스 URL

            @JsonProperty("description")
            String description,         // 기사 요약 (검색어는 <b> 태그로 감싸져 있음)

            @JsonProperty("pubDate")
            String pubDate              // 발행일시 (예: Mon, 26 Sep 2016 07:50:00 +0900)
    ) {
    }
}
