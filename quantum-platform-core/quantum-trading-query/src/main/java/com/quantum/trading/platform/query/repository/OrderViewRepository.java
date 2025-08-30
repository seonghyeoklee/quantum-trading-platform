package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.trading.platform.shared.value.OrderStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

/**
 * OrderView Repository
 * 
 * 주문 조회 최적화된 쿼리 인터페이스
 */
@Repository
public interface OrderViewRepository extends JpaRepository<OrderView, String> {
    
    /**
     * 사용자별 주문 목록 조회 (페이징)
     */
    Page<OrderView> findByUserIdOrderByCreatedAtDesc(String userId, Pageable pageable);
    
    /**
     * 포트폴리오별 주문 목록 조회 (페이징)
     */
    Page<OrderView> findByPortfolioIdOrderByCreatedAtDesc(String portfolioId, Pageable pageable);
    
    /**
     * 포트폴리오별 상태별 주문 목록 조회 (페이징)
     */
    Page<OrderView> findByPortfolioIdAndStatusOrderByCreatedAtDesc(String portfolioId, OrderStatus status, Pageable pageable);
    
    /**
     * 사용자별 특정 상태 주문 목록 조회
     */
    List<OrderView> findByUserIdAndStatusOrderByCreatedAtDesc(String userId, OrderStatus status);
    
    /**
     * 포트폴리오별 특정 상태 주문 목록 조회
     */
    List<OrderView> findByPortfolioIdAndStatusOrderByCreatedAtDesc(String portfolioId, OrderStatus status);
    
    /**
     * 사용자별 활성 주문 조회 (미완료 주문)
     */
    @Query("SELECT o FROM OrderView o WHERE o.userId = :userId " +
           "AND o.status IN ('PENDING', 'SUBMITTED', 'PARTIALLY_FILLED') " +
           "ORDER BY o.createdAt DESC")
    List<OrderView> findActiveOrdersByUserId(@Param("userId") String userId);
    
    /**
     * 특정 종목의 주문 목록 조회
     */
    List<OrderView> findBySymbolOrderByCreatedAtDesc(String symbol);
    
    /**
     * 사용자별 특정 종목 주문 목록 조회
     */
    List<OrderView> findByUserIdAndSymbolOrderByCreatedAtDesc(String userId, String symbol);
    
    /**
     * 기간별 주문 조회
     */
    @Query("SELECT o FROM OrderView o WHERE o.userId = :userId " +
           "AND o.createdAt BETWEEN :startDate AND :endDate " +
           "ORDER BY o.createdAt DESC")
    List<OrderView> findByUserIdAndDateRange(
            @Param("userId") String userId,
            @Param("startDate") Instant startDate,
            @Param("endDate") Instant endDate);
    
    /**
     * 체결된 주문 조회 (손익 계산용)
     */
    @Query("SELECT o FROM OrderView o WHERE o.userId = :userId " +
           "AND o.status = 'FILLED' " +
           "AND o.filledAt IS NOT NULL " +
           "ORDER BY o.filledAt DESC")
    List<OrderView> findFilledOrdersByUserId(@Param("userId") String userId);
    
    /**
     * 포트폴리오별 체결된 주문 조회 (거래 내역용)
     */
    @Query("SELECT o FROM OrderView o WHERE o.portfolioId = :portfolioId " +
           "AND o.status = 'FILLED' " +
           "AND o.filledAt IS NOT NULL " +
           "ORDER BY o.filledAt DESC")
    Page<OrderView> findFilledOrdersByPortfolioId(@Param("portfolioId") String portfolioId, Pageable pageable);
    
    /**
     * 포트폴리오별 체결된 주문 조회 (종목 필터)
     */
    @Query("SELECT o FROM OrderView o WHERE o.portfolioId = :portfolioId " +
           "AND o.symbol = :symbol " +
           "AND o.status = 'FILLED' " +
           "AND o.filledAt IS NOT NULL " +
           "ORDER BY o.filledAt DESC")
    Page<OrderView> findFilledOrdersByPortfolioIdAndSymbol(@Param("portfolioId") String portfolioId, 
                                                          @Param("symbol") String symbol, 
                                                          Pageable pageable);
    
    /**
     * 특정 브로커의 주문 조회
     */
    List<OrderView> findByBrokerTypeOrderByCreatedAtDesc(String brokerType);
    
    /**
     * 브로커 주문 ID로 조회
     */
    Optional<OrderView> findByBrokerOrderId(String brokerOrderId);
    
    /**
     * 사용자별 주문 통계
     */
    @Query("SELECT COUNT(o), o.status FROM OrderView o WHERE o.userId = :userId GROUP BY o.status")
    List<Object[]> getOrderStatsByUserId(@Param("userId") String userId);
    
    /**
     * 일별 주문 수 통계
     */
    @Query("SELECT CAST(o.createdAt as LocalDate), COUNT(o) FROM OrderView o " +
           "WHERE o.userId = :userId " +
           "AND o.createdAt >= :startDate " +
           "GROUP BY CAST(o.createdAt as LocalDate) " +
           "ORDER BY CAST(o.createdAt as LocalDate)")
    List<Object[]> getDailyOrderStats(
            @Param("userId") String userId,
            @Param("startDate") Instant startDate);
    
    /**
     * 미체결 주문 수 조회
     */
    @Query("SELECT COUNT(o) FROM OrderView o WHERE o.userId = :userId " +
           "AND o.status IN ('PENDING', 'SUBMITTED', 'PARTIALLY_FILLED')")
    Long countPendingOrdersByUserId(@Param("userId") String userId);
    
    /**
     * 특정 종목의 최근 체결가 조회
     */
    @Query("SELECT o.filledPrice FROM OrderView o WHERE o.symbol = :symbol " +
           "AND o.status = 'FILLED' AND o.filledPrice IS NOT NULL " +
           "ORDER BY o.filledAt DESC")
    List<java.math.BigDecimal> getRecentFilledPrices(@Param("symbol") String symbol, Pageable pageable);
}