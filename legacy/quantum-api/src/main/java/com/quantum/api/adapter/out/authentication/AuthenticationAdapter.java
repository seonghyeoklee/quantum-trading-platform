package com.quantum.api.adapter.out.authentication;

import com.quantum.api.application.port.out.AuthenticationPort;
import com.quantum.core.domain.model.kis.KisToken;
import com.quantum.core.domain.port.repository.KisTokenRepository;
import com.quantum.kis.client.KisFeignClient;
import com.quantum.kis.model.KisTokenResponse;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** 인증 어댑터 구현체 - DB 기반 토큰 관리 (1분당 1회 제한 대응) */
@Slf4j
@Component
@RequiredArgsConstructor
public class AuthenticationAdapter implements AuthenticationPort {

    private final KisFeignClient kisFeignClient;
    private final KisTokenRepository kisTokenRepository;

    @Value("${kis.api.app-key}")
    private String appKey;

    @Value("${kis.api.app-secret}")
    private String appSecret;

    @Override
    public String getValidAccessToken() {
        // DB에서 활성화된 유효한 토큰 조회
        Optional<KisToken> validToken = kisTokenRepository.findActiveValidToken();

        if (validToken.isPresent() && !validToken.get().isExpired()) {
            KisToken token = validToken.get();
            log.debug("KIS: Using DB cached access token (expires: {})", token.getExpiresAt());
            return token.getAccessToken();
        }

        log.info("KIS: DB token expired or missing, requesting new token");
        return refreshAccessToken();
    }

    @Override
    public String refreshAccessToken() {
        try {
            // 기존 토큰 모두 비활성화
            kisTokenRepository.deactivateAllTokens();

            Map<String, String> requestBody =
                    Map.of(
                            "grant_type", "client_credentials",
                            "appkey", appKey,
                            "appsecret", appSecret);

            KisTokenResponse response = kisFeignClient.getAccessToken(requestBody);

            String newToken = response.accessToken();
            if (newToken == null || newToken.isEmpty()) {
                throw new RuntimeException("KIS API returned empty access token");
            }

            // DB에 새 토큰 저장
            KisToken kisToken =
                    KisToken.fromKisResponse(
                            response.tokenType(),
                            response.accessToken(),
                            response.accessTokenExpired(),
                            response.expiresIn());

            KisToken savedToken = kisTokenRepository.save(kisToken);
            log.info("KIS: New access token saved to DB (expires: {})", savedToken.getExpiresAt());

            // 만료된 토큰 정리
            kisTokenRepository.deleteExpiredTokens();

            return newToken;

        } catch (Exception e) {
            log.error("KIS: Failed to refresh access token", e);
            throw new RuntimeException("KIS 액세스 토큰 갱신 실패", e);
        }
    }

    @Override
    public boolean isTokenRefreshRequired() {
        Optional<KisToken> validToken = kisTokenRepository.findActiveValidToken();

        if (validToken.isEmpty()) {
            return true;
        }

        KisToken token = validToken.get();
        LocalDateTime refreshTime = token.getCreatedAt().plusHours(6);
        boolean shouldRefreshByPolicy = LocalDateTime.now().isAfter(refreshTime);
        boolean isExpired = token.isExpired();

        return shouldRefreshByPolicy || isExpired;
    }

    @Override
    public boolean isHealthy() {
        try {
            String token = getValidAccessToken();
            return token != null && !token.isEmpty();
        } catch (Exception e) {
            log.warn("KIS: Health check failed", e);
            return false;
        }
    }

    /** DB에서 토큰 만료 시간 조회 */
    public LocalDateTime getTokenExpiryTime() {
        Optional<KisToken> validToken = kisTokenRepository.findActiveValidToken();
        return validToken.map(KisToken::getExpiresAt).orElse(null);
    }

    /** 모든 토큰 무효화 */
    public void invalidateToken() {
        kisTokenRepository.deactivateAllTokens();
        log.info("KIS: All access tokens invalidated in DB");
    }
}
