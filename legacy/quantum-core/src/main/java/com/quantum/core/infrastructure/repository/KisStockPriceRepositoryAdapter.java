package com.quantum.core.infrastructure.repository;

import com.quantum.core.domain.model.kis.KisStockPriceData;
import com.quantum.core.domain.port.repository.KisStockPriceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * KIS 주식 가격 리포지토리 어댑터 구현체
 * Port-Adapter 패턴으로 JPA와 도메인 분리
 */
@Repository
@RequiredArgsConstructor
public class KisStockPriceRepositoryAdapter implements KisStockPriceRepository {

    private final KisStockPriceJpaRepository jpaRepository;

    @Override
    public KisStockPriceData save(KisStockPriceData kisStockPriceData) {
        return jpaRepository.save(kisStockPriceData);
    }

    @Override
    public List<KisStockPriceData> saveAll(List<KisStockPriceData> kisStockPriceDataList) {
        return jpaRepository.saveAll(kisStockPriceDataList);
    }

    @Override
    public Optional<KisStockPriceData> findLatestBySymbol(String symbol) {
        return jpaRepository.findLatestBySymbol(symbol);
    }

    @Override
    public List<KisStockPriceData> findBySymbolOrderByQueryTimeDesc(String symbol) {
        return jpaRepository.findBySymbolOrderByQueryTimeDesc(symbol);
    }

    @Override
    public List<KisStockPriceData> findBySymbolAndQueryTimeBetween(
            String symbol, LocalDateTime startTime, LocalDateTime endTime) {
        return jpaRepository.findBySymbolAndQueryTimeBetween(symbol, startTime, endTime);
    }

    @Override
    public List<KisStockPriceData> findAllLatestBySymbol() {
        return jpaRepository.findAllLatestBySymbol();
    }

    @Override
    public List<KisStockPriceData> findAllOrderByQueryTimeDesc() {
        return jpaRepository.findAllOrderByQueryTimeDesc();
    }
}