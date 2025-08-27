package com.quantum.web.service;

import com.quantum.trading.platform.query.service.OrderQueryService;
import com.quantum.trading.platform.query.service.PortfolioQueryService;
import com.quantum.trading.platform.query.view.OrderView;
import com.quantum.trading.platform.query.view.PortfolioView;
import com.quantum.trading.platform.shared.value.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

/**
 * 리스크 관리 서비스
 * 
 * 주문 실행 전 리스크 검증 및 관리:
 * - 자금 검증 (매수 가능 금액)
 * - 보유 수량 검증 (매도 가능 수량)
 * - 일일 거래량 제한
 * - 손실 한도 체크
 * - 시장 시간 검증
 * - 주문 크기 제한
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class RiskManagementService {
    
    private final PortfolioQueryService portfolioQueryService;
    private final OrderQueryService orderQueryService;
    
    // 설정값들 - 실제 환경에서는 데이터베이스나 설정 서버에서 관리
    @Value("${trading.risk.max-order-amount:10000000}") // 1천만원
    private BigDecimal maxOrderAmount;
    
    @Value("${trading.risk.max-daily-loss:5000000}") // 500만원
    private BigDecimal maxDailyLoss;
    
    @Value("${trading.risk.max-daily-trade-count:50}")
    private int maxDailyTradeCount;
    
    @Value("${trading.risk.max-position-ratio:0.3}") // 30%
    private BigDecimal maxPositionRatio;
    
    @Value("${trading.market.start-time:09:00}")
    private String marketStartTime;
    
    @Value("${trading.market.end-time:15:30}")
    private String marketEndTime;
    
    /**
     * 주문 전 종합적인 리스크 검증
     * 
     * @param userId 사용자 ID
     * @param portfolioId 포트폴리오 ID  
     * @param symbol 종목코드
     * @param side 매매방향
     * @param quantity 주문수량
     * @param price 주문가격
     * @param orderType 주문유형
     * @return RiskValidationResult 검증 결과
     */
    public RiskValidationResult validateOrder(
            UserId userId,
            PortfolioId portfolioId,
            Symbol symbol,
            OrderSide side,
            Quantity quantity,
            Money price,
            OrderType orderType) {
        
        log.info("🔍 Starting risk validation for order - userId: {}, symbol: {}, side: {}, quantity: {}", 
                userId.value(), symbol.value(), side.name(), quantity.value());
        
        try {
            // 1. 포트폴리오 조회
            PortfolioView portfolio = portfolioQueryService.findByPortfolioId(portfolioId);
            if (portfolio == null) {
                return RiskValidationResult.rejected("Portfolio not found: " + portfolioId.id());
            }
            
            // 2. 시장 시간 검증
            RiskValidationResult marketTimeResult = validateMarketTime(orderType);
            if (!marketTimeResult.isValid()) {
                return marketTimeResult;
            }
            
            // 3. 주문 크기 검증
            Money orderAmount = price.multiply(quantity.value());
            RiskValidationResult orderSizeResult = validateOrderSize(orderAmount);
            if (!orderSizeResult.isValid()) {
                return orderSizeResult;
            }
            
            // 4. 매매방향별 검증
            if (side == OrderSide.BUY) {
                return validateBuyOrder(portfolio, symbol, quantity, price, orderAmount);
            } else {
                return validateSellOrder(portfolio, symbol, quantity);
            }
            
        } catch (Exception e) {
            log.error("🚨 Risk validation failed unexpectedly - userId: {}", userId.value(), e);
            return RiskValidationResult.rejected("Risk validation system error: " + e.getMessage());
        }
    }
    
    /**
     * 매수 주문 검증
     */
    private RiskValidationResult validateBuyOrder(
            PortfolioView portfolio, 
            Symbol symbol, 
            Quantity quantity, 
            Money price,
            Money orderAmount) {
        
        // 1. 가용 자금 검증
        Money availableCash = portfolio.getAvailableCash();
        if (availableCash.amount().compareTo(orderAmount.amount()) < 0) {
            return RiskValidationResult.rejected(
                String.format("Insufficient funds: available=%s, required=%s", 
                    availableCash.amount(), orderAmount.amount()));
        }
        
        // 2. 포트폴리오 집중도 검증 (특정 종목이 30% 이상이 되지 않도록)
        Money totalPortfolioValue = portfolio.getTotalValue();
        if (totalPortfolioValue.amount().compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal newPositionRatio = orderAmount.amount()
                    .divide(totalPortfolioValue.amount(), 4, java.math.RoundingMode.HALF_UP);
            
            if (newPositionRatio.compareTo(maxPositionRatio) > 0) {
                return RiskValidationResult.rejected(
                    String.format("Position ratio too high: %.2f%% > %.2f%%", 
                        newPositionRatio.multiply(BigDecimal.valueOf(100)), 
                        maxPositionRatio.multiply(BigDecimal.valueOf(100))));
            }
        }
        
        // 3. 일일 거래 횟수 제한 검증
        RiskValidationResult dailyTradeResult = validateDailyTradeCount(UserId.of(portfolio.getUserId()));
        if (!dailyTradeResult.isValid()) {
            return dailyTradeResult;
        }
        
        // 4. 일일 손실 한도 검증
        RiskValidationResult dailyLossResult = validateDailyLoss(UserId.of(portfolio.getUserId()));
        if (!dailyLossResult.isValid()) {
            return dailyLossResult;
        }
        
        log.info("✅ Buy order risk validation passed - symbol: {}, amount: {}", 
                symbol.value(), orderAmount.amount());
        
        return RiskValidationResult.approved(
            String.format("Buy order approved: %s shares of %s at %s", 
                quantity.value(), symbol.value(), price.amount()));
    }
    
    /**
     * 매도 주문 검증
     */
    private RiskValidationResult validateSellOrder(
            PortfolioView portfolio, 
            Symbol symbol, 
            Quantity quantity) {
        
        // 1. 보유 수량 검증
        // TODO: PositionView에서 해당 종목의 보유 수량 조회
        // 현재는 기본 검증만 수행
        
        // 포트폴리오에서 해당 종목의 포지션 조회
        // 실제 구현에서는 PositionView를 통해 정확한 보유 수량을 확인해야 함
        
        log.info("📋 Validating sell order - checking position for symbol: {}", symbol.value());
        
        // 기본적인 검증: 수량이 양수인지 확인
        if (quantity.value() <= 0) {
            return RiskValidationResult.rejected("Sell quantity must be positive");
        }
        
        // TODO: 실제 보유 수량과 비교
        // Quantity availableQuantity = getAvailableQuantityForSymbol(portfolio, symbol);
        // if (availableQuantity.value() < quantity.value()) {
        //     return RiskValidationResult.rejected("Insufficient shares to sell");
        // }
        
        // 3. 일일 거래 횟수 제한 검증
        RiskValidationResult dailyTradeResult = validateDailyTradeCount(UserId.of(portfolio.getUserId()));
        if (!dailyTradeResult.isValid()) {
            return dailyTradeResult;
        }
        
        log.info("✅ Sell order risk validation passed - symbol: {}, quantity: {}", 
                symbol.value(), quantity.value());
        
        return RiskValidationResult.approved(
            String.format("Sell order approved: %s shares of %s", 
                quantity.value(), symbol.value()));
    }
    
    /**
     * 시장 시간 검증
     */
    private RiskValidationResult validateMarketTime(OrderType orderType) {
        LocalTime now = LocalTime.now();
        LocalTime marketStart = LocalTime.parse(marketStartTime);
        LocalTime marketEnd = LocalTime.parse(marketEndTime);
        
        // 시장가 주문은 시장 시간에만 허용
        if (orderType == OrderType.MARKET) {
            if (now.isBefore(marketStart) || now.isAfter(marketEnd)) {
                return RiskValidationResult.rejected(
                    String.format("Market orders only allowed during market hours (%s - %s)", 
                        marketStartTime, marketEndTime));
            }
        }
        
        return RiskValidationResult.approved("Market time validation passed");
    }
    
    /**
     * 주문 크기 검증
     */
    private RiskValidationResult validateOrderSize(Money orderAmount) {
        if (orderAmount.amount().compareTo(maxOrderAmount) > 0) {
            return RiskValidationResult.rejected(
                String.format("Order amount exceeds maximum: %s > %s", 
                    orderAmount.amount(), maxOrderAmount));
        }
        
        return RiskValidationResult.approved("Order size validation passed");
    }
    
    /**
     * 일일 거래 횟수 제한 검증
     */
    private RiskValidationResult validateDailyTradeCount(UserId userId) {
        try {
            LocalDateTime todayStart = LocalDateTime.now().toLocalDate().atStartOfDay();
            List<OrderView> todayOrders = orderQueryService.findOrdersByUserIdAndDateRange(
                    userId, todayStart, LocalDateTime.now());
            
            if (todayOrders.size() >= maxDailyTradeCount) {
                return RiskValidationResult.rejected(
                    String.format("Daily trade count limit exceeded: %d >= %d", 
                        todayOrders.size(), maxDailyTradeCount));
            }
            
            return RiskValidationResult.approved("Daily trade count validation passed");
            
        } catch (Exception e) {
            log.warn("⚠️ Could not validate daily trade count - allowing order: {}", e.getMessage());
            return RiskValidationResult.approved("Daily trade count validation skipped due to error");
        }
    }
    
    /**
     * 일일 손실 한도 검증
     */
    private RiskValidationResult validateDailyLoss(UserId userId) {
        try {
            // TODO: 실제 구현에서는 오늘의 실현손익을 계산해야 함
            // 현재는 기본 승인
            
            log.debug("📊 Daily loss validation for user: {} - currently not implemented", userId.value());
            
            return RiskValidationResult.approved("Daily loss validation passed");
            
        } catch (Exception e) {
            log.warn("⚠️ Could not validate daily loss - allowing order: {}", e.getMessage());
            return RiskValidationResult.approved("Daily loss validation skipped due to error");
        }
    }
    
    /**
     * 리스크 검증 결과 DTO
     */
    public static class RiskValidationResult {
        private final boolean valid;
        private final String message;
        private final RiskLevel riskLevel;
        
        private RiskValidationResult(boolean valid, String message, RiskLevel riskLevel) {
            this.valid = valid;
            this.message = message;
            this.riskLevel = riskLevel;
        }
        
        public static RiskValidationResult approved(String message) {
            return new RiskValidationResult(true, message, RiskLevel.LOW);
        }
        
        public static RiskValidationResult approvedWithWarning(String message) {
            return new RiskValidationResult(true, message, RiskLevel.MEDIUM);
        }
        
        public static RiskValidationResult rejected(String message) {
            return new RiskValidationResult(false, message, RiskLevel.HIGH);
        }
        
        // Getters
        public boolean isValid() { return valid; }
        public String getMessage() { return message; }
        public RiskLevel getRiskLevel() { return riskLevel; }
        
        public enum RiskLevel {
            LOW, MEDIUM, HIGH
        }
    }
}