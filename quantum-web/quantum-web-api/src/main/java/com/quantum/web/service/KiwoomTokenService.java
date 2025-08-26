package com.quantum.web.service;

import com.quantum.trading.platform.shared.value.ApiCredentials;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

/**
 * 키움증권 API 토큰 관리 서비스
 * 
 * Redis 기반으로 키움증권 API 토큰을 캐싱하고 관리
 * - 토큰 자동 갱신 및 만료 처리
 * - 사용자별 토큰 관리
 * - TTL 기반 토큰 라이프사이클 관리
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class KiwoomTokenService {

    private final RedisTemplate<String, Object> redisTemplate;

    // Redis 키 패턴
    private static final String TOKEN_KEY_PREFIX = "kiwoom:token:";
    private static final String TOKEN_INFO_KEY_PREFIX = "kiwoom:token_info:";
    private static final String USER_TOKEN_MAPPING_KEY_PREFIX = "kiwoom:user_token:";

    // 토큰 기본 설정
    private static final Duration DEFAULT_TOKEN_TTL = Duration.ofHours(4); // 4시간
    private static final Duration TOKEN_REFRESH_THRESHOLD = Duration.ofMinutes(30); // 30분 전 갱신

    /**
     * 키움증권 API 토큰 저장
     */
    public void storeToken(String userId, String kiwoomAccountId, KiwoomToken token) {
        try {
            log.info("Storing Kiwoom token for user: {}, account: {}", userId, kiwoomAccountId);

            String tokenKey = buildTokenKey(userId, kiwoomAccountId);
            String tokenInfoKey = buildTokenInfoKey(userId, kiwoomAccountId);
            String userTokenMappingKey = buildUserTokenMappingKey(userId);

            // 1. 토큰 저장 (TTL 설정)
            redisTemplate.opsForValue().set(tokenKey, token.getAccessToken(), DEFAULT_TOKEN_TTL);

            // 2. 토큰 메타데이터 저장
            TokenInfo tokenInfo = TokenInfo.builder()
                    .userId(userId)
                    .kiwoomAccountId(kiwoomAccountId)
                    .tokenType(token.getTokenType())
                    .expiresIn(token.getExpiresIn())
                    .issuedAt(Instant.now())
                    .expiresAt(Instant.now().plusSeconds(token.getExpiresIn()))
                    .refreshToken(token.getRefreshToken())
                    .scope(token.getScope())
                    .build();

            redisTemplate.opsForValue().set(tokenInfoKey, tokenInfo, DEFAULT_TOKEN_TTL);

            // 3. 사용자-토큰 매핑 저장
            redisTemplate.opsForValue().set(userTokenMappingKey, kiwoomAccountId, DEFAULT_TOKEN_TTL);

            log.info("Successfully stored Kiwoom token for user: {}, expires at: {}", 
                    userId, tokenInfo.getExpiresAt());

        } catch (Exception e) {
            log.error("Failed to store Kiwoom token for user: {}", userId, e);
            throw new TokenManagementException("Failed to store token", e);
        }
    }

    /**
     * 키움증권 API 토큰 조회
     */
    public Optional<String> getToken(String userId, String kiwoomAccountId) {
        try {
            log.debug("Retrieving Kiwoom token for user: {}, account: {}", userId, kiwoomAccountId);

            String tokenKey = buildTokenKey(userId, kiwoomAccountId);
            String token = (String) redisTemplate.opsForValue().get(tokenKey);

            if (token != null) {
                // 토큰 만료 임박 확인
                checkTokenExpiration(userId, kiwoomAccountId);
                log.debug("Successfully retrieved Kiwoom token for user: {}", userId);
                return Optional.of(token);
            } else {
                log.debug("No Kiwoom token found for user: {}", userId);
                return Optional.empty();
            }

        } catch (Exception e) {
            log.error("Failed to retrieve Kiwoom token for user: {}", userId, e);
            return Optional.empty();
        }
    }

    /**
     * 토큰 메타데이터 조회
     */
    public Optional<TokenInfo> getTokenInfo(String userId, String kiwoomAccountId) {
        try {
            log.debug("Retrieving Kiwoom token info for user: {}", userId);

            String tokenInfoKey = buildTokenInfoKey(userId, kiwoomAccountId);
            TokenInfo tokenInfo = (TokenInfo) redisTemplate.opsForValue().get(tokenInfoKey);

            if (tokenInfo != null) {
                log.debug("Successfully retrieved token info for user: {}", userId);
                return Optional.of(tokenInfo);
            } else {
                log.debug("No token info found for user: {}", userId);
                return Optional.empty();
            }

        } catch (Exception e) {
            log.error("Failed to retrieve token info for user: {}", userId, e);
            return Optional.empty();
        }
    }

    /**
     * 토큰 갱신 필요 여부 확인
     */
    public boolean needsRefresh(String userId, String kiwoomAccountId) {
        try {
            Optional<TokenInfo> tokenInfoOpt = getTokenInfo(userId, kiwoomAccountId);
            
            if (tokenInfoOpt.isEmpty()) {
                return true; // 토큰이 없으면 갱신 필요
            }

            TokenInfo tokenInfo = tokenInfoOpt.get();
            Instant now = Instant.now();
            Instant refreshThreshold = tokenInfo.getExpiresAt().minus(TOKEN_REFRESH_THRESHOLD);

            boolean needsRefresh = now.isAfter(refreshThreshold);
            
            if (needsRefresh) {
                log.info("Token refresh needed for user: {}, expires at: {}", 
                        userId, tokenInfo.getExpiresAt());
            }

            return needsRefresh;

        } catch (Exception e) {
            log.error("Failed to check token refresh need for user: {}", userId, e);
            return true; // 에러 시 안전하게 갱신 필요로 판단
        }
    }

    /**
     * 토큰 무효화 (로그아웃, 계정 변경 시)
     */
    public void invalidateToken(String userId, String kiwoomAccountId) {
        try {
            log.info("Invalidating Kiwoom token for user: {}, account: {}", userId, kiwoomAccountId);

            String tokenKey = buildTokenKey(userId, kiwoomAccountId);
            String tokenInfoKey = buildTokenInfoKey(userId, kiwoomAccountId);
            String userTokenMappingKey = buildUserTokenMappingKey(userId);

            // 모든 관련 키 삭제
            redisTemplate.delete(tokenKey);
            redisTemplate.delete(tokenInfoKey);
            redisTemplate.delete(userTokenMappingKey);

            log.info("Successfully invalidated Kiwoom token for user: {}", userId);

        } catch (Exception e) {
            log.error("Failed to invalidate token for user: {}", userId, e);
            throw new TokenManagementException("Failed to invalidate token", e);
        }
    }

    /**
     * 사용자의 모든 토큰 조회
     */
    public Optional<String> getUserKiwoomAccount(String userId) {
        try {
            String userTokenMappingKey = buildUserTokenMappingKey(userId);
            String kiwoomAccountId = (String) redisTemplate.opsForValue().get(userTokenMappingKey);
            
            return Optional.ofNullable(kiwoomAccountId);
        } catch (Exception e) {
            log.error("Failed to get user Kiwoom account for user: {}", userId, e);
            return Optional.empty();
        }
    }

    /**
     * 토큰 TTL 연장
     */
    public void extendTokenTTL(String userId, String kiwoomAccountId, Duration additionalTime) {
        try {
            log.info("Extending token TTL for user: {}, additional time: {}", userId, additionalTime);

            String tokenKey = buildTokenKey(userId, kiwoomAccountId);
            String tokenInfoKey = buildTokenInfoKey(userId, kiwoomAccountId);

            // 현재 TTL 조회
            Long currentTtl = redisTemplate.getExpire(tokenKey, TimeUnit.SECONDS);
            if (currentTtl != null && currentTtl > 0) {
                Duration newTtl = Duration.ofSeconds(currentTtl).plus(additionalTime);
                redisTemplate.expire(tokenKey, newTtl);
                redisTemplate.expire(tokenInfoKey, newTtl);
                
                log.info("Extended token TTL for user: {}, new TTL: {} seconds", userId, newTtl.getSeconds());
            } else {
                log.warn("Token not found or already expired for user: {}", userId);
            }

        } catch (Exception e) {
            log.error("Failed to extend token TTL for user: {}", userId, e);
        }
    }

    /**
     * 토큰 통계 조회
     */
    public TokenStatistics getTokenStatistics() {
        try {
            // 패턴으로 모든 토큰 키 조회
            var tokenKeys = redisTemplate.keys(TOKEN_KEY_PREFIX + "*");
            var tokenInfoKeys = redisTemplate.keys(TOKEN_INFO_KEY_PREFIX + "*");

            long totalTokens = tokenKeys != null ? tokenKeys.size() : 0;
            long totalTokenInfos = tokenInfoKeys != null ? tokenInfoKeys.size() : 0;

            // 만료 임박 토큰 수 계산 (실제로는 더 효율적인 방법 필요)
            long expiringTokens = 0;
            if (tokenInfoKeys != null) {
                for (String key : tokenInfoKeys) {
                    TokenInfo info = (TokenInfo) redisTemplate.opsForValue().get(key);
                    if (info != null && needsRefreshByTokenInfo(info)) {
                        expiringTokens++;
                    }
                }
            }

            return TokenStatistics.builder()
                    .totalTokens(totalTokens)
                    .activeTokens(totalTokenInfos)
                    .expiringTokens(expiringTokens)
                    .build();

        } catch (Exception e) {
            log.error("Failed to get token statistics", e);
            return TokenStatistics.builder().build();
        }
    }

    // Private helper methods

    private String buildTokenKey(String userId, String kiwoomAccountId) {
        return TOKEN_KEY_PREFIX + userId + ":" + kiwoomAccountId;
    }

    private String buildTokenInfoKey(String userId, String kiwoomAccountId) {
        return TOKEN_INFO_KEY_PREFIX + userId + ":" + kiwoomAccountId;
    }

    private String buildUserTokenMappingKey(String userId) {
        return USER_TOKEN_MAPPING_KEY_PREFIX + userId;
    }

    private void checkTokenExpiration(String userId, String kiwoomAccountId) {
        try {
            if (needsRefresh(userId, kiwoomAccountId)) {
                log.warn("Token for user {} is expiring soon and needs refresh", userId);
                // 여기서 토큰 갱신 이벤트를 발행할 수 있음
            }
        } catch (Exception e) {
            log.error("Failed to check token expiration for user: {}", userId, e);
        }
    }

    private boolean needsRefreshByTokenInfo(TokenInfo tokenInfo) {
        Instant now = Instant.now();
        Instant refreshThreshold = tokenInfo.getExpiresAt().minus(TOKEN_REFRESH_THRESHOLD);
        return now.isAfter(refreshThreshold);
    }

    // Inner classes

    @lombok.Builder
    @lombok.Data
    public static class KiwoomToken {
        private String accessToken;
        private String tokenType;
        private Long expiresIn;
        private String refreshToken;
        private String scope;
    }

    @lombok.Builder
    @lombok.Data
    public static class TokenInfo {
        private String userId;
        private String kiwoomAccountId;
        private String tokenType;
        private Long expiresIn;
        private Instant issuedAt;
        private Instant expiresAt;
        private String refreshToken;
        private String scope;
    }

    @lombok.Builder
    @lombok.Data
    public static class TokenStatistics {
        @lombok.Builder.Default
        private long totalTokens = 0;
        @lombok.Builder.Default
        private long activeTokens = 0;
        @lombok.Builder.Default
        private long expiringTokens = 0;
    }

    /**
     * 토큰 관리 예외
     */
    public static class TokenManagementException extends RuntimeException {
        public TokenManagementException(String message) {
            super(message);
        }

        public TokenManagementException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}