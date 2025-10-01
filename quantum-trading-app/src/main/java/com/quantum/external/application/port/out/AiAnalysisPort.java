package com.quantum.external.application.port.out;

import com.quantum.external.domain.news.News;
import com.quantum.external.domain.news.NewsSentiment;

import java.util.List;

/**
 * AI 분석 포트 (외부 AI 서비스 추상화)
 * 구현체: OpenAiAdapter 등
 * TODO: OpenAI API 사용 여부 결정 후 구현
 */
public interface AiAnalysisPort {

    /**
     * 뉴스 감정 분석
     *
     * @param news 분석할 뉴스 목록
     * @return 감정 분류 결과
     */
    NewsSentiment analyzeNewsSentiment(List<News> news);

    /**
     * 뉴스 요약
     *
     * @param news 요약할 뉴스 목록
     * @return 요약 텍스트
     */
    String summarizeNews(List<News> news);
}
