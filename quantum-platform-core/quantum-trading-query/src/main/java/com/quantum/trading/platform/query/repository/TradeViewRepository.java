package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.TradeView;
import com.quantum.trading.platform.shared.value.OrderSide;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 거래 이력 Repository
 * 
 * 거래 내역 조회 및 통계를 위한 최적화된 쿼리 제공
 */
@Repository
public interface TradeViewRepository extends JpaRepository<TradeView, String> {
    
    // 기본 조회
    Optional<TradeView> findByOrderId(String orderId);
    Optional<TradeView> findByBrokerOrderId(String brokerOrderId);
    Optional<TradeView> findByBrokerTradeId(String brokerTradeId);
    
    // 사용자별 거래 이력
    Page<TradeView> findByUserIdOrderByExecutedAtDesc(String userId, Pageable pageable);
    Page<TradeView> findByUserIdAndSymbolOrderByExecutedAtDesc(String userId, String symbol, Pageable pageable);
    Page<TradeView> findByUserIdAndSideOrderByExecutedAtDesc(String userId, OrderSide side, Pageable pageable);
    
    // 포트폴리오별 거래 이력
    Page<TradeView> findByPortfolioIdOrderByExecutedAtDesc(String portfolioId, Pageable pageable);
    Page<TradeView> findByPortfolioIdAndSymbolOrderByExecutedAtDesc(String portfolioId, String symbol, Pageable pageable);
    
    // 기간별 조회
    @Query("SELECT t FROM TradeView t WHERE t.userId = :userId AND t.executedAt BETWEEN :startDate AND :endDate ORDER BY t.executedAt DESC")
    Page<TradeView> findByUserIdAndDateRange(@Param("userId") String userId, 
                                           @Param("startDate") LocalDateTime startDate, 
                                           @Param("endDate") LocalDateTime endDate, 
                                           Pageable pageable);
    
    @Query("SELECT t FROM TradeView t WHERE t.portfolioId = :portfolioId AND t.executedAt BETWEEN :startDate AND :endDate ORDER BY t.executedAt DESC")
    Page<TradeView> findByPortfolioIdAndDateRange(@Param("portfolioId") String portfolioId, 
                                                @Param("startDate") LocalDateTime startDate, 
                                                @Param("endDate") LocalDateTime endDate, 
                                                Pageable pageable);
    
    // 통계 쿼리
    @Query("SELECT COUNT(t) FROM TradeView t WHERE t.userId = :userId")
    Long countByUserId(@Param("userId") String userId);
    
    @Query("SELECT COUNT(t) FROM TradeView t WHERE t.userId = :userId AND t.side = :side")
    Long countByUserIdAndSide(@Param("userId") String userId, @Param("side") OrderSide side);
    
    @Query("SELECT SUM(t.executedAmount) FROM TradeView t WHERE t.userId = :userId AND t.side = :side")
    BigDecimal sumExecutedAmountByUserIdAndSide(@Param("userId") String userId, @Param("side") OrderSide side);
    
    @Query("SELECT SUM(t.realizedPnL) FROM TradeView t WHERE t.userId = :userId AND t.realizedPnL IS NOT NULL")
    BigDecimal sumRealizedPnLByUserId(@Param("userId") String userId);
    
    // 오늘의 거래
    @Query("SELECT t FROM TradeView t WHERE t.userId = :userId AND DATE(t.executedAt) = CURRENT_DATE ORDER BY t.executedAt DESC")
    List<TradeView> findTodayTradesByUserId(@Param("userId") String userId);
    
    // 종목별 거래 요약
    @Query("SELECT t.symbol, COUNT(t), SUM(t.executedQuantity), AVG(t.executedPrice) " +
           "FROM TradeView t WHERE t.userId = :userId AND t.side = :side " +
           "GROUP BY t.symbol ORDER BY COUNT(t) DESC")
    List<Object[]> getTradesSummaryBySymbol(@Param("userId") String userId, @Param("side") OrderSide side);
    
    // 월별 거래 통계
    @Query("SELECT YEAR(t.executedAt), MONTH(t.executedAt), COUNT(t), SUM(t.executedAmount) " +
           "FROM TradeView t WHERE t.userId = :userId " +
           "GROUP BY YEAR(t.executedAt), MONTH(t.executedAt) ORDER BY YEAR(t.executedAt) DESC, MONTH(t.executedAt) DESC")
    List<Object[]> getMonthlyTradeStats(@Param("userId") String userId);
    
    // 거래 수수료 통계
    @Query("SELECT SUM(t.transactionFee), SUM(t.securitiesTax) FROM TradeView t WHERE t.userId = :userId")
    List<Object[]> getTotalFeesAndTaxes(@Param("userId") String userId);
    
    // 최근 거래 (성능 최적화)
    @Query(value = "SELECT * FROM trade_view WHERE user_id = :userId ORDER BY executed_at DESC LIMIT :limit", 
           nativeQuery = true)
    List<TradeView> findRecentTradesByUserId(@Param("userId") String userId, @Param("limit") int limit);
    
    // 부분 체결 거래 조회
    List<TradeView> findByOrderIdAndIsPartialFillTrueOrderByFillSequenceAsc(String orderId);
    
    // 종목의 최근 거래가 조회 (시장 분석용)
    @Query("SELECT t.executedPrice FROM TradeView t WHERE t.symbol = :symbol ORDER BY t.executedAt DESC LIMIT 1")
    Optional<BigDecimal> findLatestExecutedPriceBySymbol(@Param("symbol") String symbol);
    
    // 실현손익이 있는 거래만 조회 (매도 거래)
    List<TradeView> findByUserIdAndRealizedPnLIsNotNullOrderByExecutedAtDesc(String userId, Pageable pageable);
    
    // 고수익 거래 조회 (수익률 기준)
    @Query("SELECT t FROM TradeView t WHERE t.userId = :userId AND t.realizedPnLRate > :minRate ORDER BY t.realizedPnLRate DESC")
    List<TradeView> findProfitableTradesByMinRate(@Param("userId") String userId, @Param("minRate") BigDecimal minRate);
}