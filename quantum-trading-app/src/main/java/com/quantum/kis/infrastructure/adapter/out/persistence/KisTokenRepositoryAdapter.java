package com.quantum.kis.infrastructure.adapter.out.persistence;

import com.quantum.kis.application.port.out.KisTokenRepositoryPort;
import com.quantum.kis.domain.KisEnvironment;
import com.quantum.kis.domain.token.KisToken;
import com.quantum.kis.domain.token.KisTokenId;
import com.quantum.kis.infrastructure.persistence.JpaKisTokenRepository;
import com.quantum.kis.infrastructure.persistence.KisTokenEntity;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * KIS 토큰 Repository 어댑터
 * Application Port를 구현하여 JPA Repository와 도메인을 연결
 */
@Repository
public class KisTokenRepositoryAdapter implements KisTokenRepositoryPort {

    private final JpaKisTokenRepository jpaRepository;

    public KisTokenRepositoryAdapter(JpaKisTokenRepository jpaRepository) {
        this.jpaRepository = jpaRepository;
    }

    @Override
    public Optional<KisToken> findById(KisTokenId id) {
        return jpaRepository.findByEnvironmentAndTokenType(
                id.environment(),
                id.tokenType()
        ).map(KisTokenEntity::toDomain);
    }

    @Override
    public KisToken save(KisToken kisToken) {
        KisTokenEntity entity = KisTokenEntity.fromDomain(kisToken);
        KisTokenEntity savedEntity = jpaRepository.save(entity);
        return savedEntity.toDomain();
    }

    @Override
    public List<KisToken> findAll() {
        return jpaRepository.findAll().stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    public List<KisToken> findByEnvironment(KisEnvironment environment) {
        return jpaRepository.findByEnvironment(environment).stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    public List<KisToken> findTokensNeedingRenewal() {
        return jpaRepository.findTokensNeedingRenewal().stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    public List<KisToken> findAllExpired() {
        return jpaRepository.findAllExpired().stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    public int deleteExpiredTokens() {
        return jpaRepository.deleteExpiredTokens();
    }

}