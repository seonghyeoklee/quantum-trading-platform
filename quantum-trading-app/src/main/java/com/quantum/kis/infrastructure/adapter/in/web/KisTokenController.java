package com.quantum.kis.infrastructure.adapter.in.web;

import com.quantum.kis.application.port.in.RefreshTokenUseCase;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.WebSocketKeyResponse;
import com.quantum.kis.infrastructure.adapter.in.web.dto.TokenIssueResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * KIS 토큰 발급 REST API
 * Infrastructure Layer의 Inbound Adapter
 */
@RestController
@RequestMapping("/api/kis/token")
public class KisTokenController {

    private static final Logger log = LoggerFactory.getLogger(KisTokenController.class);

    private final RefreshTokenUseCase refreshTokenUseCase;

    public KisTokenController(RefreshTokenUseCase refreshTokenUseCase) {
        this.refreshTokenUseCase = refreshTokenUseCase;
    }

    /**
     * 액세스 토큰 발급
     * @param environment KIS 환경 (PROD/VPS)
     * @return 토큰 발급 응답
     */
    @PostMapping("/access")
    public ResponseEntity<TokenIssueResponse> issueAccessToken(
            @RequestParam KisEnvironment environment) {

        log.info("액세스 토큰 발급 요청 - 환경: {}", environment);

        try {
            String token = refreshTokenUseCase.refreshAccessToken(environment);
            TokenIssueResponse response = new TokenIssueResponse(
                    token,
                    "ACCESS_TOKEN",
                    environment.name(),
                    "토큰 발급 성공"
            );

            log.info("액세스 토큰 발급 완료 - 환경: {}", environment);
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("액세스 토큰 발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * 웹소켓 키 발급
     * @param environment KIS 환경 (PROD/VPS)
     * @return 토큰 발급 응답
     */
    @PostMapping("/websocket")
    public ResponseEntity<TokenIssueResponse> issueWebSocketKey(
            @RequestParam KisEnvironment environment) {

        log.info("웹소켓 키 발급 요청 - 환경: {}", environment);

        try {
            String key = refreshTokenUseCase.refreshWebSocketKey(environment);
            TokenIssueResponse response = new TokenIssueResponse(
                    key,
                    "WEBSOCKET_KEY",
                    environment.name(),
                    "웹소켓 키 발급 성공"
            );

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