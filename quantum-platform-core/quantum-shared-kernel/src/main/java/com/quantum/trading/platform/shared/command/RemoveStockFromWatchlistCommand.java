package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Value;

import jakarta.validation.constraints.NotNull;

/**
 * 관심종목에서 종목 제거 Command
 */
@Value
public class RemoveStockFromWatchlistCommand {
    @NotNull
    WatchlistId watchlistId;
    
    @NotNull
    UserId userId;
    
    @NotNull
    Symbol symbol;
    
    public static RemoveStockFromWatchlistCommand of(WatchlistId watchlistId, UserId userId, Symbol symbol) {
        return new RemoveStockFromWatchlistCommand(watchlistId, userId, symbol);
    }
    
    public void validate() {
        if (watchlistId == null) {
            throw new IllegalArgumentException("WatchlistId cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (symbol == null) {
            throw new IllegalArgumentException("Symbol cannot be null");
        }
    }
}