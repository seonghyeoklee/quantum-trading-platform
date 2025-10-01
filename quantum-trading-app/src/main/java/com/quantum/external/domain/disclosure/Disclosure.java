package com.quantum.external.domain.disclosure;

import java.time.LocalDateTime;

/**
 * 공시 도메인 모델 (DART API 기반)
 */
public record Disclosure(
        String title,               // 보고서명
        String companyName,         // 회사명
        LocalDateTime filedDate,    // 접수일시
        DisclosureType type,        // 공시 유형
        String url,                 // 공시 원문 URL
        String summary              // 비고
) {
}
