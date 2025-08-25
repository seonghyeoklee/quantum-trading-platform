package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import lombok.Value;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 관심종목 목록 생성 Command
 */
@Value
public class CreateWatchlistCommand {
    @NotNull
    WatchlistId watchlistId;
    
    @NotNull
    UserId userId;
    
    @NotBlank
    String name;
    
    String description;
    
    boolean isDefault;
    
    public static CreateWatchlistCommand of(WatchlistId watchlistId, UserId userId, String name, String description, boolean isDefault) {
        return new CreateWatchlistCommand(watchlistId, userId, name, description, isDefault);
    }
    
    public void validate() {
        if (watchlistId == null) {
            throw new IllegalArgumentException("WatchlistId cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Watchlist name cannot be null or empty");
        }
        if (name.length() > 100) {
            throw new IllegalArgumentException("Watchlist name cannot exceed 100 characters");
        }
        if (description != null && description.length() > 500) {
            throw new IllegalArgumentException("Watchlist description cannot exceed 500 characters");
        }
    }
}