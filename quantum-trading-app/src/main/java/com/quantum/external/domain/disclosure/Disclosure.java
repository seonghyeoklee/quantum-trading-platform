package com.quantum.external.domain.disclosure;

import java.time.LocalDate;

/**
 * 공시 도메인 모델
 * TODO: DART API 응답 구조 확인 후 필드 조정
 */
public record Disclosure(
        String reportCode,          // 접수번호
        String title,               // 공시 제목
        DisclosureType type,        // 공시 유형
        LocalDate reportedDate,     // 공시 일자
        String url,                 // 공시 원문 URL
        String stockCode            // 종목코드
) {
}
