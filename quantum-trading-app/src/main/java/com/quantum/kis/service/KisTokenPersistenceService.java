package com.quantum.kis.service;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;
import com.quantum.kis.domain.token.*;
import com.quantum.kis.dto.AccessTokenResponse;
import com.quantum.kis.dto.WebSocketKeyResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;

/**
 * KIS 토큰 영속성 관리 서비스
 * 도메인 모델과 데이터베이스 간의 비즈니스 로직 처리
 */
@Service
@Transactional
public class KisTokenPersistenceService {

    private static final Logger log = LoggerFactory.getLogger(KisTokenPersistenceService.class);

    private final KisTokenRepository tokenRepository;
    private final KisTokenService tokenService;

    public KisTokenPersistenceService(KisTokenRepository tokenRepository,
                                      KisTokenService tokenService) {
        this.tokenRepository = tokenRepository;
        this.tokenService = tokenService;
    }

    /**
     * 유효한 액세스 토큰을 반환한다. 없거나 만료된 경우 자동으로 재발급한다.
     * @param environment KIS 환경
     * @return 액세스 토큰 값
     */
    @Transactional
    public String getValidAccessToken(KisEnvironment environment) {
        KisTokenId tokenId = new KisTokenId(environment, TokenType.ACCESS_TOKEN);

        Optional<KisToken> existingToken = tokenRepository.findById(tokenId);

        if (existingToken.isPresent() && existingToken.get().isUsable()) {
            KisToken token = existingToken.get();

            // 곧 만료될 예정이면 미리 재발급
            if (token.needsRenewal()) {
                log.info("액세스 토큰 사전 재발급 - 환경: {} (만료 예정: {}분)",
                    environment, token.getMinutesUntilExpiry());
                return renewAccessToken(environment);
            }

            log.debug("기존 액세스 토큰 사용 - 환경: {}, 만료까지: {}분",
                environment, token.getMinutesUntilExpiry());
            return token.getToken().value();
        }

        // 토큰이 없거나 사용할 수 없는 경우 새로 발급
        log.info("액세스 토큰 재발급 필요 - 환경: {}", environment);
        return renewAccessToken(environment);
    }

    /**
     * 유효한 웹소켓 키를 반환한다. 없거나 만료된 경우 자동으로 재발급한다.
     * @param environment KIS 환경
     * @return 웹소켓 키 값
     */
    @Transactional
    public String getValidWebSocketKey(KisEnvironment environment) {
        KisTokenId tokenId = new KisTokenId(environment, TokenType.WEBSOCKET_KEY);

        Optional<KisToken> existingToken = tokenRepository.findById(tokenId);

        if (existingToken.isPresent() && existingToken.get().isUsable()) {
            KisToken token = existingToken.get();

            if (token.needsRenewal()) {
                log.info("웹소켓 키 사전 재발급 - 환경: {} (만료 예정: {}분)",
                    environment, token.getMinutesUntilExpiry());
                return renewWebSocketKey(environment);
            }

            log.debug("기존 웹소켓 키 사용 - 환경: {}, 만료까지: {}분",
                environment, token.getMinutesUntilExpiry());
            return token.getToken().value();
        }

        log.info("웹소켓 키 재발급 필요 - 환경: {}", environment);
        return renewWebSocketKey(environment);
    }

    /**
     * 액세스 토큰을 강제로 재발급한다.
     * @param environment KIS 환경
     * @return 새로운 액세스 토큰 값
     */
    @Transactional
    public String renewAccessToken(KisEnvironment environment) {
        try {
            AccessTokenResponse response = tokenService.getAccessToken(environment);

            // 만료 시간 파싱
            LocalDateTime expiresAt = parseTokenExpiry(response.accessTokenExpired());

            // 도메인 객체 생성
            KisTokenId tokenId = new KisTokenId(environment, TokenType.ACCESS_TOKEN);
            Token token = Token.of(response.accessToken(), expiresAt);

            // 기존 토큰이 있으면 갱신, 없으면 새로 생성
            Optional<KisToken> existingToken = tokenRepository.findById(tokenId);
            KisToken kisToken;

            if (existingToken.isPresent()) {
                kisToken = existingToken.get();
                kisToken.renewToken(token);
                log.info("액세스 토큰 갱신 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            } else {
                kisToken = KisToken.create(tokenId, token);
                log.info("액세스 토큰 신규 생성 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            }

            // 저장
            tokenRepository.save(kisToken);

            return response.accessToken();

        } catch (Exception e) {
            log.error("액세스 토큰 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());

            // 실패한 토큰을 무효 상태로 저장
            saveInvalidToken(environment, TokenType.ACCESS_TOKEN);

            throw e;
        }
    }

    /**
     * 웹소켓 키를 강제로 재발급한다.
     * @param environment KIS 환경
     * @return 새로운 웹소켓 키 값
     */
    @Transactional
    public String renewWebSocketKey(KisEnvironment environment) {
        try {
            WebSocketKeyResponse response = tokenService.getWebSocketKey(environment);

            // 웹소켓 키는 보통 24시간 유효
            LocalDateTime expiresAt = LocalDateTime.now().plusHours(24);

            // 도메인 객체 생성
            KisTokenId tokenId = new KisTokenId(environment, TokenType.WEBSOCKET_KEY);
            Token token = Token.of(response.approvalKey(), expiresAt);

            // 기존 토큰이 있으면 갱신, 없으면 새로 생성
            Optional<KisToken> existingToken = tokenRepository.findById(tokenId);
            KisToken kisToken;

            if (existingToken.isPresent()) {
                kisToken = existingToken.get();
                kisToken.renewToken(token);
                log.info("웹소켓 키 갱신 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            } else {
                kisToken = KisToken.create(tokenId, token);
                log.info("웹소켓 키 신규 생성 완료 - 환경: {}, 만료: {}", environment, expiresAt);
            }

            // 저장
            tokenRepository.save(kisToken);

            return response.approvalKey();

        } catch (Exception e) {
            log.error("웹소켓 키 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());

            // 실패한 토큰을 무효 상태로 저장
            saveInvalidToken(environment, TokenType.WEBSOCKET_KEY);

            throw e;
        }
    }

    /**
     * 모든 환경의 모든 토큰을 재발급한다.
     */
    @Transactional
    public void renewAllTokens() {
        log.info("모든 토큰 재발급 시작");

        for (KisEnvironment environment : KisEnvironment.values()) {
            try {
                renewAccessToken(environment);
                renewWebSocketKey(environment);
                log.info("토큰 재발급 완료 - 환경: {}", environment);
            } catch (Exception e) {
                log.error("토큰 재발급 실패 - 환경: {}, 오류: {}", environment, e.getMessage());
            }
        }

        log.info("모든 토큰 재발급 완료");
    }

    /**
     * 만료된 토큰들을 정리한다.
     * @return 정리된 토큰 수
     */
    @Transactional
    public int cleanupExpiredTokens() {
        log.debug("만료된 토큰 정리 시작");

        List<KisToken> expiredTokens = tokenRepository.findAllExpired();

        // 만료된 토큰들을 만료 상태로 변경
        for (KisToken token : expiredTokens) {
            token.markAsExpired();
            tokenRepository.save(token);
        }

        // 데이터베이스에서 만료된 토큰들 삭제
        int deletedCount = tokenRepository.deleteExpiredTokens();

        log.debug("만료된 토큰 정리 완료 - {}개 정리", deletedCount);
        return deletedCount;
    }

    /**
     * 현재 저장된 모든 토큰 조회
     * @return 토큰 리스트
     */
    @Transactional(readOnly = true)
    public List<KisToken> getAllTokens() {
        return tokenRepository.findAll();
    }

    /**
     * 갱신이 필요한 토큰들 조회
     * @return 갱신 필요 토큰 리스트
     */
    @Transactional(readOnly = true)
    public List<KisToken> getTokensNeedingRenewal() {
        return tokenRepository.findTokensNeedingRenewal();
    }

    /**
     * 실패한 토큰을 무효 상태로 저장
     */
    private void saveInvalidToken(KisEnvironment environment, TokenType tokenType) {
        try {
            KisTokenId tokenId = new KisTokenId(environment, tokenType);
            Optional<KisToken> existingToken = tokenRepository.findById(tokenId);

            if (existingToken.isPresent()) {
                KisToken token = existingToken.get();
                token.markAsInvalid();
                tokenRepository.save(token);
            }
        } catch (Exception e) {
            log.warn("무효 토큰 저장 실패 - 환경: {}, 타입: {}", environment, tokenType);
        }
    }

    /**
     * 토큰 만료 시간을 파싱한다.
     * @param expiryString 만료 시간 문자열 (예: "2024-01-23 15:30:45")
     * @return LocalDateTime 객체
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