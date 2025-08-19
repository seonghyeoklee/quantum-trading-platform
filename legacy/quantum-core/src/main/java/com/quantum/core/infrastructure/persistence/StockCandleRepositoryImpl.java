package com.quantum.core.infrastructure.persistence;

import com.quantum.core.domain.model.StockCandle;
import com.quantum.core.domain.port.repository.StockCandleRepository;
import jakarta.persistence.EntityManager;
import jakarta.persistence.Query;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

/** JPA 기반 주식 캔들 데이터 저장소 구현체 */
@Repository
public class StockCandleRepositoryImpl implements StockCandleRepository {

    private final StockCandleJpaRepository jpaRepository;
    private final EntityManager entityManager;

    public StockCandleRepositoryImpl(
            StockCandleJpaRepository jpaRepository, EntityManager entityManager) {
        this.jpaRepository = jpaRepository;
        this.entityManager = entityManager;
    }

    @Override
    public StockCandle save(StockCandle candle) {
        return jpaRepository.save(candle);
    }

    @Override
    public List<StockCandle> saveAll(List<StockCandle> candles) {
        return jpaRepository.saveAll(candles);
    }

    @Override
    public Optional<StockCandle> findBySymbolAndTimeframeAndTimestamp(
            String symbol, String timeframe, LocalDateTime timestamp) {
        return jpaRepository.findBySymbolAndTimeframeAndTimestamp(symbol, timeframe, timestamp);
    }

    @Override
    public List<StockCandle> findBySymbolAndTimeframeBetween(
            String symbol, String timeframe, LocalDateTime startTime, LocalDateTime endTime) {
        Query query =
                entityManager.createQuery(
                        "SELECT sc FROM StockCandle sc WHERE sc.symbol = :symbol AND sc.timeframe = :timeframe "
                                + "AND sc.timestamp BETWEEN :startTime AND :endTime ORDER BY sc.timestamp ASC",
                        StockCandle.class);
        query.setParameter("symbol", symbol);
        query.setParameter("timeframe", timeframe);
        query.setParameter("startTime", startTime);
        query.setParameter("endTime", endTime);
        return query.getResultList();
    }

    @Override
    public List<StockCandle> findRecentCandles(String symbol, String timeframe, int limit) {
        Query query =
                entityManager.createQuery(
                        "SELECT sc FROM StockCandle sc WHERE sc.symbol = :symbol AND sc.timeframe = :timeframe "
                                + "ORDER BY sc.timestamp DESC",
                        StockCandle.class);
        query.setParameter("symbol", symbol);
        query.setParameter("timeframe", timeframe);
        query.setMaxResults(limit);
        return query.getResultList();
    }

    @Override
    public Optional<StockCandle> findLastCandle(String symbol, String timeframe) {
        Query query =
                entityManager.createQuery(
                        "SELECT sc FROM StockCandle sc WHERE sc.symbol = :symbol AND sc.timeframe = :timeframe "
                                + "ORDER BY sc.timestamp DESC",
                        StockCandle.class);
        query.setParameter("symbol", symbol);
        query.setParameter("timeframe", timeframe);
        query.setMaxResults(1);

        List<StockCandle> results = query.getResultList();
        return results.isEmpty() ? Optional.empty() : Optional.of(results.get(0));
    }

    @Override
    public List<StockCandle> findDailyCandlesByDate(LocalDateTime date) {
        LocalDateTime startOfDay = date.toLocalDate().atStartOfDay();
        LocalDateTime endOfDay = startOfDay.plusDays(1).minusNanos(1);

        Query query =
                entityManager.createQuery(
                        "SELECT sc FROM StockCandle sc WHERE sc.timeframe = '1d' "
                                + "AND sc.timestamp BETWEEN :startOfDay AND :endOfDay ORDER BY sc.volume DESC",
                        StockCandle.class);
        query.setParameter("startOfDay", startOfDay);
        query.setParameter("endOfDay", endOfDay);
        return query.getResultList();
    }

    @Override
    public List<StockCandle> findTopVolumeStocks(
            String timeframe, LocalDateTime startTime, LocalDateTime endTime, int limit) {
        Query query =
                entityManager.createQuery(
                        "SELECT sc FROM StockCandle sc WHERE sc.timeframe = :timeframe "
                                + "AND sc.timestamp BETWEEN :startTime AND :endTime "
                                + "GROUP BY sc.symbol ORDER BY SUM(sc.volume) DESC",
                        StockCandle.class);
        query.setParameter("timeframe", timeframe);
        query.setParameter("startTime", startTime);
        query.setParameter("endTime", endTime);
        query.setMaxResults(limit);
        return query.getResultList();
    }

    @Override
    public boolean existsBySymbolAndTimeframeAndTimestamp(
            String symbol, String timeframe, LocalDateTime timestamp) {
        return jpaRepository.existsBySymbolAndTimeframeAndTimestamp(symbol, timeframe, timestamp);
    }

    @Override
    public void deleteOlderThan(LocalDateTime cutoffDate) {
        Query query =
                entityManager.createQuery(
                        "DELETE FROM StockCandle sc WHERE sc.timestamp < :cutoffDate");
        query.setParameter("cutoffDate", cutoffDate);
        query.executeUpdate();
    }

    @Override
    public long countBySymbolAndTimeframe(String symbol, String timeframe) {
        Query query =
                entityManager.createQuery(
                        "SELECT COUNT(sc) FROM StockCandle sc WHERE sc.symbol = :symbol AND sc.timeframe = :timeframe");
        query.setParameter("symbol", symbol);
        query.setParameter("timeframe", timeframe);
        return (Long) query.getSingleResult();
    }
}

/** JPA Repository 인터페이스 */
interface StockCandleJpaRepository extends JpaRepository<StockCandle, Long> {

    Optional<StockCandle> findBySymbolAndTimeframeAndTimestamp(
            String symbol, String timeframe, LocalDateTime timestamp);

    boolean existsBySymbolAndTimeframeAndTimestamp(
            String symbol, String timeframe, LocalDateTime timestamp);
}
