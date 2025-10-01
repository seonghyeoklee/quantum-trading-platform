package com.quantum.external.domain.news;

import java.time.LocalDateTime;

/**
 * 뉴스 도메인 모델
 * TODO: 네이버 뉴스 API 응답 구조 확인 후 필드 조정
 */
public record News(
        String title,           // 뉴스 제목
        String content,         // 뉴스 본문 (요약)
        LocalDateTime publishedDate,  // 발행 일시
        String url,             // 원문 URL
        String source           // 출처 (예: 연합뉴스, 매일경제)
) {
}
