package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.PortfolioId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 현금 입금 이벤트
 */
@Value
@Builder
public class CashDepositedEvent {
    PortfolioId portfolioId;
    Money amount;
    Money newCashBalance;
    String description;
    Instant timestamp;
}