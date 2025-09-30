package com.quantum.kis.application.service;

import com.quantum.kis.application.port.in.*;
import com.quantum.kis.application.port.out.KisApiPort;
import com.quantum.kis.application.port.out.KisTokenRepositoryPort;
import com.quantum.kis.application.port.out.NotificationPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;
import com.quantum.kis.domain.token.*;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.TokenInfo;
import com.quantum.kis.dto.WebSocketKeyResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * KIS 토큰 관리 Application Service
 * 모든 토큰 관련 Use Case를 구현
 */
@Service
@Transactional
public class KisTokenApplicationService implements
    GetTokenUseCase, RefreshTokenUseCase, GetTokenStatusUseCase, CleanupExpiredTokensUseCase {

    private static final Logger log = LoggerFactory.getLogger(KisTokenApplicationService.class);

    private final KisTokenRepositoryPort repositoryPort;
    private final KisApiPort kisApiPort;
    private final NotificationPort notificationPort;

    public KisTokenApplicationService(KisTokenRepositoryPort repositoryPort,
                                    KisApiPort kisApiPort,
                                    NotificationPort notificationPort) {
        this.repositoryPort = repositoryPort;
        this.kisApiPort = kisApiPort;
        this.notificationPort = notificationPort;
    }

    // ============= GetTokenUseCase 구현 =============

    @Override
    @Transactional
    public String getValidAccessToken(KisEnvironment environment) {
        KisTokenId tokenId = new KisTokenId(environment, TokenType.ACCESS_TOKEN);

        Optional<KisToken> existingToken = repositoryPort.findById(tokenId);

        if (existingToken.isPresent() && existingToken.get().isUsable()) {
            KisToken token = existingToken.get();

            // 곧 만료될 예정이면 미리 재발급
            if (token.needsRenewal()) {
                log.info("액세스 토큰 사전 재발급 - 환경: {} (만료 예정: {}분)",
                    environment, token.getMinutesUntilExpiry());
                return refreshAccessToken(environment);
            }

            log.debug("기존 액세스 토큰 사용 - 환경: {}, 만료까지: {}분",
                environment, token.getMinutesUntilExpiry());
            return token.getToken().value();
        }

        // 토큰이 없거나 사용할 수 없는 경우 새로 발급
        log.info("액세스 토큰 재발급 필요 - 환경: {}", environment);
        return refreshAccessToken(environment);
    }

    @Override
    @Transactional
    public String getValidWebSocketKey(KisEnvironment environment) {
        KisTokenId tokenId = new KisTokenId(environment, TokenType.WEBSOCKET_KEY);

        Optional<KisToken> existingToken = repositoryPort.findById(tokenId);

        if (existingToken.isPresent() && existingToken.get().isUsable()) {
            KisToken token = existingToken.get();

            if (token.needsRenewal()) {
                log.info("웹소켓 키 사전 재발급 - 환경: {} (만료 예정: {}분)",
                    environment, token.getMinutesUntilExpiry());
                return refreshWebSocketKey(environment);
            }

            log.debug("기존 웹소켓 키 사용 - 환경: {}, 만료까지: {}분",
                environment, token.getMinutesUntilExpiry());
            return token.getToken().value();
        }

        log.info("웹소켓 키 재발급 필요 - 환경: {}", environment);
        return refreshWebSocketKey(environment);
    }

    // ============= RefreshTokenUseCase 구현 =============

    @Override
    @Transactional
    public String refreshAccessToken(KisEnvironment environment) {
        try {
            AccessTokenResponse response = kisApiPort.issueAccessToken(environment);

            // 만료 시간 파싱
            LocalDateTime expiresAt = parseTokenExpiry(response.accessTokenExpired());

            // 도메인 객체 생성
            KisTokenId tokenId = new KisTokenId(environment, TokenType.ACCESS_TOKEN);
            Token token = Token.of(response.accessToken(), expiresAt);

            // 기존 토큰이 있으면 갱신, 없으면 새로 생성
            Optional<KisToken> existingToken = repositoryPort.findById(tokenId);
            KisToken kisToken;

            if (existingToken.isPresent()) {
                kisToken = existingToken.get();
                kisToken.renewToken(token);
                log.info("액세스 토큰 갱신 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            } else {
                kisToken = KisToken.create(tokenId, token);
                log.info("액세스 토큰 신규 생성 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            }

            // 저장 및 알림
            repositoryPort.save(kisToken);
            notificationPort.notifyTokenRefreshed(environment, TokenType.ACCESS_TOKEN);

            return response.accessToken();

        } catch (Exception e) {
            log.error("액세스 토큰 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());

            // 실패한 토큰을 무효 상태로 저장
            saveInvalidToken(environment, TokenType.ACCESS_TOKEN);
            notificationPort.notifyTokenIssueFailed(environment, TokenType.ACCESS_TOKEN, e.getMessage());

            throw e;
        }
    }

    @Override
    @Transactional
    public String refreshWebSocketKey(KisEnvironment environment) {
        try {
            WebSocketKeyResponse response = kisApiPort.issueWebSocketKey(environment);

            // 웹소켓 키는 보통 24시간 유효
            LocalDateTime expiresAt = LocalDateTime.now().plusHours(24);

            // 도메인 객체 생성
            KisTokenId tokenId = new KisTokenId(environment, TokenType.WEBSOCKET_KEY);
            Token token = Token.of(response.approvalKey(), expiresAt);

            // 기존 토큰이 있으면 갱신, 없으면 새로 생성
            Optional<KisToken> existingToken = repositoryPort.findById(tokenId);
            KisToken kisToken;

            if (existingToken.isPresent()) {
                kisToken = existingToken.get();
                kisToken.renewToken(token);
                log.info("웹소켓 키 갱신 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            } else {
                kisToken = KisToken.create(tokenId, token);
                log.info("웹소켓 키 신규 생성 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            }

            // 저장 및 알림
            repositoryPort.save(kisToken);
            notificationPort.notifyTokenRefreshed(environment, TokenType.WEBSOCKET_KEY);

            return response.approvalKey();

        } catch (Exception e) {
            log.error("웹소켓 키 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());

            // 실패한 토큰을 무효 상태로 저장
            saveInvalidToken(environment, TokenType.WEBSOCKET_KEY);
            notificationPort.notifyTokenIssueFailed(environment, TokenType.WEBSOCKET_KEY, e.getMessage());

            throw e;
        }
    }

    @Override
    @Transactional
    public void refreshAllTokens() {
        log.info("모든 토큰 재발급 시작");

        for (KisEnvironment environment : KisEnvironment.values()) {
            try {
                refreshAccessToken(environment);
                refreshWebSocketKey(environment);
                log.info("토큰 재발급 완료 - 환경: {}", environment);
            } catch (Exception e) {
                log.error("토큰 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            }
        }

        log.info("모든 토큰 재발급 완료");
    }

    // ============= GetTokenStatusUseCase 구현 =============

    @Override
    @Transactional(readOnly = true)
    public Map<String, TokenInfo> getAllTokenStatus() {
        List<KisToken> allTokens = repositoryPort.findAll();

        return allTokens.stream()
                .collect(Collectors.toMap(
                        token -> token.getId().toKey(),
                        this::convertToTokenInfo
                ));
    }

    @Override
    @Transactional(readOnly = true)
    public List<KisToken> getTokensByEnvironment(KisEnvironment environment) {
        return repositoryPort.findByEnvironment(environment);
    }

    @Override
    @Transactional(readOnly = true)
    public List<KisToken> getTokensNeedingRenewal() {
        return repositoryPort.findTokensNeedingRenewal();
    }

    // ============= CleanupExpiredTokensUseCase 구현 =============

    @Override
    @Transactional
    public int cleanupExpiredTokens() {
        log.debug("만료된 토큰 정리 시작");

        // 삭제 전 만료된 토큰들의 정보를 수집 (알림용)
        List<KisToken> expiredTokens = repositoryPort.findAllExpired();

        // 알림 발송
        for (KisToken token : expiredTokens) {
            notificationPort.notifyTokenExpired(token.getId().environment(), token.getId().tokenType());
        }

        // 데이터베이스에서 만료된 토큰들 직접 삭제
        int deletedCount = repositoryPort.deleteExpiredTokens();

        log.debug("만료된 토큰 정리 완료 - {}개 정리", deletedCount);
        return deletedCount;
    }

    // ============= Private Helper Methods =============

    /**
     * 도메인 토큰을 TokenInfo DTO로 변환
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

    /**
     * 실패한 토큰을 무효 상태로 저장
     */
    private void saveInvalidToken(KisEnvironment environment, TokenType tokenType) {
        try {
            KisTokenId tokenId = new KisTokenId(environment, tokenType);
            Optional<KisToken> existingToken = repositoryPort.findById(tokenId);

            if (existingToken.isPresent()) {
                KisToken token = existingToken.get();
                token.markAsInvalid();
                repositoryPort.save(token);
            }
        } catch (Exception e) {
            log.warn("무효 토큰 저장 실패 - 환경: {}, 타입: {}", environment, tokenType);
        }
    }

    /**
     * 토큰 만료 시간을 파싱한다.
     */
    private LocalDateTime parseTokenExpiry(String expiryString) {
        try {
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
            return LocalDateTime.parse(expiryString, formatter);
        } catch (Exception e) {
            log.warn("토큰 만료 시간 파싱 실패: {}, 기본값 사용 (24시간 후)", expiryString);
            return LocalDateTime.now().plusHours(24);
        }
    }
}