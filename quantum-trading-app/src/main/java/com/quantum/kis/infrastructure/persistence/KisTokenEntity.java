package com.quantum.kis.infrastructure.persistence;

import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.TokenType;
import com.quantum.kis.domain.token.KisToken;
import com.quantum.kis.domain.token.KisTokenId;
import com.quantum.kis.domain.token.Token;
import com.quantum.kis.domain.token.TokenStatus;
import jakarta.persistence.*;

import java.time.LocalDateTime;
import lombok.Getter;

/**
 * KIS 토큰 JPA 엔티티
 * 도메인 모델과 데이터베이스 테이블 간의 매핑
 */
@Getter
@Entity
@Table(name = "kis_tokens", uniqueConstraints = {
        @UniqueConstraint(columnNames = {"environment", "token_type"})
})
public class KisTokenEntity {

    @Id
    @Column(name = "token_key", length = 50)
    private String tokenKey;  // "PROD_ACCESS_TOKEN" 형태

    @Enumerated(EnumType.STRING)
    @Column(name = "environment", nullable = false, length = 10)
    private KisEnvironment environment;

    @Enumerated(EnumType.STRING)
    @Column(name = "token_type", nullable = false, length = 20)
    private TokenType tokenType;

    @Column(name = "token_value", nullable = false, length = 1000)
    private String tokenValue;

    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    @Column(name = "issued_at", nullable = false)
    private LocalDateTime issuedAt;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 10)
    private TokenStatus status;

    @Column(name = "last_updated_at", nullable = false)
    private LocalDateTime lastUpdatedAt;

    @Version
    private Long version;

    // 기본 생성자 (JPA 필수)
    protected KisTokenEntity() {}

    // 팩토리 메서드로 도메인 엔티티에서 JPA 엔티티 생성
    public static KisTokenEntity fromDomain(KisToken domainToken) {
        KisTokenEntity entity = new KisTokenEntity();
        entity.tokenKey = domainToken.getId().toKey();
        entity.environment = domainToken.getId().environment();
        entity.tokenType = domainToken.getId().tokenType();
        entity.tokenValue = domainToken.getToken().value();
        entity.expiresAt = domainToken.getToken().expiresAt();
        entity.issuedAt = domainToken.getIssuedAt();
        entity.status = domainToken.getStatus();
        entity.lastUpdatedAt = domainToken.getLastUpdatedAt();
        return entity;
    }

    // JPA 엔티티를 도메인 엔티티로 변환
    public KisToken toDomain() {
        KisTokenId id = new KisTokenId(environment, tokenType);
        Token token = Token.of(tokenValue, expiresAt);

        // 복원용 정적 메서드 사용
        return KisToken.restore(id, token, issuedAt, status, lastUpdatedAt);
    }

    // 도메인 엔티티의 변경사항을 JPA 엔티티에 반영
    public void updateFromDomain(KisToken domainToken) {
        this.tokenValue = domainToken.getToken().value();
        this.expiresAt = domainToken.getToken().expiresAt();
        this.issuedAt = domainToken.getIssuedAt();
        this.status = domainToken.getStatus();
        this.lastUpdatedAt = domainToken.getLastUpdatedAt();
    }

}