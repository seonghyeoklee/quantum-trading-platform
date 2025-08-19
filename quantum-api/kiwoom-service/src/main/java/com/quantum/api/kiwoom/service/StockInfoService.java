package com.quantum.api.kiwoom.service;

import com.quantum.api.kiwoom.client.KiwoomApiClient;
import com.quantum.api.kiwoom.dto.stock.StockInfoRequest;
import com.quantum.api.kiwoom.dto.stock.StockInfoResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.Map;

/**
 * 키움증권 주식 기본정보 서비스
 * API: /api/dostk/stkinfo (ka10001)
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class StockInfoService {
    
    private final WebClient kiwoomWebClient;
    private final AuthService authService;
    private final KiwoomTokenCacheService tokenCacheService;
    
    // API 엔드포인트
    private static final String STOCK_INFO_ENDPOINT = "/api/dostk/stkinfo";
    private static final String API_ID = "ka10001";
    
    /**
     * 주식 기본정보 조회
     * 
     * @param stockCode 종목코드 (예: 005930)
     * @param accessToken 접근토큰
     * @return 주식 기본정보
     */
    public Mono<StockInfoResponse> getStockInfo(String stockCode, String accessToken) {
        return getStockInfo(stockCode, accessToken, "N", "");
    }
    
    /**
     * 주식 기본정보 조회 (연속조회 지원)
     * 
     * @param stockCode 종목코드
     * @param accessToken 접근토큰
     * @param contYn 연속조회여부 (Y/N)
     * @param nextKey 연속조회키
     * @return 주식 기본정보
     */
    public Mono<StockInfoResponse> getStockInfo(String stockCode, String accessToken, 
                                                 String contYn, String nextKey) {
        
        // 요청 DTO 생성
        StockInfoRequest request = StockInfoRequest.builder()
                .stockCode(stockCode)
                .build();
        
        // 요청 검증
        try {
            request.validate();
        } catch (IllegalArgumentException e) {
            log.error("주식 기본정보 요청 검증 실패: {}", e.getMessage());
            return Mono.error(e);
        }
        
        log.info("주식 기본정보 조회 시작 - 종목코드: {}, 연속조회: {}", stockCode, contYn);
        
        return kiwoomWebClient.post()
                .uri(STOCK_INFO_ENDPOINT)
                .header(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .header("api-id", API_ID)
                .header("cont-yn", contYn != null ? contYn : "N")
                .header("next-key", nextKey != null ? nextKey : "")
                .bodyValue(request)
                .retrieve()
                .onStatus(status -> status.is4xxClientError() || status.is5xxServerError(),
                    response -> response.bodyToMono(String.class)
                            .flatMap(body -> {
                                log.error("주식 기본정보 조회 실패 - 상태코드: {}, 응답: {}", 
                                        response.statusCode(), body);
                                return Mono.error(new RuntimeException(
                                        "주식 기본정보 조회 실패: " + response.statusCode()));
                            }))
                .toEntity(StockInfoResponse.class)
                .timeout(Duration.ofSeconds(10))
                .map(responseEntity -> {
                    // 응답 헤더 로깅
                    HttpHeaders headers = responseEntity.getHeaders();
                    log.debug("응답 헤더 - cont-yn: {}, next-key: {}, api-id: {}",
                            headers.getFirst("cont-yn"),
                            headers.getFirst("next-key"),
                            headers.getFirst("api-id"));
                    
                    StockInfoResponse body = responseEntity.getBody();
                    if (body != null) {
                        log.info("주식 기본정보 조회 성공 - 종목: {} ({}), 현재가: {}, 등락율: {}%",
                                body.getStockName(), body.getStockCode(),
                                body.getCurrentPrice(), body.getChangeRate());
                    }
                    
                    return body;
                })
                .doOnError(error -> log.error("주식 기본정보 조회 실패", error));
    }
    
    /**
     * 주식 기본정보 조회 (토큰 자동 관리)
     * 
     * @param stockCode 종목코드
     * @param appKey 앱키
     * @param appSecret 앱시크릿
     * @return 주식 기본정보
     */
    public Mono<StockInfoResponse> getStockInfoWithAuth(String stockCode, 
                                                        String appKey, 
                                                        String appSecret) {
        
        log.info("주식 기본정보 조회 (토큰 자동 관리) - 종목코드: {}", stockCode);
        
        // 1. 캐시된 토큰 조회 또는 새 토큰 발급
        return tokenCacheService.getCachedToken(appKey)
                .flatMap(cachedToken -> {
                    if (cachedToken != null && !cachedToken.isExpired()) {
                        // 캐시된 토큰 사용
                        log.debug("캐시된 토큰 사용 - 종목코드: {}", stockCode);
                        return Mono.just(cachedToken.getToken());
                    } else {
                        // 새 토큰 발급 필요
                        log.debug("새 토큰 발급 필요 - 종목코드: {}", stockCode);
                        return getNewToken(appKey, appSecret);
                    }
                })
                .switchIfEmpty(getNewToken(appKey, appSecret))
                .flatMap(token -> getStockInfo(stockCode, token))
                .doOnSuccess(response -> 
                    log.info("주식 기본정보 조회 완료 - 종목: {} ({})", 
                            response.getStockName(), response.getStockCode()))
                .onErrorResume(error -> {
                    log.error("주식 기본정보 조회 실패 - 종목코드: {}", stockCode, error);
                    return Mono.error(new RuntimeException("주식 기본정보 조회 실패", error));
                });
    }
    
    /**
     * 여러 종목의 기본정보 일괄 조회
     * 
     * @param stockCodes 종목코드 목록
     * @param accessToken 접근토큰
     * @return 주식 기본정보 목록
     */
    public Mono<Map<String, StockInfoResponse>> getMultipleStockInfo(
            Iterable<String> stockCodes, String accessToken) {
        
        return reactor.core.publisher.Flux.fromIterable(stockCodes)
                .parallel()
                .flatMap(stockCode -> 
                    getStockInfo(stockCode, accessToken)
                            .map(response -> Map.entry(stockCode, response))
                            .onErrorResume(error -> {
                                log.error("종목 {} 조회 실패", stockCode, error);
                                return Mono.empty();
                            })
                )
                .sequential()
                .collectMap(Map.Entry::getKey, Map.Entry::getValue)
                .doOnSuccess(result -> 
                    log.info("여러 종목 기본정보 조회 완료 - 성공: {}/{}", 
                            result.size(), stockCodes));
    }
    
    /**
     * 새 토큰 발급 (내부 메서드)
     */
    private Mono<String> getNewToken(String appKey, String appSecret) {
        return authService.issueKiwoomOAuthToken(
                com.quantum.api.kiwoom.dto.auth.TokenRequest.builder()
                        .grantType("client_credentials")
                        .appkey(appKey)
                        .secretkey(appSecret)
                        .build()
        ).map(tokenResponse -> tokenResponse.getToken());
    }
}