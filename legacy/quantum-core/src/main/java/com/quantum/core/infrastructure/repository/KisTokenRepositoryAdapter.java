package com.quantum.core.infrastructure.repository;

import com.quantum.core.domain.model.kis.KisToken;
import com.quantum.core.domain.port.repository.KisTokenRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.Optional;

/**
 * KIS 토큰 리포지토리 어댑터 구현체
 * Port-Adapter 패턴으로 JPA와 도메인 분리
 */
@Repository
@RequiredArgsConstructor
public class KisTokenRepositoryAdapter implements KisTokenRepository {

    private final KisTokenJpaRepository jpaRepository;

    @Override
    public KisToken save(KisToken token) {
        return jpaRepository.save(token);
    }

    @Override
    public Optional<KisToken> findActiveValidToken() {
        return jpaRepository.findActiveValidToken();
    }

    @Override
    public void deactivateAllTokens() {
        jpaRepository.deactivateAllTokens();
    }

    @Override
    public void deleteExpiredTokens() {
        jpaRepository.deleteTokensBefore(LocalDateTime.now().minusDays(3));
    }
}