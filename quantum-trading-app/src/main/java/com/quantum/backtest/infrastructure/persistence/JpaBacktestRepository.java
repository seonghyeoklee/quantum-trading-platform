package com.quantum.backtest.infrastructure.persistence;

import com.quantum.backtest.domain.BacktestStatus;
import com.quantum.backtest.domain.StrategyType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 백테스팅 JPA Repository
 */
@Repository
public interface JpaBacktestRepository extends JpaRepository<BacktestEntity, Long> {

    /**
     * UUID로 백테스팅 조회
     */
    Optional<BacktestEntity> findByBacktestUuid(String backtestUuid);

    /**
     * 상태별 백테스팅 조회
     */
    List<BacktestEntity> findByStatus(BacktestStatus status);

    /**
     * 생성 시간 범위로 백테스팅 조회 (최신순)
     */
    List<BacktestEntity> findByCreatedAtBetweenOrderByCreatedAtDesc(
            LocalDateTime startDateTime, LocalDateTime endDateTime);

    /**
     * 종목코드별 백테스팅 조회 (최신순)
     */
    List<BacktestEntity> findByStockCodeOrderByCreatedAtDesc(String stockCode);

    /**
     * 전략 타입별 백테스팅 조회 (최신순)
     */
    List<BacktestEntity> findByStrategyTypeOrderByCreatedAtDesc(StrategyType strategyType);

    /**
     * 완료된 백테스팅 중 수익률 상위 조회
     */
    @Query("SELECT b FROM BacktestEntity b WHERE b.status = 'COMPLETED' " +
           "ORDER BY b.totalReturn DESC")
    List<BacktestEntity> findTopProfitableBacktests(Pageable pageable);

    /**
     * 실행 중인 백테스팅 조회
     */
    @Query("SELECT b FROM BacktestEntity b WHERE b.status = 'RUNNING' " +
           "ORDER BY b.startedAt ASC")
    List<BacktestEntity> findRunningBacktests();

    /**
     * 특정 기간 완료된 백테스팅 통계
     */
    @Query("SELECT COUNT(b), AVG(b.totalReturn), MAX(b.totalReturn), MIN(b.totalReturn) " +
           "FROM BacktestEntity b " +
           "WHERE b.status = 'COMPLETED' AND b.completedAt BETWEEN :startDate AND :endDate")
    Object[] getBacktestStatistics(@Param("startDate") LocalDateTime startDate,
                                   @Param("endDate") LocalDateTime endDate);

    /**
     * 전체 백테스팅 목록 (페이징, 최신순)
     */
    Page<BacktestEntity> findAllByOrderByCreatedAtDesc(Pageable pageable);

    /**
     * 상태별 백테스팅 목록 (페이징, 최신순)
     */
    Page<BacktestEntity> findByStatusOrderByCreatedAtDesc(BacktestStatus status, Pageable pageable);

    /**
     * 종목코드와 전략으로 백테스팅 검색
     */
    @Query("SELECT b FROM BacktestEntity b WHERE " +
           "(:stockCode IS NULL OR b.stockCode = :stockCode) AND " +
           "(:strategyType IS NULL OR b.strategyType = :strategyType) " +
           "ORDER BY b.createdAt DESC")
    Page<BacktestEntity> findByStockCodeAndStrategyType(
            @Param("stockCode") String stockCode,
            @Param("strategyType") StrategyType strategyType,
            Pageable pageable);

    /**
     * 오래된 완료/실패/취소 백테스팅 조회 (정리용)
     */
    @Query("SELECT b FROM BacktestEntity b WHERE " +
           "b.status IN ('COMPLETED', 'FAILED', 'CANCELLED') AND " +
           "b.completedAt < :cutoffDate")
    List<BacktestEntity> findOldFinishedBacktests(@Param("cutoffDate") LocalDateTime cutoffDate);

    /**
     * 종목별 백테스팅 수 집계
     */
    @Query("SELECT b.stockCode, COUNT(b) FROM BacktestEntity b " +
           "GROUP BY b.stockCode ORDER BY COUNT(b) DESC")
    List<Object[]> countByStockCode();

    /**
     * 전략별 성과 집계
     */
    @Query("SELECT b.strategyType, COUNT(b), AVG(b.totalReturn), " +
           "SUM(CASE WHEN b.totalReturn > 0 THEN 1 ELSE 0 END) " +
           "FROM BacktestEntity b WHERE b.status = 'COMPLETED' " +
           "GROUP BY b.strategyType")
    List<Object[]> getStrategyPerformanceStats();
}