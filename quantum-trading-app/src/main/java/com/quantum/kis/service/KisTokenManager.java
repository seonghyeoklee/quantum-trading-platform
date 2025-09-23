package com.quantum.kis.service;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.token.KisToken;
import com.quantum.kis.dto.TokenInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * KIS 토큰 관리 서비스 (DB 기반으로 리팩토링)
 * - 데이터베이스 기반 토큰 관리
 * - 자동 만료 관리
 * - 토큰 유효성 검증
 */
@Service
public class KisTokenManager {

    private static final Logger log = LoggerFactory.getLogger(KisTokenManager.class);

    private final KisTokenPersistenceService persistenceService;

    public KisTokenManager(KisTokenPersistenceService persistenceService) {
        this.persistenceService = persistenceService;
    }

    /**
     * 유효한 액세스 토큰을 반환한다. 만료된 경우 자동으로 재발급한다.
     * @param environment KIS 환경
     * @return 액세스 토큰
     */
    public String getValidAccessToken(KisEnvironment environment) {
        return persistenceService.getValidAccessToken(environment);
    }

    /**
     * 유효한 웹소켓 키를 반환한다. 만료된 경우 자동으로 재발급한다.
     * @param environment KIS 환경
     * @return 웹소켓 키
     */
    public String getValidWebSocketKey(KisEnvironment environment) {
        return persistenceService.getValidWebSocketKey(environment);
    }

    /**
     * 액세스 토큰을 강제로 재발급한다.
     * @param environment KIS 환경
     * @return 새로운 액세스 토큰
     */
    public String refreshAccessToken(KisEnvironment environment) {
        return persistenceService.renewAccessToken(environment);
    }

    /**
     * 웹소켓 키를 강제로 재발급한다.
     * @param environment KIS 환경
     * @return 새로운 웹소켓 키
     */
    public String refreshWebSocketKey(KisEnvironment environment) {
        return persistenceService.renewWebSocketKey(environment);
    }

    /**
     * 모든 환경의 모든 토큰을 재발급한다.
     */
    public void refreshAllTokens() {
        persistenceService.renewAllTokens();
    }

    /**
     * 만료된 토큰들을 정리한다.
     */
    public void cleanupExpiredTokens() {
        persistenceService.cleanupExpiredTokens();
    }

    /**
     * 현재 저장된 토큰 상태를 반환한다 (TokenInfo 형태로 변환).
     * @return 토큰 상태 맵
     */
    public Map<String, TokenInfo> getTokenCacheStatus() {
        List<KisToken> allTokens = persistenceService.getAllTokens();

        return allTokens.stream()
                .collect(Collectors.toMap(
                        token -> token.getId().toKey(),
                        this::convertToTokenInfo
                ));
    }

    /**
     * 도메인 토큰을 TokenInfo DTO로 변환
     * @param kisToken 도메인 토큰
     * @return TokenInfo DTO
     */
    private TokenInfo convertToTokenInfo(KisToken kisToken) {
        return new TokenInfo(
                kisToken.getId().environment(),
                kisToken.getId().tokenType(),
                kisToken.getToken().value(),
                kisToken.getIssuedAt(),
                kisToken.getToken().expiresAt(),
                kisToken.isUsable()
        );
    }
}