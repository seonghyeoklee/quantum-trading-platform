package com.quantum.external.infrastructure.adapter.out.openai;

import com.quantum.external.application.port.out.AiAnalysisPort;
import com.quantum.external.domain.news.News;
import com.quantum.external.domain.news.NewsSentiment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.List;

/**
 * OpenAI API 어댑터 (선택사항)
 * TODO: OpenAI API 사용 여부 결정 후 구현
 *
 * 참고 사항:
 * - API 엔드포인트: https://api.openai.com/v1/chat/completions
 * - 인증 방식: Bearer Token (헤더)
 * - 모델: gpt-3.5-turbo (비용 효율적)
 * - 프롬프트: 뉴스 감정 분석 및 요약
 * - Rate Limit: 계정별 다름
 */
@Component
public class OpenAiAdapter implements AiAnalysisPort {

    private static final Logger log = LoggerFactory.getLogger(OpenAiAdapter.class);

    private final RestClient restClient;

    public OpenAiAdapter(RestClient restClient) {
        this.restClient = restClient;
    }

    @Override
    public NewsSentiment analyzeNewsSentiment(List<News> news) {
        log.info("OpenAI 뉴스 감정 분석 시작: newsCount={}", news.size());

        // TODO: OpenAI API 호출 구현
        // 1. API 키 설정 확인 (application-secrets.yml)
        // 2. 뉴스 제목/본문을 프롬프트로 구성
        // 3. ChatGPT API 호출
        // 4. 응답에서 감정 분류 추출
        // 5. NewsSentiment로 변환

        throw new UnsupportedOperationException("OpenAI API 구현 필요 - 사용 여부 결정 필요");
    }

    @Override
    public String summarizeNews(List<News> news) {
        log.info("OpenAI 뉴스 요약 시작: newsCount={}", news.size());

        // TODO: OpenAI API 호출 구현
        // 1. 뉴스 목록을 요약 프롬프트로 구성
        // 2. ChatGPT API 호출
        // 3. 요약 텍스트 반환

        throw new UnsupportedOperationException("OpenAI API 구현 필요 - 사용 여부 결정 필요");
    }
}
