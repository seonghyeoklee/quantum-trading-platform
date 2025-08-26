package com.quantum.trading.platform.shared.command;

import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;
import lombok.Value;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 관심종목 그룹 생성 Command
 */
@Value
public class CreateWatchlistGroupCommand {
    @NotNull
    WatchlistGroupId groupId;
    
    @NotNull
    WatchlistId watchlistId;
    
    @NotNull
    UserId userId;
    
    @NotBlank
    String name;
    
    String color; // 그룹 색상 (optional)
    
    public static CreateWatchlistGroupCommand of(WatchlistGroupId groupId, WatchlistId watchlistId, UserId userId, String name, String color) {
        return new CreateWatchlistGroupCommand(groupId, watchlistId, userId, name, color);
    }
    
    public void validate() {
        if (groupId == null) {
            throw new IllegalArgumentException("WatchlistGroupId cannot be null");
        }
        if (watchlistId == null) {
            throw new IllegalArgumentException("WatchlistId cannot be null");
        }
        if (userId == null) {
            throw new IllegalArgumentException("UserId cannot be null");
        }
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("Group name cannot be null or empty");
        }
        if (name.length() > 100) {
            throw new IllegalArgumentException("Group name cannot exceed 100 characters");
        }
        if (color != null && color.length() > 20) {
            throw new IllegalArgumentException("Color cannot exceed 20 characters");
        }
    }
}