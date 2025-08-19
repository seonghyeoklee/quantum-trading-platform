package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.PortfolioId;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import java.math.BigDecimal;

/**
 * 포트폴리오 생성 명령
 */
@Value
@Builder
public class CreatePortfolioCommand {
    @TargetAggregateIdentifier
    PortfolioId portfolioId;
    
    UserId userId;
    Money initialCash;
    
    public void validate() {
        if (portfolioId == null) {
            throw new IllegalArgumentException("Portfolio ID cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        if (initialCash == null || initialCash.getAmount().compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException("Initial cash cannot be negative");
        }
    }
}