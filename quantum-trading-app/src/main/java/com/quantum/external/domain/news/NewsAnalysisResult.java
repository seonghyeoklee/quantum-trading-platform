package com.quantum.external.domain.news;

import java.util.List;

/**
 * 뉴스 분석 결과
 * TODO: 분석 요구사항 확정 후 필드 조정
 */
public record NewsAnalysisResult(
        String stockCode,
        int totalNewsCount,
        int positiveCount,
        int neutralCount,
        int negativeCount,
        NewsSentiment overallSentiment,
        double sentimentScore,      // -1.0 ~ 1.0
        List<String> keyTopics,
        String summary
) {
}
