package com.quantum.batch.service;

import com.quantum.core.domain.model.kis.KisToken;
import com.quantum.core.domain.port.repository.KisTokenRepository;
import com.quantum.kis.service.KisRateLimiter;
import com.quantum.kis.service.KisTokenProvider;
import com.quantum.kis.client.KisFeignClient;
import com.quantum.kis.model.KisTokenResponse;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * KIS API 토큰 관리 서비스
 * 1분당 1회 제한 대응을 위한 DB 기반 토큰 관리
 * 
 * 다른 배치 프로세서에서도 공통으로 사용할 수 있는 토큰 관리 서비스입니다.
 * 필요시 다른 모듈(quantum-api 등)에서도 유사한 서비스를 만들어 사용하세요.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class KisTokenService implements KisTokenProvider {

    private final KisFeignClient kisFeignClient;
    private final KisTokenRepository kisTokenRepository;
    private final KisRateLimiter kisRateLimiter;

    @Value("${kis.api.app-key}")
    private String appKey;

    @Value("${kis.api.app-secret}")
    private String appSecret;

    /**
     * 유효한 액세스 토큰 조회 (DB 우선, 없으면 API 호출)
     * 
     * 이 메서드는 thread-safe하며 동시 호출시에도 안전합니다.
     * KIS API의 1분당 1회 제한을 자동으로 준수합니다.
     * 
     * @return 유효한 액세스 토큰, 실패시 null
     */
    public String getValidAccessToken() {
        try {
            // 1. DB에서 활성화된 유효한 토큰 조회
            Optional<KisToken> existingToken = kisTokenRepository.findActiveValidToken();
            
            if (existingToken.isPresent() && !existingToken.get().isExpired()) {
                log.debug("KIS Token Service: Using existing valid token from DB");
                return existingToken.get().getAccessToken();
            }
            
            // 2. 기존 토큰이 없거나 만료된 경우 API로 새 토큰 발급
            log.info("KIS Token Service: Requesting new access token from KIS API");
            KisTokenResponse tokenResponse = requestNewAccessToken();
            
            if (tokenResponse == null || tokenResponse.accessToken() == null) {
                log.error("KIS Token Service: Failed to get new access token from API");
                return null;
            }
            
            // 3. 기존 토큰들 비활성화 후 새 토큰 저장
            kisTokenRepository.deactivateAllTokens();
            
            KisToken newToken = KisToken.fromKisResponse(
                tokenResponse.tokenType(),
                tokenResponse.accessToken(),
                tokenResponse.accessTokenExpired(),
                tokenResponse.expiresIn()
            );
            
            KisToken savedToken = kisTokenRepository.save(newToken);
            log.info("KIS Token Service: New access token saved to DB, expires at: {}", 
                savedToken.getExpiresAt());
            
            return savedToken.getAccessToken();
            
        } catch (Exception e) {
            log.error("KIS Token Service: Error getting valid access token", e);
            return null;
        }
    }
    
    /**
     * KIS API에서 새로운 액세스 토큰 요청
     * 
     * @return KIS 토큰 응답, 실패시 null
     */
    public KisTokenResponse requestNewAccessToken() {
        try {
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("grant_type", "client_credentials");
            requestBody.put("appkey", appKey);
            requestBody.put("appsecret", appSecret);
            
            KisTokenResponse response = kisFeignClient.getAccessToken(requestBody);
            log.debug("KIS Token Service: Successfully requested new token from API");
            
            return response;
            
        } catch (Exception e) {
            log.error("KIS Token Service: Error requesting new access token from API", e);
            return null;
        }
    }
    
    /**
     * 현재 저장된 토큰 정보 조회 (디버깅/모니터링 용)
     * 
     * @return 활성화된 토큰 정보, 없으면 Optional.empty()
     */
    public Optional<KisToken> getCurrentToken() {
        try {
            return kisTokenRepository.findActiveValidToken();
        } catch (Exception e) {
            log.error("KIS Token Service: Error getting current token info", e);
            return Optional.empty();
        }
    }
    
    /**
     * 모든 토큰 강제 만료 (토큰 재발급 강제 실행용)
     * 
     * 주로 테스트나 운영상 필요에 의해 토큰을 강제로 갱신할 때 사용합니다.
     */
    public void forceTokenRefresh() {
        try {
            log.info("KIS Token Service: Force refreshing all tokens");
            kisTokenRepository.deactivateAllTokens();
            
            // 만료된 토큰들 정리
            kisTokenRepository.deleteExpiredTokens();
            
        } catch (Exception e) {
            log.error("KIS Token Service: Error during force token refresh", e);
        }
    }
    
    /**
     * 토큰 상태 체크 (헬스체크용)
     * 
     * @return 토큰이 유효하면 true, 아니면 false
     */
    public boolean isTokenValid() {
        try {
            Optional<KisToken> token = kisTokenRepository.findActiveValidToken();
            return token.isPresent() && !token.get().isExpired();
        } catch (Exception e) {
            log.error("KIS Token Service: Error checking token validity", e);
            return false;
        }
    }
    
    /**
     * API 호출 전 Rate Limiting 체크
     * KIS API 공식 제한: 실전투자 20건/초, 모의투자 2건/초
     * 
     * @param apiEndpoint API 엔드포인트 구분자
     * @return 호출 가능하면 true, 제한에 걸리면 false
     */
    public boolean checkRateLimit(String apiEndpoint) {
        return kisRateLimiter.tryAcquire(apiEndpoint, false);
    }
    
    /**
     * 강제 대기 후 API 호출 (재시도 포함)
     * 
     * @param apiEndpoint API 엔드포인트 구분자
     * @return 호출 가능하면 true, 최종 실패시 false
     */
    public boolean acquireWithWait(String apiEndpoint) {
        return kisRateLimiter.acquireWithWait(apiEndpoint, false);
    }
    
    /**
     * Rate Limiter 상태 조회 (모니터링용)
     * 
     * @param apiEndpoint API 엔드포인트 구분자
     * @return Rate Limit 상태 정보
     */
    public KisRateLimiter.RateLimitStatus getRateLimitStatus(String apiEndpoint) {
        return kisRateLimiter.getStatus(apiEndpoint);
    }
}