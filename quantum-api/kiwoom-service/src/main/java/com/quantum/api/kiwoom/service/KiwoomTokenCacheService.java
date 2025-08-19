package com.quantum.api.kiwoom.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.api.kiwoom.dto.auth.CachedTokenInfo;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.ReactiveRedisTemplate;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

/**
 * 키움증권 토큰 Redis 캐시 서비스 (Reactive)
 * 
 * 토큰 정책:
 * - 24시간 만료
 * - 6시간 이내 재요청 시 기존 토큰 재활용
 * - 6시간 후 재요청 시 새 토큰 발급 후 기존 토큰 폐기
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class KiwoomTokenCacheService {
    
    private final ReactiveRedisTemplate<String, Object> reactiveRedisTemplate;
    private final ObjectMapper objectMapper;
    
    private static final String TOKEN_KEY_PREFIX = "kiwoom:token:";
    private static final long TOKEN_TTL_HOURS = 24;
    
    /**
     * 앱키별 토큰 캐시 키 생성
     */
    private String getTokenCacheKey(String appkey) {
        return TOKEN_KEY_PREFIX + appkey;
    }
    
    /**
     * 캐시된 토큰 정보 조회 (Reactive)
     */
    public Mono<CachedTokenInfo> getCachedToken(String appkey) {
        String key = getTokenCacheKey(appkey);
        
        return reactiveRedisTemplate.opsForValue().get(key)
                .cast(String.class)
                .flatMap(cached -> {
                    try {
                        CachedTokenInfo tokenInfo = objectMapper.readValue(cached, CachedTokenInfo.class);
                        
                        log.debug("캐시된 토큰 조회 - appkey: {}***, 발급시간: {}, 만료시간: {}", 
                                appkey.substring(0, Math.min(5, appkey.length())), 
                                tokenInfo.getIssuedAt(), 
                                tokenInfo.getExpiresAt());
                        
                        return Mono.just(tokenInfo);
                        
                    } catch (Exception e) {
                        log.error("캐시된 토큰 역직렬화 실패 - appkey: {}***, error: {}", 
                                appkey.substring(0, Math.min(5, appkey.length())), e.getMessage());
                        return Mono.empty();
                    }
                })
                .doOnNext(tokenInfo -> log.debug("캐시된 토큰 조회 성공"))
                .switchIfEmpty(Mono.fromRunnable(() -> 
                    log.debug("캐시된 토큰 없음 - appkey: {}***", appkey.substring(0, Math.min(5, appkey.length())))))
                .onErrorResume(error -> {
                    log.error("캐시된 토큰 조회 실패 - appkey: {}***, error: {}", 
                            appkey.substring(0, Math.min(5, appkey.length())), error.getMessage());
                    return Mono.empty();
                });
    }
    
    /**
     * 토큰 정보 캐시에 저장 (Reactive)
     */
    public Mono<Void> cacheToken(CachedTokenInfo tokenInfo) {
        return Mono.fromCallable(() -> {
            try {
                String key = getTokenCacheKey(tokenInfo.getAppkey());
                String jsonValue = objectMapper.writeValueAsString(tokenInfo);
                return new CacheData(key, jsonValue, tokenInfo);
            } catch (Exception e) {
                log.error("토큰 직렬화 실패 - appkey: {}***, error: {}", 
                        tokenInfo.getAppkey().substring(0, Math.min(5, tokenInfo.getAppkey().length())), 
                        e.getMessage());
                throw new RuntimeException("토큰 직렬화에 실패했습니다", e);
            }
        })
        .flatMap(cacheData -> 
            reactiveRedisTemplate.opsForValue()
                    .set(cacheData.key, cacheData.jsonValue, Duration.ofHours(TOKEN_TTL_HOURS))
                    .doOnSuccess(success -> {
                        if (Boolean.TRUE.equals(success)) {
                            log.info("토큰 캐시 저장 - appkey: {}***, token: {}***, 만료시간: {}", 
                                    cacheData.tokenInfo.getAppkey().substring(0, Math.min(5, cacheData.tokenInfo.getAppkey().length())),
                                    cacheData.tokenInfo.getToken().substring(0, Math.min(8, cacheData.tokenInfo.getToken().length())),
                                    cacheData.tokenInfo.getExpiresAt());
                        } else {
                            log.warn("토큰 캐시 저장 실패 - Redis 반환값: {}", success);
                        }
                    })
                    .then()
        )
        .onErrorMap(error -> {
            log.error("토큰 캐시 저장 실패", error);
            return new RuntimeException("토큰 캐시 저장에 실패했습니다", error);
        });
    }
    
    /**
     * 캐시 데이터 전달용 내부 클래스
     */
    private static class CacheData {
        final String key;
        final String jsonValue;
        final CachedTokenInfo tokenInfo;
        
        CacheData(String key, String jsonValue, CachedTokenInfo tokenInfo) {
            this.key = key;
            this.jsonValue = jsonValue;
            this.tokenInfo = tokenInfo;
        }
    }
    
    /**
     * 특정 앱키의 캐시된 토큰 삭제 (Reactive)
     */
    public Mono<Void> evictToken(String appkey) {
        String key = getTokenCacheKey(appkey);
        
        return reactiveRedisTemplate.delete(key)
                .doOnNext(deleted -> 
                    log.info("토큰 캐시 삭제 - appkey: {}***, 삭제 개수: {}", 
                            appkey.substring(0, Math.min(5, appkey.length())), deleted))
                .then()
                .onErrorResume(error -> {
                    log.error("토큰 캐시 삭제 실패 - appkey: {}***, error: {}", 
                            appkey.substring(0, Math.min(5, appkey.length())), error.getMessage());
                    return Mono.error(new RuntimeException("토큰 캐시 삭제에 실패했습니다", error));
                });
    }
    
    /**
     * 특정 토큰으로 캐시에서 삭제 (토큰 폐기 시 사용) - Reactive
     */
    public Mono<Void> evictTokenByValue(String token) {
        String pattern = TOKEN_KEY_PREFIX + "*";
        
        return reactiveRedisTemplate.keys(pattern)
                .cast(String.class)
                .flatMap(key -> 
                    reactiveRedisTemplate.opsForValue().get(key)
                            .cast(String.class)
                            .flatMap(cached -> {
                                try {
                                    CachedTokenInfo tokenInfo = objectMapper.readValue(cached, CachedTokenInfo.class);
                                    
                                    if (token.equals(tokenInfo.getToken())) {
                                        // 토큰 일치하면 삭제
                                        return reactiveRedisTemplate.delete(key)
                                                .doOnNext(deleted -> 
                                                    log.info("토큰값으로 캐시 삭제 - token: {}***, key: {}, 삭제 개수: {}", 
                                                            token.substring(0, Math.min(8, token.length())), key, deleted))
                                                .then(Mono.just(true)); // 찾았다는 신호
                                    } else {
                                        return Mono.just(false); // 일치하지 않음
                                    }
                                } catch (Exception e) {
                                    log.warn("토큰 비교 중 오류 - key: {}, error: {}", key, e.getMessage());
                                    return Mono.just(false);
                                }
                            })
                            .onErrorReturn(false)
                )
                .filter(found -> found) // 삭제된 경우만 필터링
                .hasElements() // 하나라도 삭제되었는지 확인
                .flatMap(foundAndDeleted -> {
                    if (!foundAndDeleted) {
                        log.debug("삭제할 토큰을 캐시에서 찾지 못함 - token: {}***", 
                                token.substring(0, Math.min(8, token.length())));
                    }
                    return Mono.<Void>empty();
                })
                .onErrorResume(error -> {
                    log.error("토큰값으로 캐시 삭제 실패 - token: {}***, error: {}", 
                            token.substring(0, Math.min(8, token.length())), error.getMessage());
                    return Mono.error(new RuntimeException("토큰 캐시 삭제에 실패했습니다", error));
                });
    }
}