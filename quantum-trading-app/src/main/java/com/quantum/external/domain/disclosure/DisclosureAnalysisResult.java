package com.quantum.external.domain.disclosure;

import java.util.List;

/**
 * 공시 분석 결과
 * TODO: 분석 요구사항 확정 후 필드 조정
 */
public record DisclosureAnalysisResult(
        String stockCode,
        int totalDisclosureCount,
        int majorDisclosureCount,
        int fairDisclosureCount,
        double materialityScore,    // 재료성 점수 0.0 ~ 1.0
        List<String> keyTopics,
        String summary
) {
}
