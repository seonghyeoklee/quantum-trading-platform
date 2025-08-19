package com.quantum.api.kiwoom.controller;

import com.quantum.api.kiwoom.dto.auth.TokenRequest;
import com.quantum.api.kiwoom.dto.auth.TokenResponse;
import com.quantum.api.kiwoom.dto.auth.TokenRevokeRequest;
import com.quantum.api.kiwoom.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

/**
 * OAuth 인증 관련 API 컨트롤러 (Reactive)
 * 키움증권 OAuth 2.0 인증 처리
 */
@RestController
@RequiredArgsConstructor
@Slf4j
@Tag(name = "인증", description = "키움증권 OAuth 인증 API")
public class AuthController {
    
    private final AuthService authService;
    
    /**
     * 키움증권 OAuth 2.0 토큰 발급 (키움 API 스펙)
     * POST /oauth2/token
     * 
     * Request Body: {"grant_type": "client_credentials", "appkey": "...", "secretkey": "..."}
     * Response Headers: cont-yn, next-key, api-id
     */
    @PostMapping("/oauth2/token")
    @Operation(
        summary = "접근토큰 발급 (키움 API 스펙)", 
        description = "키움증권 OAuth 2.0 client_credentials 방식 토큰 발급"
    )
    public Mono<ResponseEntity<TokenResponse>> issueOAuthToken(
            @RequestBody TokenRequest request) {
        
        log.info("키움 OAuth 토큰 발급 요청 - grant_type: {}, appkey: {}", 
                request.getGrantType(), 
                request.getAppkey() != null ? request.getAppkey().substring(0, Math.min(5, request.getAppkey().length())) + "***" : "null");
        
        return authService.issueKiwoomOAuthToken(request)
                .map(tokenResponse -> {
                    // 키움 API 스펙에 따른 응답 헤더 설정
                    return ResponseEntity.ok()
                            .header("cont-yn", "N")                    // 연속조회여부 (N: 종료)
                            .header("next-key", "")                    // 다음키 (없음)
                            .header("api-id", "au10001")              // API ID
                            .body(tokenResponse);
                })
                .doOnSuccess(response -> log.info("키움 OAuth 토큰 발급 완료"))
                .doOnError(error -> log.error("키움 OAuth 토큰 발급 실패", error));
    }
    
    /**
     * 키움증권 OAuth 2.0 토큰 폐기 (키움 API 스펙)
     * POST /oauth2/revoke
     * 
     * Request Body: {"appkey": "...", "secretkey": "...", "token": "..."}
     * Response Headers: cont-yn, next-key, api-id
     */
    @PostMapping("/oauth2/revoke")
    @Operation(
        summary = "접근토큰 폐기 (키움 API 스펙)", 
        description = "키움증권 OAuth 2.0 접근토큰 폐기"
    )
    public Mono<ResponseEntity<Void>> revokeOAuthToken(
            @RequestBody TokenRevokeRequest request) {
        
        log.info("키움 OAuth 토큰 폐기 요청 - appkey: {}, token: {}", 
                request.getAppkey() != null ? request.getAppkey().substring(0, Math.min(5, request.getAppkey().length())) + "***" : "null",
                request.getToken() != null ? request.getToken().substring(0, Math.min(8, request.getToken().length())) + "***" : "null");
        
        return authService.revokeKiwoomOAuthToken(request)
                .then(Mono.fromCallable(() -> {
                    // 키움 API 스펙에 따른 응답 헤더 설정
                    return ResponseEntity.noContent()
                            .header("cont-yn", "N")                    // 연속조회여부 (N: 종료)
                            .header("next-key", "")                    // 다음키 (없음)
                            .header("api-id", "au10002")              // API ID (토큰폐기)
                            .<Void>build();
                }))
                .doOnSuccess(response -> log.info("키움 OAuth 토큰 폐기 완료"))
                .doOnError(error -> log.error("키움 OAuth 토큰 폐기 실패", error));
    }
    
    /**
     * 기존 API 호환용 토큰 발급
     * POST /api/v1/auth/token
     */
    @PostMapping("/api/v1/auth/token")
    @Operation(summary = "접근토큰 발급 (호환용)", description = "기존 API 호환을 위한 OAuth 토큰 발급")
    public Mono<ResponseEntity<TokenResponse>> getAccessToken(@RequestBody TokenRequest request) {
        log.info("접근토큰 발급 요청: {}", request.getGrantType());
        return authService.getAccessToken(request)
                .map(ResponseEntity::ok)
                .doOnSuccess(response -> log.info("토큰 발급 완료"))
                .doOnError(error -> log.error("토큰 발급 실패", error));
    }
    
    @PostMapping("/token/refresh")
    @Operation(summary = "접근토큰 갱신", description = "만료된 접근토큰을 리프레시 토큰으로 갱신")
    public Mono<ResponseEntity<TokenResponse>> refreshToken(@RequestHeader("Authorization") String refreshToken) {
        log.info("접근토큰 갱신 요청");
        return authService.refreshAccessToken(refreshToken)
                .map(ResponseEntity::ok)
                .doOnSuccess(response -> log.info("토큰 갱신 완료"))
                .doOnError(error -> log.error("토큰 갱신 실패", error));
    }
    
    @DeleteMapping("/token")
    @Operation(summary = "접근토큰 폐기", description = "발급받은 접근토큰 폐기")
    public Mono<ResponseEntity<Void>> revokeToken(@RequestHeader("Authorization") String accessToken) {
        log.info("접근토큰 폐기 요청");
        return authService.revokeToken(accessToken)
                .then(Mono.just(ResponseEntity.noContent().<Void>build()))
                .doOnSuccess(response -> log.info("토큰 폐기 완료"))
                .doOnError(error -> log.error("토큰 폐기 실패", error));
    }
}