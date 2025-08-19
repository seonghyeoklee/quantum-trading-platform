package com.quantum.trading.platform.shared.event;

import com.quantum.trading.platform.shared.value.Money;
import com.quantum.trading.platform.shared.value.PortfolioId;
import com.quantum.trading.platform.shared.value.UserId;
import lombok.Builder;
import lombok.Value;

import java.time.Instant;

/**
 * 포트폴리오 생성 이벤트
 */
@Value
@Builder
public class PortfolioCreatedEvent {
    PortfolioId portfolioId;
    UserId userId;
    Money initialCash;
    Instant timestamp;
}