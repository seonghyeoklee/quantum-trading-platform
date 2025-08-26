package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;

import jakarta.validation.constraints.NotNull;

/**
 * 관심종목에서 종목 제거 Command
 */
public record RemoveStockFromWatchlistCommand(
    @NotNull(message = "Watchlist ID cannot be null")
    WatchlistId watchlistId,
    
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotNull(message = "Symbol cannot be null")
    Symbol symbol
) {
    
    /**
     * Compact constructor with validation
     */
    public RemoveStockFromWatchlistCommand {
        if (watchlistId == null) {
            throw new IllegalArgumentException("Watchlist ID cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        if (symbol == null) {
            throw new IllegalArgumentException("Symbol cannot be null");
        }
    }
    
    /**
     * Factory method for removing stock from watchlist
     */
    public static RemoveStockFromWatchlistCommand create(WatchlistId watchlistId, UserId userId, Symbol symbol) {
        return new RemoveStockFromWatchlistCommand(watchlistId, userId, symbol);
    }
    
    /**
     * Validation method for backward compatibility
     */
    public void validate() {
        // Record compact constructor already handles validation
        // This method is kept for backward compatibility
    }
}