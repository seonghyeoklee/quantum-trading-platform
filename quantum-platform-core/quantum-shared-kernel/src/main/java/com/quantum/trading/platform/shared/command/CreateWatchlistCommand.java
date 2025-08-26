package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/**
 * 관심종목 목록 생성 Command
 */
public record CreateWatchlistCommand(
    @NotNull(message = "Watchlist ID cannot be null")
    WatchlistId watchlistId,
    
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotBlank(message = "Watchlist name cannot be null or empty")
    @Size(max = 100, message = "Watchlist name cannot exceed 100 characters")
    String name,
    
    @Size(max = 500, message = "Watchlist description cannot exceed 500 characters")
    String description,
    
    boolean isDefault
) {
    
    /**
     * Compact constructor with validation and normalization
     */
    public CreateWatchlistCommand {
        if (watchlistId == null) {
            throw new IllegalArgumentException("Watchlist ID cannot be null");
        }
        
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Watchlist name cannot be null or empty");
        }
        
        // 정규화
        name = name.trim();
        description = description != null ? description.trim() : null;
        
        // 길이 제한 검증
        if (name.length() > 100) {
            throw new IllegalArgumentException("Watchlist name cannot exceed 100 characters");
        }
        
        if (description != null && description.length() > 500) {
            throw new IllegalArgumentException("Watchlist description cannot exceed 500 characters");
        }
    }
    
    /**
     * Factory method for creating watchlist
     */
    public static CreateWatchlistCommand create(WatchlistId watchlistId, UserId userId, String name, String description, boolean isDefault) {
        return new CreateWatchlistCommand(watchlistId, userId, name, description, isDefault);
    }
    
    /**
     * Factory method for creating default watchlist
     */
    public static CreateWatchlistCommand createDefault(WatchlistId watchlistId, UserId userId, String name) {
        return new CreateWatchlistCommand(watchlistId, userId, name, null, true);
    }
    
    /**
     * Validation method for backward compatibility
     */
    public void validate() {
        // Record compact constructor already handles validation
        // This method is kept for backward compatibility
    }
}