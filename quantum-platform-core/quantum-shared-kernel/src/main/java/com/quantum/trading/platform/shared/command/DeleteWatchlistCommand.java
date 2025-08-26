package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

/**
 * 관심종목 목록 삭제 Command
 */
public record DeleteWatchlistCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "Watchlist ID cannot be null")
    WatchlistId watchlistId,
    
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotNull(message = "Deleted at cannot be null")
    LocalDateTime deletedAt
) {
    
    /**
     * Compact constructor with validation
     */
    public DeleteWatchlistCommand {
        if (watchlistId == null) {
            throw new IllegalArgumentException("Watchlist ID cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        if (deletedAt == null) {
            deletedAt = LocalDateTime.now();
        }
    }
    
    /**
     * Factory method for deleting watchlist
     */
    public static DeleteWatchlistCommand create(WatchlistId watchlistId, UserId userId) {
        return new DeleteWatchlistCommand(watchlistId, userId, LocalDateTime.now());
    }
    
    /**
     * Factory method with specific deletion time
     */
    public static DeleteWatchlistCommand create(WatchlistId watchlistId, UserId userId, LocalDateTime deletedAt) {
        return new DeleteWatchlistCommand(watchlistId, userId, deletedAt);
    }
    
    /**
     * Validation method for backward compatibility
     */
    public void validate() {
        // Record compact constructor already handles validation
        // This method is kept for backward compatibility
    }
}