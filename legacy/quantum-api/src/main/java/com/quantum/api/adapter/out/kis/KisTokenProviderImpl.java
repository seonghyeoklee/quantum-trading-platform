package com.quantum.api.adapter.out.kis;

import com.quantum.batch.service.KisTokenService;
import com.quantum.kis.service.KisRateLimiter;
import com.quantum.kis.service.KisTokenProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * KIS 토큰 제공자 구현체 (quantum-api 모듈)
 *
 * <p>quantum-adapter가 quantum-batch에 직접 의존하지 않도록 quantum-api에서 KisTokenProvider 인터페이스를 구현
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisTokenProviderImpl implements KisTokenProvider {

    private final KisTokenService kisTokenService;
    private final KisRateLimiter kisRateLimiter;

    @Override
    public String getValidAccessToken() {
        try {
            String token = kisTokenService.getValidAccessToken();
            if (token != null) {
                log.debug("KisTokenProviderImpl: Successfully retrieved access token");
                return token;
            } else {
                log.warn("KisTokenProviderImpl: No valid access token available");
                return null;
            }
        } catch (Exception e) {
            log.error("KisTokenProviderImpl: Failed to get access token", e);
            return null;
        }
    }

    @Override
    public boolean checkRateLimit(String apiEndpoint) {
        return kisRateLimiter.tryAcquire(apiEndpoint, false);
    }

    @Override
    public boolean acquireWithWait(String apiEndpoint) {
        return kisRateLimiter.acquireWithWait(apiEndpoint, false);
    }
}
