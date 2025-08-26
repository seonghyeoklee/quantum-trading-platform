package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Builder;
import lombok.Value;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import java.time.LocalDateTime;

/**
 * 관심종목 목록 삭제 Command
 */
@Value
@Builder
public class DeleteWatchlistCommand {

    @TargetAggregateIdentifier
    WatchlistId watchlistId;
    
    UserId userId;
    
    @Builder.Default
    LocalDateTime deletedAt = LocalDateTime.now();

    public void validate() {
        if (watchlistId == null) {
            throw new IllegalArgumentException("WatchlistId cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (deletedAt == null) {
            throw new IllegalArgumentException("DeletedAt cannot be null");
        }
    }
}