package com.quantum.kis.domain.token;

import java.time.LocalDateTime;

/**
 * KIS 토큰 도메인 엔티티 (Aggregate Root)
 * 토큰의 생명주기와 비즈니스 로직을 관리
 */
public class KisToken {

    private final KisTokenId id;
    private Token token;
    private LocalDateTime issuedAt;
    private TokenStatus status;
    private LocalDateTime lastUpdatedAt;

    // 기본 생성자 (JPA용)
    protected KisToken() {
        this.id = null;
    }

    // 새 토큰 생성
    private KisToken(KisTokenId id, Token token) {
        this.id = id;
        this.token = token;
        this.issuedAt = LocalDateTime.now();
        this.status = TokenStatus.ACTIVE;
        this.lastUpdatedAt = LocalDateTime.now();
    }

    // 복원용 생성자 (JPA 엔티티에서 도메인 객체 복원 시 사용)
    private KisToken(KisTokenId id, Token token, LocalDateTime issuedAt,
                     TokenStatus status, LocalDateTime lastUpdatedAt) {
        this.id = id;
        this.token = token;
        this.issuedAt = issuedAt;
        this.status = status;
        this.lastUpdatedAt = lastUpdatedAt;
    }

    /**
     * 새 KIS 토큰 생성
     * @param id 토큰 ID
     * @param token 토큰 값 객체
     * @return KisToken 엔티티
     */
    public static KisToken create(KisTokenId id, Token token) {
        if (id == null) {
            throw new IllegalArgumentException("토큰 ID는 필수입니다.");
        }
        if (token == null) {
            throw new IllegalArgumentException("토큰은 필수입니다.");
        }

        return new KisToken(id, token);
    }

    /**
     * 기존 데이터로부터 KIS 토큰 복원 (JPA 엔티티에서 사용)
     * @param id 토큰 ID
     * @param token 토큰 값 객체
     * @param issuedAt 발급 시간
     * @param status 상태
     * @param lastUpdatedAt 마지막 업데이트 시간
     * @return KisToken 엔티티
     */
    public static KisToken restore(KisTokenId id, Token token, LocalDateTime issuedAt,
                                  TokenStatus status, LocalDateTime lastUpdatedAt) {
        if (id == null) {
            throw new IllegalArgumentException("토큰 ID는 필수입니다.");
        }
        if (token == null) {
            throw new IllegalArgumentException("토큰은 필수입니다.");
        }

        return new KisToken(id, token, issuedAt, status, lastUpdatedAt);
    }

    /**
     * 토큰 갱신
     * @param newToken 새로운 토큰
     */
    public void renewToken(Token newToken) {
        if (newToken == null) {
            throw new IllegalArgumentException("새 토큰은 필수입니다.");
        }

        this.token = newToken;
        this.issuedAt = LocalDateTime.now();
        this.status = TokenStatus.ACTIVE;
        this.lastUpdatedAt = LocalDateTime.now();
    }

    /**
     * 토큰을 만료 상태로 변경
     */
    public void markAsExpired() {
        this.status = TokenStatus.EXPIRED;
        this.lastUpdatedAt = LocalDateTime.now();
    }

    /**
     * 토큰을 무효 상태로 변경
     */
    public void markAsInvalid() {
        this.status = TokenStatus.INVALID;
        this.lastUpdatedAt = LocalDateTime.now();
    }

    /**
     * 토큰이 사용 가능한지 확인
     * @return 사용 가능한 경우 true
     */
    public boolean isUsable() {
        return status == TokenStatus.ACTIVE && token.isValid();
    }

    /**
     * 토큰이 곧 만료될지 확인
     * @return 곧 만료될 경우 true
     */
    public boolean needsRenewal() {
        return !isUsable() || token.isExpiringSoon();
    }

    /**
     * 토큰 만료 시간까지 남은 시간(분) 계산
     * @return 남은 시간(분)
     */
    public long getMinutesUntilExpiry() {
        if (token == null) return 0;

        LocalDateTime now = LocalDateTime.now();
        LocalDateTime expiry = token.expiresAt();

        if (now.isAfter(expiry)) return 0;

        return java.time.Duration.between(now, expiry).toMinutes();
    }

    // Getters
    public KisTokenId getId() {
        return id;
    }

    public Token getToken() {
        return token;
    }

    public LocalDateTime getIssuedAt() {
        return issuedAt;
    }

    public TokenStatus getStatus() {
        return status;
    }

    public LocalDateTime getLastUpdatedAt() {
        return lastUpdatedAt;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        KisToken kisToken = (KisToken) obj;
        return id != null && id.equals(kisToken.id);
    }

    @Override
    public int hashCode() {
        return id != null ? id.hashCode() : 0;
    }

    @Override
    public String toString() {
        return "KisToken{" +
                "id=" + id +
                ", status=" + status +
                ", issuedAt=" + issuedAt +
                ", expiresAt=" + (token != null ? token.expiresAt() : null) +
                '}';
    }
}