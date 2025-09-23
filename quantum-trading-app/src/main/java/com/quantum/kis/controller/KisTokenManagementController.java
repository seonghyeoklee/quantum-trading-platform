package com.quantum.kis.controller;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.TokenInfo;
import com.quantum.kis.service.KisTokenManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * KIS 토큰 관리 REST API
 */
@RestController
@RequestMapping("/api/kis/token-management")
public class KisTokenManagementController {

    private static final Logger log = LoggerFactory.getLogger(KisTokenManagementController.class);

    private final KisTokenManager tokenManager;

    public KisTokenManagementController(KisTokenManager tokenManager) {
        this.tokenManager = tokenManager;
    }

    /**
     * 유효한 액세스 토큰 조회 (자동 재발급 포함)
     * @param environment KIS 환경
     * @return 액세스 토큰
     */
    @GetMapping("/access-token")
    public ResponseEntity<String> getValidAccessToken(
            @RequestParam KisEnvironment environment) {

        log.info("유효한 액세스 토큰 요청 - 환경: {}", environment);

        try {
            String token = tokenManager.getValidAccessToken(environment);
            return ResponseEntity.ok(token);
        } catch (Exception e) {
            log.error("액세스 토큰 조회 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 유효한 웹소켓 키 조회 (자동 재발급 포함)
     * @param environment KIS 환경
     * @return 웹소켓 키
     */
    @GetMapping("/websocket-key")
    public ResponseEntity<String> getValidWebSocketKey(
            @RequestParam KisEnvironment environment) {

        log.info("유효한 웹소켓 키 요청 - 환경: {}", environment);

        try {
            String key = tokenManager.getValidWebSocketKey(environment);
            return ResponseEntity.ok(key);
        } catch (Exception e) {
            log.error("웹소켓 키 조회 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 특정 환경의 액세스 토큰 강제 재발급
     * @param environment KIS 환경
     * @return 새로운 액세스 토큰
     */
    @PostMapping("/refresh/access-token")
    public ResponseEntity<String> forceRefreshAccessToken(
            @RequestParam KisEnvironment environment) {

        log.info("액세스 토큰 강제 재발급 요청 - 환경: {}", environment);

        try {
            String token = tokenManager.refreshAccessToken(environment);
            return ResponseEntity.ok(token);
        } catch (Exception e) {
            log.error("액세스 토큰 강제 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 특정 환경의 웹소켓 키 강제 재발급
     * @param environment KIS 환경
     * @return 새로운 웹소켓 키
     */
    @PostMapping("/refresh/websocket-key")
    public ResponseEntity<String> forceRefreshWebSocketKey(
            @RequestParam KisEnvironment environment) {

        log.info("웹소켓 키 강제 재발급 요청 - 환경: {}", environment);

        try {
            String key = tokenManager.refreshWebSocketKey(environment);
            return ResponseEntity.ok(key);
        } catch (Exception e) {
            log.error("웹소켓 키 강제 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 모든 환경의 모든 토큰 강제 재발급
     * @return 성공 메시지
     */
    @PostMapping("/refresh/all")
    public ResponseEntity<String> forceRefreshAllTokens() {
        log.info("모든 토큰 강제 재발급 요청");

        try {
            tokenManager.refreshAllTokens();
            return ResponseEntity.ok("모든 토큰 재발급 완료");
        } catch (Exception e) {
            log.error("모든 토큰 강제 재발급 실패 - 오류: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body("토큰 재발급 실패: " + e.getMessage());
        }
    }

    /**
     * 현재 캐시된 토큰 상태 조회
     * @return 토큰 캐시 상태
     */
    @GetMapping("/status")
    public ResponseEntity<Map<String, TokenInfo>> getTokenStatus() {
        log.info("토큰 상태 조회 요청");

        try {
            Map<String, TokenInfo> status = tokenManager.getTokenCacheStatus();
            return ResponseEntity.ok(status);
        } catch (Exception e) {
            log.error("토큰 상태 조회 실패 - 오류: {}", e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 만료된 토큰 정리
     * @return 성공 메시지
     */
    @PostMapping("/cleanup")
    public ResponseEntity<String> cleanupExpiredTokens() {
        log.info("만료된 토큰 정리 요청");

        try {
            tokenManager.cleanupExpiredTokens();
            return ResponseEntity.ok("만료된 토큰 정리 완료");
        } catch (Exception e) {
            log.error("만료된 토큰 정리 실패 - 오류: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body("토큰 정리 실패: " + e.getMessage());
        }
    }
}