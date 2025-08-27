package com.quantum.trading.platform.query.service;

import com.quantum.trading.platform.query.repository.PortfolioViewRepository;
import com.quantum.trading.platform.query.view.PortfolioView;
import com.quantum.trading.platform.query.view.PositionView;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

/**
 * 포트폴리오 조회 서비스
 * 
 * CQRS Query Side 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class PortfolioQueryService {
    
    private final PortfolioViewRepository portfolioViewRepository;
    
    /**
     * 포트폴리오 상세 조회
     */
    public Optional<PortfolioView> getPortfolio(String portfolioId) {
        return portfolioViewRepository.findById(portfolioId);
    }
    
    /**
     * 포트폴리오 조회 by PortfolioId (RiskManagementService용)
     */
    public PortfolioView findByPortfolioId(com.quantum.trading.platform.shared.value.PortfolioId portfolioId) {
        return portfolioViewRepository.findById(portfolioId.id()).orElse(null);
    }
    
    /**
     * 포트폴리오 존재 여부 확인 (TradingService용)
     */
    public boolean portfolioExists(String portfolioId) {
        return portfolioViewRepository.existsById(portfolioId);
    }
    
    /**
     * 사용자별 포트폴리오 조회
     */
    public Optional<PortfolioView> getUserPortfolio(String userId) {
        return portfolioViewRepository.findByUserId(userId);
    }
    
    /**
     * 여러 사용자의 포트폴리오 조회
     */
    public List<PortfolioView> getPortfolios(List<String> userIds) {
        return portfolioViewRepository.findByUserIdIn(userIds);
    }
    
    /**
     * 포지션을 보유한 포트폴리오 목록 조회
     */
    public List<PortfolioView> getPortfoliosWithPositions() {
        return portfolioViewRepository.findPortfoliosWithPositions();
    }
    
    /**
     * 최소 현금 잔액 이상인 포트폴리오 조회
     */
    public List<PortfolioView> getPortfoliosByMinimumCash(BigDecimal minCash) {
        return portfolioViewRepository.findByMinimumCashBalance(minCash);
    }
    
    /**
     * 최소 수익률 이상인 포트폴리오 조회
     */
    public List<PortfolioView> getPortfoliosByMinimumReturn(BigDecimal minReturn) {
        return portfolioViewRepository.findByMinimumReturn(minReturn);
    }
    
    /**
     * 최소 총 평가액 이상인 포트폴리오 조회
     */
    public List<PortfolioView> getPortfoliosByMinimumTotalValue(BigDecimal minValue) {
        return portfolioViewRepository.findByMinimumTotalValue(minValue);
    }
    
    /**
     * 특정 종목을 보유한 포트폴리오 조회
     */
    public List<PortfolioView> getPortfoliosHoldingSymbol(String symbol) {
        return portfolioViewRepository.findPortfoliosHoldingSymbol(symbol);
    }
    
    /**
     * 포트폴리오 성과 순위 조회
     */
    public List<PortfolioView> getPortfoliosByPerformance() {
        return portfolioViewRepository.findPortfoliosByPerformance();
    }
    
    /**
     * 포트폴리오 규모 순위 조회
     */
    public List<PortfolioView> getPortfoliosBySize() {
        return portfolioViewRepository.findPortfoliosBySize();
    }
    
    /**
     * 사용자 포트폴리오의 특정 종목 포지션 조회
     */
    public Optional<PositionView> getUserPosition(String userId, String symbol) {
        return getUserPortfolio(userId)
                .map(portfolio -> portfolio.getPosition(symbol));
    }
    
    /**
     * 포트폴리오별 특정 종목 포지션 조회 (TradingService용)
     */
    public Optional<PositionView> getPosition(String portfolioId, String symbol) {
        return getPortfolio(portfolioId)
                .map(portfolio -> portfolio.getPosition(symbol));
    }
    
    /**
     * 사용자 포트폴리오의 모든 포지션 조회
     */
    public List<PositionView> getUserPositions(String userId) {
        return getUserPortfolio(userId)
                .map(PortfolioView::getPositions)
                .orElse(List.of());
    }
    
    /**
     * 활성 포트폴리오 수 조회
     */
    public long getActivePortfolioCount() {
        return portfolioViewRepository.countActivePortfolios();
    }
    
    /**
     * 전체 관리 자산(AUM) 조회
     */
    public BigDecimal getTotalAssetsUnderManagement() {
        BigDecimal total = portfolioViewRepository.getTotalAssetsUnderManagement();
        return total != null ? total : BigDecimal.ZERO;
    }
    
    /**
     * 포트폴리오 분산투자 점수 조회
     */
    public List<PortfolioDiversification> getPortfolioDiversificationScores() {
        List<Object[]> results = portfolioViewRepository.getPortfolioDiversificationScores();
        
        return results.stream()
                .map(result -> new PortfolioDiversification(
                        (String) result[0], // userId
                        (Integer) result[1] // positionCount
                ))
                .toList();
    }
    
    /**
     * 수익률 분포 통계
     */
    public PortfolioReturnStatistics getReturnStatistics() {
        Object result = portfolioViewRepository.getReturnStatistics();
        
        if (result instanceof Object[] stats) {
            return PortfolioReturnStatistics.builder()
                    .profitableCount(((Number) stats[0]).longValue())
                    .losingCount(((Number) stats[1]).longValue())
                    .breakevenCount(((Number) stats[2]).longValue())
                    .averageReturn((BigDecimal) stats[3])
                    .maxReturn((BigDecimal) stats[4])
                    .minReturn((BigDecimal) stats[5])
                    .build();
        }
        
        return PortfolioReturnStatistics.builder().build();
    }
    
    /**
     * 사용자 포트폴리오 요약 정보
     */
    public PortfolioSummary getUserPortfolioSummary(String userId) {
        return getUserPortfolio(userId)
                .map(portfolio -> PortfolioSummary.builder()
                        .portfolioId(portfolio.getPortfolioId())
                        .userId(portfolio.getUserId())
                        .cashBalance(portfolio.getCashBalance())
                        .totalInvested(portfolio.getTotalInvested())
                        .totalMarketValue(portfolio.getTotalMarketValue())
                        .totalPortfolioValue(portfolio.getTotalPortfolioValue())
                        .totalProfitLoss(portfolio.getTotalProfitLoss())
                        .profitLossPercentage(portfolio.getProfitLossPercentage())
                        .positionCount(portfolio.getPositionCount())
                        .hasPositions(!portfolio.isEmpty())
                        .build())
                .orElse(PortfolioSummary.builder()
                        .portfolioId("")
                        .userId(userId)
                        .cashBalance(BigDecimal.ZERO)
                        .totalInvested(BigDecimal.ZERO)
                        .totalMarketValue(BigDecimal.ZERO)
                        .totalPortfolioValue(BigDecimal.ZERO)
                        .totalProfitLoss(BigDecimal.ZERO)
                        .profitLossPercentage(BigDecimal.ZERO)
                        .positionCount(0)
                        .hasPositions(false)
                        .build());
    }
    
    /**
     * 포트폴리오 분산투자 DTO
     */
    public record PortfolioDiversification(String userId, Integer positionCount) {}
    
    /**
     * 포트폴리오 수익률 통계 DTO
     */
    public static class PortfolioReturnStatistics {
        private final long profitableCount;
        private final long losingCount;
        private final long breakevenCount;
        private final BigDecimal averageReturn;
        private final BigDecimal maxReturn;
        private final BigDecimal minReturn;
        
        public static PortfolioReturnStatisticsBuilder builder() {
            return new PortfolioReturnStatisticsBuilder();
        }
        
        private PortfolioReturnStatistics(long profitableCount, long losingCount, long breakevenCount,
                                         BigDecimal averageReturn, BigDecimal maxReturn, BigDecimal minReturn) {
            this.profitableCount = profitableCount;
            this.losingCount = losingCount;
            this.breakevenCount = breakevenCount;
            this.averageReturn = averageReturn != null ? averageReturn : BigDecimal.ZERO;
            this.maxReturn = maxReturn != null ? maxReturn : BigDecimal.ZERO;
            this.minReturn = minReturn != null ? minReturn : BigDecimal.ZERO;
        }
        
        // Getters
        public long getProfitableCount() { return profitableCount; }
        public long getLosingCount() { return losingCount; }
        public long getBreakevenCount() { return breakevenCount; }
        public BigDecimal getAverageReturn() { return averageReturn; }
        public BigDecimal getMaxReturn() { return maxReturn; }
        public BigDecimal getMinReturn() { return minReturn; }
        public long getTotalCount() { return profitableCount + losingCount + breakevenCount; }
        
        public static class PortfolioReturnStatisticsBuilder {
            private long profitableCount;
            private long losingCount;
            private long breakevenCount;
            private BigDecimal averageReturn;
            private BigDecimal maxReturn;
            private BigDecimal minReturn;
            
            public PortfolioReturnStatisticsBuilder profitableCount(long profitableCount) {
                this.profitableCount = profitableCount;
                return this;
            }
            
            public PortfolioReturnStatisticsBuilder losingCount(long losingCount) {
                this.losingCount = losingCount;
                return this;
            }
            
            public PortfolioReturnStatisticsBuilder breakevenCount(long breakevenCount) {
                this.breakevenCount = breakevenCount;
                return this;
            }
            
            public PortfolioReturnStatisticsBuilder averageReturn(BigDecimal averageReturn) {
                this.averageReturn = averageReturn;
                return this;
            }
            
            public PortfolioReturnStatisticsBuilder maxReturn(BigDecimal maxReturn) {
                this.maxReturn = maxReturn;
                return this;
            }
            
            public PortfolioReturnStatisticsBuilder minReturn(BigDecimal minReturn) {
                this.minReturn = minReturn;
                return this;
            }
            
            public PortfolioReturnStatistics build() {
                return new PortfolioReturnStatistics(profitableCount, losingCount, breakevenCount,
                                                   averageReturn, maxReturn, minReturn);
            }
        }
    }
    
    /**
     * 포트폴리오 요약 정보 DTO
     */
    public static class PortfolioSummary {
        private final String portfolioId;
        private final String userId;
        private final BigDecimal cashBalance;
        private final BigDecimal totalInvested;
        private final BigDecimal totalMarketValue;
        private final BigDecimal totalPortfolioValue;
        private final BigDecimal totalProfitLoss;
        private final BigDecimal profitLossPercentage;
        private final Integer positionCount;
        private final boolean hasPositions;
        
        public static PortfolioSummaryBuilder builder() {
            return new PortfolioSummaryBuilder();
        }
        
        private PortfolioSummary(String portfolioId, String userId, BigDecimal cashBalance, 
                                BigDecimal totalInvested, BigDecimal totalMarketValue, BigDecimal totalPortfolioValue,
                                BigDecimal totalProfitLoss, BigDecimal profitLossPercentage, 
                                Integer positionCount, boolean hasPositions) {
            this.portfolioId = portfolioId;
            this.userId = userId;
            this.cashBalance = cashBalance;
            this.totalInvested = totalInvested;
            this.totalMarketValue = totalMarketValue;
            this.totalPortfolioValue = totalPortfolioValue;
            this.totalProfitLoss = totalProfitLoss;
            this.profitLossPercentage = profitLossPercentage;
            this.positionCount = positionCount;
            this.hasPositions = hasPositions;
        }
        
        // Getters
        public String getPortfolioId() { return portfolioId; }
        public String getUserId() { return userId; }
        public BigDecimal getCashBalance() { return cashBalance; }
        public BigDecimal getTotalInvested() { return totalInvested; }
        public BigDecimal getTotalMarketValue() { return totalMarketValue; }
        public BigDecimal getTotalPortfolioValue() { return totalPortfolioValue; }
        public BigDecimal getTotalProfitLoss() { return totalProfitLoss; }
        public BigDecimal getProfitLossPercentage() { return profitLossPercentage; }
        public Integer getPositionCount() { return positionCount; }
        public boolean isHasPositions() { return hasPositions; }
        
        public static class PortfolioSummaryBuilder {
            private String portfolioId;
            private String userId;
            private BigDecimal cashBalance;
            private BigDecimal totalInvested;
            private BigDecimal totalMarketValue;
            private BigDecimal totalPortfolioValue;
            private BigDecimal totalProfitLoss;
            private BigDecimal profitLossPercentage;
            private Integer positionCount;
            private boolean hasPositions;
            
            public PortfolioSummaryBuilder portfolioId(String portfolioId) {
                this.portfolioId = portfolioId;
                return this;
            }
            
            public PortfolioSummaryBuilder userId(String userId) {
                this.userId = userId;
                return this;
            }
            
            public PortfolioSummaryBuilder cashBalance(BigDecimal cashBalance) {
                this.cashBalance = cashBalance;
                return this;
            }
            
            public PortfolioSummaryBuilder totalInvested(BigDecimal totalInvested) {
                this.totalInvested = totalInvested;
                return this;
            }
            
            public PortfolioSummaryBuilder totalMarketValue(BigDecimal totalMarketValue) {
                this.totalMarketValue = totalMarketValue;
                return this;
            }
            
            public PortfolioSummaryBuilder totalPortfolioValue(BigDecimal totalPortfolioValue) {
                this.totalPortfolioValue = totalPortfolioValue;
                return this;
            }
            
            public PortfolioSummaryBuilder totalProfitLoss(BigDecimal totalProfitLoss) {
                this.totalProfitLoss = totalProfitLoss;
                return this;
            }
            
            public PortfolioSummaryBuilder profitLossPercentage(BigDecimal profitLossPercentage) {
                this.profitLossPercentage = profitLossPercentage;
                return this;
            }
            
            public PortfolioSummaryBuilder positionCount(Integer positionCount) {
                this.positionCount = positionCount;
                return this;
            }
            
            public PortfolioSummaryBuilder hasPositions(boolean hasPositions) {
                this.hasPositions = hasPositions;
                return this;
            }
            
            public PortfolioSummary build() {
                return new PortfolioSummary(portfolioId, userId, cashBalance, totalInvested, 
                                          totalMarketValue, totalPortfolioValue, totalProfitLoss, 
                                          profitLossPercentage, positionCount, hasPositions);
            }
        }
    }
}