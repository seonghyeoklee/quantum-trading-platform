package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import lombok.Value;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 관심종목에 종목 추가 Command
 */
@Value
public class AddStockToWatchlistCommand {
    @NotNull
    WatchlistId watchlistId;
    
    @NotNull
    UserId userId;
    
    @NotNull
    Symbol symbol;
    
    @NotBlank
    String stockName;
    
    WatchlistGroupId groupId; // nullable - 그룹이 없으면 null
    
    String note; // 사용자 메모
    
    public static AddStockToWatchlistCommand of(WatchlistId watchlistId, UserId userId, Symbol symbol, String stockName, WatchlistGroupId groupId, String note) {
        return new AddStockToWatchlistCommand(watchlistId, userId, symbol, stockName, groupId, note);
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
        if (stockName == null || stockName.trim().isEmpty()) {
            throw new IllegalArgumentException("Stock name cannot be null or empty");
        }
        if (stockName.length() > 100) {
            throw new IllegalArgumentException("Stock name cannot exceed 100 characters");
        }
        if (note != null && note.length() > 500) {
            throw new IllegalArgumentException("Note cannot exceed 500 characters");
        }
    }
}