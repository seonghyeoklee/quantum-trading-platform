package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/**
 * 관심종목에 종목 추가 Command
 */
public record AddStockToWatchlistCommand(
    @NotNull(message = "Watchlist ID cannot be null")
    WatchlistId watchlistId,
    
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotNull(message = "Symbol cannot be null")
    Symbol symbol,
    
    @NotBlank(message = "Stock name cannot be null or empty")
    @Size(max = 100, message = "Stock name cannot exceed 100 characters")
    String stockName,
    
    WatchlistGroupId groupId, // nullable - 그룹이 없으면 null
    
    @Size(max = 500, message = "Note cannot exceed 500 characters")
    String note // 사용자 메모
) {
    
    /**
     * Compact constructor with validation and normalization
     */
    public AddStockToWatchlistCommand {
        if (watchlistId == null) {
            throw new IllegalArgumentException("Watchlist ID cannot be null");
        }
        
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (symbol == null) {
            throw new IllegalArgumentException("Symbol cannot be null");
        }
        
        if (stockName == null || stockName.trim().isEmpty()) {
            throw new IllegalArgumentException("Stock name cannot be null or empty");
        }
        
        // 정규화
        stockName = stockName.trim();
        note = note != null ? note.trim() : null;
        
        // 길이 제한 검증
        if (stockName.length() > 100) {
            throw new IllegalArgumentException("Stock name cannot exceed 100 characters");
        }
        
        if (note != null && note.length() > 500) {
            throw new IllegalArgumentException("Note cannot exceed 500 characters");
        }
    }
    
    /**
     * Factory method for adding stock to watchlist
     */
    public static AddStockToWatchlistCommand create(WatchlistId watchlistId, UserId userId, Symbol symbol, 
                                                  String stockName, WatchlistGroupId groupId, String note) {
        return new AddStockToWatchlistCommand(watchlistId, userId, symbol, stockName, groupId, note);
    }
    
    /**
     * Factory method for adding stock without group or note
     */
    public static AddStockToWatchlistCommand create(WatchlistId watchlistId, UserId userId, Symbol symbol, String stockName) {
        return new AddStockToWatchlistCommand(watchlistId, userId, symbol, stockName, null, null);
    }
    
    /**
     * Factory method for adding stock to specific group
     */
    public static AddStockToWatchlistCommand createInGroup(WatchlistId watchlistId, UserId userId, Symbol symbol, 
                                                         String stockName, WatchlistGroupId groupId) {
        return new AddStockToWatchlistCommand(watchlistId, userId, symbol, stockName, groupId, null);
    }
    
    /**
     * Validation method for backward compatibility
     */
    public void validate() {
        // Record compact constructor already handles validation
        // This method is kept for backward compatibility
    }
}