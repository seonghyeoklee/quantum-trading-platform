package com.quantum.kis.infrastructure.persistence;

import com.quantum.kis.domain.token.KisToken;
import com.quantum.kis.domain.token.KisTokenId;
import com.quantum.kis.domain.token.KisTokenRepository;
import com.quantum.kis.domain.token.TokenStatus;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * KisTokenRepository 구현체
 * DDD Repository 패턴과 Spring Data JPA 연결
 */
@Repository
@Transactional
public class KisTokenPersistenceRepository implements KisTokenRepository {

    private final JpaKisTokenRepository jpaRepository;

    public KisTokenPersistenceRepository(JpaKisTokenRepository jpaRepository) {
        this.jpaRepository = jpaRepository;
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<KisToken> findById(KisTokenId tokenId) {
        return jpaRepository.findById(tokenId.toKey())
                .map(KisTokenEntity::toDomain);
    }

    @Override
    @Transactional(readOnly = true)
    public List<KisToken> findAll() {
        return jpaRepository.findAll().stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public List<KisToken> findAllActive() {
        return jpaRepository.findByStatus(TokenStatus.ACTIVE).stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public List<KisToken> findAllExpired() {
        return jpaRepository.findExpiredTokens(LocalDateTime.now()).stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public List<KisToken> findTokensNeedingRenewal() {
        LocalDateTime expiringSoon = LocalDateTime.now().plusHours(1);
        return jpaRepository.findTokensNeedingRenewal(
                expiringSoon,
                TokenStatus.INVALID,
                TokenStatus.EXPIRED
        ).stream()
                .map(KisTokenEntity::toDomain)
                .toList();
    }

    @Override
    public KisToken save(KisToken token) {
        String tokenKey = token.getId().toKey();

        // 기존 엔티티가 있는지 확인
        Optional<KisTokenEntity> existingEntity = jpaRepository.findById(tokenKey);

        KisTokenEntity entity;
        if (existingEntity.isPresent()) {
            // 기존 엔티티 업데이트
            entity = existingEntity.get();
            entity.updateFromDomain(token);
        } else {
            // 새 엔티티 생성
            entity = KisTokenEntity.fromDomain(token);
        }

        KisTokenEntity savedEntity = jpaRepository.save(entity);
        return savedEntity.toDomain();
    }

    @Override
    public void deleteById(KisTokenId tokenId) {
        jpaRepository.deleteById(tokenId.toKey());
    }

    @Override
    public int deleteExpiredTokens() {
        return jpaRepository.deleteExpiredTokens(LocalDateTime.now(), TokenStatus.EXPIRED);
    }

    @Override
    @Transactional(readOnly = true)
    public boolean existsById(KisTokenId tokenId) {
        return jpaRepository.existsById(tokenId.toKey());
    }

    @Override
    public void deleteAll() {
        jpaRepository.deleteAll();
    }
}