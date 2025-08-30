package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.PortfolioId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import java.math.BigDecimal;

/**
 * 현금 입금 명령
 */
public record DepositCashCommand(
    @TargetAggregateIdentifier
    PortfolioId portfolioId,
    Money amount,
    String description
) {
    
    public void validate() {
        if (portfolioId == null) {
            throw new IllegalArgumentException("Portfolio ID cannot be null");
        }
        if (amount == null || amount.amount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Deposit amount must be positive");
        }
    }
    
    /**
     * Builder pattern support for test compatibility
     */
    public static Builder builder() {
        return new Builder();
    }
    
    public static class Builder {
        private PortfolioId portfolioId;
        private Money amount;
        private String description;
        
        public Builder portfolioId(PortfolioId portfolioId) {
            this.portfolioId = portfolioId;
            return this;
        }
        
        public Builder amount(Money amount) {
            this.amount = amount;
            return this;
        }
        
        public Builder description(String description) {
            this.description = description;
            return this;
        }
        
        public DepositCashCommand build() {
            return new DepositCashCommand(portfolioId, amount, description);
        }
    }
}