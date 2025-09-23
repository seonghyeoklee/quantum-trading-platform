package com.quantum.kis.controller;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.WebSocketKeyResponse;
import com.quantum.kis.service.KisTokenService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * KIS 토큰 발급 REST API
 */
@RestController
@RequestMapping("/api/kis/token")
public class KisTokenController {

    private static final Logger log = LoggerFactory.getLogger(KisTokenController.class);

    private final KisTokenService tokenService;

    public KisTokenController(KisTokenService tokenService) {
        this.tokenService = tokenService;
    }

    /**
     * 액세스 토큰 발급
     * @param environment KIS 환경 (PROD/VPS)
     * @return 액세스 토큰 응답
     */
    @PostMapping("/access")
    public ResponseEntity<AccessTokenResponse> issueAccessToken(
            @RequestParam KisEnvironment environment) {

        log.info("액세스 토큰 발급 요청 - 환경: {}", environment);

        try {
            AccessTokenResponse response = tokenService.getAccessToken(environment);
            log.info("액세스 토큰 발급 완료 - 환경: {}, 토큰 타입: {}",
                    environment, response.tokenType());
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("액세스 토큰 발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 웹소켓 키 발급
     * @param environment KIS 환경 (PROD/VPS)
     * @return 웹소켓 키 응답
     */
    @PostMapping("/websocket")
    public ResponseEntity<WebSocketKeyResponse> issueWebSocketKey(
            @RequestParam KisEnvironment environment) {

        log.info("웹소켓 키 발급 요청 - 환경: {}", environment);

        try {
            WebSocketKeyResponse response = tokenService.getWebSocketKey(environment);
            log.info("웹소켓 키 발급 완료 - 환경: {}", environment);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("웹소켓 키 발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 토큰 상태 확인
     * @return 서비스 상태
     */
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("KIS Token Service is running");
    }
}