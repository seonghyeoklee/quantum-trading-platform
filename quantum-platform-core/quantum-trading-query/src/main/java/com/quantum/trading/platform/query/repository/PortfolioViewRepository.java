package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.PortfolioView;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

/**
 * PortfolioView Repository
 * 
 * 포트폴리오 조회 최적화된 쿼리 인터페이스
 */
@Repository
public interface PortfolioViewRepository extends JpaRepository<PortfolioView, String> {
    
    /**
     * 사용자별 포트폴리오 조회
     */
    Optional<PortfolioView> findByUserId(String userId);
    
    /**
     * 사용자 ID 목록으로 포트폴리오 조회
     */
    List<PortfolioView> findByUserIdIn(List<String> userIds);
    
    /**
     * 포지션을 보유한 포트폴리오 조회
     */
    @Query("SELECT p FROM PortfolioView p WHERE p.positionCount > 0")
    List<PortfolioView> findPortfoliosWithPositions();
    
    /**
     * 특정 현금 잔액 이상인 포트폴리오 조회
     */
    @Query("SELECT p FROM PortfolioView p WHERE p.cashBalance >= :minCash")
    List<PortfolioView> findByMinimumCashBalance(@Param("minCash") BigDecimal minCash);
    
    /**
     * 수익률 기준 포트폴리오 조회
     */
    @Query("SELECT p FROM PortfolioView p WHERE p.profitLossPercentage >= :minReturn " +
           "ORDER BY p.profitLossPercentage DESC")
    List<PortfolioView> findByMinimumReturn(@Param("minReturn") BigDecimal minReturn);
    
    /**
     * 총 평가액 기준 포트폴리오 조회
     */
    @Query("SELECT p FROM PortfolioView p WHERE (p.cashBalance + p.totalMarketValue) >= :minValue " +
           "ORDER BY (p.cashBalance + p.totalMarketValue) DESC")
    List<PortfolioView> findByMinimumTotalValue(@Param("minValue") BigDecimal minValue);
    
    /**
     * 특정 종목을 보유한 포트폴리오 조회
     */
    @Query("SELECT DISTINCT p FROM PortfolioView p " +
           "JOIN p.positions pos " +
           "WHERE pos.symbol = :symbol AND pos.quantity > 0")
    List<PortfolioView> findPortfoliosHoldingSymbol(@Param("symbol") String symbol);
    
    /**
     * 포트폴리오 성과 순위 조회
     */
    @Query("SELECT p FROM PortfolioView p WHERE p.totalInvested > 0 " +
           "ORDER BY p.profitLossPercentage DESC")
    List<PortfolioView> findPortfoliosByPerformance();
    
    /**
     * 포트폴리오 규모 순위 조회
     */
    @Query("SELECT p FROM PortfolioView p " +
           "ORDER BY (p.cashBalance + p.totalMarketValue) DESC")
    List<PortfolioView> findPortfoliosBySize();
    
    /**
     * 활성 포트폴리오 수 조회 (포지션 보유 또는 현금 잔액 > 0)
     */
    @Query("SELECT COUNT(p) FROM PortfolioView p " +
           "WHERE p.positionCount > 0 OR p.cashBalance > 0")
    Long countActivePortfolios();
    
    /**
     * 전체 관리 자산(AUM) 조회
     */
    @Query("SELECT SUM(p.cashBalance + p.totalMarketValue) FROM PortfolioView p")
    BigDecimal getTotalAssetsUnderManagement();
    
    /**
     * 포트폴리오 분산투자 점수 조회 (보유 종목 수 기준)
     */
    @Query("SELECT p.userId, p.positionCount FROM PortfolioView p " +
           "WHERE p.positionCount > 0 " +
           "ORDER BY p.positionCount DESC")
    List<Object[]> getPortfolioDiversificationScores();
    
    /**
     * 수익률 분포 통계
     */
    @Query("SELECT " +
           "COUNT(CASE WHEN p.profitLossPercentage > 0 THEN 1 END) as profitable, " +
           "COUNT(CASE WHEN p.profitLossPercentage < 0 THEN 1 END) as losing, " +
           "COUNT(CASE WHEN p.profitLossPercentage = 0 THEN 1 END) as breakeven, " +
           "AVG(p.profitLossPercentage) as avgReturn, " +
           "MAX(p.profitLossPercentage) as maxReturn, " +
           "MIN(p.profitLossPercentage) as minReturn " +
           "FROM PortfolioView p WHERE p.totalInvested > 0")
    Object getReturnStatistics();
}