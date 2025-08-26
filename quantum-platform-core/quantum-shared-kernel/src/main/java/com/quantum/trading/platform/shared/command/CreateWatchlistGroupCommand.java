package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/**
 * 관심종목 그룹 생성 Command
 */
public record CreateWatchlistGroupCommand(
    @NotNull(message = "Group ID cannot be null")
    WatchlistGroupId groupId,
    
    @NotNull(message = "Watchlist ID cannot be null")
    WatchlistId watchlistId,
    
    @NotNull(message = "User ID cannot be null")
    UserId userId,
    
    @NotBlank(message = "Group name cannot be null or empty")
    @Size(max = 100, message = "Group name cannot exceed 100 characters")
    String name,
    
    @Size(max = 20, message = "Color cannot exceed 20 characters")
    String color // 그룹 색상 (optional)
) {
    
    /**
     * Compact constructor with validation and normalization
     */
    public CreateWatchlistGroupCommand {
        if (groupId == null) {
            throw new IllegalArgumentException("Group ID cannot be null");
        }
        if (watchlistId == null) {
            throw new IllegalArgumentException("Watchlist ID cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("User ID cannot be null");
        }
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Group name cannot be null or empty");
        }
        
        // 정규화
        name = name.trim();
        color = color != null ? color.trim() : null;
        
        // 길이 제한 검증
        if (name.length() > 100) {
            throw new IllegalArgumentException("Group name cannot exceed 100 characters");
        }
        if (color != null && color.length() > 20) {
            throw new IllegalArgumentException("Color cannot exceed 20 characters");
        }
    }
    
    /**
     * Factory method for creating watchlist group
     */
    public static CreateWatchlistGroupCommand create(WatchlistGroupId groupId, WatchlistId watchlistId, 
                                                   UserId userId, String name, String color) {
        return new CreateWatchlistGroupCommand(groupId, watchlistId, userId, name, color);
    }
    
    /**
     * Factory method without color
     */
    public static CreateWatchlistGroupCommand create(WatchlistGroupId groupId, WatchlistId watchlistId, 
                                                   UserId userId, String name) {
        return new CreateWatchlistGroupCommand(groupId, watchlistId, userId, name, null);
    }
    
    /**
     * Validation method for backward compatibility
     */
    public void validate() {
        // Record compact constructor already handles validation
        // This method is kept for backward compatibility
    }
}