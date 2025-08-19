package com.quantum.kis.config;

import com.quantum.kis.service.KisRateLimiter;
import feign.RequestInterceptor;
import feign.RequestTemplate;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * KIS API Rate Limiting Feign Interceptor
 *
 * <p>모든 Feign 요청에 대해 Rate Limiting을 적용합니다. 공식 정책: 실전투자 20건/초, 모의투자 2건/초, 토큰발급 1건/초
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisRateLimitInterceptor implements RequestInterceptor {

    private final KisRateLimiter kisRateLimiter;

    @Override
    public void apply(RequestTemplate template) {
        String path = template.path();
        String apiEndpoint = extractApiEndpoint(path);
        boolean isTokenRequest = path.contains("/oauth2/tokenP");

        try {
            // Rate Limiting 체크 및 대기
            if (!kisRateLimiter.acquireWithWait(apiEndpoint, isTokenRequest)) {
                log.error("KIS API rate limit exceeded for endpoint: {} ({})", apiEndpoint, path);
                throw new RuntimeException("KIS API rate limit exceeded: " + apiEndpoint);
            }

            log.debug("KIS API rate limit check passed for: {} ({})", apiEndpoint, path);

        } catch (Exception e) {
            log.error("Rate limit check failed for {}: {}", apiEndpoint, e.getMessage());
            // Rate limiting 실패시에도 요청은 진행 (시스템 중단 방지)
            // 하지만 경고 로그 출력
            log.warn("Proceeding with API call despite rate limit check failure: {}", apiEndpoint);
        }
    }

    /** API 경로에서 엔드포인트 식별자 추출 */
    private String extractApiEndpoint(String path) {
        if (path.contains("/oauth2/tokenP")) {
            return "oauth2_token";
        } else if (path.contains("/quotations/inquire-price")) {
            return "current_price";
        } else if (path.contains("/quotations/inquire-daily-itemchartprice")) {
            return "daily_candle";
        } else if (path.contains("/quotations/inquire-time-itemchartprice")) {
            return "minute_candle";
        } else if (path.contains("/trading/inquire-balance")) {
            return "account_balance";
        } else {
            // 알 수 없는 엔드포인트는 일반적인 이름으로
            return "unknown_api";
        }
    }
}
