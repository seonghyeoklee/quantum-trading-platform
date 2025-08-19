package com.quantum.core.infrastructure.repository;

import com.quantum.core.domain.model.stock.Stock;
import com.quantum.core.domain.port.repository.StockRepository;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/** 주식 정보 리포지토리 구현체 */
@Repository
public interface StockRepositoryImpl extends JpaRepository<Stock, String>, StockRepository {

    @Override
    default Optional<Stock> findBySymbol(String symbol) {
        return findById(symbol);
    }

    @Override
    List<Stock> findByExchange(String exchange);

    @Override
    default boolean existsBySymbol(String symbol) {
        return existsById(symbol);
    }
}
