package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.PortfolioId;
import com.quantum.trading.platform.shared.value.UserId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 포트폴리오 생성 명령
 */
public record CreatePortfolioCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "Portfolio ID cannot be null")
    PortfolioId portfolioId,
    
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotNull(message = "Initial cash cannot be null")
    Money initialCash
) {
    
    /**
     * Compact constructor with validation
     */
    public CreatePortfolioCommand {
        if (portfolioId == null) {
            throw new IllegalArgumentException("Portfolio ID cannot be null");
        }
        
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (initialCash == null) {
            throw new IllegalArgumentException("Initial cash cannot be null");
        }
        
        if (initialCash.amount().compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Initial cash cannot be negative");
        }
    }
    
    /**
     * Factory method for creating portfolio with zero initial cash
     */
    public static CreatePortfolioCommand createWithZeroCash(PortfolioId portfolioId, UserId userId) {
        return new CreatePortfolioCommand(portfolioId, userId, Money.ofKrw(BigDecimal.ZERO));
    }
    
    /**
     * Factory method for creating portfolio with specific initial cash
     */
    public static CreatePortfolioCommand create(PortfolioId portfolioId, UserId userId, Money initialCash) {
        return new CreatePortfolioCommand(portfolioId, userId, initialCash);
    }
    
    /**
     * Validation method for backward compatibility
     */
    public void validate() {
        // Record compact constructor already handles validation
        // This method is kept for backward compatibility
    }
    
    // Getter methods for legacy code compatibility
    public PortfolioId getPortfolioId() {
        return portfolioId;
    }
    
    public UserId getUserId() {
        return userId;
    }
    
    public Money getInitialCash() {
        return initialCash;
    }
}