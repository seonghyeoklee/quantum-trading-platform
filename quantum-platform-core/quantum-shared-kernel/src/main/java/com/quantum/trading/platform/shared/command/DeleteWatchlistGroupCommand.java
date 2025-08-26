package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import org.axonframework.modelling.command.TargetAggregateIdentifier;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

/**
 * 관심종목 그룹 삭제 Command
 */
public record DeleteWatchlistGroupCommand(
    @TargetAggregateIdentifier
    @NotNull(message = "Group ID cannot be null")
    WatchlistGroupId groupId,
    
    @NotNull(message = "Deleted at cannot be null")
    LocalDateTime deletedAt
) {
    
    /**
     * Compact constructor with validation
     */
    public DeleteWatchlistGroupCommand {
        if (groupId == null) {
            throw new IllegalArgumentException("Group ID cannot be null");
        }
        if (deletedAt == null) {
            deletedAt = LocalDateTime.now();
        }
    }
    
    /**
     * Factory method for deleting watchlist group
     */
    public static DeleteWatchlistGroupCommand create(WatchlistGroupId groupId) {
        return new DeleteWatchlistGroupCommand(groupId, LocalDateTime.now());
    }
    
    /**
     * Factory method with specific deletion time
     */
    public static DeleteWatchlistGroupCommand create(WatchlistGroupId groupId, LocalDateTime deletedAt) {
        return new DeleteWatchlistGroupCommand(groupId, deletedAt);
    }
    
    /**
     * Validation method for backward compatibility
     */
    public void validate() {
        // Record compact constructor already handles validation
        // This method is kept for backward compatibility
    }
}